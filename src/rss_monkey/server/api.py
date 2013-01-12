#-*- coding: utf8 -*-

from fastjsonrpc.server import JSONRPCServer
from zope.interface.interface import Method

from rss_monkey.common.context import AppContext


class ApiResourceFactory(object):
    def __init__(self, api_name, interface):
        self.api_name = api_name
        self.interface = interface

        methods = self.create_methods()
        self.api_class = type(self.api_name, (object, JSONRPCServer), methods)

    def __call__(self, service):
        return self.api_class(service)

    def create_methods(self):
        def api_init(self_, service):
            if not self.interface.providedBy(service):
                raise TypeError('Service object has to implement %s'
                                 % self_.interface.__class__.__name__)

            self_.interface = self.interface
            self_.service = service

        method_names = [name for name in list(self.interface)
                        if isinstance(self.interface.get(name), Method)]

        methods = {'__init__': api_init}

        for method_name in method_names:
            methods['jsonrpc_' + method_name] = self.create_method(method_name)

        return methods

    def create_method(self, method_name):
        def wrapper(self_, *args, **kw):
            method = getattr(self_.service, method_name)
            return method(*args, **kw)
        wrapper.__name__ = method_name

        doc = self.interface.get(method_name).getDoc()
        if doc:
            wrapper.__doc__ = (
                "\nWarning! This wrapper method returns a Deferred!\n\n" + doc)

        return wrapper


class RssResourceFactory(object):
    api_factory = None

    def __call__(self, user_id):
        service = AppContext.get_object('rss_service')
        service.user_id = user_id
        return self.api_factory(service)
