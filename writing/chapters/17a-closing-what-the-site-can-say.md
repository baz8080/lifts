# 17a. Closing: what the site can and cannot say
*~9 min read · the whole series · 12 September 2026*

*Where we are:* the end, in two halves. This one is the account: the figures, the two lists, and
the table of where the three sites diverged. The next is what I would tell somebody starting a
fourth.

## The question, answered

**Which Irish Rail stations have lifts out of service, and for how long?**

As of 12 September 2026, over 35 days of collection, 1,648 runs and 497 recorded notices:

- **53 outages across 37 stations.** 6 planned works in August and 1 in September, 3 escalators.
- Lift availability across the 21 stations named in August: **76%**, and **79%** across the 22
  named in September so far. That is the share of watched days on which no lift was reported
  out at those stations.
- August grades across 21 station-months: **A 3, B 1, C 4, D 6, E 5, F 2.** September so far,
  across 22: **A 2, C 7, D 10, E 1, F 2.**
- At the last poll: three lift notices, across three stations.
- **28 of the 45 notices removed step-free access** to at least one platform, as worked out
  from Irish Rail's own station pages. 3 were escalators. **14 are unknown**, because the two
  hand-written sources disagree.

Thirty-five days is not a season and none of these numbers should be quoted as a fact about
Irish Rail. They are a fact about thirty-five days, which is the honest scope, and the site says
the collection start date on every page. Several of them were different a week ago for reasons
that had nothing to do with lifts breaking: chapters 10 and 11.

The unknown share is the row to watch, and it is going the wrong way: 6 of 24 on 31 August, 7 of
30 on 4 September, **14 of 45** now. The corpus is reaching stations whose pages are thinner
than the ones it started with, which is what chapter 12's reliability section meant by the
page's own error rate being the ceiling, and chapter 15 is the attempt to raise it.

## What the site can say

- **How long a notice was listed**, to the resolution of a 30-minute poll, over a window whose
  boundaries are recorded runs rather than a clock.
- **Which stations were named**, keyed by location code, named from the newest notice.
- **How much of a month a station spent with a lift reported out**, as a share of days watched,
  and a letter for that share on a scale it declares as its own.
- **How long each stretch a notice was on the feed ran**, rather than the envelope of its first
  and last appearance, and **which stations are out right now**.
- **Whether a notice was a fault or planned works**, from the notice's own words, and how long
  works ran past a week of grace.
- **What Irish Rail claims the start date was**, printed as their claim and used for nothing.
- **What an outage did to step-free access**, worked out from Irish Rail's own station page,
  labelled as an inference, with a link inviting correction, and **which platform kept it**
  where the page says so plainly and the two sources agree.
- **Which leg of the journey a notice is about**, from its own words, and therefore which of
  Irish Rail's two access fields to read it against.
- **Who lost a way up** when an escalator stopped, and what the page names on the same leg.
- **How many stations have a lift**: 57 of 152, from a versioned snapshot.
- **How far to trust all of that**, in a dated section separating the strong claims from Irish
  Rail's word taken on trust and from untested machinery.
- **All of it, off the page**: an Atom feed for the network and one per station, and a CSV of
  every outage the site shows.

## What it cannot

- **Say anything is "fixed".** There is no completion signal. A notice stops being listed, and
  that is all that is known.
- **Say how many lifts a station has**, or whether the one named was the only one. A notice
  names one machine in prose.
- **Say a station is accessible.** It can say Irish Rail's page names a step-free way to a
  platform that does not use the lift, at two stations in the country. That is a much smaller
  claim and the site's wording stays inside it.
- **Say a lift was working** while an escalator was out. It can say the page names one on the
  same leg and that no lift notice overlapped, and no more: the feed is not complete.
- **Give a network availability figure.** The denominator is the stations named that month,
  because the feed names a station only when something is wrong with it, and the page says so.
- **Judge an entrance-leg lift outage against experience.** The machinery exists, no notice has
  exercised it, and a sixth of the network says it has no ticket office.
- **Tell "planned maintenance" from a fault.** The marker is one literal phrase and Irish Rail
  used another on 11 September. Open as issue #53.
- **Colour a day before 8 August 2026.** Nothing was watching.

## The three-way table

The deliverable of this series. Every row is a place where the three sites do the same job
differently, and every one traces to a property of the data rather than a preference.

| | uisce (water) | esb (power) | lifts | forced by |
|---|---|---|---|---|
| **The archive** | the database, built by upsert | verbatim append-only logs, database disposable | verbatim append-only logs, database disposable | that feed purges an outage hours after restoration; this one is patient, so the same design is inherited rather than derived |
| **The collector** | a cloud scheduler, twice a day | a Pi in the hall, every 30 minutes | a Pi in the hall, every 30 minutes | same |
| **An outage's start** | publication time, re-stamped; every duration a floor | the operator's own, back-dated by hours, and measured from | the operator's own, back-dated by **months**, shown and never measured | Rush and Lusk is dated 451.6 days before its first sighting, over polled days it was absent |
| **One event** | pins sharing a reference number | records merged on identical location and start time | one notice's listing, with same-poll reissues folded | no id in this feed either, but only one notice per station per machine, so merging is nearly free |
| **How big it is** | Census population in a 500 m circle | the operator's own customer count | there is no size | the feed carries no count of anything |
| **The grade** | person-hours availability, own thresholds | share restored inside 4 hours, the operator's published aim | share of watched days with no **lift** listed, own bands | electricity is regulated in public; water and lift availability are not |
| **Band calibration** | fitted against its distribution | set by arithmetic from a published target | calibrated to whole days, because the bar is days | at day granularity one bad day is already 96.8% |
| **What knocks the grade** | binary: health notices knock, discolouration does not | planned works excluded, storm days kept and stated | planned works excused a week then counted; escalators show on their own bar and do not knock | nobody excluded anything on our behalf, so every exclusion had to be argued twice: in, then back out |
| **What an outage means** | a boil notice is a boil notice | supply off is supply off | needs a station inventory that does not exist | no NeTEx, no SIRI-FM, no `pathways.txt`, no `wheelchair_boarding` |
| **The second source** | Census Small Areas, official and versioned | Census Small Areas, borrowed from the water site | a hand-typed CMS field, snapshotted monthly, and since 8 September a hand-recorded observation log beside it | the CMS field is the only machine-readable statement that exists, and its error rate is the ceiling on everything derived from it |

### The identical column

Some things all three do the same way, and they are the conventions worth carrying to a fourth
site:

- Raw responses written verbatim before any parsing, with sorted keys, so two machines' logs
  merge with `sort -u`.
- A window that ends at the last **successful** collection, never at the build clock, with the
  gap drawn as "no data".
- A failed run structurally unable to reach the code that closes records.
- Instants in the reader's wall-clock; machine stamps in UTC and labelled.
- A payload budget printed by every build and asserted by a test.
- Decisions written to `notes/` with the date, the numbers, and the alternatives that lost.
- One shared design layer, edited upstream and rolled out to all three.

## The settled decisions, in plain language

The repository keeps a table of things not to re-litigate. Translated out of its own shorthand:

- **The site measures how long a notice was listed**, not what Irish Rail says the outage
  began. Their date is printed as their claim.
- **A row is a station**, identified by its location code and named from the most recent notice
  about it.
- **Escalators are included and tagged**, never excluded, and since 28 August they get their own
  strip so a working lift is never painted by a broken escalator. Since 3 September that strip
  carries no weight on the letter: an escalator outage is visible everywhere except the grade.
- **A bar shows the stretches a notice was actually on the feed**, and a single missed poll is
  the feed blinking rather than an outage ending.
- **A notice reissued at the very poll the old one vanished is the same outage.** A gap of a
  poll or more is two.
- **Planned works are whatever the notice text calls planned works**, and they are excused for
  their first week and counted in full after it, in their own colour once they are.
- **A station's grade is lift availability**: days watched with no lift reported out, on this
  site's own A to F scale, because no Irish or EU target exists. It is not step-free
  availability either, because it counts notices rather than access, and a quarter of the
  access verdicts are unknown.
- **The scale runs A to F inclusive**, with E splitting the old F band at 50%, which lands in a
  real gap in the data.
- **Irish Rail's end date is printed while the notice is up and dropped once it comes down**,
  and plays no part in any measure.
- **Windows end at the collection horizon**, and a notice listed for zero minutes still counts
  in its month.
- **"and" in the station prose is a sequence, not a choice**, so a lift out removes step-free
  access unless one of two reviewed exceptions applies.
- **An escalator is not step-free**, so its outage removes no step-free access. It does remove a
  way up for anyone who finds stairs hard, and the site says so in those words. The one shape
  that should still knock the grade, an escalator at a station whose page claims no lift, has no
  instance and is written down with a test that fails the day it appears.
- **Which leg a notice is about is read from the notice's own text**, and each leg is read
  against its own field.
- **OpenStreetMap was carried and removed** on measurements: it changed no verdict.
- **NeTEx is the one thing worth watching for.** Every other source is checked and closed.
- **A hand-recorded fact is admissible if it carries provenance, expiry and an audit trail.**
  This reverses the 29 August decision to curate nothing by hand, which objected to a *file*
  rather than to the method.
- **How reliable the derivation is has its own dated section**, by class of claim, including
  the classes that are untested.

## Notes

- Corpus figures measured 12 September 2026 by rebuilding `../lifts-data` and running the site
  build and `python -m lift_access report`. All registered in `figures.md`.
- The settled-decisions list is a plain-language rendering of the table in `CLAUDE.md` §
  Settled - don't re-litigate without reading the note, whose rows point at `notes/site.md`,
  `notes/station-access.md`, `notes/publish-cadence.md` and `notes/step-free-graph.md`.
- Continued in **17b**, which carries the moral and the glossary.
