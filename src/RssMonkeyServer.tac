# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import app_context

LOG = logging.getLogger('FeedProcessorService')


app_context.install_context(app_context.RssMonkeyServerConfig())

top_service = service.MultiService()

web_api = app_context.AppContext.get_object('web_api')
web_api.setServiceParent(top_service)

application = service.Application('rss_monkey_server')
top_service.setServiceParent(application)
