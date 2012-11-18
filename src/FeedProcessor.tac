# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import app_context

LOG = logging.getLogger('FeedProcessorService')


app_context.install_context(app_context.FeedProcessorConfig())

top_service = service.MultiService()

srv = app_context.AppContext.get_object('feed_processor_service')
srv.setServiceParent(top_service)

rpc = app_context.AppContext.get_object('feed_processor_rpc_server')
rpc.setServiceParent(top_service)

application = service.Application('feed_processor')
top_service.setServiceParent(application)
