# Scope: does this station have another accessible route? - 2026-08-29

**Answered on 2026-08-30. Everything below is kept for the reasoning; the
answers and what was built are in [`station-access.md`](station-access.md).**

All three phase-0 checks were run from a machine with real network egress, plus
the two sources this note did not know about. In short:

- **GTFS carries nothing.** No `pathways.txt`, and `wheelchair_boarding` is not
  merely unpopulated - the column does not exist. Both closed permanently.
- **The NTA developer API is bus-only** and the wrong shape besides. An account
  buys nothing here. Closed.
- **Irish Rail's own station pages carry a per-platform access description**,
  keyed by the exact `locationCodes` code space, served as JSON. That is the
  source, and it is what phases 1 to 3 were built on.
- **The routes question has a near-constant answer: no.** Of 61 stations whose
  prose mentions a lift, two name a step-free way round one. No route engine was
  needed or built.

Struck sources are marked below. Do not scope them again. The one source worth
checking again is **NeTEx**, the European standard for station equipment and
accessibility, with **SIRI-FM** for live lift status. Ireland publishes neither
today. See `station-access.md` for why that is lawful rather than an oversight,
and for the GTFS fields Google and Apple read that are also absent.

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

**Checked on 2026-08-30. There is no `pathways.txt`, and no `levels.txt`.**
`GTFS_Irish_Rail.zip`, `GTFS_All.zip` and `GTFS_Realtime.zip` each hold exactly
ten files: `feed_info`, `agency`, `stops`, `calendar`, `calendar_dates`,
`routes`, `trips`, `shapes`, `stop_times`, `translations`. Closed permanently.

### B. GTFS `stops.txt` `wheelchair_boarding` - the likely realistic source

Standard GTFS, near-certain to be present, values fixed by the spec:

- `0` or empty - no accessibility information
- `1` - some vehicles or paths at this stop are accessible
- `2` - not accessible

**Checked on 2026-08-30. The column does not exist.** The `stops.txt` header is
identical in all three feeds and ends at `parent_station`:
`stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station`.
`location_type` is empty for all 152 rail stops too, so there is not even a
station/platform hierarchy. GTFS gives an inventory and nothing else. Closed.

The same is true of the rest of the NTA catalogue: `NaPTAN.json` has 152 rail
stops keyed by station code with `AccessArea` null on every one and the string
"accessib" absent from the whole 22 MB file, and `ptims.zip` is bus street
furniture.

`stops.txt` also carries `stop_id`, `stop_name`, `stop_lat`, `stop_lon` and
`parent_station`, which is the station inventory of question 1 on its own.

### C. `api.irishrail.ie/.../getAllStationsXML` - the join, no accessibility

**Checked on 2026-08-30. Still up, still unkeyed**, 171 stations with
`StationCode`. It was right about the code space. Superseded, though: the
station pages carry the same codes *and* the accessibility prose, so this was
not needed.

No accessibility data at all. Inventory only.

### D. The lifts-and-escalators alerts page - checked, useless

`https://www.irishrail.ie/en-ie/travel-information/accessibility-onboard-trains/lifts-and-escalators-reports`,
titled "Alerts for Lifts and Escalators". Found while scoping this and it
looked promising: if it were a per-machine inventory with status it would have
been a better primary source than the message feed, and would have answered
"how many lifts does this station have".

**Checked on 2026-08-29. It is not.** Ruled out; do not spend time on it again.

### E. Station pages, scraped

**This turned out to be the source, and it is not scraping.** Each station page
is server-rendered Nuxt and serves its data as JSON at `<page>/_payload.json`:
named fields, no `html.parser`. `platformAccess` describes access per platform,
`stationCode` gives the join for free, and the find-a-station payload lists all
152 slugs so nothing is crawled. `robots.txt` disallows only `/stations.csv`.
See [`station-access.md`](station-access.md).

## The join

**There is no join to make.** Source E carries `stationCode` itself, in exactly
the `locationCodes` code space. All 15 codes with lift notices matched, 15/15,
with no fuzzy matching and no committed mapping. The worry below was real and
the problem simply does not arise.

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

## Phasing, smallest first - all three done

**Phase 0 - verification.** Done, 2026-08-30. See the answers at the top.

**Phase 1 - the inventory.** Done. 152 stations with codes, snapshotted to
`lifts-data/stations/`. The site has a denominator.

**Phase 2 - the accessibility flag.** Done, from a better source than the one
scoped: `platformAccess` rather than `wheelchair_boarding`, which does not
exist. Per station: has a lift, has none, or unknown.

**Phase 3 - routes.** Answered rather than built, and the answer is that no
graph is needed. See [`station-access.md`](station-access.md) - "and" in this
prose is a sequence, not a choice, so a lift out nearly always removes step-free
access, and only two stations in the country say otherwise.

## What is deliberately out

Hand-curating station accessibility by hand from photographs, station visits
or Wikipedia. It would be a second source with no provenance, no refresh and
no way to audit, attached to a site whose entire discipline is that every
number traces back to a recorded observation. Better to say nothing.
