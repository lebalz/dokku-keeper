import os
from prometheus_client import CollectorRegistry, push_to_gateway
from prometheus_client.exposition import basic_auth_handler


def auth_handler(url, method, timeout, headers, data):
    username = os.environ['AUTH_USER']
    password = os.environ['AUTH_PASSWORD']
    headers.append(['User-Agent', 'Mozilla/5.0'])
    return basic_auth_handler(url, method, timeout, headers, data, username, password)


class PromReporter:
    url: str
    job_name: str

    def __init__(self, pushgateway_url: str, job_name: str) -> None:
        self.url = pushgateway_url
        self.job_name = job_name

    def report(self, registry: CollectorRegistry):
        push_to_gateway(self.url, job=self.job_name, registry=registry, handler=auth_handler)
