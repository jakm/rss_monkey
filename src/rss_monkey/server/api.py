#-*- coding: utf8 -*-

from fastjsonrpc.server import JSONRPCServer
from zope.interface.interface import Method

from rss_monkey.common.context import AppContext
from rss_monkey.common.utils import defer_to_thread


class ApiResourceFactory(object):
    def __init__(self, api_name, interface):
        def api_init(self, service):
            if not interface.providedBy(service):
                raise TypeError('Service object has to implement %s'
                                 % self.interface.__class__.__name__)

            self.interface = interface
            self.service = service

        @defer_to_thread
        def wrapper(self, method_name, *args, **kw):
            method = getattr(self.service, method_name)
            return method(*args, **kw)

        method_names = [name for name in list(interface)
                        if isinstance(interface.get(name), Method)]

        methods = {'__init__': api_init}
        for method_name in method_names:
            methods['jsonrpc_' + method_name] = lambda self_, *args, **kw: wrapper(self_, method_name, *args, **kw)

        self.api_class = type(api_name, (object, JSONRPCServer), methods)

    def __call__(self, service):
        return self.api_class(service)


class RssResourceFactory(object):
    api_factory = None

    def __call__(self, user_id):
        service = AppContext.get_object('rss_service')
        service.user_id = user_id
        return self.api_factory(service)
