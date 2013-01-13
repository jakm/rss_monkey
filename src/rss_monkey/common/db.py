# -*- coding: utf8 -*-

import logging

from MySQLdb import DatabaseError, IntegrityError
from twisted.internet import defer

LOG = logging.getLogger(__name__)


class NoResultError(DatabaseError):
    pass


class Db(object):
    db_pool = None

    def __init__(self, db_pool):
        self.db_pool = db_pool

        self.param = self._get_paramstyle()
        self.identity_function = self._get_identity_function()

    def _get_paramstyle(self):
        paramstyle_map = {'format': '%s', 'qmark': '?'}
        wildcard = paramstyle_map.get(self.db_pool.dbapi.paramstyle, None)
        if not wildcard:
            raise NotImplementedError('Paramstyle used by db engine is not supported')

        return wildcard

    def _get_identity_function(self):
        id_function_map = {'MySQLdb': 'LAST_INSERT_ID()',
                           'sqlite3': 'LAST_INSERT_ROWID()'}
        function = id_function_map.get(self.db_pool.dbapiName, None)
        if not function:
            raise NotImplementedError('Used db engine is not supported')

        return function

    def fmt(self, sql):
        return sql.format(self.param)

    @defer.inlineCallbacks
    def get_user(self, login):
        sql = self.fmt('SELECT id, login, passwd FROM users WHERE login = {0}')
        res = yield self.db_pool.runQuery(sql, (login,))
        if len(res) == 0:
            raise NoResultError()

        row = res[0]
        user = {'id': row[0], 'login': row[1], 'passwd': row[2]}
        defer.returnValue(user)

    def add_user(self, login, passwd):
        sql = self.fmt('INSERT INTO users(login, passwd) VALUES({0}, {0})')
        return self.db_pool.runOperation(sql, (login, passwd))

    @defer.inlineCallbacks
    def get_feed_ids(self):
        res = yield self.db_pool.runQuery('SELECT id FROM feeds')
        defer.returnValue((row[0] for row in res))

    @defer.inlineCallbacks
    def get_feed(self, feed_id):
        sql = self.fmt('SELECT * FROM feeds WHERE id = {0}')
        res = yield self.db_pool.runQuery(sql, (feed_id,))
        if len(res) == 0:
            raise NoResultError()

        row = res[0]
        feed = {'id': row[0], 'url': row[1], 'title': row[2],
                'description': row[3], 'link': row[4], 'modified': row[5]}
        defer.returnValue(feed)

    def update_feed(self, feed_id, data):
        sets = []
        params = []
        for column, value in data.iteritems():
            sets.append(self.fmt(column + ' = {0}'))
            params.append(value)

        sql = 'UPDATE feeds SET ' + ','.join(sets) + self.fmt(' WHERE id = {0}')
        params.append(feed_id)

        return self.db_pool.runOperation(sql, params)

    @defer.inlineCallbacks
    def add_feed(self, url):
        feed_id = None
        try:
            sql = self.fmt('INSERT INTO feeds(url) VALUES({0})')
            feed_id = yield self._insert(sql, (url,))
        except IntegrityError:
            sql = self.fmt('SELECT id FROM feeds WHERE url = {0}')
            res = yield self.db_pool.runQuery(sql, (url,))
            feed_id = res[0][0]

        defer.returnValue(feed_id)

    def assign_feed(self, user_id, feed_id):
        def interaction(txn):
            sql = self.fmt('SELECT max(ifnull(`order`,0)) + 1 '
                   'FROM user_feeds WHERE user_id = {0}')
            txn.execute(sql, (user_id,))
            next_in_order = txn.fetchone()[0]
            if next_in_order is None:
                next_in_order = 1

            sql = self.fmt('INSERT INTO user_feeds(user_id, feed_id, `order`) '
                  'VALUES({0}, {0}, {0})')
            params = (user_id, feed_id, next_in_order)

            txn.execute(sql, params)

        return self.db_pool.runInteraction(interaction)

    def unassign_feed(self, user_id, feed_id):
        sql = self.fmt('DELETE FROM user_feeds '
                       'WHERE user_id = {0} AND feed_id = {0}')
        params = (user_id, feed_id)
        return self.db_pool.runOperation(sql, params)

    @defer.inlineCallbacks
    def insert_entry(self, feed_id, data):
        # check duplicity
        sql = self.fmt('SELECT count(*) FROM feed_entries WHERE feed_id = {0} '
                       'AND link = {0}')

        res = yield self.db_pool.runQuery(sql, (feed_id, data['link']))
        if len(res) > 0 and res[0][0] != 0:
            return

        # ok, insert row
        sql = self.fmt('INSERT INTO feed_entries(feed_id, title, summary, link, date) '
                       'VALUES({0}, {0}, {0}, {0}, {0})')

        params = (feed_id, data['title'], data['summary'], data['link'], data['date'])

        entry_id = yield self._insert(sql, params)
        defer.returnValue(entry_id)

    @defer.inlineCallbacks
    def get_entries(self, feed_id):
        sql = self.fmt('SELECT * FROM feed_entries WHERE feed_id = {0}')
        res = yield self.db_pool.runQuery(sql, (feed_id,))

        entries = ({'id': row[0], 'title': row[2], 'summary': row[3],
                    'link': row[4], 'date': str(row[5])}
                   for row in res)

        defer.returnValue(entries)

    @defer.inlineCallbacks
    def get_users_feeds(self, user_id):
        sql = self.fmt('SELECT feeds.* FROM user_feeds '
                       'JOIN feeds ON feeds.id = user_feeds.feed_id '
                       'WHERE user_feeds.user_id = {0} '
                       'ORDER BY user_feeds.order')
        res = yield self.db_pool.runQuery(sql, (user_id,))

        feeds = ({'id': row[0], 'url': row[1], 'title': row[2],
                  'description': row[3], 'link': row[4], 'modified': row[5]}
                  for row in res)
        defer.returnValue(feeds)

    @defer.inlineCallbacks
    def get_users_entries(self, user_id, feed_id, read=None, limit=None, offset=None):
        sql = self.fmt(
                'SELECT feed_entries.*, user_entries.read FROM user_entries '
                'JOIN feed_entries ON feed_entries.id = user_entries.entry_id '
                'WHERE user_entries.user_id = {0} '
                'AND user_entries.feed_id = {0}')

        params = [user_id, feed_id]

        if read is not None:
            sql += self.fmt(' AND user_entries.read = {0}')
            params.append(read)
        if limit is not None:
            sql += self.fmt(' LIMIT {0}')
            params.append(limit)
        if offset is not None:
            sql += self.fmt(' OFFSET {0}')
            params.append(offset)

        LOG.debug('Query: %s', sql)
        LOG.debug('Params: %s', str(params))

        res = yield self.db_pool.runQuery(sql, params)

        entries = ({'id': row[0], 'title': row[2], 'summary': row[3],
                    'link': row[4], 'date': str(row[5]), 'read': bool(row[6])}
                   for row in res)

        defer.returnValue(entries)

    def set_entry_read(self, user_id, entry_id, read):
        sql = self.fmt('UPDATE user_entries SET `read` = {0} '
                       'WHERE user_id = {0} AND entry_id = {0}')
        params = (read, user_id, entry_id)
        return self.db_pool.runOperation(sql, params)

    @defer.inlineCallbacks
    def _insert(self, sql, params):
        def interaction(txn):
            txn.execute(sql, params)
            txn.execute('SELECT ' + self.identity_function)
            lastid = txn.fetchone()[0]
            return lastid

        id_ = yield self.db_pool.runInteraction(interaction)
        defer.returnValue(id_)
