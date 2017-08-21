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


def setup_logging(level=logging.INFO, file=None):
    '''create file hamdler'''

    coloredlogs.install(level=level, fmt='%(message)s', logger=logging.getLogger("haascli"))

    if file is not None:
        file_handler = logging.FileHandler(file)
        file_handler.setLevel(level)
        file_fmt = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        file_formatter = logging.Formatter(file_fmt)
        file_handler.setFormatter(file_formatter)
        logging.getLogger("haascli").addHandler(file_handler)
