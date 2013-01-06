# -*- coding: utf8 -*-

import base64
import logging
import new
from fastjsonrpc.client import Proxy
from fastjsonrpc.jsonrpc import VERSION_2
from twisted.internet import reactor
from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import Agent
from zope.interface import Interface
from zope.interface.interface import Method


LOG = logging.getLogger()


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


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

        method_names = [name for name in list(self.interface)
                        if isinstance(self.interface.get(name), Method)]

        def create_method(method_name):
            # create function object
            def wrapper(self_, *args, **kw):
                if self_.proxy is None:
                    raise ValueError('Proxy is not set.')

                return self.proxy.callRemote(method_name, *args, **kw)
            wrapper.__name__ = method_name

            doc = self.interface.get(method_name).getDoc()
            if doc:
                wrapper.__doc__ = (
                    "\nWarning! This wrapper method returns a Deferred!\n\n"
                    + doc)

            # bound it with instance
            method = new.instancemethod(wrapper, self, self.__class__)

            return method

        for method_name in method_names:
            method = create_method(method_name)
            setattr(self, method_name, method)

    def _connect(self, url, login=None, passwd=None, protocol='http'):
        """
        Connect proxy object to RPC server.

        @param url str, URL address of RPC server
        @param login str, User name
        @param passwd str, User's password
        @param protocol str, 'http' or 'https'
        """

        agent = None
        if protocol == 'https':
            agent = Agent(reactor, WebClientContextFactory())

        extra_headers = {}
        if login:
            if passwd is None:
                passwd = ''
            basic_auth = base64.encodestring('%s:%s' % (login, passwd))
            auth_header = "Basic " + basic_auth.strip()
            extra_headers['Authorization'] = [auth_header]

        self.proxy = Proxy(url, VERSION_2, agent=agent, extra_headers=extra_headers)

    def _close(self):
        """
        Close connection.
        """
        self.proxy = None
