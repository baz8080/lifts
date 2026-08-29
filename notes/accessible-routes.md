# Scope: does this station have another accessible route? - 2026-08-29

**This is a scope, not a decision.** Nothing here is settled and nothing has
been built. It exists because the grade now counts escalator outages, and the
reasoning for that (see `site.md` § An escalator out is a day the station was
short of a way up) rests on a gap: the site has no idea what a station has.

## The three questions that keep getting conflated

They need separating before any of this is worth doing, because they have
different answers, different sources, and different value.

1. **How many stations have a lift at all?** The denominator problem. The
   national figure says "across the stations named this month" because the feed
   names a station only when something is wrong with it. A real denominator
   turns "66% at the stations listed" into a network figure.
2. **Does this station have step-free access when nothing is listed?** A
   station with no lift and no notice is currently indistinguishable from a
   station whose lift is working. Both read as green cells. The first is worse
   and the site calls it better.
3. **When a lift is out, is there another accessible way in?** The one the
   Pearse question was really asking. Hardest by a distance, and the only one
   that would let the site say an outage did or did not remove access.

Question 1 is cheap and useful. Question 2 is moderate and would fix a real
misreading. Question 3 is a research project and may have no data behind it.

## What the site cannot say today, exactly

- Whether a station has a lift, an escalator, both, or neither.
- How many lifts a station has. Every notice names one machine in prose - "the
  lift at platform 2" - so a notice coming down means *that* notice came down,
  not that the station is served.
- Whether the escalator that is out was beside a lift, beside stairs, or the
  only powered way between levels.
- Whether a street entrance, a ramp, or a second concourse offers a way round.

## Candidate sources

Confidence is marked because **this session could not reach any of them**: the
sandbox's egress proxy returns 403 for `www.irishrail.ie`, `api.irishrail.ie`
and `data.gov.ie` alike. Everything below is from search results and from the
GTFS specification, and every "unverified" line is a browser tab away from
being settled.

### A. GTFS `pathways.txt` - the right shape, probably absent

GTFS-Pathways models a station's *interior* as a graph. `pathway_mode` is
exactly the distinction this question needs:

| mode | meaning |
|---|---|
| 1 | walkway |
| 2 | stairs |
| 3 | moving sidewalk / travelator |
| 4 | escalator |
| 5 | elevator (lift) |
| 6 | fare gate |
| 7 | exit gate |

That is the answer to question 3 in machine-readable form: if a station's
pathway graph carries a mode-5 edge and a mode-4 edge between the same pair of
nodes, the escalator has a lift beside it; if the only other edge is mode 2,
it does not. It also settles the "flat escalator" question in data rather than
in prose - a travelator is mode 3, a different edge from an escalator.

`levels.txt` and the `stair_count`, `max_slope` and `min_width` columns are in
the same extension.

**Unverified, and the single highest-value check:** whether the NTA publishes
`pathways.txt` at all for Irish Rail. Most agencies do not - it is rare
outside large metro operators, and it is optional in the spec. Check this
first, because a yes collapses most of this document and a no closes question
3 more or less permanently.

### B. GTFS `stops.txt` `wheelchair_boarding` - the likely realistic source

Standard GTFS, near-certain to be present, values fixed by the spec:

- `0` or empty - no accessibility information
- `1` - some vehicles or paths at this stop are accessible
- `2` - not accessible

Answers question 2, weakly (it is a flag, not a route), and question 1 by
giving the full station list. **Unverified:** whether the NTA populates it
meaningfully for rail stops or leaves it `0` throughout, which is the common
failure mode and would make it worthless. One `awk` over `stops.txt` settles it.

`stops.txt` also carries `stop_id`, `stop_name`, `stop_lat`, `stop_lon` and
`parent_station`, which is the station inventory of question 1 on its own.

### C. `api.irishrail.ie/.../getAllStationsXML` - the join, no accessibility

Recalled from prior knowledge, **unverified in this session**: an unkeyed
endpoint returning every station with `StationDesc`, `StationCode`,
`StationId`, `StationAlias`, `StationLatitude`, `StationLongitude`. If it is
still up and still unkeyed it is the cheapest possible source for question 1,
and it carries `StationCode` - the same code space `locationCodes` uses, which
removes the name-matching problem below entirely.

No accessibility data at all. Inventory only.

### D. The lifts-and-escalators alerts page - the interesting unknown

`irishrail.ie/en-ie/travel-information/accessibility-onboard-trains/lifts-and-escalators-reports`,
titled "Alerts for Lifts and Escalators". Discovered while scoping this; it is
not the endpoint this project collects.

Two possibilities, and they are far apart:

- It renders the same service messages the collector already has, in which
  case it is worth nothing and should be written off in one line.
- It is a per-machine inventory with status - every lift at every station,
  named, with an up/down state - in which case **it is a better primary source
  than the message feed** and reframes this whole project. It would answer "how
  many lifts does this station have", which is the question underneath most of
  the others.

Search suggested Irish Rail updates station information "weekly", which if it
applies to this page makes it an inventory rather than a realtime feed - but
that phrasing came from a summary, not from the page. **Check this second.**
Ten minutes with devtools open settles which of the two it is.

### E. Station pages, scraped

`irishrail.ie` station pages reportedly carry accessibility detail. Last
resort: HTML scraping with stdlib only (`html.parser`) against a CMS that can
change without notice, ~150 fetches per refresh, and no version history. Only
if A, B and D all fail, and even then it wants a hard look at whether question
2 is worth that fragility.

## The join

Sources B and E key on names ("Dublin Pearse", "Pearse", "Dublin Pearse
(Westland Row)"); this project keys on `locationCodes` and takes display names
from `eventStops[0].sStop`. Any name-based source needs a reviewed
name-to-code mapping, committed and diffable, not a fuzzy match computed at
build time - a silent mismatch would attach one station's accessibility to
another's row, which is worse than saying nothing.

Source C sidesteps this completely by carrying `StationCode` itself. That
alone may be reason to prefer it for question 1 even if GTFS is richer.

## What this must not break

- **Stdlib only.** GTFS is a zip of CSV: `zipfile` and `csv` are both stdlib,
  so A and B cost no dependency. Good. HTML scraping is where this gets
  tempting - resist.
- **Not on the Pi, and not in the 30-minute loop.** The collector runs on a
  Raspberry Pi and does one HTTP call per poll. A GTFS archive is tens of
  megabytes and changes monthly at most. This belongs in CI or in a separate
  manual refresh, never in `poll`.
- **The invariant.** "The raw logs are the source of truth; the database is
  disposable." A second source has to obey the same rule or it becomes an
  un-auditable file somebody edited once in 2026 - snapshot the fetched
  artefact, commit it, derive everything from it, and let `rebuild` replay it.
  A hand-maintained `stations.json` is the failure mode to design against.
- **The 500 KB initial load.** A per-station accessibility flag for ~150
  stations is a rounding error in `data.js`. A pathway graph is not - it would
  belong in the per-station shard, like the outages.
- **Licensing.** NTA/data.gov.ie data is open, but the licence and attribution
  need reading before station data is redistributed inside `data.js`.

## Phasing, smallest first

**Phase 0 - verification, no code.** Answer, in this order: does
`pathways.txt` exist for Irish Rail; what is the alerts page actually serving;
is `wheelchair_boarding` populated; is `getAllStationsXML` still unkeyed. Each
is a browser tab. The answers decide whether phases 2 and 3 exist at all, and
this is the only phase that cannot be done from a Claude Code web session.

**Phase 1 - the inventory.** Station list with codes, from C or from GTFS
`stops.txt`. Snapshot committed to `lifts-data`. The site gains a real
denominator and can finally say "N of 144 stations had a notice this month".
Small, useful on its own, and independent of everything below it.

**Phase 2 - the accessibility flag.** Only if `wheelchair_boarding` turns out
to be populated, or the alerts page turns out to be an inventory. The site
gains the ability to distinguish "no lift here" from "lift working", which is
the misreading most worth fixing: today those are the same green cells.

**Phase 3 - routes.** Only if `pathways.txt` exists. Then, and only then, the
site could say whether a given escalator outage removed a way up or removed a
convenience, and the grade could stop being a single number that means
different things at different stations.

Stop after any phase. Each is worth shipping alone, and phase 3 will probably
never start.

## What is deliberately out

Hand-curating station accessibility by hand from photographs, station visits
or Wikipedia. It would be a second source with no provenance, no refresh and
no way to audit, attached to a site whose entire discipline is that every
number traces back to a recorded observation. Better to say nothing.
