# Progress ledger

Read this first each session. Statuses: `todo` -> `drafted` -> `reviewed` (continuity pass by a
later session) -> `final`.

- **Session 0 (31 Aug 2026)** drafted chapters 00 to 09 and the closing, the three diagrams and
  `figures.md`.
- **Session 1 (4 Sep 2026)** merged `main` and extended over PRs #37 to #45. All four issues
  chapter 09 called open had closed within four days of it being written; 09 was kept as the
  argument at the time, three chapters added, the closing renumbered 10 to 13.
- **Session 2 (12 Sep 2026)** merged `main` and extended over PRs #46 to #54. **Two of the
  series' own settled decisions were reversed that week**, and both are narrated rather than
  edited away: chapter 12's account of the golden file is corrected by chapter 14, and chapter
  06's "hand-curation is deliberately out" by chapter 15. Four chapters added; the closing,
  which had passed the series' own 3,000-word ceiling, split into 17a and 17b; the new chapters
  numbered 13 to 16 so no number is skipped.

A later session should do the continuity and review pass, and re-check the "quoted at the date
they were measured" rows in `figures.md` against their stated sources.

| Ch | Title | PRs / issues | Status | Words |
|---|---|---|---|---|
| 00 | The easiest of the three (intro) | - | drafted | 1,736 |
| 01 | A feed that is not about lifts | #1 | drafted | 1,722 |
| 02 | The start date that is 451 days old | #2 | drafted | 2,016 |
| 03 | Three sites, one design layer | #3 to #17 | drafted | 1,232 |
| 04 | A grade with nothing to borrow | #18 | drafted | 2,174 |
| 05 | The grade argued with the bar underneath it | #25, #27 | drafted | 2,210 |
| 06 | The data Ireland does not have | issue #24, #30 | drafted | 2,189 |
| 07 | "and" is a sequence, not a choice | #30 | drafted | 2,327 |
| 08 | The same bug, three times | #30 reviews, #34 | drafted | 1,996 |
| 09 | What one letter cannot say | issues #28, #31, #32, #33 | drafted | 2,448 |
| 10 | Two ways the page lied about time | #39, #42, #44 | drafted | 2,192 |
| 11 | The grade narrows to lifts | #38, #43 | drafted | 1,812 |
| 12 | Both legs, and who was on the stairs | #37, #45 | drafted | 2,741 |
| 13 | What a reader can take away | #49, #50 | drafted | 1,364 |
| 14 | A guard that was guarding the corpus | #51 | drafted | 1,421 |
| 15 | Building the thing that does not exist | #46 | drafted | 2,403 |
| 16 | A fourth site, and two bugs found sideways | #54, issues #52, #53 | drafted | 1,576 |
| 17a | Closing: what the site can and cannot say | - | drafted | 2,111 |
| 17b | Closing: what I would tell someone starting the fourth | - | drafted | 1,520 |

Total ~37,200 words, 27 concept boxes, three hand-written SVGs and one mermaid flow (ch 01).

Now longer than both siblings (esb ~24,500 over 12, uisce ~32,600 over 18), which is a fact
about the repository rather than about the writing: it has shipped 15 pull requests in the
twelve days since the first draft. The shape still holds. Chapter 03 is still the compressed
one, and **chapters 06 to 16 are 22,000 words, 59% of the series**, all of them on the access
problem and what followed from it.

## Chapter summaries (3 lines each)

- **00** The question, the family, and the turn. Today's figures with today's date, including
  the unknown share going the wrong way. AI process named once (204 commits, 135 co-authored).
- **01** Verbatim before parse, database disposable, `rebuild` replays the live path. No id, no
  completion signal, and a failed run structurally unable to close anything. Boxes: source of
  truth against derived index; a failed run is not an empty one. Mermaid pipeline.
- **02** The listing is the measure. Rush and Lusk's 451.6 days precede all collection;
  Docklands and Hazelhatch are the watched-and-absent cases. The UTC/Dublin bucket bug. Boxes:
  measure the window you watched; two clocks for one date. SVG.
- **03** The short one, on purpose. Vendored then pinned, `dependencies` empty for the Pi, the
  alignment pass, the 16-hour threshold (later 10, ch 10), the 3.11 floor checked in CI. Box:
  an empty dependency list as a deployment contract.
- **04** No Irish or EU target, so the bands are the site's own, counted in days. The grace rule
  in its three versions. The clock-skew crash. Boxes: a scale with no anchor; a band calibrated
  in the bar's unit.
- **05** Connolly A/100% over two red cells, so escalators count. Blue meant two opposite things.
  E at 50% lands in a real gap. Boxes: one colour two meanings; a cut in a real gap. Reversed in
  ch 11.
- **06** Every source empty; NeTEx and SIRI-FM unpublished; EU 2017/1926's "provided they exist"
  clause makes the absence lawful; the snapshots turn out to be the only versioned record that
  exists. Boxes: a National Access Point; a lawful absence. Ch 15 stops working around it.
- **07** The reading. Boilerplate stripped first; Hazelhatch; 29 sequences, 11 "or stairs", 2
  real alternatives, so no connective parser at all. Boxes: the safe direction of an error; an
  inference that expires with its source. SVG.
- **08** Three of the second review's findings were the first review's. One shape: a predicate
  over the wrong quantity. Found twice more in the collector. OSM carried, measured, removed.
  Box: a guard that passes because what it checks is absent.
- **09** The four open questions as reasoning. Box: one number, two populations. Kept as the
  argument stood on 31 August; all four closed by 3 September.
- **10** The build stalled, not the collector; and a notice that came back published as never
  having left. Boxes: the age on the page is the age of the data; a test that exercises the easy
  half.
- **11** #28 turned out to be the blocker for #32: a 15px gutter is what let escalators leave
  the grade. Boxes: a conditional column is a misalignment; a rule with no instance, written
  down and guarded.
- **12** The kept-platform note, leg detection, the escalator sentence, the overlap guard, the
  golden file, and the reliability section. Boxes: reading a claim against the right leg; what
  the code's own history says about the code. Its golden-file paragraph is corrected by ch 14.
- **13** What a visitor can take away: the "Lift out" tag, Atom feeds, a CSV, a link to the
  source page, plus two tripwires for a silent drop. Boxes: a feed entry for something still
  happening; a tripwire for a silent drop.
- **14** A red build from a merge that could not have caused it. The notes said the logs are
  append-only and therefore a dropped notice means a bad checkout; `messages` is not append-only,
  and a reword overwrites the body in place. Inputs pinned. Box: a guard over an input you do
  not control.
- **15** The reversal. Provenance, refresh and audit were three named defects, so they became
  three requirements: an append-only observation log, replayed like the collector's, with
  page-sourced facts expiring when their quote leaves the page. Boxes: the objection is a
  specification; an edge that records ignorance. Ends on a GTFS export of the file ch 06 found
  missing.
- **16** A fourth site reads the same logs. The boundary written down, the location-codes trap
  (288 of 497, zero lift notices), and two bugs found by pointing a different tool at the same
  data. Box: a second reader of the same data is a test you did not write.
- **17a** The figures, the two lists, the three-way table, the settled decisions.
- **17b** The moral, its two codas, and a 26-entry glossary.

## Open threads

- Review pass not yet done: every chapter is `drafted`.
- The three SVGs are functional and unpolished. Neither Session 1 nor Session 2 needed to change
  them. Chapter 15 is the first chapter that would clearly benefit from one (the station graph);
  it was left out rather than drawn badly against a five-station pilot.
- Cross-references to the sibling series are by chapter number, not URL, so they survive
  uisce #43 and esb #30 merging or renumbering. Check them if either lands.
- **The pattern across three sessions is that this series' own "settled" sections keep being
  reversed**, which is the repository working as intended and is now the series' most
  distinctive feature. The habit to keep: date the chapter, leave it standing, and write the
  correction as a later chapter. Do not edit a chapter to match today.
- **The most perishable things now.** Chapter 15's graph is a schema, a derivation and a
  five-station pilot that the site does not read; the day it does, that chapter needs a
  successor rather than an edit. Chapter 16's two issues are open, and #53 in particular turns
  on what chapter 04's grace is *for*, so whatever is decided belongs beside that argument.
  Chapter 12's entrance leg is still machinery with no live case.
- **The unknown verdict share is the number to watch**: 6 of 24, then 7 of 30, now 14 of 45. If
  it keeps climbing, chapters 07 and 12's account of the prose derivation needs revisiting, and
  it is the strongest argument in the series for chapter 15's survey.
- A root `README.md` pointer to `writing/` is deliberately left for the publish decision, as
  both sibling series did.
- The repository has shipped 15 pull requests in twelve days. Check `git log origin/main` before
  assuming this account is current; anything after #54 needs a new chapter or an extension.
