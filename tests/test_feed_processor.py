# -*- coding: utf8 -*-

# uncomment for logging function calls by @log_function_call
# import logging
# logging.basicConfig(level=logging.INFO)

from twisted.trial import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool

from rss_monkey.common.db import DbRegistry
from rss_monkey.common.model import Feed
from rss_monkey.feed_processor import FeedProcessor


class ProcessFeedTest(unittest.TestCase):

    def setUp(self):
        engine = create_engine('sqlite:///:memory:',
                               connect_args={'check_same_thread': False},
                               poolclass=StaticPool)

        Feed.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)

        self.db_registry = DbRegistry()
        self.db_registry.session_registry = scoped_session(Session)
        self.db = self.db_registry()

    def get_feed_processor(self):
        processor = FeedProcessor()
        processor.db_registry = self.db_registry
        return processor

    def test_get_one_feed(self):
        feed = Feed()
        feed.url = 'http://www.abclinuxu.cz/auto/zpravicky.rss'

        # store test feed to mock database
        self.db.store(feed)
        self.db.commit()

        feed_id = feed.id

        # test FeedProcessor
        processor = self.get_feed_processor()
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
        processor = self.get_feed_processor()
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
