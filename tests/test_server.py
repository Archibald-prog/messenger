import os
import sys
import unittest
from common.utils import PrepareConnection
from server import Server

sys.path.append(os.path.join(os.getcwd(), '..'))
filepath = os.path.join(sys.path[-1], 'common', 'config.json')


class TestServer(unittest.TestCase):
    CONFIGS = PrepareConnection.load_configs(self=PrepareConnection, path_to_configs=filepath)

    ok_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): 111111.111111,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'Guest'
        }
    }
    no_action_message = {
        CONFIGS.get('TIME'): 111111.111111,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'Guest'
        }
    }
    wrong_action_message = {
        CONFIGS.get('ACTION'): 'wrong',
        CONFIGS.get('TIME'): 111111.111111,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'Guest'
        }
    }
    no_time_message = {
        CONFIGS.get('ACTION'): 'wrong',
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'Guest'
        }
    }
    no_user_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): 111111.111111
    }
    wrong_user_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): 111111.111111,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'some_other_name'
        }
    }
    expected_response_ok = {CONFIGS.get('RESPONSE'): 200}
    expected_response_er = {
        CONFIGS.get('RESPONSE'): 400,
        CONFIGS.get('ERROR'): 'Bad Request'
    }

    def test_success_check(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.ok_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_ok)

    def test_no_action(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.no_action_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_er)

    def test_wrong_action(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.wrong_action_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_er)

    def test_no_time(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.no_time_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_er)

    def test_no_user(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.no_user_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_er)

    def test_wrong_user(self):
        actual_response = Server.process_client_message(self=Server,
                                                        message=self.wrong_user_message,
                                                        CONFIGS=self.CONFIGS)
        self.assertEqual(actual_response, self.expected_response_er)


if __name__ == '__main__':
    unittest.main()
