# The lifts series - brief and style guide

A chapter-by-chapter account of how this repository went from a script polling Irish Rail's
service-message feed on a Raspberry Pi to a status site that says what a lift outage did to
step-free access at each station. It is the third of three: the water site's series
([uisce PR #43](https://github.com/baz8080/uisce/pull/43)) and the power site's
([esb PR #30](https://github.com/baz8080/esb/pull/30)) came first, and this one is written
against both.

Nothing in `writing/` is imported by the package. It is prose and diagrams only.

## What this series is about

The other two are stories about measurement: how to count people affected, how to grade a
utility against a promise. This one starts as the easiest of the three and ends somewhere
else entirely.

One endpoint, one flat list of messages, no geography, no Census, no regulator. And then the
question the site exists to answer turns out to need a fact nobody in Ireland publishes:
**what does this station have?** A lift out at a station with a ramp to the other platform is
not the same event as a lift out at a station where the lift is the only way up, and there is
no machine-readable source in the country that can tell the two apart. So the back half of
this series is about the shape of an absence: what was looked for, why it is lawfully missing,
what was used instead, and how reading one hand-typed sentence the wrong way published the
opposite of the truth.

The chapters are deliberately back-loaded. The collector and the site get one each, the shared
design layer gets one short one, four carry the problem that arrived at the end, and three more
cover the four days in early September when every question the fourth of those left open was
answered.

## Who it is for

The same reader as the other two series: an intelligent professional who is not a programmer.
They can follow arithmetic when it is shown and a table when it has real station names in it.
They will not tolerate a term used before it is explained, and they will notice a number that
appears without a sentence saying what it means. The chapters assume the reader *may* have
read the other two but must not require it: every comparison states the other site's approach
in a sentence before contrasting it.

## Voice

- First person, "I". The AI-assisted process is named once, in the intro, and not
  re-litigated chapter by chapter.
- Candid. The wrong turns are the story: the reading of "and" that would have told a
  wheelchair user access was fine at a station where it was gone; the grade that gave a
  station an A over two red cells; the rebuild that emptied the database and reported
  success. Tell what was believed, what was measured, what changed.
- Chronological within a chapter.
- Plain. Prefer "the log" to "append-only JSONL", "a notice" to "a message record". Introduce
  a technical term once, in a concept box, then use it freely.
- **Careful about access.** This site makes claims about whether a disabled passenger could
  get to a platform. The prose never says "the disabled" and never uses a wheelchair as a
  synonym for disability: an escalator outage matters to somebody with a heart condition, a
  pram or a suitcase, and the series says so where the site does not yet.

## Rules

The other two series' rules, restated so this file stands alone.

1. **Every number carries a source and a date.** In text: "(PR #18, 28 Aug 2026)" or
   "(measured 31 Aug 2026)". Every number quoted also gets a row in `figures.md`.
2. **No figure without a sentence saying what it means.**
3. **One concept box per hard idea**, at the point the idea first matters, <= 200 words, in a
   blockquote starting `> **Concept: <name>**`. Where a sibling series already boxed the idea,
   restate it in a line and point at theirs rather than re-explaining.
4. **At least one worked example per hard concept**, using a real station and real numbers,
   with the arithmetic shown. The running examples are **Hazelhatch and Celbridge** (the
   misreading), **Dublin Pearse** (the F driven by an escalator alone) and **Rush and Lusk**
   (the notice dated 451 days before anyone saw it).
5. **Diagrams earn their place.** A mermaid fence for a flow; small hand-written SVG in
   `diagrams/` for anything spatial or temporal. Under 40 lines, no polish.
6. **Length: target ~1,500 to 2,000 words, hard ceiling 3,000.** Each post carries a
   "~N min read" line (about 230 words a minute).
7. **Standalone.** Each chapter opens with a two-line *Where we are* so it works as a single
   blog post.
8. **Vocabulary is fixed** (below); do not drift between synonyms.
9. **Missing number becomes `[verify: what]`** and is collected in the final pass.
10. **No em dashes, and no en dashes either.** This repo's own rule (`CLAUDE.md` §
    Punctuation, 29 Aug 2026): the house dash is a spaced hyphen. Unlike the sibling series,
    this one is checked rather than trusted, and it is stricter than esb's: `scripts/no-em-dash.sh`
    greps tracked files for both characters, so `writing/` is covered the moment it is
    committed and a numeric range has to be written "8 to 15". The uisce series is written the
    other way, which is a deliberate difference of its own and is noted in the esb series.

## The series' own mandate

The esb series carries a rule that every fork from uisce is stated as *(their approach, ours,
and the property of the data that forced it)*. This one is three-way, because on the questions
that matter all three sites landed in different places, and none of the splits is taste.

Where the three diverge, say it as **(what uisce does, what esb does, what this site does, and
the fact about this feed that forced it)**. The four that anchor chapters:

| | uisce | esb | lifts | forced by |
|---|---|---|---|---|
| The operator's start time | publication time, re-stamped, so every duration is a floor | back-dated by hours, immutable, and measured from | back-dated by **months**, shown as their claim, colours nothing | Rush and Lusk is dated 451 days before its first sighting, over days the feed was polled every 30 minutes and the notice was absent |
| How big an event is | people inside a 500 m circle | ESB's own count of customers off | there is no size: a notice is listed or it is not | the feed carries no count of anything |
| What anchors the grade | its own thresholds on person-hours | ESB's published 4-hour / 95% charter aim | its own bands, counted in days | the PRM TSI sets a duty to hold a written policy, not a percentage, and Irish Rail publishes no availability figure |
| What is allowed to knock the grade | `KNOCK_CATS`, binary: health notices knock, discolouration shows and does not | planned works excluded, because the regulator excludes them; storm days kept, and said out loud | planned works excused for one week then counted in full; escalators counted for five days, then stopped | nobody excluded anything on our behalf, so every exclusion had to be argued from the data, twice |

That last row is the spine of the back half of the series.

## Fixed vocabulary

| Use | Not | Meaning |
|---|---|---|
| **the feed** | the API (except in code contexts) | Irish Rail's realtime service-message endpoint |
| **a notice** | a message, a banner, an alert | one service message as the feed publishes it |
| **an outage** | an incident, an event | one notice's listing, with same-poll reissues folded in |
| **listed** | active, open, live | present in the feed at a given poll |
| **no longer listed** | fixed, resolved, repaired | absent from a later successful poll. The site never says "fixed" |
| **a run** | a poll (as a noun), a pass | one scheduled collection attempt, every 30 minutes |
| **the log** | the archive, the JSONL | the raw append-only files; the source of truth |
| **the horizon** | last update, cutoff | the last moment a run actually reached the feed |
| **planned works** | maintenance, scheduled | a notice whose text says "due to planned works" |
| **availability** | uptime, score | the share of days watched with nothing reported out at that station |
| **grade** | rating, mark | the A to F letter, station-month only |
| **step-free** | wheelchair-accessible, accessible | a route with no steps on it. The narrower, checkable claim |
| **a way up** | vertical access, circulation | what an escalator provides and a lift also provides. Losing one is not losing step-free access |
| **a leg** | a segment, a stage | street to concourse, or concourse to platform. Irish Rail keeps them in separate fields |
| **a stretch** | a span, a run | one continuous period a notice was on the feed. A notice can have several |
| **the prose** | the description, the blurb | Irish Rail's hand-written `platformAccess` and `ticketOfficeAccess` fields |
| **the water site / the power site** | uisce / esb (except as repo names) | the two siblings |

## Chapter template

```markdown
# NN. Title
*~N min read · PRs #a to #b · dates*

*Where we are:* two lines placing this chapter in the series.

## The question that opened this stretch

## What changed
(narrative, chronological within the chapter)

> **Concept: <name>** - plain-English box, <= 200 words.

### Worked example: <station>
(real numbers, arithmetic shown, source and date)

## What went wrong   <- when applicable

## Where it left the site
(the numbers as of the chapter's last PR)

## Notes
PRs, commit subjects, `notes/` sections and code functions used; each figure's source.
```

## Working method

Session 0 (31 August 2026) drafted chapters 00 to 09 and the closing in one pass from the
repository's own history: the commit messages, the pull request bodies, the three files in
`notes/`, the README and the open issues. Unlike the esb series it had the corpus to hand, so
the figures were re-measured rather than lifted.

Session 1 (4 September 2026) merged `main` and extended the series over pull requests #37 to
#45. All four issues chapter 09 described as open had closed within four days of it being
written, so that chapter was reframed as the argument at the time with forward pointers, three
chapters were added, and the closing was renumbered 10 to 13. Every current figure was
re-measured against `../lifts-data` at its 4 September state.

`figures.md` marks which rows come from a measurement and which are quoted at the date they
were first measured. `PROGRESS.md` is the ledger for any later session.
