# 00. The easiest of the three
*~8 min read · the whole series · 8 August to 12 September 2026*

*Where we are:* the beginning. This post says what the site answers, what it turned out to
cost, and how the nineteen posts are arranged.

## The question

Which Irish Rail stations have lifts out of service, and for how long?

It is a question you cannot answer today. Irish Rail publishes a live feed of service messages,
and a lift outage appears in it as a banner of English prose: *"The lift at platform 2 is
currently out of service. Iarnród Éireann Irish Rail apologise for the inconvenience caused."*
When the lift is working again the banner is gone. Nothing accumulates. There is no page
listing which stations broke most this year, or how long an outage typically runs, or whether
the same lift keeps failing.

So this repository writes it down. A Raspberry Pi in a hallway asks the feed what is listed,
every 30 minutes, and appends the answer to a file. As of 12 September 2026 that file holds
1,648 runs over 35 days, from which 53 lift and escalator outages across 37 stations have been
reconstructed, and the site built from it is at
[baz8080.github.io/lifts](https://baz8080.github.io/lifts). It is the third site of a family:
[uisce](https://github.com/baz8080/uisce) does the same for Uisce Éireann's water notices, and
[esb](https://github.com/baz8080/esb) for ESB Networks' power outages. Each has a series like
this one.

## Why this one is written separately

I expected this to be the easy one, and for a fortnight it was.

The water site has to work out how many people a boil-water notice touches, which means Census
Small Areas, a radius, and a long argument about what a pin on a map even means. The power site
has to merge five records into one fault, argue with a regulator's published indices, and
decide what to do about storm days. This site has one endpoint returning one flat list. No
geography. No population. No merging worth the name. The collector was written in a day and
the site in another, and the architecture was lifted almost unchanged from the power site,
which had already lifted it from the water one.

Then the site tried to say what any of it *meant*, and hit something neither sibling has.

A lift out at Athy is not the same event as a lift out at Dublin Connolly. At Athy the page
says "Level to platform 1, Lift to platform 2", so when the lift goes, platform 2 stops being
reachable without stairs and platform 1 is fine. At Connolly four platforms are level from the
ticket office, one has a ramp, and two are behind a lift. The outage that matters is not the
same outage, and no number on a status page is honest until it knows the difference.

To know the difference you need an inventory: what does this station have, and which platform
does each machine serve. Ireland does not publish one. Not in GTFS, which is the format transit
apps read. Not in NaPTAN. Not in the NTA's developer API. Not in NeTEx, the European standard
written for exactly this, which Ireland does not publish at all. The regulation that was
supposed to force it obliges a member state to publish the listed data types *"provided they
exist in digital machine-readable format"*, and that clause is the whole story: the duty is to
publish what you hold, not to create it.

What does exist is a free-text field on irishrail.ie, typed by hand, with no schema and no
obligation to be correct. It is the only machine-readable statement of what an Irish rail
station has that this project could find, and reading one sentence in it the wrong way produced
a page that told a wheelchair user access was fine at a station where it was gone.

That is the story this series is arranged around.

## How the posts are arranged

Nineteen, deliberately back-loaded. The first five are the site anyone would expect. Chapters
06 to 09 are what happened when it tried to mean something, 10 to 12 are the four days in early
September when everything 09 left open was closed, and 14 to 17 are the week after that, in
which the project stopped working around the missing data and started recording it.

| # | Title | What it covers |
|---|---|---|
| 01 | A feed that is not about lifts | The collector. Verbatim before parse, and why a failed run must never look like an empty one |
| 02 | The start date that is 451 days old | Measuring the listing rather than Irish Rail's own start date |
| 03 | Three sites, one design layer | The shared front end. The short chapter, on purpose |
| 04 | A grade with nothing to borrow | Inventing an availability scale when no regulator publishes one |
| 05 | The grade argued with the bar underneath it | Escalators, a colour that meant two things, and a sixth letter |
| 06 | The data Ireland does not have | Every source checked, why the absence is lawful, and what it costs |
| 07 | "and" is a sequence, not a choice | Reading the prose, and the misreading that nearly shipped |
| 08 | The same bug, three times | A review pass, and one bug shape found in three places |
| 09 | What one letter cannot say | Four open questions, and why they are hard |
| 10 | Two ways the page lied about time | A build that stalled, and a gap in a listing that vanished |
| 11 | The grade narrows to lifts | The 15 pixels that let escalators leave the letter |
| 12 | Both legs, and who was on the stairs | Which platform kept access, who lost a way up, and how far to trust any of it |
| 13 | What a reader can take away | Feeds, a CSV, and two tripwires for a silent drop |
| 14 | A guard that was guarding the corpus | A test that failed on Irish Rail editing a sentence |
| 15 | Building the thing that does not exist | Recording station access by hand, with provenance |
| 16 | A fourth site, and two bugs found sideways | A second reader of the same feed, and what it found |
| 17a | Closing: what the site can and cannot say | The two lists, and the three-way table |
| 17b | Closing: what I would tell someone starting the fourth | The moral, and the glossary |

Each post stands alone. Every number in them carries a source and a date, and every figure has
a row in `figures.md` saying where it came from. Where the three sites did the same job
differently, the chapter says what each one does and what fact about its data forced the split,
because none of those splits is taste.

## What the site says today

As of 12 September 2026, over 35 days of collection:

- **53 outages across 37 stations**, of which 3 are escalators.
- **76% availability** across the 21 stations named in August, and 79% across the 22 named in
  September so far. That is the share of watched days on which no lift was reported out at those
  stations, and the denominator is stated on the page, because the feed names a station only
  when something is wrong with it.
- The August grade mix across 21 station-months: **A 3, B 1, C 4, D 6, E 5, F 2**.
- Of the 45 notices on record, **28** are worked out to have removed step-free access to at
  least one platform, **3** were escalators, and **14** come back `unknown` because Irish Rail's
  own two sources disagree with each other.

That last row is the one I would point at, and it is getting worse rather than better: it was 6
of 24 on 31 August and it is 14 of 45 now. Every one of the fourteen is a real contradiction
between a notice and a station page: a page whose access description is the single word "Level"
at a station whose lifts keep breaking, a page that lists platform 1 twice and never mentions
platform 2, stations where the notice and the page put the lift on opposite platforms. The site
prints "unknown" for all of them rather than guessing, and chapter 07 is about why that is the
only defensible thing to do.

The reason it is getting worse is the interesting part: the corpus keeps reaching stations whose
pages are thinner than the ones it started with, and no amount of care with the parsing improves
a page that does not say anything. That is what chapter 15 is a response to.

Both of the grade figures above moved twice in the first week of September, once because a bug
was making several stations look far worse than they were and once because escalators stopped
counting towards the letter. Chapters 10 and 11.

## One note on how it was built

This repository was written with AI assistance, mostly Claude Code, working against
instructions and review rather than unattended. Of 204 commits on `main` as of 12 September
2026, 135 carry a `Co-Authored-By` trailer, across six Claude model identifiers. The design
decisions, the corrections and the arguments in `notes/` are the interesting part and are
mine; several of the wrong turns in this series were caught by a human reading the output and
saying "no, that station does not work like that". Chapter 07 is one of those, and it is the
most important correction in the project.

That is the last time the process is mentioned. The rest is about the data.

## Notes

- Figures measured 12 September 2026 by rebuilding `../lifts-data` and running the site build
  and `python -m lift_access report`. Registered in `figures.md`.
- Commit and trailer counts: `git log --oneline | wc -l` and a grep for `Co-Authored-By`,
  12 September 2026.
- The regulation quoted is Commission Delegated Regulation (EU) 2017/1926, Annex; the clause is
  read in full in chapter 06.
- Sibling series: [uisce #43](https://github.com/baz8080/uisce/pull/43),
  [esb #30](https://github.com/baz8080/esb/pull/30).
