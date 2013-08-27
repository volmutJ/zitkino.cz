# -*- coding: utf-8 -*-

from zitkino import parsers
from zitkino.utils import download
from zitkino.models import Cinema, Showtime, ScrapedFilm

from . import scrapers
import os
import tempfile
import re
import times

cinema = Cinema(
    name=u'Letní kino MDB',
    url='http://www.letnikinobrno.cz',
    street=u'Lidická 12',
    town=u'Brno',
    coords=(49.2011200, 16.6078831)
)

@scrapers.register(cinema)
class Scraper(object):
    url = 'http://www.letnikinobrno.cz/program/'
    starts_at = 21.00
    tags_map = {
    }

    additional_info_re = re.compile(r'''
            \s+                         #first space
            (?P<countries>(\D+))        #countries
            \s*\|\s*                    #separator
            (?P<year>\d+)               #year
            \s*\|\s*                    #separator
            (?P<length>\d+)             #length
            \s*min\s*\|\s*žánr:\s*      #separator & crap
            (?P<genre>\D+)              #genre
            \s*\|\s*režie:\s*           #separator & crap
            (?P<director>\D+)           #director
            ''', re.U | re.X)

    info_re = re.compile(r'''
            (?P<date>\d{1,2}\.\d{1,2}\.)
            \s+
            (?P<title>.*?)
            \s+
            (?P<price>\d+)
            ''', re.U | re.X)
    
    def __call__(self):
        resp = download(self.url)
        html = parsers.html(resp.content, base_url=self.url)
        links = html.cssselect("#right a")
        if(links[0] is not None):
            return self._scrape_pdf(url=cinema.url + links[0].get('href'))


	
    def _scrape_pdf(self, url):
        actual_month_pdf = download(url).content
        temp_file = open(tempfile.gettempdir() + "/letnikonomdb_temp.pdf", "w")
        temp_file.write(actual_month_pdf)
        temp_file.close()
        temp_result = tempfile.NamedTemporaryFile(delete=True)
        
        #exec pdftotext
        os.system('pdftotext -layout -enc "UTF-8" ' + temp_file.name + ' ' + temp_result.name)

        text = temp_result.read()
        head = re.findall(r"(\d{1,2}\.\d{1,2}\.\s.*?\s+\d+)", text, re.U)    #header of entry

        #info about entry
        info = re.findall(
            r"( \S\D+\s*\|\s*\d+\s*\|\s*\d+\s*min\s*\|\s*žánr:\s*\D+\s*\|\s*režie:\s*(?:\S+\s)*)",
            text, re.U)

        temp_result.close()
        if (len(head) == len(info) != 0):
            #put head and info together and parse
            for i, j in enumerate(head):
                yield self._parse_row(head[i], info[i])

    def _parse_row(self, info, additional_info):
        info_parsed = self.info_re.match(info)

        if info_parsed:
            #insert space between dot and second number
            date = re.sub(
            r"(\d+\.)(\d+\.)", 
            r"\1 \2", 
            info_parsed.group("date").strip(), 
            0, re.U | re.X)
            
            starts_at = parsers.date_time_year(date, self.starts_at)
            title_main = info_parsed.group("title")
            price = int(info_parsed.group("price"))

        a_info_parsed = self.additional_info_re.match(additional_info)
        
        if a_info_parsed:
            countries = [c.strip() for c in a_info_parsed.group("countries").split("/")]
            year = int(a_info_parsed.group("year"))
            length = int(a_info_parsed.group("length"))
            genre = [genre.strip() for genre in a_info_parsed.group("genre").split("/")]
            director = a_info_parsed.group("director")

        tags = []

        return Showtime(
            cinema=cinema,
            film_scraped=ScrapedFilm(
                title_main=title_main,
                titles=[title_main],
                year=year,
                length=length,
            ),
            starts_at=starts_at,
            tags=tags,
            price=price,
        )

        
