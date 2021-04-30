#!/usr/bin/env python3

from prometheus_client import CollectorRegistry
from lib.helpers import prom_report
from lib.rsync_job import RsyncJob
from lib.command import Command
from lib.config import Config
from typing import List
from pathlib import Path
import datetime
import yaml
import os
import re

DATE_TIME_EXTRACTOR = re.compile(r'backup-(?P<date>\d\d\d\d-\d\d-\d\d)--(?P<time>\d\d-\d\d-\d\d).*.tar.gz')

def try_set_envs():
    try:
        from set_envs import set_envs
        set_envs()
    except Exception as e:
        print('Failed to load envs with set_envs.py: ', e)
        print('Try using the shell envs')

try_set_envs()
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
keep_for = int(os.environ.get('KEEP_BACKUP_DAYS', 30))
backup_dir = Path(os.environ.get('BACKUP_DIR', Path.cwd().joinpath('backups')))
for app in backup_dir.iterdir():
    backups = app.glob('*.tar.gz')
    for backup in backups:
        match = DATE_TIME_EXTRACTOR.match(backup.name)
        if not match:
            break

        today = datetime.date.today()
        backup_date = datetime.datetime.strptime(match['date'], "%Y-%m-%d").date()
        if backup_date < (today - datetime.timedelta(days=keep_for)):
            os.remove(backup)
