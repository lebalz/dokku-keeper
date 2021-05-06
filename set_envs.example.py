import os


def set_envs():
    os.environ['DOKKU_USER'] = 'root'
    os.environ['DOKKU_HOST_IP'] = '192.168.1.1'
    os.environ['PROM_PUSHGATEWAY_URL'] = 'https://push-gateway.foo.bar'
    os.environ['AUTH_USER'] = 'admin'
    os.environ['AUTH_PASSWORD'] = 'asdfasdf'
    os.environ['KEEP_BACKUP_DAYS'] = '30'
    os.environ['BACKUP_DIR'] = 'backups/'
    os.environ['METRICS_TTL_S'] = '10'
