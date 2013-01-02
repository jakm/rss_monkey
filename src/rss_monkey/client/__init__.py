# -*- coding: utf8 -*-

from urllib2 import urlparse

from twisted.internet import defer

from rss_monkey.client.proxy import JsonRpcProxy
from rss_monkey.server.interfaces import (ITestService, IRegistrationService,
                                          IRssService)

class RssClientError(Exception):
    pass


class Channel(object):
    _id = None
    url = None
    title = None
    description = None
    link = None
    modified = None

    @property
    def entries(self):
        pass


class Entry(object):
    _id = None
    _parent = None
    title = None
    summary = None
    link = None
    date = None

    @property
    def read(self):
        pass

    @read.setter
    def read(self, value):
        pass


class RssClient(object):
    def __init__(self):
        self._is_connected = False
        self.rpc_proxy = JsonRpcProxy(IRssService)

    def connect(self, url, login, passwd):
        url, p = RssClient._get_url_and_protocol(url, 'rss')

        self.rpc_proxy._connect(url, login=login, passwd=passwd, protocol=p)

    def disconnect(self):
        self.login_svc_proxy.logout(self.session_token)

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def channels(self):
        if not self.is_connected:
            raise Exception() # TODO: exception

        return self.rpc_proxy.jsonrpc_get_channels()

    @staticmethod
    def register_user(url, login, passwd):
        pass

    @staticmethod
    @defer.inlineCallbacks
    def test_connection(url):
        url, p = RssClient._get_url_and_protocol(url, 'test')

        proxy = JsonRpcProxy(ITestService)
        proxy._connect(url, protocol=p)
        res = yield proxy.test()

        if res != 'OK':
            raise ValueError('Server returned unexpected value')

    @staticmethod
    def _get_url_and_protocol(base_url, path):
        parsed = urlparse.urlparse(base_url)

        if parsed.scheme not in ('http', 'https'):
            raise ValueError('Podporovány jsou pouze protokoly HTTP a HTTPS')

        path = parsed.path + '/' + path

        url = urlparse.urljoin(base_url, path)

        return url, parsed.scheme
