# -*- coding: utf8 -*-

import logging

from ConfigParser import RawConfigParser
from springpython.config import Object, PythonConfig
from springpython.context import scope
from twisted.internet import reactor
from twisted.python import log

CONFIG_FILE = '/etc/rss_monkey_server.ini'

LOG = logging.getLogger(__name__)


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

        logging_observer = log.PythonLoggingObserver()
        logging_observer.start()

        logging.basicConfig(format=format, level=level, filename=filename)

    @Object(lazy_init=True)
    def db_config(self):
        LOG.info('Loading db_config object')

        host = self.config.get('database', 'host')
        user = self.config.get('database', 'user')
        passwd = self.config.get('database', 'passwd')
        db = self.config.get('database', 'db')
        pool_size_min = self.config.getint('database', 'pool_size_min')
        pool_size_max = self.config.getint('database', 'pool_size_max')
        debug = self.config.getboolean('database', 'debug')

        return {'host': host, 'user': user, 'passwd': passwd, 'db': db,
                'pool_size_min': pool_size_min, 'pool_size_max': pool_size_max,
                'debug': debug}

    @Object(lazy_init=True)
    def db_pool(self):
        LOG.info('Loading db_pool object')
        from twisted.enterprise import adbapi

        db_config = self.db_config()

        kwargs = dict(host=db_config['host'],
                      user=db_config['user'],
                      passwd=db_config['passwd'],
                      db=db_config['db'],
                      charset='utf8')

        if db_config['pool_size_min'] >= 0:
            kwargs['cp_min'] = db_config['pool_size_min']
        if db_config['pool_size_max'] >= 0:
            kwargs['cp_max'] = db_config['pool_size_max']
        if db_config['debug']:
            kwargs['cp_noisy'] = True

        dbpool = adbapi.ConnectionPool("MySQLdb", **kwargs)

        return dbpool

    @Object(lazy_init=True)
    def db(self):
        LOG.info('Loading db object')
        from rss_monkey.common.db import Db

        db = Db(self.db_pool())

        return db

    @Object(lazy_init=True)
    def feed_processor(self):
        LOG.info('Loading feed_processor object')
        from rss_monkey.feed_processor import FeedProcessor

        processor = FeedProcessor()
        processor.db = self.db()

        processor.download_interval = self.config.getint('feed_processor', 'download_interval')
        processor.download_timeout = self.config.getint('feed_processor', 'download_timeout')

        pool_size = self.config.getint('feed_processor', 'pool_size')
        if pool_size > 0:
            reactor.suggestThreadPoolSize(pool_size)

        return processor

    @Object(lazy_init=True)
    def feed_processor_service(self):
        LOG.info('Loading feed_processor_service object')
        from rss_monkey.feed_processor import FeedProcessorService

        service = FeedProcessorService()
        service.feed_processor = self.feed_processor()

        return service

    @Object(lazy_init=True)
    def feed_processor_rpc_server(self):
        LOG.info('Loading feed_processor_rpc_service object')
        from twisted.web import server
        from rss_monkey.feed_processor import FeedProcessorRpcServer

        root = FeedProcessorRpcServer()
        root.feed_processor = self.feed_processor()

        site = server.Site(root)

        port = self.config.getint('feed_processor_rpc', 'port')

        LOG.info('Binding feed_processor_rpc_server with port %d', port)
        return self._get_internet_server(port, site)

    @Object(scope.PROTOTYPE, lazy_init=True)
    def rss_service(self):
        LOG.info('Loading rss_service object')
        from rss_monkey.server.services import RssService

        service = RssService()
        service.db = self.db()
        service.feed_processor_rpc_port = self.config.getint('feed_processor_rpc', 'port')
        service.ssl_enabled = self.ssl_enabled()

        return service

    @Object(lazy_init=True)
    def registration_service(self):
        LOG.info('Loading registration_service object')
        from rss_monkey.server.services import RegistrationService

        service = RegistrationService()
        service.db = self.db()

        return service

    @Object(lazy_init=True)
    def test_service(self):
        LOG.info('Loading test_service object')
        from rss_monkey.server.services import TestService

        service = TestService()

        return service

    @Object(lazy_init=True)
    def rss_api_factory(self):
        LOG.info('Loading rss_api_factory object')
        from rss_monkey.server.interfaces import IRssService
        from rss_monkey.server.api import ApiResourceFactory

        factory = ApiResourceFactory('RssApi', IRssService)
        return factory

    @Object(lazy_init=True)
    def rss_resource_factory(self):
        LOG.info('Loading rss_resource_factory object')
        from rss_monkey.server.api import RssResourceFactory

        factory = RssResourceFactory()
        factory.api_factory = self.rss_api_factory()

        return factory

    @Object(lazy_init=True)
    def rss_api(self):
        LOG.info('Loading rss_api_realm object')
        from twisted.cred.portal import Portal
        from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory
        from rss_monkey.server.authentication import PrivateServiceRealm
        from rss_monkey.server.authentication import DbCredentialsChecker

        portal = Portal(PrivateServiceRealm(self.rss_resource_factory()),
                        [DbCredentialsChecker(self.db())])

        credential_factory = BasicCredentialFactory("RssApi")

        resource = HTTPAuthSessionWrapper(portal, [credential_factory])
        return resource

    @Object(lazy_init=True)
    def registration_api(self):
        LOG.info('Loading registration_api object')
        from rss_monkey.server.interfaces import IRegistrationService
        from rss_monkey.server.api import ApiResourceFactory

        factory = ApiResourceFactory('RegistrationApi', IRegistrationService)
        resource = factory(self.registration_service())
        return resource

    @Object(lazy_init=True)
    def test_api(self):
        LOG.info('Loading test_api object')
        from rss_monkey.server.interfaces import ITestService
        from rss_monkey.server.api import ApiResourceFactory

        factory = ApiResourceFactory('TestApi', ITestService)
        resource = factory(self.test_service())
        return resource

    @Object(lazy_init=True)
    def web_api_server(self):
        LOG.info('Loading web_api_server object')
        from twisted.web import resource, server

        root = resource.Resource()
        root.putChild('rss', self.rss_api())
        root.putChild('registration', self.registration_api())
        root.putChild('test', self.test_api())

        site = server.Site(root)

        port = self.config.getint('web_api', 'port')

        LOG.info('Binding web_api_server with port %d', port)

        return self._get_internet_server(port, site)

    @Object(lazy_init=True)
    def ssl_context(self):
        from twisted.internet import ssl

        private_key = self.config.get('global', 'private_key')
        ca_cert = self.config.get('global', 'ca_cert')

        LOG.info('Loading server SSL private key and certificate: %s, %s',
                  private_key, ca_cert)

        return ssl.DefaultOpenSSLContextFactory(private_key, ca_cert)

    @Object(lazy_init=True)
    def ssl_enabled(self):
        return self.config.getboolean('global', 'enable_ssl')

    def _get_internet_server(self, port, site):
        from twisted.application import internet

        enable_ssl = self.ssl_enabled()

        LOG.info('SSL enabled: %s', enable_ssl)

        if enable_ssl:
            ctx = self.ssl_context()
            return internet.SSLServer(port, site, ctx)
        else:
            return internet.TCPServer(port, site)
