# 16. A fourth site, and two bugs found sideways
*~7 min read · PR #54 and issues #52, #53 · 11 September 2026*

*Where we are:* the series has been about one repository reading one feed. This chapter is about
what happened when a second reader of the same feed appeared, and about the two bugs it found
here without looking for them.

## The question that opened this stretch

Chapter 01 recorded that this collector stores every service banner Irish Rail publishes, not
just the lift ones, and that as of 31 August 24 of 234 messages qualified as lift or escalator
notices. The other 210 sat in the log, unread.

Somebody was eventually going to read them. A fourth site, `rail-delays`, now does: it reads
this project's data repository and publishes the delay notices.

Almost none of that work belongs in this repository. The question is which parts do.

## What changed

### The collector is not duplicated, not extended, and not touched

One endpoint returns the whole feed in one response, and the raw write already stores it
verbatim. So a second poller buys nothing and costs three things: two pollers hitting a
credentialed endpoint that Irish Rail rotates without notice, a second install on the Pi, and
two logs that disagree about the same feed.

A delays package living *here* was rejected too, for a reason that is about repositories rather
than code: this repository's CI would become the gate on two sites, and a repository publishes
one Pages site, so the delays would have had to claim to be part of this one.

> **Concept: the boundary is a question about the artefact, not the code.** "Should this live
> here?" usually gets argued as a code question, about coupling and shared helpers. The
> decisions above turn on things that have nothing to do with code: how many credentials hit an
> endpoint, how many machines run an install, whose CI blocks whose merge, and what a Pages site
> claims to be. The cause reader that moved across imports nothing from any package here, which
> is what made it a copy rather than a port. The collector stayed because duplicating it would
> duplicate a credential, not because it was hard to extract.

The note now carries a short table of which repository a change belongs in, because the
question had come up twice. The row that is easy to get wrong is "a fact about the feed", and it
had been got wrong here: two observations about delay notices, that the apology sentence ends a
particular way and that the start field is a departure time, had been written into this
repository's data-shape traps. They are traps for code that reads a cause or identifies a train,
and nothing here does either. They live across the way now.

### The trap, which is about this collector

The useful thing the new site found is a property of the identity model that nothing here had
noticed, and could not have.

**Irish Rail empties a notice's location codes part-way through its life.** When that happens
the collector's validity check routes it to the unidentifiable table, and its tracked listing
ends while the notice is still on the feed.

Counted over every notice collected since 8 August:

| | notices | never carry codes | lose them partway |
|---|---|---|---|
| lift and escalator | 55 | 0 | 0 |
| everything else | 497 | 21 | **288** |

**No lift or escalator notice has ever done it.** That is why nothing here noticed, and it is
why the identity model is not changing on the strength of it. It is also what fills a table this
repository otherwise never reads: chapter 01 described the unidentifiable items as delay notices
with empty location codes and left it there, and the real explanation is that most of them
arrive with codes and lose them.

The reason to write it down is the next person who touches the validity check. The current
behaviour is correct for this site and would be a bug for a site that reads delays, and nothing
in the code says so.

## Two bugs found sideways

Both of the issues open on this repository today were found by somebody looking at something
else, and neither has broken anything on the published site. That combination is worth a section
because it is the argument for building the tools in the first place.

### "planned maintenance" is not "planned works"

The planned-works marker is the literal string "planned works", tested as a substring. Irish
Rail wrote a different word on one notice:

> The Lift on platform 1 is currently out of service due to **planned maintenance**.

First seen at Salthill and Monkstown on 11 September and still listed. It reads as a fault, so
its day cells are drawn in the fault colour, it gets none of chapter 04's grace week, and the
station page and the overview both describe it as something it does not say it is.

It is the first notice in the corpus to use the phrase, so nothing published before that day was
wrong.

**It was not found by looking for it.** The delays site's cause reader parses a cause out of any
notice's own clause, and lift notices are in its corpus because they are in the feed. Run beside
this site's planned-works test over all 416 distinct notices collected since 8 August, the two
disagree exactly **once**, on this notice. The cause reader's planned category matches "planned
works" (7 notices), "engineering works" (3) and "planned maintenance" (1), all three being
wordings the corpus actually carries.

> **Concept: a second reader of the same data is a test you did not write.** A substring test
> against one phrase is unfalsifiable from inside: there is no input that makes it fail, only
> inputs it silently declines to match, and chapter 13's tripwires catch that shape only where
> somebody thought to add one. Two independent implementations of "is this planned" over the
> same corpus produce a disagreement count, and a disagreement count is a finding. One in 416 is
> a good result and it is still one more than staring at the regular expression would ever have
> produced. The general move: when a second consumer of your data appears, run it beside yours
> and diff the answers before you do anything else with it.

What to do about it is genuinely open, and the issue says so rather than deciding: whether
"planned maintenance" should earn the same week of grace as "planned works" is a question about
what the grace is for, which is chapter 04's argument, not a question about a regular expression.

### Kishoge is keyed by its name

The station facts are keyed by station code, read from the page's own code field. For one
station, Kishoge, that field is missing or unparseable on irishrail.ie, so the code falls back
to the slug. The record is keyed `"Kishoge"` instead of `"KISHO"`.

Chapter 06 celebrated that join being free: every payload carries a code in exactly the code
space the message feed uses, all 15 codes with lift notices matched, no fuzzy matching and no
mapping file. That is still true of 151 stations.

For this one, a real lift notice would fail to join to its station facts, print as "(no station)"
in the report, and fall back to an unknown verdict, even though Kishoge does have a lift and
real access prose. No lift or escalator notice has ever been posted there, so nothing on the
live site is wrong today, and the join would fail silently the day one is.

It was found while investigating a user report of an outage at Kishoge that turned out not to be
in the feed at all.

The fix is not obvious and the issue does not pretend otherwise. Falling back to the name is what
produced this; validating the code against the known code space, or refusing the record outright
the way chapter 08's partial-fetch refusal does, are both defensible and both change what the
denominator means.

## Where it left the site

Nothing on the page changed. A second site reads the same logs, the boundary between them is
written down, one property of the identity model is recorded before somebody trips over it, and
two silent joins-in-waiting are filed with their measurements.

Chapter 08 was about the same bug turning up three times in one review. This one is about two
bugs turning up because somebody built a different tool and pointed it at the same data, which
is the cheaper way to find them.

## Notes

- PR #54, "Record what the delays site cost this repository, and the one trap it found"
  (11 Sep 2026), documentation only: the three reasons the collector is not duplicated, the
  boundary table, the location-codes measurement, and the two traps moved to the other
  repository.
- `notes/delays-site.md`.
- Issue #53, "'planned maintenance' is not 'planned works'" (11 Sep 2026): the notice, its three
  effects on the page, and the one disagreement in 416 notices.
- Issue #52, "Kishoge station-facts record is keyed by name, not location code" (11 Sep 2026).
- The location-codes table counts notices by head plus text plus start, over the corpus from
  8 August to 11 September 2026.
