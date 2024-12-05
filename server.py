import socket
import os
import logging
import select
import threading
from common.utils import OperateMessage, PrepareConnection
from common.decorators import log
from common.descriptors import Address, Port
from common.metaclasses import ServerMaker
from server_database import ServerStorage
from log import server_log_config

SERVER_LOGGER = logging.getLogger('server')


class OperateServer(OperateMessage, threading.Thread, metaclass=ServerMaker):
    address = Address()
    port = Port()

    def __init__(self, listen_address, listen_port, CONFIGS, database):
        self.address = listen_address
        self.port = listen_port
        self.configs = CONFIGS
        self.database = database

        self.clients = []
        self.messages = []
        self.names = dict()
        super().__init__()

    def init_socket(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv_sock.bind((self.address, self.port))
        serv_sock.settimeout(0.5)

        self.sock = serv_sock
        self.sock.listen(self.configs.get('MAX_CONNECTIONS'))

    def run(self):
        self.init_socket()

        while True:
            try:
                client_sock, addr = self.sock.accept()
            except OSError:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соединение с ПК {addr}.')
                self.clients.append(client_sock)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = (
                        select.select(self.clients, self.clients, [], 0))
            except OSError:
                pass

            if recv_data_lst:
                for sending_client in recv_data_lst:
                    try:
                        self.process_client_message(
                            self.get_message(sending_client, self.configs),
                            sending_client)
                    except:
                        SERVER_LOGGER.info(f'Клиент {sending_client.getpeername()} '
                                           f'отключился.')
                        self.clients.remove(sending_client)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    SERVER_LOGGER.info(f"Связь с клиентом {message['DESTINATION']} "
                                       f"была потеряна.")
                    self.clients.remove(self.names[message['DESTINATION']])
                    del self.names[message['DESTINATION']]
            self.messages.clear()

    @log
    def process_client_message(self, message, client_sock):
        SERVER_LOGGER.debug(f'Принято сообщение от клиента: {message}.')
        if self.configs.get('ACTION') in message \
                and message[self.configs.get('ACTION')] == self.configs.get('PRESENCE') \
                and self.configs.get('TIME') in message \
                and self.configs.get('USER') in message:
            if message[self.configs.get('USER')][self.configs.get('ACCOUNT_NAME')] not in self.names.keys():
                self.names[message[self.configs.get('USER')][self.configs.get('ACCOUNT_NAME')]] = client_sock
                client_ip, client_port = client_sock.getpeername()
                self.database.user_login(message[self.configs.get('USER')][self.configs.get('ACCOUNT_NAME')],
                                         client_ip, client_port)
                self.send_message(client_sock, {self.configs.get('RESPONSE'): 200}, self.configs)
                return
            else:
                response = {self.configs.get('RESPONSE'): 400,
                            self.configs.get('ERROR'): 'Имя пользователя уже занято.'}
                self.send_message(client_sock, response, self.configs)
                self.clients.remove(client_sock)
                client_sock.close()
            return
        elif self.configs.get('ACTION') in message \
                and message[self.configs.get('ACTION')] == self.configs.get('MESSAGE') \
                and self.configs.get('DESTINATION') in message \
                and self.configs.get('TIME') in message \
                and self.configs.get('SENDER') in message \
                and self.configs.get('MESSAGE_TEXT') in message:
            self.messages.append(message)
            return
        elif self.configs.get('ACTION') in message \
                and message[self.configs.get('ACTION')] == self.configs.get('EXIT') \
                and self.configs.get('ACCOUNT_NAME') in message:
            self.database.user_logout(message['ACCOUNT_NAME'])
            self.clients.remove(self.names[message['ACCOUNT_NAME']])
            self.names[message['ACCOUNT_NAME']].close()
            del self.names[message['ACCOUNT_NAME']]
            return
        else:
            response = {self.configs.get('RESPONSE'): 400,
                        self.configs.get('ERROR'): 'Запрос некорректен.'}
            self.send_message(client_sock, response, self.configs)
            print(f'response 400: {response}')
            return

    def process_message(self, message, listen_sockets):
        if message[self.configs.get('DESTINATION')] in self.names \
                and self.names[message[self.configs.get('DESTINATION')]] in listen_sockets:
            self.send_message(self.names[message[self.configs.get('DESTINATION')]],
                              message, self.configs)
            SERVER_LOGGER.info(f"Отправлено сообщение пользователю "
                               f"{message[self.configs.get('DESTINATION')]}."
                               f"От пользователя {message[self.configs.get('SENDER')]}.")
        elif message[self.configs.get('DESTINATION')] in self.names \
                and self.names[message[self.configs.get('DESTINATION')]] not in listen_sockets:
            SERVER_LOGGER.error(f"Пользователь {message[self.configs.get('DESTINATION')]} "
                                f"не зарегистрирован. ")

    def print_help(self):
        print('Поддерживаемые команды:')
        print('users - список известных пользователей')
        print('connected - список подключенных пользователей')
        print('loghist - история входов пользователя')
        print('exit - завершение работы сервера.')
        print('help - вывод справки по поддерживаемым командам')


class StartServer(PrepareConnection, OperateServer):

    @classmethod
    def main(cls, path_to_config):
        CONFIGS = cls.load_configs(path_to_config)
        listen_address, listen_port = cls.parse_argv(CONFIGS)

        database = ServerStorage(CONFIGS)

        server = OperateServer(listen_address, listen_port, CONFIGS, database)
        server.daemon = True
        server.start()

        server.print_help()

        while True:
            command = input('Введите команду: ')
            if command == 'help':
                server.print_help()
            elif command == 'exit':
                break
            elif command == 'users':
                for user in sorted(database.users_list()):
                    print(f'Пользователь {user[0]}, последний вход: {user[1]}')
            elif command == 'connected':
                for user in sorted(database.active_users_list()):
                    print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, '
                          f'время подключения: {user[3]}')
            elif command == 'loghist':
                name = input('Введите имя пользователя. '
                             'Для вывода всей истории просто нажмите Enter: ')
                for user in sorted(database.login_history(name)):
                    print(f'Пользователь: {user[0]} время входа: {user[1]}. '
                          f'Вход с: {user[2]}:{user[3]}')
            else:
                print('Команда не распознана.')


if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(CURRENT_DIR, 'common', 'config.json')
    StartServer.main(path_to_config=filepath)
