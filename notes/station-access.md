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

## OpenStreetMap, and why it only ever suppresses

OSM genuinely micro-maps Irish stations - named platform ways, `highway=elevator`
nodes with `level` tags, escalators as `highway=steps` + `conveying`. It is the
routable graph GTFS `pathways.txt` would have been. But it covers about two
thirds of the lift stations, and the two sources disagree on 39 of the 74
stations one of them credits with a lift.

So OSM never makes a claim here. It can only turn a "no lift at this station"
into "unknown", where it maps a lift the prose is silent about. Its silence says
nothing, because it is incomplete; Irish Rail's claim stands over it.

Overpass rate-limited and 500ed across three endpoints while this was written;
`api.openstreetmap.org/api/0.6/map.json` served every box. It still answers a
150-box burst with 429s and 509s, so the fetch retries with a widening wait and
**refuses to write a partial digest**. A station missing from the cross-check
makes the site more confident about that station, not less, which is the one
direction of error worth engineering against. A truncated cross-check is worse
than none, because it looks like one.

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
