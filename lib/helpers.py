
from __future__ import annotations
from pathlib import Path
import tarfile
from pathlib import Path
from typing import Literal
from time import time_ns


def time_s() -> float:
    '''
    returns the current time in seconds since epoche
    '''
    return time_ns() / 1000000000.0


def make_tarfile(output_filename: Path, source_dir: Path):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=Path(source_dir).name)


def backup_commands(config, stage: Literal['pre-backup', 'backup', 'post-backup']):
    from lib.command import Command
    res: list[Command] = [cmd for cmd in config.commands if cmd.stage == stage]
    return res


def sanitize_job_name(name: str | Path) -> str:
    jn = str(name)
    jn = jn.replace('/', '_')
    jn = jn.replace(' ', '')
    jn = jn.replace('-', '_')
    while jn.startswith('_'):
        jn = jn[1:]
    while jn.endswith('_'):
        jn = jn[:-1]
    return jn.lower()


def path_for(root: str | Path, destination: str | Path) -> Path:
    '''joins root path with (potentially absolute) destination path

    Example
    -------
    ```py
    path('/home/user/backup','/root/ENV')
    # -> /home/user/backup/root/ENV'
    ```
    '''
    root = Path(root)
    destination = str(destination)
    while destination.startswith('/'):
        destination = destination[1:]
    p = root.joinpath(destination)
    p.parent.mkdir(exist_ok=True, parents=True)
    return p
