import click
import haascli.config
import haascli.cluster
import haascli.stack
import haascli.data

__version__ = '0.0.1'


def error(*args):
    msg = "ERROR: " + ' '.join(args)
    click.echo(click.style(msg, fg='red'))


def warning(*args):
    msg = ' '.join(args)
    click.echo(click.style(msg, fg='yellow'))


def bad_response(response):
    '''Checks status code from boto response; return True if bad
    '''
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        haascli.error('status code',
                      response['ResponseMetadata']['HTTPStatusCode'])
        return True
