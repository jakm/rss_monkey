# -*- coding: utf8 -*-

import logging
import new
from fastjsonrpc.client import Proxy
from fastjsonrpc.jsonrpc import VERSION_2
from twisted.cred.credentials import Anonymous, UsernamePassword
from twisted.internet.ssl import ClientContextFactory
from zope.interface import Interface
from zope.interface.interface import Method

from rss_monkey.client.config import Config

LOG = logging.getLogger(__name__)


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


class JsonRpcProxy(object):
    """
    Client proxy using JSON-RPC.
    """
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
            wrapper.__doc__ = self.interface.get(method_name).getDoc()

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

        timeout = int(Config().get('connection', 'timeout'))

        if not login:
            credentials = Anonymous()
        else:
            credentials = UsernamePassword(login, passwd)

        if protocol == 'https':
            self.proxy = Proxy(url, VERSION_2, credentials=credentials,
                               contextFactory=WebClientContextFactory(),
                               connectTimeout=timeout)
        else:
            self.proxy = Proxy(url, VERSION_2, credentials=credentials,
                               connectTimeout=timeout)

    def _close(self):
        """
        Close connection.
        """
        self.proxy = None
