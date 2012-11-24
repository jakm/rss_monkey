#-*- coding: utf8 -*-

import jsonrpclib
import logging
from zope.interface import Interface, implements

from rss_monkey.common.model import (User, Feed, FeedEntry, user_feeds_table,
                                     user_entries_table)
from rss_monkey.common.utils import log_function_call

logging.basicConfig()
LOG = logging.getLogger(__name__)


class LoginService(object):
    def login(self, login, passwd):
        pass
        # TODO: vygeneruje nejaky klic, ulozi do db a vrati zpet


class IRssService(Interface):
    """
    Interface of essential service to control user's channels and entries.
    """

    def get_channels(self, user_id):
        """
        Retrieve channels registered by user. Records are in format:
        {'id': int, 'title': str, 'url': str}

        @param user_id int, User ID
        @return tuple, Tuple of records
        """

    def reorder_channels(self, user_id, new_order):
        """
        Change ordering of user's channels.

        @param user_id int, User ID
        @param new_order sequence, Sequence of ordered channel IDs
        """

    def add_channel(self, user_id, url):
        """
        Bind user with channel. If channel doesn't exist create new record.

        @param user_id int, User ID
        @param url str, URL of channel
        """

    def remove_channel(self, user_id, channel_id):
        """
        Unbind user with channel. If channel is not bound with any user remove it.

        @param user_id int, User ID
        @param channel_id int, Channel ID
        """

    def has_unread_entries(self, user_id, channel_id):
        """
        True if channel has unread entries or False.

        @param user_id int, User ID
        @param channel_id int, Channel ID
        @return bool
        """

    def get_entries(self, user_id, channel_id, limit=None, offset=None):
        """
        Return entries with any read status. Records are in format:
        {'id', int, 'title': str, 'summary': str, 'link': str, 'date':
         datetime.datetime, 'read': bool}

        @param user_id int, User ID
        @param channel_id int, Channel ID
        @param limit int, Maximal number of returned records or None for unlimited
        @param offset int, Number of records to skip
        @return tuple, Tuple of records
        """

    def set_entry_read(self, user_id, entry_id, read):
        """
        Set read status of entry.

        @param user_id int, User ID
        @param entry_id int, Entry ID
        @param read bool, Read status of entry
        """


class RssService(object):
    implements(IRssService)

    db = None
    feed_processor_rpc_port = None

    @log_function_call()
    def get_channels(self, user_id):
        user = self.db.load(User, id=user_id)
        return tuple([{'id': feed.id, 'title': feed.title, 'url': feed.url}
            for feed in user.feeds])

    @log_function_call()
    def reorder_channels(self, user_id, new_order):
        feeds = (self.db.query(user_feeds_table.c.feed_id)
                     .filter(user_feeds_table.c.user_id == user_id)
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

                self.db.execute(
                    user_feeds_table.update()
                        .where(user_feeds_table.c.feed_id == feed_id)
                        .where(user_feeds_table.c.user_id == user_id)
                        .values({user_feeds_table.c.order: order})
                )
        except:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    @log_function_call()
    def add_channel(self, user_id, url):
        user = self.db.load(User, id=user_id)
        feed = Feed(url=url)
        user.feeds.append(feed)
        self.db.commit()

        # notify feed processor to reload feeds
        url = 'http://localhost:%d' % self.feed_processor_rpc_port
        server = jsonrpclib.Server(url)
        server._notify.reload_feeds()

    @log_function_call()
    def remove_channel(self, user_id, channel_id):
        user = self.db.load(User, id=user_id)
        for feed in user.feeds:
            if feed.id == channel_id:
                user.feeds.remove(feed)
                self.db.commit()
                break
        else:
            raise Exception('Cannot find channel')

    @log_function_call()
    def has_unread_entries(self, user_id, channel_id):
        return len(self.get_unread_entries(user_id, channel_id)) > 0

    @log_function_call()
    def get_unread_entries(self, user_id, channel_id, limit=None, offset=None):
        return self._get_entries(user_id, channel_id, read=False, limit=limit, offset=offset)

    @log_function_call()
    def get_entries(self, user_id, channel_id, limit=None, offset=None):
        return self._get_entries(user_id, channel_id, limit=limit, offset=offset)

    @log_function_call()
    def set_entry_read(self, user_id, entry_id, read):
        user = self.db.load(User, id=user_id)
        entry = user.get_users_entry(entry_id)
        user.set_entry_read(entry, read)
        self.db.commit()

    def _get_entries(self, user_id, channel_id, read=None, limit=None, offset=None):
        user = self.db.load(User, id=user_id)
        try:
            feed = [f for f in user.feeds if f.id == channel_id][0]
        except IndexError:
            return ()

        if limit is None and offset is None:
            entries = user.get_users_entries(feed=feed, read=read)
        else:
            q = (self.db.query(FeedEntry)
                        .filter(FeedEntry.id == user_entries_table.c.entry_id,
                                user_entries_table.c.user_id == user.id,
                                user_entries_table.c.feed_id == feed.id))
            if read is not None:
                q = q.filter(user_entries_table.c.read == read)
            if limit is not None:
                q = q.limit(limit)
            if offset is not None:
                q = q.offset(offset)

            entries = q.all()

        if read is not None:
            get_read = lambda e: read
        else:
            get_read = lambda e: user.is_entry_read(e)

        result = []
        for entry in entries:
            record = {'id': entry.id, 'title': entry.title,
                     'summary': entry.summary, 'link': entry.link,
                     'date': str(entry.date), 'read': get_read(entry)}
            print record

            result.append(record)

        return tuple(result)
