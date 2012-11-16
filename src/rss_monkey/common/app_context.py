# -*- coding: utf8 -*-

import logging

from ConfigParser import RawConfigParser
from springpython.config import Object, PythonConfig
from springpython.container import ObjectContainer
from springpython.context import ApplicationContext
from twisted.internet import reactor

CONFIG_FILE = '/etc/rss_monkey.ini'

logging.basicConfig()
LOG = logging.getLogger(__name__)


class AppContext(object):
    _context = None

    @staticmethod
    def get_object(name, ignore_abstract=False):
        if not AppContext._context:
            raise RuntimeError('Application context is not installed')
        return AppContext._context.get_object(name, ignore_abstract)

    @staticmethod
    def install(app_context):
        if not isinstance(app_context, ObjectContainer):
            raise TypeError('Context has to inherit from ObjectContainer')
        AppContext._context = app_context


class AppConfig(PythonConfig):
    def __init__(self):
        super(AppConfig, self).__init__()
        self.config = RawConfigParser()
        self.config.read(CONFIG_FILE)

        format = self.config.get('logging', 'format')
        level = self.config.getint('logging', 'level')
        filename = self.config.get('logging', 'filename')
        if filename == '' or filename == 'stdout':
            filename = None

        logging.basicConfig(format=format, level=level, filename=filename)

    @Object(lazy_init=True)
    def db_engine(self):
        LOG.debug('Loading db engine from AppConfig')
        from sqlalchemy import create_engine

        host = self.config.get('database', 'host')
        user = self.config.get('database', 'user')
        passwd = self.config.get('database', 'passwd')
        db = self.config.get('database', 'db')
        pool_size = self.config.getint('database', 'pool_size')

        LOG.debug('Database: host=%s, user=%s, passwd=***, db=%s, pool_size=%d',
            host,  user, passwd, db, pool_size)

        connection_string = 'mysql://%s:%s@%s/%s?charset=utf8' % (
            user, passwd, host, db)
        kwargs = {'pool_size': pool_size} if pool_size >= 0 else {}

        return create_engine(connection_string, **kwargs)

    @Object(lazy_init=True)
    def db_session(self):
        LOG.debug('Loading db session from AppConfig')
        from sqlalchemy.orm import sessionmaker

        engine = self.db_engine()

        Session = sessionmaker(bind=engine)
        return Session()


class FeedProcessorConfig(AppConfig):
    def __init__(self):
        super(FeedProcessorConfig, self).__init__()

    @Object(lazy_init=True)
    def db(self):
        LOG.debug('Loading sync db from AppConfig')
        from rss_monkey.common.db import SyncDb
        db = SyncDb()
        db.session = self.db_session()
        return db

    @Object(lazy_init=True)
    def feed_processor(self):
        LOG.debug('Loading feed_processor from AppConfig')
        from rss_monkey.feed_processor import FeedProcessor
        processor = FeedProcessor()
        processor.download_interval = self.config.getint('feed_processor', 'download_interval')
        processor.download_timeout = self.config.getint('feed_processor', 'download_timeout')

        pool_size = self.config.getint('feed_processor', 'pool_size')
        if pool_size > 0:
            reactor.suggestThreadPoolSize(pool_size)

        return processor


class ServerServiceConfig(AppConfig):
    def __init__(self):
        super(ServerServiceConfig, self).__init__()

    @Object(lazy_init=True)
    def db(self):
        LOG.debug('Loading async db from AppConfig')
        from rss_monkey.common.db import AsyncDb
        db = AsyncDb()
        db.session = self.db_session()
        return db


def install_context(app_config):
    global AppContext
    AppContext.install(ApplicationContext(app_config))
