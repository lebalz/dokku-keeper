import os
def set_envs():
    os.environ['DOKKU_USER'] = 'root'
    os.environ['DOKKU_HOST_IP'] = '192.168.1.1'
    os.environ['PUSH_GATEWAY'] = 'https://push-gateway.foo.ch'
    os.environ['AUTH_USER'] = 'admin'
    os.environ['AUTH_PASSWORD'] = 'asdfasdf'