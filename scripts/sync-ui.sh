#!/bin/sh
# Refresh the vendored shared UI from ../statusui (see lift_site/ui/UPSTREAM).
set -eu
here="$(cd "$(dirname "$0")/.." && pwd)"
exec "$here/../statusui/sync.sh" "$here/lift_site/ui"
