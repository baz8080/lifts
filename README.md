# lifts

Tracks lift (elevator) outages at Irish Rail stations over time, by polling
Irish Rail's realtime service-message feed every 30 minutes and recording
which messages are present. Built to run unattended on a Raspberry Pi for
years, so it can accumulate enough history to look for patterns - which
stations break most, how long outages tend to last, whether there's
seasonality, and so on.

The collected data is published as a status site at
<https://baz8080.github.io/lifts> - see [The site](#the-site) below.

Sibling project: [`esb`](https://github.com/baz8080/esb), which does the same
thing for ESB Networks power outages. This project mirrors its architecture
closely, adapted for a simpler single-endpoint API.

## How it works

`GET https://connect.irishrail.ie/realtime/messages?lang=en` returns a flat
JSON list of every current service-message banner - lift outages, but also
unrelated notices, since the feed isn't lift-specific. Every message seen is
recorded verbatim, regardless of content; filtering "is this actually about a
lift" is left as a query-time concern over the stored data, not a collection-
time decision.

There is no reliable way to ask "is this fixed yet": each message carries an
`end` field, but in every message observed so far it's set to a placeholder
date near the end of the current calendar year, unrelated to when the actual
issue is likely to be resolved. It's recorded anyway (in case it turns out to
be useful later), but the only signal this project actually trusts for
"fixed" is **a message that was present in one run and is absent from the
next**.

Since the API has no ID field for a message, identity is derived from `head`
+ `locationCodes` + `start`. This means an edited message (Irish Rail
tweaking the wording, or correcting a start time by a few minutes) will look
like the old message closing and a new one opening - a known, accepted
limitation. Raw responses are kept forever, so this can be reprocessed with
smarter matching later if it turns out to matter.

The design's central concern is making sure a *failed* poll (network error,
rejected API key, a changed response shape) can never be misread as "the list
came back empty" - which would otherwise mark every currently-open message as
fixed. See `lift_status/poll.py` for how that's enforced structurally, not
just checked at runtime.

## Storage

- `raw/messages-YYYYMMDD.jsonl` - one line per poll *attempt*, success or
  failure, written before any parsing. This is the actual source of truth.
- `lift_status.db` - a derived SQLite database, entirely rebuildable from the
  raw log via `rebuild`. Never back this up; back up `raw/` instead.

`messages` holds one row per notice, keyed by identity, and `listings` one row
per stretch that notice was continuously on the feed. A notice that vanishes
and comes back keeps its `messages` row and gains a second `listings` row: the
gap between them is what the site measures, so it cannot live in a row that
spans it.

## CLI

```
python3 -m lift_status poll         # run one collection pass (the scheduled command)
python3 -m lift_status check        # verify the API key/connectivity; writes nothing
python3 -m lift_status test-alert   # send a test alert through LIFT_STATUS_ALERT_WEBHOOK
python3 -m lift_status rebuild      # rebuild the database from the raw JSONL logs
python3 -m lift_status stats        # summarise what has been collected
```

All accept `--data-dir` (default: `$LIFT_STATUS_DATA_DIR`, or `/data`).

### Environment variables

| Variable | Purpose |
|---|---|
| `LIFT_STATUS_DATA_DIR` | Storage root (default `/var/lib/lift-status` once installed) |
| `LIFT_STATUS_API_KEY` | **Required.** The `x-api-key` value, captured from a browser session. Deliberately not stored in this repository |
| `LIFT_STATUS_ALERT_WEBHOOK` | Where failure alerts are POSTed (an ntfy.sh topic URL works out of the box). An unchanged alert repeats at most daily, so a stuck fault doesn't push every 30 minutes |
| `LIFT_STATUS_GRACE_MISSES` | Consecutive misses before a message is marked closed (default `2`). It still closes at the *first* miss; the second only confirms it |

## The site

`lift_site` builds a static status page from the collected data and publishes
it to <https://baz8080.github.io/lifts> - lift (elevator) and escalator
outages by station, month by month, drilling into each station's full history.

```bash
python3 -m lift_site --data-dir /var/lib/lift-status     # writes out/site/
```

It reads `lift_status.db`, so run `rebuild` first if the database is stale.
The overview lists the stations with a notice in the selected month; a
station's page shows every month since collection began. Everything measured
is the interval a notice was *listed* for. The start date Irish Rail writes on
a notice is shown as their claim but colours nothing, because it routinely
predates the listing by months over days the feed was watched and the notice
was not there - notices have been seen to appear and disappear in batches,
months after the start date they carry. "No longer listed" is the word used,
never "fixed": there is no completion signal in the feed.

A station is graded on **lift availability**: the share of the days watched on
which no lift notice was listed there. The scale is this site's
own - the PRM TSI sets design rules and a duty to hold a written access
policy, not a number, and Irish Rail publishes no availability target - so the
bands are calibrated in days: A is 100% available, B 95%+, C 90%+, D 75%+,
E 50%+, F below that. A is not "nothing listed": planned works inside their grace are
drawn on the bar and left out of the total.
Planned works are excused for their first week and count in full past it, in
their own colour once they do.
Escalator notices keep their own bar and are off the total: an escalator is
never a step-free route, so its going out removes a way up for anyone who finds
stairs hard, and not a step-free route; each escalator outage on a station page
says so, and what Irish Rail's page puts on the same leg.
The grade is named for what it counts and not "step-free availability", because
a lift out knocks it even where Irish Rail's page names a ramp round the lift,
and so does an outage the site cannot read either way. The one escalator outage
that should knock, an escalator that is the only powered way up, has no example
yet; `notes/site.md` carries the rule and a test on the real corpus fails the
day it applies.

A reissued notice that appears at the very poll the old one vanished is one
outage with the reissue noted; a notice that comes back a poll or more later
is a separate outage, because the gap is what the site is measuring.

`notes/site.md` has the decisions and the numbers behind them.
`.github/workflows/pages.yml` rebuilds the database from
[`lifts-data`](https://github.com/baz8080/lifts-data) and publishes the site. It
runs on every push to `main`, twice a day on a fallback cron, and - the trigger
that actually keeps the page current - whenever `lifts-data` itself is pushed to.
That last one is a workflow in `lifts-data` calling this workflow's
`workflow_dispatch`, and it needs a fine-grained token with **Actions: write** on
this repository stored there as the secret `SITE_BUILD_TOKEN`. Without it the
dispatch fails visibly on each push and the site falls back to the cron.

Pages needs enabling once, under **Settings → Pages → source "GitHub Actions"**.
GitHub disables the cron after 60 days without a commit to *this* repository -
the data lands in `lifts-data`, which does not count - so re-arm it when the
email arrives. `notes/publish-cadence.md` has why the cron is only the fallback.

## Running the tests

Standard library only, no dependencies to install:

```
python3 -m unittest discover -s tests -t .
```

`tests/test_site_real.py` runs the site pipeline against the real corpus and
skips unless `LIFT_STATUS_DATA_DIR` points at a data directory with a rebuilt
database; CI sets it. `uv run --group dev ruff check` lints - uv and ruff are
development tooling only, nothing at runtime needs them.

The most important test is `tests/test_rebuild.py`: it drives a realistic
run history (opens, updates, a close, a failed run that must change nothing,
a reopen, a duplicate, a schema-drift item) through the real `poll` code
path, wipes the database, rebuilds it from the raw log alone, and asserts the
result is identical.

## Deploying to a Raspberry Pi

```
git clone git@github.com:baz8080/lifts.git
cd lifts
sudo sh scripts/install-native.sh
```

This is idempotent - re-run it after a `git pull` to deploy an update. It
creates a `lift-status` system user, installs the code to
`/opt/lift-status`, creates `/etc/lift-status.env` (chmod 600), and installs
the systemd units. Then, following the printed instructions:

1. Set `LIFT_STATUS_API_KEY` in `/etc/lift-status.env` (chmod 600, root-owned).
   The key is not in this repository: it is Irish Rail's credential, captured
   from a browser session, and committing it would publish it to everyone who
   can read the repo. Capture it as described under "Recovering from a rotated
   API key" below. With no key set, every run fails loudly with a "NO API KEY
   CONFIGURED" banner rather than quietly collecting nothing.
2. Set `LIFT_STATUS_ALERT_WEBHOOK` in the same file - pick an unguessable
   ntfy.sh topic name, e.g. `https://ntfy.sh/<random-string>`, and subscribe to
   it on your phone. **This step is not optional**: Irish Rail can rotate the
   key at any time without notice. Without alerting, collection can stop
   silently and nobody will know until the gap in the data is noticed much
   later.
3. `sudo lift test-alert` - confirm the alert actually reaches your phone.
4. `sudo lift check` - confirm the current key still works.
5. `sudo systemctl start lift-status.service` for one run now, then
   `sudo systemctl enable --now lift-status.timer` for every 30 minutes.

### Setting up the data backup

Raw logs back up to a separate repository (`lifts-data`), pushed every six hours
via a dedicated deploy key - mirroring the `esb`/`esb-data` pattern:

1. Create a new (can be public) GitHub repo, e.g. `lifts-data`.
2. Generate a deploy key with write access:
   `sudo ssh-keygen -t ed25519 -f /etc/lift-status-deploy-key -N ""`, then add
   `/etc/lift-status-deploy-key.pub` to the repo's Deploy Keys with write
   access. **`chown` the private half to the service user** -
   `sudo chown lift-status:lift-status /etc/lift-status-deploy-key` - since
   `ssh-keygen` run under `sudo` leaves it root-owned, mode 600, and
   `lift-status-backup.service` runs as the unprivileged `lift-status` user,
   not root.
3. `cd /var/lib/lift-status && sudo -u lift-status git init -b main && sudo -u lift-status git remote add origin git@github.com:<you>/lifts-data.git`
4. `sudo systemctl enable --now lift-status-backup.timer`

Separately, point your own NAS backup at `/var/lib/lift-status/` for a second
copy - it's a plain directory of a SQLite file and JSONL text files, nothing
NAS-backup-unfriendly about it.

### Recovering from a rotated API key

The key lives only in `/etc/lift-status.env` on the Pi, never in this
repository. If `sudo lift check` starts failing, or an alert titled "API KEY
REJECTED" arrives: open `https://www.irishrail.ie` in a browser, open
devtools' Network tab, find the request to
`connect.irishrail.ie/realtime/messages`, and copy the `x-api-key` header
value into `LIFT_STATUS_API_KEY` in `/etc/lift-status.env`. No data is lost
while this is broken except the gap in coverage itself - the raw log and
database are untouched by an auth failure.

## Known limitations

- **Identity drift**: an edited `head` or a corrected `start` time produces a
  new identity key, which looks like the old message closing and an
  unrelated new one opening. Raw responses are kept forever in case this
  needs smarter reprocessing later.
- **No completion signal from the API**: `end` is recorded but not trusted;
  "fixed" is inferred purely from a message's absence in a later run.
- **Flapping**: `LIFT_STATUS_GRACE_MISSES` defaults to `2`, so a notice gone
  from one poll and back at the next is treated as the feed blinking rather
  than as an outage ending. A miss absorbed by the grace extends the open
  `listings` row instead of starting a new one, and the close is still dated
  to the first miss, so the grace costs nothing but a poll's delay. Raise it
  further if longer blips show up.

## Credits

The lift and escalator glyphs on the day bars are `elevator` and `escalator`
from [Material Design Icons](https://pictogrammers.com/library/mdi/) by
Pictogrammers, used under the Apache License 2.0. They are inlined into every
page as CSS masks; the path data and this credit sit together in
`lift_site/site.css`.
