#!/bin/bash
# Bring a web session up to where a local checkout already is: dependencies
# installed, the collected corpus present, and LIFT_STATUS_DATA_DIR pointing at
# it so tests/test_site_real.py runs instead of skipping.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "$CLAUDE_PROJECT_DIR"

# dev and site are the default groups, so this also brings in statusui at the
# commit uv.lock pins
uv sync

# The data is a separate repository. CLAUDE.md says ../lifts-data and CI checks
# out the same one; the database is derived, so it is rebuilt rather than fetched.
DATA="$(cd .. && pwd)/lifts-data"
if [ -d "$DATA/.git" ]; then
  git -C "$DATA" fetch --depth 1 origin main && git -C "$DATA" reset --hard origin/main
else
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/baz8080/lifts-data "$DATA"
fi
uv run python -m lift_status --data-dir "$DATA" rebuild
echo "export LIFT_STATUS_DATA_DIR=$DATA" >> "$CLAUDE_ENV_FILE"

# The design layer is edited upstream and rolled out from there, so a session
# that touches the UI needs the checkout and not just the pinned dependency.
# Not fatal: everything except a statusui edit works without it.
[ -d "../statusui/.git" ] ||
  git clone --depth 1 https://github.com/baz8080/statusui ../statusui ||
  echo "note: ../statusui not cloned; UI changes cannot be made upstream from here"
