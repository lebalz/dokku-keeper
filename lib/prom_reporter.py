import os
from typing import Any, Dict, List, Union
from prometheus_client import CollectorRegistry, Gauge, Info, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler, delete_from_gateway
import functools
from lib.helpers import sanitize_job_name, time_s
from urllib.error import URLError


def auth_handler(url, method, timeout, headers, data):
    username = os.environ['AUTH_USER']
    password = os.environ['AUTH_PASSWORD']
    headers.append(['User-Agent', 'Mozilla/5.0'])
    return basic_auth_handler(url, method, timeout, headers, data, username, password)


CLEANUP_AFTER_S = int(os.environ.get('METRICS_TTL_S', 10), 10)


class ReportJob:
    url = os.environ.get('PROM_PUSHGATEWAY_URL', None)
    start: float
    job: str
    description: str
    value: Union[int, float]
    unit: str
    name: str
    tags: dict

    def __init__(self, job: str, name: str, description: str, value: Union[int, float], unit: str, tags: Dict = {}) -> None:
        self.start = time_s()
        self.job = job
        self.tags = tags
        self.description = description
        self.value = value
        self.unit = unit
        self.name = name

    def report(self):
        tags = {sanitize_job_name(key): value for key, value in self.tags.items()}

        job = sanitize_job_name(self.job)
        registry = CollectorRegistry()
        g = Gauge(name=self.name, documentation=self.description, registry=registry, unit=self.unit)
        g.set(self.value)
        try:
            pushadd_to_gateway(gateway=self.url, job=job, grouping_key=tags, registry=registry, handler=auth_handler)
        except URLError:
            print("{:.2f}".format(time_s() - PromReporter.init_time), 'LOG', self)
            return

        print("{:.2f}".format(time_s() - PromReporter.init_time), 'reported', self)

    def update_and_report(self, value: Union[int, float]):
        self.start = time_s()
        self.value = value
        self.report()

    def remove(self):
        try:
            delete_from_gateway(self.url, job=self.job,
                                grouping_key=self.tags,
                                handler=auth_handler)
        except URLError:
            return

    def __str__(self) -> str:
        return f'start: {"{:.2f}".format(self.start - PromReporter.init_time)}, job: {self.job}:{self.name}, tags: {self.tags}, value: {self.value}{self.unit}'


class PromReporter:
    url = os.environ.get('PROM_PUSHGATEWAY_URL', None)
    jobs: List[ReportJob] = []
    init_time: float = time_s()

    @classmethod
    def reports(cls, func):
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            from lib.command import Command
            from lib.rsync_job import RsyncJob
            value = func(*args, **kwargs)
            if type(args[0]) == Command:
                cls.report_cmd(args[0])
            elif type(args[0]) == RsyncJob:
                cls.report_sync_job(args[0])
            return value
        return wrapper_timer

    @classmethod
    def report_cmd(cls, cmd: Any):
        from lib.command import Command
        cmd: Command = cmd
        if not cmd.processed:
            return
        tags = {
            'type': 'cmd_duration',
            'app': cmd.app_name,
            'stage': cmd.stage,
            'name': cmd.name,
        }
        cls.report(cmd.app_name, 'cmd_duration', f'execute command {cmd.cmd}', cmd.duration, 's', tags)

    @classmethod
    def report_sync_job(cls, job: Any):
        from lib.rsync_job import RsyncJob
        job: RsyncJob = job
        if not job.processed:
            return
        tags = {
            'type': 'sync_duration',
            'app': job.app_name,
            'sync_type': job.type,
        }
        cls.report(job.app_name, 'sync_duration', f'sync duration', job.duration, 's', tags)
        tags = {
            'type': 'sync_size',
            'app': job.app_name,
            'sync_type': job.type,
        }
        cls.report(job.app_name, 'sync_size', f'synced file size', job.size, 'bytes', tags)
        tags = {
            'type': 'sync_file_count',
            'app': job.app_name,
            'sync_type': job.type,
        }
        cls.report(job.app_name, 'sync_file_count', f'synced files', job.synced_files, '', tags)

    @classmethod
    def report(cls, job: str, name: str, description: str, value: Union[int, float], unit: str, tags: Dict = {}, remove: bool = True):
        cls.check_cleanup()
        report_job = ReportJob(job=job, name=name, description=description, value=value, unit=unit, tags=tags)
        report_job.report()
        if remove:
            cls.jobs.append(report_job)
        return report_job

    @classmethod
    def cleanup_job(cls, job: ReportJob):
        if job.start + CLEANUP_AFTER_S < time_s():
            job.remove()
        else:
            cls.jobs.append(job)

    @classmethod
    def check_cleanup(cls):
        for job in cls.jobs:
            if job.start + CLEANUP_AFTER_S < time_s():
                job.remove()
                cls.jobs.remove(job)
