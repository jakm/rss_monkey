# -*- coding: utf8 -*-

import logging

from sqlalchemy import (ForeignKey, Column, Boolean, Integer,
                        String, DateTime, Table)
from sqlalchemy.orm import relationship
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


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(20), index=True, unique=True, nullable=False)
    passwd = Column(String(64), nullable=False)

    feeds = relationship('Feed',
                secondary=user_feeds_table,
                backref='users',
                order_by='user_feed.c.order',
                primaryjoin='User.id == user_feed.c.user_id',
                secondaryjoin='Feed.id == user_feed.c.feed_id')
                #cascade='all, delete, delete-orphan') # TODO: delete-orphan neni podporovan na many-to-many vztazich!!!
