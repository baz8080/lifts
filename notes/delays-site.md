# A site for the delay notices - 2026-09-11

The feed this collector polls is every service banner Irish Rail publishes, of
which the lift and escalator ones are 51 of 416. The rest are mostly delays, and
they now have their own site: `baz8080/rail-delays`, which reads `lifts-data`
and publishes them.

This note is what that decision cost **this** repository, which is almost
nothing, and the one trap it turned up in the collector. How a cause is read and
what the delays site publishes are that repository's own notes.

Corpus throughout: the 416 distinct (head, text) pairs in
`lifts-data/raw/messages-*.jsonl` between the first poll on 2026-08-08 21:30:55Z
and 2026-09-11, over 1620 successful runs.

## The collector is already collecting this

The question "a second collector, or a delay poll target added to `lift_status`"
has a shorter answer than it looks: **there is nothing to collect**. One endpoint
returns the whole feed in one response - `client.py` says so and the log proves
it - and `store.write_raw` writes that response verbatim before anything reads
it. Every delay notice the other site will ever show is already on disk, back to
the first poll.

So both alternatives are rejected on cost, and the cost is not small:

| option | what it costs | what it gains |
|---|---|---|
| A second collector | Two pollers on one credentialed endpoint Irish Rail rotates without notice, so twice the request rate and a second place the key has to live; a second Pi install; ~60 MB a year of duplicated raw log; two logs that disagree about the same feed because they poll at different instants | Nothing. The bytes are identical |
| A "delay poll target" in `lift_status` | A day spent discovering there is one URL and one response | Nothing |
| Read `lifts-data` as it stands | Nothing | Everything, once § *The trap* below is dealt with |

`lift_status` is a general Irish Rail service-message collector with a
lift-shaped name. That is worth saying plainly rather than renaming: the name is
on a Pi, in a systemd unit and in `install-native.sh`, and the misnomer costs one
sentence of explanation where a rename costs a redeployment.

**Settled: the collector is not duplicated, not extended, and not touched.**

A `delay_site` package in this repository was rejected too, and that one was
tempting because it is cheapest to start. It is wrong within a month: this
repository's CI becomes the gate on two sites, a red `test_site_real` blocks a
delays fix, and a repository publishes one Pages site, so the delays would have
had to live under `baz8080.github.io/lifts/delays/` and claim to be part of this
one. One repository per site is what `uisce`, `esb` and `lifts` already do.

Renaming `lifts-data` to something neutral was rejected on the same grounds: it
breaks the Pi's push remote, all three workflows here, nine places in this
repository's `CLAUDE.md` and the sibling's checkout step, to fix a name nobody
reading either site ever sees.

## The trap: the feed empties `locationCodes`

The one finding here that is about this collector rather than about the other
site.

`derive_identity_key` is `head` + sorted `locationCodes` + `start`, and
`identity_fields_valid` routes an item with an empty `locationCodes` to
`unidentifiable_items` rather than to `messages`, so it takes no part in
open/closed tracking. That is the right call for a collector that cannot know
which station a notice is about.

**Irish Rail empties that field on a notice part-way through its life.** Over the
corpus, keyed on `head` + `text` + `start`, which is deliberately not the
collector's key: `head` moves on these, so the collector's own key cannot group
them at all.

| | notices | never carry codes | lose them partway |
|---|---|---|---|
| lift and escalator | 55 | 0 | 0 |
| everything else | 497 | 21 | 288 |

565 item sightings go to `unidentifiable_items`, 9.5% of every non-lift sighting,
and that is what fills a table this repository otherwise never looks at. 309 of
the 552 notices go empty at some point and only one of those ever gets its codes
back; the other 308 keep `[]` until they leave the feed. So a delay notice's
tracked listing ends when Irish Rail strips the field, not when the notice comes
down.

**Nothing here is affected, and that is the point of recording it.** No lift or
escalator notice has done it once, which is why nothing in this repository ever
noticed, and why the identity model is not being changed to accommodate it. A
delay notice wants a different identity anyway: hold `start` and `locationCodes`
still and the head moves underneath them 63 times over the 725 groups on the
corpus, because a delay head carries the minutes and "+15mins delayed" becomes
"+21mins delayed" at the next poll.

**Settled: the delays site replays the raw logs and derives its own identity, as
`rebuild` does.** That read lives in `baz8080/rail-delays`. If anyone ever
changes `identity_fields_valid` or wonders why `unidentifiable_items` is full,
this is why.

## Which repository a change belongs in

The boundary, because it will be asked again. **The subject decides, not the
convenience.**

| | here | `baz8080/rail-delays` |
|---|---|---|
| The collector, `lifts-data`, the Pi, the poll | yes | never |
| Anything about lift and escalator outages | yes | never |
| Anything about delays, cancellations, suspensions and what they say went wrong | never | yes |
| A fact about the feed | only if this collector or this site acts on it | only if that one does |

The last row is the one that is easy to get wrong, and it was got wrong once
here: the apology sentence that ends in "caused", and the fact that `start` is a
departure time on a delay notice, were both written into this repository's
data-shape traps. They are traps for code that reads a cause or identifies a
train, and nothing here does either. They belong across the way and that is
where they are.

The trap above stays because it is the other way round: it is about
`identity_fields_valid` and `unidentifiable_items`, which are this repository's,
even though the notices it affects are not.

A fact both act on gets written in both, with the numbers, rather than one
pointing at the other. `lifts-data` is the shared thing, and the only one.

## What went the other way

`delay_cause`, the cause reader, was written here because this is where the
corpus and the test harness are, and moved whole once the repository existed. It
imports nothing from `lift_status`, `lift_site` or `lift_access`, which is what
made that a copy rather than a port.

Everything it settled - the eleven categories and their counts, the four markers,
what the reader refuses to say, and the apology sentence that ends in the word
"caused" - is in `baz8080/rail-delays` `notes/cause-reading.md`. What the site
publishes, and how a disruption is identified once `eventStops` empties out the
way `locationCodes` does, are in its `notes/site.md`.

## Left open here

- Whether `is_planned` becomes a call into that reader at all. A `planned`
  reading is a strict superset of `PLANNED_MARKERS` today.
