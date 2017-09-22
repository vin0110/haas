import logging

import click

import haascli
from haascli import Defaults
from haascli import cluster as haascli_cluster
from haascli import stack as haascli_stack
from haascli import data as haascli_data


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--debug/--no-debug', default=False)
@click.option('--exec/--no-exec', default=True)
# @click.option('--provider', type=click.Choice(['aws', 'azure']),
#               default='aws')
@click.option('--config_dir',
              type=click.Path(exists=True, resolve_path=True),
              default=Defaults['haas_dir'],
              help="The haas configuration directory (default: {})".format(
                  Defaults['haas_dir']))
@click.option('-L', '--log-file',
              help='set log file; default "{}"; "-" for stdout'
              .format(Defaults['log_file']))
@click.option('-i', '--identity', help="PEM file")
@click.option('-u', '--username',
              help="user name in AMI (default: {})".format(
                  Defaults['username']))
@click.option('-r', '--region',
              help='AWS region name (default: {})'.format(Defaults['region']))
@click.option('-k', '--key', help='AWS key')
@click.option('-s', '--secret', help='AWS secret key')
@click.pass_context
def cli(ctx, **kwargs):
    """This is a command line tool for HPCC-as-a-Service (HaaS)
    """
    # seed obj dict with defaults; then overwrite with rcfile; last
    # overwrit with cmd-line params
    try:
        ctx.obj.update(Defaults)
    except AttributeError:
        # if obj is None
        ctx.obj = Defaults
        ctx.obj['d'] = 'f'
    # conditional update; do not update if none
    for k, v in kwargs.items():
        if v:
            ctx.obj[k] = v

    try:
        f = open(haascli.RCFILE)
        for n, line in enumerate(f.readlines()):
            try:
                key, val = line.split('=', 1)
                key = key.strip()
                if key in Defaults:
                    val = val.strip()
                    if val.lower() in ['t', 'true', 'yes', 'y']:
                        ctx.obj[key] = True
                    elif val.lower() in ['f', 'false', 'no', 'n']:
                        ctx.obj[key] = False
                    else:
                        ctx.obj[key] = val
                else:
                    print(click.style('unknown parameter {} in rc file {} '
                                      'at line {}'.format(
                                          key, haascli.RCFILE, n+1), fg='red'))
                    ctx.abort()
            except ValueError:
                print(click.style('error in rc file {} at line {}'.format(
                    haascli.RCFILE, n+1), fg='red'))
                ctx.abort()
    except IOError:
        # no rcfile; go on
        pass

    haascli.setup_logging(
        level=logging.DEBUG if kwargs['debug'] else logging.INFO,
        file=ctx.obj['log_file'])


cli.add_command(haascli_stack.cli, name='stack')
cli.add_command(haascli_cluster.cli, name='cluster')
cli.add_command(haascli_data.cli, name='data')
