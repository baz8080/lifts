# 13. What a reader can take away
*~6 min read · PRs #49 and #50 · 6 to 7 September 2026*

*Where we are:* chapters 10 to 12 closed every question chapter 09 left open. The site is now
accurate about what it measures. This chapter is about a different question, which is whether
any of it can leave the page.

## The question that opened this stretch

A survey of the site against a corpus of 36 outages over 28 stations, asking one thing of each
screen: **what can a visitor actually do with this?**

Five answers came back as "nothing", and two of them were not about visitors at all.

## What changed

### "Lift out", beside the name

The most-asked question of a status site is the present tense, and the site answered it only
by implication: a station with a notice up sorted to the top, and you had to know that.

There is now a tag beside the station's name while a notice is listed, on the overview row and
on both station headers: **"Lift out"**, **"Escalator out"** or **"Lift and escalator out"**.

The mechanism is a small piece of housekeeping worth noting because it is the shape of a lot of
the work in this repository. The row's fourth statistic was a boolean that existed only to feed
the sort. It is now a mask of which kinds are listed at the horizon, the sort treats any nonzero
value exactly as it treated the boolean, and both renderers print the label from it. Nothing new
is stored: the site was already carrying the fact and throwing away the detail.

Placing the tag took a second pull request the next day, and the reasoning is a good short
example of measuring rather than choosing. The tag first dropped under the name at an indent
that lined up with the name's first letter, which read as stray padding and made every row
carrying a notice taller than the rest. It is now flush with the right edge of the name column,
so the pills line up down the list. Above 780px the name column widens from 170px to 230px,
which fits an ordinary name and its tag on one line, and incidentally stops "Kilkenny
(MacDonagh)" truncating.

780px is measured, not chosen for roundness: below about 740px the row's fixed columns plus a
31-day bar at its three-pixels-a-cell floor stop fitting the viewport. Four other placements
were rendered against the real CSS and compared before this one was settled on.

### Atom feeds, and an outage that appears twice

`feed.xml` carries the 50 most recent outages, and `s/<slug>.xml` sits beside each station page
with every outage that station has ever had.

The interesting decision is the dating, because a feed reader's model of an entry is a thing
that happened once and this site's model of an outage is an interval with an uncertain end.

> **Concept: a feed entry for something that is still happening.** A feed reader shows an entry
> at its date and never again. An outage has two moments a reader cares about, the one where it
> starts and the one where it is no longer listed, and the second is the whole point of this
> site. So an entry is dated to the appearance while the notice is up, and **moves** to the
> close once it is down, with "(no longer listed)" in the title. A subscriber sees the outage
> twice, and the second showing is the completion signal. That is a deliberate abuse of a
> feed's semantics in exchange for the one thing a subscriber actually wants, and it is only
> defensible because the title says which showing they are looking at. The feed's own date is
> the collection horizon, never the build clock, which is the same rule chapter 02 fixed for
> every other date on the site.

### A CSV, and a link back to the source

`outages.csv` is one row per outage the site shows: the listing instants in UTC, Irish Rail's
own dates as they were written, and a blank end while a notice is still listed. Linked from the
footer.

And the access card now links the Irish Rail page its prose was quoted from. That is three
words of markup and it closes a gap chapter 07 left open: the caveat asks the reader to check
the reading, and until now it did not say where.

### Two guards that are not for visitors at all

These are the ones I would keep if I had to drop the rest, and both are chapter 08's family:
a thing that could go wrong silently, made loud.

**`unclassified_mentions`** finds any message whose head or text mentions a lift, an elevator or
an escalator that `classify` rejects. Chapter 01's classifier matches heads of a particular
shape. If Irish Rail reworded a head, its notices would simply stop appearing on the site, and
nothing anywhere would fail. The build prints any it finds and the real-corpus test fails on
them. It finds nothing today, which is the point: it is a tripwire, not a feature.

**`thin_days`** names any Dublin day the collector reached the feed fewer than 40 times,
including a day with none. A day with two polls paints exactly like a day with 48, and chapter
02's whole argument is that the site must not colour a day it did not watch. The horizon
handles the end of the window; this handles a hole in the middle of it.

> **Concept: a tripwire for a silent drop.** Most tests assert that code does what it should on
> an input you wrote. These assert that a category is *empty*: no message mentions a lift and
> fails to classify, no watched day has too few polls. That kind of check is cheap, it passes
> forever, and it is worth having precisely because the failure it guards is invisible. A
> notice that stops matching does not error, it just is not there, and nobody counts the things
> that are not on a page.

### The reword, discovered in passing

Regenerating the golden file for this branch turned up something that is not a rendering
problem at all.

The real-corpus test was red on `main` from data drift, and one of the causes was that
**Midleton's notice text had been rewritten under the same identity key**. Chapter 01's derived
identity is head plus location codes plus start, and it deliberately excludes the body. So when
Irish Rail rewords a live banner, the key survives, and the collector overwrites the stored text
in place. The earlier planned-works stretch now carries the later fault wording.

That was noted and not touched, because it is its own problem. It is chapter 14.

## Where it left the site

A visitor can see what is out right now, subscribe to a station, download the lot as a
spreadsheet, and click through to the page a claim was read from. The build fails if a notice
stops classifying or a day was barely watched. The initial load went from 64.8 KB to 65.8 KB,
and the feeds and the CSV are off it entirely, fetched only if asked for.

## Notes

- PR #49, "Say which stations are out now, publish feeds and a CSV, and warn about what the page
  cannot show" (6 Sep 2026): the survey that produced the five items, the `NOW_KIND` mask, the
  feed dating rule, the CSV, the source link, `unclassified_mentions` and `thin_days`, and the
  Midleton reword noted in passing.
- PR #50, "Align the 'Lift out' tag to the right of the name column" (7 Sep 2026): the four
  rendered alternatives, the 780px measurement, and the overflow check at twelve widths.
- `notes/site.md` § What a reader can take away, and its 7 September correction to the
  placement described on 5 September.
- Initial load 64.8 KB to 65.8 KB, measured in PR #49 on 6 Sep 2026. As of 12 September it is
  68.3 KB, with `outages.csv` at 22.4 KB and `feed.xml` at 43.3 KB, both on demand.
