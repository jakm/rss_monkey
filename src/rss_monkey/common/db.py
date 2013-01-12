# -*- coding: utf8 -*-

from sqlalchemy.util import ThreadLocalRegistry

from rss_monkey.common.utils import log_function_call


class DbRegistry(object):
    session_registry = None

    def __init__(self):
        def new_db():
            db = Db()
            db.session = self.session_registry()
            return db

        self.db_registry = ThreadLocalRegistry(new_db)

    def __call__(self):
        return self.db_registry()


class Db(object):
    session = None

    def load(self, cls, **kwargs):
        return self.session.query(cls).filter_by(**kwargs).one()

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

    def query(self, *entities, **kwargs):
        return self.session.query(*entities, **kwargs)

    def execute(self, clause, params=None, mapper=None, bind=None, **kw):
        return self.session.execute(clause, params, mapper, bind, **kw)

    def commit(self):
        self._commit()

    def rollback(self):
        self._rollback()

    @log_function_call
    def _commit(self):
        self.session.commit()

    @log_function_call
    def _rollback(self):
        self.session.rollback()
