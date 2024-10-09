import sys
import traceback
import inspect
import logging


if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def log(func):
    def log_saver(*args, **kwargs):
        result = func(*args, **kwargs)
        LOGGER.debug(f'Функция {func.__name__}.'
                     f'Параметры: {args}, {kwargs}.'
                     f'Модуль: {func.__module__}.'
                     f'Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}'
                     f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
        return result
    return log_saver


class Log:
    def __call__(self, func):
        def log_saver(*args, **kwargs):
            result = func(*args, **kwargs)
            LOGGER.debug(f'Функция {func.__name__}.'
                         f'Параметры: {args}, {kwargs}.'
                         f'Модуль: {func.__module__}.'
                         f'Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}'
                         f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
            return result

        return log_saver