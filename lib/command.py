# from lib.loki_reporter import LokiReporter
from lib.prom_reporter import PromReporter
import os
import subprocess
from lib.helpers import path_for, sanitize_job_name, time_s
from pathlib import Path
from typing import Dict, List, Literal, Optional
from lib.result import Result


class Command:
    name: str
    cmd: str
    app_name: str
    to: Optional[str]
    stage: Literal['pre-backup', 'backup', 'post-backup']
    result: Optional[Result] = None
    root: Path
    duration: Optional[int] = None

    def __init__(self, app_name: str, cmd: str, name: str = None, to: str = None, stage: str = None, root: Path = None) -> None:
        self.app_name = app_name
        self.name = name
        self.root = root
        self.cmd = cmd
        self.to = to
        self.stage = stage or 'backup'
        if self.stage not in ['pre-backup', 'backup', 'post-backup']:
            print(f'Unknown stage \'{self.stage}\', skipping')

    def __str__(self) -> str:
        return f'{f"{self.stage}: " if self.stage else ""}{self.cmd}{f" > {self.to}" if self.to else ""}'

    @PromReporter.reports
    def run(self) -> None:
        user = os.environ['DOKKU_USER']
        host = os.environ['DOKKU_HOST_IP']
        t0 = time_s()
        res = subprocess.Popen(f"ssh {user}@{host} {self.cmd}", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        self.duration = time_s() - t0
        self.set_result(res[0], res[1])

    def set_result(self, std_out: bytes, std_err: bytes):
        res = Result(std_out, std_err)
        self.result = res
        if self.to and res.success:
            base = self.root or Path.cwd()
            with open(path_for(base, self.to), 'wb') as f:
                f.write(res.raw_result)

    @property
    def processed(self):
        return self.result is not None

    @property
    def report_name(self):
        return sanitize_job_name(self.name)

    @staticmethod
    def fromDict(app_name: str, name: str, data: Dict, root: Path):
        if 'cmd' not in data:
            raise Exception('key \'cmd\' is missing')
        updated = {'to': None, 'stage': None}
        updated.update(**data)
        return Command(app_name=app_name, cmd=updated['cmd'], name=name, to=updated['to'], stage=updated['stage'], root=root)
