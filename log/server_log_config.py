import os
import sys
import logging.handlers

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(CURRENT_DIR, 'logs/server.log')

SERVER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setLevel(logging.DEBUG)
STREAM_HANDLER.setFormatter(SERVER_FORMATTER)

FILE_HANDLER = logging.handlers.TimedRotatingFileHandler(
    PATH, encoding='utf-8', interval=1, backupCount=10, when='D'
)
FILE_HANDLER.setFormatter(SERVER_FORMATTER)

LOGGER = logging.getLogger('server')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(STREAM_HANDLER)
LOGGER.addHandler(FILE_HANDLER)

if __name__ == '__main__':
    LOGGER.debug('debug message')
    LOGGER.info('info message')
    LOGGER.warning('warning message')
    LOGGER.error('error message')
    LOGGER.critical('critical short')
