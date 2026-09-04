# A human-labelled step-free access graph - 2026-09-04

Barry's question: the site cannot build an authoritative picture of how a
station's entrances, concourse, platforms, lifts and escalators connect from
the data that exists, because no such data exists (`station-access.md` § Why
scraping prose is the only option). What would it take to build one by hand,
what would the questionnaire look like, who could help, and what other routes
are there?

The short answer is that it takes three things `accessible-routes.md` § What is
deliberately out said a hand-curated file could not have: provenance, refresh
and audit. This note designs them in, and the first PR ships the schema, the
questionnaire, the derivation and a pilot, with the site untouched. The
observation log lives in `lifts-data/survey/`, one file per station, and this
repository carries the code that reads it and the fixture that pins what it
says.

## What was learned from the three documents Barry brought

**Irish Rail's Guide for Rail Passengers with Disabilities (2026).** No
per-station data at all. It is a who-to-ask: `access@irishrail.ie`, Ronan
Murphy as Head of Customer Care and Accessibility, a quarterly Disability User
Group chaired by Tony Ward with eleven member organisations named (the Irish
Wheelchair Association, Vision Ireland, Voice of Vision Impaired, Kildare
Access Group, the Central Remedial Clinic, As I Am, the Irish Deaf Society,
Headway, the Alzheimer Society, the Irish Non-Neurotypical DPO and Irish Guide
Dogs), a quarterly accessibility newsletter, a hub station per DART and
Commuter zone whose staff cover the zone, "over 50 lifts" renewed since 2020
(so a lift register exists), and the Customer Lift Call system at "most"
stations with a lift.

**Metro Nation's Dublin rail map (July 2025).** Excluded as a source, and the
decision was Barry's. Its "No step-free access" glyph marks twelve stations,
recovered from the PDF's vector layer, and checked against Irish Rail's page it
disagrees at Athy and Carlow (page: "Lift to platform 2") and at Ashtown (page:
"Both platforms can be accessed via ramp"), on no stated definition, and it was
already behind the network: Athy's lift was delivered after it was drawn.
Nothing it says survives one survey answer. It is kept here as one sentence of
evidence for the rule it teaches: define the terms before asking anyone
anything.

**The Station Accessibility Programme preliminary business case** (Iarnrod
Eireann to the NTA, PBC-3.5, 30 October 2024, 188 pages). The most useful of
the three, by a distance:

- Table 6-2 lists **the 51 stations that do not yet meet the accessibility
  standard, in the order the programme means to fix them**: 15 in the first
  package (Dalkey to Claremorris), 15 in the second, 21 in the third. Carlow,
  Ennis and Edgeworthstown were done before it was written; Connolly, Ashtown
  and Coolmine went to DART+; Limerick was done under other funding. About 80
  stations were improved between the late 1990s and 2022. This is the
  denominator the site never had, and `lift_access/nta.py` carries it.
- Appendix B has a dated **"Current context" paragraph for the first fifteen**
  that reads like a route graph: "Accessible access to platform 2 (southbound)
  is via the station building and platform 1 (northbound) is via a ramp which
  connects to Ardeevin Road", "passengers wishing to travel southbound must exit
  the station property, pass over a small road bridge ... and enter the station
  via a ramp behind Platform 1". Better than Irish Rail's page for those
  fifteen, and each has a delivery date beside it, which is why the 2024 text
  for Athy says no step-free access to platform 2 and the 2026 page says "Lift
  to platform 2". The questionnaire quotes it and asks what has changed.
- **The audit exists.** The 2014 Accessibility Project Feasibility Report
  surveyed all 54 then-outstanding stations against the PRM-TSI, the 2019
  Review updated the list, and 2021 Preliminary Design Reports cover the first
  fifteen. Table 6-1 gives the prioritisation criteria (track crossing, station
  access, platforms, lighting, user group input, unstaffed stations) and Table
  12-3 names the holders: IE Design Team, IE Compliance Team, IE Station
  Operations. That is what a Freedom of Information request asks for, by name.
- **Its definitions.** The 2014 supplementary study scoped the minimum as "a
  wheelchair user to board and alight from a train and enter and leave each
  station", distinguished **assisted** from **un-assisted** routes, counted
  un-assisted access to a *single* platform per station, and treated routes
  *between* platforms separately because crossing the track is the expensive
  part. A MIAS, Mobility Impaired Access Structure, is a footbridge with lifts.
  The questionnaire uses this vocabulary so answers line up with IE's own.

## The other options, and what each is for

| Option | Verdict |
|---|---|
| Freedom of Information to Iarnrod Eireann and the NTA | The cheapest route to structured per-station data that already exists. Ask by name for the 2014 Feasibility Report station surveys, the 2019 Review addendum, the 2021 Preliminary Design Reports, and the lift register behind "over 50 lifts renewed", in their native spreadsheet form rather than as PDFs |
| The business case's Appendix B paragraphs | Admitted now as a `nta-pbc-2024-10` source, page number and all: a second opinion where the page is thin, naming routes the page does not |
| GTFS pathways as the shape | Yes, as the export. `pathway_mode` 5 beside 4 between the same nodes is exactly "the escalator has a lift beside it", and Google, Apple and Transit read it. MobilityData publishes a pathways survey methodology handbook, which is a ready-made field guide |
| The UK precedent: Rail Delivery Group Knowledgebase step-free coverage and Stations Made Easy | A national human-surveyed graph exists there. Its recorded failure, from an FOI on the definition, is that each operator defined "step-free" differently. Hence terms first |
| Transport for London's step-free categories | The right vocabulary for the platform-train gap the guide keeps mentioning; ramps and staff assistance are a layer beside the station graph, not part of it |
| OpenStreetMap as the home | Public and community-refreshed, but ODbL, no per-fact provenance, and the earlier pass found no `level` tags outside the Dublin termini (`station-access.md` § OpenStreetMap). Worth contributing *to* once the log exists; not the source of truth |
| A11yJSON, accessibility.cloud, Wheelmap | Place-level schemas, not route graphs. Skip |
| Remote labelling from imagery (Irish Rail's `streetViewCode`, Mapillary) | Cheap for the way in, weak for the interior. Admitted as an `imagery` source with its URL and date, at whatever confidence the viewer is honest about |
| The site's prefilled correction issue | Has existed since 2026-08-30 and has never fired. Passive crowdsourcing yields nothing; the outreach has to be structured, which is what the questionnaire is for |
| Advocacy groups, hub-station staff, Irish Rail customer support | Labellers, not sources. Access for All Ireland is a small X account; the Disability User Group's members are the organised ones. Every answer is one observation with the person or organisation and the date |

## The observation log

`lifts-data/survey/<CODE>.jsonl`, one file per station, because a
questionnaire maps to one file, two labellers never collide, and a diff is
readable. One JSON object per line, `sort_keys=True`, never edited. The replay
rule mirrors `rebuild`: **lines apply in file order and the last line for a
fact key wins.** A correction is a later line with the same id; `observed` is
provenance, not ordering. There are no line ids and nothing to cross-reference,
so a hand-appended line stays cheap.

```json
{"code": "ATHY", "observed": "2026-09-12", "confidence": "high",
 "source": {"kind": "survey", "by": "Barry"},
 "fact": {"type": "edge", "id": "lift-p2", "mode": "lift", "from": "footbridge",
          "to": "platform-2", "equipment": "lift-p2", "hours": "06:00-23:30"}}
```

`confidence` is `low` (read off a page), `medium` (told, or a reviewed
sentence), `high` (seen). `source.kind` and what `survey.validate` demands of
each: `irishrail-page` (`snapshot`, `field`, verbatim `quote`), `survey`
(`by`), `irishrail-support` (`reference`), `nta-pbc-2024-10` (`page`), `photo`
(`file`), `imagery` (`url`), `osm` (`object`, `date`), `foi` (`reference`).

A page-sourced fact **expires when its quote leaves the page**, the
`STEP_FREE_ALTERNATIVES` rule generalised: `graph.replay` drops it and says
so, and the real-corpus test turns red until somebody reads the diff. An empty
quote records that the field said nothing usable, boilerplate only or blank,
and expires the day it says something.

Facts are keyed `node:<id>`, `edge:<id>`, `equipment:<id>`, `level:<id>`,
plus `retract` (removes a key) and `note` (keys nothing). Node kinds are
`entrance`, `concourse`, `platform` (with its label), `landing`, `generic`.
Edge modes are `walkway`, `ramp`, `stairs`, `footbridge-stairs`,
`subway-stairs`, `lift`, `escalator`, `gate` (wicket, barrow-crossing,
level-crossing, ticket-barrier) and `unsurveyed`, which is a way known to
exist whose nature nobody has recorded: without it an entrance the seeder
cannot read would make every platform "never step-free", and with it the graph
is incomplete, which is the truth. A ramp or gate with `wheelchair: false`
(Rathdrum's ramp, Kilcoole's wicket gate) is recorded and is not step-free.
A lift or escalator edge belongs to a piece of `equipment`, which can carry
`aliases` so a notice worded "the lift on P2" can be joined by hand.

## What the graph says, and what it refuses to

Step-free per platform is reachability from any entrance over walkway, ramp,
lift and gate edges, `wheelchair` not false, fewest lifts first. A notice is
joined to equipment by alias, then by the platform it names, then by its leg
(an entrance-leg notice is every machine touching an entrance; a notice naming
nowhere is every machine of its kind), and a platform it names that no
equipment touches is reported, never guessed at. The outage is that
equipment's edges removed: a platform is **lost** if no step-free route is
left, **kept** if one is, **never** step-free if it had none to begin with,
and untouched if its best route never used the machine. An escalator notice
is the same deduction as the prose one, plus whether the survey records a lift
between the same two places.

Two rules keep this on the safe side of `station-access.md` § The safe
direction:

- **The confidence gate.** "Another step-free way" is published only where
  every edge on the surviving route was recorded at medium or better.
  Otherwise the platform is read as lost and the detail says the survey names
  a route nobody has confirmed. Seeds are `low`, so a graph seeded from the
  page can never say more than the prose derivation does, and it earns
  verdicts only as lines with a human source land. Seeded, this bites at
  Raheny's reviewed ramp: the ramp is medium, the way in is low, so the graph
  says lost where the prose says alternative, until somebody confirms the door.
- **Nothing joined is unknown.** Hazelhatch's page claims a lift without naming
  a platform, so the seed draws none, and the notice "The lift to Platform 2
  and 3" comes back unknown where the prose says lost. That is the seed being
  honest about a page that is vague; the questionnaire asks the question.

The site does not read any of this yet. When it does, a later PR, the graph
verdict replaces the prose one only at a station whose log has a human
source, and the prose verdict stands everywhere else.

## The questionnaire

Generated, never hand-written: `python -m lift_access --data-dir D
questionnaire [CODE...]` writes one Markdown form per station, every station
with a notice on record by default. The definitions come first, in the
business case's own words, because the sources already in hand disagree for
want of them: step-free is a way from the road to the platform edge with no
step, over level ground, a ramp, a lift or an open gate, un-assisted; an
escalator, a footbridge, a subway, a barrow crossing, a locked wicket gate or
"a companion is needed" is assisted, recorded and not counted; to a platform
and between platforms are asked separately; the platform-train gap is asked
separately and changes nothing about the station.

Then, per station: the page's two fields quoted verbatim with "is this right,
what does it leave out"; how the site reads them; the page-versus-feed
discrepancy where `station-access.md` § When it says "unknown" has one; the
business case paragraph and rank where it has them, with "this was written in
2024, what has changed since"; every distinct notice the feed has carried
about the place with "which machine is this, and which two places does it
connect"; the ten common questions (entrances, platforms, each entrance to
each platform as a walked sequence, each lift, each escalator, each ramp, each
gate, what a wheelchair user does when the lift is out, the step and gap, who
answered and when); and the draft observations for the person to correct.

## The seed

`seed CODE` drafts a station's log from its page, at `low`, quoting the
sentence each line came from, so the person corrects rather than starts from
nothing. It uses `model.py`'s own pickers and parses no connectives: a level
sentence gives a walkway or ramp, a lift sentence naming platforms gives lift
equipment and a lift edge with a parallel stairs edge where the sentence is
stepped, "lifts and ramps" gives no ramp, a stepped sentence with no lift gives
stairs only, the two reviewed alternatives give a medium ramp marked as
reviewed, Pearse's entrance-leg sentence gives a second entrance with lift,
stairs and escalator, a general lift claim gives a note and no lift, and a
way-in field that is blank or says "No ticket office" gives an `unsurveyed`
edge. `observed` is the snapshot's date, so a reseed is byte-identical.
`seed --write` refuses an existing file, because a log is append-only and a
second seed would duplicate every line.

The pilot is Hazelhatch, Pearse, Connolly, Athy and Castleknock, seeded and
committed to `lifts-data/survey/`. Every line is page-sourced, so the pipeline
runs end to end and publishes nothing new, which is the design working:

| station | graph | prose |
|---|---|---|
| Athy, lift at platforms 1 and 2 | lost 2, platform 1 never needed it, platform 1 named but no lift touches it | lost 2, same note about 1 |
| Pearse, lift at platform 2 | lost 2, platform 1 never needed it | lost 2, platform 1 kept |
| Pearse, escalator at platform 2 | unknown: the page's only escalator is on the way in | escalator, quoting the platform 2 lift |
| Connolly, escalator at the concourse | escalator, and a lift between the entrance and the concourse | escalator, quoting both entrance sentences |
| Hazelhatch, lift to platforms 2 and 3 | unknown: no platform named on the page | lost 2 and 3 |

## A format to propose to Irish Rail

Barry's angle, and the cheapest lasting fix, because the page fields are the
one source Irish Rail already maintains. The first draft here was a field list
with headings, and the review was right that it read as written for a machine.
A passenger asks two questions, *can I get to my platform without steps* and
*what happens if the lift is out*, so the layout answers those first, per
platform, in sentences, and puts the inventory after. `prose CODE` renders a
surveyed station in it, so the proposal arrives with worked examples and a
fact the layout cannot say is a test failure. Athy, from the seed:

```
Getting to the platforms without steps

Platform 1: yes. A level walk to the concourse or ticket office, then a
level walk to platform 1.

Platform 2: yes, by lift. A level walk to the concourse or ticket office,
then a lift to platform 2. If the lift is out of service there is no
step-free way to platform 2.

Getting into the station

The station entrance: level to the concourse or ticket office.

Lifts and escalators here

One lift.
- Lift lift-p2: between the concourse or ticket office and platform 2.
No escalators recorded.
```

What makes it less ambiguous than today's fields without making it a form: a
fixed order of questions, one paragraph per platform naming the trains it
serves, "yes", "yes, by lift" or "no" as the first words, the failure case
stated rather than left to be inferred, "without steps" in the passenger's
words rather than "un-assisted" in the engineer's, and the lift-call sentence
moved to a site-wide page so it stops standing in for a lift inventory. The
controlled vocabulary lives inside the sentences (level, ramp, lift, stairs,
footbridge, subway, escalator, wicket gate, barrow crossing) so the page can
still be read back by a machine, and the machine form proper is the same
graph exported as GTFS pathways (`gtfs --out DIR`) or, one day, NeTEx, which is
what 2017/1926 would have Irish Rail publish if the data existed. The layout
is a draft to work on; the principle is fixed.

## The fixture, and why it is a second file

`tests/fixtures/graph-golden.json` pins what the survey says: every surveyed
station's step-free platforms with their routes, lift platforms, platforms
with no route, completeness and contradictions, and the graph verdict for
every notice at a surveyed station. It is keyed on a fingerprint of the survey
files, not on the station snapshot, so a line appended to a log fails this
file and not `access-golden.json`, and a refreshed snapshot fails that one and
not this. Same document shape, same `golden.differences`. `golden` writes
both.

The cross-repo ordering is the same as the snapshot's: the survey lives in
`lifts-data`, CI reads it at its head, and the real-corpus class skips without
it. A stale `graph-golden.json` after an append is intended.

## Rejected

- **A hand-maintained `stations.json`.** Still the failure mode; the log is
  not one because every line carries who, when and from what, a page line
  expires with the page, and the fixture makes every change a read diff.
- **Supersede ids on observations.** Last line wins is enough, mirrors
  `rebuild`, and keeps a hand-appended line to one object with nothing to
  look up.
- **Authoring GTFS pathways directly.** Interoperable, but GTFS has no column
  for who said so, when, or how sure, and the equipment-to-notice join would
  have to live beside it anyway. It is the export.
- **OpenStreetMap as the home.** Above.
- **The Dublin map as a source.** Above.
- **A `station` fact for "no step-free access here".** Existed only to carry
  the map's glyph; went with it. A station-level claim is what the graph
  derives, not what a line asserts.
- **Reading the site's verdicts from the graph in this PR.** Not until a
  station has a human-sourced line; a seeded graph says less than the prose,
  on purpose.
