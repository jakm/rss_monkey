# -*- coding: utf8 -*-

import logging

from ConfigParser import ConfigParser
from springpython.config import Object, PythonConfig
from springpython.container import ObjectContainer
from springpython.context import ApplicationContext
from twisted.internet import reactor

CONFIG_FILE = '/etc/rss_monkey.ini'

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
            raise TypeError('Context have to inherit from ObjectContainer')
        AppContext._context = app_context


class AppConfig(PythonConfig):
    def __init__(self):
        super(AppConfig, self).__init__()
        self.config = ConfigParser()
        self.config.read(CONFIG_FILE)

        format = self.config.get('logging', 'logging_format')
        level = self.config.getint('logging', 'logging_level')
        logging.basicConfig(format=format, level=level)

    @Object(lazy_init=True)
    def db(self):
        LOG.debug('Loading db from AppConfig')
        from rss_monkey.db import AsyncDb
        db = AsyncDb()
        db.session = None  # TODO
        return db

    @Object(lazy_init=True)
    def feed_processor(self):
        LOG.debug('Loading feed_processor from AppConfig')
        from rss_monkey.feed_processor import FeedProcessor
        processor = FeedProcessor()
        processor.download_period = self.config.get('feed_processor', 'download_period')
        processor.download_timeout = self.config.get('feed_processor', 'download_timeout')

        pool_size = self.config.get('feed_processor', 'pool_size')
        if pool_size > 0:
            reactor.suggestThreadPoolSize(pool_size)

        return processor


def install_default():
    global AppContext
    AppContext.install(ApplicationContext(AppConfig()))
