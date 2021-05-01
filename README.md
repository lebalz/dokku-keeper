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



