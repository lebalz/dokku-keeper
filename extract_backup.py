import tarfile
from pathlib import Path
from typing import Union
import subprocess

def extract(backup: Union[str, Path]):
    backup = Path(backup)
    tar = tarfile.open(backup, "r:gz")
    tar.extractall(path=backup.parent)
    tar.close()
    return Path(f'{backup.absolute()}'.replace('.tar.gz', ''))

def exec_db(db, user, query):
    return  subprocess.Popen(f"psql -d {db} -U {user} -c '{query}'", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

def restore(backup_dir: Path, db_user: str, db: str = 'postgres'):
    db_path = backup_dir.joinpath('database');
    if not db_path.is_dir():
        print('nothing to restore')
        return
    print('has db')
    dump = None
    for dmp in db_path.iterdir():
        if dmp.is_file() and dmp.suffix == '.dump':
            dump = dmp
            break
    if not dump:
        print('nothing to restore')
        return

    new_db_name = f"tmp_{dump.stem}{dump.parent.parent.name.replace('backup', '')}".replace('-', '_')

    res = exec_db(db, db_user, f'DROP DATABASE IF EXISTS {new_db_name}')
    print(*res, sep = "\n")
    res = exec_db(db, db_user, f'CREATE DATABASE {new_db_name}')
    print(*res, sep = "\n")
    res = subprocess.Popen(f"pg_restore --verbose --clean --no-acl --no-owner --host=localhost --dbname={new_db_name} --username={db_user} {dump}", shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print(*res, sep = "\n")

    print('==========================')
    print('Restored to database', new_db_name)
    print('')
    print('Connect to db:')
    print('')
    print(f'psql -d {new_db_name} -U {db_user}')
    print('')
    print('When you are done, drop with')
    print('')
    print(f"psql -d {db} -U {db_user} -c 'DROP DATABASE {new_db_name}'")

backup = extract('backup-2022-06-02--01-00-02.tar.gz')
restore(backup, 'db_user')
