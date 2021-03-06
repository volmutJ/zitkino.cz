# -*- coding: utf-8 -*-


from zitkino import parsers
from zitkino.utils import download
from zitkino.models import Cinema, Showtime, ScrapedFilm

from . import scrapers


cinema = Cinema(
    name=u'RWE letní kino na Riviéře',
    url='http://www.kinonariviere.cz/',
    street=u'Bauerova 322/7',
    town=u'Brno',
    coords=(49.18827, 16.56924)
)


@scrapers.register(cinema)
class Scraper(object):

    url = 'http://www.kinonariviere.cz/program'
    tags_map = {
        u'premiéra': 'premiere',
        u'titulky': 'subtitles',
    }

    def __call__(self):
        for row in self._scrape_rows():
            yield self._parse_row(row)

    def _scrape_rows(self):
        resp = download(self.url)
        html = parsers.html(resp.content, base_url=resp.url)
        return html.cssselect('.content table tr')

    def _parse_row(self, row):
        starts_at = parsers.date_time_year(
            row[1].text_content(),
            row[2].text_content()
        )

        title_main = row[3].text_content()
        title_orig = row[4].text_content()

        tags = [self.tags_map.get(t) for t
                in (row[5].text_content(), row[6].text_content())]

        url_booking = row[8].link()
        price = parsers.price(row[7].text_content())

        return Showtime(
            cinema=cinema,
            film_scraped=ScrapedFilm(
                title_main=title_main,
                titles=[title_main, title_orig],
            ),
            starts_at=starts_at,
            tags=tags,
            url_booking=url_booking,
            price=price,
        )
