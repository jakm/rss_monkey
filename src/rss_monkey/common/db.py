# -*- coding: utf8 -*-

from sqlalchemy.orm.query import Query

from rss_monkey.common.utils import defer_to_thread, log_function_call


class SyncDb(object):
    session = None

    def load(self, cls, id):
        return self.session.query(cls).filter_by(id=id).one()

    def store(self, object, commit=False):
        self.session.add(object)
        if commit:
            self._commit()
        return object

    def store_all(self, objects, commit=False):
        self.session.add_all(objects)
        if commit:
            self._commit()
        return objects

    def query(self, entities):
        return self.session.query(entities)

    def commit(self):
        self._commit()

    def rollback(self):
        self._rollback()

    @log_function_call()
    def _commit(self):
        self.session.commit()

    @log_function_call()
    def _rollback(self):
        self.session.rollback()


class AsyncDb(object):
    session = None

    @defer_to_thread
    def load(self, cls, id):
        return self.session.query(cls).filter_by(id=id).one()

    @defer_to_thread
    def store(self, object, commit=False):
        self.session.add(object)
        if commit:
            self._commit()
        return object

    @defer_to_thread
    def store_all(self, objects, commit=False):
        self.session.add_all(objects)
        if commit:
            self._commit()
        return objects

    # this method is sychronous, because returns asynchronous query object
    def query(self, entities):
        return AsyncQuery(entities, self.session)

    @defer_to_thread
    def commit(self):
        self._commit()

    @defer_to_thread
    def rollback(self):
        self._rollback()

    @log_function_call()
    def _commit(self):
        self.session.commit()

    @log_function_call()
    def _rollback(self):
        self.session.rollback()


class AsyncQuery(Query):
    def __init__(self, entities, session=None):
        super(AsyncQuery, self).__init__(entities, session)

    @defer_to_thread
    def all(self):
        return super(AsyncQuery, self).all()

    @defer_to_thread
    def first(self):
        return super(AsyncQuery, self).first()

    @defer_to_thread
    def one(self):
        return super(AsyncQuery, self).one()
