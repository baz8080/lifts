# Figures registry

Every number quoted in a chapter gets a row here. *Source* is a pull request number, a commit
subject, a `notes/` section heading, an issue number, a README section, or **measured**, which
means a read-only check run by the writing session against the real corpus.

Unlike the two sibling series, this one had the data to hand, so the current figures are
measured rather than lifted. Historical figures are quoted as measured on their stated date and
say so where the number has since moved.

## Measured 24 September 2026 (Session 3)

Everything in this section was re-run on 24 September after merging `main` (through PR #58),
with `../lifts-data` pulled to commit `cd7ea6a`. Same commands as the 12 September block below.
Chapters 00, 17, 18, 19a and 19b quote this block; chapters 13 to 16 quote the 12 September one.

### The corpus

| Figure | Value | How |
|---|---|---|
| Runs recorded | 2,224 | `stats` |
| Run outcomes | 2,217 ok, 7 unreachable | `stats` |
| Coverage | 2026-08-08T21:30:55Z to 2026-09-24T05:02:51Z, 46 days | `stats` |
| Messages tracked | 737 (13 open, 724 closed, 10 reopened at least once) | `stats` |
| Unidentifiable items | 952 | `stats` |
| Raw log size | 10.5 MiB; database 1.4 MiB | `stats` |
| Outages after merging | 69, across 44 stations; 5 escalator, 9 planned | `lift_site.model.load_outages` |
| Listed at the horizon | 4 lift and 1 escalator notice across 5 stations (HWTHJ, BROCK, BTSTN, TMORE lift; PERSE escalator) | site build |
| Notices on record for the access report | 58 | `report` |
| Verdicts | 31 lost, 23 unknown, 4 escalator | `report`, counting `->` lines |
| Unknown by reason | 13 page does not mention a lift; 10 notice names a platform the page puts no lift at | same |
| Unknown share over time | 6 of 24 (31 Aug), 7 of 30 (4 Sep), 14 of 45 (12 Sep), 23 of 58 (24 Sep) | the four measured blocks |
| Tests | 526, OK, 11 skipped with `LIFT_STATUS_DATA_DIR` set; 34 skipped without | `unittest discover` |
| Commits on `main` | 215, of which 142 carry `Co-Authored-By` | `git log origin/main` |
| Trailer identifiers | seven: Opus 5 (78), Fable 5 (27), Fable 5.1 (18), Opus 5 (1M context) (9), Sonnet 5 (4), Opus 5.5 (3), bare "Claude" (3) | same |
| Merged pull requests | 48 | `gh pr list --state merged` |
| Open issues | none | `gh issue list` |

### The site

| Figure | Value | How |
|---|---|---|
| `index.html` | 61.5 KB | site build |
| `data.js` | 7.9 KB | site build |
| Initial load | 69.4 KB against a 500 KB budget | site build |
| `outages.csv` | 28.7 KB, on demand | site build |
| `feed.xml` | 43.0 KB, on demand | site build |
| Station pages | 1,243.7 KB over 44 files | site build |
| Shards | 32.3 KB over 44 files, largest `PERSE.js` at 2.5 KB | site build |
| August national row | 21 stations, 28 outages, 22 faults, 6 planned, **75%**, 2 still out at month end | `national_month` |
| August grade mix | A 2, B 1, C 4, D 7, E 5, F 2 | `station_month` per station |
| September national row, so far | 30 stations, 43 outages, 39 faults, 4 planned, 85%, 5 ongoing | `national_month` |
| September grade mix, so far | A 2, B 7, C 10, D 6, E 5 | `station_month` per station |

### Chapter 17

| Figure | Value | How |
|---|---|---|
| `PLANNED_MARKERS` | "planned works", "planned maintenance", "engineering works" | PR #56, `lift_site/model.py` |
| Salthill and Monkstown, notice 1 | platform 1, planned maintenance, 2026-09-11T13:32:31Z to 2026-09-15T14:32:55Z; Irish Rail's start 2025-11-03 | database, messages 2049 |
| Salthill and Monkstown, notice 2 | platforms 1 and 2, planned maintenance, from 2026-09-16T14:01:41Z; reissued 2026-09-17T09:01:12Z as a fault with head "Station - Lift out of order", closed 2026-09-17T23:02:21Z | database, messages 2184 and 2189 |
| Salthill and Monkstown, September | old marker E 66% (8 of 24 days against); new marker C 91% (2 of 24) | `station_month` with the tuple swapped |
| National September, old marker vs new | 85% both; planned 3 vs 4; C 9 vs 10, E 6 vs 5 | same |
| Kishoge's `stationCode` | the literal name "Kishoge" | PR #55; `snapshot.load` with the fixup table emptied |
| Feed location codes joining a station record | 76 of 76 with the table; 75 without, the miss being KISHO | `messages.location_codes` against `snapshot.load` |
| Notices at KISHO | 1, "Delays of up to +15mins" | database |
| Snapshot codes not matching `[A-Z0-9]+` | none with the table; "Kishoge" without | same |
| August, 12 Sep corpus vs today, same code | 76% and A 3, then 75% and A 2; only Tullamore differs | raw logs cut at 2026-09-12 morning, rebuilt in a scratch dir |
| Tullamore, August | A 100% then D 83% (4 of 24 watched days against) | `station_month` |
| Tullamore's notice, stretch 1 | 2026-08-28T15:01:32Z to 2026-09-01T09:02:41Z, 3 d 18 h 01 m, planned | `load_outages` |
| Tullamore's notice, stretch 2 | from 2026-09-16T14:01:41Z, still listed; pooled planned total 11 d 09 h at the horizon | same |
| Irish Rail's start on Tullamore's notice | 31 Aug 2026 00:00 Dublin | station page |
| When the pooled total crossed a week | about 2026-09-19T20:00Z, by arithmetic | 7 d minus 3 d 18 h 01 m 09 s after stretch 2 opened |
| Tullamore, September so far | E 58% | station page |

### Chapter 18

| Figure | Value | How |
|---|---|---|
| Findings in the collector review | 10: 8 fixed, 1 not a real path, 1 left | `notes/collector-review.md` |
| Collector files unchanged since 18 Aug | `parse.py`, `client.py`, `__main__.py`; `poll.py` by 16 lines | same |
| Diff-by-diff review of the rest | since 2026-08-26 | same |
| Database failure exit code | 7 | same; `lift_status/alert.py` |
| Alert marker clears after | 4 consecutive clean runs, two hours | same |
| `TimeoutStartSec` | 60, now 300; client worst case 3 attempts of 15 s connect and 15 s read, plus backoff and DNS | same |
| Backup unit cap | 15 minutes | PR #58 |
| Raw lines already in time order | all 2,224, so no rebuild moved | `notes/collector-review.md`; PR #58 verification |
| `fake-hwclock` skew after a power cut | up to an hour | `notes/collector-review.md` |
| First review of the access branch | 9 findings | ch 12 § The golden file |

## Measured 12 September 2026 (Session 2), quoted by chapters 13 to 16

Session 0 measured on 31 August and Session 1 on 4 September. Everything in this section was
re-run on 12 September after merging `main`. Where a chapter quotes an earlier figure it says so,
and the row is in one of the dated blocks below.

Run from `/Users/barry/Code/lifts` with `../lifts-data` pulled to its 12 September state, then:

```bash
python -m lift_status --data-dir ../lifts-data rebuild
python -m lift_status --data-dir ../lifts-data stats
python -m lift_site --data-dir ../lifts-data
python -m lift_access --data-dir ../lifts-data report
```

### The corpus

| Figure | Value | How |
|---|---|---|
| Runs recorded | 1,648 | `stats` |
| Run outcomes | 1,645 ok, 3 unreachable | `stats` |
| Coverage | 2026-08-08T21:30:55Z to 2026-09-12T05:01:41Z | `stats` |
| Collection horizon at build | 2026-09-12 05:01Z, 2.8 h behind the build | site build |
| Messages tracked | 497 (29 open, 468 closed, 7 reopened at least once) | `stats` |
| Unidentifiable items | 587 | `stats` |
| Raw log size | 6.2 MiB | `stats` |
| Outages after merging | 53, across 37 stations | site build |
| Notices on record for the access report | 45 | `report` |
| Listed at the horizon | 3 lift notices across 3 stations, 0 escalator | site build |
| `LIFT_STATUS_GRACE_MISSES` default | 2 | `lift_status/store.py:24` |

### The site

| Figure | Value | How |
|---|---|---|
| `index.html` | 61.2 KB | site build |
| `data.js` | 7.1 KB | site build |
| Initial load | 68.3 KB against a 500 KB budget | site build |
| `outages.csv` | 22.4 KB, on demand | site build |
| `feed.xml` | 43.3 KB, on demand | site build |
| Station pages | 1,038.4 KB over 37 files | site build |
| Shards | 25.4 KB over 37 files, largest `PERSE.js` at 1.8 KB | site build |
| `STALE_AFTER` | 10 hours | `lift_site/render.py` |
| Lift availability, August 2026 | 76% | `data.js` `national["2026-08"]` |
| August national row | 21 stations, 28 outages, 22 faults, 6 planned, 76%, 2 still out at month end | same |
| Lift availability, September so far | 79% | `data.js` `national["2026-09"]` |
| September national row | 22 stations, 27 outages, 26 faults, 1 planned, 79%, 3 ongoing | same |
| Grade mix, August, 21 station-months | A 3, B 1, C 4, D 6, E 5, F 2 | `data.js` `stats` against `bands` |
| Grade mix, September so far, 22 station-months | A 2, C 7, D 10, E 1, F 2 | same |
| Band table | A 100, B 95, C 90, D 75, E 50, F 0 | `data.js` `bands` |

### Listings and start dates

| Figure | Value | How |
|---|---|---|
| Longest lead: Rush and Lusk | 451.6 days, from a start of 2025-05-14 08:00Z against a first sighting at the very first poll, 2026-08-08T21:30:55Z | `lift_site.model.load_outages` |
| Outages whose start predates their first sighting, 31 Aug | 23 of 24, 12 by seven days or more | same, measured 31 Aug 2026 |
| Next four leads | Docklands 253.4, Dublin Pearse lift 242.9, Hazelhatch 237.6, Thurles 197.4 | same |
| Further leads quoted | Pearse escalator 146.1, Ballinasloe 123.9, Skerries 118.5, Ballybrophy 100.5 | same |
| The one negative lead | Tullamore, minus 2.3 days (works announced in advance) | same |
| Listing durations, hours | 6.5 to 541.5; median 62.25 | same |
| Shortest listing | Portarlington, 6.5 h | same |
| Longest listings | Athy and Midleton, 541.5 h and still listed | same |
| Hazelhatch listing | 48.5 h | same |
| Outages carrying a folded reissue | 0 | same |

### Station facts

| Figure | Value | How |
|---|---|---|
| Stations in the snapshot | 152 | `stations/irishrail-20260830.jsonl` |
| Stations recorded as having a lift | 57 | `report`, `model.has_lift` |
| Stations recorded as having none | 95 | same |
| Station snapshots on record | `irishrail-20260830.jsonl`, `irishrail-20260901.jsonl` | `lifts-data/stations/` |
| Prose mentioning "lift" before boilerplate stripping | 61 | `model.LIFT` over `platform_access` |
| ... after stripping | 58 | `model.strip_boilerplate` then `model.LIFT` |
| Difference explained | 3 boilerplate-only (Greystones, Killiney, Donabate), then Dromod's explicit denial | `notes/station-access.md` |
| `platformAccess` naming an escalator | 2 of 152: Tara Street, Dublin Pearse | `model.ESCALATOR` |
| `ticketOfficeAccess` naming an escalator | 1: Dublin Connolly | same |
| Stations with any `ticketOfficeAccess` text | 143 of 152 | snapshot |
| Verdicts across the 45 notices | 28 lost, 14 unknown, 3 escalator | `report` |
| Unknown share over time | 6 of 24 (31 Aug), 7 of 30 (4 Sep), 14 of 45 (12 Sep) | `report`, each date |
| Step-free pill rendered on the live site | never; `stepfree` is empty | `data.js` |
| Surveyed stations (`survey-pilot` branch of `lifts-data`) | 5: ATHY, CNLLY, CNOCK, HZLCH, PERSE | `git ls-tree origin/survey-pilot survey/` |
| `survey/` on `lifts-data` `main` | absent | same |

### The repository

| Figure | Value | How |
|---|---|---|
| Commits on `main` | 204 | `git log --oneline \| wc -l` |
| Commits with a `Co-Authored-By` trailer | 135, across six Claude model identifiers (77 Opus 5, 27 Fable 5, 18 Fable 5.1, 9 Opus 5 1M, 1 Sonnet 5, 3 unversioned) | `git log --format='%b' \| grep -o 'Co-Authored-By: [^<]*' \| sort \| uniq -c` |
| Merged pull requests | 42, numbered to #54 | GitHub, `baz8080/lifts` |
| Open issues | #52, #53 | GitHub |
| Test count | 516, passing with `LIFT_STATUS_DATA_DIR` set (11 skipped) and with it unset (34 skipped) | `python -m unittest discover -s tests -t .` |
| `notes/` files | site · station-access · accessible-routes · publish-cadence · step-free-graph · delays-site | `ls notes/` |
| First commit | 2026-08-08 | `git log --reverse` |
| Em dashes in `writing/` | 0 | `scripts/no-em-dash.sh` |

## Measured 4 September 2026 (Session 1), quoted by chapters 10 to 12

| Figure | Value |
|---|---|
| Runs / outcomes | 1,264; 1,261 ok, 3 unreachable |
| Coverage | to 2026-09-04T05:01:41Z |
| Messages tracked | 281 (4 open, 277 closed, 4 reopened at least once) |
| Listings | 285 across 281 messages; 4 messages with more than one stretch |
| Unidentifiable items | 323 |
| Outages after merging | 34 across 27 stations; 8 planned, 3 escalator |
| Lift availability | August 76%, September so far 62% |
| Grade mix, August | A 3, B 1, C 4, D 6, E 5, F 2 |
| Grade mix, September so far, 8 station-months | A 2, D 3, E 1, F 2 |
| August availabilities, sorted | 0, 0, 54, 54, 70, 70, 70, 83, 83, 87, 87, 87, 87, 91, 91, 91, 91, 95, 100, 100, 100 |
| Verdicts across 30 notices | 20 lost, 7 unknown, 3 escalator |
| Lost verdicts carrying a kept-platform note | 5: Pearse, Dún Laoghaire, Malahide, Portarlington, Tullamore |
| Initial load | 64.6 KB |
| Commits / trailers / tests | 182 / 121 / 390 |

## Measured 31 August 2026 (Session 0), quoted by chapters 00 to 09

Kept because chapters 02, 05, 07 and 09 quote the corpus as it stood before the September
changes, and say so where they do.

| Figure | Value |
|---|---|
| Runs / outcomes | 1,084; 1,081 ok, 3 unreachable |
| Coverage | 2026-08-08T21:30:55Z to 2026-08-31T11:01:41Z |
| Messages tracked | 234, of which 24 classify as lift or escalator (22 lift, 2 escalator) |
| Unidentifiable items | 264 |
| Outages after merging | 24 across 21 stations; 6 planned, 2 escalator |
| Aggregate availability, August | 67%, with escalators counting |
| Grade mix, 21 station-months | A 1, B 1, C 5, D 5, E 4, F 5 |
| Availabilities, sorted | 0, 0, 20, 25, 29, 54, 66, 70, 70, 83, 87, 87, 87, 87, 91, 91, 91, 91, 91, 95, 100 |
| Dublin Pearse | F, 20%: 6 lift cells inside grace, 19 escalator cells overrun, 24 days watched |
| Dublin Connolly | C, 91%: 0 lift cells, 2 red escalator cells |
| Tullamore | A, 100%, over four planned-works cells |
| Verdicts across 24 notices | 16 lost, 6 unknown, 2 escalator |
| Listing durations | 6.5 h (Portarlington) to 541.5 h (Athy, Midleton); median 62.25 |
| Initial load | 64.3 KB |
| Commits / trailers / tests | 139 / 88 / 287 |

Several of these are not merely stale, they were **wrong**, and chapter 10 is why: Portlaoise's
29%, Thurles' 25% and Clondalkin's grade all included a fortnight the notice was not on the
feed. The August aggregate and the grade mix moved again in chapter 11 when escalators stopped
counting.

## Quoted at the date they were measured (not re-run)

### Ch 01

| Figure | Value | Source |
|---|---|---|
| Lift/escalator notices in the first corpus | 17 of 113 | `notes/site.md` preamble, 18 Aug 2026 |
| `sort_keys=True` is load-bearing | present in `store.write_raw` | `CLAUDE.md` § The invariant |

### Ch 02

| Figure | Value | Source |
|---|---|---|
| Starts predating first sighting, at PR #2 | 14 of 17, and 12 by a week or more | `notes/site.md` § The measured interval, 18 Aug 2026 |
| Batch arrivals | 6 at the first poll; 3 new at 10 Aug 14:30; 4 at 13 Aug 10:30; 2 at 17 Aug 14:02; 3 removed together 14 Aug 14:01 | same |
| `end` as a placeholder | 13 of 17 near the year end | `notes/site.md` § `end` is shown, 18 Aug 2026 |
| Docklands gap | closed 14 Aug 14:01, new notice 17 Aug 14:02 | `notes/site.md` § Notices reissued |
| The non-lift reissue chain | `Station currently closed` to `CLOSED` to `Station is OPEN`, ids 42, 45, 46 | same |
| Initial payload at PR #2 | 30 KB against 500 KB | PR #2 |
| Stations listed in August at PR #2 | 15 | PR #2 |
| The power site's `startTime` | 8 revisions in 1,460 records; median lag about one poll | esb `notes/grading.md`, 18 Aug 2026 |

### Ch 03

| Figure | Value | Source |
|---|---|---|
| Drift while vendored | this site and esb on one statusui commit, uisce five UI commits behind | `notes/site.md` § The vendored copy became a pinned dependency, 20 Aug 2026 |
| `STALE_AFTER` | 16 hours; widest legitimate gap about 14 h, missed push 17 h+ | `lift_site/render.py`, PR #12 |
| Python floor | `requires-python` 3.11, development interpreter 3.14, both run in CI | PR #13, `CLAUDE.md` |

### Ch 04

| Figure | Value | Source |
|---|---|---|
| PRM TSI | Regulation (EU) 1300/2014: design rules and a written-policy duty, no percentage | PR #18, 28 Aug 2026 |
| Irish Rail Passengers' Charter | "every effort ... available as advertised" | same |
| Big Lift | 52 stations, 2020 to 2024, no availability figure published | same |
| ORR / Network Rail | 8,696 lift faults in a year, 6.6 per lift, over 20 hours average repair | same |
| TfL | 93.7% lift availability, 98.8% excluding planned works | same |
| One listed day over 31 | 96.8% available | arithmetic, 30/31 floored |
| Bands at PR #18 | A 100, B 95, C 90, D 75, F below | PR #18 |
| Grace outcomes | Pearse 5 days and Greystones 2 forgiven; Limerick Junction 10 and Midleton 19 not | `notes/site.md` § Planned works are excused for a week, 28 Aug 2026 |
| The grace worked example | 6 days works then 4 of fault: version 3 gives 60% | `notes/site.md`, same section |
| The skew crash | Midleton at 13 h skew: observed 20 against 21, availability minus 5, `StopIteration` | PR #18 review notes |

### Ch 05

| Figure | Value | Source |
|---|---|---|
| Availability before and after counting escalators | 70% to 66% | `notes/site.md` § An escalator out is a day the station was short of a way up, 29 Aug 2026 |
| Connolly and Pearse, same change | A to C, and A to F at 22% | same, and PR #25 |
| The old F band's nine values | 0, 0, 18, 22, 22, 50, 68, 68, 72 | PR #27, 29 Aug 2026 |
| Cuts at 60 and 40 | split the same nine values identically | same |
| Grade mix before and after E | A 1 B 1 C 5 D 5 F 9, becoming A 1 B 1 C 5 D 5 E 4 F 5 | same |
| E over a 31-day month | 8 to 15 days listed; F 16 or more | arithmetic, floor division |
| Chip contrast work | B measured Lc 38.6 on dark ink against 69.2 on white; the no-grade dash failed at 4.24:1 light and 3.90:1 dark | PR #27, via statusui#11 |

### Ch 06

| Figure | Value | Source |
|---|---|---|
| GTFS archives | `GTFS_Irish_Rail.zip`, `GTFS_All.zip`, `GTFS_Realtime.zip`, ten files each | `notes/accessible-routes.md`, checked 30 Aug 2026 |
| `pathways.txt`, `levels.txt` | absent from all three | same |
| `wheelchair_boarding` | column absent; header ends at `parent_station` | same |
| `location_type` | empty for all 152 rail stops | same |
| NaPTAN | 152 rail stops, `AccessArea` null on every one, "accessib" absent from 22 MB | same |
| `getAllStationsXML` | up, unkeyed, 171 stations, no accessibility data | same |
| NTA catalogue searched | 24 GTFS archives, NaPTAN, PTIMS, nothing else | `notes/station-access.md`, 30 Aug 2026 |
| The regulation | Commission Delegated Regulation (EU) 2017/1926, Annex, "provided they exist in digital machine-readable format" | same |
| The three GTFS fields mapping apps read | `wheelchair_boarding`, `wheelchair_accessible`, `pathways.txt`, all absent | same |
| Code-space join | all 15 codes with lift notices matched, 15/15 | PR #30 |
| `alert` staleness | 131 stations carry one, never cleared, `alertEnd` back to 2014 | `notes/station-access.md` |
| Snapshot size | 7.8 MB plain, about 2 MB in git | same |

### Ch 07

| Figure | Value | Source |
|---|---|---|
| The 61-station reading | 29 "and" as a sequence, 11 "or stairs", 2 real alternatives | `notes/station-access.md` § "and" is a sequence, 30 Aug 2026 |
| The two exceptions | Raheny "Lift or ramp to platform 1"; Cork "Ramp or lift to platform 5A, 5B and 6" | same |
| Boilerplate-only lift mentions | Greystones, Killiney, Donabate | same |
| Dromod | the one explicit "(no lift at this station)" | same |
| Verdicts at PR #30 | 18 of 24 resolve, 2 escalator, 6 unknown | PR #30, 30 Aug 2026 |

### Ch 08

| Figure | Value | Source |
|---|---|---|
| The rebuild transcript | 228 messages and 1,012 runs before; 0 and 0 after; exit code 0 | PR #34, 30 Aug 2026 |
| The alert marker transcript | `delivered: False`, marker written, second attempt suppressed | same |
| `ALERT_REPEAT_SECONDS` | 24 hours | same |
| Partial fetch | 38 empty bodies in an 8 MB diff would go unnoticed | `notes/station-access.md` § Three things a review caught |
| OSM, verdicts changed | 0 of 24, with a synthetic digest mapping a lift at all 152 stations | `notes/station-access.md` § OpenStreetMap, 30 Aug 2026 |
| OSM, level tags | 2 of 12 sampled stations, both Dublin termini | same |
| OSM, stations it spots | 13 where the prose mentions no lift and OSM maps one | same |
| OSM, what it cost | about 60 lines, a monthly rate-limited HTTP budget, and a derived rather than verbatim artefact from roughly 450 MB of extracts | same |

### Ch 09

| Figure | Value | Source |
|---|---|---|
| Pearse and Connolly, graded against lifts only | Pearse F 21% against A 100%; Connolly C 91% against A 100%; national 67% against 70% | issue #32, 30 Aug 2026 |
| Pearse's August notices | lift at platform 2 for 5 days (inside grace), escalator at platform 2 for 16 days (overran) | same |
| Platforms reached without a lift | 32 of 57 stations that claim a lift; 12 of the 21 that have had a notice | issue #31 and `notes/station-access.md`, 30 Aug 2026. Recorded, not re-derived: a quick re-derivation with a narrower rule gives 27 and 10, so the figure is sensitive to how "named without a lift" is defined and the recorded derivation is the one to trust |
| Direction named in the prose | 10 of 57 stations | issue #31 |
| Platforms that would need hand labelling | roughly 120 | same |
| `ticketOfficeAccess` present | 143 of 152 stations | issue #33 |
| Stations naming an escalator | Pearse and Tara Street in `platformAccess`, Connolly in `ticketOfficeAccess`; all three also have lifts | same |

### Ch 10

| Figure | Value | Source |
|---|---|---|
| Cron actual start times, week to 1 Sep | `40 5` at 10:24, 10:39, 11:46, 11:48, 13:38, 16:46, 17:41; `40 12` at 16:51, 16:53, 16:56, 19:13, 22:33, 22:36 | PR #39, `notes/publish-cadence.md`, 2 Sep 2026 |
| Normal jitter before 26 Aug | runs started 05:58 to 06:06Z against a `40 5` cron | same |
| The reported string | a 10:24Z build saw data to 23:22Z; a 16:53Z build saw data to 11:19Z; 21.5 h old by 09:47 | same |
| Push cadence and worst-case age | six-hourly, capping age at about 7 h against about 13 h before | same |
| `STALE_AFTER` | 16 h to 10 h | same |
| Live lag measured while implementing | 10.2 h at 09:12Z | same |
| Portlaoise as published | 16 days listed, F, 29% available | PR #42, 3 Sep 2026 |
| What actually happened at Portlaoise | 20 h from 10 Aug, absent from 672 consecutive successful polls, 22 h from 25 Aug | same |
| Grade moves from the split | Portlaoise F 29% to D 83%; Thurles F 25% to E 54%; Clondalkin F to E 70%; Pearse and Midleton unmoved | same |
| Reopens the counter had recorded | 6 in the first month, 5 of them lift or escalator notices | `notes/site.md`, 2 Sep 2026 |
| Athy's blink | absent from exactly one poll on 21 Aug, back 29 minutes later | same |
| Gap sizes in the corpus | 1, 9, 79, 388 and 672 polls | same |
| Midleton's real block | 1,087 consecutive successful polls, no gaps | PR #42 |
| The pooled planned total | without it, a 4-hour blip took the Pearse escalator from 20% to 41% | same |
| The double-counted chain total | 5.5 days of works reported as 9 | same |

### Ch 11

| Figure | Value | Source |
|---|---|---|
| The reverted label column | 64px, appeared on the one station with two bars, put its day 14 over every other row's day 15 | PR #38, 1 Sep 2026 |
| The gutter | 15px on every row, 84px with the word on station pages | same |
| Alignment measured | all 21 August rows start their days at the same x at 980px and 500px | same |
| Glyph cost | about 730 bytes on a 68 KB initial load | same |
| Review findings on that branch | 6, including three tests that passed with the feature removed | same |
| Grade moves from taking escalators off | Connolly C 91% to A 100%; Pearse F 20% to A 100%; August national 72% to 76%; Tara Street F 33% to A 100%; September national 50% to 61% | PR #43, 3 Sep 2026, corpus to 05:00Z |
| The narrower denominator that was rejected | 75% instead of 76% for August, 53% instead of 61% for September | same |
| Stations claiming a lift among the escalator three | Pearse, Connolly and Tara Street all claim one, so the only-powered-way-up rule has no instance | same |

### Ch 12

| Figure | Value | Source |
|---|---|---|
| Lost verdicts gaining a kept-platform note | 5: Pearse, Dún Laoghaire, Malahide, Portarlington, Tullamore | PR #37, 3 Sep 2026 |
| Stations naming a platform reached without a lift | 32 of the 57 that claim a lift | same, and issue #31 |
| Leg detection over 24 distinct notice texts | 19 platform, 1 entrance (Connolly), 4 unlocated, no false entrance hits | PR #45, 3 Sep 2026 |
| `ticketOfficeAccess` across 152 stations | 9 blank, 26 no ticket office, 89 level, 21 ramp; 4 name a lift (Connolly, Clondalkin, Docklands, Grand Canal Dock), 1 names an escalator (Connolly) | same |
| Escalator verdicts that moved | 3: Pearse, Connolly, Tara Street; no lift verdict moved | same |
| Overlaps found by the guard | 0. Pearse's lift listing closed at the exact poll its escalator's opened, 2026-08-13T10:30:46Z | same |
| Review passes and findings | 9, then 6, then 5, then 4; two fixes were themselves regressions | same |
| The regressions caught by hand | Carrigaloe's and Dalkey's "platform No 1" lines dropped; Banteer's and Booterstown's hidden by a split at "No." | same |
| Corpus growth in distinct notice texts | 21 in 26 days | same |
| Reliability by class, corpus to 3 Sep (27 notices) | 18 lost, 6 unknown, 3 escalator; entrance leg has 0 lift notices and 1 escalator notice | `notes/station-access.md` § How reliable this is, honestly, 3 Sep 2026 |
| Stations with no ticket office | 26 of 152, so a sixth of the network is unknown on the entrance leg by construction | same |

### Ch 13

| Figure | Value | Source |
|---|---|---|
| The survey that produced the work | the site read against a corpus of 36 outages over 28 stations | PR #49, 6 Sep 2026 |
| Initial load change | 64.8 KB to 65.8 KB; feeds and CSV off it entirely | same |
| Feed sizes | `feed.xml` carries the 50 most recent outages; `s/<slug>.xml` carries a station's every outage | same |
| `thin_days` threshold | fewer than 40 polls in a Dublin day, a day with none included | same |
| `unclassified_mentions` findings today | none | same |
| Name column widening | 170px to 230px above 780px | PR #50, 7 Sep 2026 |
| Why 780px | below about 740px the fixed columns plus a 31-day bar at its 3px-a-cell floor stop fitting | same |
| Placements compared | four, rendered against the real CSS | same |
| Overflow checked at | 500, 560, 641, 660, 700, 740, 779, 781, 800, 900, 1200, 1600px | same |

### Ch 14

| Figure | Value | Source |
|---|---|---|
| The failing message | `notice RLUSK lift: dropped`, on `main` | PR #51, 8 Sep 2026 |
| The corrected assumption | "the logs are append-only and that can only mean a bad checkout" | `notes/station-access.md`, corrected in place 8 Sep 2026 |
| The reword | Rush and Lusk's body flipped from "platform 2" to "platform 1" overnight, 8 Sep 2026 | PR #51 |
| Failures in five days | 3: a statusui bump (#48), a Midleton reword (#49), this one | same |
| Fixture size | 53 KB to 115 KB, of which about 23 KB is page fragments across 152 stations | same |
| Determinism check | `lifts-data` checked out 20 commits back, predating the reword; suite green | same |
| Guard still fires | breaking `strip_boilerplate` fails on Donabate, Greystones and Killiney | same |

### Ch 15

| Figure | Value | Source |
|---|---|---|
| The reversed decision | `notes/accessible-routes.md` § What is deliberately out, 29 Aug 2026 | quoted in full in the chapter |
| Business case | Iarnród Éireann to the NTA, PBC-3.5, 30 October 2024, 188 pages | `notes/step-free-graph.md`, 4 Sep 2026 |
| Table 6-2 | 51 stations not yet meeting the standard, in packages of 15, 15 and 21 | same |
| Prior audits named | 2014 feasibility report over 54 stations, 2019 review, 2021 preliminary design reports for the first fifteen | same |
| Metro Nation map | 12 stations glyphed "no step-free access"; disagrees with Irish Rail's page at Athy, Carlow and Ashtown | same |
| Confidence levels | `low` read off a page, `medium` told or a reviewed sentence, `high` seen | same |
| Pilot stations | Hazelhatch, Pearse, Connolly, Athy, Castleknock, all seeded page-sourced at low confidence | same |
| Where the graph says less than the prose | Hazelhatch (no platform named) and the Pearse escalator (page's only escalator is on the way in) come back unknown | same |
| Raheny under the confidence gate | ramp medium, way in low, so the graph says lost where the prose says alternative | same |
| The correction issue | live since 30 Aug 2026, has never fired | same |
| Tests at that merge | 490 | PR #46 |

### Ch 16

| Figure | Value | Source |
|---|---|---|
| Location codes emptied part-way | lift and escalator 55 notices, 0 lose codes; everything else 497 notices, 21 never carry them, 288 lose them partway | PR #54, 11 Sep 2026 |
| The planned-maintenance notice | Salthill and Monkstown, first seen 2026-09-11T13:32:31Z, still listed | issue #53 |
| Disagreement count | 1 in 416 distinct notices, between the delays site's cause reader and `is_planned` | same |
| The cause reader's planned wordings | "planned works" (7 notices), "engineering works" (3), "planned maintenance" (1) | same |
| Kishoge | station facts keyed `"Kishoge"` rather than `"KISHO"`; no lift notice there yet | issue #52 |

## Open `[verify:]` items

None. Every number quoted in the chapters resolves to a row above.
