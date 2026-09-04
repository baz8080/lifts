# 12. Both legs, and who was on the stairs
*~12 min read · PRs #37 and #45 · 3 September 2026*

*Where we are:* chapter 11 took escalators off the grade and shipped saying that issue #33 is
what makes that honest rather than a dodge. This chapter is #33, and #31 with it, and it ends
with the most uncomfortable section in the series: an honest account of how much any of this
derivation can be trusted.

## The question that opened this stretch

Two questions, actually, and they turn out to be the same shape.

**Which platform was still fine?** A lift out does not strand a station, it strands a platform,
and Irish Rail's prose usually says which platform never needed the lift. The site knew that
and said nothing.

**Who lost something when an escalator stopped?** The verdict said a wheelchair user lost
nothing and stopped there, which reads as *nothing happened*. Somebody with a heart condition,
a stick, a pram or a suitcase reads that sentence about the day they could not get to their
train.

Both are the site knowing more than it was saying.

## What changed

### "Platform 1 needed no lift"

A lost verdict now carries a second sentence:

> Platform 1 needed no lift, so it kept step-free access: "Level to platform 1".

The rule is deliberately narrow, and every clause in it is a guard. A sentence from the station
page contributes its platforms if it **says level or ramp**, **names a platform number**, and
**mentions no lift, stairs, step, footbridge, subway, escalator, level crossing, or "from
platform"**. That last exclusion list is longer than it looks because each entry is a way a
sentence can describe a route with a step in it while still using the word "level".

The note is then withheld wherever the two hand-written sources disagree: a platform the page
puts a lift at, a platform the notice itself names, or a general "lifts to all platforms"
claim. Only lost verdicts carry it, since it makes no sense beside an unknown one. And it quotes
a sentence re-read from the live prose at every build, so a reworded page withdraws it rather
than leaving a stale claim standing, which is chapter 07's expiring-inference rule applied
again.

Five lost verdicts gained the note: Dublin Pearse, Dún Laoghaire, Malahide, Portarlington and
Tullamore.

The wording is the part that took the most care, and it is deliberately **not** the exception
list's wording. Chapter 07's `STEP_FREE_ALTERNATIVES` says *"you can still reach this platform
another way"*, which is the same platform by a different route. This says *"that platform was
unreachable, this one was not"*, which is a different platform and therefore a different train.
The second is a weaker claim and must not be dressed as the first.

And the direction labelling that an earlier draft of issue #31 proposed stayed struck, for the
reason chapter 09 gave: this is an outage archive, not a travel planner.

### The journey has two legs, and now the notice says which one it is on

Every verdict up to this point was derived from `platformAccess`, which describes getting from
the ticket office to the platforms. Connolly's escalator notice says "at the main concourse",
which is the *other* leg, and Connolly's escalator is named only in `ticketOfficeAccess`. A
lift notice of that shape would have been reasoned about against prose describing a different
part of the building.

> **Concept: reading a claim against the right leg.** A station is not one place. Getting from
> the street to the concourse and getting from the concourse to the platform are separate
> journeys with separate equipment, and Irish Rail keeps them in separate fields. A derivation
> that reads only one field will, for any notice about the other, produce a confident sentence
> about the wrong half of the building. The fix is not to merge the fields, which would lose the
> distinction entirely, but to work out which leg the *notice* is about and read it against the
> matching prose. When the notice does not say, the honest output is the reading the site had
> before, not a guess.

A notice's own text says which leg it is on. A platform number or the word "platform" is the
platform leg. Failing that, "concourse", "entrance", "booking hall", "ticket office", "ticket
hall", "car park" or "street level" is the entrance leg. A notice naming neither is unlocated
and keeps today's reading.

A platform **wins** over an entrance word, and the reason is a nice piece of source-reading:
`platformAccess` starts at the ticket office, so "the lift from the concourse to platform 2" is
already that field's leg. The page itself has put that lift on the platform side.

Over the 24 distinct notice texts on record: **19 platform, 1 entrance** (Connolly's), **4
unlocated** (Malahide's "at Malahide Station", Docklands' "The lift is currently out of
service", Tullamore, and Clonsilla's "on P2", which nothing here reads as a platform). No false
entrance hits. The entrance vocabulary is built from one real example and from the words
`ticketOfficeAccess` itself uses; a notice saying "main hall" or "foyer" falls to unlocated,
which is the safe direction.

### What is actually in the entrance field

All 152 stations carry `ticketOfficeAccess`. Nine are blank, all Northern Ireland stations.
**Twenty-six say there is no ticket office**, which is read as the page naming no lift there,
because the field is literally how to reach an office that does not exist. Eighty-nine say
level, 21 say ramp.

**Four name a lift**: Connolly, Clondalkin, Docklands and Grand Canal Dock. **One names an
escalator**: Connolly.

So a lift notice on the entrance leg is read against `ticketOfficeAccess` and nothing else,
before the platform claim is consulted, because a page can put a lift on the way in and claim
none to the platforms. Where the field names a lift the verdict is lost, quoting the sentence,
with the page's own level way in quoted beside it where there is one. Where it names none, or is
blank, the verdict is unknown, saying which.

No entrance-leg lift notice has been listed yet. This is machinery with unit coverage and no
live case, and the note says exactly that: treat it as untested until a notice exercises it.

### The escalator sentence says who lost a way up

The verdict now reads, in full:

> An escalator is moving stairs, so it was not a step-free route to begin with and its being out
> did not remove one. **Anyone who finds a flight of stairs hard, or has a buggy, a suitcase or
> a stick, did lose a way up.** Irish Rail's page puts a lift on the way into the station as
> well: "Escalator, lift or stairs from Amiens Street and from LUAS stop". Irish Rail's page
> names a level way into the station: "Level access from car park".

That is Connolly's. Three verdicts moved (Pearse, Connolly, Tara Street) and no lift verdict
did.

The label above it changed too: **"A way up lost, not step-free access"**, with a muted border
rather than the green of a reviewed step-free alternative. The colour is doing real work there:
green would read as reassurance about a station where something was genuinely lost.

Two careful refusals in that sentence. It **never says a lift was working**, because the feed
cannot back that: it says what Irish Rail's page names on the same leg, quoted, or that the page
names none. And where the notice and the page disagree about a platform being level, it says so
and quotes both rather than picking a side.

### The overlap guard

Quoting "the page puts a lift on the way to platform 2 as well" beside an escalator outage
invites a reader to conclude the lift was working. The site knows one thing about that, so it
says it.

`render.shard` is the one place that holds all of a station's outages at once, so it tells the
verdict whether a lift notice at the same station overlapped the escalator's listing. If one
did, the quoted lift is withheld with a line saying why. Half-open intervals, or both still
listed.

Zero overlaps on the corpus, and the near miss is instructive: **Dublin Pearse's lift listing
closed at the exact poll its escalator's opened**, at 10:30:46Z on 13 August. Touching, not
overlapping, and a real-corpus test asserts the flag against independently computed interval
arithmetic rather than against the code's own answer.

### The golden file

Four review passes ran over this branch. An extra-high review found nine findings, a high review
of that delta found six, a third found five, and a fourth on the final commit found four.

**Two of the fixes were themselves regressions**, and neither was caught by a test. A broadened
negation guard, added so that Kilcoole's "Not level" would not be quoted as a level way in,
dropped Carrigaloe's and Dalkey's "platform No 1" lines. And the sentence splitter was breaking
at "No." as though it were a full stop, hiding Banteer's and Booterstown's level platforms.

What caught both was comparing the level lines and the report across all 152 stations against
`main`, by hand.

So that comparison became a file. `tests/fixtures/access-golden.json` pins every level line,
entrance sentence and verdict across the 152 stations and the notices on record, and a test
regenerates it in memory and diffs. A regex or a sentence that moves anything now appears as a
diff in the pull request that moved it.

It lives in this repository rather than in the data repository, and that is a deliberate
trade-off with a cost. A refreshed station snapshot merged in `lifts-data` turns this
repository's CI red until somebody regenerates the file and reads the diff. That is the monthly
report of chapter 07 made **mandatory rather than advisory**. Skipping the check on a snapshot
mismatch was considered and rejected, because the guard would then be silently off from the
first refresh nobody regenerated after.

One refinement: the first version failed on any notice the file had not seen, which is wrong. A
new notice on the feed is not a regression, and the corpus gained 21 distinct texts in 26 days.

## How reliable is any of this, honestly

The most valuable thing to come out of that day is not a feature. It is a dated section in the
notes answering the question a reader should be asking by now, which the pull requests kept
implying and never stated.

**The short form: defensible as an annotation on an outage archive, with the safeguards below,
and not as anything a traveller should act on.**

Why it is defensible at all: the alternative is not a better source, it is silence. Every
structured source is empty (chapter 06). A reading of somebody's prose beats silence only if the
error direction is controlled, and that is the entire design, which is worth listing in one
place because it is scattered across five chapters: default to "gone"; say "unknown" freely;
quote the sentence each claim rests on; carry the caveat and the correction link on every page
that makes a derived claim; and keep the grade independent of all of it. A reader can falsify
any verdict against the quoted words. Remove the quoting or the one-directional bias and it
stops being defensible.

Then, by class of sentence, on the corpus to 3 September:

- **"Step-free access was gone"**, 18 of 27 notices. The strongest part: one direct sentence and
  one notice. Its failure mode is a wrong page, and the page has already produced a typo, a
  self-contradiction and an omission. Six of 27 verdicts are unknown for exactly that reason.
  That figure is honest and it is also **the reliability ceiling of the source**.
- **"Platform 1 needed no lift"** and **"Level access from car park"**. Direct statements, but
  "level" is Irish Rail's word. Nobody has checked one of these against a station: distance,
  gates, opening hours, whether the route is usable with a buggy in the rain. The correction
  link is the only feedback channel and it has never fired.
- **The escalator sentence's second half**, 3 of 27. "The page puts a lift on the way to
  platform 2 as well" is true *of the page*. What a reader infers is that the lift worked. The
  overlap guard covers the one thing the site knows, but the feed is not complete, since notices
  appear and vanish in batches, so a lift out that Irish Rail never posted is invisible. The
  site controls its words, not the inference.
- **The entrance leg**, zero lift notices and one escalator notice. Built from one real example,
  on a field that is literally about reaching the ticket office, and at 26 stations it says there
  is no office, so a sixth of the network is unknown on that leg by construction. Untested
  machinery.

> **Concept: what the code's own history says about the code.** The usual evidence for a
> derivation being right is that its tests pass. Here that evidence is weak and the note says
> why: three review passes on the day this was built found nine, six and five findings in about
> a thousand lines of this kind of logic, one fix was itself a regression, and every rule tested
> against the corpus was later found to have a wording it had not seen ("platform No 1", "Not
> level", "No." mid-sentence). The unit tests mostly pin strings their own author wrote, so they
> confirm the author's model of the prose rather than the prose. The checks that caught the real
> regressions compared output across all 152 pages against the previous version. That finding
> rate is itself a measurement, it belongs in the note beside the feature, and the honest
> conclusion is to assume wording gaps remain.

## Where it left the site

Five lost verdicts that name a platform which kept step-free access. Three escalator verdicts
that say who lost a way up and quote what the page names on the same leg. A notice read against
the leg it is about. A golden file that turns any change in this derivation into a visible diff.
And a dated section saying how far any of it should be trusted, which is the thing I would most
want a reader of the site to see.

As of 4 September, across 30 notices on record: 20 resolve to step-free access lost, 3 are
escalators, and 7 are unknown.

## Notes

- PR #37, "Add note when another platform kept step-free access" (3 Sep 2026), closing issue
  #31: the contribution rule and its carve-outs, the five verdicts, the wording distinction, and
  the struck direction labelling.
- PR #45, "Read a notice against the leg it names, and say who an escalator outage affected"
  (3 Sep 2026), closing issue #33: leg detection, the entrance-leg reading, the escalator
  sentence, the overlap guard, the golden file, and the four review passes.
- `notes/station-access.md` §§ The other platform is often still step-free, The entrance leg and
  who an escalator served (3 Sep 2026), How reliable this is, honestly (3 Sep 2026).
- Leg detection over 24 distinct notice texts: 19 platform, 1 entrance, 4 unlocated, no false
  entrance hits (PR #45, 3 Sep 2026).
- `ticketOfficeAccess` breakdown across 152 stations: 9 blank, 26 no ticket office, 89 level,
  21 ramp, 4 naming a lift, 1 naming an escalator (same).
- The Pearse touching-not-overlapping instant, 2026-08-13 10:30:46Z (same).
- Reliability figures are quoted from the note as measured on the corpus to 3 Sep 2026 (27
  notices, 18 lost, 6 unknown, 3 escalator). Re-measured 4 Sep 2026 the same counts read 30
  notices, 20 lost, 7 unknown, 3 escalator.
- Review finding rate (9, 6, 5, 4 across four passes; two fixes that were regressions) from
  PR #45 and the reliability note.
