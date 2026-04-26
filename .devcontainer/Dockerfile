FROM mcr.microsoft.com/devcontainers/python:3.12

USER root

RUN pip install poetry && \
    apt-get update && apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]