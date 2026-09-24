# 18. The one code a rebuild cannot undo
*~9 min read · PRs #57, #58 · 20 to 24 September 2026*

*Where we are:* chapter 01 built everything on one rule: the raw log is the truth, and anything
derived from it can be thrown away and rebuilt. This chapter is about the code *upstream* of the
log, where that rule gives no protection at all, and about one sentence in chapter 01 that did
not hold.

## The question that opened this stretch

Every part of this repository had been reviewed, line by line, as it changed, except the part
that changed least. Was that the part that needed it least?

## What changed

### Why the collector, and only the collector

The collector was written on 18 August, before pull requests here went through a review agent.
It then barely changed. Three of its files were never touched again, and the poll loop changed
by sixteen lines. Everything built after it, the access derivation and most of the site, was
reviewed diff by diff from 26 August, and the real-corpus and golden tests pin what those parts
publish.

The argument for reviewing the collector, and nothing else, as whole files on 24 September is
one sentence in the note: it is **the only code whose mistakes a rebuild cannot undo**. A parse
bug is fixed by fixing the parser and replaying the log. A response that never reached the log
is gone.

> **Concept: the invariant has an upstream edge.** "The log is the truth and everything else is
> disposable" protects everything that runs *after* the log is written, and it makes review of
> that code cheaper, because any mistake can be replayed away. It protects nothing that runs
> *before* the write: fetching, retrying, deciding whether to write, and the order of the write
> relative to everything else. Those mistakes are permanent, and their cost is data you never
> find out you lost. So review effort should follow how reversible a mistake is, not how
> recently the code changed. By that measure the oldest and quietest code in the repository was
> the most urgent to review.

The review made ten findings. Eight were fixed, one turned out not to be a real path, and one is
left as it is by the owner's decision. Ten is close to the nine that the first review of the
access branch found (chapter 12), so the collector was not unusually careless. It had just never
been looked at.

### The log waited on the database

Chapter 01 said the raw line is written **before any parsing happens at all**. That was true.
What it did not say, because nobody had looked, is that the line was written *inside* the block
that opened the SQLite database and ran its schema. So if a power cut left the database corrupt,
or something held it locked past five seconds, every poll failed before reaching the log. The
failure came with a traceback and no alert.

The derived index could cost the source of truth, which is the dependency chapter 01 exists to
rule out, running the wrong way. Now the append happens before the database is opened, and it is
the only way a line gets written. A database failure has its own exit code, 7, and its own alert,
which says the response was kept and what to do about a lock, a full card or corruption.

### Three more ways a line could be lost

- **A full SD card was a traceback, not the storage alert.** The storage check touched an empty
  file. An empty file needs no data block, so it can be created on a full disk. This is chapter
  08's shape again, a guard that passes because what it checks is absent. Chapter 08 audited the
  collector for exactly that shape and found two, and this one was missed. An error from the
  append itself now goes to the storage alert.
- **A cut-off last line took the next good one with it.** A power cut in the middle of an append
  leaves a line with no newline, and the next run's line was appended onto the fragment, so
  replay dropped both. The append now finishes the broken line first, and only the fragment is
  lost.
- **A truncated gzip body escaped the retry.** Python reports a cut-off compressed body as an
  `EOFError` or a `zlib.error`, and neither is the network error the client was catching. So the
  attempt skipped the retry, the raw line and the alert. Now they count as transient.

Two more were about the collector being stopped or silenced:

- **systemd could kill a poll before it logged anything.** The unit allowed 60 seconds. The
  client's own worst case is three attempts, each with a 15-second connect and a 15-second read,
  plus backoff and DNS: well over 90 seconds. It is 300 now.
- **A second outage within a day of the first was silent.** This is the same 24-hour
  repeat-suppression window chapter 08 fixed once already, when it opened on the attempt rather
  than the delivery. The marker also outlived a recovery, so if the same fault came back after
  a clean stretch, it was suppressed. The marker now clears after four clean runs in a row, which
  is two hours. A suppressed failure resets that count, so an API that keeps flapping still sends
  one alert a day. Clearing the marker on the first clean run was tried and rejected in review,
  because a flapping API would then alert on every failure.

The backup could also hang forever on a half-open ssh connection, and every later firing did
nothing while it hung. It now has timeouts on the connection, a 15-minute cap on the unit, and a
trap that makes sure hitting the cap still sends an alert.

### The one keyword argument was not the whole story

Chapter 01, on the line `json.dumps(..., sort_keys=True)`:

> Because the keys are always in the same order, the same observation written by two different
> machines produces byte-identical text, so two collectors' logs can be merged with `sort -u`
> and the duplicates simply vanish. That is the whole of the multi-machine story, and it is one
> keyword argument.

The duplicates do vanish. But `sort -u` removes duplicates *by sorting*, and sorting puts lines
in an order of its own. With sorted keys, the first key on every line is `body`, the whole feed
response. So a merged file comes out grouped by what the feed said, not by when it said it. And
replay read the file in line order, so the afternoon's polls, where a notice had come down, could
be replayed before the morning's, where it was still up. That is a different history, with
outages opened and closed at the wrong times.

`sort -u` is also how a git conflict on a shared day file gets resolved, and the backup merges
from the remote, so this was not just a thought experiment. Replay now sorts each file by its
fetch timestamp, stably, and the order lives in the data rather than in line positions.

> **Concept: a merge that deduplicates also reorders.** Any merge that removes duplicates by
> sorting puts its output in an order of its own choosing. If anything downstream treats line
> position as meaning, that merge has quietly rewritten the history. The fix is to make the
> order explicit: sort on a field that carries it, at the point where order matters. Then say
> what the explicit order costs, because a timestamp is only as good as the clock that wrote it.

The cost is written into the note. After a power cut, the Pi has no hardware clock, so it
restores the last hourly save. A catch-up poll can then be stamped up to an hour *before* runs
already in the same file. A rebuild now applies it before them, where the live run applied it
after. Line order only ever covered part of that case, since a stamp that crosses midnight
already lands in the wrong day's file, and line order cannot survive a merge at all. It was the
owner's call: merging logs has to work.

### Worked example: the claim that nothing moved

The claim is that on the real data this changes nothing. That can be checked rather than
argued. On 24 September, all 2,224 raw lines were already in time order within their files, and
`rebuild` followed by `stats` gives identical output before and after every commit on the
branch. So the reordering hole had never fired. It was waiting for the first real merge.

### What was not a path, and what was left

The review also flagged that the backup merges from the remote without taking the poll lock.
That turned out not to be a real path. A merge only rewrites files that changed upstream, and
nothing but the Pi writes the raw logs. Taking the lock for a whole fetch and push would make a
poll skip, which is worse.

One finding was left alone. After a reboot, systemd's time-sync target is reached as soon as the
time service starts, not when the clock is actually right, unless a wait service is enabled.
Enabling it risks a poll that never runs if NTP is unreachable, and a silent poll is exactly
what this collector exists to prevent. The note records what the fix would look like if it is
ever taken up: a poll that checks whether the clock is synced and still writes the line, flagged,
rather than one that waits or skips.

### What a comment is for

Four days earlier, PR #57 rewrote this repository's rule on code comments, because comments kept
arriving in volume. A comment now earns its place only when it records something the reader
cannot see: an external system's behaviour, a measurement, a dependency nothing else records, a
reason the obvious approach was rejected, or a trap that would otherwise be refactored away.

The collector review is a demonstration of that list. What it added next to the code is a power
cut leaving a line with no newline, a probe file that passes on a full card, and a shell that
skips its exit trap on a signal it does not trap. None of those can be seen by reading the line
below, and each would be the first thing a tidy-minded refactor removed.

## What this corrects in the series

Chapter 01 is left as written. Two of its sentences are corrected here:

- "Written before any parsing" was true, and the line was still written after the database was
  opened. A broken derived index could cost a raw line until 24 September.
- `sort_keys=True` made merged logs deduplicate. It did not make them replay correctly, because
  the merge reorders them. That took a second change, in replay, and it carries a stated cost.

## Where it left the site

Nothing on the page changed, and on the real corpus nothing in the database changed either,
which is the point. The collector now puts the raw line first unconditionally, reports each way
of failing under its own name, and can have its logs merged without rewriting their history.
The unit files and the backup script only take effect on the Pi after a reinstall.

## Notes

- PR #58, "Review the collector: the raw line no longer waits on the database" (24 Sep 2026):
  the ten findings, the second review of the PR itself, and the verification list.
- `notes/collector-review.md`, dated 2026-09-24, which carries each finding, the rejected
  first-run clearing of the alert marker, the `fake-hwclock` cost and the NTP decision.
- PR #57, "Say what a comment has to record to earn its place" (20 Sep 2026): `CLAUDE.md`
  § Comments. Documentation only.
- Chapter 08's guard shape: the review findings there, the two found by auditing the collector
  for it on 30 Aug 2026, the dropped-record check in chapter 14, and the storage probe here.
- 2,224 raw lines in time order within their files, measured 24 Sep 2026 and stated in the note;
  `rebuild` then `stats` gives 2,224 runs (2,217 ok, 7 unreachable), coverage to
  2026-09-24T05:02:51Z.
- The client's worst case is from the note: three attempts of a 15 s connect and a 15 s read,
  plus backoff and DNS, against `TimeoutStartSec=60`, now 300.
