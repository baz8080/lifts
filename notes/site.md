# The site: what it measures, and what was measured before deciding

Decisions behind `lift_site`, dated, with the numbers that settled them. The
corpus at the time of writing is ten days of polls (8-17 August 2026, 436 runs,
435 of them ok), holding 113 distinct notices of which 17 are about a lift or
an escalator. Everything below should be re-checked once there is a season of
data; the point of writing it down is so that re-check compares against
something.

## Settled - 2026-08-18

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
- **2026-08-18**, after they were not. Bucketing by UTC date while printing
Dublin wall-clock split them for four hours a day in summer: a notice first
seen at the 23:15 UTC poll on 31 August lit the 31 August cell while its own
summary read "first listed 1 Sep 2026, 00:15", and at a month boundary it was
filed under August and absent from September. Two conventions for one date is
a bug in either direction; the site says Dublin everywhere a reader can see.
The cost is that a month is no longer a whole number of days - March is 23
hours short and October 25 long - so the cell count comes from
`calendar.monthrange`, never from subtracting the bounds.

Durations are computed from the offset-aware instants and shipped in the case
record (`hours`, `lead_days`) rather than recomputed from the rendered
strings, which carry no offset: subtracting them loses the hour at the October
change, and did.

## Open

- **A reopened notice publishes its gap as listed.** `LIFT_STATUS_GRACE_MISSES`
  is 1, and a notice that vanishes and comes back *unchanged* reopens the same
  row: `closed_at_utc` is nulled and `first_seen_at_utc` kept, so the site
  paints the whole absence as listed - days that were polled every 30 minutes
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

## The design layer is shared with uisce and esb - 2026-08-19

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

## The vendored copy became a pinned dependency - 2026-08-20

One day was enough to show the vendored mechanism's cost: a shared fix meant a sync, test,
commit and PR in each of three repos, and the sites still drifted - this site and esb were
synced to statusui `f248ac3` while uisce sat five UI commits behind, with nothing failing to
say so (the byte-compare only fires against the checkout you happen to have). `statusui` is
now a real package, declared in the `site` dependency group with a `[tool.uv.sources]` git
source and pinned to a commit in `uv.lock` - `dependencies` stays literally empty, so the Pi
collector's stdlib-only file-copy install is untouched, and `default-groups` keeps a plain
`uv run` building. The vendored tree, `scripts/sync-ui.sh` and the byte-compare went; the
no-redeclared-globals guard stayed as `tests/test_ui_globals.py`, reading `ui.js` from the
installed package. **To change the shared UI now:** edit in `../statusui`, test there, push,
then `../statusui/rollout.sh` bumps the pin in all three sites, runs each site's tests and
opens the PRs. An unpushed statusui change can be tried here with
`uv run --with-editable ../statusui python -m lift_site ...`.

## The design alignment pass - 2026-08-26

The owner reviewed uisce and esb side by side, picked a winner per element, and asked for the
same language here, so the three sites read as one product. What this site absorbed, and what
it deliberately kept:

- **Banner** takes the shared shape: `**August 2026 so far:** 3 out of service and 1 planned
  works across 4 stations` - the bold long-month prefix, " so far" only while the viewed
  month is still collecting (`observed_iso` month == viewed month). The old line was the
  right-now station count; the right-now information moved to the latest month's tile (the
  lifts / escalators split "with a notice up at the last poll"), which replaces the plain
  ongoing-count tile there. The freshness chip (statusui `freshness()`, the age not the
  timestamp, stale past 16 h) replaces both the banner's "as of …" and the header's
  `stampLine`; the exact horizon survives as the chip's hover title and, in full, on the
  static station pages' sub line. `observed_iso` and `stale_hours` joined the payload for it.
  The stamps that remain visible are still UTC and say so - the wall-clock/UTC split holds.
- **The national heading** is the shared "The national picture in August 2026" (was "Across
  the network in Aug 2026"); the "stations affected" and "out of service / planned works"
  tiles went, because the banner now carries both.
- **The legend** moved above the list, swatches went from inline styles to the same
  `.legend i.bN` site.css rules that colour the bars (so the key cannot drift), and it now
  also appears at the top of the station view and the static station pages, which had none.
- **Search** is statusui's shared `bindSearch`, fed an index built at boot (each station
  keyed under its own name - that is what keeps the match a substring match; `searchHits`
  grew a dedupe upstream for exactly this shape). The per-hit "nothing listed in Aug 2026"
  note survives via the new `note()` hook. Lost, accepted: the empty state is now the shared
  "Nothing matching “q”" rather than "No station matching “q” has had a notice yet".
- **Rows**: the day-count stat renamed `.days` → the shared `.cml` (site.css rule deleted;
  base carries it). The wider `--row-cols`/`--stats-cols` stay - station names and the
  "out of service" labels are longer than the siblings', and the knobs exist for exactly
  that. The fixed worst-first sort stays: it is the settled decision above, and it is also
  esb's pattern.
- **Day captions** go through `fmtDay` ("Sun 9 Aug: lift out of service"), matching the
  static pages, which always did.
- **Footer**: "What this measures" became a disclosure like its siblings, keeping the
  bold no-fixed-field caveat always visible above the disclosures; the final line is the
  shared "Source code · not affiliated with Iarnród Éireann." on both page types.

Not taken, on purpose: no grade, no percentage, no intensity ramp (the settled "a notice is
listed or it is not"); no alphabetical-only list (26 counties scroll, a growing station list
led by live outages is the site's point); and none of the measured-interval wording moved -
"no longer listed", never "fixed".

## The permalink affordance moved out of the footer - 2026-08-26

Every drill-down on all three sites now offers the static page it has a permanent URL for, in the same place: its own line directly under the heading, above the month tabs where a site has them. The rule that styles that line, `.chead + .sub`, is promoted to statusui's `base.css`: lifts and esb had been carrying it byte for byte in their own `site.css` and uisce is now the third consumer, which is exactly the "two sites want it and none wants it different" test. The three local copies went with the pin bump that followed.

This site already had the link - it was the model for the other two - but it trailed the descriptive sentence after a `·`, which made it the least prominent of the three once esb and uisce gained theirs. It now has its own line.

**The wording is deliberately per site, and it is the interesting part.** A link's label makes a promise. Name it for the content on the other side and a reader who is already looking at that content asks "am I not looking at this already?" - so the label has to match the *content relationship*, not a house style:

That yields two categories, not three:

| | The view shows | The page shows | Label |
|---|---|---|---|
| esb, uisce | one month at a time | every month | "Every month for County X on one page" |
| lifts | every month, newest first | the same months and cases (`render.station_page`) | "Permanent link to Athy station" |

esb and uisce stand in the same relation to their views, so they say the same sentence. uisce first shipped "Every notice ever recorded in Co. Carlow" and that was wrong - its page caps the notice list at 60 and prints "older notices not shown here", so the label was contradicted by the page it landed on. Corrected the same day.

Naming *this* site's for its content would be a false promise in the other direction: there is no more content on the other side, only a durable address. Rejected on those grounds, not on taste.

"Permalink" as a word was considered and kept only here, where nothing better fits. It is blogging-era vocabulary that a general audience mostly does not hold; the failure mode is a missed click, which is cheaper than the broken promise a wrong content label would make on a site whose whole pitch is that its numbers are trustworthy. The station name is in the link text because a screen reader lists links stripped of their context.

Guarded by `tests/test_permalink_affordance.py`.
