#-*- coding: utf8 -*-

import jsonrpclib
import logging
from zope.interface import implements

from rss_monkey.common.model import (User, Feed, FeedEntry, user_feeds_table,
                                     user_entries_table)
from rss_monkey.common.utils import log_function_call
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

    db_registry = None

    @log_function_call
    def register_user(self, login, passwd):
        assert len(login) > 0 and len(login) <= 20, 'login length'
        assert len(passwd) == 64, 'passwd length'

        try:
            user = User(login=login, passwd=passwd)
            self.db_registry().store(user)
            self.db_registry().commit()
        except Exception:
            self.db_registry().rollback()
            raise ValueError('Registration failed')


class RssService(object):
    implements(IRssService)

    db_registry = None
    feed_processor_rpc_port = None
    user_id = None
    ssl_enabled = False

    @log_function_call(log_result=False)
    def get_channels(self):
        user = self.db_registry().load(User, id=self.user_id)
        return tuple([{'id': feed.id, 'title': feed.title, 'url': feed.url}
            for feed in user.feeds])

    @log_function_call
    def reorder_channels(self, new_order):
        feeds = (self.db_registry().query(user_feeds_table.c.feed_id)
                     .filter(user_feeds_table.c.user_id == self.user_id)
                     .all())

        if not feeds:
            return

        try:
            for feed_id in (f[0] for f in feeds):
                order = None
                try:
                    order = new_order.index(feed_id)
                except ValueError:
                    pass

                self.db_registry().execute(
                    user_feeds_table.update()
                        .where(user_feeds_table.c.feed_id == feed_id)
                        .where(user_feeds_table.c.user_id == self.user_id)
                        .values({user_feeds_table.c.order: order})
                )
        except:
            self.db_registry().rollback()
            raise
        else:
            self.db_registry().commit()

    @log_function_call
    def add_channel(self, url):
        user = self.db_registry().load(User, id=self.user_id)
        feed = Feed(url=url)
        user.feeds.append(feed)
        self.db_registry().commit()

        return feed.id

    @log_function_call
    def reload_channel(self, channel_id):
        # send RPC to feed processor
        protocol = 'https' if self.ssl_enabled else 'http'
        url = '%s://localhost:%d' % (protocol, self.feed_processor_rpc_port)
        server = jsonrpclib.Server(url)
        server.reload_feed(channel_id)

    @log_function_call
    def remove_channel(self, channel_id):
        user = self.db_registry().load(User, id=self.user_id)
        for feed in user.feeds:
            if feed.id == channel_id:
                user.feeds.remove(feed)
                self.db_registry().commit()
                break
        else:
            raise Exception('Cannot find channel')

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
        user = self.db_registry().load(User, id=self.user_id)
        entry = user.get_users_entry(entry_id)
        user.set_entry_read(entry, read)
        self.db_registry().commit()

    def _get_entries(self, user_id, channel_id, read=None, limit=None, offset=None):
        user = self.db_registry().load(User, id=user_id)
        try:
            feed = [f for f in user.feeds if f.id == channel_id][0]
        except IndexError:
            LOG.debug('Feed not found (user_id: %d, channel_id: %d', user_id, channel_id)
            return ()

        if limit is None and offset is None:
            LOG.debug('Using simple get (limit and offset are None)')
            entries = user.get_users_entries(feed=feed, read=read)
        else:
            raise NotImplementedError('Not tested!!!')

            LOG.debug('Using complex query (limit: %s, offset: %s', limit, offset)
            q = (self.db_registry().query(FeedEntry)
                        .filter(FeedEntry.id == user_entries_table.c.entry_id,
                                user_entries_table.c.user_id == user.id,
                                user_entries_table.c.feed_id == feed.id))
            if read is not None:
                q = q.filter(user_entries_table.c.read == read)
            if limit is not None:
                q = q.limit(limit)
            if offset is not None:
                q = q.offset(offset)

            LOG.debug('Query: %s', str(q))

            entries = q.all()

        if read is not None:
            get_read = lambda e: read
        else:
            get_read = lambda e: user.is_entry_read(e)

        LOG.debug('Result: %d rows', len(entries))

        result = []
        for entry in entries:
            record = {'id': entry.id, 'title': entry.title,
                     'summary': entry.summary, 'link': entry.link,
                     'date': str(entry.date), 'read': get_read(entry)}

            result.append(record)

        return tuple(result)
