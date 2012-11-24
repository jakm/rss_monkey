# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import app_context

LOG = logging.getLogger('FeedProcessorService')


app_context.install_context(app_context.AppConfig())

top_service = service.MultiService()

# set web api service
web_api = app_context.AppContext.get_object('web_api_service')
web_api.setServiceParent(top_service)

# set feed processor services
feed_service = service.MultiService()
feed_service.setServiceParent(top_service)

srv = app_context.AppContext.get_object('feed_processor_service')
srv.setServiceParent(feed_service)

rpc = app_context.AppContext.get_object('feed_processor_rpc_service')
rpc.setServiceParent(feed_service)

# start server
application = service.Application('rss_monkey_server')
top_service.setServiceParent(application)
