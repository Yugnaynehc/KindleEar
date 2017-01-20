#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import requests
from lib import feedparser
from base import BaseFeedBook
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder


def getBook():
    return ArxivDaily


class ArxivDaily(BaseFeedBook):
    title                 = "ArxivDaily"
    description           = "arXiv daily on CV and AI"
    language              = "en"
    feed_encoding         = "utf-8"
    page_encoding         = "utf-8"
    # mastheadfile = ""
    # coverfile = ""
    # fulltext_by_readability = False
    # oldest_article        = 1
    feeds = [
            ("cs.CV", "http://export.arxiv.org/rss/cs.CV", True),
            ("cs.AI", "http://export.arxiv.org/rss/cs.AI", True),
           ]

    def ParseFeedUrls(self):
        """ return list like [(section,title,url,article),..] """
        urls = []
        urladded = set()

        for feed in self.feeds:
            section, url = feed[0], feed[1]
            isfulltext = feed[2] if len(feed) > 2 else False
            result = requests.get(url)
            if result.status_code == 200 and result.content:
                content = result.content.decode(self.feed_encoding)
                feed = feedparser.parse(content)
                for e in feed['entries'][:self.max_articles_per_feed]:
                    authors = e.author
                    arxiv_abs = e.link
                    desc = e.summary
                    article = authors + arxiv_abs + desc
                    urls.append((section, e.title, arxiv_abs, article))
                    urladded.add(arxiv_abs)
            else:
                self.log.warn('fetch rss failed: %s' % url)

        return urls
