# 06. The data Ireland does not have
*~11 min read · issue #24 and PR #30 · 29 to 30 August 2026*

*Where we are:* the site counts lift outages and grades stations on them (chapters 04 and 05).
This chapter is about the question it could not answer, which is what any of that *means*, and
about the two weeks spent finding out that Ireland does not publish the answer.

## The question that opened this stretch

The site had a hole in it that a reader could not see, and it went like this.

A station with no lift, and therefore no lift notices, renders exactly like a station whose
lift is working perfectly. Both are a row of green cells. One of those stations is worse for a
disabled passenger than the other, and the site was calling it better.

And the national figure had no denominator. "67% available across the stations listed this
month" is a number divided by a set the feed chose, and the feed names a station only when
something is wrong with it. There is no roll of the stations that have a lift at all, so the
percentage floats: it cannot be a network figure, and the page has to say so.

Underneath both is the real question, the one that would let the site say something worth
saying:

> When a lift is out, is there another accessible way in?

Filed as issue #24, and blocking treating the published site as usable. Three questions that
kept getting conflated were separated first, because they have different answers, different
sources and different value: how many stations have a lift at all (the denominator), does this
station have step-free access when nothing is listed, and is there another route when
something is.

The third is the interesting one, and answering it needs a fact this project does not have:
**what does this station have, and which platform does each machine serve?**

## What changed

### Every source, checked

The checks were run from a machine with real network egress on 30 August 2026, and written down
so nobody runs them again.

**GTFS.** The General Transit Feed Specification is what transit apps read. It has an extension
built for exactly this question: `pathways.txt` models a station's interior as a graph, with a
`pathway_mode` column that distinguishes a walkway from stairs from a travelator from an
escalator from a lift. If a station's graph carries a lift edge and an escalator edge between
the same two nodes, the escalator has a lift beside it. If the only other edge is stairs, it
does not. That is the answer in machine-readable form, and it even settles the "flat escalator"
question in data rather than prose, since a travelator is a different mode from an escalator.

There is no `pathways.txt`. Not in `GTFS_Irish_Rail.zip`, not in `GTFS_All.zip`, not in
`GTFS_Realtime.zip`. Each archive holds exactly ten files and none of them is it. There is no
`levels.txt` either.

**GTFS, the simpler field.** Standard `stops.txt` carries `wheelchair_boarding`, a three-valued
column: no information, some vehicles or paths accessible, not accessible. It is not merely
unpopulated here. **The column does not exist.** The header is identical in all three archives
and ends at `parent_station`. `location_type` is empty for all 152 rail stops as well, so there
is not even a station-to-platform hierarchy. GTFS gives an inventory of stops and nothing else.

**NaPTAN.** 152 rail stops keyed by station code, with `AccessArea` null on every one of them.
The string "accessib" does not appear anywhere in the 22 MB file.

**PTIMS.** Bus street furniture.

**The NTA developer API.** Bus only. Its own description names Dublin Bus, Bus Éireann and
Go-Ahead, and the GTFS archive it links to was already ruled out above.

**Irish Rail's own `getAllStationsXML`.** Still up, still unkeyed, 171 stations with a
`StationCode`. It was right about the code space and carries no accessibility data at all.
Inventory only.

**Irish Rail's lifts-and-escalators alerts page.** Found while scoping and it looked promising:
a page titled "Alerts for Lifts and Escalators" would, if it were a per-machine inventory with
status, have been a better primary source than the message feed and would have answered "how
many lifts does this station have". Checked on 29 August. It is not that.

### The formats that were written for this, and are not published here

There are two European standards that carry exactly the data this chapter is looking for.

**NeTEx** is the European standard for a station's static equipment and accessibility: lifts,
escalators, ramps, entrances, and the paths between them. **SIRI-FM**, Facility Monitoring, is
its realtime companion, which is precisely a live "is this lift working" feed. If Ireland
published SIRI-FM, this repository would not need to exist.

Neither is published for Ireland. data.gov.ie and the NTA's public transport data catalogue
were searched on 30 August 2026: 24 GTFS archives, NaPTAN, PTIMS, and nothing else. The only
occurrences of the string "accessibility" on the NTA's data page are navigation menu links.

### The regulation, and the hole in it

This is the part I did not expect, and it is why the absence looks permanent rather than like
an oversight somebody will fix.

Commission Delegated Regulation (EU) 2017/1926 requires each member state to run a **National
Access Point** publishing a listed set of travel data types, with NeTEx as the required
representation. Read the Annex and you find the data types listed. Read the qualifying clause
and you find this:

> provided they exist in digital machine-readable format

> **Concept: a National Access Point, and a lawful absence.** A National Access Point is a
> single official place where a country publishes its transport data so that anyone, including
> Google and Apple, can build on it. Ireland has one and it works. The clause above is what
> decides what goes into it: the duty is to **publish what you hold**, not to create what you
> do not. So if Irish Rail never captured a lift and escalator inventory in machine-readable
> form, nothing in the regulation compels them to start, and the obligation is satisfied by
> publishing timetables. The absence is lawful. That is a more uncomfortable finding than a
> gap somebody forgot to fill, because there is no process that closes it: no deadline, no
> non-compliance, nobody to write to. It closes when an operator decides to build an inventory,
> or when a future revision drops the qualifying clause.

### What the mapping apps have to work with, which is nothing

The strongest evidence that this data was never created, rather than that I searched badly, is
that four independent consumers of Irish public transport data hit the same wall.

Google Maps, Apple Maps, Transit, Citymapper and Moovit all consume GTFS for transit
directions, and accessible routing in all of them rests on three fields. Checked against the
live Irish Rail feed:

| field | what it answers | present? |
|---|---|---|
| `stops.txt` `wheelchair_boarding` | can you board here | **no, the column is absent** |
| `trips.txt` `wheelchair_accessible` | does this vehicle take a wheelchair | **no, the column is absent** |
| `pathways.txt` | a step-free route from entrance to platform | **no, the file is absent** |

So none of them can offer wheelchair routing on Irish Rail. That is a gap in the input, not a
failure of their products. Their place-level accessibility pins come from their own pipelines
instead: Google from Places and Local Guides, Apple from its own surveys. Crowd-sourced,
patchy, no platform detail, and no idea whether a lift is out today.

> **Worked example: the four-consumer argument.** When a search comes back empty there are
> always two explanations, and the weak one is that you searched badly. The way to tell them
> apart is to look at who else would need the same data and check whether *they* have it. Five
> billion-dollar mapping products, each with commercial reasons to offer accessible routing in
> Ireland and each with a team who would have found the file if it existed, all fall back to
> their own crowd-sourced pins for Irish stations. Two European standards exist for precisely
> this and neither is published. A regulation that would have compelled it carries a clause
> that exempts it. Four independent lines of evidence pointing the same way is much stronger
> than any one search, and it is the reason `notes/station-access.md` ends with an instruction
> not to re-run these checks: the one thing worth watching for is Ireland starting to publish
> NeTEx.

### What is left, and it is a CMS field

The only machine-readable statement of what an Irish rail station has is a free-text field on
irishrail.ie, written by hand, with no schema, no versioning and no obligation to be accurate.

It is at least not a scrape in the ugly sense. Each station page is server-rendered Nuxt and
serves its own data as JSON at `<page>/_payload.json`: named fields, no HTML parsing.
`robots.txt` disallows only `/stations.csv`. The find-a-station payload carries the full list of
152 station slugs, so nothing is crawled.

Two facts made it usable rather than merely available:

- **The join is free.** Every payload carries a `stationCode`, and it is exactly the same code
  space the message feed uses in `locationCodes`. All 15 codes that had lift notices at the
  time matched, 15 out of 15, with no fuzzy matching and no mapping file to maintain. The
  name-to-code join the scoping note had worried about does not exist as a problem.
- **The site already held half of it.** The notice text has always said which platform: "The
  lift at platform 2", "The lifts at platform 1 and 4". Nothing was parsing it, because the
  `head` says only "Dublin Pearse - Lift out of order" and that is what everything read.

And two fields that look useful and are not, both worth naming because both would have shipped
a wrong claim:

- **`wheelchairAvailability`** does not mean "this station is accessible". It means a
  wheelchair can be **borrowed** there. Dublin Pearse says Yes, Docklands says No. Surfacing it
  as accessibility would be a serious misrepresentation and it is one keyword away from
  happening.
- **`alert`, `alertStart`, `alertEnd`.** 131 stations carry one and they are never cleared.
  `alertEnd` values run back to 2014, 2015 and 2021. It is the last alert ever posted, not a
  live one.

### The unintended consequence

The snapshot is stored the way everything else in this project is stored: every payload
verbatim, one per line, sorted keys, in `lifts-data/stations/`. 7.8 MB plain, about 2 MB in
git, and it greps and diffs. Never edited; the derivation is always recomputed from it.
Refreshed monthly by a workflow that opens a pull request rather than pushing, because a
reworded station page can move a verdict from "no step-free access" to "unknown" and back, and
that is not a change to land unread.

Which produces something nobody set out to build. **The dated snapshots in
`lifts-data/stations/` appear to be the only versioned machine-readable record of Irish rail
station access that exists.** That was not the intent, it is a poor substitute for the operator
holding one, and it is a reason to keep the monthly refresh running well beyond keeping this
site's derivation fresh.

## Where it left the site

152 stations with codes, of which **57 claim a lift** and 95 do not. A denominator. A per-station
statement of what the operator says the station has, versioned and diffable.

And a new problem, which is that the source is prose, and prose has to be read. The next chapter
is about getting that wrong.

## Notes

- Issue #24, "Verify the accessibility data sources before the site is shared as usable"
  (closed by PR #30); PR #30, "Say what a lift outage did to step-free access" (30 Aug 2026).
- `notes/accessible-routes.md` (29 Aug 2026, answered 30 Aug): the three questions separated,
  the source-by-source scope, the struck sources, and the instruction not to scope them again.
- `notes/station-access.md` §§ Why scraping prose is the only option not the lazy one, The
  regulation and the hole in it, What the mapping apps have to work with, The sources and the
  ones that are closed, The snapshot (all 30 Aug 2026).
- GTFS checks: three NTA archives, ten files each, no `pathways.txt` and no `levels.txt`;
  `stops.txt` header ending at `parent_station`; `location_type` empty on 152 rail stops;
  NaPTAN 152 rail stops with `AccessArea` null and no "accessib" substring in 22 MB.
- Regulation: Commission Delegated Regulation (EU) 2017/1926, Annex, and its "provided they
  exist in digital machine-readable format" qualifier.
- Station counts measured 31 Aug 2026 from `stations/irishrail-20260830.jsonl`: 152 stations,
  57 with a lift, 95 without.
- Diagram: `diagrams/what-would-carry-it.svg`.
