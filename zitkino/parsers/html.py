# -*- coding: utf-8 -*-


import lxml.html
from lxml import etree

from zitkino.utils import clean_whitespace


class HTMLElement(lxml.html.HtmlElement):

    def text_content(self, whitespace=False):
        """Returns text content, by default with normalized whitespace."""
        text = super(HTMLElement, self).text_content()
        if whitespace:
            return text
        return clean_whitespace(text)

    def links(self):
        """Returns iterable of URL addresses present in element."""
        self.make_links_absolute()
        for element, attribute, link, pos in self.iterlinks():
            yield link

    def link(self):
        """Returns the first URL address present in element."""
        for link in self.links():
            return link
        return None

    def split(self, tag, wrapper='div'):
        """Splits element's children into sets and returns these sets
        wrapped in newly created HTML elements (wrapper's tag can be
        specified).
        """
        wrapper_el = self._make_element(wrapper)
        for child in self:
            if child.tag.lower() == tag.lower():
                yield wrapper_el
                wrapper_el = self._make_element(wrapper)
            else:
                wrapper_el.append(child)

    def _make_element(self, tag):
        """Creates brand new HTML element, which inherits behavior of
        the current one (including ``base_url``, etc.).
        """
        return html('<{0} />'.format(tag), base_url=self.base_url)


def HTMLParser(*args, **kwargs):
    lookup = etree.ElementDefaultClassLookup(element=HTMLElement)
    parser = etree.HTMLParser(*args, **kwargs)
    parser.set_element_class_lookup(lookup)
    return parser


_html_parser = HTMLParser()  # default HTML parser


def html(text, base_url=None):
    """Takes text and returns HTML tree."""
    return lxml.html.fromstring(text, parser=_html_parser, base_url=base_url)
