# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import app_context

LOG = logging.getLogger('FeedProcessorService')


class FeedProcessorService(service.Service):
    def __init__(self):
        app_context.install_default()
        self.feed_processor = app_context.AppContext.get_object('feed_processor')

    def startService(self):
        LOG.info('Starting FeedProcessor')
        service.Service.startService(self)
        return self.feed_processor.plan_jobs()

    def stopService(self):
        LOG.info('Stopping FeedProcessor')
        self.feed_processor.task.stop()
        service.Service.stopService(self)


feed_processor_service = FeedProcessorService()
application = service.Application('feed_processor')
feed_processor_service.setServiceParent(application)
