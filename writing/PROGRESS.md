# Progress ledger

Read this first each session. Statuses: `todo` -> `drafted` -> `reviewed` (continuity pass by a
later session) -> `final`.

- **Session 0 (31 Aug 2026)** drafted all eleven posts, the three diagrams and `figures.md`,
  from the repository's own history and from a fresh measurement of the corpus. Nothing is
  `[verify:]`.

A later session should do the continuity and review pass, and re-check the "quoted at the date
they were measured" rows in `figures.md` against their stated sources.

| Ch | Title | PRs / issues | Status | Words |
|---|---|---|---|---|
| 00 | The easiest of the three (intro) | - | drafted | 1,420 |
| 01 | A feed that is not about lifts | #1 | drafted | 1,722 |
| 02 | The start date that is 451 days old | #2 | drafted | 1,861 |
| 03 | Three sites, one design layer | #3 to #17 | drafted | 1,182 |
| 04 | A grade with nothing to borrow | #18 | drafted | 2,161 |
| 05 | The grade argued with the bar underneath it | #25, #27 | drafted | 2,162 |
| 06 | The data Ireland does not have | issue #24, #30 | drafted | 2,138 |
| 07 | "and" is a sequence, not a choice | #30 | drafted | 2,258 |
| 08 | The same bug, three times | #30 reviews, #34 | drafted | 1,996 |
| 09 | What one letter cannot say | issues #28, #31, #32, #33 | drafted | 2,197 |
| 10 | Closing: three feeds, three sites, one discipline | - | drafted | 2,408 |

Total ~21,500 words, 14 concept boxes, three hand-written SVGs and one mermaid flow (ch 01).

Deliberately shorter than the esb series (~24,500 words over 12 posts) and much shorter than
uisce's (~32,600 over 18). The repo is three weeks old, it inherited its collector architecture
rather than deriving it, and the shared-UI story is told twice already, so chapter 03 is
compressed on purpose. The length that *was* spent went where the work went: chapters 06 to 09
are 8,600 words, 40% of the series, on a problem neither sibling has.

## Chapter summaries (3 lines each)

- **00** The question, the family, and the turn: it looked like the easiest of the three until
  the site tried to say what a lift outage means, which needs a station inventory Ireland does
  not publish. Today's figures with today's date. AI process named once (139 commits, 88
  co-authored).
- **01** Verbatim before parse, database disposable, `rebuild` replays the live path,
  `sort_keys=True` load-bearing. The feed is every service banner: 24 of 234. No id, no
  completion signal. Boxes: source of truth against derived index; a failed run is not an empty
  one. Mermaid pipeline. Contrast: esb's purging feed forced the Pi, ours inherited it.
- **02** The listing is the measure: 23 of 24 starts predate the first sighting, 12 by a week
  or more, Rush and Lusk by 451.6 days. Batch arrivals, so "no longer listed" not "fixed".
  Reissue folding on an exact poll. The UTC/Dublin bucket bug. Boxes: measure the window you
  watched; two clocks for one date. SVG. The sharpest three-way fork in the series.
- **03** The short one, on purpose. Vendored the 19th, drifted by the 20th, pinned in `uv.lock`
  the same day, with `dependencies` empty for the Pi. The alignment pass, the per-site
  permalink wording, the 16-hour threshold sized to a twice-daily cadence, the 3.11 floor
  checked in CI. Box: an empty dependency list as a deployment contract.
- **04** No Irish or EU target exists (PRM TSI, Passengers' Charter, Big Lift; ORR and TfL are
  elsewhere), so the bands are the site's own, counted in days, because one bad day in 31 is
  already 96.8%. The grace rule in its three versions. The clock-skew crash. Boxes: a scale
  with no anchor; a band calibrated in the bar's unit.
- **05** Connolly A/100% over two red cells, so escalators count and the grade becomes "something
  was reported out". Blue meant two opposite things, so overrun works go amber. The grade key
  keyed nothing, then left the top of the page. E at 50% lands in a real gap (0, 0, 18, 22, 22,
  50, 68, 68, 72). Boxes: one colour two meanings; a cut in a real gap.
- **06** The heart. Every source empty: no `pathways.txt`, `wheelchair_boarding` column absent,
  NaPTAN `AccessArea` null on 152, PTIMS bus, NTA API bus, `getAllStationsXML` inventory-only,
  the alerts page struck. NeTEx and SIRI-FM unpublished. EU 2017/1926's "provided they exist"
  clause makes the absence lawful. Five mapping apps hit the same wall. The snapshots turn out
  to be the only versioned record that exists. Boxes: a National Access Point; a lawful absence.
- **07** The reading. Boilerplate stripped first (it is the only lift mention at three
  stations). Hazelhatch: "lifts and ramps" read as a choice would publish "access remains"
  where access is gone; Barry caught it. 29 sequences, 11 "or stairs", 2 real alternatives, so
  no connective parser at all. Specific beats general; a reviewed entry expires to `unknown`,
  not `lost`. Six of 24 unknown, all real discrepancies. Boxes: the safe direction of an error;
  an inference that expires with its source. SVG.
- **08** Three of the second review's findings were the first review's findings, reappearing in
  the fixes. One shape underneath: a predicate over the wrong quantity, passing vacuously. Found
  twice more in the collector: `rebuild` wiped 228 messages and exited 0; the alert window
  opened on the attempt not the delivery. OSM carried, measured (0 verdicts changed, 2 of 12
  level tags), removed. Box: a guard that passes because what it checks is absent.
- **09** The open work as reasoning. #32: Pearse is F on an escalator alone, beside a sentence
  saying access was fine; one letter, two populations; weighting refused; uisce's binary
  `KNOCK_CATS` is the precedent, and #33 is what makes the fix honest. The entrance leg
  (`ticketOfficeAccess`, 143 of 152). #31, 32 of 57 stations. Direction labelling refused on
  principle. Box: one number, two populations.
- **10** Can-say and cannot-say lists; the ten-row three-way table plus the identical column;
  the settled decisions in plain language; the moral, "collect first, and publish no meaning you
  cannot source"; a 14-entry glossary.

## Open threads

- Review pass not yet done: every chapter is `drafted`.
- The three SVGs are functional and unpolished, as in both sibling series. An optional later
  pass.
- Cross-references to the sibling series are by chapter number, not URL, so they survive
  uisce #43 and esb #30 merging or renumbering. Check them if either lands.
- **Chapter 09 is the most perishable thing here.** All four issues it describes are open, and
  #32 in particular has a recommended option that would change every figure in chapters 05 and
  09 the day it lands. If escalators stop knocking the grade, that chapter needs rewriting from
  "here is the argument" to "here is what was decided", and a new chapter probably follows it.
- The `figures.md` row for "32 of 57 stations name a platform reached without a lift" is
  recorded rather than re-derived, and a quick re-derivation with a narrower rule gave 27. The
  definition, not the data, is what differs. Worth pinning down when #31 is built, since the
  number will be published then.
- A root `README.md` pointer to `writing/` is deliberately left for the publish decision, as
  both sibling series did.
- The repository is moving roughly a pull request a day. Check `git log origin/main` before
  assuming this account is current; anything after #34 needs a new chapter or an extension.
