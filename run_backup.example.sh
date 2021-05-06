#!/bin/bash
export DOKKU_USER=""
export DOKKU_HOST_IP=""
export PROM_PUSHGATEWAY_URL=""
export AUTH_USER=""
export AUTH_PASSWORD=""
export KEEP_BACKUP_DAYS=""
export BACKUP_DIR=""
export METRICS_TTL_S="10"

./backup.py