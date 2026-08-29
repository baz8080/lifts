#!/bin/sh
# The house dash is a spaced hyphen. See CLAUDE.md, § Punctuation.
# Tracked files only: a PR body or a chat reply is nobody's repository.
set -eu
cd "$(dirname "$0")/.."
if git grep -n -e '—' -e '–' -- . ; then
    echo "em or en dash found above; the house dash is a spaced hyphen - like this" >&2
    exit 1
fi
echo "no em or en dashes in tracked files"
