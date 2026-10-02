# 19b. Closing: what I would tell someone starting the fourth one
*~8 min read · the whole series · 24 September 2026*

*Where we are:* the second half of the closing. 19a is the account of what the site can and
cannot say; this is what seven weeks of it taught, and a glossary of every idea the series
boxed.

## What I would tell someone starting the fourth one

The other two series each end with a sentence: the water site's about approximating carefully,
the power site's *collect first, interpret later, keep the bytes*. This one is different, and it
is the thing I did not know seven weeks ago:

> **Collect first, and publish no meaning you cannot source.**

Collecting is the easy half and it is where all the discipline usually goes: write the bytes
down, never edit them, make the interpretation disposable. That machinery was inherited from a
sibling, worked on day one, and never once let me down.

What it does not do is tell you what any of it means. A perfectly recorded observation that
"the lift at platform 2 is out of service" is worth very little until you know whether platform
2 has another way up, and that is a fact about the world rather than about your pipeline. No
amount of care with the bytes creates it.

And in Ireland, for rail station accessibility, nobody has created it. Not through
carelessness: the European standards exist, and the regulation that would compel it exempts
data you do not already hold, so the obligation is satisfied. The gap is lawful. Five major
mapping products have hit the same wall and fall back to crowd-sourced pins. The only
machine-readable statement of what an Irish rail station has is a free-text field somebody
types into a CMS, and reading one conjunction in it the wrong way would have told a wheelchair
user that access was fine at a station where it was gone.

Which leaves one more thing to say, and it is the newest. For three weeks the answer to a
missing source was to work carefully around it and publish the limits. On 8 September it became
something else: if the fact does not exist in machine-readable form, record it, with who saw it
and when and how sure they were, and replay it the way the collector's logs are replayed. The
objection to doing that had been written down in full, which is the only reason it could be
read later as a specification rather than a verdict. **Write your rejections out properly. One
of them is a design document you have not recognised yet.**

So the second half of that sentence is where the work went. Say "unknown" as often as it is
true, which here is two times in five. Publish the derivation as an inference and link a way to
correct it. Default every error to the direction that wastes a journey rather than strands one. Refuse to write a parser where
a reviewed list of two entries is the true claim. And when the number on the front of the page
starts answering a question you did not ask it, write the issue with the measurements in it
rather than adjusting the number quietly.

There is a coda from the four days in September that closed every question chapter 09 left
open. The one that unblocked the rest was a fifteen-pixel layout fix filed as the least
interesting item on the list, and it was only visible as the blocker because the argument
against the alternative had been written out in full rather than summarised as "decided
against". A note that records why something was rejected also tells you, later, exactly what
would have to change for it to be right.

And a coda from the last week, which is about where not to look. The code that had never been
reviewed was the collector, because it was the oldest and the quietest, and it was also the only
code whose mistakes a rebuild cannot undo. The rule that made everything else safe to change
made the thing upstream of it look safe too. Review by how permanent a mistake would be, not by
how recently the code moved. And re-measure the months you think are finished: one of them was
not.

## Glossary

Every concept boxed in the series, in order of appearance. Thirty-one of them.

| Concept | Chapter | In one line |
|---|---|---|
| Source of truth against derived index | 01 | The log is what was observed; the database is what it currently means, and only one of them is disposable |
| A run that failed is not a run that saw nothing | 01 | "I could not ask" recorded as "nothing was there" closes every open outage at once |
| Measure the window you actually watched | 02 | Colouring days nobody observed publishes an observation nobody made, and it looks like a real one |
| Two clocks for one date is a bug in either direction | 02 | If the bucket and the label come from different time zones, no reader can tell which the total believes |
| An empty dependency list as a deployment contract | 03 | Keeping `dependencies` empty is what lets the collector install on a Pi by copying a directory |
| A scale with no anchor | 04 | With no published target, an absolute scale of your own, stated as such, beats a relative or borrowed one |
| A band calibrated in the unit the bar is drawn in | 04 | If the bar shows days, the cuts must land on whole days, or the grade claims a precision the data lacks |
| One colour, two meanings | 05 | A mark that covers two cases a reader would distinguish is not wrong, it is silent |
| A cut that lands in a real gap | 05 | A memorable threshold is fine if the data has empty space on both sides of it, which is checkable |
| A National Access Point, and a lawful absence | 06 | The duty is to publish what you hold, not to create it, so the missing data has no process that fills it |
| The safe direction of an error | 07 | Telling somebody access is gone costs a wasted check; telling them it remains strands them |
| An inference that expires with its source | 07 | When a claim's evidence is reworded away, retract the claim rather than inverting it |
| A guard that passes because what it checks is absent | 08 | Ask what a guard asserts when its input is missing; if the answer is "success", it is over the wrong quantity |
| One number, two populations | 09 | One letter cannot answer two audiences whose honest answers differ, and the fine print is not what people read |
| The age on the page is the age of the data | 10 | Rebuilding later cannot make the data younger, so only pushing more often and building on the push move the number |
| A test that exercises the easy half | 10 | If the fixture takes a path where the bug cannot occur, the test's name is the only evidence the behaviour holds |
| A conditional column is a misalignment | 11 | An element that appears only where it has content makes every other row wrong relative to the one that has it |
| A rule with no instance, written down and guarded | 11 | State it in prose and add a test that fails when the case first appears, rather than coding against no example |
| Reading a claim against the right leg | 12 | A station is two journeys with separate equipment; work out which the notice means before reading prose against it |
| What the code's own history says about the code | 12 | When four review passes find nine, six, five and four things, that rate is itself a measurement |
| A feed entry for something still happening | 13 | Date it to the appearance, then move it to the close, so a subscriber sees the outage twice and the second showing is the signal |
| A tripwire for a silent drop | 13 | Assert that a category is empty, because a notice that stops matching does not error, it just is not there |
| A guard over an input you do not control | 14 | The tell is a red build on a merge that could not have caused it; pin the inputs rather than improve the message |
| The objection is a specification | 15 | "No provenance, no refresh, no audit" is not a verdict on an approach, it is a list of three things to build |
| An edge that records ignorance | 15 | A model with no way to say "something is here and I do not know what" encodes absence as impossibility |
| The boundary is a question about the artefact, not the code | 16 | Whose CI blocks whose merge, and how many credentials hit an endpoint, decide where code lives more than coupling does |
| A second reader of the same data is a test you did not write | 16 | Run it beside yours and diff the answers: a disagreement count is a finding a regular expression cannot give you |
| A literal string is a vocabulary of one | 17 | A phrase test cannot fail, only decline; let the corpus list the wordings, and know the list is still closed |
| A property of the notice, published as a property of the month | 17 | If a past month's number depends on something that outlives the month, it is provisional, and should say so or stop at the edge |
| The invariant has an upstream edge | 18 | "Everything derived is disposable" protects what runs after the log is written, and nothing that runs before it |
| A merge that deduplicates also reorders | 18 | Removing duplicates by sorting imposes an order; keep order in a field, not in line position, and state what the field costs |

## Notes

- Corpus figures measured 24 September 2026 by rebuilding `../lifts-data` and running the site
  build and `python -m lift_access report`. All registered in `figures.md`.
- The sibling closings: uisce series ch 17, esb series ch 8.
