import os
import logging

import coloredlogs


__version__ = '0.0.1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = '/tmp/haas.log'

logger = logging.getLogger(__name__)


def bad_response(response):
    '''Checks status code from boto response; return True if bad
    '''
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        logger.error('status code ' +
                     response['ResponseMetadata']['HTTPStatusCode'])
        return True


def setup_logging(level=logging.INFO, file=DEFAULT_LOG):
    '''create file hamdler'''
    logger.setLevel(level)
    if file == '-':
        # create console handler for error
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_fmt = '%(name)s:%(levelname)s:%(message)s'
        console_formatter = logging.Formatter(console_fmt)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        coloredlogs.install(level=level, logger=logger)
    else:
        if file:
            file_handler = logging.FileHandler(file)
        else:
            file_handler = logging.FileHandler(DEFAULT_LOG)
        file_handler.setLevel(level)
        file_fmt = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        file_formatter = logging.Formatter(file_fmt)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
