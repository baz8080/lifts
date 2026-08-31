# 02. The start date that is 451 days old
*~9 min read · PR #2 · 18 August 2026*

*Where we are:* the collector from chapter 01 has been running since 8 August and the log holds
every notice it saw. This chapter is the first site, and the decision that shapes every number
on it: what interval are we actually measuring?

## The question that opened this stretch

Each notice in the feed carries a `start` field. It looks like the answer to "when did this
outage begin", and using it would make the site trivial: colour the days from `start` to `end`,
count them, print a duration.

The first thing PR #2 did was check whether that field describes anything the collector saw.

It does not. Measured against all 24 outages on record as of 31 August 2026, **23 carry a start
that predates the poll they were first seen at, and 12 of those by a week or more**:

| station | Irish Rail's start predates the first sighting by |
|---|---|
| Rush and Lusk | 451.6 days |
| Docklands | 253.4 days |
| Dublin Pearse (lift) | 242.9 days |
| Hazelhatch and Celbridge | 237.6 days |
| Thurles | 197.4 days |
| Dublin Pearse (escalator) | 146.1 days |
| Ballinasloe | 123.9 days |
| Skerries | 118.5 days |
| Ballybrophy | 100.5 days |

Rush and Lusk is the one to sit with. Irish Rail's notice dates the outage from 14 May 2025.
The notice was present at the very first poll this project ever made, at 21:30 on 8 August
2026, which means all 451 of those days precede collection entirely. Nobody observed anything
at Rush and Lusk in May 2025, because nothing was watching.

Docklands and Hazelhatch make the same point from the other side, and more sharply, because
there the absence was observed. Docklands' notice is dated 3 December 2025 and first appeared
at 10:30 on 13 August 2026, five days into collection. Hazelhatch's is dated 18 December 2025
and first appeared on 12 August, four days in. For those five and four days the feed was
queried 48 times a day and those notices were **not in it**.

There are two readings of any of them. Either the lift really has been out since the date on
the notice and Irish Rail only got round to publishing it, or somebody typed a date. Both are
plausible and the feed gives no way to choose. What is certain is which days were watched.

> **Concept: measure the window you actually watched.** A status site's honesty rests on the
> difference between "this was true" and "I saw this". Colouring 451 days of a bar because a
> text field claims them would publish an observation nobody made, and it would look exactly
> like an observation somebody did make: same colour, same bar, same page. So this site
> measures the **listing**: from the poll a notice was first seen at, to the poll it was first
> absent from. Irish Rail's start is still printed, as their claim, in their words ("Irish
> Rail's notice dates it from 14 May 2025, 451 days before it was listed"), and it colours
> nothing and enters no total. The claim is information. It is just not evidence about days
> nobody was looking.

One outage runs the other way, and it is worth naming because it is the exception that shows
the field is not simply broken. Tullamore's planned-works notice carries a start **2.3 days
after** it was first listed: works announced in advance, which is exactly what the field is
for. The field is not nonsense. It is a claim about the world, published at an unrelated time,
and the site treats it as one.

### The three-way split

This is the sharpest fork in the whole family of sites, and all three landed differently on
the same field for reasons in their own data.

| | what it does | why |
|---|---|---|
| **uisce** (water) | takes the notice's publication time and re-stamps it, so every duration is explicitly a **floor** | its feed gives no start at all; the earliest defensible instant is when the notice appeared |
| **esb** (power) | uses ESB's own `startTime` and **measures from it** | it was validated as immutable and back-dated by *hours* to the actual fault: 8 revisions in 1,460 records, and the median lag is about one poll |
| **lifts** | shows Irish Rail's start, **measures from the listing** | back-dated by *months*, over days that were watched with the notice absent |

Same-shaped field, three different treatments, and none of them is a preference. The power
site's start survives because it was checked and passed. This one's is shown because it was
checked and failed.

## What else the first site had to decide

### "No longer listed", never "fixed"

The word matters more than it looks. There is no completion signal in the feed (chapter 01), so
the only thing the site knows is that a notice stopped being published.

The pattern of publication makes it worse. Notices do not trickle in one at a time as lifts
break: they arrive and vanish in **batches**. Six were present at the very first poll. Three
more appeared together at 14:30 on 10 August, four at 10:30 on 13 August, two at 14:02 on
17 August. Three were removed in the same single poll on 14 August. Lifts do not break in
threes at 14:01 and they do not get repaired in threes either. That is somebody working through
a publishing queue.

So the site says "no longer listed" everywhere it would be tempting to say "fixed", and the
rule is written into the fixed vocabulary of this series for the same reason.

### A reissued notice is one outage; a gap is two

Chapter 01's derived identity comes back to bite here. Because identity is `head` plus codes
plus `start`, an edited head or a corrected start looks like one notice closing and another
opening **in the same poll**.

The site folds those: `merge_edits` joins a same-station, same-kind successor whose first
sighting is exactly the predecessor's closing instant. Exactly, on the run timestamp, not
within a tolerance. If a notice comes back a poll or more later it stays a separate outage,
because that gap is information: Docklands closed at 14:01 on 14 August and a new notice
appeared at 14:02 on 17 August, three days apart, and those three days are days the lift was
not reported broken. Two notices open at once at one station never merge either, since the
older is still listed when the newer arrives.

No lift notice has needed the merge yet. Non-lift ones have: `Station currently closed` became
`Station currently CLOSED` became `Station is OPEN`, three ids in a row.

### `end` is shown, not used

For most notices `end` is a placeholder near the end of the calendar year. A handful look real.
Too few to trust, so it is printed as "listed end 30 Dec 2026" and plays no part in anything
measured.

It later grew one rule, in PR #18: the listed end **disappears when the notice does**. On a
notice that has come down, "listed end 30 Dec 2026" reads as though the works were still
running, which is exactly how Dublin Pearse's closed lift notice read. The notice coming down
is the completion signal; a placeholder that outlived its notice is noise.

### Two clocks for one date

The last decision of this chapter is the one that came from a bug rather than a measurement.

Irish Rail's start is a Dublin wall-clock time with no offset. "Since 5 May, 00:00" rendered in
UTC becomes "4 May, 23:00", which misquotes them by an hour for half the year. So every instant
a reader sees is rendered in Europe/Dublin.

That was done first for the printed timestamps and not for the day buckets, and the two
conventions promptly disagreed. Bucketing by UTC date while printing Dublin wall-clock splits
them for four hours a day in summer: a notice first seen at the 23:15 UTC poll on 31 August lit
the 31 August cell while its own summary line read "first listed 1 Sep 2026, 00:15", and at a
month boundary it was filed under August and missing from September entirely.

> **Concept: two clocks for one date is a bug in either direction.** It is tempting to think of
> this as a rendering detail, but a date is a bucket as well as a label. If the bucket boundary
> and the printed label come from different time zones, then for a few hours a day the site
> shows a cell in one month and a sentence about another, and no reader can tell which one the
> total believes. There is no version of this that is only cosmetic. The fix is to pick one
> convention for everything a reader can see, which here is Dublin, and to say so where the
> remaining UTC stamps are (the build time and the collection horizon, both machine facts).
> It has a real cost: a month is no longer a whole number of days, since March is 23 hours
> short and October 25 long, so the cell count comes from the calendar and never from
> subtracting two instants. Durations are computed once from offset-aware instants and shipped
> with the record, rather than recomputed from rendered strings that carry no offset, because
> subtracting those loses the hour at the October change, and did.

### The window stops at the horizon, not at the build clock

Taken straight from the power site. The site's window ends at the last run whose outcome was
`ok`, not at the moment the page was built. Days between the two are drawn as "no data", never
as "nothing listed", because the difference between "we looked and saw nothing" and "we did not
look" is the whole of chapter 01.

## Where it left the site

A page of stations with day bars, an initial payload of 30 KB against a self-imposed 500 KB
budget, and every measured interval anchored to something somebody actually observed. The
overview listed the 15 stations with a notice in August; a station's own page carried every
month since collection began.

What it did not have was any way to say whether five days listed was bad. That is chapter 04.

## Notes

- PR #2, "Add a static status site for the collected lift data" (18 Aug 2026): the measured
  interval, the batch-arrival evidence, the reissue rule, `end` as a placeholder, the Dublin
  wall-clock decision, the 30 KB payload.
- `notes/site.md` §§ The measured interval is the listing, "No longer listed" is the word,
  Notices reissued in the same poll are one outage, `end` is shown not used, Displayed instants
  are Dublin wall-clock, Windows end at the collection horizon (all 18 Aug 2026).
- `notes/site.md` § Irish Rail's end date goes when the notice does (28 Aug 2026).
- Lead times re-measured 31 Aug 2026 against `../lifts-data`: 23 of 24 outages have a start
  predating their first sighting, 12 by seven days or more, maximum 451.6 days (Rush and Lusk),
  minimum minus 2.3 days (Tullamore). At PR #2 the same measure read 14 of 17 and 12 of 17.
- The power site's `startTime` validation: esb series ch 3 (`notes/grading.md` "Does startTime
  drift?", 18 Aug 2026). The water site's floors: uisce series ch 3.
- Diagram: `diagrams/listed-not-started.svg`.
