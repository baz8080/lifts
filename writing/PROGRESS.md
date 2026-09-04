# Progress ledger

Read this first each session. Statuses: `todo` -> `drafted` -> `reviewed` (continuity pass by a
later session) -> `final`.

- **Session 0 (31 Aug 2026)** drafted chapters 00 to 09 and the closing, the three diagrams and
  `figures.md`, from the repository's own history and a fresh measurement of the corpus.
- **Session 1 (4 Sep 2026)** merged `main` and extended the series over pull requests #37 to
  #45. **All four issues chapter 09 described as open closed within four days of it being
  written**, which is what `PROGRESS.md` had flagged as the series' biggest risk. Chapter 09 is
  kept as the argument as it stood, with a note at the top and forward pointers; three chapters
  were added; the closing was renumbered 10 to 13; chapters 00, 02, 03, 05 and 07 gained forward
  pointers and current figures. Every current figure was re-measured against `../lifts-data` at
  its 4 September state.

A later session should do the continuity and review pass, and re-check the "quoted at the date
they were measured" rows in `figures.md` against their stated sources.

| Ch | Title | PRs / issues | Status | Words |
|---|---|---|---|---|
| 00 | The easiest of the three (intro) | - | drafted | 1,550 |
| 01 | A feed that is not about lifts | #1 | drafted | 1,722 |
| 02 | The start date that is 451 days old | #2 | drafted | 2,016 |
| 03 | Three sites, one design layer | #3 to #17 | drafted | 1,232 |
| 04 | A grade with nothing to borrow | #18 | drafted | 2,173 |
| 05 | The grade argued with the bar underneath it | #25, #27 | drafted | 2,205 |
| 06 | The data Ireland does not have | issue #24, #30 | drafted | 2,138 |
| 07 | "and" is a sequence, not a choice | #30 | drafted | 2,294 |
| 08 | The same bug, three times | #30 reviews, #34 | drafted | 1,996 |
| 09 | What one letter cannot say | issues #28, #31, #32, #33 | drafted | 2,448 |
| 10 | Two ways the page lied about time | #39, #42, #44 | drafted | 2,192 |
| 11 | The grade narrows to lifts | #38, #43 | drafted | 1,812 |
| 12 | Both legs, and who was on the stairs | #37, #45 | drafted | 2,668 |
| 13 | Closing: three feeds, three sites, one discipline | - | drafted | 2,998 |

Total ~29,400 words, 20 concept boxes, three hand-written SVGs and one mermaid flow (ch 01).

Now longer than the esb series (~24,500 over 12 posts) and approaching uisce's (~32,600 over
18), which was not the plan at Session 0 and is a fact about the repository rather than about
the writing: it shipped nine pull requests in the four days after the first draft. The shape
still holds. Chapter 03 is still the compressed one, and **chapters 06 to 12 are 15,500 words,
53% of the series**, all of them on the access problem and its consequences.

## Chapter summaries (3 lines each)

- **00** The question, the family, and the turn: it looked like the easiest of the three until
  the site tried to say what a lift outage means, which needs a station inventory Ireland does
  not publish. Today's figures with today's date. AI process named once (182 commits, 121
  co-authored).
- **01** Verbatim before parse, database disposable, `rebuild` replays the live path,
  `sort_keys=True` load-bearing. The feed is every service banner. No id, no completion signal.
  Boxes: source of truth against derived index; a failed run is not an empty one. Mermaid
  pipeline.
- **02** The listing is the measure: Rush and Lusk's start is 451.6 days before the first poll,
  which precedes all collection; Docklands and Hazelhatch were watched-and-absent. Batch
  arrivals, so "no longer listed" not "fixed". The UTC/Dublin bucket bug. Boxes: measure the
  window you watched; two clocks for one date. SVG. Forward pointer to ch 10's listing split.
- **03** The short one, on purpose. Vendored then pinned, `dependencies` empty for the Pi, the
  alignment pass, the per-site permalink wording, the 16-hour threshold (later 10, ch 10), the
  3.11 floor checked in CI. Box: an empty dependency list as a deployment contract.
- **04** No Irish or EU target exists, so the bands are the site's own, counted in days, because
  one bad day in 31 is already 96.8%. The grace rule in its three versions. The clock-skew
  crash. Boxes: a scale with no anchor; a band calibrated in the bar's unit.
- **05** Connolly A/100% over two red cells, so escalators count and the grade becomes "something
  was reported out". Blue meant two opposite things, so overrun works go amber. E at 50% lands
  in a real gap. Boxes: one colour two meanings; a cut in a real gap. Reversed in ch 11.
- **06** The heart. Every source empty; NeTEx and SIRI-FM unpublished; EU 2017/1926's "provided
  they exist" clause makes the absence lawful; five mapping apps hit the same wall; the
  snapshots turn out to be the only versioned record that exists. Boxes: a National Access
  Point; a lawful absence.
- **07** The reading. Boilerplate stripped first. Hazelhatch: "lifts and ramps" read as a choice
  would publish "access remains" where access is gone; Barry caught it. 29 sequences, 11 "or
  stairs", 2 real alternatives, so no connective parser at all. Boxes: the safe direction of an
  error; an inference that expires with its source. SVG.
- **08** Three of the second review's findings were the first review's, reappearing in the fixes.
  One shape underneath: a predicate over the wrong quantity, passing vacuously. Found twice more
  in the collector. OSM carried, measured, removed. Box: a guard that passes because what it
  checks is absent.
- **09** The four open questions as reasoning: #32's Pearse F on an escalator alone, #33's
  entrance leg, #31's 32-of-57, #28's unlabelled bars. Box: one number, two populations. **Kept
  as the argument stood on 31 August**; all four closed by 3 September, and a closing section
  says what actually happened next.
- **10** Two false statements about time. The build stalled, not the collector: GitHub's crons
  ran four to ten hours late every day, so the build fires on the data landing and the threshold
  went 16 h to 10 h. And a notice that came back was published as never having left: Portlaoise
  as one 16-day outage rather than two short ones, fixed by a `listings` table, grace 2, and a
  pooled planned total. Boxes: the age on the page is the age of the data; a test that exercises
  the easy half.
- **11** #28 turned out to be the blocker for #32. A 15px kind gutter reserved on *every* row
  (the August attempt was right except that it was conditional) makes red escalator cells under
  a green lift chip read as two facts, which was the whole argument for counting escalators. So
  escalators come off the letter, and the key says "Lift availability" and not "step-free
  availability", because the grade counts notices. Boxes: a conditional column is a
  misalignment; a rule with no instance, written down and guarded.
- **12** #31 and #33. The kept-platform note and its carve-outs; leg detection from the notice's
  own text; the entrance leg read against `ticketOfficeAccess`; the escalator sentence that says
  who lost a way up; the overlap guard; the golden file born of two fixes that were regressions.
  Then the reliability section, which is the most valuable thing in the chapter. Boxes: reading
  a claim against the right leg; what the code's own history says about the code.
- **13** Can-say and cannot-say lists; the ten-row three-way table plus the identical column; the
  settled decisions in plain language; the moral, "collect first, and publish no meaning you
  cannot source", with a coda on rejected alternatives; a 20-entry glossary.

## Open threads

- Review pass not yet done: every chapter is `drafted`.
- The three SVGs are functional and unpolished, as in both sibling series. An optional later
  pass. None of them needed changing in Session 1.
- Cross-references to the sibling series are by chapter number, not URL, so they survive
  uisce #43 and esb #30 merging or renumbering. Check them if either lands.
- **Session 0 flagged chapter 09 as the most perishable thing here, and it was right within four
  days.** The lesson for a later session is not to soften such a chapter but to date it: 09 now
  says what it was arguing and when, and the three chapters after it say what was decided. That
  is a better record than a chapter silently rewritten to match today.
- **The next perishable thing is chapter 12's entrance leg.** It is machinery with no live case:
  no entrance-leg lift notice has ever been listed. The day one is, the chapter needs a
  paragraph saying what the derivation actually did with it, and `notes/station-access.md` §
  How reliable this is, honestly needs the same.
- The `figures.md` row for "32 of 57 stations name a platform reached without a lift" is
  recorded rather than re-derived, and a Session 0 re-derivation with a narrower rule gave 27.
  PR #37 has now published the derived version, so the definition is pinned in code and the
  golden file; worth reconciling the note's figure against `lift_access` output.
- A root `README.md` pointer to `writing/` is deliberately left for the publish decision, as
  both sibling series did.
- The repository shipped nine pull requests in the four days after Session 0. Check
  `git log origin/main` before assuming this account is current; anything after #45 needs a new
  chapter or an extension.
