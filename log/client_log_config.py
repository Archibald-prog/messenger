import os
import sys
import logging

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(CURRENT_DIR, 'logs/client.log')

CLIENT_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setLevel(logging.DEBUG)
STREAM_HANDLER.setFormatter(CLIENT_FORMATTER)

FILE_HANDLER = logging.FileHandler(PATH, encoding='utf-8')
FILE_HANDLER.setFormatter(CLIENT_FORMATTER)

LOGGER = logging.getLogger('client')
# LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(FILE_HANDLER)
LOGGER.setLevel(logging.DEBUG)

if __name__ == '__main__':
    LOGGER.debug('debug message')
    LOGGER.info('info message')
    LOGGER.warning('warning message')
    LOGGER.error('error message')
    LOGGER.critical('critical short')
