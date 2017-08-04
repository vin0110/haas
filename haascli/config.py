import os
import enum
import contextlib

import click
import executor
import yaml

from haascli import message, error, debug
from haascli.utils import Singleton


class HaasConfigurationKey(enum.Enum):
    AWS_ACCESS_KEY_ID = 'aws_access_key_id'
    AWS_SECRET_ACCESS_KEY_ID = 'aws_secret_access_key_id'
    AWS_REGION_NAME = 'aws_region_name'
    HAAS_EC2_KEY_PAIR = 'haas_ec2_key_pair'
    HAAS_SERVICE_NUM_NODES = 'haas_service_num_nodes'
    HAAS_WORKER_NUM_NODES = 'haas_worker_num_nodes'
    HAAS_SERVICE_INSTANCE_TYPE = 'haas_service_instance_type'
    HAAS_WORKER_INSTANCE_TYPE = 'haas_worker_instance_type'
    HAAS_EBS_VOLUME_SIZE = 'haas_ebs_volume_size'


class HaaSConfiguration(object):
    @staticmethod
    def load(config_path):
        debug("Loading config from {}", config_path)
        with open(config_path, 'r') as f:
            config_raw = yaml.load(f)
            config = {HaasConfigurationKey[k.upper()]: v for k, v in config_raw.items()}
            debug(config)
            return HaaSConfiguration(config)

    @staticmethod
    def dump(config, config_path):
        debug("Writing config to {}", config_path)
        with open(config_path, 'w') as f:
            config_raw = {k.value: v for k, v in config.config.items()}
            yaml.dump(config_raw, f, default_flow_style=False)

    def __init__(self, config):
        self.config = config

    def to_file(self, config_path):
        HaaSConfiguration.dump(self, config_path)

    def get(self, key, value=None):
        if not isinstance(key, HaasConfigurationKey):
            raise Exception("The key must be an instance of {}".format(type(HaasConfigurationKey)))
        return self.config[key]


class HaasConfigurationManager(metaclass=Singleton):
    def __init__(self, haas_dir=None):
        self.haas_dir = os.path.join(os.path.expanduser("~"), '.haas') if haas_dir is None else haas_dir
        self.config_db_dir = os.path.join(self.haas_dir, 'config')
        self.config_db = {}
        self._init_dir()

        debug("haas dir: {}", self.haas_dir)
        debug("haas config dir: {}", self.config_db_dir)

        self.reload()

    def _init_dir(self):
        debug("Creating config dir {}", self.config_db_dir)
        os.makedirs(self.config_db_dir, exist_ok=True)

    def get_config_path(self, config_name):
        return os.path.join(self.config_db_dir, "{}.yaml".format(config_name))

    def add(self, config_name, config_item):
        if not isinstance(config_item, HaaSConfiguration):
            raise Exception("Incompatible class type {} with {}".format(type(config_item)), type(HaaSConfiguration))
        debug("##############")
        config_path = self.get_config_path(config_name)
        config_item.to_file(config_path)
        self.config_db[config_name] = config_item

    def remove(self, config_name):
        with contextlib.suppress(FileNotFoundError):
            os.remove(self.get_config_path(config_name))
        self.config_db.pop(config_name, None)

    def exists(self, config_name):
        debug("config name: {}", config_name)
        debug("config path: {}", self.get_config_path(config_name))
        return config_name in self.config_db and os.path.exists(self.get_config_path(config_name))

    def reload(self):
        for config_file in os.listdir(self.config_db_dir):
            if not config_file.endswith('yaml'):
                continue
            config_name = os.path.splitext(os.path.basename(config_file))[0]
            config_path = os.path.join(self.config_db_dir, config_file)
            self.config_db[config_name] = HaaSConfiguration.load(config_path)
        debug(self.config_db)

    def list(self):
        return self.config_db


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Config related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.pass_context
def list(ctx):
    config_manager = HaasConfigurationManager()
    for config_name, config_item in config_manager.list().items():
        message(config_name)


@cli.command()
@click.pass_context
def refresh(ctx):
    pass


@cli.command()
@click.pass_context
def update(ctx):
    pass


@cli.command()
@click.argument('name')
@click.option('--key', type=str, default='haas', help="The key profile name configured in AWS")
@click.option('--master_node', type=int, default=1, help="The number of cluster-wider service nodes")
@click.option('--slave_node', type=int, default=1, help="The number of Thor/Roxie nodes")
@click.option('--master_instance_type', type=click.Choice(['t2.micro', 'c4.large']), default='t2.micro',
              help="The instance type of the master nodes")
@click.option('--slave_instance_type', type=click.Choice(['t2.micro', 'c4.large']), default='t2.micro',
              help="The instance type of the master nodes")
@click.option('--ebs_volume_size', type=int, default=20, help="The size of the EBS volume")
@click.pass_context
def new(ctx, name, key, master_node, slave_node, master_instance_type, slave_instance_type, ebs_volume_size):
    config_manager = HaasConfigurationManager(haas_dir=ctx.obj['config_dir'])

    if config_manager.exists(name):
        error("config name {} already exists", name)
        ctx.abort()

    haas_config = HaaSConfiguration(
        {
            HaasConfigurationKey.HAAS_EC2_KEY_PAIR: key,
            HaasConfigurationKey.HAAS_SERVICE_NUM_NODES: master_node,
            HaasConfigurationKey.HAAS_WORKER_NUM_NODES: slave_node,
            HaasConfigurationKey.HAAS_SERVICE_INSTANCE_TYPE: master_instance_type,
            HaasConfigurationKey.HAAS_WORKER_INSTANCE_TYPE: slave_instance_type,
            HaasConfigurationKey.HAAS_EBS_VOLUME_SIZE: ebs_volume_size
        }
    )
    config_manager.add(name, haas_config)
