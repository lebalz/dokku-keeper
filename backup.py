#!/usr/bin/env python3

from set_envs import set_envs
from lib.reporter import PromReporter
from prometheus_client import CollectorRegistry
from lib.helpers import path_for, prom_report
from lib.rsync_job import RsyncJob
from lib.command import Command
from lib.config import Config
from typing import List
import yaml

set_envs()


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
