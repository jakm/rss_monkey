# -*- coding: utf8 -*-

import functools
import logging
from threading import Lock
from twisted.internet import threads


def singleton(cls):
    """
    Decorator. Create singleton from decorated class.
    """

    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance


def defer_to_thread(fnc):
    """
    Decorator. Decorated function will be executed in deferred thread.
    """
    @functools.wraps(fnc)
    def wrapper(*args, **kwargs):
        return threads.deferToThread(fnc, *args, **kwargs)
    return wrapper


def log_function_call(function=None, level=logging.DEBUG, log_params=True, log_result=True):
    """
    Decorator. Decorated class will be logged in entry and exit point.

    @param level int, logging level when decorate function
    @param log_params bool, Log full listing of parameters
    @param log_result bool, Log full listing of result
    """
    def decorator(function):
        if logging.root.level <= level:
            @functools.wraps(function)
            def logging_wrapper(*args, **kwargs):
                logger = logging.getLogger(function.__module__)
                if logger.level == logging.NOTSET:
                    logger.setLevel(logging.root.level)

                with log_function_call.lock:
                    call_order = log_function_call.call_order
                    log_function_call.call_order += 1

                params = '...'
                if log_params:
                    args_ = ','.join(map(str, args))
                    kwargs_ = ','.join(['%s=%s' %
                        (str(k), str(v)) for k, v in kwargs.iteritems()])
                    params = ','.join([x for x in (args_, kwargs_) if x != ''])
                logger.log(level, '[%d] Called: %s(%s)', call_order, function.__name__, params)

                result = function(*args, **kwargs)

                if log_result:
                    logger.log(level, '[%d] Result: %s', call_order, result)
                else:
                    logger.log(level, '[%d] Return', call_order)

                return result
            return logging_wrapper
        else:
            @functools.wraps(function)
            def dummy_wrapper(*args, **kwargs):
                return function(*args, **kwargs)
            return dummy_wrapper

    if not function:  # User passed in some optional argument
        def waiting_for_func(function):
            return decorator(function)
        return waiting_for_func
    else:
        return decorator(function)
log_function_call.lock = Lock()
log_function_call.call_order = 0
