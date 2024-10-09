import os
import sys
import unittest

from common.utils import PrepareConnection
from client import Client

sys.path.append(os.path.join(os.getcwd(), '..'))
filepath = os.path.join(sys.path[-1], 'common', 'config.json')


class TestClient(unittest.TestCase):
    CONFIGS = PrepareConnection.load_configs(self=PrepareConnection, path_to_configs=filepath)

    expected_pres_message = {
        CONFIGS.get('ACTION'): CONFIGS.get('PRESENCE'),
        CONFIGS.get('TIME'): 1.1,
        CONFIGS.get('USER'): {
            CONFIGS.get('ACCOUNT_NAME'): 'Guest'
        }
    }
    test_ok_message = {CONFIGS.get('RESPONSE'): 200}
    test_er_message = {
        CONFIGS.get('RESPONSE'): 400,
        CONFIGS.get('ERROR'): 'Bad Request'
    }
    expected_ok_response = '200: OK'
    expected_er_response = '400: Bad Request'

    def test_create_presence(self):
        actual_pres_message = Client.create_presence(self=Client, CONFIGS=self.CONFIGS,
                                                     account_name='Guest')
        actual_pres_message[self.CONFIGS.get('TIME')] = 1.1
        self.assertEqual(actual_pres_message, self.expected_pres_message)

    def test_correct_answer(self):
        actual_ok_response = Client.process_response(self=Client,
                                                     message=self.test_ok_message,
                                                     CONFIGS=self.CONFIGS)
        self.assertEqual(actual_ok_response, self.expected_ok_response)

    def test_bad_request(self):
        actual_er_response = Client.process_response(self=Client,
                                                     message=self.test_er_message,
                                                     CONFIGS=self.CONFIGS)
        self.assertEqual(actual_er_response, self.expected_er_response)


if __name__ == '__main__':
    unittest.main()
