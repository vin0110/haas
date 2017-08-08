import os
import logging
import click


__version__ = '0.0.1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


logger = logging.getLogger('haascli')


def error(msg, *args, **kwargs):
    msg_output = "ERROR: " + msg.format(*args, **kwargs)
    # msg = "ERROR: " + ' '.join(args)
    logger.error(click.style(msg_output, fg='red'))


def warning(msg, *args, **kwargs):
    msg_output = msg.format(*args, **kwargs)
    # msg = ' '.join(args)
    logger.warning(click.style(msg_output, fg='yellow'))


def debug(msg, *args, **kwargs):
    if isinstance(msg, str):
        msg_output = msg.format(*args, **kwargs)
        logger.debug(msg_output)
    else:
        logger.debug(str(msg))
    # logger.debug(click.style(msg_output, fg='green'))


def message(msg, *args, **kwargs):
    if isinstance(msg, str):
        if (len(args) > 0) or (len(kwargs) > 0):
            msg_output = msg.format(*args, **kwargs)
            logger.info(msg_output)
        else:
            logger.info(msg)
    else:
        logger.info(str(msg))


def bad_response(response):
    '''Checks status code from boto response; return True if bad
    '''
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        error('status code',
              response['ResponseMetadata']['HTTPStatusCode'])
        return True


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(message)s'
    )
