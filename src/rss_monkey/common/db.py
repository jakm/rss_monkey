# -*- coding: utf8 -*-

from rss_monkey.common.utils import log_function_call


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
