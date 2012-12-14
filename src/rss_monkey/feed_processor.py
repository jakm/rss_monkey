# -*- coding: utf8 -*-

import feedparser
import logging

from datetime import datetime
from fastjsonrpc.server import JSONRPCServer
from twisted.application import service
from twisted.internet import defer, task, threads

from rss_monkey.common.context import AppContext
from rss_monkey.common.model import Feed, FeedEntry
from rss_monkey.common.utils import log_function_call

logging.basicConfig()
LOG = logging.getLogger(__name__)


class FeedParser(object):
    def __init__(self, url):
        self.url = url

    @log_function_call(log_result=False)
    def parse(self, modified=None):
        feed = feedparser.parse(self.url,
            modified=self._datetime_to_time_struct(modified))

        if feed.bozo:
            raise feed.bozo_exception

        channel = {
            'url': feed.url,
            'title': feed.channel.title,
            'link': feed.channel.link,
            'description': feed.channel.description,
            'modified': None
        }

        if 'date' in feed:
            channel['modified'] = feed.date_parsed
        elif 'modified' in feed:
            channel['modified'] = feed.modified_parsed
        elif 'published' in feed:
            channel['modified'] = feed.published_parsed
        elif 'updated' in feed:
            channel['modified'] = feed.updated_parsed
        else:
            if feed.entries:
                if 'modified' in feed.entries[0]:
                    channel['modified'] = feed.entries[0].date_parsed
                elif 'published' in feed.entries[0]:
                    channel['modified'] = feed.entries[0].published_parsed
                elif 'updated' in feed.entries[0]:
                    channel['modified'] = feed.entries[0].updated_parsed

        if channel['modified'] is not None:
            channel['modified'] = self._time_struct_to_datetime(channel['modified'])

        entries = []
        for record in feed.entries:
            entry = {'title': record.title,
                      'summary': record.summary,
                      'link': record.link,
                      'date': None}
            if 'date' in record:
                entry['date'] = record.date_parsed
            elif 'published' in record:
                entry['date'] = record.published_parsed

            if entry['date'] is not None:
                entry['date'] = self._time_struct_to_datetime(entry['date'])

            entries.append(entry)

        LOG.debug('Got %d new feeds from %s since %s',
            len(entries), self.url, channel['modified'].isoformat(' '))

        return channel, entries

    def _datetime_to_time_struct(self, date_time):
        if date_time:
            return date_time.timetuple()

    def _time_struct_to_datetime(self, date_time):
        if date_time:
            return datetime(date_time.tm_year, date_time.tm_mon, date_time.tm_mday,
                date_time.tm_hour, date_time.tm_min, date_time.tm_sec)


class FeedProcessor(object):
    db = None
    download_interval = None
    download_timeout = None  # TODO: timeout!!!
    task = None

    @log_function_call()
    def schedule_jobs(self):
        if self.task:
            raise Exception('Task is planned') # TODO: konkretni vyjimka

        self.task = task.LoopingCall(self.process_feeds)
        return self._start_task()

    @log_function_call()
    def reschedule(self):
        self.stop_jobs()
        return self._start_task()

    @log_function_call()
    def stop_jobs(self):
        if self.task and self.task.running:
            self.task.stop()

    @log_function_call()
    def process_feeds(self):
        feed_ids = self._get_feed_ids()

        defers = []
        for feed_id in feed_ids:
            d = threads.deferToThread(self.process_feed, feed_id)
            d.addErrback(self.errback, feed_id)
            defers.append(d)

        return defer.DeferredList(defers)

    @log_function_call()
    def _start_task(self):
        return self.task.start(self.download_interval)

    @log_function_call()
    def _get_feed_ids(self):
        return (res[0] for res in self.db.query(Feed.id).all())

    @log_function_call()
    def process_feed(self, feed_id):
        feed = self.get_feed_from_db(feed_id)
        data = self.download_feed(feed)
        self.update_feed(feed, data)

    @log_function_call()
    def get_feed_from_db(self, feed_id):
        return self.db.load(Feed, id=feed_id)

    @log_function_call(log_result=False)
    def download_feed(self, feed):
        parser = FeedParser(feed.url)
        data = parser.parse(modified=feed.modified)
        return data

    @log_function_call(log_params=False)
    def update_feed(self, feed, data):
        channel = data[0]

        if feed.modified is None:
            LOG.debug('Feed %d: storing channel data', feed.id)
            feed.title = channel['title']
            feed.description = channel['description']
            feed.link = channel['link']

        # have to store always
        feed.modified = channel['modified']

        records = data[1]
        for record in records:
            entry = FeedEntry(title=record['title'],
                              summary=record['summary'],
                              link=record['link'],
                              date=record['date'])
            feed.add_entry(entry)

        self.db.commit()

    @log_function_call()
    def errback(self, failure, feed_id):
        LOG.error('Can not download feed %d: %s', feed_id, failure.getErrorMessage())


class FeedProcessorService(service.Service):
    feed_processor = None

    def startService(self):
        LOG.info('Starting FeedProcessor')
        service.Service.startService(self)
        return self.feed_processor.schedule_jobs()

    def stopService(self):
        LOG.info('Stopping FeedProcessor')
        self.feed_processor.stop_jobs()
        service.Service.stopService(self)


class FeedProcessorRpcServer(JSONRPCServer):
    feed_processor = None

    @log_function_call()
    def jsonrpc_reload_feeds(self):
        self.feed_processor.reschedule()
