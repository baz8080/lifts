# 07. "and" is a sequence, not a choice
*~10 min read · PR #30 · 30 August 2026*

*Where we are:* chapter 06 established that the only source for what an Irish rail station has
is a hand-typed field on irishrail.ie. This chapter is about reading it, and about the reading
that would have told a wheelchair user access was fine at a station where it was gone.

## The question that opened this stretch

Here is the field, at one station:

> **Hazelhatch and Celbridge:** "All platforms can be accessed via lifts and ramps"

The site now knows there is a lift notice at Hazelhatch. It has that sentence. What does it
publish?

The first version of this branch read the sentence as a list of options. Lifts **or** ramps:
two ways to reach the platforms, so if the lift is out, the ramps remain, and step-free access
survives the outage.

That is wrong, and it is wrong in the worst available direction.

## What changed

### The sentence describes a route, not a menu

Read it again as somebody who has been to the station. The ramp gets you along. The lift does
the level change. You need **both**, in sequence, and there is no way to most platforms at
Hazelhatch without the lift.

The site would have published "access remains" at a station where access was gone. Barry, who
knows the station, caught it.

> **Concept: the safe direction of an error.** Any derived claim will sometimes be wrong, so
> the question is not whether to be wrong but which way. A reader told access is gone when it
> was not has made one wasted check: annoying, recoverable, a phone call. A reader told access
> remains when it is gone travels to the station and is **stranded on a platform**, possibly
> after a journey they cannot easily reverse. The two errors are not symmetric and they must
> not be weighted as if they were. So every rule in this module leans the same way: default to
> "gone", say "unknown" freely, and never infer that access remains. That single principle
> decides most of the design decisions in the rest of this chapter, including several that look
> like they are about parsing.

### Then it was checked, everywhere

One caught misreading is an anecdote. The useful move was to check whether the conjunctive
reading holds across the whole network, and it does. Across all 61 stations whose prose
mentions a lift:

- **"and" as a sequence: 29 stations.** "Lift and footbridge to platform 2" (Malahide,
  Skerries, Portlaoise, Maynooth, Monasterevin, Portarlington, Templemore, Tullamore,
  Balbriggan, Laytown) is lift up, cross, lift down. Same for "Lifts and footbridge to all
  platforms" and "Platforms accessible via stairs and lifts".
- **"or" is a genuine disjunction, but it is nearly always "or stairs": 11 stations.**
  Adamstown, Bayside, Clonsilla, Glenageary, Howth Junction, Shankill, Blackrock, Booterstown,
  Bray, Tara Street. Stairs are not a step-free alternative, so the lift is still the only way.
- **Two stations, out of 61, name a step-free way round a lift for the same platform.**
  Raheny, "Lift or ramp to platform 1", and Cork, "Ramp or lift to platform 5A, 5B and 6".

So the question issue #24 set out to answer, *when a lift is out, is there another accessible
way in?*, has a near-constant answer on this network: **no**.

That is worth publishing on its own. It also means no route engine is needed, and no graph, and
no pathfinding. The model works out which platforms a lift serves, assumes an outage removes
step-free access to them, and carves out the two exceptions by hand.

### The model deliberately does not parse connectives

This is the design decision the chapter exists to explain, and it is the opposite of what a
programmer's instinct suggests. The obvious move, having discovered that "and" means sequence
and "or" sometimes means alternative, is to write a parser that tells them apart.

`lift_access/model.py` does not parse connectives at all.

The two exceptions live in a constant, `STEP_FREE_ALTERNATIVES`, which is a hand-reviewed list
of two entries. Adding one is a human decision visible in a diff, never a parser output, and a
test fails if any published verdict claims an alternative that is not in the list.

The reason is the safe direction again. A connective parser that is 95% right is a machine that
will, five times in a hundred, publish "access remains" without anybody having read the
sentence. Two entries reviewed by a person, with a test preventing a third from appearing
without review, is a smaller claim that is actually true.

### Three things a review caught, all of them about reading

**A summary sentence is not a per-platform claim.** Dublin Pearse's field opens "Via ramps,
stairs, escalators, and lifts." A lift, no platform number. Counted as covering the station,
that made the page's own "Ramp to platform 1" into a lift platform, so a notice about platform
1 would have published "Platform 1 is reached by lift". The rule is now that **specific beats
general**: a segment naming a lift with no platform covers every platform only when no other
segment names one.

**Template text invents lifts.** This one is a trap with teeth:

> "To access the lift, you must call via the help point at each landing of the lift shaft.
> Please see lift call operation page for steps to call the lift."

Pasted verbatim at dozens of stations. At **three** of them (Greystones, Killiney, Donabate) it
is the *only* mention of a lift, so matching on the word "lift" invents lifts nobody claimed. It
is stripped before anything else runs. The arithmetic is visible in the numbers: 61 stations
mention "lift" in the raw prose, 58 still do after the boilerplate is stripped, and 57 are
recorded as having one once Dromod's explicit "(no lift at this station)" is honoured.

Stripping it also dissolves a contradiction. Greystones' page says "Footbridge **only** to
platform 2" and elsewhere carries the lift-call boilerplate. Those cannot both be true. Once
the template is gone the real claim stands alone, and Greystones is recorded as not mentioning
a lift, which is why its two notices come back `unknown` rather than resolved.

**A reviewed entry expires with the page it quotes.** `STEP_FREE_ALTERNATIVES` cites a
sentence, and these pages are refetched monthly because Irish Rail rewords them. If the
sentence is gone, the entry stops applying, and the verdict becomes **`unknown`, not `lost`**.

> **Concept: an inference that expires with its source.** A hand-reviewed exception is a
> statement about a document at a moment: *on 30 August 2026, Irish Rail's page for Raheny said
> there is a ramp to platform 1*. When the document changes, that statement is no longer
> supported, and the honest move is to stop making it. The subtle part is what to fall back to.
> Falling back to "access was lost" would be treating a reworded page as evidence there is no
> ramp, which it is not: the review found a way round, and a rewrite is silence, not
> contradiction. So it falls back to "unknown" and a test fails loudly so somebody reads the
> page again. The general rule: when a claim's evidence disappears, retract the claim, do not
> invert it.

### Where the two sources disagree, the site says so

The most useful thing the derivation does is refuse to answer. Measured on the corpus as of
31 August 2026, of 24 notices: **16 resolve to "step-free access was lost"**, 2 are escalators,
and **6 come back `unknown`**. A quarter of everything on the site.

Every one of the six is a real discrepancy between two hand-written sources, and none of them
is a parsing failure:

| station | why |
|---|---|
| Limerick Junction | the access field is the single word "Level", yet the station has lift notices, and OpenStreetMap maps two lifts |
| Greystones (twice) | the prose names no lift outside the stripped boilerplate |
| Rush and Lusk | the prose reads "Level access to platform 1 / Lift and footbridge to platform 1": platform 1 twice, plainly a typo, and the notice names platform 2 |
| Portlaoise | the prose puts the lift at platform 1; the notice says platform 2 |
| Carlow | the prose puts the lift at platform 2; the notice says platform 1 |

Papering over any of these means inventing a fact. Printing "unknown" costs the site a row of
confident prose and keeps it truthful.

One refinement matters here, because the first version of it was too blunt. A notice naming
**more** platforms than the page accounts for used to forfeit everything it knew. Athy's notice
names platforms 1 and 2; the page has a lift at 2 and calls 1 level. Platform 2 is still
knowable, so the verdict keeps it and says the notice also named a platform the page does not
list a lift at. Partition what you know from what you do not, rather than discarding both.

### The pill, and what it deliberately does not say

The two exception stations get a small green pill on their row and their page: **"Step-free
route"**, with the card underneath quoting the line that earned it.

It deliberately does not say "accessible station" and deliberately does not use the
international access symbol. Both would read as a far bigger claim than the reviewed list
makes. What the list actually says is only this: *Irish Rail's page names a step-free way to a
platform here that does not use the lift.* That is a narrow, checkable statement and the label
has to stay inside it.

Neither Raheny nor Cork has ever had a notice in the corpus, so the pill has never rendered on
the live site. It is covered by tests rather than left to be discovered the first time it
matters.

### The site says it is an inference, and asks to be corrected

Every access line on this site is worked out from a page somebody typed. This project has
already found, in that source: a typo (Rush and Lusk, platform 1 twice), a self-contradiction
(Greystones), a station whose page says "Level" while its lifts break (Limerick Junction), and
an escalator omitted from the field that should carry it (Dublin Connolly). Presenting derived
sentences in a confident voice on top of that would be claiming more than is known.

So the card carries a caveat in the site's own words: worked out from Irish Rail's page,
written by hand, wrong before, a careful reading rather than a survey, and blind to whatever
the page leaves out.

And then it asks. A static site has no feedback channel, so the caveat ends in a prefilled
GitHub issue link: *"Know this station? Tell us what this gets wrong."*

That is not a politeness. People who use these stations know things no source in chapter 06
records, and a filed issue is auditable in the way this project asks every other claim to be.
It is also the only route by which a fact that exists nowhere machine-readable can ever reach
the site.

## Worked example: what Hazelhatch actually publishes

The station that started the chapter, as the site renders it today:

- **The prose:** "All platforms can be accessed via lifts and ramps."
- **The notice:** a lift out of service, listed 48.5 hours in August.
- **The verdict:** step-free access to the platforms was gone while the notice was listed.
- **What it does not say:** how many lifts Hazelhatch has, whether the one named was the only
  one, or whether anybody was actually stranded.

The first version of this branch would have published the opposite of the third line, from the
same input, by treating one word as a disjunction. The distance between the two readings is one
conjunction and a station somebody has been to.

## Where it left the site

18 of 24 notices carry a worked-out consequence, 6 say "unknown" and say why, two stations
carry a narrow green pill, and every derived line on the site is labelled as an inference with
a link to correct it.

Two things were left open on purpose, and both are chapter 09: the grade still counts escalator
days at full weight, on the same page where an escalator notice is told it removed nothing, and
the derivation reasons about only one leg of the journey. Both were closed on 3 September, in
chapters 11 and 12, and chapter 12 also carries the thing this chapter's caveat gestures at
without measuring: a written account of how far the derivation can be trusted.

Before that, chapter 08 is about what the review of this branch found, which was the same bug
three times.

## Notes

- PR #30, "Say what a lift outage did to step-free access" (30 Aug 2026).
- `notes/station-access.md` §§ "and" is a sequence not a choice, The chip, Three things a review
  caught, It is an inference and the page says so, The lift-call sentence is boilerplate, When
  it says "unknown" (all 30 Aug 2026).
- The 61-station breakdown (29 sequences, 11 "or stairs", 2 alternatives) is from
  `notes/station-access.md`, 30 Aug 2026.
- Re-measured 31 Aug 2026 against `../lifts-data`: 61 stations mention "lift" in the raw prose,
  58 after boilerplate stripping, 57 recorded as having one; verdicts across 24 notices are 16
  lost, 6 unknown, 2 escalator; the six unknown rows are as tabulated, from
  `python -m lift_access report`.
- `lift_access/model.py`: `STEP_FREE_ALTERNATIVES`, `BOILERPLATE`, `read_platform_access`,
  `verdict`. `tests/test_site_real.py` holds the exception-list guard.
- Hazelhatch's listing duration (48.5 hours) measured 31 Aug 2026.
- Diagram: `diagrams/and-is-a-sequence.svg`.
