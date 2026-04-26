#!/bin/bash
# Cron management for live trader API
# Usage: ./cron.sh --setup | --show | --remove

API_URL="http://localhost:8503/trading-cycle"
CRON_COMMENT="# Live Trader API cron"
CRON_ENTRY="* * * * * curl -X POST ${API_URL} 2>/dev/null"

setup() {
    if ! command -v crontab &> /dev/null; then
        echo "Error: crontab not found. Install cron: apt-get install cron"
        return 1
    fi
    if crontab -l 2>/dev/null | grep -q "Live Trader API cron"; then
        echo "Cron already configured for Live Trader"
        return
    fi
    crontab -l 2>/dev/null | grep -v "trading-cycle" | crontab -
    (crontab -l 2>/dev/null; echo ""; echo "${CRON_COMMENT}"; echo "${CRON_ENTRY}") | crontab -
    echo "Cron configured: hits ${API_URL} every minute"
}

show() {
    echo "=== Live Trader Cron ==="
    crontab -l 2>/dev/null | grep -A1 "Live Trader API cron" || echo "Not configured"
}

remove() {
    if ! command -v crontab &> /dev/null; then
        echo "Error: crontab not found. Install cron: apt-get install cron"
        return 1
    fi
    crontab -l 2>/dev/null | grep -v "Live Trader API cron" | grep -v "trading-cycle" | crontab -
    echo "Cron removed"
}

case "$1" in
    --setup|-s)  setup ;;
    --show|-l)    show ;;
    --remove|-r)  remove ;;
    *)            echo "Usage: $0 --setup | --show | --remove"; exit 1 ;;
esac