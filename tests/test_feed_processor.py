# -*- coding: utf8 -*-

import os
import tempfile
from twisted.enterprise import adbapi
from twisted.internet import defer
from twisted.trial import unittest

from rss_monkey.common.db import Db
from rss_monkey.feed_processor import FeedProcessor

# COMPARE WITH create_tables.sql!!!

FEEDS_COMMAND = '''CREATE TABLE `feeds` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `url` TEXT UNIQUE,
    `title` TEXT,
    `description` TEXT,
    `link` TEXT,
    `modified` TEXT
    )'''

FEED_ENTRIES_COMMAND = '''CREATE TABLE `feed_entries` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `feed_id` INT,
    `title` TEXT,
    `summary` TEXT,
    `link` TEXT,
    `date` TEXT,
    CONSTRAINT `feed_entries_ibfk_1` FOREIGN KEY (`feed_id`) REFERENCES `feeds` (`id`)
    )'''


class ProcessFeedTest(unittest.TestCase):

    @defer.inlineCallbacks
    def setUp(self):

        self.db_filename = tempfile.mktemp('.sqlite', 'rss_monkey_', '/tmp')

        self.db_pool = adbapi.ConnectionPool('sqlite3',
                                             self.db_filename,
                                             check_same_thread=False)
        self.db = Db(self.db_pool)

        try:
            yield self.db_pool.runOperation(FEEDS_COMMAND)
            yield self.db_pool.runOperation(FEED_ENTRIES_COMMAND)
        except Exception as e:
            self.fail('Cannot create test database: %s' % str(e))

    def tearDown(self):
        os.unlink(self.db_filename)

    def get_feed_processor(self):
        processor = FeedProcessor()
        processor.db = self.db
        return processor

    @defer.inlineCallbacks
    def test_get_one_feed(self):
        # store feed to test database
        url = 'http://www.abclinuxu.cz/auto/zpravicky.rss'
        feed_id = yield self.db.add_feed(url)

        # test FeedProcessor
        processor = self.get_feed_processor()
        yield processor.process_feed(feed_id)

        # check result
        feed = yield self.db.get_feed(feed_id)
        self.assertTrue(feed['title'], 'Feed was not updated')

    @defer.inlineCallbacks
    def test_process_feeds(self):
        # prepare test feeds
        feed_urls = ['http://www.abclinuxu.cz/auto/zpravicky.rss',
                     'http://www.root.cz/rss/zpravicky/']
        feed_ids = []
        for url in feed_urls:
            feed_id = yield self.db.add_feed(url)
            feed_ids.append(feed_id)

        # test FeedProcessor
        processor = self.get_feed_processor()
        yield processor.process_feeds()

        # check results
        for feed_id in feed_ids:
            feed = yield self.db.get_feed(feed_id)
            self.assertTrue(feed['title'],
                            'Feed was not updated (url: %s)' % feed['url'])

            res = yield self.db.get_entries(feed_id)
            entries = tuple(res)
            self.assertGreater(len(entries), 0,
                              'Entries were not stored (url: %s)' % feed['url'])
