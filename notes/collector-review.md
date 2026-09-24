# The collector's first review

`lift_status/` and `scripts/` were written before PRs here went through a review
agent, and barely changed after: `parse.py`, `client.py` and `__main__.py` not at
all, `poll.py` by 16 lines. They are also the only code whose mistakes a
rebuild cannot undo, since a response that never reached the raw log is gone.
So they were reviewed once, as whole files, on 2026-09-24. The rest of the
repository was left alone: `lift_access/` and most of `lift_site/` have been
reviewed diff by diff since 2026-08-26, and the real-corpus and golden tests pin
what they publish.

Ten findings. Eight were fixed, one was not a real path, and one is left for now.

## Fixed

- **The database could cost the response.** `Store()` opened SQLite and ran the
  schema before the raw append, so a database left corrupt by a power cut, or
  locked past the 5s busy timeout, stopped every poll from reaching the log,
  with a traceback and no alert. `append_raw` now writes the line before the
  database is opened, and a database failure is its own alert and exit code 7,
  saying the response was kept and what to do for a lock, a full card or
  corruption. A fetch that failed keeps its own alert even when the database
  is broken too, since then there was no response to keep.
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
  marker outlived a recovery, so the same banner after a clean stretch was
  suppressed for up to 24h. The marker now counts consecutive clean runs and
  goes after four, two hours at the 30-minute cadence; a suppressed failure
  resets the count. Clearing it on the first clean run was tried first and
  rejected in review: a flapping API would then alert on every failure, which
  is what the window exists to stop.
- **systemd could kill a poll before it logged anything.** `TimeoutStartSec=60`
  was below the client's own worst case (three attempts of a 15s connect and a
  15s read, plus backoff and DNS). It is 300 now.
- **The backup could hang forever.** A oneshot has no start timeout by default,
  and ssh had no keepalive, so a push stalled on a half-open connection held the
  unit "activating" and turned every later firing into a no-op. ssh now has
  `ConnectTimeout` and `ServerAliveInterval`, and the unit has a 15-minute cap.
  The script traps TERM, because dash skips the EXIT trap on a signal it does
  not trap, and the cap would otherwise end the backup without an alert.

- **A `sort -u` merge replayed out of order.** `sort_keys=True` is there so two
  collectors' logs can be merged with `sort -u`, which is also how git's
  conflict on a shared day file gets resolved. But `sort -u` orders lines by
  their first key, `body`, and replay followed line order, so a merged file
  replayed out of time order. Replay now sorts each file by `fetched_at_utc`,
  stably. The cost is the clock jump the old line-order rule was for: after a
  power cut, fake-hwclock restores the last hourly save, so a catch-up poll can
  be stamped up to an hour before runs already in the same file, and a rebuild
  applies it before them where the live run applied it after. Line order only
  ever covered part of that, since a stamp that crosses midnight already lands
  in the wrong day's file, and it cannot survive a merge at all. On
  2026-09-24 all 2,224 real lines were already in time order within their
  files, so no rebuild moved. The owner's call: merging logs has to work.

## Not a real path

- **The backup merges `origin` into the tree the poller appends to, without the
  poll lock.** A merge only rewrites files that changed upstream, and nothing
  but the Pi writes `raw/`: the stations workflow touches `stations/` and
  `survey/`, through PRs. Taking the lock for a whole fetch and push would
  instead make a poll skip.

## Left for now

- **`time-sync.target` does not wait for NTP.** It is reached as soon as
  timesyncd starts unless `systemd-time-wait-sync.service` is enabled, and the
  install does not enable it, so a catch-up poll after a reboot can be stamped
  with fake-hwclock's time. Enabling the wait service risks a poll that never
  runs if NTP is unreachable, which is the silent failure this collector exists
  to avoid. Left as it is by the owner on 2026-09-24. If it is taken up, the
  shape is a poll that checks whether the clock is synced and still writes the
  line, flagged, rather than one that waits or skips.

## The review of the review - 2026-09-24

The commit that acted on the PR's review was merged without a review of its
own, and one found ten more. The root of three was the dedup marker: it held a
single digest of the whole banner, raw error included. The fixes were reviewed
in turn before they shipped, and that round changed the first of them.

- **Two faults at once took turns to alert.** With the database broken and the
  API flapping, the database and unreachable banners alternated, and each
  change of digest was delivered. Each kind now has its own window.
- **The same fault with different words was never suppressed.** 'timed out'
  then 'connection refused', or `lift check` wording the error with `str()`
  where the poll uses `repr()`, hashed apart. The kind is now the exit code,
  plus a detail where a difference is news: a rejected key carries the masked
  key, so a second key rejected within the day is pushed. Keying on the
  banner's title was tried first and rejected in review for exactly that: it
  would have sat on a newly captured key that was also refused. Schema root
  and schema drift share an exit code and so a window; the first push already
  said the shape moved.
- **A failure that was not delivered did not break the clean stretch.** The
  count was reset only when an alert was suppressed, so a fault lost to a
  webhook blip counted as clean. `fail()` resets it on every failure.
- **The database banner blamed `lift rebuild` for a lock.** A rebuild holds the
  poll lock, so a poll never sees its lock, and `lift stats` holds its read
  lock for far less than the 5s busy timeout. It says to find the holder with
  `fuser`.
- **The backup's TERM alert said nothing of the cause**, INT reported 143, and
  a TERM landing on a curl mid-alert lost the alert. 143 now always alerts,
  naming the timeout or a stop or shutdown; `on_exit` ignores TERM, which its
  curl inherits, so the cgroup-wide TERM cannot kill it; INT is 130.
- Three copies of the marker read became `_read_marker`, and `_run` classifies
  the fetch before opening the database rather than again inside the error
  handler. A marker in the older shape reads as empty, so the first failure
  after deploying can send one extra alert.

The finding that replay order no longer reproduces a live run after a
fake-hwclock jump is the trade-off above, restated, and stands.
