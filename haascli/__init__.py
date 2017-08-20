import os
import logging
import click


__version__ = '0.0.1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = '/tmp/haas.log'

logger = logging.getLogger(__name__)

# create console handler for error
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_fmt = click.style('%(name)s:%(levelname)s:%(message)s', fg='red')
console_formatter = logging.Formatter(console_fmt)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def bad_response(response):
    '''Checks status code from boto response; return True if bad
    '''
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        logger.error('status code ' +
                     response['ResponseMetadata']['HTTPStatusCode'])
        return True


def setup_logging(level=logging.INFO, file=DEFAULT_LOG):
    '''create file hamdler'''
    if file == '-':
        console_handler.setLevel(level)
    else:
        file_fmt = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        if file:
            file_handler = logging.FileHandler(file)
        else:
            file_handler = logging.FileHandler(DEFAULT_LOG)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(file_fmt)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
