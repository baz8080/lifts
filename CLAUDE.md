# Working in this repository

Two things live here: `lift_status`, a collector that snapshots Irish Rail's
realtime service-message feed every 30 minutes, and `lift_site`, a static site
generator that turns the result into https://baz8080.github.io/lifts. **Both run
on the standard library alone** — `pyproject.toml` declares no runtime
dependencies and exists only for ruff and the dev tooling, because the collector
is installed on a Raspberry Pi by copying files. Keep it that way.

```bash
uv run python -m lift_status --data-dir <dir> poll      # one collection pass
uv run python -m lift_status --data-dir <dir> rebuild   # replay JSONL into lift_status.db
uv run python -m lift_status --data-dir <dir> stats
uv run python -m lift_site --data-dir <dir>             # build out/site/
uv run --group dev ruff check
uv run python -m unittest discover -s tests -t .
```

Plain `python3` works for all of these too; uv only pins the interpreter, to the
3.14 in `.python-version`. The collector itself still has to run on the Pi's
Python, which `scripts/install-native.sh` gates at 3.9 — `requires-python` says
so, and ruff takes its target from it, so the linter will not suggest syntax the
Pi cannot run.

The collected data is a separate repository, `baz8080/lifts-data`, normally
checked out at `../lifts-data`. Set `LIFT_STATUS_DATA_DIR` to it (after a
`rebuild`), or pass `--data-dir`. `tests/test_site_real.py` skips without it,
so run the suite with it set before shipping anything that touches the site.

Lifts are elevators outside Ireland; the site says so once for search engines.

## The UI is shared — change it upstream

`lift_site/ui/` is a **vendored copy** of [`../statusui`](https://github.com/baz8080/statusui)
(`ui/UPSTREAM` names the commit): the tokens, base CSS, row/bar/card components and the JS
helpers that uisce, esb and lifts all use, inlined into every page at build. Edit it there,
then `scripts/sync-ui.sh` here — `tests/test_ui_vendored.py` fails if the copy is edited in
place. This site's own rules are `lift_site/site.css`; the shared/per-site rule is in statusui's
CLAUDE.md. The vendoring keeps `dependencies` empty and a clone building.

## The invariant

**The raw JSONL logs are the source of truth. The database is disposable.**
Nothing is parsed before it is written to the log, and `rebuild` replays the
logs through the same code path a live run uses. If a parse is wrong, fix it and
rebuild; never edit the logs. `json.dumps(..., sort_keys=True)` in
`store.py:write_raw` is load-bearing — it is what lets two machines' logs be
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
- **Every lift notice names one location code**; `eventStops[0].sStop` is the
  full station name. 131 delay notices had empty `locationCodes` and sit in
  `unidentifiable_items` — irrelevant to the site.
- **A run that failed is not a run that saw nothing.** `poll.py` enforces this
  structurally; the site's horizon is `MAX(started_at_utc)` over `outcome='ok'`
  runs only, and days past it are "no data".

## Settled — don't re-litigate without reading the note

| Decision | Where |
|---|---|
| The listing interval is measured; Irish Rail's start is shown, not measured | `notes/site.md` § The measured interval |
| Stations keyed by location code, named from the newest notice | `notes/site.md` § Rows are stations |
| Escalators included and tagged, never excluded | `notes/site.md` § Escalators |
| Same-poll reissues merge; a gap of a poll or more is a new outage | `notes/site.md` § Notices reissued |
| Planned works is what the notice text says | `notes/site.md` § Planned works |
| No grade; overview sorts by listed-now, then days listed | `notes/site.md` § No grade |
| `end` printed as "listed end", plays no part in any measure | `notes/site.md` § `end` is shown |
| Windows end at the collection horizon; zero-minute listings count in its month | `notes/site.md` § Windows end |
| Displayed instants are Dublin wall-clock; build/horizon stamps are UTC | `notes/site.md` § Displayed instants |
| Station page shows every month, newest first; overview lists only stations with a notice that month | this file, and the ESB PR discussion |
| The design layer is shared with uisce and esb via `../statusui`, vendored under `lift_site/ui/` — edit upstream, then `scripts/sync-ui.sh`; never edit the copy. `lift_site/site.css` is this site's own | `notes/site.md` § The design layer is shared; statusui's README |

Decisions go in `notes/`, dated, with the rejected alternatives and their
numbers. Add a row here when one closes something off — this file carries
pointers only, never the rationale, or it becomes the thing it exists to fix.

## Before changing anything the site publishes

`tests/test_site_real.py` runs the pipeline against the real corpus: every
lift/escalator notice appears on the site exactly once, the shards add up to
the headline, the horizon is the last successful run. If it fails, something
moved in the model or in the feed — find out which before adjusting the model
to make it pass.

The 500 KB initial-load budget is printed by every build and asserted by the
render tests. It holds because individual outages live in per-station shards
(`h/<CODE>.js`) and quiet station-months fall back to a single `blank` bar;
keep both.
