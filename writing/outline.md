# Outline - 18 posts plus intro and a two-part closing, chronological

Each entry: PRs and dates, thesis, concepts boxed, worked example, and the three-way contrast
the chapter must state. The repo's history is small enough to read directly (215 commits, 48
merged pull requests, seven `notes/` files, no open issues), so there is no `sources/` extraction
as the uisce series needed; `figures.md` is the registry.

The series' standing mandate, on top of the shared rules: **every fork from the sibling sites
is stated as (uisce's approach, esb's approach, ours, and the fact about this feed that forced
it).** The four that anchor chapters are tabulated in `README.md`.

The shape of the series is the argument. Chapters 01 to 05 are the site anyone would expect:
collect, measure, publish, grade. Chapters 06 to 09 are what happened when the site tried to
say what any of it *meant*, which is the part that was not foreseen and is the reason this
series exists separately from the other two. Chapters 10 to 12 are the four days in early
September when everything chapter 09 left open closed, in an order nobody predicted. Chapters 13
to 16 are the week after, in which the project stopped working around the missing data and
started recording it, and two of the series' own settled decisions were reversed.

---

## Ch 00 - The easiest of the three · intro

The question: which Irish Rail stations have lifts out, and for how long. The third site of a
family, built to a pattern that already worked twice. Then the turn, stated up front so the
back-loading reads as design: what a lift outage *means* needs a station inventory, Ireland
publishes none, and the only machine-readable statement of what a station has is a hand-typed
CMS field. Today's answer with today's date. AI process named once (204 commits, 135 with a
`Co-Authored-By` trailer, across six Claude model identifiers).

## Ch 01 - A feed that is not about lifts · PR #1 · 8 to 18 Aug

**Thesis.** Write it down before you read it: raw JSONL verbatim before any parse, the database
disposable, `rebuild` replaying the live code path, `sort_keys=True` load-bearing so two
machines' logs merge with `sort -u`. The feed is every service banner, not a lift feed: 24 of
234 messages qualify. There is no id, so identity is `head` + sorted `locationCodes` + `start`.
There is no completion signal, so an outage ends when its notice is first absent. And a failed
run must never read as an empty list, which `poll.py` enforces structurally rather than
checking. **Concepts.** Source of truth against derived index; a run that failed is not a run
that saw nothing. **Example.** The 264 unidentifiable items, and why they are the right kind of
mess to keep. **Contrast.** uisce's archive *is* its database; esb's feed purges within hours
and that is what forced a Pi. Here the feed is patient, so the Pi is inherited rather than
derived, and the cost of that inheritance is nearly zero. Mermaid pipeline diagram.

## Ch 02 - The start date that is 451 days old · PR #2 · 18 Aug

**Thesis.** The site measures the listing, not Irish Rail's start. 23 of 24 notices carry a
start that predates the poll they were first seen at, 12 of them by a week or more, over days
the feed was polled every 30 minutes and the notice was not there. So the bars, the month
filing and every duration run `first_seen` to `end`; the start is printed as Irish Rail's claim
and colours nothing. `end` is a year-end placeholder. "No longer listed", never "fixed",
because notices arrive and vanish in batches. Reissues fold on an exact poll match and a gap of
one poll is two outages. Everything a reader sees is Dublin wall-clock, after a bug that filed
a 31 August notice under August while its own summary read 1 September. **Concepts.** Measure
the window you actually watched; two clocks for one date is a bug in either direction.
**Example.** Rush and Lusk at 451.6 days, and Tullamore at minus 2.3. **Contrast.** The
operator-start row of the table in full: this is the sharpest three-way split in the series.
SVG `listed-not-started.svg`.

## Ch 03 - Three sites, one design layer · PRs #3 to #17 · 19 to 26 Aug

**Thesis.** The short chapter, and it says so in its first line, because the other two series
already tell this story from their side. Vendored on the 19th, drifted within a day, a pinned
git dependency by the 20th, with `dependencies` staying literally empty because the Pi install
is a file copy and nothing else. The design alignment pass. Twice-daily pushes and a 16-hour
stale threshold, sized above the widest legitimate gap and below a missed slot. A 3.11 floor
checked in CI rather than declared. **Concept.** An empty dependency list as a deployment
contract. **Example.** The staleness arithmetic. **Contrast.** One paragraph, pointing at
uisce ch 14 and esb ch 6a.

## Ch 04 - A grade with nothing to borrow · PR #18 · 28 Aug

**Thesis.** This reverses a settled decision, and the note records the reversal dated. There is
no Irish or EU availability target: the PRM TSI sets design rules and a written-policy duty,
the Passengers' Charter promises "every effort", the Big Lift programme publishes no figure.
The regulators who publish numbers are elsewhere (ORR/Network Rail, TfL). So the bands are this
site's own, calibrated in days a reader can count, because bands tuned for TfL's 98% put every
station in the bottom band at day granularity. Planned works are excused for their first week,
measured over the planned segments summed, after review killed two wrong versions of that rule.
And the build-killer: the bar stops at the build clock, the window at the collection horizon,
and those come from different machines, so availability went negative. **Concepts.** A scale
with no anchor; a band calibrated in the unit the bar is drawn in. **Example.** Six days of
works then four of fault, under all three versions of the grace rule. **Contrast.** The
grade-anchor row: esb could grade against a published promise, uisce had to invent one from
population, and this site had to invent one *and* had no magnitude to invent it out of.

## Ch 05 - The grade argued with the bar underneath it · PRs #25, #27 · 29 Aug

**Thesis.** Dublin Connolly graded A / 100% available directly above two red escalator cells.
Fixing that meant counting escalators, and the honest consequence is that the grade is a
weaker claim than it looked: *Irish Rail reported something out here*, not step-free
availability, because a wheelchair user cannot use an escalator. Then a colour that said two
opposite things (Midleton's 19 days and Pearse's forgiven 6 drew the same blue), amber for
works past their grace rather than a second red because a deuteranope cannot separate orange
from red at cell width, and a legend that keyed a code the page does not use and then left the
top of the page. The scale grows an E at 50%, and the measurement agrees with the arithmetic
when it did not have to. **Concepts.** One colour, two meanings; a cut that lands in a real
gap. **Example.** The E arithmetic over a 31-day month, against the nine availabilities the old
F band held. **Contrast.** The knock-the-grade row, with uisce's binary `KNOCK_CATS` named as
the precedent chapter 09 comes back to.

## Ch 06 - The data Ireland does not have · issue #24, PR #30 · 30 Aug

**Thesis.** The heart of the series, and the chapter the whole shape was built for. Every
source checked came back empty: GTFS `pathways.txt` absent from all three NTA archives,
`wheelchair_boarding` not merely unpopulated but column-absent, `location_type` empty on all
152 rail stops, NaPTAN's `AccessArea` null on every one, PTIMS bus street furniture, the NTA
developer API bus-only, `getAllStationsXML` an inventory with no accessibility at all, the
lifts-and-escalators alerts page checked and struck. NeTEx and SIRI-FM are the European formats
that would carry exactly this and Ireland publishes neither. Then the reason, which is the
point of the chapter: Delegated Regulation (EU) 2017/1926 obliges a National Access Point to
publish the listed data types *"provided they exist in digital machine-readable format"*, so
the duty is to publish what you hold and not to create it, and the absence is lawful rather
than an oversight somebody will fix. Then the consequence a reader can feel: Google, Apple,
Transit, Citymapper and Moovit all read the three GTFS fields that are missing, so none of them
can offer wheelchair routing on Irish Rail. Closing turn: the dated snapshots in
`lifts-data/stations/` appear to be the only versioned machine-readable record of Irish rail
station access that exists, which was never the intent. **Concepts.** A National Access Point;
a lawful absence. **Example.** The four-consumer argument. SVG `what-would-carry-it.svg`.

## Ch 07 - "and" is a sequence, not a choice · PR #30 · 30 Aug

**Thesis.** What was used instead, and how it was nearly read backwards. The lift-call sentence
is pasted template text and is the only mention of a lift at three stations, so it is stripped
before anything is matched, and stripping it dissolves the Greystones contradiction. Then
Hazelhatch: "All platforms can be accessed via lifts and ramps" read as a choice concludes a
lift outage left access intact, the exact opposite of the truth and in the one direction that
strands a reader. Barry caught it. The 61-station check that followed found 29 sequences, 11
"or stairs", and two stations in the country naming a real step-free way round a lift. So the
model parses no connectives at all. Specific beats general. A reviewed entry expires with the
sentence it quotes, and expiry means `unknown`, not `lost`. Six of 24 notices come back unknown
and every one is a real discrepancy. Two fields that look useful and are not. A pill that is
deliberately not the access symbol. And a caveat that ends in a prefilled issue link, because
it is the only route by which a fact recorded nowhere can reach the site. **Concepts.** The
safe direction of an error; an inference that expires with its source. **Example.** Hazelhatch,
then the six-row unknown table. SVG `and-is-a-sequence.svg`.

## Ch 08 - The same bug, three times · PR #30's second review, PR #34 · 30 Aug

**Thesis.** Three of the second review's findings were the *first* review's findings
reappearing in the code written to fix them, which makes them a habit rather than three bugs.
Underneath them one shape: a predicate over the wrong quantity, which passes vacuously exactly
when the thing it should assert is missing. Audited for across the rest of the codebase, it
turned up twice more, both in the collector and neither with anything to do with the site: a
`rebuild` that wiped 228 messages and 1,012 runs and exited 0, and an alert repeat window that
opened on the attempt rather than the delivery, so one blip at the moment the collector first
breaks buys 24 hours of silence. Plus OpenStreetMap, carried as a second opinion and removed
after being measured: zero verdicts changed, its one signal redundant, and 2 of 12 sampled
stations carrying a `level` tag. **Concept.** A guard that passes because what it checks is
absent. **Example.** The rebuild transcript, before and after. **Contrast.** The one chapter
with no sibling contrast, and it says so.

## Ch 09 - What one letter cannot say · issues #28, #31, #32, #33 · open 31 Aug, all closed by 3 Sep

**Thesis.** The open work, written as reasoning rather than a backlog, because the reasoning is
the interesting part. #32 is the sharp one: Dublin Pearse is graded F, the worst band on the
scale, on the strength of an escalator alone, on a page that also tells the reader that outage
did not remove step-free access. Both statements are true and the fine print is honest. The
problem is that one letter is answering two different questions for two different populations,
and the chip is what people read. Weighting is refused because there is nothing to calibrate it
against and it would make a number nobody can reconstruct by counting days; uisce's binary
`KNOCK_CATS` is the precedent. What makes the fix honest rather than a dodge is #33: say who an
escalator outage *did* affect instead of dropping them from the number and saying nothing. #33
also carries the entrance leg, which is a real limit: the derivation reasons about the platform
leg only, and Connolly's escalator is named in a field it never reads. #31 is the largest
unclaimed win, an order of magnitude bigger than the exception list. And direction labelling is
refused on principle: this is an archive, not a travel planner. **Concept.** One number, two
populations. Kept as the argument stood on 31 August, with forward pointers, because every issue
closed within four days and the arguments are what shaped what got built.

## Ch 10 - Two ways the page lied about time · PRs #39, #42, #44 · 2 to 3 Sep

**Thesis.** Two false statements about time, neither the collector's fault. The page read
"collection has stopped" when the *build* had: GitHub's scheduled runs were landing four to ten
hours late every day, so the site now builds on the data landing and the crons are a fallback,
pushes went six-hourly and the threshold followed 16 h to 10 h. And a notice that vanished and
came back unchanged was published as never having left, because the unique identity key left
nowhere to put the second appearance: Portlaoise as one sixteen-day outage rather than two short
ones a fortnight apart. A `listings` table holds one row per stretch; grace goes to 2 because
Athy blinked for a single poll; the planned total is pooled across stretches so a gap cannot
launder a grace week. **Concepts.** The age on the page is the age of the data, not of the
build; a test that exercises the easy half. **Example.** The four-hour blip that would have
taken Pearse from 20% to 41%. **Contrast.** The build-clock and horizon split is shared with
both siblings; this is the first time the *publishing* half of it broke here.

## Ch 11 - The grade narrows to lifts · PRs #38, #43 · 1 to 3 Sep

**Thesis.** The order is the point: #28, filed as the least interesting item on the list, was
the blocker. Reserving a 15px kind gutter on *every* row (the 28 August attempt was right except
that it was conditional) means red escalator cells under a green lift chip read as two facts
rather than a contradiction, which was the entire argument that had kept escalators in the
grade. So escalators come off the letter, and the key says "Lift availability" and not the
issue's "step-free availability", because the grade counts notices and a quarter of the access
verdicts are unknown. The only-powered-way-up case is written down with a test that fails the
day it applies. The denominator question a review raised, and why it was kept. **Concepts.** A
conditional column is a misalignment; a rule with no instance, written down and guarded.
**Example.** Pearse and Connolly at A over red escalator strips. **Contrast.** uisce's binary
`KNOCK_CATS`, now matched rather than cited.

## Ch 12 - Both legs, and who was on the stairs · PRs #37, #45 · 3 Sep

**Thesis.** #31 and #33, and what came out of them. A lost verdict names the platform that
needed no lift, quoting the sentence, withheld wherever the two sources disagree. A notice's own
text says which leg it is about (19 platform, 1 entrance, 4 unlocated over 24 texts), and the
entrance leg is read against `ticketOfficeAccess`, where four of 152 stations name a lift. The
escalator verdict says who lost a way up in those words, quotes what the page names on the same
leg, and never says a lift was working; the overlap guard covers the one thing the site knows.
The golden file, born of two fixes that were themselves regressions, and its deliberate cost.
Then the section that matters most: a dated, honest account of reliability by class of claim.
**Concepts.** Reading a claim against the right leg; what the code's own history says about the
code. **Example.** Connolly's full verdict sentence. **Contrast.** None, and it says so.

## Ch 13 - What a reader can take away · PRs #49, #50 · 6 to 7 Sep

**Thesis.** A survey of the site asking one thing of each screen: what can a visitor do with
this? Five answers were "nothing". A "Lift out" tag beside the name, built from a boolean the
row was already carrying and throwing away; Atom feeds per network and per station; a CSV; a
link back to the page a claim was quoted from. And two guards that are not for visitors at all:
`unclassified_mentions` (a reworded head would drop its notices with nothing failing) and
`thin_days` (a day with two polls paints like a day with 48). The tag's placement took a second
PR and four rendered alternatives; 780px is measured, not chosen. **Concepts.** A feed entry for
something still happening; a tripwire for a silent drop. **Example.** The Midleton reword, found
in passing, which is ch 14. **Contrast.** Neither sibling publishes a feed.

## Ch 14 - A guard that was guarding the corpus · PR #51 · 8 Sep

**Thesis.** A red build on `main` from a merge that could not have caused it. The access golden
file pinned outputs but re-derived them from whatever the data repo held when CI ran, so it
failed on two other repositories' schedules. The hole was a sentence written confidently into
the notes: "the logs are append-only and that can only mean a bad checkout". The logs are; the
`messages` table is not, because identity excludes the body, so a reword overwrites `text_raw`
in place. Rush and Lusk flipped overnight; third such failure in five days. Inputs pinned (53 KB
to 115 KB), the test moves to a bare clone, regeneration is additive, and the comparison reports
moves only. The review found the narrowing took the drop check off the other fixture.
**Concept.** A guard over an input you do not control. **Example.** The determinism claim tested
directly by checking the data repo out 20 commits back. **Contrast.** Corrects ch 12 in the
series' own record rather than by editing it.

## Ch 15 - Building the thing that does not exist · PR #46 · 4 to 8 Sep

**Thesis.** The big reversal. `accessible-routes.md` had ruled out hand-curation since 29 August
because a hand-curated file has no provenance, no refresh and no audit. Those are three
properties, and properties can be built: an append-only observation log per station, one fact a
line with who, when, from what and how sure; replayed the way `rebuild` replays the collector's
logs; a page-sourced fact expiring when its quote leaves the page. Then a graph, reachability
per platform, and an outage as the named equipment's edges removed. Two safe-side rules keep it
from outrunning its evidence, and the pilot demonstrably says *less* than the prose derivation,
which is the design working. The three documents Barry brought, and what the business case gave
that no search would have: 51 stations in priority order, route-like paragraphs, a named audit
to request under FOI, and the definitions. Ends on the turn: a `gtfs` export of the very file
ch 06 found absent, and a format drafted to hand to Irish Rail. **Concepts.** The objection is a
specification; an edge that records ignorance. **Example.** The five-station pilot table.
**Contrast.** Neither sibling ever had to manufacture its second source.

## Ch 16 - A fourth site, and two bugs found sideways · PR #54, issues #52, #53 · 11 Sep

**Thesis.** A fourth site reads the same logs and publishes the delay notices. What belongs
here: not the collector (two pollers on a rotated credential, a second Pi install, two logs that
disagree), not a package (this repo's CI would gate two sites, and a repo publishes one Pages
site). The trap that is about this collector: Irish Rail empties `locationCodes` part-way through
a notice's life, 288 of 497 non-lift notices and **zero** lift ones, which is why nothing here
noticed and why the identity model is not changing. Then two bugs found by looking at something
else: "planned maintenance" is not "planned works" (one disagreement in 416 notices, found by
running the delays site's cause reader beside `is_planned`), and Kishoge keyed by name because
its page's code field is unparseable. **Concept.** A second reader of the same data is a test
you did not write. **Contrast.** The boundary question is new; the siblings have no fourth
reader.

## Ch 17 - The same thing, said differently · PRs #55, #56 · 18 to 24 Sep

**Thesis.** Both of ch 16's bugs close, and neither the way its issue proposed. "planned
maintenance" and "engineering works" join "planned works" because, by ch 04's own account of
what the grace is for, all three claim the same kind of event, so ch 16 made #53 sound more open
than it was. Kishoge's page publishes the name *in* the code field (the issue's "missing or
unparseable, falls back" was wrong, and ch 16 repeated it); the fix is a one-entry hand table,
not validation or refusal, and nothing guards the next one. Then a finding from re-measuring:
Tullamore's planned works came back on 16 Sep, the pooled total crossed a week on the 19th, and
August's A became a D nineteen days after August ended, with nothing on the page saying so.
**Concepts.** A literal string is a vocabulary of one; a property of the notice, published as a
property of the month. **Example.** Salthill and Monkstown's September, E 66% to C 91%, and the
reissue whose head said "Station". **Contrast.** None needed; the month question is this site's
own.

## Ch 18 - The one code a rebuild cannot undo · PRs #57, #58 · 20 to 24 Sep

**Thesis.** The collector was the oldest, least-changed code and the only code whose mistakes
a rebuild cannot undo, so it got the repository's one whole-file review. Ten findings: the raw
line was written inside the block that opened the database; an empty probe file passes on a full
card (ch 08's shape, missed by ch 08's own audit); a power-cut fragment swallowed the next line;
gzip errors escaped the retry; the alert marker outlived a recovery; systemd's 60 s cap was
below the client's worst case; the backup could hang. And ch 01's "one keyword argument":
`sort -u` deduplicates by sorting, which reorders by `body`, so replay now sorts by fetch time,
at the stated cost of `fake-hwclock`'s hour. #57's comment rule as a coda. **Concepts.** The
invariant has an upstream edge; a merge that deduplicates also reorders. **Example.** 2,224 lines
already in order, so nothing moved. **Contrast.** Stated only as a question in 19a: whether the
siblings' merges need the same.

## Ch 19a - Closing: what the site can and cannot say

The figures with their date, the two lists, the ten-row three-way table and the identical
column, the settled decisions in plain language. Split from 19b because the closing outgrew the
series' own 3,000-word ceiling.

## Ch 19b - Closing: what I would tell someone starting the fourth one

The moral, which is not either sibling's: *collect first, and publish no meaning you cannot
source*, with the September coda on rejected alternatives and the newer one from ch 15: write
your rejections out properly, because one of them is a design document you have not recognised
yet. A coda from ch 17 and 18 on where not to look. Glossary of all 31 concept boxes.
