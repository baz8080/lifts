# What a station has, and what an outage means - 2026-08-30

The site could count lift outages but had no idea what a station *was*. A
station with no lift and no notice read exactly like a station whose lift was
working, and the national figure had no denominator: "66% across the stations
listed" says nothing until you know how many stations there are. Issue #24.

This note records what the sources turned out to be, and the one reading
mistake that nearly shipped.

## "and" is a sequence, not a choice

Irish Rail's station pages carry a `platformAccess` field. It is prose, written
by hand, and its **"and" lists a route you traverse, not alternatives you pick
between**.

> Hazelhatch and Celbridge: "All platforms can be accessed via lifts and ramps"

You need both. The ramp gets you along; the lift does the level change. There
is no way to most platforms there without the lift. This session first read
that sentence as a disjunction and concluded a lift outage at Hazelhatch left
access intact - the exact opposite of the truth, and in the one direction that
strands a reader on a platform. Barry, who knows the station, caught it.

Checked across all 61 stations whose prose mentions a lift, the conjunctive
reading holds everywhere:

- **"and" as a sequence: 29 stations.** "Lift and footbridge to platform 2"
  (Malahide, Skerries, Portlaoise, Maynooth, Monasterevin, Portarlington,
  Templemore, Tullamore, Balbriggan, Laytown) is lift up, cross, lift down.
  Same for "Lifts and footbridge to all platforms" (Ballybrophy, Clontarf Road,
  Gort) and "Platforms accessible via stairs and lifts" (Clondalkin, Grand
  Canal Dock, Kishoge).
- **"or" is a real disjunction, but it is nearly always "or stairs": 11
  stations.** Adamstown, Bayside, Clonsilla, Glenageary, Howth Junction,
  Shankill, Blackrock, Booterstown, Bray, Tara Street. Stairs are not a
  step-free alternative, so the lift is still the only way.
- **Two stations, of 61, name a step-free way round a lift for the same
  platform.** Raheny, "Lift or ramp to platform 1", and Cork, "Ramp or lift to
  platform 5A, 5B and 6". They are the whole of
  `lift_access.model.STEP_FREE_ALTERNATIVES`.

So the question issue #24 set out to answer - *when a lift is out, is there
another accessible way in?* - has a near-constant answer on this network:
**no**. That is worth publishing, and it means no route engine is needed. The
model works out which platforms a lift serves, assumes an outage removes
step-free access to them, and carves out the two exceptions by hand.

`lift_access/model.py` deliberately does not parse connectives at all. Adding an
entry to the exception list is a human decision in a diff, never a parser
output, and `tests/test_site_real.py` fails if any published verdict claims an
alternative that is not in it.

## The chip

The two exceptions get a small green pill, "Step-free route", on the overview
row, the app's station detail and the static station page, and the card that
quotes the prose says which line earned it. It deliberately does not say
"accessible station" and does not use the international access symbol: both
would read as a far bigger claim than the reviewed list makes, which is only
that Irish Rail's page names a step-free way to a platform there that does not
use the lift.

Neither Raheny nor Cork has ever had a notice in the corpus, so the chip has
never rendered on the live site. `tests/test_site_render.py` is the only thing
exercising it, which is why it is tested rather than left to be discovered.

## The safe direction

A reader told access is gone when it was not has made one wasted check. A reader
told access remains when it is gone is stranded. Every rule here leans the same
way: default to "gone", say "unknown" freely, and never infer "remains".

## The lift-call sentence is boilerplate

> "To access the lift, you must call via the help point at each landing of the
> lift shaft. Please see lift call operation page for steps to call the lift."

Pasted template text at dozens of stations. At **three** it is the only mention
of a lift - Greystones, Killiney, Donabate - so matching on the word "lift"
invents lifts nobody claimed. It is stripped before anything else. This is also
what dissolves the Greystones contradiction: "Footbridge **only** to platform 2"
is the real claim and the lift sentence is template.

Dromod carries the one explicit negative: "(no lift at this station)".

## Escalators are not step-free

An escalator is moving stairs. An escalator outage never removes step-free
access; it removes a convenience. Only 2 of 147 stations mention an escalator in
`platformAccess` at all.

This sits awkwardly beside `site.md` § *An escalator out is a day the station
was short of a way up*, which counts escalator outages in the grade at the same
weight as lift outages. **Not settled here.** The station page now says an
escalator outage did not remove step-free access while the grade still marks the
day down, and those two should be reconciled. Left as its own decision rather
than folded into this change.

## The other platform is often still step-free, and the prose says so

Not yet built. Recorded because it is the largest unclaimed win here and it is
bigger than the exception list by an order of magnitude.

A lift out does not strand a station, it strands a *platform*. The other
platform is frequently at street or car park level and needs no lift at all,
and Irish Rail's prose says which one in plain words:

| station | lift serves | still step-free |
|---|---|---|
| Athy | platform 2 | "Level to platform 1" |
| Malahide | platform 2 | "Level to platform 1 (City Centre)" |
| Portlaoise | platform 1 | "Level to platform 2" |
| Skerries | platform 2 | "Level to platform 1" |
| Dublin Pearse | platform 2 | "Ramp to platform 1 (City Centre and northbound)" |
| Dublin Connolly | platforms 6, 7 | "Level access to platforms 1, 2, 3 and 4 from ticket office" |

**32 of the 57 stations that claim a lift name at least one platform reached
without one, and 12 of the 21 that have had a notice do.**

This is a different claim from `STEP_FREE_ALTERNATIVES`, and the wording has to
keep them apart. The exception list says *"you can still reach this platform
another way"*. This says *"you cannot reach that platform, but this one is
still fine"*. The second is weaker and is about a different train.

It is also safe to derive, unlike the connectives: "Level to platform 1" is a
direct statement, not an inference. The model already knows which platforms the
lift serves, so the complement falls out.

### What it cannot derive, and where a person would help

The passenger-facing form of this is directional. "Platform 1 is still level"
means nothing to somebody who does not know the layout; "you can still travel
towards the city, but not away from it" is the sentence worth printing.

**Only 10 of 57 stations name a direction in the prose**, and 2 of the 12
notice stations above (Pearse, Malahide). For the other 10 the platform-to-
direction mapping is not in any source checked - not GTFS, which has no
platform data for Irish Rail at all, and not OSM, which has no `level` tags
outside the Dublin termini.

That mapping is stable, small (roughly 120 platforms across 57 stations), and
exactly the kind of thing a person who uses these stations can verify. It is
also the failure mode `accessible-routes.md` warns against: a hand-maintained
file with no provenance and no refresh.

The way to have both is the discipline `STEP_FREE_ALTERNATIVES` already sets:
an in-repo constant, one entry per platform, **each recording how it was
verified** - the prose sentence where there is one, and otherwise a named source
(a station visit, a photograph, a timetable that only lists one direction from
that platform). An entry with no verification field does not go in. That keeps
it auditable in the way a `stations.json` somebody edited once in 2026 is not.

Worth doing only if somebody will actually label them. Ten stations of it are
free from the prose today.

## When it says "unknown"

Both sources are hand-written and they disagree. On the corpus as of
2026-08-30, six of 24 notices come back unknown, and every one is a real
discrepancy worth not papering over:

| station | why |
|---|---|
| Limerick Junction | `platformAccess` is the single word "Level", yet it has lift notices, and OSM maps two lifts |
| Greystones (x2) | prose names no lift outside the boilerplate |
| Rush and Lusk | prose says "Level access to platform 1 / Lift and footbridge to platform 1" - platform 1 twice, plainly a typo; the notice names platform 2 |
| Portlaoise | prose puts the lift at platform 1; the notice says platform 2 |
| Carlow | prose puts the lift at platform 2; the notice says platform 1 |

A notice naming more platforms than the page accounts for keeps what it knows
rather than forfeiting everything: Athy's notice names 1 and 2, the page has a
lift at 2 and calls 1 level, and platform 2 is still knowable.

## The sources, and the ones that are closed

The three checks `accessible-routes.md` scoped are answered. They are struck
there, not here.

**What is used:** `https://www.irishrail.ie/en-ie/station/<slug>/_payload.json`.
Server-rendered Nuxt, named fields, no HTML parsing. `robots.txt` disallows only
`/stations.csv`. The find-a-station payload carries `kontentStations`, the full
list of 152 slugs, so nothing is crawled.

**The join is free.** Each payload carries `stationCode`, and it is exactly the
`locationCodes` code space the message feed uses. All 15 codes with lift
notices matched, 15/15. The name-to-code mapping the scope worried about is not
needed.

**The site already held half of this.** `messages.text_raw` names the platform -
"The lift at platform 2", "The lifts at platform 1 and 4" - and nothing parsed
it. `head` says only "Dublin Pearse - Lift out of order".

**Two fields that look useful and are not:**

- `alert` / `alertStart` / `alertEnd`. 131 stations carry one and they are never
  cleared: `alertEnd` values run back to 2014, 2015 and 2021. It is the last
  alert ever posted, not a live one.
- `wheelchairAvailability` means "a wheelchair can be borrowed here", not "this
  station is accessible". Pearse says Yes, Docklands says No. Never surface it
  as accessibility.

## OpenStreetMap: what it can do, what it cannot, and why it is still here

Recorded properly because the honest answer to "what is it for" is currently
"nothing", and the next person to look at this should not have to re-measure.

### What it can do

- It is the only machine-readable station graph that exists for this network.
  Around Pearse: named `Platform 1` and `Platform 2` ways, four
  `highway=elevator` nodes carrying `level` tags, three escalators as
  `highway=steps` + `conveying`, `highway=corridor`, `wheelchair` tags. That is
  a routable topology, the thing GTFS `pathways.txt` would have been.
- It independently spots 13 stations where Irish Rail's prose mentions no lift
  and OSM maps one, including Limerick Junction, whose page is the single word
  "Level" while it has lift notices on record.
- It is a second opinion on prose that is hand-written and demonstrably stale in
  places.

### What it cannot do

Three measurements, all against the real data:

**1. It cannot change a verdict. Zero, measured.** `has_lift()` is consulted in
exactly one place, `model.verdict`, as `!= "yes"`. OSM can only move a station
from `no` to `unknown`, and both are `!= "yes"`. Checked with a synthetic digest
mapping a lift at all 152 stations: `24 outages, 0 verdicts changed`.

**2. Its one genuinely useful signal is redundant.** The 13 stations where the
prose is silent and OSM maps a lift look like a real catch, but a station in
that set that has a notice already returns `unknown` without OSM, because
`claims_lift` is false. Limerick Junction is the worked example: same verdict,
same wording, with or without the digest. The signal only bites at stations with
*no* notice, and those never appear on the site.

**3. It cannot answer the street-side question**, which is the one thing that
would have earned its keep. "Which platform is reachable from the car park or
the street without a lift" needs `level` tags on platforms and entrances.
Sampled across 12 stations that have had notices:

| | stations |
|---|---|
| platforms mapped | 12 of 12 |
| platforms carrying a `level` tag | **2 of 12** (Pearse, Connolly) |
| lifts carrying a `level` tag | 3 of 12 |

The micro-mapping is a Dublin-termini phenomenon. Everywhere else OSM has the
platform geometry and none of the vertical information, so the graph is not
traversable and the question is unanswerable. Irish Rail's prose answers it at
32 of 57 stations, in words.

### So why is it still here

On the merits it should probably go: about 60 lines, a monthly HTTP budget, and
the one place the raw-artefact invariant is bent, in exchange for nothing that
reaches a reader. It is kept for one reason only, and it is a weak one: the
moment the site says **"this station has no lift"** out loud - a full station
list, a network accessibility figure - those 13 stations become a wrong claim
rather than a silent one, and this is what prevents it.

If that never gets built, delete it. See issue #29, which carries the same
numbers and the fill-it / use-it / drop-it options.

## The snapshot, and where it bends the invariant

`lifts-data/stations/irishrail-<date>.jsonl` holds every payload **verbatim**,
one per line, `sort_keys=True`, the shape `store.write_raw` uses. 7.8 MB plain,
which git stores at about 2 MB and which greps and diffs. Never edited; the
derivation is always recomputed from it.

`lifts-data/stations/osm-<date>.jsonl` is **a derived digest, not a verbatim
snapshot** - counts per station, with the bbox and the ODbL attribution. The raw
map extracts total roughly 450 MB across the network (Pearse's box alone is
3 MB) and cannot go in a repository. This is the one place the raw-artefact rule
is bent, and it is bent for the only source that can never make a claim on its
own.

Refreshed monthly by `.github/workflows/stations.yml`, which opens a PR rather
than pushing: a reworded station page can move a verdict from "no step-free
access" to "unknown" and back, and that is not a change to land unread. Never on
the Pi, never in the 30-minute poll loop.

## Reading the report

`python -m lift_access --data-dir <dir> report` prints every notice's verdict
beside the prose it came from, and `--all` prints every station that claims a
lift. It is the only real check on a derivation built out of somebody's
hand-written sentences, and it is how the Hazelhatch reading was caught. Read it
when a refresh changes anything.
