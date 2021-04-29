import subprocess
from prometheus_client import CollectorRegistry, Gauge
from prometheus_client.metrics import MetricWrapperBase
from lib.ijob import IJob
from lib.helpers import path_for, sanitize_job_name, time_s
from lib.result import Result
from typing import List, Literal, Optional, Union
from pathlib import Path
import os


class RsyncJob(IJob):
    path: Path
    root: Path
    type: Literal['file', 'dir']
    result: Optional[Result] = None
    synced_files: int = 0

    def __init__(self, path: Union[str, Path], root: Path, type: Literal['file', 'dir']) -> None:
        self.path = Path(path)
        self.root = root
        self.type = type

    def __str__(self) -> str:
        return f'{self.type}: {self.path}'

    def set_result(self, std_out: bytes, std_err: bytes):
        self.result = Result(std_out, std_err)
        if self.result.success:
            if self.type == 'file':
                cnt = 1
            else:
                cnt = sum([len(files) for r, d, files in os.walk(path_for(self.root, self.path))])
            self.synced_files = cnt

    def run(self, registry: CollectorRegistry) -> None:
        user = os.environ['DOKKU_USER']
        host = os.environ['DOKKU_HOST_IP']
        t0 = time_s()
        flags = '-zarvh' if self.type == 'dir' else '-zavh'

        res = subprocess.Popen(f"rsync {flags} {user}@{host}:{self.path} {self.target_dir}", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        self.set_result(res[0], res[1])
        g = Gauge(f'backup_dokku_rsync_sync_time_s', 'Rsync sync time (seconds)', registry=registry)
        g.set(time_s() - t0)

    @property
    def target_dir(self):
        if self.type == 'file':
            return path_for(self.root, self.path)
        return self.root

    @property
    def processed(self):
        return self.result is not None

    @property
    def report_name(self):
        return sanitize_job_name(self.path)

    def report(self, registry: CollectorRegistry) -> List[MetricWrapperBase]:
        s1 = Gauge(f'backup_dokku_rsync_number_of_files', 'number of synchronized files', registry=registry)
        s1.set(self.synced_files)
        pass
