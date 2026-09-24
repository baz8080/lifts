# The collector's first review

`lift_status/` and `scripts/` were written before PRs here went through a review
agent, and barely changed after: `parse.py`, `client.py` and `__main__.py` not at
all, `poll.py` by 16 lines. They are also the only code whose mistakes a
rebuild cannot undo, since a response that never reached the raw log is gone.
So they were reviewed once, as whole files, on 2026-09-24. The rest of the
repository was left alone: `lift_access/` and most of `lift_site/` have been
reviewed diff by diff since 2026-08-26, and the real-corpus and golden tests pin
what they publish.

Ten findings. Seven were fixed, one was not a real path, and two are open.

## Fixed

- **The database could cost the response.** `Store()` opened SQLite and ran the
  schema before `write_raw`, so a database left corrupt by a power cut, or
  locked past the 5s busy timeout, stopped every poll from reaching the log,
  with a traceback and no alert. `append_raw` now writes the line before the
  database is opened, and a database failure is its own alert and exit code 7,
  saying the response was kept.
- **A full SD card was a traceback, not the storage alert.** `check_writable`
  touches an empty file, which needs no data block and passes on a full disk.
  An `OSError` from the append now goes to the storage banner.
- **A cut-off last line took the next good one with it.** A power cut mid-append
  leaves no trailing newline, and the next record was appended onto the
  fragment, so replay dropped both. The append now finishes the broken line
  first, and only the fragment is lost.
- **A truncated or corrupt gzip body escaped the client.** `gzip.decompress`
  raises `EOFError` or `zlib.error`, neither an `OSError`, so they bypassed the
  retry, the raw line and the alert. They are now a `TransientError`.
- **A second outage within a day of the first was silent.** The alert dedup
  marker outlived a recovery, so the same banner after a clean run was
  suppressed for up to 24h. A clean run now clears it. The cost is that a
  fault flapping at poll granularity alerts on each return; each poll already
  retries three times, so that is a real outage each time.
- **systemd could kill a poll before it logged anything.** `TimeoutStartSec=60`
  was below the client's own worst case (three attempts of a 15s connect and a
  15s read, plus backoff and DNS). It is 300 now.
- **The backup could hang forever.** A oneshot has no start timeout by default,
  and ssh had no keepalive, so a push stalled on a half-open connection held the
  unit "activating" and turned every later firing into a no-op. ssh now has
  `ConnectTimeout` and `ServerAliveInterval`, and the unit has a 15-minute cap.

## Not a real path

- **The backup merges `origin` into the tree the poller appends to, without the
  poll lock.** A merge only rewrites files that changed upstream, and nothing
  but the Pi writes `raw/`: the stations workflow touches `stations/` and
  `survey/`, through PRs. Taking the lock for a whole fetch and push would
  instead make a poll skip.

## Open

- **`sort -u` and replay order disagree.** CLAUDE.md says `sort_keys=True` lets
  two machines' logs be merged with `sort -u`. Replay follows line order within
  a file, and `sort -u` orders lines by their first key, `body`, so a merged
  file replays out of time order. It has never happened (one collector), and
  the fix is a choice: sort by `fetched_at_utc` within a file on replay, which
  `iter_raw_lines` currently refuses because of clock jumps, or merge by
  timestamp rather than `sort -u`.
- **`time-sync.target` does not wait for NTP.** It is reached as soon as
  timesyncd starts unless `systemd-time-wait-sync.service` is enabled, and the
  install does not enable it, so a catch-up poll after a reboot can be stamped
  with fake-hwclock's time. Enabling the wait service risks a poll that never
  runs if NTP is unreachable, which is the silent failure this collector exists
  to avoid, so it is not changed blind.
