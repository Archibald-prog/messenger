import os
import sys
import unittest
import json
from common.utils import PrepareConnection, OperateMessage

sys.path.append(os.path.join(os.getcwd(), '..'))
filepath = os.path.join(sys.path[-1], 'common', 'config.json')


class TestConnection(unittest.TestCase):
    CONFIGS = (PrepareConnection.load_configs
               (self=PrepareConnection, path_to_configs=filepath))
    expected_configs = {
        "DEFAULT_IP_ADDRESS": "127.0.0.1",
        "DEFAULT_PORT": 7777,
        "MAX_CONNECTIONS": 5,
        "MAX_PACKAGE_SIZE": 1024,
        "ENCODING": "utf-8",
        "ACTION": "action",
        "TIME": "time",
        "USER": "user",
        "ACCOUNT_NAME": "account_name",
        "SENDER": "from",
        "DESTINATION": "to",
        "PRESENCE": "presence",
        "RESPONSE": "response",
        "ERROR": "error",
        "LOGGING_LEVEL": 10,
        "MESSAGE": "message",
        "MESSAGE_TEXT": "message_text",
        "EXIT": "exit"
    }

    def test_load_configs(self):
        actual_configs = PrepareConnection.load_configs(self=PrepareConnection, path_to_configs=filepath)
        self.assertEqual(actual_configs, self.expected_configs)

    # def test_server_parse_argv(self):
    #     expected_serv_addr = ('', 7777)
    #     actual_serv_addr = PrepareConnection.parse_argv(self=PrepareConnection, configs=self.CONFIGS)
    #     self.assertEqual(actual_serv_addr, expected_serv_addr)
    #     self.assertEqual(type(actual_serv_addr), tuple)
    #
    # def test_client_parse_argv(self):
    #     expected_client_addr = ('127.0.0.1', 7777)
    #     actual_client_addr = PrepareConnection.parse_argv(self=PrepareConnection, configs=self.CONFIGS, is_server=False)
    #     self.assertEqual(actual_client_addr, expected_client_addr)
    #     self.assertEqual(type(actual_client_addr), tuple)


class TestSocket:
    CONFIGS = (PrepareConnection.load_configs
               (self=PrepareConnection, path_to_configs=filepath))

    def __init__(self, test_message):
        self.test_message = test_message
        self.expected_message = None
        self.actual_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_message)
        self.expected_message = json_test_message.encode(self.CONFIGS.get('ENCODING'))
        self.actual_message = message_to_send

    def recv(self, buf_size):
        json_test_message = json.dumps(self.test_message)
        return json_test_message.encode(self.CONFIGS.get('ENCODING'))


class TestOperateMessage(unittest.TestCase):
    CONFIGS = (PrepareConnection.load_configs
               (self=PrepareConnection, path_to_configs=filepath))

    test_message_send = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): 111111.111111,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'test_test'
        }
    }
    test_success_receive = {CONFIGS.get('RESPONSE'): 200}
    test_error_receive = {
        CONFIGS.get('RESPONSE'): 400,
        CONFIGS.get('ERROR'): 'Bad Request'
    }

    def test_send_message(self):
        test_sock = TestSocket(self.test_message_send)
        OperateMessage.send_message(self=OperateMessage, sock=test_sock,
                                    message=self.test_message_send, configs=self.CONFIGS)
        self.assertEqual(test_sock.actual_message, test_sock.expected_message)
        with self.assertRaises(Exception):
            OperateMessage.send_message(self=OperateMessage, sock=test_sock,
                                        message=test_sock, configs=self.CONFIGS)

    def test_get_message(self):
        test_sock_ok = TestSocket(self.test_success_receive)
        test_sock_er = TestSocket(self.test_error_receive)
        get_ok_message = OperateMessage.get_message(self=OperateMessage, sock=test_sock_ok,
                                                    configs=self.CONFIGS)
        get_er_message = OperateMessage.get_message(self=OperateMessage, sock=test_sock_er,
                                                    configs=self.CONFIGS)
        self.assertEqual(get_ok_message, self.test_success_receive)
        self.assertEqual(get_er_message, self.test_error_receive)


if __name__ == '__main__':
    unittest.main()
