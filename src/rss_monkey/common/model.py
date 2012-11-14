# -*- coding: utf8 -*-

import logging

from sqlalchemy import ForeignKey, Column, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

logging.basicConfig()
LOG = logging.getLogger(__name__)


Base = declarative_base()


class Feed(Base):
    __tablename__ = 'feeds'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), index=True, unique=True)
    title = Column(String(255))
    description = Column(String(1024))
    link = Column(String(255))
    modified = Column(DateTime)

    entries = relationship('FeedEntry', order_by='FeedEntry.date',
        backref='feed', cascade='all, delete, delete-orphan')

    def add_entry(self, entry):
        """
        Warning! This method is only synchronous!
        """
        if (Session.object_session(self)
                .query(FeedEntry)
                .with_parent(self)
                .filter_by(link=entry.link)
                .count() > 0):
            return

        self.entries.append(entry)
        LOG.debug("Feed %d: new entry '%s'", self.id, entry.link)


class FeedEntry(Base):
    __tablename__ = 'feed_entries'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feeds.id'))
    title = Column(String(255))
    summary = Column(String(1024))
    link = Column(String(255), index=True, unique=True)
    date = Column(DateTime)


user_feed_table = Table('user_feed', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('feed_id', Integer, ForeignKey('feeds.id'), primary_key=True),
)
# TODO: poradi feedu pri zobrazeni - samostatna tabulka


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(20), index=True, unique=True)
    passwd = Column(String(50), unique=True) # TODO: ???

    feeds = relationship('Feed',
                secondary=user_feed_table,
                backref='users',
                primaryjoin='User.id == user_feed.c.user_id',
                secondaryjoin='Feed.id == user_feed.c.feed_id')
                #cascade='all, delete, delete-orphan') # TODO: delete-orphan neni podporovan na many-to-many vztazich!!!
