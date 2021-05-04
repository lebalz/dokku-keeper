from lib.loki_reporter import LokiReporter
import subprocess
from lib.ijob import IJob
from lib.helpers import path_for, sanitize_job_name, time_s
from lib.result import Result
from typing import List, Literal, Optional, Union
from pathlib import Path
import re
import os
# 'total size is 13.72M  speedup is 1.92'
# 'total size is 1.05K  speedup is 1.37'
SIZE_EXTRACTOR = re.compile(r'total size is (?P<size>\d+\.\d+)(?P<unit>[KMG])?')


class RsyncJob(IJob):
    path: Path
    root: Path
    type: Literal['file', 'dir']
    result: Optional[Result] = None
    synced_files: int = 0
    size: int = 0
    app_name: str
    duration: Optional[float] = None

    def __init__(self, app_name: str, path: Union[str, Path], root: Path, type: Literal['file', 'dir']) -> None:
        self.path = Path(path)
        self.app_name = app_name
        self.root = root
        self.type = type

    def __str__(self) -> str:
        return f'{self.type}: {self.path}'

    def set_result(self, std_out: bytes, std_err: bytes):
        self.result = Result(std_out, std_err)
        if self.result.success:
            r = self.result.result.splitlines()
            cnt = len(list(filter(lambda x: not x.endswith('/'), r))) - 4
            self.synced_files = cnt
            size_match = SIZE_EXTRACTOR.match(r[-1])
            if size_match:
                sz = float(size_match['size'])
                unit = size_match['unit']
                if unit == 'K':
                    sz = sz * 1000
                elif unit == 'M':
                    sz = sz * 1000 * 1000
                elif unit == 'G':
                    sz = sz * 1000 * 1000 + 1000
                self.size = int(sz)

    @property
    def file_size_bytes(self) -> int:
        return self.target_dir.stat().st_size

    @LokiReporter.reports
    def run(self) -> None:
        user = os.environ['DOKKU_USER']
        host = os.environ['DOKKU_HOST_IP']
        t0 = time_s()
        flags = '-zarvh' if self.type == 'dir' else '-zavh'

        res = subprocess.Popen(f"rsync {flags} {user}@{host}:{self.path} {self.target_dir}", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        self.duration = time_s() - t0
        self.set_result(res[0], res[1])

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

    def report(self):
        pass
