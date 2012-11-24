#-*- coding: utf8 -*-

import new
from fastjsonrpc.server import JSONRPCServer
from zope.interface import interface

from rss_monkey.common.app_context import AppContext
from rss_monkey.common.utils import defer_to_thread
from rss_monkey.server.service import IRssService


class WebApi(JSONRPCServer):
    def __init__(self):
        """
        Creates new service and register its methods for RPC.
        """
        self.service = AppContext.get_object('rss_service')
        if not IRssService.providedBy(self.service):
            raise TypeError('Service object has to implement IRssService')

        self.service_methods = {}

        self._extend_with_service_methods()

    def _extend_with_service_methods(self):
        method_names = [name for name in list(IRssService)
                        if isinstance(IRssService.get(name), interface.Method)]

        @defer_to_thread
        def wrapper(method_name, *args, **kw):
            return self.service_methods[method_name](*args, **kw)

        def wrap_method(method_name):
            orig_method = getattr(self.service, method_name)
            self.service_methods[method_name] = orig_method

            def wrapped(self, *args, **kw):
                return wrapper(method_name, *args, **kw)
            wrapped.__name__ = method_name

            return wrapped

        for method_name in method_names:
            orig_method = getattr(self.service, method_name)
            self.service_methods[method_name] = orig_method

            method = wrap_method(method_name)

            method.__doc__ = 'Warning! Method wrapper returns deferred!\n'
            doc = IRssService.get(method_name).getDoc()
            if doc:
                method.__doc__ += doc

            self._add_method(method, 'jsonrpc_' + method_name)

    def _add_method(self, func, method_name):
        method = new.instancemethod(func, self, self.__class__)
        setattr(self, method_name, method)
