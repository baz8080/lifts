# 10. Closing: three feeds, three sites, one discipline
*~11 min read · the whole series · 31 August 2026*

*Where we are:* the end. What the site can say, what it cannot, where it differs from its two
siblings and why, and a glossary of every idea the series boxed.

## The question, answered

**Which Irish Rail stations have lifts out of service, and for how long?**

As of 31 August 2026, over 23 days of collection, 1,084 runs and 234 recorded notices:

- **24 outages across 21 stations.** 6 planned works, 2 escalators.
- Aggregate availability across the stations named in August: **67%**. That is the share of
  watched days on which nothing was reported out at those stations.
- Grades across 21 station-months: **A 1, B 1, C 5, D 5, E 4, F 5.**
- Listings ran from 6.5 hours (Portarlington) to 541.5 hours and still going (Athy and
  Midleton). The median was about 62 hours.
- Four lift notices were still up at the last poll, at four stations.
- **16 of the 24 outages removed step-free access** to at least one platform, as worked out
  from Irish Rail's own station pages. 2 were escalators. **6 are unknown**, because the two
  hand-written sources disagree.

Twenty-three days is not a season and none of these numbers should be quoted as a fact about
Irish Rail. They are a fact about twenty-three days, which is the honest scope, and the site
says the collection start date on every page.

## What the site can say

- **How long a notice was listed**, to the resolution of a 30-minute poll, over a window whose
  boundaries are recorded runs rather than a clock.
- **Which stations were named**, keyed by location code, named from the newest notice.
- **How much of a month a station spent with something reported out**, as a share of days
  actually watched, and a letter for that share on a scale it declares as its own.
- **Whether a notice was a fault or planned works**, from the notice's own words, and how long
  works ran past a week of grace.
- **What Irish Rail claims the start date was**, printed as their claim and used for nothing.
- **What an outage did to step-free access**, worked out from Irish Rail's own station page,
  labelled as an inference, with a link inviting correction.
- **How many stations have a lift**: 57 of 152, from a versioned snapshot.

## What it cannot

- **Say anything is "fixed".** There is no completion signal. A notice stops being listed, and
  that is all that is known.
- **Say how many lifts a station has**, or whether the one named was the only one. A notice
  names one machine in prose.
- **Say a station is accessible.** It can say Irish Rail's page names a step-free way to a
  platform that does not use the lift, at two stations in the country. That is a much smaller
  claim and the site's wording stays inside it.
- **Give a network availability figure.** The denominator is the stations named that month,
  because the feed names a station only when something is wrong with it, and the page says so.
- **Distinguish who an escalator outage affected.** Open as issue #33.
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
| **The grade** | person-hours availability, own thresholds | share restored inside 4 hours, the operator's published aim | share of watched days with nothing listed, own bands | electricity is regulated in public; water and lift availability are not |
| **Band calibration** | fitted against its distribution | set by arithmetic from a published target | calibrated to whole days, because the bar is days | at day granularity one bad day is already 96.8% |
| **What knocks the grade** | binary: health notices knock, discolouration does not | planned works excluded, storm days kept and stated | planned works excused a week then counted; escalators knock, and that is open | nobody excluded anything on our behalf |
| **What an outage means** | a boil notice is a boil notice | supply off is supply off | needs a station inventory that does not exist | no NeTEx, no SIRI-FM, no `pathways.txt`, no `wheelchair_boarding` |
| **The second source** | Census Small Areas, official and versioned | Census Small Areas, borrowed from the water site | a hand-typed CMS field, snapshotted monthly | it is the only machine-readable statement of what an Irish station has |

### The identical column

Some things all three do the same way, and they are the conventions worth carrying to a fourth
site:

- Raw responses written verbatim before any parsing, with sorted keys, so two machines' logs
  merge with `sort -u`.
- A window that ends at the last **successful** collection, never at the build clock, with the
  gap drawn as "no data".
- A failed run structurally unable to reach the code that closes records.
- Instants displayed in the reader's local wall-clock; machine stamps in UTC and labelled.
- A payload budget printed by every build and asserted by a test.
- Decisions written to `notes/` with the date, the numbers, and the alternatives that lost.
- A shared design layer edited in one place and rolled out to all three.

## The settled decisions, in plain language

The repository keeps a table of things not to re-litigate. Translated out of its own shorthand:

- **The site measures how long a notice was listed**, not what Irish Rail says the outage
  began. Their date is printed as their claim.
- **A row is a station**, identified by its location code and named from the most recent notice
  about it.
- **Escalators are included and tagged**, never excluded, and since 28 August they get their own
  strip so a working lift is never painted by a broken escalator.
- **A notice reissued at the very poll the old one vanished is the same outage.** A gap of a
  poll or more is two.
- **Planned works are whatever the notice text calls planned works**, and they are excused for
  their first week and counted in full after it, in their own colour once they are.
- **A station's grade is availability**: days watched with nothing reported out, on this site's
  own A to F scale, because no Irish or EU target exists. It is not step-free availability.
- **The scale runs A to F inclusive**, with E splitting the old F band at 50%, which lands in a
  real gap in the data.
- **Irish Rail's end date is printed while the notice is up and dropped once it comes down**,
  and plays no part in any measure.
- **Windows end at the collection horizon**, and a notice listed for zero minutes still counts
  in its month.
- **"and" in the station prose is a sequence, not a choice**, so a lift out removes step-free
  access unless one of two reviewed exceptions applies.
- **An escalator is not step-free**, so an escalator outage removes a convenience rather than
  access. The grade weighs them the same, so the two disagree, and that is open rather than
  settled.
- **OpenStreetMap was carried and removed** on measurements: it changed no verdict.
- **NeTEx is the one thing worth watching for.** Every other source is checked and closed.

## What I would tell someone starting the fourth one

The other two series each end with a sentence. The water site's is about approximating
carefully. The power site's is *collect first, interpret later, keep the bytes*.

This one is different, and it is the thing I did not know three weeks ago:

> **Collect first, and publish no meaning you cannot source.**

Collecting is the easy half and it is where all the discipline usually goes: write the bytes
down, never edit them, make the interpretation disposable. That machinery worked here on day
one, inherited from a sibling, and it never once let me down.

What it does not do is tell you what any of it means. A perfectly recorded observation that
"the lift at platform 2 is out of service" is worth very little until you know whether platform
2 has another way up, and that is a fact about the world rather than about your pipeline. No
amount of care with the bytes creates it.

And in Ireland, for rail station accessibility, nobody has created it. Not because anybody was
careless: the European standards for it exist, the regulation that would compel it carries a
clause that exempts data you do not already hold, and the obligation is therefore satisfied.
The gap is lawful. Five major mapping products have run into the same wall and fall back to
crowd-sourced pins. The only machine-readable statement of what an Irish rail station has is a
free-text field somebody types into a CMS, and reading one conjunction in it the wrong way
would have told a wheelchair user that access was fine at a station where it was gone.

So the second half of that sentence is where the work went. Say "unknown" a quarter of the
time. Publish the derivation as an inference and link a way to correct it. Default every error
to the direction that wastes a journey rather than strands one. Refuse to write a parser where
a reviewed list of two entries is the true claim. And when the number on the front of the page
starts answering a question you did not ask it, write the issue with the measurements in it
rather than adjusting the number quietly.

## Glossary

Every concept boxed in the series, in order of appearance.

| Concept | Chapter | In one line |
|---|---|---|
| Source of truth against derived index | 01 | The log is what was observed; the database is what it currently means, and only one of them is disposable |
| A run that failed is not a run that saw nothing | 01 | "I could not ask" must never be recorded as "there was nothing there", or every open outage closes at once |
| Measure the window you actually watched | 02 | Colouring days nobody observed publishes an observation nobody made, and it looks identical to a real one |
| Two clocks for one date is a bug in either direction | 02 | If the bucket boundary and the printed label come from different time zones, no reader can tell which one the total believes |
| An empty dependency list as a deployment contract | 03 | Keeping `dependencies` empty is what lets the collector install on a Pi by copying a directory |
| A scale with no anchor | 04 | With no published target to grade against, an absolute scale of your own, stated as such, beats a relative one or a borrowed one |
| A band calibrated in the unit the bar is drawn in | 04 | If the bar shows days, the cuts must land on whole days, or the grade claims a precision the data lacks |
| One colour, two meanings | 05 | A mark that covers two cases a reader would distinguish is not wrong, it is silent |
| A cut that lands in a real gap | 05 | A threshold chosen for being memorable is fine if the data has empty space on both sides of it, and that is checkable |
| A National Access Point, and a lawful absence | 06 | The duty is to publish what you hold, not to create it, so the missing data has no process that fills it |
| The safe direction of an error | 07 | Telling somebody access is gone costs a wasted check; telling them it remains strands them |
| An inference that expires with its source | 07 | When a claim's evidence is reworded away, retract the claim rather than inverting it |
| A guard that passes because what it checks is absent | 08 | Ask every guard what it asserts when the input is missing entirely; if the answer is "success", it is over the wrong quantity |
| One number, two populations | 09 | A single letter cannot answer two audiences whose honest answers differ, and the fine print is not what people read |

## Notes

- Corpus figures measured 31 August 2026 by rebuilding `../lifts-data` and running the site
  build and `python -m lift_access report`. All registered in `figures.md`.
- The settled-decisions list is a plain-language rendering of the table in `CLAUDE.md` §
  Settled - don't re-litigate without reading the note, whose rows point at `notes/site.md` and
  `notes/station-access.md`.
- The sibling closings: uisce series ch 17, esb series ch 8.
