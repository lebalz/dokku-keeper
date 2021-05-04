import os
from typing import Any, Dict, Union
from prometheus_client import CollectorRegistry, Gauge, Info, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler, delete_from_gateway
import functools
from lib.helpers import sanitize_job_name, time_s


def auth_handler(url, method, timeout, headers, data):
    username = os.environ['AUTH_USER']
    password = os.environ['AUTH_PASSWORD']
    headers.append(['User-Agent', 'Mozilla/5.0'])
    return basic_auth_handler(url, method, timeout, headers, data, username, password)


CLEANUP_AFTER_S = 7


class PromReporter:
    url = os.environ.get('PROM_URL', '')
    jobs: list = []

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
        tags = {sanitize_job_name(key): value for key, value in tags.items()}

        job = sanitize_job_name(job)
        registry = CollectorRegistry()
        g = Gauge(name=name, documentation=description, registry=registry, unit=unit)
        g.set(value)
        pushadd_to_gateway(gateway=cls.url, job=job, grouping_key=tags, registry=registry, handler=auth_handler)
        print(time_s(), 'reported', job, tags, value)
        ref = {'start': time_s(), 'job': job, 'tags': tags, 'remove': remove}
        cls.jobs.append(ref)
        return ref

    @classmethod
    def check_cleanup(cls, force: bool = False):
        print('@cleanup: job size', len(cls.jobs))
        for job in cls.jobs:
            if job['start'] + CLEANUP_AFTER_S < time_s() and (force or job['remove']):
                cls.cleanup(job['job'], job['tags'])
                cls.jobs.remove(job)

    @classmethod
    def cleanup(cls, job: str, grouping_key: dict):
        print(time_s(), 'cleanup', job, grouping_key)
        delete_from_gateway(cls.url, job=job,
                            grouping_key=grouping_key,
                            handler=auth_handler)
