# -*- coding: utf8 -*-

from sqlalchemy import ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Feed(Base):
    __tablename__ = 'feeds'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), index=True)
    title = Column(String(255), index=True)
    description = Column(String(1024))
    link = Column(String(255))
    modified = Column(DateTime)
    entries = relationship('FeedEntry', order_by='FeedEntry.date',
        backref='feed', cascade="all, delete, delete-orphan")


class FeedEntry(Base):
    __tablename__ = 'feed_entries'

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feeds.id'))
    title = Column(String(255))
    summary = Column(String(1024))
    link = Column(String(255))
    date = Column(DateTime)
