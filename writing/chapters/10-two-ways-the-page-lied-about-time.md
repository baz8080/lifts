# 10. Two ways the page lied about time
*~10 min read · PRs #39, #42 and #44 · 2 to 3 September 2026*

*Where we are:* chapter 09 left four open questions about what the site *says*. This chapter is
about two things it was saying wrongly, both about time, and neither of them the collector's
fault.

## The first: "collection has stopped", when it had not

The page read:

> Updated 22 hours ago - collection has stopped

while `lifts-data` held data from nine hours earlier. Collection had not stopped. **The site
build had.**

The stale banner's whole design (chapter 03) is that it states the age of the data and names no
cause, because from a browser a stalled build and a stalled collector look identical. That was
the right call and it was still not enough, because 22 hours of age is a genuine problem
whoever caused it.

### GitHub's scheduled runs were four to ten hours late, every day

The build asked for two crons, at 05:40 and 12:40 UTC. What actually ran, over the week to
1 September:

| Cron | Actual run start, UTC |
|---|---|
| `40 5` | 10:24, 10:39, 11:46, 11:48, 13:38, 16:46, 17:41 |
| `40 12` | 16:51, 16:53, 16:56, 19:13, 22:33, 22:36 |

The morning slot never once landed in the morning. This is not jitter: before 26 August, with a
single cron, runs started between 05:58 and 06:06Z, which is the 18 to 26 minutes GitHub
documents. Push-triggered and dispatch-triggered runs are unaffected and land within seconds.
Only `schedule` events are throttled this way.

That produces exactly the string on the page. The 10:24Z build saw data to 23:22Z the previous
night. The 16:53Z build saw data to 11:19Z. Nothing built after it, so by 09:47 the next
morning the horizon was 21.5 hours old.

**Retiming the cron was rejected**, and the reason is worth stating plainly: a delay of four to
ten hours cannot be aimed at a one-hour window. A better cron time only moves where the miss
lands.

> **Concept: the age on the page is the age of the data, not of the build.** This is what makes
> the obvious fix wrong. The freshness chip measures from the collection horizon, the last
> moment a run actually reached the feed, against the reader's clock. Rebuilding the site later
> cannot make that number smaller: the data is as old as it is. So only two things move it,
> pushing the data more often, and building promptly after a push the site has not yet seen.
> A schedule does neither. It is a fallback for a trigger that never fired, and treating it as
> the primary mechanism means the page's freshness is bounded by the least reliable part of the
> chain.

So the data repository now dispatches the site build on every push, and the site rebuilds
within a minute of the data landing. The crons stay on as the fallback, moved to 07:00 and
14:00 UTC. That choice has a small detail worth keeping: GitHub Actions cron has no timezone
and Dublin shifts by an hour with daylight saving, so for a one-hour local window only the hour
boundaries land inside it in both seasons.

The Pi's push cadence went from twice daily to every six hours, which caps how old the page can
look: about 7 hours at worst (a six-hour slot, half an hour of randomised delay, one 30-minute
poll interval) against about 13 before. And the stale threshold followed it down from 16 hours
to **10**. Sized above the widest legitimate age and below a missed push, exactly as before,
just against a different cadence.

One deployment note from that pull request is a good example of a change that is safe in the
repository and unsafe in the world: the new threshold had to reach the Pi *before* the merge,
because while the Pi was still pushing twice daily a 10-hour threshold would have shown the red
banner for the last three hours of every twelve-hour window. The fix would have caused the
symptom it was fixing.

## The second: a notice that came back was published as never having left

This one is worse, because nothing on the page looked wrong.

**Portlaoise was published as 16 days listed, F, 29% available.** What actually happened: the
lift was listed for 20 hours from 10 August, then absent from **672 consecutive successful
polls** over the next fortnight, then listed again for 22 hours from 25 August.

Two short outages a fortnight apart, published as one continuous sixteen-day one. Every one of
those 672 polls is in the raw log, exactly as collected. The site simply never looked.

### Where the gap fell out

Chapter 01's derived identity comes back one more time, and this is the sharpest edge on it.

`identity_key` is `UNIQUE` on the messages table, which is what makes a notice the same notice
across polls. So when a notice came back, the collector had nowhere to put the second
appearance except the row already there: it cleared the closing timestamp, incremented a
reopen counter, and left the first-seen timestamp alone. The site then read one row as one
listing, first seen to closed, and **the absence in the middle vanished**.

The reopen counter had recorded this happening six times in the first month, five of them lift
or escalator notices. Nothing downstream read it. No test covered it.

That last part is the interesting bit, because there *was* a test that looked like it did:
`test_a_notice_that_comes_back_a_poll_later_is_a_separate_outage`. It gives the returning
notice a corrected start time, which changes the identity key, which makes a genuinely new row.
So it exercised the case where the collector's own mechanism produces the right answer for
free, and never the common case, where it does not.

> **Concept: a test that exercises the easy half.** A test named for a behaviour is not evidence
> the behaviour holds. This one passed for years of commits while the thing it was named after
> was broken, because its fixture happened to take a path where the bug cannot occur. That is
> not a badly written test, it is a badly chosen input: the returning notice was given a
> *changed* start, which is the rare case, and the unchanged return, which is what actually
> happens, was never run. The general check is to ask what the fixture makes true incidentally,
> and whether the code under test would still be exercised if that incidental thing were
> removed. The related habit from chapter 08 is the same family: a predicate is only as good as
> the quantity it is computed over, and a test is only as good as the input it is computed on.

This was never a raw-log problem, which is the whole point of chapter 01's invariant. Every gap
is in the JSONL exactly as collected. The fix is a `rebuild`, not a correction anybody has to
write down and remember.

### One row per stretch

A **listings** table now holds one row per stretch a notice was continuously on the feed. A
reopen opens a new row rather than reviving the old one, and the site builds one outage per
row. The messages table keeps its own first-seen and closed timestamps, which still answer
"when did we first ever see this notice", a different question and not the one the bars ask.

Two alternatives lost. **Deriving the gaps in the site**, by walking runs against each notice's
last-seen timestamp, would have left the schema alone but puts the collector's knowledge in the
renderer and needs a scan of every run per notice. The collector is the thing that watches the
feed; when a notice stopped being on it is the collector's fact to record. And **dropping the
uniqueness constraint** to insert a fresh row per appearance would have duplicated every
notice's text and start across every stretch, for no gain, and the identity key is what makes
reissue detection work at all.

### Splitting the listing exposed a second flaw

Athy's lift has been listed continuously since collection began. It was absent from **exactly
one poll** on 21 August and back 29 minutes later.

With the grace at one miss, that closed and reopened the notice, and once listings were split,
the site published two outages: one "no longer listed 21 Aug", another starting half an hour
later. That reads as fixed, then broken again, which is the one claim this site must never
make.

The default grace is **2** now. The measurement that justifies it is the shape of the gaps in
the corpus, which sort into 1, 9, 79, 388 and 672 polls. There is nothing near the cut on
either side. The second miss only confirms the close, since the closing timestamp is still the
first poll the notice was absent from, so nothing measured moved. It is set in code rather than
in the environment file, because `rebuild` replays under whatever value is set when it runs and
a replay must not depend on a machine's local configuration.

### Worked example: the grace week that a four-hour gap would have refreshed

Splitting one notice into several stretches interacts with the planned-works grace from
chapter 04, and the interaction is not obvious.

The grace forgives works listed seven days or less **in total**. Split the listing and each
stretch is now its own outage, so a notice that ran six days, blinked out for four hours, and
ran another six would present as two six-day works, each inside the grace, each forgiven. A gap
would have laundered the works.

So the total is pooled across all of a notice's stretches before they separate. Without it, the
Dublin Pearse escalator's four-hour blip would have handed it a fresh grace week and taken it
from 20% to 41%, with nothing at all changed about the notice.

The review of that branch found the same idea applied twice by accident: the fold that merges
reissued notices was summing the pooled total per chain member, and a chain can hold two
stretches of one notice (A reissued as B, then reverted to A), so A's total was counted twice.
Five and a half days of works reported as nine, which crosses the grace and drops the grade.

## What the split moved

| station, August 2026 | before | after |
|---|---|---|
| Portlaoise | F, 29% | **D, 83%** |
| Thurles | F, 25% | **E, 54%** |
| Clondalkin Fonthill | F | **E, 70%** |
| Dublin Pearse | F, 20% | F, 20% |
| Midleton | F, 0% | F, 0% |

The last two rows matter as much as the first three. Midleton really was listed from the day
collection began to the end of August, in 1,087 consecutive successful polls with no gaps, and
its 8 August edge is the collection horizon rather than the outage's start. The Pearse escalator
really did come down at exactly the end date Irish Rail wrote on it, which is the one place in
this corpus where that placeholder field turned out to predict something. Chasing those two,
because they *looked* wrong, is what found the notice that was actually broken.

One smaller fix landed in the same window. The overview's "still out when the month ended" tile
read 0 for every past month, because its test could only be true in the horizon's own month. It
counts an outage that ran past the boundary, or one still open exactly at it, and excludes a
notice that came down at the boundary poll.

## Where it left the site

A page that is at most a few hours behind the feed instead of up to a day, a threshold sized to
the new cadence, and a bar that shows the days a notice was actually on the feed rather than
the envelope of its first and last appearance. As of 4 September 2026 the database holds 285
listings across 281 messages, four of which have more than one stretch.

## Notes

- PR #39, "Publish on the data landing, not on a cron that runs hours late" (2 Sep 2026): the
  cron timing table, the dispatch-on-push change, six-hourly pushes, `STALE_AFTER` 16 h to 10 h,
  and the deployment ordering.
- `notes/publish-cadence.md`, and its § The banner blamed the wrong half.
- PR #42, "Record one listing row per stretch a notice was on the feed" (3 Sep 2026): Portlaoise,
  the listings table, the grace default, the pooled planned total, the back-dated span for
  notices open before the table existed, and the three review findings.
- `notes/site.md` § A notice that came back was published as never having left (2 Sep 2026),
  which carries the rejected alternatives.
- PR #44 and issue #36: the past-month ongoing tile.
- Measured 4 Sep 2026: 285 listings across 281 messages, 4 messages with more than one stretch;
  1,264 runs, 1,261 ok. Grade moves as tabulated are from PR #42, measured 3 Sep 2026.
