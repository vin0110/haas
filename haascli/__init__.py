import os
import logging


__version__ = '0.0.1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = '/tmp/haas.log'
RCFILE = os.path.join(os.path.expanduser('~'), '.haasrc')

#############
# default values
# any key that is allowable in the rcfile, must be defined in this dict.
#############
Defaults = dict(
    haas_dir=os.path.join(os.path.expanduser('~'), '.haas'),
    region='us-east-1',
    bucket='hpcc_checkpoint',
    username='ubuntu',
    log_file=DEFAULT_LOG,
    identity=RCFILE,
    key=None,
    secret=None,
    debug=None,
    test=None,
    )


logger = logging.getLogger(__name__)

# create console handler for error
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
console_fmt = '%(name)s:%(levelname)s:%(message)s'
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
    logger.setLevel(level)

    if file == '-':
        console_handler.setLevel(level)
    else:
        if file is None:
            file_handler = logging.FileHandler(DEFAULT_LOG)
        elif file:
            file_handler = logging.FileHandler(file)
        file_fmt = '%(asctime)s:%(name)s:%(levelname)s:%(message)s'
        file_formatter = logging.Formatter(file_fmt)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
