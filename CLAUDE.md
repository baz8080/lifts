# Working in this repository

Three things live here: `lift_status`, a collector that snapshots Irish Rail's
realtime service-message feed every 30 minutes; `lift_site`, a static site
generator that turns the result into https://baz8080.github.io/lifts; and
`lift_access`, which fetches what each station *has* so an outage can be read
against it. Only the first goes on the Pi - `scripts/install-native.sh` copies
`lift_status` and `scripts`, nothing else. **All three run
on the standard library alone** - `pyproject.toml` declares no runtime
dependencies and exists only for ruff and the dev tooling, because the collector
is installed on a Raspberry Pi by copying files. Keep it that way.

```bash
uv run python -m lift_status --data-dir <dir> poll      # one collection pass
uv run python -m lift_status --data-dir <dir> rebuild   # replay JSONL into lift_status.db
uv run python -m lift_status --data-dir <dir> stats
uv run python -m lift_site --data-dir <dir>             # build out/site/
uv run python -m lift_access --data-dir <dir> refresh   # station facts (monthly, not on the Pi)
uv run python -m lift_access --data-dir <dir> report    # every verdict beside its source prose
uv run --group dev ruff check
uv run python -m unittest discover -s tests -t .
```

Plain `python3` works for all of these too; uv only pins the interpreter, to the
3.14 in `.python-version`. That pin is the dev and CI interpreter, not the floor:
`requires-python` says **3.11**, because that is what Raspberry Pi OS bookworm
ships and the collector has to run there. `scripts/install-native.sh` gates on
the same number, ruff takes its target from it so the linter will not suggest
syntax the Pi cannot run, and CI runs the tests on 3.11 as well as 3.14 so the
floor is checked rather than declared.

The collected data is a separate repository, `baz8080/lifts-data`, normally
checked out at `../lifts-data`. Set `LIFT_STATUS_DATA_DIR` to it (after a
`rebuild`), or pass `--data-dir`. `tests/test_site_real.py` skips without it,
so run the suite with it set before shipping anything that touches the site.

In a Claude Code web session all of that is already done:
`.claude/hooks/session-start.sh` syncs the dependencies, clones or updates
`../lifts-data`, rebuilds the database and exports `LIFT_STATUS_DATA_DIR`. It
also clones `../statusui`, which the UI workflow below needs. Locally it exits
without doing anything.

## Looking at the built site

Chromium is on the box, and a change to the bars or the rows is worth seeing:

```bash
python3 -m lift_site --data-dir ../lifts-data                    # writes out/site/
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless --no-sandbox \
  --disable-gpu --hide-scrollbars --window-size=980,1300 --virtual-time-budget=3000 \
  --screenshot=/tmp/site.png file://$PWD/out/site/index.html
```

`--dump-dom` with a `<script>` that writes measurements into `document.title`
gets numbers out of a rendered page - widths, overflow, computed styles.

**Its layout viewport never goes below 500px**, whatever `--window-size` says. A
narrow shot is a cropped image of a 500px page, not a phone: an element hanging
off the right edge of the PNG is not proof of overflow (compare `scrollWidth`
with `clientWidth` instead), and a rule under `@media (max-width: 480px)` can
only be seen by raising its breakpoint in a copy of the built page.

Lifts are elevators outside Ireland; the page metadata says so for search engines.

## The UI is shared - change it upstream

The tokens, base CSS, row/bar/card components and the JS helpers that uisce, esb and lifts
all use come from [`../statusui`](https://github.com/baz8080/statusui), a **uv git dependency
pinned in `uv.lock`** (the `site` dependency group - `dependencies` stays empty for the Pi
collector) and inlined into every page at build by `statusui.assemble()`. Edit it there,
push, then `../statusui/rollout.sh` bumps the pin in all three sites and opens the PRs. This
site's own rules are `lift_site/site.css`; the shared/per-site rule is in statusui's
CLAUDE.md.

## The invariant

**The raw JSONL logs are the source of truth. The database is disposable.**
Nothing is parsed before it is written to the log, and `rebuild` replays the
logs through the same code path a live run uses. If a parse is wrong, fix it and
rebuild; never edit the logs. `json.dumps(..., sort_keys=True)` in
`store.py:write_raw` is load-bearing - it is what lets two machines' logs be
merged with `sort -u`.

## Data-shape traps

- **The feed is every service banner, not a lift feed.** Delays, cancellations,
  "Station currently closed" all arrive alongside. `lift_site.model.classify`
  picks out `head`s matching `Lift(s) out of order|service` and
  `Escalator(s) out of order|service`; 17 of the first 113 notices qualified.
- **There is no id.** Identity is `head` + sorted `locationCodes` + `start`
  (`parse.derive_identity_key`). An edited head or corrected start closes one
  message and opens another in the same poll; `model.merge_edits` folds those.
- **`start` is a Dublin wall-clock time with no offset**, and it routinely
  predates the notice being listed by months (Rush and Lusk: 451 days). The
  site measures the *listing* (`first_seen` → `end`), shows the start as Irish
  Rail's claim, and renders instants in Europe/Dublin. `notes/site.md`.
- **`end` is a year-end placeholder** for most notices (13 of 17). Shown, not used.
- **There is no completion signal.** An outage ends when its notice is first
  absent from a successful poll. Notices appear and vanish in batches; say
  "no longer listed", never "fixed".
- **The feed only names a station when something is wrong with it.** There is
  no roll of the stations that have a lift, so availability is aggregated over
  the stations listed in the month and the page says so; a wider denominator
  would be invented.
- **Every lift notice names one location code**; `eventStops[0].sStop` is the
  full station name. 131 delay notices had empty `locationCodes` and sit in
  `unidentifiable_items` - irrelevant to the site.
- **`platformAccess` prose is a description, not a route graph, and its "and"
  is a sequence.** Irish Rail's station pages say how each platform is reached.
  "All platforms can be accessed via lifts and ramps" means you need both, not
  either - reading it as a choice publishes "access remains" where access is
  gone. Two stations in the country name a step-free way round a lift.
  `notes/station-access.md`.
- **The lift-call sentence is boilerplate.** "To access the lift, you must call
  via the help point..." is template text, and at Greystones, Killiney and
  Donabate it is the only mention of a lift. Strip it before matching, or you
  invent lifts.
- **`wheelchairAvailability` is not accessibility.** It means a wheelchair can
  be borrowed at that station. The station `alert` field is stale too: it is the
  last alert ever posted, never cleared, with end dates back to 2014.
- **A run that failed is not a run that saw nothing.** `poll.py` enforces this
  structurally; the site's horizon is `MAX(started_at_utc)` over `outcome='ok'`
  runs only, and days past it are "no data".

## Settled - don't re-litigate without reading the note

| Decision | Where |
|---|---|
| The listing interval is measured; Irish Rail's start is shown, not measured | `notes/site.md` § The measured interval |
| Stations keyed by location code, named from the newest notice | `notes/site.md` § Rows are stations |
| Escalators included and tagged, never excluded (their own bar since 2026-08-28) | `notes/site.md` § Escalators, § One bar per kind |
| Same-poll reissues merge; a gap of a poll or more is a new outage. The collector records one `listings` row per stretch a notice was on the feed, because a reopen used to revive the `messages` row and republish the gap as listed time | `notes/site.md` § Notices reissued, § A notice that came back was published as never having left |
| A notice absent from a single poll is the feed blinking, not an outage ending: `DEFAULT_GRACE_MISSES` is 2, and the close is still dated to the first miss | `notes/site.md` § One missed poll is the feed blinking |
| The planned-works grace is earned per notice, pooled over all its stretches (`Outage.planned_total`), and spent per stretch - so a gap splits what is measured without refreshing what is excused | `notes/site.md` § The grace is earned per notice and spent per stretch |
| Planned works is what the notice text says | `notes/site.md` § Planned works |
| Stations are graded on lift availability - days watched with no lift notice - on this site's own scale, there being no Irish or EU target; an escalator notice has its own bar and knocks nothing. Named for what it counts, not "step-free": a lift out knocks even where the page names a ramp round it, and so does an unknown verdict. Overview sorts by listed-now, whatever the kind, then availability | `notes/site.md` § The grade is availability, § The grade is lift availability |
| The scale runs A to F inclusive. E splits the old F band at **50%**, which over a 31-day month is 8 to 15 days listed against F's 16 or more: up to half the month, then more than half. Every A-D cut is unmoved, and the cut lands in a real gap in the data | `notes/site.md` § The scale grew an E |
| Planned works are excused for their first week and count in full past it, in their own colour once they do | `notes/site.md` § Planned works are excused for a week, § Blue said two opposite things |
| A bar carries one kind and an escalator notice gets its own strip - separate bars, and only the lift bar's days are graded | `notes/site.md` § One bar per kind, § The grade is lift availability |
| Every bar names its kind with an MDI glyph in a gutter the same width on every row, and the word too where the bars are tall; the kinds are their own legend key, the day key still names no kind | `notes/site.md` § The bars say which kind |
| `end` printed as "listed end" while the notice is up, dropped once it comes down; plays no part in any measure | `notes/site.md` § `end` is shown, § Irish Rail's end date goes when the notice does |
| Windows end at the collection horizon; zero-minute listings count in its month | `notes/site.md` § Windows end |
| Displayed instants are Dublin wall-clock; build/horizon stamps are UTC | `notes/site.md` § Displayed instants |
| Station page shows every month, newest first; overview lists only stations with a notice that month | this file, and the ESB PR discussion |
| The Pi pushes every six hours and `lifts-data` dispatches the site build on each push; the two crons are a fallback only, because scheduled runs here have landed 4-10h behind their cron time. The stale banner trips at 10h - above the widest legitimate age (~7h), below a missed push (13h+) | `notes/publish-cadence.md`; `STALE_AFTER` in `lift_site/render.py` |
| The stale banner states the data's age and names no cause: from the browser a stalled build and a stalled collector look identical, so the page says the one thing it knows | `notes/publish-cadence.md` § The banner blamed the wrong half |
| Banner, national heading, legend placement, search widget and footer follow the shared design language (aligned 2026-08-26); the horizon left the header stamp for the freshness chip's hover title and the static pages' sub line | `notes/site.md` § The design alignment pass |
| Every drill-down links to its static page from its own line under the heading; the wording follows the content relationship, which gives two categories: esb and uisce both say "every month ... on one page" because their pages carry months their views do not, while this site's page is the same content as its view and so names the address instead | `notes/site.md` § The permalink affordance moved out of the footer |
| irishrail.ie `stationCode` is the same code space as `locationCodes`, so there is no name-to-code join to build | `notes/station-access.md` § The sources |
| "and" in `platformAccess` is a sequence, not a choice; a lift out removes step-free access unless one of two reviewed exceptions applies | `notes/station-access.md` § "and" is a sequence |
| Escalators are not step-free, so an escalator outage removes a convenience, not access, and since 2026-09-03 the grade agrees. The one escalator that should knock is one that is the only powered way up; no station is of that shape, and a real-corpus test fails the day one appears | `notes/station-access.md` § Escalators; `notes/site.md` § The grade is lift availability |
| An escalator verdict says who did lose a way up and quotes what the page puts on the same leg; it never says a lift was working, and the site withholds the quoted lift when its own rows show a lift notice overlapping | `notes/station-access.md` § The entrance leg, and who an escalator served |
| A notice's own text says which leg it is about, and a platform wins over an entrance word; a lift notice naming the way in is read against `ticketOfficeAccess`, lost where that field puts a lift there and unknown otherwise | `notes/station-access.md` § The entrance leg, and who an escalator served |
| A lost verdict names the platforms that never needed the lift, quoting the prose - withheld wherever the notice and the page disagree, and worded apart from the reviewed same-platform alternatives | `notes/station-access.md` § The other platform is often still step-free |
| OpenStreetMap was carried as a second opinion and removed: it changed no verdict, its one signal was redundant, and it has no `level` tags outside the Dublin termini | `notes/station-access.md` § OpenStreetMap |
| GTFS, GTFS-R, the NTA developer API, NaPTAN, PTIMS and OSM all carry no station accessibility data, and the GTFS fields Google and Apple read for accessible routing are absent too. Scraping the prose is the last resort, not the lazy option | `notes/station-access.md` § Why scraping prose is the only option |
| NeTEx and SIRI-FM are the formats that would carry this. Ireland publishes neither, and 2017/1926 only obliges publishing data that already exists. NeTEx appearing is the one thing worth watching for | `notes/station-access.md` § The regulation |
| The design layer is shared with uisce and esb via `../statusui`, a uv git dependency pinned in `uv.lock` - edit upstream, then `../statusui/rollout.sh` bumps all three sites. Vendored copies were tried first and drifted within a day. `lift_site/site.css` is this site's own | `notes/site.md` § The vendored copy became a pinned dependency; statusui's README |

Decisions go in `notes/`, dated, with the rejected alternatives and their
numbers. Add a row here when one closes something off - this file carries
pointers only, never the rationale, or it becomes the thing it exists to fix.

## Comments

Comments earn their place or they go. Say **why**, not what - never a paraphrase
of the line below, a heading for an obviously-named block, or an explanation of a
standard flag. What does earn a comment: a reason the obvious approach was
rejected, a dependency nothing else records, a constraint from outside the code.

One line where one will do. If the reasoning needs a paragraph it belongs in the
commit message, the PR, or `notes/` - not above the line.

## Punctuation

**No em dashes.** Not in the site's prose, the code comments, `notes/`, commit
messages, PR bodies, issue bodies or the replies in a session. The house dash
is a spaced hyphen - like this one - and it is what every file here already
uses. Write it out where a sentence reads better for it: "which is", "because",
a colon, or two sentences.

This was an unwritten rule until 2026-08-29, which is exactly why it kept being
broken: the repo was clean and every violation arrived in a PR body or a chat
reply, where nothing checked it. `scripts/no-em-dash.sh` checks the tracked
files; the prose outside the repo is on whoever is writing it.

## Before changing anything the site publishes

`tests/test_site_real.py` runs the pipeline against the real corpus: every
lift/escalator notice appears on the site exactly once, the shards add up to
the headline, the horizon is the last successful run. If it fails, something
moved in the model or in the feed - find out which before adjusting the model
to make it pass.

The 500 KB initial-load budget is printed by every build and asserted by the
render tests. It holds because individual outages live in per-station shards
(`h/<CODE>.js`) and quiet station-months fall back to a single `blank` bar;
keep both.
