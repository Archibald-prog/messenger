from socket import socket, AF_INET, SOCK_STREAM
import os
import logging
import select
from common.utils import OperateMessage, PrepareConnection
from common.decorators import log
from common.descriptors import Address, Port
from log import server_log_config

SERVER_LOGGER = logging.getLogger('server')


class OperateServer(OperateMessage):
    """
    The class contains methods for managing the server.
    """
    address = Address()
    port = Port()

    def __init__(self, listen_address, listen_port):
        self.address = listen_address
        self.port = listen_port

        self.clients = []
        self.messages = []
        self.names = dict()

    def init_socket(self, CONFIGS):
        serv_sock = socket(AF_INET, SOCK_STREAM)
        serv_sock.bind((self.address, self.port))
        serv_sock.settimeout(0.5)

        self.sock = serv_sock
        self.sock.listen(CONFIGS.get('MAX_CONNECTIONS'))

    def main_loop(self, CONFIGS):
        self.init_socket(CONFIGS)

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
                        self.process_client_message(self.get_message(sending_client, CONFIGS),
                                                    self.messages, sending_client,
                                                    self.clients, self.names, CONFIGS)
                    except:
                        SERVER_LOGGER.info(f'Клиент {sending_client.getpeername()} '
                                           f'отключился.')
                        self.clients.remove(sending_client)

            for i in self.messages:
                try:
                    self.process_message(i, self.names, send_data_lst, CONFIGS)
                except Exception:
                    SERVER_LOGGER.info(f"Связь с клиентом {i['DESTINATION']} "
                                       f"была потеряна.")
                    self.clients.remove(self.names[i['DESTINATION']])
                    del self.names[i['DESTINATION']]
            self.messages.clear()

    @log
    def process_client_message(self, message, messages_list, client_sock,
                               clients, names, CONFIGS):
        SERVER_LOGGER.debug(f'Принято сообщение от клиента: {message}.')
        if CONFIGS.get('ACTION') in message \
                and message[CONFIGS.get('ACTION')] == CONFIGS.get('PRESENCE') \
                and CONFIGS.get('TIME') in message \
                and CONFIGS.get('USER') in message:
            if message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')] not in names.keys():
                names[message[CONFIGS.get('USER')][CONFIGS.get('ACCOUNT_NAME')]] = client_sock
                self.send_message(client_sock, {CONFIGS.get('RESPONSE'): 200}, CONFIGS)
                return
            else:
                response = {CONFIGS.get('RESPONSE'): 400,
                            CONFIGS.get('ERROR'): 'Имя пользователя уже занято.'}
                self.send_message(client_sock, response, CONFIGS)
                clients.remove(client_sock)
                client_sock.close()
            return
        elif CONFIGS.get('ACTION') in message \
                and message[CONFIGS.get('ACTION')] == CONFIGS.get('MESSAGE') \
                and CONFIGS.get('DESTINATION') in message \
                and CONFIGS.get('TIME') in message \
                and CONFIGS.get('SENDER') in message \
                and CONFIGS.get('MESSAGE_TEXT') in message:
            messages_list.append(message)
            return
        elif CONFIGS.get('ACTION') in message \
                and message[CONFIGS.get('ACTION')] == CONFIGS.get('EXIT') \
                and CONFIGS.get('ACCOUNT_NAME') in message:
            clients.remove(names[message['ACCOUNT_NAME']])
            names[message['ACCOUNT_NAME']].close()
            del names[message['ACCOUNT_NAME']]
            return
        else:
            response = {CONFIGS.get('RESPONSE'): 400,
                        CONFIGS.get('ERROR'): 'Запрос некорректен.'}
            self.send_message(client_sock, response, CONFIGS)
            print(f'response 400: {response}')
            return

    def process_message(self, message, names, listen_sockets, CONFIGS):
        if message[CONFIGS.get('DESTINATION')] in names \
                and names[message[CONFIGS.get('DESTINATION')]] in listen_sockets:
            self.send_message(names[message[CONFIGS.get('DESTINATION')]], message, CONFIGS)
            SERVER_LOGGER.info(f"Отправлено сообщение пользователю "
                               f"{message[CONFIGS.get('DESTINATION')]}."
                               f"От пользователя {message[CONFIGS.get('SENDER')]}.")
        elif message[CONFIGS.get('DESTINATION')] in names \
                and names[message[CONFIGS.get('DESTINATION')]] not in listen_sockets:
            SERVER_LOGGER.error(f"Пользователь {message[CONFIGS.get('DESTINATION')]} "
                                f"не зарегистрирован. ")

class StartServer(PrepareConnection, OperateServer):
    """The class is responsible for initializing the server."""

    @classmethod
    def main(cls, path_to_config):

        CONFIGS = cls.load_configs(path_to_config)
        listen_address, listen_port = cls.parse_argv(CONFIGS)

        server = OperateServer(listen_address, listen_port)
        server.main_loop(CONFIGS)


if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(CURRENT_DIR, 'common', 'config.json')
    StartServer.main(path_to_config=filepath)
