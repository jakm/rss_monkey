# -*- coding: utf8 -*-

import feedparser


class FeedParser(object):
    def __init__(self, url):
        self.url = url

    def parse(self, modified=None):
        feed = feedparser.parse(self.url, modified=modified)

        if feed.bozo:
            return  # TODO: logovani chyby

        channel = {
            'url': feed.channel.url,
            'title': feed.channel.title,
            'link': feed.channel.link,
            'description': feed.channel.description,
            'modified': None
        }

        if 'date' in feed:
            channel['modified'] = feed.date_parsed
        elif 'modified' in feed:
            channel['modified'] = feed.modified_parsed
        else:
            if feed.entries:
                channel['modified'] = feed.entries[0].date_parsed

        entries = [{
            'title': entry.title,
            'summary': entry.summary,
            'link': entry.link,
            'date': entry.date_parsed
        } for entry in feed.entries]

        return channel, entries
