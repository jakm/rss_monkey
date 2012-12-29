# -*- coding: utf8 -*-

import jsonrpclib
from urllib2 import urlparse

from twisted.internet import defer

from rss_monkey.client.proxy import JsonRpcProxy
from rss_monkey.server.interfaces import (ILoginService, IRegistrationService,
                                          IRssService, ITestService)

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
        self.connected = False
        self.login_svc_proxy = None
        self.rss_svc_proxy = None
        self.session_token = None

    def connect(self, url, login, passwd):
        self.login_svc_proxy = JsonRpcProxy(ILoginService)
        self.login_svc_proxy._connect(url)
        self.session_token = self.login_svc_proxy.login(login, passwd)

    def disconnect(self):
        self.login_svc_proxy.logout(self.session_token)

    @property
    def channels(self):
        pass

    @staticmethod
    def register_user(url, login, passwd):
        pass

    @staticmethod
    @defer.inlineCallbacks
    def test_connection(url):
        RssClient._check_url(url)
        url = RssClient._urljoin(url, 'test')

        test_svc_proxy = JsonRpcProxy(ITestService)
        test_svc_proxy._connect(url)
        res = yield test_svc_proxy.test()

        if res != 'OK':
            raise ValueError('Server returned unexpected value')

    @staticmethod
    def _check_url(url):
        parsed = urlparse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            raise ValueError('Podporovány jsou pouze protokoly HTTP a HTTPS')

    @staticmethod
    def _urljoin(url, path):
        parsed = urlparse.urlparse(url)
        path = parsed.path + '/' + path
        return urlparse.urljoin(url, path)
