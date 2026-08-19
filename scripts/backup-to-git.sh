#!/bin/sh
#
# Commit and push the raw logs to a git remote, as an offsite backup.
#
# One-time setup (see README for the full walkthrough):
#   cd /var/lib/lift-status
#   git init -b main
#   git remote add origin git@github.com:<you>/lifts-data.git
#
# Only raw/ is committed. lift_status.db is deliberately excluded: it is a
# binary that rewrites wholesale every run, so git cannot delta it, and it is
# rebuildable from raw/ anyway. The raw logs alone are a complete backup.

set -eu

DATA_DIR="${LIFT_STATUS_DATA_DIR:-/var/lib/lift-status}"

notified=0

notify() {
    notified=1
    printf '%s\n' "$1" >&2
    if [ -n "${LIFT_STATUS_ALERT_WEBHOOK:-}" ]; then
        curl -fsS -m 10 -H "Title: lift-status backup failure" \
            -d "$1" "$LIFT_STATUS_ALERT_WEBHOOK" >/dev/null 2>&1 || true
    fi
}

# So a `set -e` abort anywhere below still alerts instead of failing silently.
on_exit() {
    status=$?
    if [ "$status" -ne 0 ] && [ "$notified" -eq 0 ]; then
        notify "lift-status backup: failed unexpectedly (exit $status) in $DATA_DIR.
Nothing new is offsite. Check:
  journalctl -u lift-status-backup.service -n 30"
    fi
    exit "$status"
}
trap on_exit EXIT

cd "$DATA_DIR" || {
    notify "lift-status backup: $DATA_DIR does not exist. Nothing is being backed up."
    exit 1
}

if [ ! -d .git ]; then
    notify "lift-status backup: $DATA_DIR is not a git repository. Run the
one-time setup in scripts/backup-to-git.sh. Nothing is being backed up."
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    notify "lift-status backup: no 'origin' remote configured in $DATA_DIR.
Nothing is being backed up."
    exit 1
fi

# Belt and braces: the poller never writes anything but raw/ and the db file,
# but an accidentally committed database would bloat the repo permanently.
if [ ! -f .gitignore ]; then
    printf 'lift_status.db\nlift_status.db-wal\nlift_status.db-shm\n.poll.lock\n.write-test\n' > .gitignore
fi

git add -A .gitignore raw

if git diff --cached --quiet; then
    echo "no new data to commit"
else
    git -c user.name="lift-status-collector" -c user.email="lift-status-collector@localhost" \
        commit -q -m "Message data through $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
fi

# Pull in anything pushed to origin from elsewhere first, so a rejected
# non-fast-forward push doesn't strand local commits until someone notices.
branch="$(git rev-parse --abbrev-ref HEAD)"
if ! git fetch -q origin 2>/tmp/lift-status-backup-fetch.err; then
    notify "lift-status backup: git fetch failed, so it's unknown whether
origin has commits this checkout lacks. Data is committed locally but not
pushed.

$(cat /tmp/lift-status-backup-fetch.err)"
    exit 1
fi

if git rev-parse --verify -q "origin/$branch" >/dev/null &&
    ! git -c user.name="lift-status-collector" -c user.email="lift-status-collector@localhost" \
        merge -q --no-edit "origin/$branch" 2>/tmp/lift-status-backup-merge.err; then
    git merge --abort 2>/dev/null || true
    notify "lift-status backup: origin has commits that conflict with
$DATA_DIR. Resolve manually, then re-run this script.

$(cat /tmp/lift-status-backup-merge.err)"
    exit 1
fi

# Push unconditionally, even when there was nothing new to commit. A previous
# push may have failed and left commits sitting only on this disk; treating
# "nothing to commit" as "nothing to do" would report success forever while
# the data was never actually offsite. Pushing an up-to-date branch is a
# cheap no-op.
if ! git push -q origin HEAD 2>/tmp/lift-status-backup-push.err; then
    notify "lift-status backup: git push failed. The data is committed locally
but is NOT offsite, so an SD card failure would still lose everything since
the last successful push.

$(cat /tmp/lift-status-backup-push.err)"
    exit 1
fi

echo "backed up through $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
