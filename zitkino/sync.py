# -*- coding: utf-8 -*-


import times
import logging
import itertools

from zitkino.scrapers.cinemas import active_scrapers
from zitkino.scrapers.films import CSFDFilmRecognizer
from zitkino.models import data, Film, Cinema, Showtime


class StaticDataSynchronizer(object):
    """Inserts or updates static data defined in models."""

    def sync(self):
        """Perform synchronization."""
        for document in data:
            found = document.__class__.objects(slug=document.slug).first()
            if found:
                document.id = found.id
                document.save()  # update
            else:
                document.save()  # insert


class ShowtimesSynchronizer(object):
    """Synchronizes showtimes."""

    scrapers = active_scrapers

    def __init__(self, user_agent=None, logging_context=None):
        if logging_context:
            self._log = logging_context.logger(__name__)
        else:
            self._log = logging.getLogger(__name__)

        self.user_agent = user_agent
        self.csfd_recognizer = CSFDFilmRecognizer(user_agent)

    def _scrape_showtimes(self):
        now = times.now()

        showtime_lists = []
        for scraper in self.scrapers:
            s = scraper(now, self.user_agent)
            showtime_lists.append(s.scrape())
        return itertools.chain(*showtime_lists)

    def _sync_film(self, film):
        film_db = Film.objects(slug=film.slug).first()
        if film_db:
            film_db.sync(film)
            film_db.save()
            return film_db
        film.save()
        return film

    def _find_film_db(self, scraped_showtime):
        # TODO pokud ten film ma nejaka pole jako None, zkusim jej aktualizovat
        # podle toho co mam z kina
        params = {'titles__iexact': scraped_showtime.film_title}
        return Film.objects(**params).first()

    def _find_film_csfd(self, scraped_showtime):
        return self.csfd_recognizer.scrape(scraped_showtime)

    def _create_unknown_film(self, scraped_showtime):
        # TODO pokud mi hledani v csfd nic nevrati, musim si film ulozit do db
        # nejak sam z informaci, ktere jsem nascrapoval v kine
        film = Film()
        film.title_main = scraped_showtime.film_title
        film.titles = [scraped_showtime.film_title]
        film.save()
        return film

    def _get_film(self, scraped_showtime):
        film_title = scraped_showtime.film_title
        film = self._find_film_db(scraped_showtime)
        if not film:
            self._log.info('Film "%s" not found in db.', film_title)
            film = self._find_film_csfd(scraped_showtime)
            if film:
                self._log.info('Film "%s" found on CSFD.cz', film_title)
                film.titles.append(scraped_showtime.film_title)
                film = self._sync_film(film)
                self._log.info('Film "%s" synchronized.', film.title_main,
                               extra={'film_id': film.id})
            else:
                self._log.info('Film "%s" cannot be identified.', film_title)
                film = self._create_unknown_film(scraped_showtime)
        else:
            self._log.info('Film "%s" found in db.', film_title,
                           extra={'film_id': film.id})
        return film

    def _get_cinema(self, scraped_showtime):
        return Cinema.objects(slug=scraped_showtime.cinema_slug).first()

    def _get_showtime(self, scraped_showtime, film):
        cinema = self._get_cinema(scraped_showtime)
        starts_at = scraped_showtime.starts_at

        st = Showtime.objects(
            cinema=cinema,
            film=film,
            starts_at=starts_at).first()
        if st:
            #  update tags
            tags = list(set(st.tags + scraped_showtime.tags))
            st.tags = tags
            self._log.info('Updated showtime %s / "%s" scraped from %s.',
                           starts_at, film.title_main, cinema.slug,
                           extra={'showtime_id': st.id})
        else:
            # create a new one
            st = Showtime()
            st.cinema = cinema
            st.film = film
            st.starts_at = scraped_showtime.starts_at
            st.tags = scraped_showtime.tags
            self._log.info('Created showtime %s / "%s" scraped from %s.',
                           starts_at, film.title_main, cinema.slug)
        return st

    def sync(self):
        """Perform synchronization."""
        # TODO vyresit "čas probuzení" = "čas" ... stahovat z kin vic informaci
        # o filmech!

        for scraped_showtime in self._scrape_showtimes():
            film = self._get_film(scraped_showtime)
            film.save()
            showtime = self._get_showtime(scraped_showtime, film)
            showtime.save()
