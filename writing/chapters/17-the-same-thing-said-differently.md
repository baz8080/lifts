# 17. The same thing, said differently
*~9 min read · PRs #55, #56 · 18 to 24 September 2026*

*Where we are:* chapter 16 filed two bugs, both found by pointing a second reader at the same
data. Both are fixed now, and neither fix is the one the issue proposed. Re-measuring for this
chapter turned up a third thing. It is not a bug, and nothing on the page mentions it.

## The question that opened this stretch

Chapter 16 said #53 was a question about what the planned-works grace is *for*, rather than
about a regular expression. It was answered as a question about vocabulary. Was that a dodge?

## What changed

### Three words for one claim

PR #56, merged 18 September, turned `PLANNED_MARKER` into `PLANNED_MARKERS`: "planned works",
"planned maintenance" and "engineering works". The note gives the reason in one sentence. They
are the same claim in different words. The delays site's cause reader already put all three in
one category, and the corpus carries all three.

To decide whether that dodges chapter 16's question, go back to what chapter 04 said the grace
is for. *A week is a plausible maintenance window, and because Irish Rail's own end dates are
placeholders, the listing is the only measure of how long works actually ran.* The grace is not
a reward for a phrase. It is a concession to a kind of event: the operator took the lift out on
purpose, for a job with an end. Maintenance is that kind of event, and so are engineering works.
The vocabulary answer and the purpose answer turn out to be the same answer. It would have been
a real question about purpose if the new wording had described a different event, and none of
the three does.

So chapter 16 made #53 sound more open than it was. That is worth saying, because the
temptation after a bug found sideways is to treat it as deep.

> **Concept: a literal string is a vocabulary of one.** A test for a phrase is really a test
> for how one person typed a claim once. It cannot fail. It can only decline to match, and it
> declines silently. The fix is not a cleverer pattern. It is to let the corpus act as the
> dictionary: list every wording the data actually carries for the claim, and widen to exactly
> those. After widening, the list is still closed, and the next synonym will be as invisible
> as the first one was. That is why a second reader over the same data matters. It was the
> only thing that noticed the first time, and it is the only thing that will notice the next.

### Worked example: Salthill and Monkstown in September

As of 24 September the station has two notices and one reissue on record:

- *"The Lift on platform 1 is currently out of service due to planned maintenance."* Listed
  11 September 13:32Z to 15 September 14:32Z, which is four days and an hour.
- *"The Lifts on platforms 1 and 2 are currently out of service due to planned maintenance."*
  Listed from 16 September 14:01Z. At 09:01Z on the 17th, in the same poll that it vanished, a
  fault notice for platform 1 appeared with no cause given. Chapter 02's rule folds a reissue
  in the same poll into one outage, and that outage came down at 23:02Z, which in Dublin is two
  minutes into the 18th.

September had 24 days watched by the horizon. Under the old marker, every listed day counted:
the 11th to the 18th, eight days, so 16 of 24 were available. That is **66%, an E**. Under the
new one, each maintenance notice ran well inside its week and costs nothing, and only the
fault's two Dublin days count, which leaves 22 of 24. That is **91%, a C**.

That is two bands for one word. It moved nothing else: across September's 30 station-months the
national figure is 85% either way, planned notices go from 3 to 4, and one C replaces one E.

One more detail from that reissue. Its head, the line the overview's rows are built from, read
*"Station - Lift out of order"*, with the word "Station" where the station's name belongs. The
site still printed "Salthill and Monkstown", because a row takes its name from the notice's list
of stops and uses the head only when that list is missing. A row is named from its newest
notice. If the name had come from the head, the overview would have renamed Salthill and
Monkstown "Station" at 09:01 that morning.

### A code that was a name

PR #55, also 18 September. Chapter 16 followed issue #52 in saying that Kishoge's code field
was "missing or unparseable", so the loader had fallen back to the station's name. The fix found
that this was not what happened. Irish Rail's page for Kishoge publishes the name, `"Kishoge"`,
in the field where every other page publishes a five-letter code. Nothing fell back to anything.
The loader read exactly what the page said. Chapter 16 repeated the issue's diagnosis without
checking it, and the correction lives here rather than being edited into that chapter.

The issue offered two fixes: validate the code against the known code space, or refuse the
record. Neither shipped. What shipped is a table, `STATION_CODE_FIXUPS`, with one entry keyed by
the page's slug. It was checked by hand against a real notice in the corpus, whose location code
is `KISHO` and whose stop name is "Kishoge".

Measured on 24 September, the feed has named 76 distinct location codes since 8 August. With the
table, all 76 join to a station record. Without it, 75 do. The one that misses is Kishoge's, and
it has appeared exactly once, on a delay notice (*"Delays of up to +15mins"*). There is still no
lift notice there, so the fix changes nothing a reader can see today. What it prevents is a
silent miss on the day there is one.

This is the second hand-maintained constant in the access code, after chapter 07's list of two
reviewed step-free alternatives, and it has the same shape: a human decision, made in a diff,
with the evidence in the pull request. What it lacks is a guard. If another page puts a name in
the code field, that station will miss in the same silent way, and the comment the fix left in
`survey.py` says as much: *"a fixed page bug is not a promise every code stays clean."* Chapter
13's tripwire is the shape that would catch it: assert that every code in the snapshot looks like
a code, or that every code the feed names joins. Today neither assertion exists.

## Found while measuring: August moved

Re-measuring for this chapter, August's national figure came back as **75%**. Chapter 16 and the
closing had quoted **76%**, and today's grade mix has one more D and one fewer A. August ended on
the 31st, and nothing about August's lifts can have changed since.

To tell a code change from a data change, the corpus was cut at the morning of 12 September and
rebuilt with today's code. The result was 76% and three A grades, exactly as quoted then. Today's
code on today's corpus gives 75% and two A grades. So the data moved it, and exactly one
station-month changed: **Tullamore, August, from A at 100% to D at 83%.**

Tullamore's notice, *"Lifts are temporarily unavailable due to planned works"*, was first seen on
28 August at 15:01Z and came down on 1 September at 09:02Z. That is three days and eighteen
hours, inside the week, so its four August days cost nothing and the month graded A. On 16
September at 14:01Z **the same notice came back**, with the same head, the same station and the
same start date Irish Rail claims. By chapter 01's identity it is one notice. It is still listed
at the horizon.

Chapter 10's pooling adds a notice's planned stretches before anything is spent. By the
arithmetic, the total crossed seven days at about 20:00Z on 19 September. From the next poll,
every listed day of the notice counted, **including the four in August**, and 20 of 24 watched
days is 83%. August's letter changed nineteen days after August ended. No page, feed or file
says it changed.

It is not a bug. The rule is doing exactly what chapter 10 built it to do, and the code's own
docstring anticipates a milder version of this: *"a fortnight of works spanning a month end
counts in both halves"*. The case that motivated pooling was Pearse's four-hour blink. Tullamore's
gap was fifteen days, and the rule does not look at the gap. Whether works fifteen days apart are
"the same works" is a question the notice itself answers. Irish Rail reissued it with the same
claimed start, 31 August, so by its own words it is one job.

What is new is what this means for the page. A month that has ended is presented as history,
and a reader who noted Tullamore's A for August on the 19th would find a D on the 20th, with no
mark saying the month was revised.

> **Concept: a property of the notice, published as a property of the month.** A month on a
> status page reads as settled. If any number in its grade is computed over something that
> outlives the month, such as a notice's running total, a correction or an average, then the
> month's figure depends on the future too. That is not wrong in itself. It is wrong when the
> page presents the figure as final. The check is to ask, of every number on a past month's
> card, what could still change it. If the answer is not "nothing", then either the number is
> provisional and should say so, or the computation should stop at the month's edge. Which of
> those is right depends on what the number is for, and that is a decision, not a fix.

The shapes are easy to list and hard to choose between. One is to say on the page that a month
stays provisional while any notice in it can come back, and with no completion signal (chapter
01) that means forever. Another is to freeze a month's letter when the month closes, which lets
the August card disagree with the rule applied to the same notice today. A third is to spend the
grace in time order, so the first week is always forgiven, which reverses chapter 04's
"including the first week" and moves other grades. All three belong beside chapter 04's argument
in `notes/site.md`, with these measurements. As of 24 September none is an issue yet.

## Where it left the site

Salthill and Monkstown's September is a C where it was an E, because a claim of planned work is
now recognised in the three wordings the corpus uses. Kishoge will join the day a lift notice
names it. And there is one measurement the page does not show: a past month's letter can move,
and it did.

The thread running through all three is sameness. Three phrases turned out to be one claim, a
name stood in for a code, and a notice that came back fifteen days later turned out, by its own
account, to be the same notice, which rewrote a month.

## Notes

- PR #56, "Treat 'planned maintenance' and 'engineering works' as planned works" (18 Sep 2026),
  closing issue #53: `lift_site/model.py` `PLANNED_MARKERS`, `notes/site.md` § Planned works
  (amended 2026-09-18), and the resolved paragraph removed from `notes/delays-site.md`.
- PR #55, "Fix Kishoge's station code join (issue #52)" (18 Sep 2026): `STATION_CODE_FIXUPS`
  in `lift_access/model.py`, the golden fixture regenerated, and the `survey.py` comment quoted
  above.
- Salthill and Monkstown's September grade under both markers, the national September figures,
  the 76-code join and Tullamore's two stretches were all measured 24 Sep 2026 against
  `../lifts-data` (horizon 2026-09-24T05:02:51Z), running `lift_site.model` with the marker
  tuple swapped. Registered in `figures.md`.
- The August comparison: raw logs to 2026-09-12 morning, rebuilt into a scratch directory with
  today's code, against the full corpus. Only Tullamore's August differs.
- The Tullamore crossing time is arithmetic, not an observed poll: 3 d 18 h 01 m before, plus
  the ongoing stretch from 2026-09-16T14:01:41Z, reaches seven days at about 2026-09-19T20:00Z.
- `lift_site/model.py` `day_marks` docstring, quoted for the month-end case.
