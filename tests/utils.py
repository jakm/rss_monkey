# -*- coding: utf8 -*-

import new

from mock import MagicMock
from springpython.config import (Object, PythonConfig)
from springpython.context import ApplicationContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class ContainerMock(PythonConfig):
    def __init__(self, objects):
        super(ContainerMock, self).__init__()

        for object_name, callable_obj in objects.iteritems():
            if callable_obj.func_name == '<lambda>':
                callable_obj.func_name = object_name
            decorated = Object(callable_obj, lazy_init=True)
            method = new.instancemethod(decorated, self, self.__class__)
            self.__dict__[object_name] = method

    def get_context(self):
        return ApplicationContext(self)


def DbMock(db_class, metadata):
    engine = create_engine('sqlite:///:memory:',
        connect_args={'check_same_thread': False}, poolclass=StaticPool)

    if metadata:
        metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    db = db_class()
    db.session = session

    mock = MagicMock()
    mock._session = session
    mock._db = db
    mock.load.side_effect = lambda cls, id: mock._db.load(cls, id)

    def store(object, commit=False):
        return mock._db.store(object, commit)
    mock.store.side_effect = store

    def store_all(object, commit=False):
        return mock._db.store_all(object, commit)
    mock.store_all.side_effect = store_all
    mock.query.side_effect = lambda entities: mock._db.query(entities) # TODO: mock pro query
    mock.commit.side_effect = lambda: mock._db.commit()
    mock.rollback.side_effect = lambda: mock._db.rollback()

    return mock
