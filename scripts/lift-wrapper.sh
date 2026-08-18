#!/bin/sh
#
# Installed as /usr/local/bin/lift by install-native.sh.
#
# Runs the collector as its service user with the right data directory and
# environment, so day-to-day commands are just:
#
#   sudo lift stats
#   sudo lift check
#   sudo lift test-alert
#   sudo lift rebuild

set -eu

PREFIX="/opt/lift-status"
DATA_DIR="/var/lib/lift-status"
ENV_FILE="/etc/lift-status.env"
SERVICE_USER="lift-status"

# Readable only by root, which is why these commands need sudo.
if [ -r "$ENV_FILE" ]; then
    . "$ENV_FILE"
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "lift: run with sudo (needs to read $ENV_FILE and write as $SERVICE_USER)" >&2
    exit 1
fi

exec sudo -u "$SERVICE_USER" env \
    LIFT_STATUS_DATA_DIR="$DATA_DIR" \
    ${LIFT_STATUS_ALERT_WEBHOOK:+LIFT_STATUS_ALERT_WEBHOOK="$LIFT_STATUS_ALERT_WEBHOOK"} \
    ${LIFT_STATUS_API_KEY:+LIFT_STATUS_API_KEY="$LIFT_STATUS_API_KEY"} \
    ${LIFT_STATUS_GRACE_MISSES:+LIFT_STATUS_GRACE_MISSES="$LIFT_STATUS_GRACE_MISSES"} \
    sh -c 'cd "$1" && shift && exec python3 -m lift_status "$@"' _ "$PREFIX" "$@"
