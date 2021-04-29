# dokku keeper


## ENV
Required environment variables:
- `DOKKU_USER` (e.g. 'root')
- `DOKKU_HOST_IP`

## commands
You can specify a list of commands, each command must have at least a `name` (the key) and a `cmd` in the properties.

Optional Properties:
- `stage` [`pre-backup`, `backup` (default), `post-backup`]
- `to` [`str`] file location to save the output of the command, e.g. when the data to backup comes from the standard output.

```yaml
commands:
    - cmd1:
        stage: pre-backup
        cmd: "ls -lah /home/dokku"
    - postgres:
        cmd: "dokku postgres:export js-app"
        to: "/database/js-app.dump"
    - cmd2:
        stage: post-backup
        cmd: "ps -afuxw"
```

### stage: `pre-backup`
```yaml

```
### stage: `backup`
### stage: `post-backup`

