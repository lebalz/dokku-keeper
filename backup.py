#!/usr/bin/env python3

import re
import os
import yaml
import datetime
from pathlib import Path
from lib.config import Config
from lib.command import Command
from lib.helpers import time_s
import time


def try_set_envs():
    try:
        from set_envs import set_envs
        set_envs()
        print('Using envs from set_envs.py: ')
    except Exception:
        print('Using the shell envs')


try_set_envs()


DATE_TIME_EXTRACTOR = re.compile(
    r'backup-(?P<date>\d\d\d\d-\d\d-\d\d)--(?P<time>\d\d-\d\d-\d\d).*.tar.gz')


BACKUP_CONFIG = 'backup_config.yaml'

t0 = time_s()


def backup_configs() -> list[Config]:
    cmd = Command(app_name='dokku-keeper',
                  cmd=f'cat /root/{BACKUP_CONFIG}', name='fetch_config')
    cmd.run()
    if not cmd.result:
        raise Exception('Failed to fetch backup config')
    if not cmd.result.success:
        raise Exception(cmd.result.error)
    configs = yaml.full_load(cmd.result.result)
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
        backup_date = datetime.datetime.strptime(
            match['date'], "%Y-%m-%d").date()
        if backup_date < (today - datetime.timedelta(days=keep_for)):
            os.remove(backup)
