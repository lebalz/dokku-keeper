#!/usr/bin/env python3

import yaml
from typing import TypedDict
import os
import re
from lib.helpers import time_s
from lib.command import Command
from lib.config import Config
from pathlib import Path
import datetime
import time

CONFIG_FILE = os.environ.get('CONFIG_FILE', 'config.yaml')
CONFIG_DIR = os.environ.get('CONFIG_DIR', '/data/')
BACKUP_CONFIG = 'backup_config.yaml'


DATE_TIME_EXTRACTOR = re.compile(
    r'backup-(?P<date>\d\d\d\d-\d\d-\d\d)--(?P<time>\d\d-\d\d-\d\d).*.tar.gz')


'''
typical config.yaml:
- server-1:
    DOKKU_USER: root
    DOKKU_HOST_IP: 1.2.3.4
    KEEP_BACKUP_DAYS: 30
    BACKUP_DIR: backups/s1
- server-2:
    DOKKU_USER: root
    DOKKU_HOST_IP: 1.2.3.10
    KEEP_BACKUP_DAYS: 30
    BACKUP_DIR: backups/s2
'''

# creates a typed dict of the config


class LocalConfig(TypedDict):
    DOKKU_USER: str
    DOKKU_HOST_IP: str
    KEEP_BACKUP_DAYS: int
    BACKUP_DIR: str


def validate_config(config: list[dict]) -> list[LocalConfig]:
    validated_configs = []
    for item in config:
        if len(item) != 1:
            raise ValueError(f'Invalid config item: {item}')
        name, data = list(item.items())[0]
        try:
            validated_config = LocalConfig(
                DOKKU_USER=data['DOKKU_USER'],
                DOKKU_HOST_IP=data['DOKKU_HOST_IP'],
                KEEP_BACKUP_DAYS=int(data['KEEP_BACKUP_DAYS']),
                BACKUP_DIR=data['BACKUP_DIR']
            )
            validated_configs.append(validated_config)
        except KeyError as e:
            raise ValueError(f'Missing key {e} in config item: {item}')
    return validated_configs


def load_local_configs():
    with open(os.path.join(CONFIG_DIR, CONFIG_FILE), 'r') as f:
        return validate_config(yaml.safe_load(f))


def fetch_remote_configs() -> list[Config]:
    cmd = Command(app_name='dokku-keeper',
                  cmd=f'cat /root/{BACKUP_CONFIG}', name='fetch_config')
    cmd.run()
    if not cmd.result:
        raise Exception('Failed to fetch backup config')
    if not cmd.result.success:
        raise Exception(cmd.result.error)
    configs = yaml.full_load(cmd.result.result)
    return [Config(app, data) for app, data in configs.items()]


def setup_env(config: LocalConfig):
    os.environ['DOKKU_USER'] = config['DOKKU_USER']
    os.environ['DOKKU_HOST_IP'] = config['DOKKU_HOST_IP']
    os.environ['KEEP_BACKUP_DAYS'] = str(config['KEEP_BACKUP_DAYS'])
    os.environ['BACKUP_DIR'] = config['BACKUP_DIR']


def cleanup_old_backups():
    keep_for = int(os.environ.get('KEEP_BACKUP_DAYS', 30))
    backup_dir = Path(os.environ.get(
        'BACKUP_DIR', Path.cwd().joinpath('backups')))
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


def run():
    configs = load_local_configs()
    for config in configs:
        try:
            setup_env(config)
            t0 = time_s()
            remote_configs = fetch_remote_configs()
            for rconfig in remote_configs:
                rconfig.run()
                print(rconfig.report())
        except Exception as e:
            print(f'Error running backup for config {config}: {e}')
        try:
            cleanup_old_backups()
        except Exception as e:
            print(f'Error cleaning up old backups for config {config}: {e}')


if __name__ == '__main__':
    configs = load_local_configs()
    for config in configs:
        print(config)
