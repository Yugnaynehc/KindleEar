#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
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
    # astheadfile = ""
    # coverfile = ""
    # fulltext_by_readability = False
    oldest_article        = 1
    feeds = [
            (u'cs.CV', 'http://export.arxiv.org/rss/cs.CV', True),
            (u'cs.AI', 'http://export.arxiv.org/rss/cs.AI', True),
           ]

    def ParseFeedUrls(self):
        """ return list like [(section,title,url,desc),..]
        desc = authors + arxiv_abs + content
        """
        urls = []
        tnow = datetime.datetime.utcnow()
        urladded = set()

        for feed in self.feeds:
            section, url = feed[0], feed[1]
            isfulltext = feed[2] if len(feed) > 2 else False
            timeout = self.timeout+10 if isfulltext else self.timeout
            opener = URLOpener(self.host, timeout=timeout, headers=self.extra_header)
            result = opener.open(url)
            if result.status_code == 200 and result.content:
                #debug_mail(result.content, 'feed.xml')

                if self.feed_encoding:
                    try:
                        content = result.content.decode(self.feed_encoding)
                    except UnicodeDecodeError:
                        content = AutoDecoder(True).decode(result.content,opener.realurl,result.headers)
                else:
                    content = AutoDecoder(True).decode(result.content,opener.realurl,result.headers)
                feed = feedparser.parse(content)

                for e in feed['entries'][:self.max_articles_per_feed]:
                    updated = None
                    if hasattr(e, 'updated_parsed') and e.updated_parsed:
                        updated = e.updated_parsed
                    elif hasattr(e, 'published_parsed') and e.published_parsed:
                        updated = e.published_parsed
                    elif hasattr(e, 'created_parsed'):
                        updated = e.created_parsed

                    if self.oldest_article > 0 and updated:
                        updated = datetime.datetime(*(updated[0:6]))
                        delta = tnow - updated
                        if self.oldest_article > 365:
                            threshold = self.oldest_article #以秒为单位
                        else:
                            threshold = 86400*self.oldest_article #以天为单位

                        if delta.days*86400+delta.seconds > threshold:
                            self.log.info("Skip old article(%s): %s" % (updated.strftime('%Y-%m-%d %H:%M:%S'),e.link))
                            continue

                    #支持HTTPS
                    if hasattr(e, 'link'):
                        if url.startswith('https://'):
                            urlfeed = e.link.replace('http://','https://')
                        else:
                            urlfeed = e.link

                        if urlfeed in urladded:
                            continue
                    else:
                        urlfeed = ''

                    authors = e['creator']
                    arxiv_abs = e['id']

                    desc = None
                    if isfulltext:
                        summary = e.summary if hasattr(e, 'summary') else None
                        desc = e.content[0]['value'] if (hasattr(e, 'content')
                            and e.content[0]['value']) else None

                        #同时存在，因为有的RSS全文内容放在summary，有的放在content
                        #所以认为内容多的为全文
                        if summary and desc:
                            desc = summary if len(summary) > len(desc) else desc
                        elif summary:
                            desc = summary

                        if not desc:
                            if not urlfeed:
                                continue
                            else:
                                self.log.warn('Fulltext feed item no has desc,link to webpage for article.(%s)' % e.title)
                    desc = authors + arxiv_abs + desc   # add by Yangyu Chen
                    urls.append((section, e.title, urlfeed, desc))
                    urladded.add(urlfeed)
            else:
                self.log.warn('fetch rss failed(%s):%s'%(URLOpener.CodeMap(result.status_code), url))

        return urls
