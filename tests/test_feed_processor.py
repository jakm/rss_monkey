# -*- coding: utf8 -*-

# uncomment for logging function calls by @log_function_call
# import logging
# logging.basicConfig(level=logging.INFO)

from twisted.trial import unittest

from rss_monkey.common.db import Db
from rss_monkey.common.model import Feed
from rss_monkey.feed_processor import FeedProcessor

from utils import DbMock


class ProcessFeedTest(unittest.TestCase):

    def setUp(self):
        # prepare mock database object
        self.db = DbMock(Db, Feed.metadata)

    def test_get_one_feed(self):
        #setup_debug_logging()

        feed = Feed()
        feed.url = 'http://www.abclinuxu.cz/auto/zpravicky.rss'

        # store test feed to mock database
        self.db.store(feed)
        self.db.commit()

        feed_id = feed.id

        # test FeedProcessor
        processor = FeedProcessor()
        processor.db = self.db
        processor.process_feed(feed_id)

        # check result
        updated_feed = self.db.load(Feed, id=feed_id)
        self.assertTrue(updated_feed.title, 'Feed was not updated')

    def test_process_feeds(self):

        # prepare test feeds
        feed_urls = ['http://www.abclinuxu.cz/auto/zpravicky.rss',
                     'http://www.root.cz/rss/zpravicky/']
        feed_ids = []
        for url in feed_urls:
            feed = Feed()
            feed.url = url
            # store test feed to mock database
            self.db.store(feed, commit=True)
            feed_ids.append(feed.id)

        # test FeedProcessor
        processor = FeedProcessor()
        processor.db = self.db
        dl = processor.process_feeds()

        def check_result(result):
            for res in result:
                if not res[0]:
                    failure = res[1]
                    self.fail('%s: %s' % (failure.type.__name__,
                                          failure.getErrorMessage()))

            for feed_id in feed_ids:
                updated_feed = self.db.load(Feed, id=feed_id)
                self.assertTrue(updated_feed.title,
                    'Feed was not updated (url: %s)' % updated_feed.url)
                self.assertGreater(len(updated_feed.entries), 0,
                    'Entries were not stored (url: %s)' % updated_feed.url)

        dl.addCallback(check_result)
        return dl
