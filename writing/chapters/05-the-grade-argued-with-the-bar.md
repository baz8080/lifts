# 05. The grade argued with the bar underneath it
*~10 min read · PRs #25 and #27 · 29 August 2026*

*Where we are:* every station row now carries a letter grade derived from its day bar
(chapter 04). This chapter is the day after, when a reader could see the letter and the bar
disagree on the same line.

## The question that opened this stretch

Dublin Connolly, on 29 August, read:

> **A · 100% available**

with two **red** cells sitting directly beneath it on the escalator strip.

The grade was lifts only, on what looked like sound reasoning: the lift is the step-free route,
so lift availability is the thing that matters. Escalators had their own bar, added the day
before precisely so a working lift would never be painted by a broken escalator.

Both halves were defensible and together they published a contradiction. No reader was going to
resolve "100% available" against two red cells in the site's favour.

## What changed

### Escalators count, and the grade becomes a smaller claim

The fix was to put escalator days into the pool. That is one line of arithmetic and a
paragraph of consequences, and the consequences are the interesting part, because counting
escalators means the grade can no longer be called what it was being called.

An escalator is moving stairs. A wheelchair user cannot use one: every operator prohibits it,
Irish Rail included, and it is a matter of the step geometry rather than a formality. So an
escalator going out of service **never removes step-free access**. It removes the easier route
for somebody who can manage stairs with difficulty, or who has a buggy, a stick or a suitcase.

If escalator days count, then the grade is not step-free availability. It is something weaker
and plainer:

> **Irish Rail reported something out at this station on this day.**

Vertical circulation degraded, not access lost. The legend says "Lift and escalator
availability", which is the honest label for that.

And the site could not honestly grade step-free access anyway, even if escalators were kept
out. A notice names one machine in prose ("the lift at platform 2") and there is no roll of how
many lifts a station has, so a lift notice coming down does not mean every lift at that station
works. Reserving the grade for lifts would have given it a name it could not live up to.

Two alternatives were weighed and both lost:

- **Lifts only, escalators visible but out of the letter.** More precise, and it was the
  position until that day. What killed it is Connolly: the contradiction above is worse than
  the imprecision below.
- **Two grades, a step-free one and a softer one.** The most honest of the three. It costs a
  second chip on every row and a decision about which one sorts the overview, which is out of
  proportion to a distinction this feed cannot support cleanly in the first place.

The bars still split by kind, for the reason they always did.

On the corpus that day the change moved aggregate availability from 70% to 66%: Connolly from
A to C, and Dublin Pearse from A to **F**, at 22%. Chapter 09 is about why that F is a problem
even though every step to it was correct.

### One colour said two opposite things

The same pull request fixed a second self-contradiction, in the bar rather than beside it.

Planned works were drawn in blue. All of them, forgiven or not. So Midleton, listed 19 days at
that point and grading 0% available, drew exactly the same blue as Dublin Pearse's six-day lift
notice, which cost nothing at all. One colour carried both "this is forgiven" and "this is the entire reason
this station is an F", and a reader comparing two blue bars had no way to tell which was which.

> **Concept: one colour, two meanings.** A legend is a promise that a mark means one thing.
> When the same mark covers two cases that a reader would want to distinguish, the legend is
> not wrong so much as useless: it is true of both, and true of both is the same as silent.
> The failure is easy to introduce because it happens between two changes, neither of which
> is wrong on its own: a colour is chosen for "planned works", and later a rule is added that
> forgives *some* planned works. Nobody revisits the colour. The check is to ask, for every
> mark on the page, whether two cells drawn the same way could lead a reader to two different
> conclusions about what happened.

Works past their grace are now **amber**, with their own key entry. Amber rather than a second
red, for two reasons: works that overran are not a fault and the notice text under the bar says
"planned works" either way, so recolouring them red would put two words and one colour in
disagreement, which is how this started. And at cell width a person with deuteranopia cannot
separate orange from the critical red.

Three shades can now share a day, so the rule for which one wins had to become explicit rather
than a comparison: a day cell takes the worst of what was listed on it, ranked fault, then
overrun works, then works inside their grace.

### The legend that keyed nothing

A smaller thing that is a good illustration of the same discipline.

Under the day key sat a second row: five colour swatches drawn from the grade chip fills. A
reader asking what they referred to was right to ask. A grade is read as a **letter**. The
colour behind the letter is reinforcement, and nothing else on the page is painted in it. So
the row was a key to a code the page does not use, sitting directly beneath a key where every
swatch does map to something in a bar.

It was rebuilt to carry the chips themselves, letter and all, which is the object a reader has
been looking at on every row. That fixed *what* it keyed without fixing *where* it sat: two
legend rows stacked above the list still read as one key with two halves, only one of which
maps to anything visible. So it moved into the footer, inside a "How the grade works"
disclosure, directly under the sentences that define availability and the works grace. The key
and its explanation are one thing. The static station pages carry their own copy rather than a
link, because a station page is where a search result lands and its chip has to be explicable
without a second page load.

### The scale grew an E

The band table ran A, B, C, D, F. Skipping E is an American convention and Irish Rail is not
American, so the letter was added (PR #27).

The interesting part is where to cut it. E splits the old F band and moves nothing else: every
cut from 100 down to 75 stays where it was, so no station-month graded A to D changes letter.

**50%**, because it is the same kind of number the other cuts are: a count of days a reader can
hold in their head. Availability is floor-divided, so over a 31-day month a floor of 50 makes E
8 to 15 days listed and F 16 or more. Up to half the month, against more than half.

### Worked example: the cut lands in a real gap

The arithmetic above justifies 50 as a *legible* number. It does not justify it as the right
place to put a boundary, and those are different claims. So the distribution was checked.

Over the 21 graded station-months in a rebuild of the corpus, the old F band held nine values:

```
0, 0, 18, 22, 22, 50, 68, 68, 72   (per cent available)
```

There is a real gap between 22 and 50, and the cut lands in it. E takes the four stations
listed for part of the month; F keeps the five listed for most or all of it, including two at
nothing available at all. Cuts at 60 and 40 both fall inside the same gap and split the nine
values identically, so 50 was chosen for saying something a reader can repeat, not because the
data preferred it.

> **Concept: a cut that lands in a real gap.** A threshold is arbitrary until you check what it
> separates. Two things can be true at once and both are worth stating: the number was chosen
> for a reason that has nothing to do with the data (it is memorable, and half a month is a
> phrase), and the data happens to agree, because there is empty space on either side of it.
> If the values had been evenly spread, moving the cut by five points would have reclassified
> stations, and the honest thing would have been to say the boundary is a convention. Here it
> is not doing that work, and that is checkable rather than assertable: 60 and 40 produce the
> same split, which is what "lands in a gap" means operationally.

The grade mix moved from A 1, B 1, C 5, D 5, F 9 to **A 1, B 1, C 5, D 5, E 4, F 5**, and it
still reads that way as of 31 August 2026.

The pin bump for the sixth chip shipped in the same pull request rather than a follow-up,
because the band table and the chip that renders it are two halves of one change. It brought
some accessibility work with it: two of the chips moved to colours that take white lettering,
because dark ink on them had been chosen on one contrast standard and a newer one rated it far
worse, and the "no grade" dash moved off a token that was failing contrast in both light and
dark. This site renders that dash more than its siblings do, for a station-month with nothing
to grade.

### Plain words on the tiles

One last change from the same day, small and worth copying. The summary tiles read "4 lifts
with a notice up at the last poll" and "70% of days available". The first asks a reader to know
what a poll is. The second asks them to work out what "available" was measured over.

They now read "lifts reported out when we last checked" and "of days with lifts and escalators
available, across the stations named this month". Longer, and the denominator stays, because
that is the part that could not be dropped: the feed names a station only when something is
wrong with it, so the site has no roll of the stations that have a lift, and any wider
denominator would be invented.

"Poll" left the visitor-facing text entirely. "Listed" stayed, because a notice being listed is
exactly what the site measures, and "fixed" is the word it must not use.

## Where it left the site

A letter that means what its legend says, a bar where two cells of the same colour mean the
same thing, a six-band scale whose cuts a reader can reconstruct by counting days, and tiles
written for somebody who has not read the source.

And one station, Dublin Pearse, sitting at the bottom of the scale on the strength of an
escalator alone. Every step to that F was correct. Chapter 09 is about why it is still wrong.

## Notes

- PR #25, "Count escalators in the grade, colour works that overran, and say plainly what the
  page means" (29 Aug 2026): the Connolly contradiction, the escalator reasoning, the amber
  code and the explicit day-severity ranking, the grade key, the plain-words pass, and the five
  statements the review of that branch found untrue.
- PR #27, "Grade stations A to F inclusive, with E at 50%" (29 Aug 2026): the cut, the
  nine-value distribution, the grade-mix move, and the statusui pin bump with its contrast
  work.
- `notes/site.md` §§ An escalator out is a day the station was short of a way up, Blue said two
  opposite things, The grade key keys the letter not a colour, ... and then left the top of the
  page entirely, The scale grew an E, Plain words on the summary tiles (all 28 to 29 Aug 2026).
- Availability 70% to 66%, Connolly A to C, Pearse A to F at 22%: `notes/site.md`, 29 Aug 2026.
  Measured again 31 Aug 2026 the same figures read 67% aggregate, Connolly C at 91%, Pearse F
  at 20%; the corpus grew two days in between.
- Grade mix A 1, B 1, C 5, D 5, E 4, F 5: PR #27, and re-measured 31 Aug 2026 across 21 graded
  station-months.
- The water site's binary knock rule, which chapter 09 returns to: uisce series ch 15.
