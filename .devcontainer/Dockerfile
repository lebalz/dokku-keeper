FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# The upstream image can include a stale Yarn apt source with a rotated key.
# We do not need Yarn here, so drop that source to keep apt-get update reliable.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends rsync openssh-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/pip-tmp/requirements.txt
RUN pip3 --disable-pip-version-check install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp