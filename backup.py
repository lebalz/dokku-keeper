#!/usr/bin/env python3

from prometheus_client import CollectorRegistry
from lib.helpers import prom_report
from lib.rsync_job import RsyncJob
from lib.command import Command
from lib.config import Config
from typing import List
from pathlib import Path
import yaml
import os

def try_set_envs():
    try:
        from set_envs import set_envs
        set_envs()
    except Exception as e:
        print('Failed to load envs with set_envs.py: ', e)
        print('Try using the shell envs')


BACKUP_CONFIG = 'backup_config.yaml'


def backup_configs() -> List[Config]:
    registry = CollectorRegistry()
    cmd = Command(f'cat /root/{BACKUP_CONFIG}', name='fetch_config')
    cmd.run(registry)
    if not cmd.result.success:
        raise Exception(cmd.result.error)
    configs = yaml.full_load(cmd.result.result)
    prom_report('fetch_config', registry)
    return [Config(app, data) for app, data in configs.items()]


configs = backup_configs()

for config in configs:
    config.run()

# cleanup old backups
version_size = int(os.environ.get('VERSION_HISTORY_SIZE', 30))
backup_dir = Path(os.environ.get('BACKUP_DIR', Path.cwd()))
backups = backup_dir.glob('*.tar.gz')
