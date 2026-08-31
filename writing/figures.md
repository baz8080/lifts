# Figures registry

Every number quoted in a chapter gets a row here. *Source* is a pull request number, a commit
subject, a `notes/` section heading, an issue number, a README section, or **measured**, which
means a read-only check run by the writing session against the real corpus.

Unlike the two sibling series, this one had the data to hand, so the current figures are
measured rather than lifted. Historical figures are quoted as measured on their stated date and
say so where the number has since moved.

## Measured 31 August 2026 (Session 0)

Run from `/Users/barry/Code/lifts` with `../lifts-data` pulled to `999922e` ("Message data
through 2026-08-31T11:16:31Z"), then:

```bash
python -m lift_status --data-dir ../lifts-data rebuild
python -m lift_status --data-dir ../lifts-data stats
python -m lift_site --data-dir ../lifts-data
python -m lift_access --data-dir ../lifts-data report
```

### The corpus

| Figure | Value | How |
|---|---|---|
| Runs recorded | 1,084 | `stats` |
| Run outcomes | 1,081 ok, 3 unreachable | `stats` |
| Coverage | 2026-08-08T21:30:55Z to 2026-08-31T11:01:41Z | `stats` |
| Collection horizon at build | 2026-08-31 11:01Z, 3.0 h behind the build | site build |
| Messages tracked | 234 (7 open, 227 closed, 6 reopened at least once) | `stats` |
| Messages classifying as lift or escalator | 24 of 234 (22 lift, 2 escalator) | `lift_site.model.classify` over `messages` |
| Unidentifiable items | 264 | `stats` |
| Raw log size | 2.9 MiB | `stats` |
| Outages after merging | 24, across 21 stations | site build |
| Planned works | 6 of 24 | site build |
| Escalator outages | 2 of 24 | site build |
| Listed at the horizon | 4 lift notices at 4 stations, 0 escalator | site build |

### The site

| Figure | Value | How |
|---|---|---|
| `index.html` | 59.8 KB | site build |
| `data.js` | 4.5 KB | site build |
| Initial load | 64.3 KB against a 500 KB budget | site build |
| Station pages | 578.7 KB over 21 files | site build |
| Shards | 10.8 KB over 21 files, largest `PERSE.js` at 0.9 KB | site build |
| Aggregate availability, August 2026 | 67% | `data.js` `national["2026-08"]` |
| National row | 21 stations, 24 outages, 18 faults, 6 planned, 67%, 4 ongoing | same |
| Grade mix, 21 station-months | A 1, B 1, C 5, D 5, E 4, F 5 | `data.js` `stats` against `bands` |
| Availabilities, sorted | 0, 0, 20, 25, 29, 54, 66, 70, 70, 83, 87, 87, 87, 87, 91, 91, 91, 91, 91, 95, 100 | same |
| Dublin Pearse | F, 20%: 6 lift cells inside grace, 19 escalator cells overrun, 24 days watched | same |
| Dublin Connolly | C, 91%: 0 lift cells, 2 red escalator cells | same |
| Tullamore | A, 100%, over four planned-works cells | same |
| Band table | A 100, B 95, C 90, D 75, E 50, F 0 | `data.js` `bands` |

### Listings and start dates

| Figure | Value | How |
|---|---|---|
| Outages whose start predates their first sighting | 23 of 24 | `lift_site.model.load_outages`, `first_seen - start` |
| ... by seven days or more | 12 of 24 | same |
| Longest lead: Rush and Lusk | 451.6 days | same |
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
| Prose mentioning "lift" before boilerplate stripping | 61 | `model.LIFT` over `platform_access` |
| ... after stripping | 58 | `model.strip_boilerplate` then `model.LIFT` |
| Difference explained | 3 boilerplate-only (Greystones, Killiney, Donabate), then Dromod's explicit denial | `notes/station-access.md` |
| `platformAccess` naming an escalator | 2 of 152: Tara Street, Dublin Pearse | `model.ESCALATOR` |
| `ticketOfficeAccess` naming an escalator | 1: Dublin Connolly | same |
| Stations with any `ticketOfficeAccess` text | 143 of 152 | snapshot |
| Verdicts across the 24 notices | 16 lost, 6 unknown, 2 escalator | `report` |
| The six unknown | Carlow, Greystones (x2), Limerick Junction, Portlaoise, Rush and Lusk | `report` |
| Step-free pill rendered on the live site | never; `stepfree` is empty | `data.js` |

### The repository

| Figure | Value | How |
|---|---|---|
| Commits on `main` | 139 | `git log --oneline \| wc -l` |
| Commits with a `Co-Authored-By` trailer | 88 (61 Claude Opus 5, 27 Claude Fable 5) | `git log --format='%b' \| grep -o 'Co-Authored-By: [^<]*' \| sort \| uniq -c` |
| Merged pull requests | 28, numbered to #34 | GitHub, `baz8080/lifts` |
| Open issues | #28, #31, #32, #33 | GitHub |
| Test count | 287, all passing with `LIFT_STATUS_DATA_DIR` set | `python -m unittest discover -s tests -t .` |
| `notes/` files | site · station-access · accessible-routes | `ls notes/` |
| First commit | 2026-08-08 | `git log --reverse` |
| Em dashes in `writing/` | 0 | `scripts/no-em-dash.sh` |

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

## Open `[verify:]` items

None. Every number quoted in the chapters resolves to a row above.
