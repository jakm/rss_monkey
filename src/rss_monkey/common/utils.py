# -*- coding: utf8 -*-

import logging
from threading import Lock
from twisted.internet import threads


def defer_to_thread(fnc):
    def wrapper(*args, **kwargs):
        return threads.deferToThread(fnc, *args, **kwargs)
    wrapper.__name__ = fnc.__name__
    wrapper.__doc__ = fnc.__doc__
    return wrapper


def log_function_call(level=logging.DEBUG, log_params=True, log_result=True):
    log_function_call.lock = Lock()
    log_function_call.call_order = 0

    def decorator(fnc):
        if logging.root.level <= level:
            def logging_wrapper(*args, **kwargs):
                module_name = fnc.__module__
                logger = logging.getLogger(module_name)
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
                    params = '%s,%s' % (args_, kwargs_)
                logger.log(level, '[%d] Called: %s(%s)', call_order, fnc.__name__, params)

                result = fnc(*args, **kwargs)

                if log_result:
                    logger.log(level, '[%d] Result: %s', call_order, result)
                else:
                    logger.log(level, '[%d] Return', call_order)

                return result

            logging_wrapper.__name__ = fnc.__name__
            logging_wrapper.__doc__ = fnc.__doc__
            return logging_wrapper
        else:
            def dummy_wrapper(*args, **kwargs):
                return fnc(*args, **kwargs)
            dummy_wrapper.__name__ = fnc.__name__
            dummy_wrapper.__doc__ = fnc.__doc__
            return dummy_wrapper
    return decorator
