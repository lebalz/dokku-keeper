# dokku keeper

## cron job

Copy the [start_backup.sh](start_backup.sh) to your server and set your ENV variables. Then add a cron job to run every night at 3am:

```sh
crontab -e
```

and append the following job:

```sh
0 3 * * * /path/to/run_backuo.py
```

...and list your cron jobs;
```sh
crontab -l : List the all your cron jobs.
```

## ENV
Required environment variables:
- `DOKKU_USER` (e.g. 'root')
- `DOKKU_HOST_IP`
- `BACKUP_DIR` (absolute path)
- `KEEP_BACKUP_DAYS`

Optional env's to report to a prometheus push gateway:
- `PROM_PUSHGATEWAY_URL`
- `AUTH_USER`
- `AUTH_PASSWORD`
- `METRICS_TTL_S` prometheus push gateway does not support a ttl, so it has to be done manually. Default is `10s` (should be twice the time as your scrape intervall)

# Backup Configuration

Place a file named [backup_config.yaml](backup_config.yaml) in the root folder of your dokku instance (or the configured location in `ENV['BACKUP_DIR']`). The backup server will use this config to backup your apps. It will synchronize files and folders. Additionally you can add commands which are performed either pre-, during- or post-backup. The output of these commands can be optionally saved to a file.

An example config may look like

```yaml
# backup_config.yaml
js-web-app:
  files:
    - "/home/dokku/js-web-app/ENV"
  folders:
    - "/var/lib/dokku/data/storage/js-web-app/data"
  commands:
    postgres:
      cmd: "dokku postgres:export js-web-app"
      to: "/database/js-web-app.dump"
web-app2:
  files:
    - ...
```

## files

Any listed file will be synchronized, the folder structure on your backup server will be kept (relative to the backup-folder).

```sh
@dokku:/home/dokku/js-web-app/ENV -> @backup:/path/to/backup/js-web-app/backup-2021-04-30/home/dokku/js-web-app/ENV
```

## folders

Any listed folder will be synchronized recursively, the folder structure on your backup server will be kept (relative to the backup-folder).

```sh
@dokku:/var/lib/dokku/data/storage/js-web-app/data -> @backup:/path/to/backup/js-web-app/backup-2021-04-30/var/lib/dokku/data/storage/js-web-app/data
```

## commands
You can specify a list of commands, each command must have at least a `name` (the key) and a `cmd` in the properties.

!! Dont redirect the output of a command (e.g. `echo hii > file.txt`), since the standard output is redirected to the executing python script [commands.py#36](https://github.com/lebalz/dokku-keeper/blob/main/lib/command.py#L36). If you need to save the output (e.g. when dumping a database), specify a file for saving the standard output.

Optional Properties:
- `stage` [`pre-backup`, `backup` (default), `post-backup`]
- `to` [`str`] file location to save the output of the command, e.g. when the data to backup comes from the standard output.

```yaml
commands:
    cmd1:
        stage: pre-backup
        cmd: "ls -lah /home/dokku"
    postgres:
        cmd: "dokku postgres:export js-app"
        to: "/database/js-app.dump"
    cmd2:
        stage: post-backup
        cmd: "ps -afuxw"
```

### stage: `pre-backup`
Executed before any file/folder synchronization.
### stage: `backup`
Executed during the file/folder synchronization.
### stage: `post-backup`
Executed after the file/folder synchronization completed. May be used to cleanup...




## On synology nas

Required packages:
- git (or git-server)
- python3 (for DSM < v7, v7+ has python 3 installed)
- nano, e.g. from [SynoCli File Tools](https://think.unblog.ch/en/how-to-install-nano-on-synology-nas/)

Required services:
- ssh
- enabled user home (Check "Enable user home service" under `Control Panel > User > Advanced > User Home`)

1. Create a shared folder where you want to store your backup (e.g. `dokku-backups`)
2. Create a subfolder for the backups: `mkdir /volume1/dokku-backups/backups`
3. cd to this directory (e.g. `cd /volume1/dokku-backups` and clone this repository (`git clone https://github.com/lebalz/dokku-keeper.git`)
4. Install pip and the packages:
```sh
cd /volume1/dokku-backups/dokku-keeper
sudo python3 -m ensurepip
# for dsm < 7
# sudo /usr/local/bin/python3 -m pip install --upgrade pip
sudo python3 -m pip install --upgrade pip

sudo python3 -m pip install -r ./requirements.txt
```
5. copy and edit the script `run_backup.example.sh` with your credentials
```sh
cp run_backup.example.sh run_backup.sh
nano run_backup.sh
# Always use absolute paths!
```
6. Add a `backup_config.yaml` to your dokku host (see the [example backup_config.yaml](backup_config.yaml))
7. Create a new task: `Control Panel > Task Scheduler > Create Scheduled Task`
8. Done 🎊



## Restore backup to inspect earlier state

If you want to restore a backup, you can either run [extract_backup.py](extract_backup.py) or you extract the `.tar` file and proceed as follows (where `foobar` ist your actual username):

```bash
psql -d postgres -U foobar

# create new db
CREATE DATABASE backup_db;
# quit
\q

# restore
pg_restore --verbose --clean --no-acl --no-owner --host=localhost --dbname=backup_db --username=foobar backup.dump

# connect

psql -d backup_db -U foobar
```