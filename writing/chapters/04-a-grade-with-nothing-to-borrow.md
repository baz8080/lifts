# 04. A grade with nothing to borrow
*~9 min read · PR #18 · 28 August 2026*

*Where we are:* the site shows day bars anchored to observed listings (chapter 02) in a shared
design (chapter 03). Every row ends in a raw count, and this chapter is about why that count
says nothing.

## The question that opened this stretch

Each overview row ended with "**5** days listed".

Five is not an answer. Is five bad? Five days out of a 31-day August is one thing; five out of
the 20 days collected so far is another; and the two cannot be compared by the number five. A
reader who wants to know whether a station is doing badly has to do arithmetic the site already
has the inputs for.

The obvious fix is a grade. The sibling sites both have one, and the obvious way to build one
is to grade against the standard the operator publishes. That is exactly what the power site
does: ESB Networks' Customer Charter states an aim anyone can read, "restore supply within less
than 4 hours in 95% of cases", so an A on that site means the operator met its own promise and
the anchor is not the author's.

So: what is the equivalent for lifts?

## What changed

### There is no target, and looking for one is the work

This was checked properly, because a decision recorded ten days earlier had said *no grade*,
partly on the grounds that no operator standard exists. Reversing a settled decision means
re-testing the reason it was settled.

- **The PRM TSI**, Regulation (EU) 1300/2014, is the European rulebook for accessibility of
  rail for persons with reduced mobility. It sets design rules for lifts and escalators, and it
  places an operational duty on the station manager to hold a written policy ensuring access
  "at all operational times". A duty to have a policy. No percentage, no reporting obligation,
  nothing a passenger can check.
- **Irish Rail's Passengers' Charter** promises "every effort ... available as advertised".
- **The Big Lift**, an NTA-funded programme that put lifts into 52 stations between 2020 and
  2024, publishes no availability figure.

The regulators who do publish numbers are in other countries. Britain's ORR and Network Rail
report lift faults in the tens of thousands (8,696 in a year, 6.6 per lift, over 20 hours
average repair). Transport for London has historically reported 93.7% lift availability, or
98.8% excluding planned works.

So there is nothing to borrow. The scale has to be this site's own, and the page has to say so
rather than dressing it up as a standard.

> **Concept: a scale with no anchor.** A grade is a compression: it turns a measurement into a
> letter so a reader can compare things at a glance. What makes a letter meaningful is what it
> is anchored to. The power site's A is anchored to a promise ESB published, so an A is
> checkable against a document. This site has no such document, which leaves two bad options
> and one acceptable one. A **relative** scale, where the worst stations get the F, always
> fails somebody by construction and moves under the reader as other stations change. A scale
> borrowed from **another country's** operator sounds rigorous and is not, for reasons the next
> section measures. What is left is an absolute scale of the author's own devising, stated
> plainly as such, with cuts chosen so a reader can reconstruct them by counting. That is
> weaker than an anchor and it is honest about being weaker, which is the trade.

### The bands are counted in days, because that is what the bar is drawn in

The first attempt borrowed TfL's numbers. It was tried on paper and thrown away in one step,
because of an arithmetic property of day-granularity data that is easy to miss.

This site colours **days**. It does not know the hour a lift came back, only which polls a
notice was present at, and the bar shows one cell per day. Over a 31-day month, a station
listed for exactly one day is 30/31 available, which is **96.8%**. A scale where 98% is the
target puts a station with a single bad day below the line, and every real station in the
bottom band.

So the bands are calibrated in the unit the reader can see:

| grade | availability | over a 31-day month |
|---|---|---|
| A | 100% | nothing counted |
| B | 95%+ | one day listed |
| C | 90%+ | two or three days |
| D | 75%+ | up to a week |
| F | below 75% | more than a week |

(An E arrives in chapter 05, splitting F. Nothing above it moves.)

> **Concept: a band calibrated in the unit the bar is drawn in.** If the bar shows days and the
> grade shows a percentage, the two are the same fact in different clothes, and a reader should
> be able to get from one to the other by counting cells. That is only true if the cuts land on
> whole numbers of days at a plausible month length. Bands imported from an operator measuring
> hourly availability do not: they encode a precision this data does not have, and a percentage
> printed to one decimal beside a bar with one red cell in it is a claim about hours that
> nothing here can support. Availability is therefore floored rather than rounded, so 100%
> cannot round up from a day that counted, and hours-based availability was rejected outright
> even though it is more precise.

**Availability** is derived from the day bar itself: days watched with nothing counted against
them, over days watched. Deriving it from the bar rather than computing it separately means the
chip and the bar cannot disagree, which turns out to matter in chapter 05.

### Planned works get a week, and then they count

Planned works were masking the thing the site measures. They sit for months: of the 24 outages
on record as of 31 August 2026, 6 were planned works, and Midleton's had been listed
continuously since 12 August.

The rule that landed: **works listed seven days or less in total cost nothing; past that, every
listed day counts, including the first week.** A week is a plausible maintenance window, and
because Irish Rail's own end dates are placeholders (chapter 02), the listing is the only
measure of how long works actually ran.

The phrase "in total" is doing a great deal of work in that sentence, and review moved it
twice.

### Worked example: six days of works, then four of fault

Take one station with a ten-day story: six days of planned works, then the works notice comes
down and a fault notice goes up for four days.

- **Version 1, per segment.** The grace applies to each folded segment separately. A notice
  reissued every few days never exceeds seven days in any one segment, so a station could carry
  a month of works and grade A. This is exactly the reissue the merge from chapter 02 exists to
  fold, so it was a hole opened by the interaction of two rules that each looked fine alone.
- **Version 2, over the whole listing.** The grace is measured over the outage's entire
  listing, works and fault together. Ten days exceeds seven, so nothing is forgiven: all ten
  days count, availability is 0%, and the fault has reached back and charged the station for
  the maintenance week it had already earned.
- **Version 3, the planned segments summed.** The works ran six days, which is inside the
  grace, so they cost nothing. The fault's four days count. Six of the ten days are available,
  which is 60%.

Versions 2 and 3 both produce an F on the five-band scale, which is why this needed a
constructed example rather than a corpus case to see: the letter is the same and the number is
not, and the gap widens the longer the works run. Version 3 is what shipped, and the rule is
one sentence: what the works cost is measured on the works.

On today's corpus the grace forgives Dublin Pearse's five-day lift notice and Greystones' two,
and does not forgive Limerick Junction's ten days or Midleton's nineteen.

### The build-killer, and where it came from

Three code-review rounds ran over this branch. One of them found a bug that would have taken
the site down, and it is a good example of a class of bug this project keeps producing.

The day bar stops at the build clock. The availability window stops at the **collection
horizon**, the last successful run. Those are two different machines' clocks: the Pi collects,
GitHub Actions builds. When the two diverge, the bar can show a day that the window has already
excluded, so the count of days-with-something-listed exceeds the count of days-watched.
Availability goes **negative**, and the band lookup, which walks the table from A downwards
looking for the first cut the value clears, finds nothing and raises `StopIteration`.

Reproduced at 13 hours of skew on Midleton: 20 days observed against a window of 21, and an
availability of minus 5.

Two other review findings from the same branch are worth recording because they have the same
shape as the grace rule: a quantity computed over the wrong extent. The month list was built
from the build clock alone, so a collection horizon in a month the build clock had left dropped
that month's outages from the shards, the statistics and the headline. And the grade key
claimed "A - no days listed", when what A actually means is nothing *counted*, which is not the
same thing once works inside their grace are drawn on the bar and left out of the total.

That last one is a wording bug with real consequences: Tullamore ships at **A / 100%
available** with planned-works cells visible on its bar - two when the review found it, four as
measured on 31 August 2026. The key has to say "100% available" and not "nothing listed", or
the page contradicts itself in the reader's first glance.

### The three-way split

| | what anchors the grade | what it is measured on |
|---|---|---|
| **uisce** (water) | its own thresholds | person-hours: population inside a radius, multiplied by the hours a notice ran |
| **esb** (power) | ESB's published 4-hour / 95% charter aim | the share of fault-interrupted customers restored inside four hours |
| **lifts** | its own bands, and the page says so | the share of watched days with nothing reported out |

The water site had to invent a standard because Irish water is measured in public by nobody.
The power site did not have to invent one. This site had to invent one **and** had nothing to
build it out of: the feed carries no magnitude at all. A notice is listed or it is not. There
is no count of people affected, no count of lifts at a station, no severity. Days are the only
unit available, which is why the grade is counted in days and why the bands had to be
calibrated to them rather than to somebody else's percentage.

## Where it left the site

Every row carries a letter and a percentage, derived from the bar beneath it so the two cannot
disagree. Planned works are forgiven for a week and counted after it. The window ends at the
horizon and the letter is a claim about days that were watched.

And within 24 hours, a reader could look at Dublin Connolly's row and see a green A sitting
directly above two red cells. That is chapter 05.

## Notes

- PR #18, "Grade stations on lift availability, one bar per kind" (28 Aug 2026): the reversal,
  the standards search, the day-calibrated bands, the planned-works grace and its two wrong
  versions, the three review rounds including the skew crash, the payload change.
- `notes/site.md` §§ No grade (18 Aug 2026, marked reversed), The grade is availability
  (28 Aug 2026), Planned works are excused for a week (28 Aug 2026).
- Standards, all as cited in PR #18: PRM TSI (Regulation (EU) 1300/2014); Irish Rail
  Passengers' Charter; NTA Big Lift, 52 stations 2020 to 2024; ORR/Network Rail 8,696 faults,
  6.6 per lift, over 20 hours average repair; TfL 93.7% and 98.8% excluding planned works.
- The 96.8% arithmetic: 30/31, floored, over a 31-day month.
- Corpus figures measured 31 Aug 2026: 24 outages, 6 planned. Grace outcomes (Pearse 5 days,
  Greystones 2, Limerick Junction 10, Midleton 19) from `notes/site.md`, 28 Aug 2026.
- The skew reproduction (Midleton, 13 h, observed 20 against 21, availability minus 5) is from
  PR #18's review notes.
- Sibling grades: uisce series ch 8a and 8b; esb series ch 4b.
