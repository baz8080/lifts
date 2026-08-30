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

## Three things a review caught

**A summary sentence is not a per-platform claim.** Pearse opens "Via ramps,
stairs, escalators, and lifts." - a lift, no platform number. Counted as
covering the station, it made the page's own "Ramp to platform 1" a lift
platform, and a notice about platform 1 published "Platform 1 is reached by
lift". Specific beats general now: a bare-lift segment means every platform only
when no other segment names one.

**A reviewed entry expires with the page it quotes.** `STEP_FREE_ALTERNATIVES`
cites a sentence, and these pages are refetched monthly because Irish Rail
rewords them. If the sentence is gone the entry stops applying and the verdict
becomes `unknown`, not `lost`: the review said there was a way round, and a
reworded page is not evidence there is not. `tests/test_site_real.py` fails
loudly so somebody looks again.

**A partial fetch is refused, not warned about.** `latest_snapshot` reads the
newest file, so a snapshot written during an irishrail.ie wobble shadows the
last good one permanently, and the damage is invisible: those stations lose
their verdicts to "not in the station snapshot" and the denominator quietly
shrinks. Nobody spots 38 empty bodies in an 8 MB diff. Transient failures are
retried, and if any station is still missing nothing is written at all.

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

## Escalators are not step-free, and what that does and does not prove

**What is deduced.** An escalator is moving stairs. It was therefore never a
step-free route, so its going out of service cannot remove one. That is valid,
and it is all the site says now.

**What was being claimed and is not proven.** The first version published "this
did not remove step-free access" for every escalator outage. That is a claim
about the *station's* access state, not about the escalator, and it needs the
station's own prose to support it. Nothing checked. The escalator branch returned
before the `station is None` guard, so it was the only path in the module that
made a confident claim without consulting the source, while every other path can
fall back to `unknown`. At Connolly it happened to be true - level access to
platforms 1 to 4, a ramp to 5, a lift to 6 and 7 - but the code never looked.

**The premise the deduction rests on** is that "escalator" in a hand-written head
means an escalator. Checked across the corpus: 0 disagreements between head and
text in 228 messages, and both escalator notices name the machine unambiguously.
That is a strong prior and not a proof, so `verdict` now returns `unknown` when a
notice headed as one machine names the other in its text. It has never fired.

**The journey has two legs and the derivation sees one.** `platformAccess`
starts at the ticket office. `ticketOfficeAccess` is how you get from the street
to the concourse, and it is a separate field. Connolly's notice is "The
Escalator at **the main concourse**" - the entrance leg - and Connolly's
escalator is named in `ticketOfficeAccess` and nowhere else:

> "Escalator, lift or stairs from Amiens Street and from LUAS stop. Level access
> from car park."

Checking only `platformAccess` published "Irish Rail's page for Dublin Connolly
does not mention an escalator" at the one station where that line rendered, and
it was false. The escalator check now reads both fields and the station page
quotes both, labelled, because a lift or an escalator can be on either leg.

**The derivation still models only the platform leg**, and that is a real limit
rather than a tidy one: a lift outage at a station entrance would be reasoned
about against prose that describes a different part of the building. No notice
on record is of that shape, and issue #33 carries it.

**Where the source is silent.** Only 2 of 152 station pages mention an escalator
at all, and **Connolly's does not** - though we know it has one, because it
broke. So the prose is demonstrably not a complete inventory of vertical
circulation, and "no travelator is mentioned anywhere" is close to worthless as
evidence that none exists. A flat moving walkway *is* step-free, and one called
an escalator in a notice would break the deduction. None is named in any of the
152 pages, which is the most that can be said. Where the page does not mention an
escalator, the verdict now says so rather than implying the machine's role is
known.

**Still open: the grade.** `site.md` § *An escalator out is a day the station was
short of a way up* counts escalator outages at the same weight as lift outages,
so the grade and the station page disagree in public. Issue #32, with the
numbers: Dublin Pearse is graded F, the worst band, on the strength of an
escalator alone. The two rules were decided at different times against different
questions and both look sound alone; the question under them is what the grade is
for. Do not try to settle it from `platformAccess`, which mentions an escalator
at 2 of 147 stations.

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

### Not the direction, and not by hand

The obvious next step looks like labelling which direction each platform faces,
so the site could say "you could still travel towards the city". It should not
be taken. **This is an outage archive, not a travel planner.** A reader here is
looking at what happened, not deciding which train to catch, and a direction
label only pays off for somebody planning a journey.

It is also the expensive kind of fact. Only 10 of 57 stations name a direction
in their prose, and no source checked has the rest: GTFS carries no platform
data for Irish Rail at all, OSM has no `level` tags outside the Dublin termini,
NaPTAN's `AccessArea` is null on all 152 rail stops. So it would be roughly 120
platforms labelled by hand - the unprovenanced file `accessible-routes.md`
warns against - bought for a question this site does not answer.

The archive-shaped version of the same fact needs no labelling at all: "the
lift to platform 2 was out for twelve days, and platform 1 was level
throughout" bounds how bad the outage was, which is exactly what an archive is
for. That is derivable from the prose today.

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

## Why scraping prose is the only option, not the lazy one

Scraping a marketing site for accessibility facts should be a last resort, and
this is the record that it is one. Four independent consumers of Irish public
transport data hit the same wall, which is much stronger evidence that the data
was never created than that the searching was bad.

### The formats that exist for exactly this, and that Ireland does not publish

- **NeTEx** is the European standard for a station's static equipment and
  accessibility: lifts, escalators, ramps, entrances, and the paths between
  them. **SIRI-FM** (Facility Monitoring) is its realtime companion, and it is
  precisely a live "is this lift working" feed.
- Neither is published for Ireland. Searched data.gov.ie and the NTA's
  `transitData/PT_Data.html` catalogue on 2026-08-30: 24 GTFS archives, NaPTAN,
  PTIMS, and nothing else. The only "accessibility" strings on the NTA data page
  are navigation menu links.

### The regulation, and the hole in it

Delegated Regulation (EU) 2017/1926 requires each member state to run a National
Access Point publishing the listed travel data types, with NeTEx as the required
representation. The Annex applies to those data types **"provided they exist in
digital machine-readable format"**.

That is the whole story. The duty is to publish what you hold, not to create it.
If Irish Rail never captured a lift inventory in machine-readable form, nothing
compels them to start, and the obligation is satisfied by publishing timetables.
So the absence is lawful and permanent-looking rather than an oversight somebody
will fix.

### What the mapping apps have to work with, which is nothing

Google Maps, Apple Maps, Transit, Citymapper and Moovit all consume GTFS for
transit directions, and accessible routing in all of them rests on three fields.
Checked against the live Irish Rail feed:

| field | purpose | present? |
|---|---|---|
| `stops.txt` `wheelchair_boarding` | can you board here | **no, column absent** |
| `trips.txt` `wheelchair_accessible` | does the vehicle take a wheelchair | **no, column absent** |
| `pathways.txt` | step-free route, entrance to platform | **no, file absent** |

So none of them can offer wheelchair routing on Irish Rail. That is a gap in the
input, not in their products. Their place-level accessibility pins come from
their own pipelines instead - Google from Places and Local Guides, Apple from
its own surveys - which is the same shape as the OpenStreetMap result below:
crowd-sourced, patchy, no platform detail, and no idea a lift is out today.

### Where that leaves this

The only machine-readable statement of what an Irish rail station has is a
free-text CMS field on irishrail.ie, written by hand, with no schema, no
versioning and no obligation to be accurate. This project has already found a
typo in it (Rush and Lusk naming platform 1 twice), a self-contradiction
(Greystones), and a station whose page says "Level" while its lifts break
(Limerick Junction).

Which makes the dated snapshots in `lifts-data/stations/` the only versioned
machine-readable record of Irish rail station access that appears to exist. That
was not the intent and it is a poor substitute for the operator holding one, but
it is a reason to keep the monthly refresh running beyond keeping the derivation
fresh.

**Do not re-run these searches.** GTFS, GTFS-Realtime, NaPTAN, PTIMS, the NTA
developer API and OpenStreetMap are all checked and recorded, here and in
`accessible-routes.md`. If anything changes it will be because Ireland starts
publishing NeTEx, and that is the one thing worth checking again.

## OpenStreetMap: carried, measured, removed

It was here as a second opinion on Irish Rail's prose and it is gone. Recorded
at this length so nobody adds it back on the same hunch, because the hunch is a
good one and it is wrong.

**What it could do.** It is the only machine-readable station graph that exists
for this network. Around Pearse: named `Platform 1` and `Platform 2` ways, four
`highway=elevator` nodes carrying `level` tags, escalators as `highway=steps` +
`conveying`, `highway=corridor`, `wheelchair` tags. A routable topology, the
thing GTFS `pathways.txt` would have been. It also spots 13 stations where the
prose mentions no lift and OSM maps one, Limerick Junction among them.

**What it could not do.** Three measurements, all against the real data:

1. **It changed no verdict.** `has_lift()` was consulted in exactly one place,
   as `!= "yes"`, and OSM could only move a station from `no` to `unknown`.
   Both fail that test. Checked with a synthetic digest mapping a lift at all
   152 stations: 24 outages, 0 verdicts changed.
2. **Its one signal was redundant.** A station in those 13 that has a notice
   already returns `unknown` without it, because `claims_lift` is false.
   Limerick Junction: same verdict, same wording, with or without.
3. **It could not answer the street-side question**, which is the only thing
   that would have earned its keep. "Which platform is reachable without a
   lift" needs `level` tags on platforms. Sampled over 12 stations that have
   had notices: 12 of 12 had platforms mapped, **2 of 12** carried a `level`
   tag, both Dublin termini. Everywhere else there is platform geometry and no
   vertical information, so the graph is not traversable.

Irish Rail's prose answers that same question at 32 of 57 stations, in words.

**So it went.** It cost about 60 lines, a monthly HTTP budget against a service
that rate-limits, and the one place the raw-artefact invariant was bent - the
raw map extracts total roughly 450 MB, so the digest had to be derived rather
than verbatim. For nothing that reached a reader.

The one thing that would bring it back: the day the site says **"this station
has no lift"** out loud, those 13 stations become a wrong claim rather than a
silent one. Nothing says that today, and the site is an outage archive, so
nothing may ever need to.

## The snapshot

`lifts-data/stations/irishrail-<date>.jsonl` holds every payload **verbatim**,
one per line, `sort_keys=True`, the shape `store.write_raw` uses. 7.8 MB plain,
which git stores at about 2 MB and which greps and diffs. Never edited; the
derivation is always recomputed from it.

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
