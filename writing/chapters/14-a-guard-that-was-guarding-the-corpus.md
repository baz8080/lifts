# 14. A guard that was guarding the corpus
*~6 min read · PR #51 · 8 September 2026*

*Where we are:* chapter 12 built a golden file to pin the access derivation's output across all
152 stations, and described its cost as a deliberate trade-off. This chapter is about the cost
being something else entirely, and about a sentence in the notes that was written down
confidently and was wrong.

## The question that opened this stretch

A CI run failed on `main` with:

```
notice RLUSK lift: dropped
```

on a merge that could not have caused it.

## What changed

### The assumption, in writing

Chapter 12 said the golden file's cost was that a refreshed station snapshot would turn CI red
until somebody read the diff, and called that the monthly report made mandatory rather than
advisory. That was the intended cost and it was real.

What was not intended is that the file pinned the derivation's **outputs** while re-deriving
them from whatever the data repository held at the moment CI happened to run. So it could fail
on two *other* repositories' schedules rather than on any change to this one.

The hole was an assumption, written into `notes/station-access.md` in exactly these terms:

> A notice that vanishes from the database still fails, because the logs are append-only and
> that can only mean a bad checkout.

The logs are append-only. `messages` is not.

Chapter 01's derived identity is head plus location codes plus start, and it **excludes the
body**. So when Irish Rail rewords a live banner, the identity key survives and the collector
overwrites the stored text in place. A verdict is keyed on the body, so a reword drops one
pinned key and adds another. The addition was tolerated. The drop was fatal.

Rush and Lusk flipped from "platform 2" to "platform 1" overnight on 8 September, and the guard
built to catch a code regression fired on Irish Rail editing a sentence.

> **Concept: a guard over an input you do not control.** A regression test is a claim that *this
> code*, on *this input*, produces *this output*. If the input is not pinned, the test is
> making a claim about three things while reporting on one, and every failure has to be
> diagnosed before it means anything. Worse, the failures arrive on somebody else's schedule: a
> data repository's six-hourly push, a monthly snapshot refresh, an upstream dependency bump.
> The tell is a red build on a merge that could not have caused it. The fix is not a better
> failure message; it is to pin the inputs into the fixture so the test replays them, and to
> move the question of "has the corpus changed" to wherever that is actually the question.

That was the third such failure in five days, after an upstream design-layer bump and a
Midleton reword (chapter 13 found that one). Each had been answered with a regeneration, which
buys a few days.

### The fixture now carries its inputs

The file carries the payload node each station was read from and the body of each notice, and
the test replays them through today's code. That is 23 KB of page fragments across 152 stations,
and the file grows from 53 KB to 115 KB.

Three things follow, and the second is my favourite.

**The test needs no data checkout at all**, so it moved out of the real-corpus test file and
runs on a bare clone. Which surfaces a quiet irony: chapter 12 recorded that skipping on a
snapshot mismatch was rejected because the guard would then be *"silently off from the first
refresh nobody regenerated after"*. The version that was built to avoid being silently off was
itself silently off for anybody without a `lifts-data` checkout, which includes a fresh clone
and any contributor who has not set it up.

**Regeneration is additive.** The regenerator builds over the union of what is already pinned
and what the corpus currently holds, so a wording Irish Rail has since withdrawn **stays as a
test vector**. Both Rush and Lusk bodies are in the file now. The station records carry the page
fragments they were read from, for exactly the reason chapter 01 gives for keeping the raw
logs: the derived form is the disposable one.

**The comparison reports moves only.** What one document holds and the other does not is the
size of the corpus, which no code change decides, and the snapshot filename is provenance rather
than a comparison. The monthly review of a reworded station page stays where it already was: the
refresh workflow opens a pull request against the data repository with the report attached and a
body saying to read it. That is a better home for it than a red build in a different repository.

### The review found the fix had a hole of its own

Narrowing the comparison to moves took the dropped-record check off the **other** golden file
too, the one chapter 15 is about, and that one does still replay live observations. There a
dropped station can be a genuine code fault rather than a corpus event.

Nothing else covered it. The test that looks as though it does passes today only because the
surveyed set happens to be the pilot set, and that coincidence ends at the sixth station.

The fix counts the stations and notices off the **directory listing** rather than off the loader
that feeds the build, and the reasoning is worth keeping: comparing a build with the loader that
produced it holds however badly the loader breaks. That was the first version of the test, which
is why the fix was checked rather than assumed. It is the same defect chapter 08 named, a
predicate over the wrong quantity, turning up in the fix for something else.

### Worked example: proving the determinism claim

The claim this pull request makes is that the test's result no longer depends on the state of
another repository. That is a claim you can check directly rather than argue for, and it was:

```
git -C ../lifts-data checkout HEAD~20   # predating the reword
rebuild
run the suite
```

Green, where the old fixture would have disagreed. The suite also runs green with the data
directory **unset**, on both the development interpreter and the 3.11 floor, and the golden
tests are confirmed by name in the verbose output to be running rather than skipping.

And the guard was checked to still fire, by breaking the thing it exists to protect: disabling
the boilerplate stripper from chapter 07 fails on Donabate, Greystones and Killiney, the three
stations where the lift-call sentence is the only mention of a lift.

## What this corrects in the series

Chapter 12 is left as written, because it records what was believed at the time, but two of its
sentences are now known to be wrong and this chapter is the correction:

- The golden file's cost was **not** only the mandatory monthly review. It was also that any
  reword anywhere, by Irish Rail, at any time, broke an unrelated build.
- The note's claim that a vanished notice "can only mean a bad checkout" rested on the logs
  being append-only, which is true, and on the database inheriting that, which is not.

## Where it left the site

A test that tests this repository's code and nothing else, on a bare clone, deterministically.
A fixture that accumulates wordings rather than replacing them. And one assumption in
`notes/station-access.md` corrected in place rather than quietly dropped, which is the habit
that makes the rest of the notes worth reading.

## Notes

- PR #51, "Pin the access golden file's inputs, so it guards code and not the corpus"
  (8 Sep 2026): the failing run, the append-only correction, the pinned inputs, additive
  regeneration, the narrowed comparison, and the review finding on the other fixture.
- `notes/station-access.md`, whose "the logs are append-only and that can only mean a bad
  checkout" sentence is corrected in place, and `notes/step-free-graph.md` on the fixture that
  still replays live observations.
- Rush and Lusk's body flipped from "platform 2" to "platform 1" on 8 Sep 2026. The two earlier
  regenerations were PR #48 (a statusui bump) and the Midleton reword found in PR #49.
- File size 53 KB to 115 KB, of which about 23 KB is page fragments across 152 stations; the
  suite runs 516 tests with the data directory unset, measured 12 Sep 2026.
