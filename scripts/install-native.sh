#!/bin/sh
#
# Install the collector on a systemd host such as a Raspberry Pi.
# Run from a checkout of this repository:
#
#   sudo sh scripts/install-native.sh
#
# Idempotent: safe to re-run after a git pull to deploy an update.

set -eu

PREFIX="/opt/lift-status"
DATA_DIR="/var/lib/lift-status"
ENV_FILE="/etc/lift-status.env"
SERVICE_USER="lift-status"

SRC=$(cd "$(dirname "$0")/.." && pwd)

if [ "$(id -u)" -ne 0 ]; then
    echo "must run as root (use sudo)" >&2
    exit 1
fi

# The collector is standard library only, so this is the entire dependency list.
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "python3 3.9 or newer is required; found $(python3 -V 2>&1)" >&2
    exit 1
fi

# Timezone data must be present or every start/end timestamp fails to parse.
# Standard on Raspberry Pi OS and Debian, but worth failing loudly rather than
# collecting months of messages with null times.
if ! python3 -c 'from zoneinfo import ZoneInfo; ZoneInfo("Europe/Dublin")' 2>/dev/null; then
    echo "Europe/Dublin timezone unavailable. Install tzdata:" >&2
    echo "  sudo apt-get install -y tzdata" >&2
    exit 1
fi

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "creating service user $SERVICE_USER"
    useradd --system --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

echo "installing code to $PREFIX"
mkdir -p "$PREFIX"
rm -rf "$PREFIX/lift_status" "$PREFIX/scripts"
cp -r "$SRC/lift_status" "$PREFIX/"
cp -r "$SRC/scripts" "$PREFIX/"
chmod +x "$PREFIX/scripts/"*.sh

mkdir -p "$DATA_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"

echo "installing the 'lift' command to /usr/local/bin"
install -m 755 "$SRC/scripts/lift-wrapper.sh" /usr/local/bin/lift

# Pre-seed the host key for the backup push. The service user's HOME is the
# data directory, and relying on ssh writing a known_hosts file there on
# first connect is both untidy and a silent trust-on-first-use. Seeding it
# here makes the backup work on its first run instead of failing with "Host
# key verification failed".
KNOWN_HOSTS="/etc/lift-status-known_hosts"
if [ ! -s "$KNOWN_HOSTS" ] && command -v ssh-keyscan >/dev/null 2>&1; then
    echo "seeding $KNOWN_HOSTS for github.com"
    ssh-keyscan -t rsa,ecdsa,ed25519 github.com > "$KNOWN_HOSTS" 2>/dev/null || true
    chmod 644 "$KNOWN_HOSTS"
fi

# If the backup deploy key exists but isn't owned by the service user (the
# common mistake: `sudo ssh-keygen ...` leaves it root-owned), fix it here.
# lift-status-backup.service runs as $SERVICE_USER, not root, and ssh refuses
# to load a private key it can't read with a bare "Permission denied" that
# gives no hint the fix is a chown.
DEPLOY_KEY="/etc/lift-status-deploy-key"
if [ -f "$DEPLOY_KEY" ]; then
    owner=$(stat -c '%U' "$DEPLOY_KEY" 2>/dev/null || stat -f '%Su' "$DEPLOY_KEY" 2>/dev/null || echo "")
    if [ "$owner" != "$SERVICE_USER" ]; then
        echo "fixing ownership of $DEPLOY_KEY (was $owner, needs to be readable by $SERVICE_USER)"
        chown "$SERVICE_USER:$SERVICE_USER" "$DEPLOY_KEY"
    fi
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "creating $ENV_FILE"
    cat > "$ENV_FILE" <<'ENVEOF'
# Failure alerts. Without this, the collector can stop and nobody will know.
# An ntfy.sh topic needs no account - pick an unguessable name.
#LIFT_STATUS_ALERT_WEBHOOK=https://ntfy.sh/change-me-to-something-unguessable

# REQUIRED. The key is not stored in the repository - capture it from a
# browser session (devtools -> Network -> the request to
# connect.irishrail.ie/realtime/messages -> the 'x-api-key' header) and paste
# it here. Re-capture the same way whenever Irish Rail rotates it.
LIFT_STATUS_API_KEY=

# How many consecutive misses before a message is marked closed. Default 1
# (close on first miss). Raise this only if the data shows real flapping -
# see the README for the tradeoff.
#LIFT_STATUS_GRACE_MISSES=1
ENVEOF
    chmod 600 "$ENV_FILE"
fi

echo "installing systemd units"
cp "$SRC/scripts/systemd/"*.service "$SRC/scripts/systemd/"*.timer \
    /etc/systemd/system/
systemctl daemon-reload

# daemon-reload alone does not re-arm a running timer, so a changed schedule
# would silently not take effect until the next reboot.
for timer in lift-status.timer lift-status-backup.timer; do
    if systemctl is-active --quiet "$timer"; then
        echo "restarting $timer to pick up any schedule change"
        systemctl restart "$timer"
    fi
done

echo
echo "Installed. Next:"
echo "  1. Set LIFT_STATUS_API_KEY and LIFT_STATUS_ALERT_WEBHOOK in $ENV_FILE"
echo "  2. Prove alerts work:  sudo lift test-alert"
echo "  3. Check the API key:  sudo lift check"
echo "  4. One run now:        sudo systemctl start lift-status.service"
echo "  5. Enable the timer:   sudo systemctl enable --now lift-status.timer"
echo "  6. Set up the backup remote (see README), then:"
echo "       sudo systemctl enable --now lift-status-backup.timer"
echo
echo "Day to day:"
echo "  sudo lift stats                            what has been collected"
echo "  systemctl list-timers lift-status.timer    when it next runs"
echo "  journalctl -u lift-status.service -n 20    what the last runs did"
