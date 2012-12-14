# -*- coding: utf8 -*-

from springpython.config import PythonConfig  # ObjectContainer import depends on this line
from springpython.container import ObjectContainer
from springpython.context import ApplicationContext


class AppContext(object):
    _context = None

    @staticmethod
    def get_object(name, ignore_abstract=False):
        if not AppContext._context:
            raise RuntimeError('Application context is not installed')
        return AppContext._context.get_object(name, ignore_abstract)

    @staticmethod
    def install(context):
        if not isinstance(context, ObjectContainer):
            raise TypeError('Context has to inherit from ObjectContainer')
        AppContext._context = context


def install_context(app_config):
    global AppContext
    AppContext.install(ApplicationContext(app_config))
