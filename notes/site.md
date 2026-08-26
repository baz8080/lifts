# The site: what it measures, and what was measured before deciding

Decisions behind `lift_site`, dated, with the numbers that settled them. The
corpus at the time of writing is ten days of polls (8-17 August 2026, 436 runs,
435 of them ok), holding 113 distinct notices of which 17 are about a lift or
an escalator. Everything below should be re-checked once there is a season of
data; the point of writing it down is so that re-check compares against
something.

## Settled — 2026-08-18

### Rows are stations, keyed by location code

Every lift/escalator notice seen names exactly one `locationCodes` entry, and
`eventStops[0].sStop` carries the full name ("Dublin Connolly" where the head
says "Connolly"). The code is the identity; the name is display, taken from
the newest notice, with the head's prefix as the fallback if a notice ever
arrives without stops. The overview lists only stations with a notice in the
selected month; the station page carries every month since collection began.

### Escalators are in, tagged, not excluded

2 of the 17 notices (Connolly, Pearse) are escalators. Same feed, same wording,
same stations, same accessibility consequence. A day cell prefers a lift notice
over an escalator one, and either over planned works.

### The measured interval is the listing, not Irish Rail's start date

Each notice carries a `start`. Against the 17 notices, that start predates the
poll the notice was first seen at in **14**, and by a week or more in **12**:
Rush and Lusk 451 days, Docklands 253, Pearse 242, Hazelhatch 237, Thurles 197,
Ballybrophy 100. Those days were watched - the feed was polled every 30
minutes from 8 August - and the notice was not there. Colouring them would
publish an observation nobody made.

So the day bars, the month filing, the station-day totals and every duration
measure `first_seen` to `end`. The start Irish Rail wrote is shown on the
outage as their claim ("Irish Rail's notice dates it from …, N days before it
was listed") and colours nothing. This is the opposite call to the sibling
`esb` site, where the operator's start was validated as immutable and
back-dated *by hours*; here it is back-dated by months and does not describe
the listing.

### "No longer listed" is the word, not "fixed"

There is no completion signal in the feed. Notices arrive and go in batches -
6 present at the first poll, 3 new at 10 Aug 14:30, 4 new at 13 Aug 10:30, 2
at 17 Aug 14:02; 3 removed in the same poll at 14 Aug 14:01 - which is
somebody publishing, not lifts breaking. An outage ends when its notice is
first absent, and the page says exactly that.

### Notices reissued in the same poll are one outage; a gap is two

The collector keys a notice on `head` + codes + `start`, so an edited head or
a corrected start is a new message to it, closing the old one at the very poll
the new one appears. `merge_edits` folds a same-station, same-kind successor
whose `first_seen` equals the predecessor's `closed_at` - an exact match on
the run timestamp, not a tolerance - and records it as a reissue. A notice
back one poll or more later stays a separate outage: Docklands closed 14 Aug
14:01 and a new notice (new start) appeared 17 Aug 14:02, three days apart,
and that gap is real information. Two notices open at once at one station
(one per lift) never merge, since the older is still listed when the newer
appears. No lift notice has yet needed the merge; non-lift ones have
(`Station currently closed` → `Station currently CLOSED` → `Station is OPEN`,
ids 42→45→46).

### Planned works is what the notice says

"temporarily unavailable due to planned works" tags an outage Planned works;
anything else is Out of service. 5 of the 17 are planned. Nothing is excluded
from any count on that basis - there is no grade to keep them out of.

### No grade

The sibling site grades counties on the operator's own published standard.
There is no equivalent for lifts, and the feed carries no magnitude - a notice
is listed or it is not - so a cell says only that and the overview sorts by
"listed right now" then days listed.

### `end` is shown, not used

For 13 of the 17 notices `end` is a placeholder near the end of the year
(28-31 December). For a few it looks real - Greystones `2026-08-12 23:59`,
removed 12 Aug 23:02; Connolly escalator and the second Docklands notice
`2026-08-24`; Pearse escalator `2026-08-30`. Too few to trust yet. It is
printed as "listed end …" and plays no part in anything measured. Revisit if a
season shows the real-looking ones predicting removal.

### Windows end at the collection horizon, not the build clock

Straight from `esb`: `until` is the last run with `outcome = 'ok'`, and days
between it and the build are "no data", never "nothing listed". A notice first
seen at that very poll is listed for zero minutes - `first_seen`, `end` and
the horizon coincide - and `listed_in` / `listed_days` count it in the
horizon's month so the headline, the bar and the shard agree.

### Displayed instants are Dublin wall-clock, and so are the day buckets

The start Irish Rail writes is a Dublin time with no offset ("since 5 May,
00:00"). Rendered in UTC it becomes "4 May, 23:00", which misquotes them. So
every timestamp on an outage is shown in Europe/Dublin; the build and horizon
stamps stay UTC and say so.

The day cells, the month filing and `partial_days` are bucketed in Dublin too
— **2026-08-18**, after they were not. Bucketing by UTC date while printing
Dublin wall-clock split them for four hours a day in summer: a notice first
seen at the 23:15 UTC poll on 31 August lit the 31 August cell while its own
summary read "first listed 1 Sep 2026, 00:15", and at a month boundary it was
filed under August and absent from September. Two conventions for one date is
a bug in either direction; the site says Dublin everywhere a reader can see.
The cost is that a month is no longer a whole number of days — March is 23
hours short and October 25 long — so the cell count comes from
`calendar.monthrange`, never from subtracting the bounds.

Durations are computed from the offset-aware instants and shipped in the case
record (`hours`, `lead_days`) rather than recomputed from the rendered
strings, which carry no offset: subtracting them loses the hour at the October
change, and did.

## Open

- **A reopened notice publishes its gap as listed.** `LIFT_STATUS_GRACE_MISSES`
  is 1, and a notice that vanishes and comes back *unchanged* reopens the same
  row: `closed_at_utc` is nulled and `first_seen_at_utc` kept, so the site
  paints the whole absence as listed — days that were polled every 30 minutes
  and showed nothing. Any gap length qualifies, not just a one-poll flap.
  The site cannot fix this alone: once the row is reopened the gap is nowhere
  in `messages`, and `identity_key` is UNIQUE so the re-listing cannot become
  its own row. It needs the collector to record the re-listing instant (an
  intervals table, or a `previous_closed_at_utc` column) and the site to build
  one outage per interval. One reopen exists so far, a delay notice, not a
  lift. `merge_edits` already handles the *edited*-notice case; this is the
  unchanged-notice one.
- **Same-day merge tolerance.** The reissue rule is exact-poll. If Irish Rail
  turns out to reissue notices with a poll's gap, revisit with numbers.
- **The 131 unidentifiable items** are all delay notices with empty
  `locationCodes` and are irrelevant to this site; noted so nobody goes
  looking.

## The design layer is shared with uisce and esb — 2026-08-19

The three status sites are deliberately look-alike, and every UI fix had been ported three
times by hand. The tokens, base rules, row/bar/card components and the browser helpers now
live in `../statusui` (`baz8080/statusui`), vendored under `lift_site/ui/` and inlined into
`index.html` and the station pages at build by `statusui.assemble()`. `lift_site/site.css` is
what is this site's own: the cell colours, the wider name column, the notice-text style.
Instants keep their year through `when(ts, true)` and listings their days-to-months scale
through `fmtHours(h, fmtDays)`; both moved upstream with those as options.

Vendored rather than installed, so `dependencies` stays empty and a clone still builds; drift
is guarded by `tests/test_ui_vendored.py`, which compares the copy to `../statusui/ui` when
that checkout exists and skips otherwise. **To change the shared UI:** edit in `statusui`,
commit, `scripts/sync-ui.sh`, run the tests, commit. The full list of what is shared and what
is per-site is in statusui's README.

## The vendored copy became a pinned dependency — 2026-08-20

One day was enough to show the vendored mechanism's cost: a shared fix meant a sync, test,
commit and PR in each of three repos, and the sites still drifted — this site and esb were
synced to statusui `f248ac3` while uisce sat five UI commits behind, with nothing failing to
say so (the byte-compare only fires against the checkout you happen to have). `statusui` is
now a real package, declared in the `site` dependency group with a `[tool.uv.sources]` git
source and pinned to a commit in `uv.lock` — `dependencies` stays literally empty, so the Pi
collector's stdlib-only file-copy install is untouched, and `default-groups` keeps a plain
`uv run` building. The vendored tree, `scripts/sync-ui.sh` and the byte-compare went; the
no-redeclared-globals guard stayed as `tests/test_ui_globals.py`, reading `ui.js` from the
installed package. **To change the shared UI now:** edit in `../statusui`, test there, push,
then `../statusui/rollout.sh` bumps the pin in all three sites, runs each site's tests and
opens the PRs. An unpushed statusui change can be tried here with
`uv run --with-editable ../statusui python -m lift_site ...`.

## The stale banner — 2026-08-26

On the evening of 2026-08-25 this site and esb both said "collection has stopped" while
their collectors were running normally. The statusui rollout merged to main on each repo
that evening, and the site rebuilds on every push to main, not just on its morning cron —
so each rebuild landed late in the daily push cycle and saw data legitimately close to a
day old, past the then 24-hour `STALE_AFTER`. The banner then sat on the live pages until
the next rebuild. The general lesson: a rebuild can land at *any* point in the push cycle,
so the threshold must sit above the longest gap between pushes, not at it. The incident
arithmetic is written up in esb's `notes/staleness.md`.

The fix is the same in both repos. The backup timer now fires at local midnight **and
noon** (`scripts/systemd/lift-status-backup.timer`, effective on the Pi the next time
`scripts/install-native.sh` runs there), and a second site cron at 12:40Z picks the noon
push up — past its worst case whether Dublin is on UTC or UTC+1. The second slot follows
uisce's twice-daily DB build and exists for publication latency only: it roughly halves
how far the published page runs behind the feed, and changes nothing about the data — the
raw logs capture every poll either way.

`STALE_AFTER` is now 16 hours, rescaled to the cadence. Consecutive pushes are at most
~13.5 hours apart (30-minute jitter, plus the October clock change), and the horizon
trails a push by up to another half-poll, so ~14 hours is the legitimate maximum a build
can see. A dead collector shows 17.2+ hours at the first morning cron after a missed
midnight push. Any threshold in (14, 17.2) separates the two; 16 sits between. A single
missed *noon* slot shows ~14–15 hours at the 12:40Z build — indistinguishable from
unlucky timing — and is deliberately not flagged: the noon slot is a latency
optimization, and the midnight arithmetic catches a dead collector six hours later.
