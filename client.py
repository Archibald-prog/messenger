import os.path
import json
import logging
import threading
import sys
import time
from socket import socket, AF_INET, SOCK_STREAM
from common.utils import OperateMessage, PrepareConnection
from common.decorators import Log
from common.metaclasses import ClientMaker
from log import client_log_config

CLIENT_LOGGER = logging.getLogger('client')


class ClientSender(threading.Thread, OperateMessage):
    def __init__(self, account_name, sock, CONFIGS):
        self.account_name = account_name
        self.sock = sock
        self.configs = CONFIGS
        super().__init__()

    def create_exit_message(self):
        return {
            self.configs.get('ACTION'): self.configs.get('EXIT'),
            self.configs.get('TIME'): time.ctime(),
            self.configs.get('ACCOUNT_NAME'): self.account_name
        }

    def create_message(self):
        to_user = input('Введите имя адресата сообщения: ')
        message = input('Введите текст сообщения: ')
        message_dict = {
            self.configs.get('ACTION'): self.configs.get('MESSAGE'),
            self.configs.get('SENDER'): self.account_name,
            self.configs.get('DESTINATION'): to_user,
            self.configs.get('TIME'): time.ctime(),
            self.configs.get('MESSAGE_TEXT'): message
        }
        CLIENT_LOGGER.debug(f'Словарь сообщения: {message_dict}')
        try:
            self.send_message(self.sock, message_dict, self.configs)
            CLIENT_LOGGER.info(f'Отправлено сообщение '
                               f'для пользователя {to_user}.')
        except:
            CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
            sys.exit(1)

    def run(self):
        print(f'Пользователь {self.account_name}.')
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                self.send_message(self.sock,
                                  self.create_exit_message(),
                                  self.configs)
                print(f'Завершение соединения.')
                CLIENT_LOGGER.info(f'Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана. help - вывести поддерживаемые команды.')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Адресат и текст будут запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


class ClientReader(threading.Thread, OperateMessage):
    def __init__(self, account_name, sock, CONFIGS):
        self.account_name = account_name
        self.sock = sock
        self.configs = CONFIGS
        super().__init__()

    def run(self):
        while True:
            try:
                message = self.get_message(self.sock, self.configs)
                if self.configs.get('ACTION') in message \
                        and message[self.configs.get('ACTION')] == 'message' \
                        and self.configs.get('SENDER') in message \
                        and self.configs.get('DESTINATION') in message \
                        and self.configs.get('MESSAGE_TEXT') in message \
                        and message[self.configs.get('DESTINATION')] == self.account_name:
                    print(f"\nПолучено сообщение от пользователя "
                          f"{message[self.configs.get('SENDER')]}:\n"
                          f"{message[self.configs.get('MESSAGE_TEXT')]}")
                    CLIENT_LOGGER.info(f"Получено сообщение от пользователя "
                                       f"{message[self.configs.get('SENDER')]}:\n"
                                       f"{message[self.configs.get('MESSAGE_TEXT')]}")
                else:
                    CLIENT_LOGGER.error(f'Некорректное сообщение от сервера: {message}.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break


class OperateClient(OperateMessage, PrepareConnection, metaclass=ClientMaker):
    @Log()
    def create_presence(self, CONFIGS, account_name):
        presence_message = {
            CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
            CONFIGS.get('TIME'): time.ctime(),
            CONFIGS.get('USER'): {
                CONFIGS.get('ACCOUNT_NAME'): account_name
            }
        }
        CLIENT_LOGGER.info(f"Сформировано сообщение "
                           f"пользователя {account_name}.")
        return presence_message

    @Log()
    def process_response(self, message, CONFIGS):
        if CONFIGS.get('RESPONSE') in message:
            if message[CONFIGS.get('RESPONSE')] == 200:
                CLIENT_LOGGER.info(f'Успешная обработка сообщения от сервера.')
                return '200: OK'
            CLIENT_LOGGER.critical(f'Не удалось обработать сообщение от сервера.')
            return f'400: {message[CONFIGS.get("ERROR")]}'
        raise ValueError

    def init_client(self, addr, client_name, CONFIGS):
        try:
            transport = socket(AF_INET, SOCK_STREAM)
            transport.connect(addr)
            presence_message = self.create_presence(CONFIGS, client_name)
            self.send_message(transport, presence_message, CONFIGS)
            answer = self.process_response(self.get_message(transport, CONFIGS),
                                           CONFIGS)
            CLIENT_LOGGER.info(f'Установлено соединение с сервером. '
                               f'Ответ сервера: {answer}.')
            return transport
        except(ValueError, json.JSONDecodeError):
            CLIENT_LOGGER.critical(f'Не удалось декодировать сообщение сервера.')
            sys.exit(1)

    @classmethod
    def main(cls, path_to_config):
        print(f'Консольный месседжер. Клиентский модуль.')

        CONFIGS = cls.load_configs(path_to_config, is_server=False)
        address, client_name = cls.parse_argv(CONFIGS, is_server=False)

        if not client_name:
            client_name = input('Введите имя пользователя: ')

        CLIENT_LOGGER.info(f'Запущен клиент с параметрами: {address},'
                           f'имя: {client_name}.')

        client_sock = cls.init_client(cls(), address, client_name, CONFIGS)
        # если соединение прошло успешно
        receiver = ClientReader(client_name, client_sock, CONFIGS)
        receiver.daemon = True
        receiver.start()

        sender = ClientSender(client_name, client_sock, CONFIGS)
        sender.daemon = True
        sender.start()
        CLIENT_LOGGER.info(f'Запущены процессы.')

        while True:
            time.sleep(1)
            if receiver.is_alive() and sender.is_alive():
                continue
            break


if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(CURRENT_DIR, 'common', 'config.json')
    OperateClient.main(filepath)
