# -*- coding: utf8 -*-

import logging

from fastjsonrpc.jsonrpc import JSONRPCError
from urllib2 import urlparse
from twisted.internet import defer

from rss_monkey.client.proxy import JsonRpcProxy
from rss_monkey.server.interfaces import (ITestService, IRegistrationService,
                                          IRssService)

LOG = logging.getLogger(__name__)


class RssClient(object):
    """
    High-level client.
    """
    def __init__(self):
        self._is_connected = False
        self.rpc_proxy = JsonRpcProxy(IRssService)

    def connect(self, url, login, passwd):
        url, p = RssClient._get_url_and_protocol(url, 'rss')

        self.rpc_proxy._connect(url, login=login, passwd=passwd, protocol=p)
        self._is_connected = True

    def close(self):
        self.rpc_proxy._close()
        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    def get_channels(self):
        self._check_connected()

        return self.rpc_proxy.get_channels()

    @defer.inlineCallbacks
    def add_channel(self, url):
        self._check_connected()

        # try add channel, if exists return its id

        channel_id = None
        try:
            channel_id = yield self.rpc_proxy.add_channel(url)
        except JSONRPCError as e:
            if str(e) == 'Channel exists':
                channels = yield self.get_channels()
                for channel in channels:
                    if channel['url'] == url:
                        channel_id = channel['id']
                        break
                else:
                    msg = 'Race condition when adding channel (url: %s)' % url
                    LOG.warning(msg)
                    raise ValueError(msg)
            else:
                raise

        defer.returnValue(channel_id)

    def reload_channel(self, channel_id):
        self._check_connected()

        return self.rpc_proxy.reload_channel(channel_id)

    def remove_channel(self, channel_id):
        self._check_connected()

        return self.rpc_proxy.remove_channel(channel_id)

    def has_unread_entries(self, channel_id):
        self._check_connected()

        return self.rpc_proxy.has_unread_entries(channel_id)

    def get_unread_entries(self, channel_id):
        self._check_connected()

        return self.rpc_proxy.get_unread_entries(channel_id)

    def get_entries(self, channel_id):
        self._check_connected()

        return self.rpc_proxy.get_entries(channel_id)

    def set_entry_read(self, entry_id, read):
        self._check_connected()

        return self.rpc_proxy.set_entry_read(entry_id, read)

    def _check_connected(self):
        if not self.is_connected:
            raise ValueError('Client is not connected')

    @staticmethod
    @defer.inlineCallbacks
    def register_user(url, login, passwd):
        url, p = RssClient._get_url_and_protocol(url, 'registration')

        proxy = JsonRpcProxy(IRegistrationService)
        proxy._connect(url, protocol=p)
        try:
            yield proxy.register_user(login, passwd)
        except Exception as e:
            LOG.warning('Exception when registering user: %s:%s',
                        e.__class__.__name__, str(e))
            raise ValueError('User registration failed')

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
