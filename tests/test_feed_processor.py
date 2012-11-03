# -*- coding: utf8 -*-

# uncomment for logging function calls by @log_function_call
# import logging
# logging.basicConfig(level=logging.INFO)

from twisted.trial import unittest

from rss_monkey.db import SyncDb
from rss_monkey.app_context import AppContext
from rss_monkey.feed_processor import FeedProcessor
from rss_monkey.model import Feed

from utils import ContainerMock, DbMock


class ProcessFeedTest(unittest.TestCase):

    def setUp(self):
        # prepare mock database object
        self.db = DbMock(SyncDb, Feed.metadata)

        # prepare mock application context
        objects = {
            'sync_db': lambda _: self.db,
        }
        container = ContainerMock(objects)
        AppContext.install(container.get_context())

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
        processor.process_feed(feed_id)

        # check result
        updated_feed = self.db.load(Feed, feed_id)
        self.assertTrue(updated_feed.title, 'Feed were not updated')

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
        dl = processor.process_feeds()

        def check_result(result):
            for res in result:
                if not res[0]:
                    failure = res[1]
                    self.fail('%s: %s' % (failure.type.__name__,
                                          failure.getErrorMessage()))

            for feed_id in feed_ids:
                updated_feed = self.db.load(Feed, feed_id)
                self.assertTrue(updated_feed.title,
                    'Feed were not updated (url: %s)' % updated_feed.url)
                self.assertGreater(len(updated_feed.entries), 0,
                    'Entries were not stored (url: %s)' % updated_feed.url)

        dl.addCallback(check_result)
        return dl