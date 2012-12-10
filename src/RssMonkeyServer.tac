# -*- coding: utf8 -*-

import logging
from twisted.application import service

from rss_monkey.common import app_context

LOG = logging.getLogger('FeedProcessorService')

app_context.install_context(app_context.AppConfig())


def set_service(service_name, parent):
    service = app_context.AppContext.get_object(service_name)
    service.setServiceParent(parent)
    return service


top_service = service.MultiService()

# set web api service
set_service('web_api_service', top_service)

# set registration service
set_service('registration_service', top_service)

# set feed processor services
feed_service = service.MultiService()
feed_service.setServiceParent(top_service)

set_service('feed_processor_service', feed_service)

set_service('feed_processor_rpc_service', feed_service)

# start server
application = service.Application('rss_monkey_server')
top_service.setServiceParent(application)
