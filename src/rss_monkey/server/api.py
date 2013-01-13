#-*- coding: utf8 -*-

from fastjsonrpc.server import JSONRPCServer
from zope.interface.interface import Method

from rss_monkey.common.context import AppContext


class ApiResourceFactory(object):
    """
    Factory class that generate new objects with passed interface and services
    """
    def __init__(self, api_name, interface):
        """
        Initialize factory. As side effect is created new <<class>> and stored
        in self.api_class. This type inherits JSONRPCServer.

        @param api_name str, Name of new <<class>> object
        @param interface zope.interface.Interface, Interface of new <<class>> object
        """
        self.api_name = api_name
        self.interface = interface

        methods = self.create_methods()
        self.api_class = type(self.api_name, (object, JSONRPCServer), methods)

    def __call__(self, service):
        """
        Create new object of <<class>> self.api_class and initialize it with
        service.

        @param service object, Service implementing self.interface
        @return New instance of self.api_class
        """
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
        wrapper.__doc__ = self.interface.get(method_name).getDoc()

        return wrapper


class RssResourceFactory(object):
    """
    Factory class that generate new RssService objects and initialize them
    """
    api_factory = None

    def __call__(self, user_id):
        """
        Create new RssService instance and initialize it with user_id

        @param user_id int
        """
        service = AppContext.get_object('rss_service')
        service.user_id = user_id
        return self.api_factory(service)
