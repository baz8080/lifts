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
**Amended 2026-08-28**: there is a grade now, and a planned-works notice is
kept out of it for its first week only. See "Planned works are excused for a
week" below. Nothing is excluded from any *count* on that basis still.

### No grade

The sibling site grades counties on the operator's own published standard.
There is no equivalent for lifts, and the feed carries no magnitude - a notice
is listed or it is not - so a cell says only that and the overview sorts by
"listed right now" then days listed.

**Reversed 2026-08-28.** See "The grade is availability" below: the first
reason still holds and is now said out loud on the page, and the second was
answered by counting days rather than looking for a magnitude in the feed.

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
- **No station inventory, so no real denominator and no way to tell "this
  station has no lift" from "this station's lift is fine".** Scoped in
  `accessible-routes.md`.

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

Not taken, on purpose (**the first of these was reversed on 2026-08-28**): no
grade, no percentage, no intensity ramp (the settled "a notice is
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

## The grade is availability, and the bars split by kind - 2026-08-28

The corpus is now 20 days (8-28 August 2026, 940 runs, 937 ok), 23 outages
across 20 stations, of which 5 are planned works and 2 are escalators.

### The grade is availability

**Amended 2026-08-29.** Three things below are superseded and left standing
because the reasoning around them still holds. The number is no longer lift
notices alone - both kinds count, see "An escalator out is a day the station
was short of a way up". The no-EU-target paragraph is no longer "said plainly
in the footer": that paragraph was removed from the page, and the reasoning
lives here instead. And the Pearse example at the end of this section is stale
- Pearse now grades F / 22% on its escalator, and Tullamore is the station
that carries an A over planned-works cells.

**Amended again 2026-09-03.** The number is lift notices alone once more, and
the key says so; see "The grade is lift availability" at the end of this file.

"5 days listed" was a raw count: it says nothing about whether that is bad,
and a 31-day month and a 20-day partial one are not comparable by it. The
number on a row is now the share of the days watched on which no lift notice
was listed at that station, and the chip is a band of it - statusui's
`.gradechip`, the same component esb and uisce carry.

**There is no Irish or EU target to grade against, and the page says so.** The
PRM TSI (Regulation (EU) 1300/2014) sets lift and escalator design rules and
an operational duty on the station manager to hold a written policy ensuring
access "at all operational times" - no percentage, no reporting duty. Irish
Rail's Passengers' Charter promises only "every effort ... available as
advertised", and the NTA-funded "Big Lift" programme (52 stations, 2020-2024)
publishes no availability figure. The regulators that publish numbers are
elsewhere: ORR/Network Rail (8,696 lift faults in a year, 6.6 per lift, over
20 hours average repair) and TfL historically (93.7% lift availability, 98.8%
excluding planned works). So the scale is this site's own, said plainly in the
footer rather than dressed up as a standard.

The bands are calibrated in days a reader can count, not borrowed from an
annual-availability figure: A is nothing listed, B 95%+, C 90%+, D 75%+, E 50%+,
F below that. Over a 31-day month that is one day listed for B, two or three for
C, up to a week for D, up to half the month for E. Bands tuned for TfL's 98%
were tried on paper first and put every station in the bottom band: at day
granularity one listed day in a month is already 96.8%.

#### The scale grew an E - 2026-08-29

The scale ran A, B, C, D, F. Skipping E is an American-ism and Irish Rail is not
American, so the letter was added. It splits the old F band and moves nothing
else: every cut from 100 down to 75 sits where it did, so no station-month
graded A to D changes letter.

The cut is 50%, which is the same kind of number the other cuts are: a count of
days a reader can hold. Availability is floor-divided, so over a 31-day month a
floor of 50 makes E 8 to 15 days listed and F 16 or more, which is exactly "up
to half the month" against "more than half".

The measurement agrees, which is not something the arithmetic guaranteed. Over
the 21 graded station-months in a rebuild of the current lifts-data the old F
band held nine, at 0, 0, 18, 22, 22, 50, 68, 68 and 72 per cent. There is a real
gap between 22 and 50, and the cut lands in it: E takes Limerick Junction,
Docklands, Rush and Lusk, and Clondalkin, four stations listed for part of the
month, and F keeps the five that were listed for most or all of it, Athy and
Midleton among them at nothing available at all. Cuts at 60 and 40 both fall
inside the same gap and split it identically, so 50 was chosen for saying
something a reader can repeat.

Grade mix: A 1, B 1, C 5, D 5, F 9 becomes A 1, B 1, C 5, D 5, E 4, F 5.

Rejected: hours-listed availability, which is more precise but would print
99.9% beside a bar with a red day in it - the bar is days, so the grade is
days. Rejected: bands on the days-listed count, which keeps the raw number's
incomparability between a full month and a partial one. Availability is
floored, never rounded, so 100% cannot round up from a day that counted. It
is not "nothing was listed", though, and the grade key does not say so: works
inside their grace are on the bar and off the total, and Pearse grades A over
six planned-works cells.

### Planned works are excused for a week

Planned-works notices were masking the thing the site measures: 5 of 23, and
they sit for months. Works listed **7 days or less in total cost nothing**;
past that, every day they are listed counts, the first week included. A week
is a plausible maintenance window, and Irish Rail's own end dates are
placeholders, so the listing is the only measure of how long works ran.

On this corpus: Pearse's lift notice (5 days) and Greystones' (2 days) are
excused; Limerick Junction's (10 days) and Midleton's (19 days and still up)
are not. The grace is a property of the notice, not of the month, so a
fortnight of works spanning a month end counts in both halves.

**In total** is doing work in that sentence, and two reviews moved it. It was
first written per segment, which excused a month of works reissued every few
days - the fold `merge_edits` exists to perform. It was then written over the
outage's whole listing, which let a fault that replaced the works reach back
and charge for the maintenance week already forgiven. The test case is six
days of works then four of fault: the fault's four days count and the works'
seven do not, which is 60% and an F. Under the whole-listing rule all eleven
counted, which is 0% and also an F - the same letter, a different number, and
the difference grows with the works. So it is the planned segments, added up,
and nothing else: what the works cost, measured on the works.

### One bar per kind

Pearse is the case: its escalator has been listed since 13 August while its
lifts came back the same day, and one composite bar painted the station for a
working lift. A bar now carries one kind - the lift bar is the row's bar, and
a station gets a second strip only in a month it had an escalator notice. The
day-cell code for escalators (`2`) is gone: the code says fault or planned
works, and which kind is the bar it sits in. This supersedes "a day cell
prefers a lift notice over an escalator one" under Escalators above; the
preference no longer has anything to decide.

The escalator is out of the grade for the same reason it has its own bar: the
lift is the step-free route. A station whose escalator is listed still leads
the overview, because "a notice up right now" is the first sort key.

**Reversed 2026-08-29.** See "An escalator out is a day the station was short
of a way up" below: both kinds count now, and only the bars stay split.

**Reinstated 2026-09-03.** The lifts-only rule stands again, with the grade
named for what it counts; see "The grade is lift availability" at the end of
this file.

Rejected: labelling the two strips on an overview row. The label column
shortened that one station's bar and knocked its days out of line with every
other row's. The labels stay on the drill-down, where the bars are tall.

**Superseded 2026-09-01.** See "The bars say which kind" below: a label column
reserved on every row cannot knock one row out of line with the others, and
what appears in it on an overview row is a glyph rather than a word.

Two layout bugs came out of it, both on phones. statusui's 640px reflow places
`.bar` by grid area, which inside the new `.bars` wrapper put both strips on
one implicit line and painted the escalator over the lift; the wrapper takes
the area now and releases the strips. And under 480px the stats held their
195px beside the name, leaving "Clondalkin Fonthill" 57px and an ellipsis - so
below that width the stats take a line of their own and `--stats-cols` stops
reserving a fixed column. That second one predates this pass; the row was just
as squeezed when the figure read "5 days listed".

### Irish Rail's end date goes when the notice does

`end` is still shown, not used, but only while the notice is still listed. On
a notice that has come down, "listed end 30 Dec 2026" reads as if the works
were still running - which is exactly how Pearse's closed lift notice read.
The notice coming down is the completion signal; a placeholder that outlived
its notice is noise. Amends "`end` is shown, not used" above.

### The national picture reads as availability

"station-days with a notice" was a number without a scale. The tiles are now
the aggregate availability of the stations listed that month - and only those,
because the feed names a station when something is wrong with it and the site
has no roll of the stations that have a lift at all, so any wider denominator
would be invented. The composite "4 / 1 lifts / escalators" tile is split in
two. Getting a real denominator needs a station inventory scraped from
irishrail.ie, which is a second source with its own staleness and its own
name-to-code join; not done here.

## The grade counts both kinds, and overrun works get their own colour - 2026-08-29

The corpus is 21 days (8-29 August 2026, 964 runs), 24 outages across 21
stations, of which 6 are planned works and 2 are escalators.

### An escalator out is a day the station was short of a way up

Reverses "the escalator is out of the grade" under One bar per kind above. The
case against it was Connolly: an escalator listed on 17 and 18 August, two
**red** cells on the second strip - it is a fault notice, not works - and a
green **A / 100% available** chip on the row above them. The grade
contradicted the bar underneath it, and no reader was going to resolve that in
the site's favour.

**Reversed 2026-09-03.** See "The grade is lift availability" at the end of
this file. The body below stands: its account of what the grade can and cannot
claim is still what the new section leans on.

**The grade is not step-free-access availability, and this note is the place
that says so.** Wheelchair users cannot use an escalator - every operator
prohibits it, Irish Rail included, and it is a matter of the step geometry
rather than a formality. ("Flat escalators" are moving walkways, a different
machine that can be usable where it is designed to be; the feed says
"Escalator" and nothing else, and there is no evidence of a travelator at any
station in this corpus.) So an escalator going out never removes step-free
access. It removes the easier route for someone who can manage stairs with
difficulty, or has a buggy or a suitcase.

What the grade means is therefore weaker and plainer: **Irish Rail reported
something out at this station on this day.** Vertical circulation degraded,
not access lost. The legend says "Lift and escalator availability", which is
the honest label for that, and the reason the footer no longer claims the lift
is the step-free route.

The site could not honestly grade step-free access anyway. A notice names one
machine in prose - "the lift at platform 2" - and there is no roll of how many
lifts a station has, so a lift notice coming down does not mean every lift at
that station works. Reserving the grade for lifts would give it a name it
could not live up to.

Rejected: lifts only, with escalators visible on their own bar but out of the
letter. That is the more precise claim, and it was the position until today;
what killed it is that Connolly then reads A / 100% available directly above
two red escalator cells, and no reader resolves that contradiction in the
site's favour. Rejected: two grades, a step-free one and a softer escalator
one. Most honest of the three, and it costs a second chip on every row plus a
decision about which one sorts the overview - out of proportion to a
distinction the feed cannot support cleanly in the first place.

The bars still split by kind, for the reason they always did: a working lift
must not be painted by a broken escalator. Separate strips, one pool of days.

On this corpus, aggregate availability went 70% to 66%. Connolly A to C, and
Pearse - whose escalator has been listed since 13 August - A to F at 22%. Note
what that F is not saying: Pearse's lift notice came down on 13 August, so as
far as this feed shows, the step-free route there has been fine ever since.
The F is seventeen days of a station short of a way up, which is the measure
the site now publishes.

### Blue said two opposite things

`5` was every planned-works day, excused or not. Midleton (19 days, 0%
available) and Pearse's lift (6 days, costing nothing) drew the same blue, so
the one colour on the bar carried both "this is forgiven" and "this is the
whole reason the grade is F". A reader comparing two blue bars had no way to
see which was which.

Planned works past their grace are now `6`, amber, with their own key entry.
Amber rather than a second red: works that overran are not a fault, and a
deuteranope cannot tell orange from `--critical` at cell width. The day cell
takes the worst of what was listed on it - fault, then overrun works, then
works inside their grace - which is `DAY_SEVERITY`, an explicit ranking now
that three shades can share a day rather than two.

Rejected: recolouring overrun works red outright. It counts like a fault and
it is not one, and the notice text under the bar says "planned works" either
way; two words disagreeing with one colour is how this started.

### The grade key keys the letter, not a colour

The key under the day key was five colour swatches - the chip fills, at swatch
size - and a reader asking what they referred to was right to ask. A grade is
read as a letter; the fill behind it is reinforcement, and nothing else on the
page is painted in it. So the row was a key to a code the page does not use,
sitting directly beneath the day key, where every swatch does map to something
in a bar. It now carries the chips themselves, letter and all, which is the
object a reader has actually been looking at on every row.

### ... and then left the top of the page entirely

Two legend rows stacked above the list read as one key with two halves, and
only the top half maps to anything a reader can see in a bar. Rebuilding the
grade key as chips fixed what it keyed without fixing where it sat: it was
still a second row of swatches in the position that says "this explains the
thing below".

It now sits in the footer, inside `<details>` "How the grade works", directly
under the sentences that define availability and the planned-works grace. The
key and its explanation are one thing, and the top of the page carries the one
legend that belongs there. The static station pages get the same section for
themselves rather than a link to the index's: a station page is where a search
result lands, and its chip has to be explicable without a second page load.

Filled once at boot rather than on every render, unlike the day key: it sits
outside the view that re-renders, and its content never changes.

### Plain words on the summary tiles

"4 lifts with a notice up at the last poll" asks a reader to know what a poll
is and what a notice is; "70% of days available" asks them to work out what
was available. Neither is a term a visitor arrives with. The tiles now read
"lifts reported out when we last checked" and "of days with no lift or
escalator reported out, across the stations named this month" - longer, and
the denominator is still stated, which is the part that could not be dropped.
"Poll" is gone from the visitor-facing text; "listed" stays, because a notice
being listed is exactly what the site measures and "fixed" is the word it must
not use.

Two footer paragraphs went with it. The one about there being no Irish or EU
target was the site explaining its own methodology to someone who had not
asked - the reasoning is above, under The grade is availability, and that is
where it belongs. And "a notice names a lift in prose" was answering a
question in the vocabulary of the person who wrote the parser.

## The bars say which kind - 2026-09-01

Issue #28. Two bars, and nothing on the page saying which was which. The
`aria-label` said it, the day-cell caption said it on hover, and neither is
visible on a phone at rest. A lone bar was no better off: a station with only a
lift bar did not say it was a lift bar either, so this was never only about the
pairs.

Every bar now sits in a `.bars` wrapper whose first column is a fixed 15px, and
that column carries a glyph: MDI `elevator` for the lift, MDI `escalator` for
the escalator. On the station page, where the bars are tall, the glyph keeps its
word beside it in a 78px column.

**This supersedes the label rejection under One bar per kind.** A 64px text
column was tried on 2026-08-28 and reverted because it appeared on the one
station that had two bars and shortened that station's bar, putting its day 14
over every other row's day 15. The column being present on *every* row is the
whole fix: measured across the August overview, all 15 rows start their days at
the same x at 980px and at 500px, paired and unpaired alike. Nothing about the
earlier attempt was wrong except that it was conditional.

A lone tall bar is 40px and a pair is 18 + 3 + 18, so `.bars.pair` and not
`.bars` carries the height override: wrapping every bar without that would have
halved the height of every unpaired bar on every station page.

### Merging the two bars again was the other option, and it is still the bug

Reducing the overview to one bar and splitting only on the drill-down was
considered and rejected for the reason the bars split in the first place: at
Pearse on 13 August the lift came back and the escalator did not, and a merged
cell paints a working lift as broken. Which is also what the glyph would have
had nothing to point at.

### The glyph is aria-hidden

The strip's `aria-label` already opens "Lifts in August 2026: ...". An
`aria-label` on the glyph beside it would make a screen reader say the kind
twice for one bar. The glyph carries a `title` on the overview, for a mouse; a
screen reader gets the kind from the sentence that was already there.

`elevator` over `elevator-passenger`: three shapes rather than five, and at 15px
the detail is gone and only the silhouette is left, where a box against the
escalator's diagonal is the largest difference available.

### Shape is a second key, not an extension of the colour key

The day key says what was listed and says nothing about which kind, deliberately
- there is a test holding it to that. So the kinds are their own key beside it:
two questions, two keys. `LEGEND_SPANS` stays kind-free and `LEGEND_HTML`
composes the two, which is also what ships in `data.js`, so the app's legend
still cannot drift from the static pages'.

Each key is a `role="group"` with a name, because the first attempt divided them
with a 1px rule and nothing else. That divides them for an eye only: a screen
reader heard one run of seven items and was told the kinds were day-cell
colours, which is the confusion the split exists to prevent. The rule is gone
too, and not only because the names replace it. The two keys stop sharing a line
at **885px** - a common laptop width, and far above any breakpoint this site
has - so a rule between them hangs off the end of the first key more often than
it sits between them. Twenty-eight pixels, twice the gap between items in a key,
says the same thing at every width. It is scoped with `:has(.keys)` so the grade
key in the footer keeps its own spacing, and so a browser without `:has` falls
back to the plain gap rather than to a margin that indents the second key.

The glyphs are CSS masks rather than markup. The path data then lives once, in
the stylesheet both renderers already inline, and `render._bars` and site.html's
`bars()` only ever emit a class name - two mirrored functions with one less
thing to drift on. Cost is about 730 bytes on an initial load of 67 KB.
Licensing is in the README: MDI is Apache 2.0, as is this repo.

## A notice that came back was published as never having left - 2026-09-02

Midleton read oddly: a planned-works block running from the day collection
began to the end of August, then gone. That one turned out to be real, and the
page already said so. Chasing it found a different notice broken.

Portlaoise was published as **16 days listed, F, 29% available**. The lift was
listed for 20 hours from 10 August, absent from **672 consecutive successful
polls** over the next fortnight, then listed again for 22 hours from 25 August.
Two short outages a fortnight apart, published as one continuous sixteen-day
one. It grades **D, 83%** now. Thurles was 17 days and F; it was two hours in
August, eight days of nothing, then nine days, and grades E. Clondalkin
Fonthill, the Dublin Pearse escalator and Athy had the same shape, smaller.

### The gap fell out between the collector and the site

`identity_key` is `UNIQUE` on `messages`, which is what makes a notice the same
notice across polls. So when one comes back, `diff_and_update_messages` had
nowhere to put the second appearance but the row already there: it cleared
`closed_at_utc`, bumped `reopen_count` and left `first_seen_at_utc` alone. The
site then read one row as one listing, `first_seen` to `closed_at`, and the
absence in the middle vanished.

`reopen_count` recorded that this had happened - six times in the first month,
five of them lift or escalator notices - but nothing downstream read it, and no
test covered it. The one test that looked like it did,
`test_a_notice_that_comes_back_a_poll_later_is_a_separate_outage`, gives the
returning notice a corrected start, which changes the identity key and so makes
a genuinely new row. The same-identity return, which is the common case, was
never exercised.

This was never a raw-log problem. Every gap is in the JSONL exactly as
collected, which is the whole point of the invariant: the fix is a `rebuild`,
not a correction anyone has to write down.

### One row per stretch, not one per notice

A `listings` table now holds one row per stretch a notice was continuously on
the feed: `opened_at_utc`, `last_seen_at_utc`, `closed_at_utc`. A reopen opens
a new row instead of reviving the old one, and the site builds one outage per
row. `messages` keeps its own `first_seen`/`closed_at`, which still answer "when
did we first ever see this notice" - a different question, and not the one the
bars ask.

Rejected: **deriving the gaps in the site** by walking runs against
`last_seen_at_utc`. It would have kept the schema still, but it puts the
collector's knowledge in the renderer and needs a scan of every run per notice.
The collector is the thing that watches the feed; when a notice stopped being
on it is the collector's fact to record.

Also rejected: **dropping `UNIQUE` and inserting a fresh `messages` row each
time**. The identity key is what makes reissue detection work in the first
place, and a row per appearance would have duplicated the notice's text and
start across every stretch for no gain.

### One missed poll is the feed blinking - grace goes to 2

Splitting the listing made a flaw visible that the reopen had been hiding.
Athy's lift has been listed continuously since collection began, but it was
absent from exactly one poll on 21 August and back 29 minutes later. With
`LIFT_STATUS_GRACE_MISSES` at `1`, that closed and reopened the notice, and
the site published two outages: one "no longer listed 21 Aug", another
starting half an hour later. That reads as fixed, then broken again, which is
the one claim this site must never make.

The default is `2` now. The gaps in the corpus sort into 1, 9, 79, 388 and 672
polls, so the cut has nothing near it on either side, and the second miss only
confirms the close: `closed_at_utc` is still `missing_since`, the first poll
the notice was absent from. The cost is that an outage ending is recognised a
poll late, which a 30-minute cadence cannot resolve anyway, and that a
same-poll reissue takes one more poll to merge. Both self-correct at the next
poll and neither survives a `rebuild`.

Rejected: **setting it in the env** on the Pi and in the workflows. `rebuild`
replays under whatever value is set when it runs, so the published history and
the collector would have had to be kept in step by hand, in three places, with
nothing to catch them drifting.

### The Pi keeps its database across an upgrade

`install-native.sh` copies files over a running collector and does not
rebuild, so a Pi that upgrades has `messages` rows and, because
`CREATE TABLE IF NOT EXISTS` makes it empty, no `listings` at all. Nothing
published would notice - CI rebuilds from the raw logs on every deploy - but
the collector's own database would hold open notices that no longer reach
the site at all, having no span to be read through.

So a notice with no open span gets one, back-dated to the `first_seen` its row
already carries. That is the best the database can say without a replay, it
needs nothing from whoever runs the upgrade, and it is a no-op once every row
has a span.

Both paths need it, which the first cut got wrong: it back-dated only when a
notice was seen again, so one that went away and never came back was closed
with no span and vanished from the site rather than being briefly wrong. A
span is ensured wherever the collector is about to extend or close one.

### The grace is earned per notice and spent per stretch

Splitting the listing split the planned-works grace with it, and that was wrong
in the other direction. The Dublin Pearse escalator dropped off the feed for
four hours on 26 August after thirteen days up. As two outages it read as
thirteen days plus a fresh four-day stretch, and the four days fell inside the
week's grace and stopped counting: 20% available became 41%, on a notice
nothing had changed about.

So `Outage` carries `planned_total`, the notice's planned listed time pooled
over all its stretches before they separate, and `day_marks` spends the grace
against that. A gap now splits what is measured without refreshing what is
excused. Pearse is back to 20%, which is the number it should have had all
along, and works that blink off the feed for an afternoon cannot farm a new
grace week by doing it. This is the same reasoning `merge_edits` already rests
on - works reissued every few days are still works that ran for a month - so
the two now say it the same way.

## The grade is lift availability, and an escalator notice stops knocking - 2026-09-03

The corpus is 26 days (8 August to 3 September 2026, 1,216 runs, horizon
05:00Z on the 3rd), 32 outages across 25 stations, of which four are escalator
notices at three stations: Pearse twice, Connolly, and Tara Street since 2
September. All three stations claim a lift on their irishrail.ie page.

Issue #32. This reverses "An escalator out is a day the station was short of a
way up" above and reinstates the rule under "One bar per kind": the grade is
the lift bar's alone.

### The chip and the sentence disagreed

Pearse's page for August carried an F on the chip and, on the escalator outage
under it, "an escalator is moving stairs, so it was not a step-free route to
begin with and its being out did not remove one". Both true. The explainer
said "no lift and no escalator" and was accurate too. But the chip is what a
reader takes in, and one letter was answering two questions for two
populations: a wheelchair user read Pearse's F as a bad month for them, when
their lift was out for five days inside the works grace and the F was the
escalator's alone.

### One condition, and a name

`station_month` collects `against` from lift days only. The escalator keeps
its strip, its colours and its count on the tiles; it just paints nothing on
the letter. `national_month` goes through `station_month`, so the headline
follows.

The key reads "Lift availability", not "step-free availability", which the
issue proposed. The grade counts notices, not access: a lift out at Raheny or
Cork still knocks it though Irish Rail's page names a ramp round that lift, and
the six of 24 verdicts that come back `unknown` knock it too, because the safe
direction is to count them. A name that promised step-free would be claiming
what `lift_access` is at pains not to.

### Why the 2026-08-29 objection no longer holds

What killed lifts-only the first time was Connolly reading A / 100% directly
above two red cells, with nothing on the row saying the red cells were an
escalator's. Since "The bars say which kind" (2026-09-01) every bar carries its
glyph in a gutter the same width on every row, the kinds are their own legend
key, and the grade key beside the chip says what is graded. Red escalator cells
under a green lift chip now read as two facts about two machines rather than
one contradiction.

The overview sort is unchanged: a station with any notice up leads, then the
least available. Tara Street sits at the top today with an A beside its red
escalator strip, which is the correct shape for a station whose lift is fine
and whose escalator is out.

### The denominator is still the stations named

The headline averages over the stations the feed named that month, whatever
kind of notice named them, so a station with only an escalator notice is in it
at 100% lift-available. Review asked whether that pads the number. It moves it:
narrowing to stations with a lift notice gives 75% instead of 76% for August
(20 stations, Connolly out) and 53% instead of 61% for September so far (5
stations, Tara Street out). Kept as is, because the tile says "across the
stations named this month" and the overview lists exactly those stations, so
the headline is the sum of the rows a reader can see; a station shown on the
list at 100% and missing from the number above it would be the page
disagreeing with itself. The denominator that was refused on 2026-08-28 was
"every station on the network", which the feed never names. A station it did
name is not invented.

### The numbers

| month | station | shipped | lifts only |
|---|---|---|---|
| August 2026 | Dublin Connolly | C, 91% | A, 100% |
| August 2026 | Dublin Pearse | F, 20% | A, 100% |
| August 2026 | national, 21 stations | 72% | 76% |
| September so far | Tara Street | F, 33% | A, 100% |
| September so far | national, 6 stations | 50% | 61% |

The issue's own table read 21%, 67% and 70%; it was measured before the
listings split of 2026-09-02, which moved Portlaoise, Thurles and Clondalkin.

### Rejected

- **A fractional weight for escalators.** Nothing to calibrate it against, and
  the bands exist so a reader can reconstruct the number by counting days on
  the bar. A coefficient makes the letter a number nobody can check.
- **Two grades.** The most accurate, and it costs a second chip on every row
  and a decision about which one sorts the overview, for a distinction the feed
  has shown at three stations.
- **Wording only.** The wording was already accurate and fixed nothing, because
  the chip is what is read.
- **A grade driven by the access verdict**, knocking only where `verdict` says
  `lost`. The site builds with no station snapshot at all, six of 24 verdicts
  are `unknown`, and the number would then move on a monthly scrape of prose
  rather than on the feed.

### The case that should knock: the only powered way up

An escalator notice counts against a station's availability only where the
escalator is the only powered way up, which on this network is a station whose
Irish Rail page does not claim a lift. Stairs only is a real loss for the
people an escalator serves: anyone who can manage a flight with difficulty, or
has a buggy, a suitcase or a stick. No station in the corpus is of that shape;
Pearse, Connolly and Tara Street all claim a lift. So the rule is written here
and not coded. `tests/test_site_real.py`, which CI runs against the checked-out
corpus and snapshot, fails the day an escalator notice appears at a station
whose page claims no lift, and that failure is the signal
to build the rule in `station_month`, which will then need the station facts
the site is built to run without. It is not a signal to loosen the test.

Issue #33, saying who an escalator outage did affect, stays open, and it is
what makes dropping escalators from the letter honest rather than a dodge: the
group an escalator serves is off the grade and, for now, off the page.

**Settled 2026-09-03.** #33 landed the same day: every escalator verdict now
says who lost a way up and what Irish Rail's page puts on the same leg, and a
lift notice that names the way in is read against `ticketOfficeAccess`.
`notes/station-access.md` § *The entrance leg, and who an escalator served*.
The only-powered-way-up rule above is unchanged and still guarded.

## What a reader can take away - 2026-09-05

Three additions for the visitor and two checks for the build, chosen from a
survey of what the site could not do. The corpus was 36 outages over 28
stations; the initial load went from 64.8 KB to 65.8 KB.

### The row says which kind is out now

The tiles counted "2 lifts reported out when we last checked" and the rows
sorted ongoing-first, but nothing on a row said so, and a reader had to hover
the last cell to find the station that was out. The stats row's fourth field
was a bool that only ever fed the sort; it is now a mask of the kinds listed at
the horizon (`NOW_KIND`, lift 1 and escalator 2), the sort treats any nonzero
the same as before, and both renderers print "Lift out", "Escalator out" or
"Lift and escalator out" beside the name from it. The wording repeats the
notice and the title says when it was true; "out" rather than "fixed" or
"working" for the same reason the cases say "no longer listed". In the
overview's 170px name column the tag drops under the name rather than
truncating it.

Rejected: a tag per planned-works notice in blue. The mask does not carry
the works flag, and the tag's job is to say a notice is up, which the case
below it then qualifies.

### Atom feeds, one national and one per station

"Tell me when this station's lift goes out" had no answer but reloading. The
build now writes `feed.xml`, capped at the 50 most recent, and `s/<slug>.xml`
beside each station page, uncapped because a station's list stays short. An
entry's id is the case anchor on the station page, so it is a real address and
survives a rebuild; its `updated` is the appearance while the notice is up and
the close once it is down, and the title gains "(no longer listed)", so a feed
reader shows an outage twice and the second showing is the only completion
signal a reader will ever get. The feed's own `updated` is the horizon rather
than the build clock: a rebuild that saw no new data has no news. Publishing
lands within about six hours of a notice, which is what a feed can promise.

Rejected: a second webhook from the Pi for new lift notices. The feed does the
same job for anyone, through any RSS-to-push bridge, and keeps the collector's
alert channel for failures only.

### Every outage as CSV

The README's stated purpose is history to look for patterns in, and the only
data on the site was `data.js`, shaped for the app. `outages.csv` has one row
per outage the site shows, the listing instants in UTC for arithmetic, Irish
Rail's own start and end as written (Dublin wall-clock, no offset) because they
are a quotation, and `end_utc` blank while a notice is still listed so nobody
averages the horizon in as a close.

### The access card links its source

The card quoted Irish Rail's prose and asked the reader to say what it got
wrong, and never linked the page it was read from. It does now, from the
station's own slug in the snapshot. Static page only: the app's caveat quotes
no prose, and the slugs would cost bytes in `data.js` for a link that lives one
click away.

### The build warns about what the page cannot show

`classify` reads the head, and the head is Irish Rail's wording. A reworded
head would drop its notices from the site with nothing failing, and the cells
they should have coloured would read as nothing listed. `unclassified_mentions`
finds any message whose head or text mentions a lift, elevator or escalator
that `classify` rejects; the build prints them and the real-corpus test fails on
them. The check is wider than the classifier on purpose, and a hit is a notice
to read rather than a test to loosen. On the corpus to date it finds nothing,
and one head already varies ("Portarlington- Lift out of order").

`thin_days` names any Dublin day the collector reached the feed fewer than 40
times out of 48. Three gaps of about an hour exist so far and each is
invisible: a day with two polls paints like a day with 48. Painting it on the
bars was rejected for now as UI complexity out of proportion to three hours.

### Not built

Duration and repeat statistics (median listing, longest current, stations with
a second outage). With four weeks of data any "typical outage lasts" figure is
noise. Worth a tile once the corpus earns it.
