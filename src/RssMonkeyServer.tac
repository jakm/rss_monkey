# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import context
from rss_monkey.server import config

LOG = logging.getLogger('FeedProcessorService')

context.install_context(config.AppConfig())


def set_service(service_name, parent):
    service = context.AppContext.get_object(service_name)
    service.setServiceParent(parent)
    return service


top_service = service.MultiService()

# set web api server
set_service('web_api_server', top_service)

# set feed processor services
feed_service = service.MultiService()
feed_service.setServiceParent(top_service)

set_service('feed_processor_service', feed_service)

set_service('feed_processor_rpc_server', feed_service)

# start server
application = service.Application('rss_monkey_server')
top_service.setServiceParent(application)
