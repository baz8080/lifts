# 11. The grade narrows to lifts
*~8 min read · PRs #38 and #43 · 1 to 3 September 2026*

*Where we are:* chapter 09 set out four open questions. This chapter closes two of them, and
the order they closed in is the point: the answer to the small one is what made the big one
possible.

## The small one first, because it unlocked the other

Issue #28 was the least interesting thing on the list. Two bars on a row, and nothing visible
saying which was the lift and which the escalator. The accessible label said it and the day-cell
caption said it on hover, neither of which a phone shows at rest.

It had been tried once, on 28 August, and reverted. A 64px text label appeared on the one
station that had two bars, which shortened that station's bar and put its day 14 over every
other row's day 15. The whole overview stopped lining up because of one label on one row.

The fix is one sentence: **reserve the column on every row, whether or not there is anything to
put in it.** Every bar now sits in a wrapper whose first column is a fixed 15px carrying a
glyph, a lift or an escalator icon. On a station page, where the bars are tall, the glyph keeps
its word beside it in an 84px column. Measured across the August overview, all 21 rows now
start their day cells at the same horizontal position at both 980px and 500px, paired and
unpaired alike.

> **Concept: a conditional column is a misalignment.** A layout element that appears only where
> it has content is invisible on the rows that lack it and disruptive on the row that has it,
> and the disruption is comparative: it does not make that row wrong, it makes every *other*
> row wrong relative to it. Reserving the space unconditionally costs 15 pixels on every row
> and buys back the property the grid exists for, which is that the same day is at the same
> place on every line. Nothing about the first attempt was wrong except that it was
> conditional.

The two other rejected shapes are worth a line each, because both would have reintroduced
older bugs. **One merged bar on the overview, split only on the drill-down** is exactly the bug
the split exists to fix: at Pearse on 13 August the lift came back and the escalator did not,
and a merged cell paints a working lift as broken. **An automatically sized label column on
station pages** would size to "Lifts" on one month card and "Escalators" on the next, and the
bars would step sideways down the page.

The kinds became their own legend key beside the day key, which is what closes the loop: the
day key still names no kind, so the two cannot drift.

## The big one: Pearse's F

Chapter 09's sharpest open question was this pair of statements, both true, both on the same
page:

> **F · 20% available**

> *An escalator is moving stairs, so it was not a step-free route to begin with and its being
> out did not remove one.*

Pearse's F was entirely escalator-driven. One letter was answering two questions for two
populations, and the chip is what people read.

### Why lifts-only was possible now and had not been on 29 August

This is the part I like. Chapter 05 records the decision to count escalators in the grade, and
what killed the alternative was a specific reader experience: Dublin Connolly reading **A /
100%** directly above two red cells, with nothing on the row saying whose those cells were.
That was not an argument about what a grade should measure. It was an argument about what a
reader could resolve.

Issue #28 removed it. Since every bar carries its kind glyph in a fixed gutter, and the kinds
are their own legend key, red escalator cells under a green lift chip read as two facts about
two machines rather than as a contradiction. **The objection was about the row, and the row
changed.**

So the grade is the lift bar's alone. The escalator keeps its own bar, its colours and its
count on the summary tiles, and paints nothing on the letter. The overview sort is unchanged:
any notice up leads, so a station whose lift is fine and whose escalator is out sits at the top
of the page with an A beside a red strip, which is the correct shape for exactly that
situation. Tara Street is doing it right now.

### The key says "Lift availability", not "step-free availability"

Issue #32 proposed the latter and the pull request refused it, and the refusal is the most
careful thing in this chapter.

The grade counts **notices**, not access. A lift out at Raheny or Cork still knocks it, though
Irish Rail's page names a ramp round that lift and chapter 07's reviewed exception list says so.
The seven of 30 verdicts that come back `unknown` knock it too, because the safe direction is
to count them. A name that promised step-free would claim precisely what `lift_access` spends
600 lines being careful not to claim.

A grade driven by the access verdict was considered and rejected on three grounds, all
practical: the site builds with no station snapshot at all, a quarter of the verdicts are
unknown, and the number would then move on a monthly scrape of somebody's prose rather than on
the feed.

### The numbers

Measured on the corpus to 3 September, after the listings split of chapter 10, which is why
they differ from the figures in issue #32:

| month | station | before | after |
|---|---|---|---|
| August 2026 | Dublin Connolly | C, 91% | **A, 100%** |
| August 2026 | Dublin Pearse | F, 20% | **A, 100%** |
| August 2026 | national, 21 stations | 72% | **76%** |
| September so far | Tara Street | F, 33% | **A, 100%** |
| September so far | national, 6 stations | 50% | **61%** |

Pearse and Connolly both come out at A over visible red escalator strips, which is the shape
chapter 05 called a contradiction and chapter 11 calls two facts. The difference between those
two readings is a 15px gutter.

### The case that should knock, written down and guarded

There is one shape where an escalator outage genuinely should count: **an escalator at a
station whose page claims no lift**. Stairs only, and that is a real loss for the people an
escalator is for.

No station is of that shape. Pearse, Connolly and Tara Street all claim a lift. So the rule is
in the note rather than in the code, and a real-corpus test fails the day it applies, with a
message telling the next person to build the rule rather than loosen the test. The review of
that branch caught the guard's first version testing for "the page says yes", which would have
misdiagnosed a station simply missing from the snapshot as the only-powered-way-up case; it
fails only on a page that positively claims no lift, and a missing station is a different test's
problem.

> **Concept: a rule with no instance, written down and guarded.** There are three things you can
> do with a case the data does not currently contain: code it speculatively, ignore it, or state
> it and set a tripwire. The first invents behaviour against no example and is how the wrong
> abstraction gets built. The second means the day it arrives, nothing notices. The third writes
> the rule in prose where the reasoning is, and adds a test that fails when the case appears
> with an error message saying what to build. The test is not testing the rule, because there is
> no rule to test. It is testing the *premise* the absence of the rule rests on.

### One decision a review turned up that nothing had recorded

The headline denominator is still the stations named that month, so a station with only an
escalator notice sits in it at 100% lift-available. A reviewer asked whether that pads the
number, which was a fair question that nobody had written an answer to.

Narrowing to stations with a lift notice gives 75% instead of 76% for August, and 53% instead
of 61% for September so far. It was kept, on the grounds that the tile says "across the stations
named this month" and the overview lists exactly those stations, so the headline stays the sum
of the rows a reader can see. The denominator refused back on 28 August was *every station on
the network*, which would have been invented; a station the feed did name is not.

### What makes it honest rather than a dodge

Taking escalators off the letter without saying anything else would be a real loss. The people
an escalator serves would go from being counted wrongly to not being counted at all.

That is why issue #32's own text said the fix should land with issue #33, and why this pull
request shipped saying "#33 stays open and is what makes this honest rather than a dodge". It
landed ten hours later. That is chapter 12.

## Where it left the site

A letter that means one thing for one population, a bar that says which machine it is about, and
an escalator outage that is visible everywhere except in the grade. As of 4 September the August
grade mix is A 3, B 1, C 4, D 6, E 5, F 2 across 21 station-months, and September so far is
A 2, D 3, E 1, F 2 across 8.

## Notes

- PR #38, "Say which bar is lifts and which is escalators" (1 Sep 2026), closing issue #28: the
  fixed gutter, the alignment measurement, the three rejected shapes, the six review findings
  including three tests that passed with the feature removed, and the MDI glyph licensing.
- PR #43, "Grade on lift availability, and let an escalator notice paint its bar alone"
  (3 Sep 2026), closing issue #32: the reversal, the "Lift availability" naming, the numbers
  table, the only-powered-way-up rule and its guard, the denominator decision, and the four
  rejected alternatives.
- `notes/site.md` § The grade is lift availability, and an escalator notice stops knocking
  (3 Sep 2026). The 29 August section is marked reversed in place; the lifts-only rule under
  One bar per kind is marked reinstated.
- Grade figures re-measured 4 Sep 2026 against `../lifts-data`. The before/after table is from
  PR #43, measured 3 Sep 2026 on the corpus to 05:00Z.
- Verdict counts (7 unknown of 30) measured 4 Sep 2026 by `python -m lift_access report`.
