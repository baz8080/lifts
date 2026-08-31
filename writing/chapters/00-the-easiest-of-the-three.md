# 00. The easiest of the three
*~6 min read · the whole series · 8 to 31 August 2026*

*Where we are:* the beginning. This post says what the site answers, what it turned out to
cost, and how the eleven posts are arranged.

## The question

Which Irish Rail stations have lifts out of service, and for how long?

It is a question you cannot answer today. Irish Rail publishes a live feed of service messages,
and a lift outage appears in it as a banner of English prose: *"The lift at platform 2 is
currently out of service. Iarnród Éireann Irish Rail apologise for the inconvenience caused."*
When the lift is working again the banner is gone. Nothing accumulates. There is no page
listing which stations broke most this year, or how long an outage typically runs, or whether
the same lift keeps failing.

So this repository writes it down. A Raspberry Pi in a hallway asks the feed what is listed,
every 30 minutes, and appends the answer to a file. As of 31 August 2026 that file holds 1,084
runs over 23 days, from which 24 lift and escalator outages across 21 stations have been
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

Eleven, deliberately back-loaded. The first five are the site anyone would expect. The last
four are what happened when it tried to mean something.

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
| 09 | What one letter cannot say | The open questions, and why they are hard |
| 10 | Closing | What the site can and cannot say, and the three-way table |

Each post stands alone. Every number in them carries a source and a date, and every figure has
a row in `figures.md` saying where it came from. Where the three sites did the same job
differently, the chapter says what each one does and what fact about its data forced the split,
because none of those splits is taste.

## What the site says today

As of 31 August 2026, over 23 days of collection:

- **24 outages across 21 stations**, of which 6 are planned works and 2 are escalators.
- **67% aggregate availability** across the stations named in August. That is the share of
  watched days on which nothing was reported out at those stations, and the denominator is
  stated on the page, because the feed names a station only when something is wrong with it.
- The grade mix across 21 station-months: **A 1, B 1, C 5, D 5, E 4, F 5**.
- Four lift notices were still up at the last poll, at four stations.
- Of the 24 outages, **16** are worked out to have removed step-free access to at least one
  platform, **2** were escalators, and **6** come back `unknown` because Irish Rail's own two
  sources disagree with each other.

That last row is the one I would point at. Six of twenty-four is a quarter of everything on the
site, and every one of the six is a real contradiction between a notice and a station page:
a page whose access description is the single word "Level" at a station whose lifts keep
breaking, a page that lists platform 1 twice and never mentions platform 2, two stations where
the notice and the page put the lift on opposite platforms. The site prints "unknown" for all
six rather than guessing, and chapter 07 is about why that is the only defensible thing to do.

## One note on how it was built

This repository was written with AI assistance, mostly Claude Code, working against
instructions and review rather than unattended. Of 139 commits on `main` as of 31 August 2026,
88 carry a `Co-Authored-By` trailer: 61 Claude Opus 5 and 27 Claude Fable 5. The design
decisions, the corrections and the arguments in `notes/` are the interesting part and are
mine; several of the wrong turns in this series were caught by a human reading the output and
saying "no, that station does not work like that". Chapter 07 is one of those, and it is the
most important correction in the project.

That is the last time the process is mentioned. The rest is about the data.

## Notes

- Figures measured 31 August 2026 by rebuilding `../lifts-data` and running the site build and
  `python -m lift_access report`. Registered in `figures.md`.
- Commit and trailer counts: `git log --oneline | wc -l` and a grep for `Co-Authored-By`,
  31 August 2026.
- The regulation quoted is Commission Delegated Regulation (EU) 2017/1926, Annex; the clause is
  read in full in chapter 06.
- Sibling series: [uisce #43](https://github.com/baz8080/uisce/pull/43),
  [esb #30](https://github.com/baz8080/esb/pull/30).
