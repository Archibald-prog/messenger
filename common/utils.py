import json
import os.path
import sys
import logging
import argparse
from .errors import ArgumentParserError
from log import server_log_config
from log import client_log_config

SERVER_LOGGER = logging.getLogger('server')
CLIENT_LOGGER = logging.getLogger('client')

class EnhancedArgParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        raise ArgumentParserError(message)


class PrepareConnection:
    """
    The class contains methods for loading project configurations
    and command line parameters.
    """

    @classmethod
    def load_configs(cls, path_to_configs, is_server=True):
        config_keys = [
            "DEFAULT_PORT",
            "MAX_CONNECTIONS",
            "MAX_PACKAGE_SIZE",
            "ENCODING",
            "SERVER_DATABASE",
            "ACTION",
            "TIME",
            "USER",
            "ACCOUNT_NAME",
            "SENDER",
            "DESTINATION",
            "PRESENCE",
            "RESPONSE",
            "ERROR",
            "LOGGING_LEVEL",
            "MESSAGE",
            "MESSAGE_TEXT",
            "EXIT"
        ]

        if not is_server:
            config_keys.append('DEFAULT_IP_ADDRESS')
        if not os.path.exists(path_to_configs):
            SERVER_LOGGER.critical(f'Файл конфигураций не найден.')
            sys.exit(1)

        with open(path_to_configs) as configs_file:
            CONFIGS = json.load(configs_file)
        loaded_config_keys = list(CONFIGS.keys())
        for key in config_keys:
            if key not in loaded_config_keys:
                SERVER_LOGGER.critical(f'В файле конфигураций '
                                       f'не хватает ключа {key}')
                sys.exit(1)
        return CONFIGS

    @classmethod
    def get_parser(cls, configs, is_server=True):
        parser = EnhancedArgParser()
        if not is_server:
            parser.add_argument('a', nargs='?',
                                default=configs.get('DEFAULT_IP_ADDRESS'))
            parser.add_argument('p', nargs='?',
                                default=configs.get('DEFAULT_PORT'), type=int)
            parser.add_argument('-n', '--name', default=None)
            return parser
        parser.add_argument('-p', default=configs.get('DEFAULT_PORT'), type=int,
                            help='Enter the port number the server will listen on')
        parser.add_argument('-a', default='', help='Enter the server IP-address')
        return parser

    @classmethod
    def parse_argv(cls, configs, is_server=True):
        if not is_server:
            parser = cls.get_parser(configs, is_server=False)
            namespace = parser.parse_args(sys.argv[1:])

            try:
                server_address = namespace.a
                server_port = namespace.p
                client_name = namespace.name
                if server_port < 1024 or server_port > 65535:
                    raise ValueError
            except ValueError:
                SERVER_LOGGER.critical(f'Попытка запуска с некорректного порта.'
                                       f'Номер порта должен быть числом в диапазоне '
                                       f'от 1024 до 65535.')
                sys.exit(1)
            address = (server_address, server_port)
            return address, client_name

        parser = cls.get_parser(configs)
        try:
            namespace = parser.parse_args(sys.argv[1:])
            listen_port = namespace.p
            listen_address = namespace.a
        except ArgumentParserError:
            print("\nRequired arguments were not specified!!!")
            sys.exit(2)

        SERVER_LOGGER.info(f'Сервер запущен на порту {listen_port} '
                           f'по адресу {listen_address}.')
        return listen_address, listen_port


class OperateMessage:
    """
    The class contains methods for receiving and sending messages.
    """

    def get_message(self, sock, configs):
        encoded_message = sock.recv(configs.get('MAX_PACKAGE_SIZE'))
        if isinstance(encoded_message, bytes):
            json_response = encoded_message.decode(configs.get('ENCODING'))
            dict_response = json.loads(json_response)
            if isinstance(dict_response, dict):
                return dict_response
            raise ValueError
        raise ValueError

    def send_message(self, sock, message, configs):
        json_response = json.dumps(message)
        encoded_data = json_response.encode(configs.get('ENCODING'))
        sock.send(encoded_data)
