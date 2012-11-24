# -*- coding: utf8 -*-

import logging

from sqlalchemy import (ForeignKey, Column, Boolean, Integer,
                        String, DateTime, Table)
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

logging.basicConfig()
LOG = logging.getLogger(__name__)


Base = declarative_base()


class Feed(Base):
    __tablename__ = 'feeds'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), index=True, unique=True, nullable=False)
    title = Column(String(255))
    description = Column(String(1024))
    link = Column(String(255))
    modified = Column(DateTime)

    entries = relationship('FeedEntry', order_by='FeedEntry.date',
        backref='feed', cascade='all, delete, delete-orphan')

    def add_entry(self, entry):
        """
        Warning! This method uses synchronous query!
        """
        if entry in self.entries:
            return

        self.entries.append(entry)
        LOG.debug("Feed %d: new entry '%s'", self.id, entry.link)


class FeedEntry(Base):
    __tablename__ = 'feed_entries'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feeds.id'), index=True, nullable=False)
    title = Column(String(255))
    summary = Column(String(1024))
    link = Column(String(255))
    date = Column(DateTime)


user_feeds_table = Table('user_feeds', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('feed_id', Integer, ForeignKey('feeds.id'), primary_key=True),
    Column('order', Integer)
)


user_entries_table = Table('user_entries', Base.metadata,
    # TODO: nadefinovat kaskadu
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('feed_id', Integer, ForeignKey('feeds.id'), primary_key=True),
    Column('entry_id', Integer, ForeignKey('feed_entries.id'), primary_key=True),
    Column('read', Boolean, server_default='0')
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(20), index=True, unique=True, nullable=False)
    passwd = Column(String(64), nullable=False)

    feeds = relationship('Feed',
                secondary=user_feeds_table,
                backref='users',
                order_by='user_feeds.c.order',
                primaryjoin='User.id == user_feeds.c.user_id',
                secondaryjoin='Feed.id == user_feeds.c.feed_id')
                #cascade='all, delete, delete-orphan') # TODO: delete-orphan neni podporovan na many-to-many vztazich!!!

    def get_users_entries(self, feed=None, read=None):
        q = (Session.object_session(self)
                .query(FeedEntry)
                .filter(FeedEntry.id == user_entries_table.c.entry_id,
                        user_entries_table.c.user_id == self.id))
        if feed is not None:
            q = q.filter(user_entries_table.c.feed_id == feed.id)
        if read is not None:
            q = q.filter(user_entries_table.c.read == read)

        return q.all()

    def get_users_entry(self, entry_id):
        entry = (Session.object_session(self)
                        .query(FeedEntry)
                        .filter(FeedEntry.id == user_entries_table.c.entry_id,
                                user_entries_table.c.user_id == self.id,
                                user_entries_table.c.entry_id == entry_id)
                        .one())
        return entry

    def is_entry_read(self, entry):
        is_read = (Session.object_session(self)
                          .query(user_entries_table.c.read)
                          .filter(user_entries_table.c.user_id == self.id,
                                  user_entries_table.c.entry_id == entry.id)
                          .one())
        print is_read
        return bool(is_read)

    def set_entry_read(self, entry, read):
        Session.object_session(self).execute(
            user_entries_table.update()
                .where(user_entries_table.c.user_id == self.id)
                .where(user_entries_table.c.entry_id == entry.id)
                .values({user_entries_table.c.read: read})
        )
