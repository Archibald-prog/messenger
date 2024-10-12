import logging
import sys

SERVER_LOGGER = logging.getLogger('server')


class Port:

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            SERVER_LOGGER.critical(f'Попытка запуска с некорректного порта {value}.'
                                   f'Номер порта должен быть числом в диапазоне '
                                   f'от 1024 до 65535.')
            sys.exit(1)
        instance.__dict__[self.name] = value


class Address:

    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
