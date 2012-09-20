# -*- coding: utf-8 -*-

import re
import json
import requests
from bs4 import BeautifulSoup


### Abstract base scraper ###


class Scraper(object):
    """Base scraper class."""

    url = ''

    def __init__(self, user_agent=None):
        self.user_agent = user_agent

    def _download(self, url, **params):
        """Download data document (HTML, JSON, whatever)."""
        if not url:
            classname = self.__class__.__name__
            raise ValueError('No URL for scraper {0}.'.format(classname))

        headers = {'User-Agent': self.user_agent}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response

    def _decode(self, content):
        """Decode document's contents, return data structure."""
        raise NotImplementedError

    def _parse(self, decoded_content, response=None):
        """Parse decoded content and return results."""
        raise NotImplementedError

    def scrape(self):
        """Download data, parse it, return results."""
        response = self._download(self.url)
        content = self._decode(response.content)
        return self._parse(content, response)


### Decoding mixins ###


class SoupDecoder(object):
    """Scraper mixin for processing HTML documents."""

    _whitespace_re = re.compile(r'\s+')

    def _decode(self, content):
        """Turn content into HTML soup."""
        return BeautifulSoup(self._whitespace_re.sub(' ', content))


class JsonDecoder(object):
    """Scraper mixin for processing JSON documents."""

    def _decode(self, content):
        """Turn JSON content into Python dict."""
        return json.loads(content)
