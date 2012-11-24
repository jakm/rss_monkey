# -*- coding: utf8 -*-

import new
from fastjsonrpc.client import Proxy
from fastjsonrpc.jsonrpc import VERSION_2
from zope.interface import Interface, interface


class JsonRpcProxy(object):
    proxy = None

    def __init__(self, interface):
        """
        Initialize proxy with interface methods.

        @param interface type, Interface class - must be subclass of zope.interface.Interface
        """
        if not issubclass(interface, Interface):
            raise ValueError('Parameter has to be the Interface.')
        self.interface = interface

        self._extend_with_interface_methods()

    def _extend_with_interface_methods(self):
        method_names = [name for name in list(self.interface)
                        if isinstance(self.interface.get(name), interface.Method)]

        def wrapper(method_name, *args, **kw):
            if self.proxy is None:
                raise ValueError('Proxy is not set')
            return self.proxy.callRemote(method_name, *args, **kw)

        def wrap_method(method_name):
            def wrapped(self, *args, **kw):
                return wrapper(method_name, *args, **kw)
            wrapped.__name__ = method_name
            return wrapped

        for method_name in method_names:
            method = wrap_method(method_name)

            method.__doc__ = 'Warning! Method wrapper returns deferred!\n'
            doc = self.interface.get(method_name).getDoc()
            if doc:
                method.__doc__ += doc

            self._add_method(method, method_name)

    def _add_method(self, func, method_name):
        method = new.instancemethod(func, self, self.__class__)
        setattr(self, method_name, method)

    def _connect(self, url):
        """
        Connect proxy object to RPC server.

        @param url str, URL address of RPC server
        """
        self.proxy = Proxy(url, VERSION_2)

    def _close(self):
        """
        Close connection.
        """
        self.proxy = None
