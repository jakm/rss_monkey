#-*- coding: utf8 -*-

import jsonrpclib
import logging
from MySQLdb import IntegrityError
from twisted.internet import defer
from zope.interface import implements

from rss_monkey.common.utils import log_function_call, defer_to_thread
from rss_monkey.server.interfaces import (IRegistrationService, IRssService,
                                          ITestService)

LOG = logging.getLogger(__name__)


class TestService(object):
    implements(ITestService)

    @log_function_call
    def test(self):
        return 'OK'


class RegistrationService(object):
    implements(IRegistrationService)

    db = None

    @defer.inlineCallbacks
    @log_function_call
    def register_user(self, login, passwd):
        assert len(login) > 0 and len(login) <= 20, 'login length'
        assert len(passwd) == 64, 'passwd length'

        try:
            yield self.db.add_user(login, passwd)
        except Exception:
            raise ValueError('Registration failed')


class RssService(object):
    implements(IRssService)

    db = None
    feed_processor_rpc_port = None
    user_id = None
    ssl_enabled = False

    @defer.inlineCallbacks
    @log_function_call(log_result=False)
    def get_channels(self):
        feeds = yield self.db.get_users_feeds(self.user_id)
        defer.returnValue([{'id': feed['id'], 'title': feed['title'], 'url': feed['url']}
                           for feed in feeds])

    @log_function_call
    def reorder_channels(self, new_order):
        raise NotImplementedError()

        # feeds = (self.db_registry().query(user_feeds_table.c.feed_id)
        #              .filter(user_feeds_table.c.user_id == self.user_id)
        #              .all())

        # if not feeds:
        #     return

        # try:
        #     for feed_id in (f[0] for f in feeds):
        #         order = None
        #         try:
        #             order = new_order.index(feed_id)
        #         except ValueError:
        #             pass

        #         self.db_registry().execute(
        #             user_feeds_table.update()
        #                 .where(user_feeds_table.c.feed_id == feed_id)
        #                 .where(user_feeds_table.c.user_id == self.user_id)
        #                 .values({user_feeds_table.c.order: order})
        #         )
        # except:
        #     self.db_registry().rollback()
        #     raise
        # else:
        #     self.db_registry().commit()

    @defer.inlineCallbacks
    @log_function_call
    def add_channel(self, url):
        channel_id = yield self.db.add_feed(url)

        try:
            yield self.db.assign_feed(self.user_id, channel_id)
        except IntegrityError as e:
            code, msg = e.args
            if code == 1062:
                raise ValueError('Channel exists')
            else:
                raise

        defer.returnValue(channel_id)

    @defer_to_thread
    @log_function_call
    def reload_channel(self, channel_id):
        # send RPC to feed processor
        protocol = 'https' if self.ssl_enabled else 'http'
        url = '%s://localhost:%d' % (protocol, self.feed_processor_rpc_port)
        server = jsonrpclib.Server(url)
        server.reload_feed(channel_id)

    @log_function_call
    def remove_channel(self, channel_id):
        return self.db.unassign_feed(self.user_id, channel_id)

    @log_function_call
    def has_unread_entries(self, channel_id):
        return len(self.get_unread_entries(self.user_id, channel_id)) > 0

    @log_function_call(log_result=False)
    def get_unread_entries(self, channel_id, limit=None, offset=None):
        return self._get_entries(self.user_id, channel_id, read=False, limit=limit, offset=offset)

    @log_function_call(log_result=False)
    def get_entries(self, channel_id, limit=None, offset=None):
        return self._get_entries(self.user_id, channel_id, limit=limit, offset=offset)

    @log_function_call
    def set_entry_read(self, entry_id, read):
        return self.db.set_entry_read(self.user_id, entry_id, read)

    @defer.inlineCallbacks
    def _get_entries(self, user_id, channel_id, read=None, limit=None, offset=None):
        res = yield self.db.get_users_entries(user_id, channel_id, read, limit, offset)
        defer.returnValue(tuple(res))
