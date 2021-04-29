import os
import subprocess
from prometheus_client import Gauge
from prometheus_client.metrics import MetricWrapperBase
from prometheus_client.registry import CollectorRegistry
from lib.helpers import path_for, sanitize_job_name, time_s
from pathlib import Path
from typing import Dict, List, Literal, Optional
from lib.result import Result


class Command:
    name: str
    cmd: str
    to: Optional[str]
    stage: Literal['pre-backup', 'backup', 'post-backup']
    result: Optional[Result] = None
    root: Path

    def __init__(self, cmd: str, name: str = None, to: str = None, stage: str = None, root: Path = None) -> None:
        self.name = name
        self.root = root
        self.cmd = cmd
        self.to = to
        self.stage = stage or 'backup'
        if self.stage not in ['pre-backup', 'backup', 'post-backup']:
            print(f'Unknown stage \'{self.stage}\', skipping')

    def __str__(self) -> str:
        return f'{f"{self.stage}: " if self.stage else ""}{self.cmd}{f" > {self.to}" if self.to else ""}'

    def run(self, registry: CollectorRegistry) -> None:
        user = os.environ['DOKKU_USER']
        host = os.environ['DOKKU_HOST_IP']
        t0 = time_s()
        res = subprocess.Popen(f"ssh {user}@{host} {self.cmd}", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        self.set_result(res[0], res[1])
        g = Gauge(f'backup_dokku_cmd_time_s', 'Command execution time (seconds)', registry=registry)
        g.set(time_s() - t0)

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

    def report(self, registry: CollectorRegistry) -> List[MetricWrapperBase]:
        s1 = Gauge(f'backup_dokku_cmd', 'state of an executed command', registry=registry)
        s1.set(1 if self.result and self.result.success else 0)
        pass

    @staticmethod
    def fromDict(name: str, data: Dict, root: Path):
        if 'cmd' not in data:
            raise Exception('key \'cmd\' is missing')
        updated = {'to': None, 'stage': None}
        updated.update(**data)
        return Command(updated['cmd'], name=name, to=updated['to'], stage=updated['stage'], root=root)
