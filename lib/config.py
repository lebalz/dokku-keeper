# from lib.reporter import Reporter
import os
import shutil
from lib.helpers import backup_commands, make_tarfile, sanitize_job_name, time_s
from lib.ijob import IJob
from lib.rsync_job import RsyncJob
from lib.result import Result
from lib.command import Command
from typing import Dict, List
from datetime import datetime
from pathlib import Path


class Config(IJob):
    app: str
    commands: List[Command]
    rsync_jobs: List[RsyncJob]
    start_time: datetime
    results: List[Result]

    def __init__(self, app: str, data: Dict) -> None:
        self.app = app
        self.start_time = datetime.now()
        self.backup_path.mkdir(exist_ok=True, parents=True)
        if 'commands' in data:
            self.commands = [Command.fromDict(app, name, cmd, self.backup_path)
                             for name, cmd in data['commands'].items()]
        else:
            self.commands = []
        self.rsync_jobs = []
        if 'files' in data:
            for file in data['files']:
                self.rsync_jobs.append(RsyncJob(app, file, self.backup_path, 'file'))
        if 'folders' in data:
            for folder in data['folders']:
                self.rsync_jobs.append(RsyncJob(app, folder, self.backup_path, 'dir'))

    # def report(self, reporter: Reporter):
    #     pass
    def run(self):
        for cmd in backup_commands(self, 'pre-backup'):
            cmd.run()
        for cmd in backup_commands(self, 'backup'):
            cmd.run()
        for rsync_job in self.rsync_jobs:
            rsync_job.run()
        for cmd in backup_commands(self, 'post-backup'):
            cmd.run()
        make_tarfile(self.backup_tar_path, self.backup_path)

        # s2 = Gauge(f'backup_dokku_size_mb', 'backup.tar.gz size', registry=registry)
        # s2.set(self.get_tar_size_mb)

        shutil.rmtree(self.backup_path)

    @property
    def start(self) -> str:
        return self.start_time.strftime('%Y-%m-%d--%H-%M-%S')

    @property
    def backup_path(self) -> Path:
        root = Path(os.environ.get('BACKUP_DIR', Path.cwd()))
        return root.joinpath(self.app, f'backup-{self.start}')

    @property
    def backup_tar_path(self) -> Path:
        root = Path(os.environ.get('BACKUP_DIR', Path.cwd()))
        return root.joinpath(self.app, f'backup-{self.start}.tar.gz')

    @property
    def get_tar_size_mb(self) -> int:
        if not self.backup_tar_path.exists():
            return 0
        return self.backup_tar_path.stat().st_size / (1024 * 1024)

    def prefix(self, name) -> str:
        return f'{self.report_name}:{name}'

    @property
    def report_name(self):
        return sanitize_job_name(self.app)
