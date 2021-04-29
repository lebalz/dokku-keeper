import tarfile
from pathlib import Path
from typing import Union

def extract(backup: Union[str, Path]):
    backup = Path(backup)
    tar = tarfile.open(backup, "r:gz")
    tar.extractall(path=backup.parent)
    tar.close()

extract('hfr-jupyterhub/backup-29-04-2021--16-55-58.tar.gz')