import click
import os
import haascli.config
import haascli.cluster
import haascli.stack
import haascli.data

__version__ = '0.0.1'

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def error(*args):
    msg = "ERROR: " + ' '.join(args)
    click.echo(click.style(msg, fg='red'))


def warning(*args):
    msg = ' '.join(args)
    click.echo(click.style(msg, fg='yellow'))


def message(*args):
    msg = ' '.join(args)
    click.echo(msg)


def bad_response(response):
    '''Checks status code from boto response; return True if bad
    '''
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        error('status code',
              response['ResponseMetadata']['HTTPStatusCode'])
        return True
