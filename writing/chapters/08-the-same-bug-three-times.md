# 08. The same bug, three times
*~9 min read · PR #30's reviews and PR #34 · 30 August 2026*

*Where we are:* the access derivation from chapter 07 is written and reviewed. This chapter is
about what the reviews found, which turned out to be one bug wearing several coats.

## The question that opened this stretch

Two code reviews ran over the access branch. The second one found three defects, and reading
them together produced an uncomfortable observation:

**All three were the first review's findings, reappearing in the code written to fix them.**

That is worth recording as a habit rather than as three bugs, because a habit can be looked for
and three bugs cannot.

## What changed

### The three repeats

- **A stale reviewed entry forfeited every other platform.** The first review found that a
  notice naming platforms the page does not list a lift at was discarding the platforms it
  *did* know, and it was fixed by partitioning the known from the unknown (chapter 07, Athy).
  The staleness check added afterwards, which handles a reviewed exception whose sentence has
  been reworded, repeated the same mistake: a reworded Cork page would have taken platform 7
  down along with 5A. Same partition, applied again.
- **A caveat was shown where no derivation ran.** The first review found the step-free pill
  rendering for a station absent from the snapshot. The "this is an inference" caveat added
  afterwards was a single global flag and did exactly the same thing, so "worked out from Irish
  Rail's page" could sit directly above "this station is not in the station snapshot". It is
  gated per station now.
- **The correction link pointed at pages that do not exist.** The prefilled issue link was
  slugged from the snapshot's station name, while the site's pages are named from the newest
  notice's name. Those differ at Clondalkin and Hazelhatch. Both the slug and the issue title
  now come from what the page is actually called.

And one that was nobody's fault twice over: **a notice naming both machines read as unknown.**
`classify` puts lift first, so "Lifts and escalators out of order" is a lift notice whose text
names an escalator, and a guard designed to catch a mis-headed notice fired on it. The worst
case for a reader became the least informative verdict. The guard now distinguishes a text
naming only the *other* machine, which means the head is probably wrong, from one naming both,
which is a combined outage: whatever else broke, the lift is out, so the platforms are lost.

### The shape underneath them

Strip the specifics and the same defect is in all of them, and in two more found later. Call it
what it is:

> **Concept: a guard that passes because what it checks is absent.** A guard is a predicate over
> some quantity: *every station in the snapshot has a verdict*, *the replay recovered rows*,
> *this alert reached the phone*. The failure mode is not the predicate being false. It is the
> predicate being computed over a set that is **empty or wrong**, so it comes out true
> vacuously, at precisely the moment the thing it was written to protect has gone missing.
> "All 38 stations I fetched are present" is true when only 38 of 152 were fetched. "Nothing
> was left to replay" is true when the directory is wrong. Every one of these passes cleanly,
> logs nothing alarming, and exits zero. The check for it is a question, asked of every guard:
> *what does this assert when the input is missing entirely?* If the answer is "success", the
> predicate is over the wrong quantity.

Once that shape had a name, the rest of the codebase was audited for it, and it turned up twice
more, both in the collector and neither with anything to do with the site.

### A partial fetch shadowed the last good snapshot

`latest_snapshot` reads the newest file in the station directory. So a snapshot written during
an irishrail.ie wobble, holding 38 empty bodies out of 152, permanently shadows the last good
one, and the damage is invisible: those stations lose their verdicts to "not in the station
snapshot" and the denominator quietly shrinks. Nobody spots 38 empty bodies in an 8 MB diff.

Transient failures are retried, and if any station is still missing, **nothing is written at
all**. A run whose entire job is to report which stations it could reach must not half-succeed
into the same filename slot as a full success.

### `rebuild` emptied the database and reported success

This one is the cleanest instance and the most alarming.

`reset_derived_tables()` runs before the first line of the log is read, so the wipe is
unconditional. If there is nothing to replay, because `--data-dir` points at the wrong place,
or a drive is not mounted, or `raw/` has been renamed, then the guard on "recovered zero rows"
was a printed note rather than a protection, and the exit code said success.

Measured against a copy of the real corpus:

```
before:  messages: 228   runs: 1012
rebuilt from 0 recorded run(s)
nothing to replay: no raw logs found
rebuild exit code: 0
after:   messages: 0     runs: 0
```

It knew the logs were missing. It said so. It had already destroyed the tables, and it exited
zero.

The invariant from chapter 01 makes this recoverable rather than fatal: the raw log is the
source of truth and the database is disposable, so re-running `rebuild` against the right
directory restores everything. What is **not** recoverable is an exit code that says the
rebuild worked. In CI the site build happens to catch it downstream, because a build with no
outages returns a failure, but nothing else does.

The fix used something already there. `reset_derived_tables` deliberately runs inside the
caller's transaction, with a comment saying it does so a failed rebuild takes the wipe back. So
the fix is to notice that and use it: **a replay that recovered nothing, from a database that
had history in it, is refused and rolled back.** Returning 1 unconditionally would have been
wrong, because a fresh install has nothing to replay and nothing to lose, and still exits zero.
A log of nothing but truncated lines is refused the same way.

### The alert window opened on the attempt, not the delivery

The collector alerts to a phone when a run fails, and suppresses a repeat of an identical alert
for 24 hours so a stuck fault does not push every 30 minutes.

The suppression marker was written **before** the webhook was tried:

```
delivered: False
marker on disk: {"digest": "32465c90...", "sent_at": 1788105365.6}
second attempt suppressed: True
```

So one transient failure at the moment the collector first breaks buys a full day of silence,
and that first attempt is exactly where silence costs most: the API key rotates without notice,
and a silent collector loses data that cannot be recovered later.

The module is otherwise carefully fail-open, with every read error meaning "send anyway". This
was the one path that failed closed. The value needed was already in hand, since `notify`
returns whether it was delivered and the caller already consumes that, so the marker is now
written only once the webhook has taken it.

### One that was left, on purpose

`has_lift` tests the explicit denial before the claim, so a hypothetical per-platform "no lift
on this side" would silence a lift the same page claims elsewhere. Fixing it properly means
making the denial per-platform, which is a modelling decision with no data to design against:
Dromod is the only station using the phrase and it genuinely has no lift. It fails to
`unknown` rather than to a false claim, which is the safe direction from chapter 07. Left until
something real turns up, and written down so the next person does not rediscover it.

Two others were latent, with no instance in the data, and were taken anyway because the fix was
a token each and the failure would have been silent: a block tag carrying an attribute, the
`<br class="x">` a CMS paste produces, missed the separator pattern and joined two access lines
into one, which manufactures a false *specific* and defeats specific-beats-general from the
other side; and a response body that is not UTF-8, or an index that is an HTML error page,
raises an exception that neither of the two handlers catches, aborting a run whose entire job
is to report which stations it could not get.

### The one that was carried, measured, and removed

The same discipline killed a feature I liked.

OpenStreetMap was carried as a second opinion on Irish Rail's prose. It is the only
machine-readable station graph that exists for this network: around Dublin Pearse there are
named platform ways, four lift nodes carrying floor-level tags, escalators tagged as conveying
steps, corridors, wheelchair tags. A routable topology, which is the thing `pathways.txt` would
have been. It also spots 13 stations where the prose mentions no lift and OSM maps one,
Limerick Junction among them.

Three measurements, all against the real data, ended it:

1. **It changed no verdict.** The lift check was consulted in exactly one place, as a test for
   "not yes", and OSM could only move a station from "no" to "unknown". Both fail that test.
   Checked with a synthetic digest mapping a lift at all 152 stations: 24 outages, **0 verdicts
   changed**.
2. **Its one signal was redundant.** A station in those 13 that has a notice already returns
   `unknown` without it. Limerick Junction: same verdict, same wording, with or without.
3. **It could not answer the street-side question**, which is the only thing that would have
   earned its keep. "Which platform is reachable without a lift" needs floor-level tags on
   platforms. Sampled over the 12 stations that have had notices: 12 of 12 had platforms
   mapped, and **2 of 12** carried a level tag, both of them Dublin termini.

Irish Rail's prose answers that same question at 32 of 57 stations, in words.

So it went: about 60 lines, a monthly HTTP budget against a service that rate-limits, and the
one place the raw-artefact invariant had to be bent, since the map extracts run to roughly
450 MB and the digest had to be derived rather than stored verbatim. For nothing that reached a
reader. The note records all of it at length so nobody adds it back on the same hunch, because
the hunch is a good one.

## Where it left the site

No behaviour change a reader can see, which is the point. A collector that refuses to report
success after destroying its own tables, an alerting path that cannot be silenced by one failed
delivery, a fetch that is all-or-nothing, and a feature removed on measurements rather than
taste.

This chapter has no sibling contrast. The other two series have their own review stories and
their own bugs, and none of them is this one.

## Notes

- PR #30's second review, recorded in `notes/station-access.md` § What the second review caught
  (30 Aug 2026): the three repeats, the both-machines notice, the two latent fixes and the one
  deliberately left.
- `notes/station-access.md` § Three things a review caught (30 Aug 2026): the summary-sentence
  rule, the expiring reviewed entry, and the partial-fetch refusal.
- PR #34, "Refuse a rebuild that recovered nothing, and time the alert window from delivery"
  (30 Aug 2026): both transcripts quoted above, `tests/test_alert.py` (new; the repeat window
  had no coverage at all), two new cases in `tests/test_rebuild.py`, all four failing against
  the unfixed source.
- `notes/station-access.md` § OpenStreetMap: carried, measured, removed (30 Aug 2026), and
  issue #29, closed. The 32-of-57 figure it is compared against is from the same note.
- The audit that produced PR #34 was prompted by the shape turning up three times in one review
  round, which is stated in PR #34's own body.
