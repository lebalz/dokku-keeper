# from __future__ import annotations
# from lib.command import Command
from lib.helpers import time_s
import logging
import os
from typing import Any, Dict, Literal
import logging_loki
import functools


class LokiReporter:

    username = os.environ['AUTH_USER']
    password = os.environ['AUTH_PASSWORD']
    reporter_name = os.environ.get('KEEPER_NAME', 'dokku-keeper')
    handler: logging_loki.LokiHandler = logging_loki.LokiHandler(
        url=os.environ.get('LOKI_URL', ''),
        auth=(username, password),
        version="1"
    )

    @classmethod
    def reports(cls, func):
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            if not os.environ.get('LOKI_URL', None):
                return
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
    def report(cls, msg: str, tags: Dict = {}, level: Literal['info', 'error', 'warning'] = 'info'):
        data = {'tags': {str(key): str(value) for key, value in tags.items()}}
        logger = logging.getLogger(cls.reporter_name)
        logger.setLevel(logging.INFO)
        logger.addHandler(cls.handler)
        if level == 'info':
            logger.info(msg=msg, extra=data)
        elif level == 'warning':
            logger.warning(msg=msg, extra=data)
        elif level == 'error':
            logger.error(msg=msg, extra=data)
        elif level == 'debug':
            logger.debug(msg=msg, extra=data)
        elif level == 'exception':
            logger.exception(msg=msg, extra=data)
        elif level == 'critical':
            logger.critical(msg=msg, extra=data)

    @classmethod
    def report_cmd(cls, cmd: Any):
        from lib.command import Command
        cmd: Command = cmd
        if not cmd.processed:
            return
        data = {
                'type': 'cmd',
                'app': cmd.app_name,
                'stage': cmd.stage,
                'name': cmd.name,
                'duration_s': cmd.duration
            }
        msg = f'app={cmd.app_name} name={cmd.name} command={cmd.cmd} stage={cmd.stage} duration_s={cmd.duration}'
        level = 'info'
        if not cmd.result.success:
            data['error'] = cmd.result.error
            level = 'error'
        cls.report(msg, data, level=level)

    @classmethod
    def report_sync_job(cls, job: Any):
        from lib.rsync_job import RsyncJob
        job: RsyncJob = job
        if not job.processed:
            return
        data = {
                'type': 'rsync',
                'sync_type': job.type,
                'app': job.app_name,
                'path': job.target_dir,
                'file_count': job.synced_files,
                'size_bytes': job.size,
                'duration_s': job.duration
            }
        msg = f'app={job.app_name} path={job.target_dir} file_count={job.synced_files} size_bytes={job.size} duration_s={job.duration}'
        level = 'info'
        if not job.result.success:
            data['error'] = job.result.error
            level = 'error'
        cls.report(msg, data, level=level)
