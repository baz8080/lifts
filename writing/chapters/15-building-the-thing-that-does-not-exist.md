# 15. Building the thing that does not exist
*~10 min read · PR #46 · 4 to 8 September 2026*

*Where we are:* chapter 06 established that nothing machine-readable says how an Irish station's
entrances, concourse, platforms, lifts and escalators connect. Chapter 07 read somebody's prose
instead, carefully, and chapter 12 wrote down how far that can be trusted. This chapter reverses
a decision the series has been quoting as settled since chapter 06.

## The question that opened this stretch

Barry's question, which is the obvious one and which I had an answer to:

> What would it take to build one by hand?

The answer on file was *don't*. `notes/accessible-routes.md` § What is deliberately out has said
since 29 August:

> Hand-curating station accessibility by hand from photographs, station visits or Wikipedia. It
> would be a second source with no provenance, no refresh and no way to audit, attached to a
> site whose entire discipline is that every number traces back to a recorded observation.
> Better to say nothing.

That paragraph is right about the failure mode and wrong about the conclusion, and the
difference between them is one word. It does not say hand-curation is impossible. It says a
hand-curated **file** has no provenance, no refresh and no audit.

Those are three properties. Properties can be built.

> **Concept: the objection is a specification.** A rejected approach usually gets summarised as
> "we decided against that", and then nobody can tell later whether the objection was about the
> approach or about a particular implementation of it. Writing it out in full, as three named
> defects, turns it into a list of requirements: a fact must say who recorded it, when, from
> what, and how sure they were (provenance); it must expire when its source changes (refresh);
> and it must be replayable from an append-only record rather than edited in place (audit).
> Every one of those is something this repository already does for the collector's logs. The
> objection was never to hand-curation. It was to a file somebody edits.

## What changed

### Three documents, and what each turned out to be for

Barry brought three sources. Sorting them was most of the design work.

**Irish Rail's Guide for Rail Passengers with Disabilities (2026)** has no per-station data at
all. It is a who-to-ask: an access email address, a named head of customer care and
accessibility, a quarterly Disability User Group chaired and attended by eleven named member
organisations, a hub station per zone whose staff cover the zone, and the phrase "over 50 lifts"
renewed since 2020, which means **a lift register exists somewhere**.

**Metro Nation's Dublin rail map (July 2025)** was excluded as a source, and the call was
Barry's. Its "no step-free access" glyph marks twelve stations. Checked against Irish Rail's own
page it disagrees at three of them, on no stated definition, and it was already behind the
network when it was drawn: Athy's lift was delivered afterwards. It is kept in the note as one
sentence of evidence for the rule it teaches, which is **define the terms before asking anybody
anything**.

**The Station Accessibility Programme preliminary business case**, Iarnród Éireann to the NTA,
October 2024, 188 pages. The most useful of the three by a distance, and the thing I would not
have found by searching for data:

- Table 6-2 lists **the 51 stations that do not yet meet the accessibility standard, in the
  order the programme means to fix them**, in three packages of 15, 15 and 21. That is a
  denominator the site has never had, and it is now carried in code.
- Appendix B has a dated "current context" paragraph for the first fifteen that reads like a
  route graph in prose: *"passengers wishing to travel southbound must exit the station
  property, pass over a small road bridge ... and enter the station via a ramp behind Platform
  1"*. Better than Irish Rail's public page for those fifteen. Each has a delivery date beside
  it, which is why the 2024 text for Athy says there is no step-free access to platform 2 and
  the 2026 page says "Lift to platform 2".
- **The audit exists.** A 2014 feasibility report surveyed all 54 then-outstanding stations
  against the European accessibility standard, a 2019 review updated the list, and 2021
  preliminary design reports cover the first fifteen. The business case names the teams holding
  them. That is what a Freedom of Information request asks for, by name, rather than asking
  hopefully for "accessibility data".
- **Its definitions**, which is what the questionnaire needed. The 2014 study scoped the minimum
  as a wheelchair user boarding and alighting and entering and leaving each station,
  distinguished **assisted** from **un-assisted** routes, counted un-assisted access to a
  *single* platform per station, and treated routes *between* platforms separately, because
  crossing the track is the expensive part.

### The observation log

`lifts-data/survey/<CODE>.jsonl`. One file per station, one JSON object per line, sorted keys,
never edited. A questionnaire maps to one file, two labellers never collide, and a diff is
readable.

```json
{"code": "ATHY", "observed": "2026-09-12", "confidence": "high",
 "source": {"kind": "survey", "by": "Barry"},
 "fact": {"type": "edge", "id": "lift-p2", "mode": "lift", "from": "footbridge",
          "to": "platform-2", "equipment": "lift-p2", "hours": "06:00-23:30"}}
```

The replay rule mirrors `rebuild` exactly: **lines apply in file order and the last line for a
fact key wins.** A correction is a later line with the same id. There are no line ids and nothing
to cross-reference, so appending a line by hand stays cheap, which matters when the people
filling these in are not programmers.

`confidence` is `low` (read off a page), `medium` (told, or a reviewed sentence) or `high`
(seen). The source kind decides what the validator demands: a page-sourced fact must carry the
snapshot, the field and a verbatim quote; a surveyed one must say who; a business-case one must
give a page number; imagery must give a URL; an FOI response must give its reference.

And the refresh property falls out of chapter 07's rule, generalised: **a page-sourced fact
expires when its quote leaves the page.** The replay drops it and says so, and a test turns red
until somebody reads the diff. An empty quote records that the field said nothing usable, and
expires the day it says something.

### The graph, and an edge that records ignorance

Nodes are entrances, concourses, platforms, landings. Edges are walkways, ramps, stairs,
footbridge stairs, subway stairs, lifts, escalators and gates. A lift or escalator edge belongs
to a piece of equipment, which can carry aliases so a notice worded "the lift on P2" can be
joined to it by hand.

There is a ninth edge mode and it is the most interesting thing in the schema.

> **Concept: an edge that records ignorance.** `unsurveyed` is a way known to exist whose nature
> nobody has recorded. It sounds like a placeholder and it is load-bearing. Without it, an
> entrance the seeder cannot read has no edges at all, so every platform behind it comes out
> "never step-free", which is a confident false claim in the exact direction chapter 07 spends
> its length avoiding. With it, the graph is **incomplete**, and incomplete is the truth. A data
> model that has no way to say "there is something here and I do not know what" will always
> encode absence as impossibility, because those are the only two states it has.

Step-free access per platform is then reachability from any entrance over walkway, ramp, lift
and gate edges, preferring routes with fewest lifts. An outage is the named equipment's edges
removed, and a platform is **lost** if no step-free route is left, **kept** if one is, **never**
step-free if it had none to begin with, and untouched if its best route never used the machine.

### Two rules that keep it on the safe side

Chapter 07's safe direction had to survive the change of method, and it does, through two rules
that are both about the derivation refusing to outrun its evidence.

**The confidence gate.** "Another step-free way" is published only where every edge on the
surviving route was recorded at medium confidence or better. Otherwise the platform reads as
lost, and the detail says the survey names a route nobody has confirmed. Seeds are low
confidence, so **a graph seeded from the page alone can never say more than the prose derivation
does**, and it earns verdicts only as lines with a human source land.

**Nothing joined is unknown.** A notice that joins no recorded equipment is unknown, never a
guess.

### Worked example: the pilot says less than the prose, and that is the design working

Five stations were seeded from their pages and committed: Hazelhatch, Dublin Pearse, Dublin
Connolly, Athy and Castleknock. Every line is page-sourced, so the whole pipeline runs end to
end and publishes nothing new.

| station and notice | the graph says | the prose says |
|---|---|---|
| Athy, lift at platforms 1 and 2 | lost 2; platform 1 never needed it; platform 1 named but no lift touches it | lost 2, same note about 1 |
| Pearse, lift at platform 2 | lost 2; platform 1 never needed it | lost 2; platform 1 kept |
| Pearse, escalator at platform 2 | **unknown**: the page's only escalator is on the way in | escalator, quoting the platform 2 lift |
| Connolly, escalator at the concourse | escalator, and a lift between the entrance and the concourse | escalator, quoting both entrance sentences |
| Hazelhatch, lift to platforms 2 and 3 | **unknown**: no platform named on the page | lost 2 and 3 |

Read the two "unknown" rows and the new method looks worse than the old one. It is not. At
Hazelhatch the page claims a lift without naming a platform, so the seed draws no lift edge and
the notice joins nothing. The graph is being honest about a vague page where the prose
derivation was making an inference. The questionnaire asks the question.

The confidence gate bites in the same direction at Raheny, one of the two reviewed step-free
exceptions from chapter 07: the ramp is recorded at medium confidence and the way in at low, so
the graph says lost where the prose says there is an alternative, **until somebody confirms the
door.**

A method that produces fewer confident answers than the one it replaces, on its first day, is
what it looks like when the evidence bar goes up.

### The questionnaire is generated, never written

One Markdown form per station. The definitions come first, in the business case's own words,
because the three sources already in hand disagree with each other for want of them.

Then, per station: the page's two fields quoted verbatim with "is this right, what does it leave
out"; how the site currently reads them; the page-versus-feed discrepancy where chapter 07's
unknown table has one; the business case paragraph and the station's rank in the programme where
it has them, with "this was written in 2024, what has changed since"; every distinct notice the
feed has carried about the place with "which machine is this, and which two places does it
connect"; ten common questions; and the draft observations for the person to correct rather than
a blank page.

The seeder drafts those from the page at low confidence, quoting the sentence each line came
from, and **refuses to overwrite an existing log**, because a log is append-only and a second
seed would duplicate every line.

One line in the note explains why this exists at all: the site's prefilled correction issue from
chapter 07 **has existed since 30 August and has never fired.** Passive crowdsourcing yields
nothing. The outreach has to be structured, and a form somebody can answer is the structure.

## The turn at the end

Chapter 06 is about a specific absence. GTFS `pathways.txt` is the format that would say a
station's interior is a graph, and Ireland publishes none. NeTEx is the European standard the
regulation names, and Ireland publishes none.

This branch ships a `gtfs` command that exports stops, pathways and levels.

It is five stations, seeded from prose, at low confidence, and it is not authoritative about
anything. But the shape of the project has changed. For three weeks this repository catalogued
an absence and worked carefully around it. It is now building the missing artefact, in the
format the mapping apps already read, with a documented path to the format the regulation
names, plus a `prose` command that renders a surveyed station in a layout drafted to hand to
Irish Rail: a paragraph per platform, "yes", "yes, by lift" or "no" as the first words, and the
failure case stated in the same breath rather than left to be inferred.

The site does not read any of this yet. When it does, the graph verdict replaces the prose one
only at a station whose log has a human source, and the prose verdict stands everywhere else.

## Where it left the site

Unchanged, deliberately. A schema, a validator, a replay, a reachability derivation, a
questionnaire generator, a seeder, two exports, a fixture pinning what the survey says, five
pilot stations on a branch of the data repository, and a note carrying the design, the options
assessed and what to ask for under Freedom of Information.

## Notes

- PR #46, "Record station access by hand, with provenance: the observation log and the graph it
  replays into" (8 Sep 2026).
- `notes/step-free-graph.md` (4 Sep 2026): the three documents, the options table, the log
  schema, the graph, the two safe-side rules, the questionnaire, the seed, the pilot table, the
  proposed format, and the fixture.
- `notes/accessible-routes.md` § What is deliberately out (29 Aug 2026), which this reverses,
  and `notes/station-access.md` § The safe direction, which it preserves.
- The business case is Iarnród Éireann to the NTA, PBC-3.5, 30 October 2024. Table 6-2 is the
  51 stations; Appendix B the current-context paragraphs; Table 12-3 names the document holders.
- The five pilot stations are seeded on the `survey-pilot` branch of `baz8080/lifts-data`;
  `main` there carries no `survey/` directory yet, which is why the graph fixture's own inputs
  are not pinned (chapter 14).
- 490 tests passed at that merge; 516 as of 12 September 2026.
