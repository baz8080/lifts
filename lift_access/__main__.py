"""CLI entry point: python -m lift_access

`refresh` fetches the station facts and writes the snapshot they are derived
from. `report` prints what the current snapshot says, station by station, beside
the prose it came from - which is the only real check on a derivation built out
of somebody's hand-written sentences. Read it before publishing.

The survey commands work the observation log under <data-dir>/survey:
`questionnaire` writes the form for a station, `seed` drafts its first lines
from the page, `validate` checks the log, `graph-report` prints what the graph
says beside what the prose says, `prose` renders a station the way Irish Rail
could publish it, and `gtfs` exports the lot. `notes/step-free-graph.md`.

None of it runs on the Pi, and none of it belongs in the 30-minute poll loop.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from lift_status.store import DB_FILENAME, DEFAULT_DATA_DIR

from . import fetch, golden, model, prose, questionnaire, seed, snapshot, survey
from . import graph as graph_module
from . import gtfs as gtfs_module

SNAPSHOT_DIR = snapshot.SNAPSHOT_DIR
STATIONS_PREFIX = snapshot.STATIONS_PREFIX


def refresh(args):
    directory = Path(args.data_dir) / SNAPSHOT_DIR
    stamp = datetime.now(UTC).strftime("%Y%m%d")

    records, failed = fetch.fetch_stations()
    if fetch.INDEX_FAILED in failed:
        # No station was attempted, so counting this as a failed station reads as
        # "1 of 1 stations could not be fetched", which is nonsense.
        print(
            f"error: could not read the station list from {fetch.INDEX_URL}\n"
            f"  {failed[fetch.INDEX_FAILED]}\n"
            "No stations were fetched and no snapshot was written.",
            file=sys.stderr,
        )
        return 1
    if failed:
        # Refused, not warned. `latest_snapshot` reads the newest file, so a
        # partial one shadows the last good snapshot permanently, and the damage
        # is invisible: those stations lose their verdicts and the denominator
        # quietly shrinks. An 8 MB JSONL diff will not show a reviewer 38 empty
        # bodies either.
        for slug, why in sorted(failed.items())[:10]:
            print(f"  {slug}: {why}", file=sys.stderr)
        print(
            f"error: {len(failed)} of {len(failed) + len(records)} stations could not be "
            "fetched, so no snapshot was written. The last good snapshot is untouched; "
            "rerun when irishrail.ie is healthy.",
            file=sys.stderr,
        )
        return 1
    if not records:
        # The guard above counts failures, and an index that parses but names no
        # station produces none: `station_slugs` keys off `kontentStations`, a CMS
        # internal that is nobody's promise. Renamed, every fetch is skipped, the
        # empty snapshot becomes the newest file, and the site loses every verdict
        # and its denominator without a single error.
        print(
            f"error: the station list at {fetch.INDEX_URL} parsed but named no stations, "
            "so nothing was fetched and no snapshot was written. The payload's shape has "
            "probably changed; check fetch.station_slugs against it.",
            file=sys.stderr,
        )
        return 1
    path = fetch.write_snapshot(directory / f"{STATIONS_PREFIX}-{stamp}.jsonl", records)
    print(f"wrote {path} ({len(records)} stations)")
    return 0


def report(args):
    """Every verdict beside the prose it was read from.

    Prints the entrance prose too where the verdict read it: an escalator notice
    or a lift notice that names the way in. It has no listings, so it never sets
    `lift_listed_too`; that is the site build's knowledge, not the snapshot's.
    """
    facts = snapshot.load(args.data_dir)
    if not facts:
        print(f"no station snapshot under {Path(args.data_dir) / SNAPSHOT_DIR}\n"
              f"run: python -m lift_access --data-dir {args.data_dir} refresh", file=sys.stderr)
        return 1
    stations, path = facts.stations, facts.path
    print(f"{len(stations)} stations from {path}\n")
    if facts.dropped:
        print(
            f"warning: {facts.dropped} record(s) in {path.name} read back as no station. "
            "refresh refuses to write one it cannot read, so the payload shape has moved "
            "under fetch.station_node since this file was written.",
            file=sys.stderr,
        )

    tally = facts.tally()
    print(f"lift: {tally['yes']} yes, {tally['no']} no\n")

    db_path = Path(args.data_dir) / DB_FILENAME
    if db_path.exists():
        print("--- what each notice on record means ---")
        for code, kind, head, text in golden.notices(db_path):
            station = stations.get(code)
            result = model.verdict(station, kind, text)
            print(f"\n  {code:6} {head}")
            print(f"    prose:   {(station.platform_access if station else '(no station)')[:150]}")
            if station and (kind == "escalator" or result.leg == model.ENTRANCE_LEG):
                entry = " / ".join(
                    line for line in station.ticket_office_access.split("\n") if line.strip()
                )
                print(f"    entry:   {entry[:150]}")
                print(f"    leg:     {result.leg or 'not named'}")
            print(f"    notice:  {model.plain(text)[:150]}")
            print(f"    -> {result.state.upper()}: {result.detail}")

    if args.all:
        print("\n--- every station that claims a lift ---")
        for code in sorted(stations):
            station = stations[code]
            if not station.claims_lift:
                continue
            serves = "all" if model.ALL_PLATFORMS in station.lift_platforms else (
                ", ".join(sorted(station.lift_platforms)) or "none named")
            print(f"\n  {code:6} {station.name}  (lift at: {serves})")
            print(f"    {station.platform_access[:200]}")
    return 0


def write_golden(args):
    """Regenerate tests/fixtures/access-golden.json from the checked-out corpus."""
    facts = snapshot.load(args.data_dir)
    db_path = Path(args.data_dir) / DB_FILENAME
    if not facts or not db_path.exists():
        print("golden needs both a station snapshot and a rebuilt database", file=sys.stderr)
        return 1
    notices = golden.notices(db_path)
    _write_document(golden.PATH, golden.build(facts, notices))
    data = survey.load(args.data_dir)
    if data:
        _write_document(
            golden.GRAPH_PATH,
            golden.build_graph(facts, data, notices, survey.digest(args.data_dir)),
        )
    return 0


def _write_document(path, document):
    before = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    path.write_text(golden.dumps(document), encoding="utf-8")
    changes = golden.differences(before, document)
    added = golden.new_notices(before, document)
    print(f"wrote {path}")
    print(f"{len(document['stations'])} stations, {len(document['verdicts'])} notices "
          f"({len(added)} newly pinned), {len(changes)} line(s) changed"
          + (":" if changes or added else ""))
    for line in changes:
        print(f"  {line}")
    for v in added:
        print(f"  new notice {v['code']} {v['kind']}: {v['state']}")


def _notices_by_code(data_dir):
    db_path = Path(data_dir) / DB_FILENAME
    by_code = {}
    if db_path.exists():
        for code, kind, head, text in golden.notices(db_path):
            by_code.setdefault(code, []).append((kind, head, text))
    return by_code


def _need_facts(args):
    facts = snapshot.load(args.data_dir)
    if not facts:
        print(f"no station snapshot under {Path(args.data_dir) / SNAPSHOT_DIR}", file=sys.stderr)
    return facts


def _graphs(args, facts, codes=None):
    """code -> (graph, problems) for every surveyed station, or the ones asked for."""
    data = survey.load(args.data_dir)
    for problem in data.problems:
        print(f"warning: {problem}", file=sys.stderr)
    out = {}
    for code in sorted(data.observations):
        if codes and code not in codes:
            continue
        station = facts.station(code) if facts else None
        out[code] = graph_module.replay(data.observations[code], station)
    return data, out


def write_questionnaire(args):
    facts = _need_facts(args)
    if not facts:
        return 1
    by_code = _notices_by_code(args.data_dir)
    if args.all:
        codes = sorted(facts.stations)
    elif args.codes:
        codes = args.codes
    else:
        codes = sorted(code for code in by_code if code in facts.stations)
    missing = [code for code in codes if code not in facts.stations]
    if missing:
        print(f"not in the snapshot: {', '.join(missing)}", file=sys.stderr)
        return 1
    if len(codes) == 1 and not args.out:
        print(questionnaire.render(facts.station(codes[0]), by_code.get(codes[0], ()),
                                   snapshot_name=facts.path.name), end="")
        return 0
    out_dir = Path(args.out or "out/questionnaire")
    out_dir.mkdir(parents=True, exist_ok=True)
    for code in codes:
        text = questionnaire.render(facts.station(code), by_code.get(code, ()),
                                    snapshot_name=facts.path.name)
        (out_dir / f"{code}.md").write_text(text, encoding="utf-8")
    print(f"wrote {len(codes)} questionnaire(s) to {out_dir}")
    return 0


def write_seed(args):
    facts = _need_facts(args)
    if not facts:
        return 1
    directory = Path(args.data_dir) / survey.SURVEY_DIR
    status = 0
    for code in args.codes:
        station = facts.station(code)
        if station is None:
            print(f"{code}: not in the snapshot", file=sys.stderr)
            status = 1
            continue
        text = seed.dumps(seed.observations(station, facts.path.name))
        if not args.write:
            sys.stdout.write(text)
            continue
        path = directory / f"{code}.jsonl"
        if path.exists():
            # A log is append-only and a second seed would duplicate every line.
            print(f"{path} exists; append corrections to it rather than reseeding",
                  file=sys.stderr)
            status = 1
            continue
        directory.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path} ({text.count(chr(10))} lines)")
    return status


def validate(args):
    facts = snapshot.load(args.data_dir)
    data, graphs = _graphs(args, facts, args.codes)
    if not data:
        print(f"no survey under {Path(args.data_dir) / survey.SURVEY_DIR}", file=sys.stderr)
        return 1
    wrong = len(data.problems)
    for code, (graph, problems) in graphs.items():
        found = graph_module.contradictions(graph, facts.station(code) if facts else None)
        for line in problems + found:
            print(f"{code}: {line}")
        wrong += len(problems) + len(found)
        print(f"{code}: {len(data.observations[code])} observation(s), "
              f"{len(graph.nodes)} nodes, {len(graph.edges)} edges, "
              f"{'complete' if graph.complete else 'incomplete'}")
    print(f"{len(graphs)} station(s), {wrong} problem(s)")
    return 1 if wrong else 0


def graph_report(args):
    """Every notice at a surveyed station: what the graph says beside what the prose says."""
    facts = _need_facts(args)
    if not facts:
        return 1
    data, graphs = _graphs(args, facts, args.codes)
    by_code = _notices_by_code(args.data_dir)
    for code, (graph, problems) in graphs.items():
        station = facts.station(code)
        reached = graph_module.step_free_platforms(graph)
        print(f"\n{code:6} {station.name if station else ''}  "
              f"({len(data.observations[code])} observations"
              f"{', incomplete' if not graph.complete else ''})")
        for label in graph.platforms():
            if label in reached:
                print(f"    platform {label}: {graph_module.describe_route(graph, reached[label])}")
            else:
                print(f"    platform {label}: no step-free route recorded")
        for line in problems + graph_module.contradictions(graph, station):
            print(f"    ! {line}")
        seen = set()
        for kind, head, text in by_code.get(code, ()):
            if (kind, text) in seen:
                continue
            seen.add((kind, text))
            ours = graph_module.verdict(graph, kind, text)
            theirs = model.verdict(station, kind, text)
            print(f"\n    {head}")
            print(f"      notice: {model.plain(text)[:150]}")
            print(f"      graph:  {ours.state.upper()} {ours.detail}")
            print(f"      prose:  {theirs.state.upper()} {theirs.detail}")
    return 0


def write_prose(args):
    facts = _need_facts(args)
    if not facts:
        return 1
    _, graphs = _graphs(args, facts, args.codes)
    for code in args.codes:
        if code not in graphs:
            print(f"{code}: no survey", file=sys.stderr)
            return 1
        print(prose.render(graphs[code][0], facts.station(code)))
    return 0


def write_gtfs(args):
    facts = snapshot.load(args.data_dir)
    _, graphs = _graphs(args, facts)
    if not graphs:
        print(f"no survey under {Path(args.data_dir) / survey.SURVEY_DIR}", file=sys.stderr)
        return 1
    written = gtfs_module.export([g for g, _ in graphs.values()], facts, args.out)
    for path in written:
        print(f"wrote {path}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lift_access", description="Station accessibility facts for the lift site."
    )
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                        help="collector storage root (env: LIFT_STATUS_DATA_DIR)")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_cmd = sub.add_parser("refresh", help="fetch the station facts and write the snapshot")
    fetch_cmd.set_defaults(run=refresh)

    report_cmd = sub.add_parser("report", help="print what the current snapshot says")
    report_cmd.add_argument("--all", action="store_true",
                            help="also print every station that claims a lift")
    report_cmd.set_defaults(run=report)

    golden_cmd = sub.add_parser(
        "golden", help="regenerate tests/fixtures/access-golden.json and print what moved"
    )
    golden_cmd.set_defaults(run=write_golden)

    q_cmd = sub.add_parser("questionnaire", help="write the step-free access form for a station")
    q_cmd.add_argument("codes", nargs="*", help="station codes; none means every station "
                       "with a notice on record")
    q_cmd.add_argument("--all", action="store_true", help="every station in the snapshot")
    q_cmd.add_argument("--out", help="directory to write into (default out/questionnaire; "
                       "one code with no --out prints to stdout)")
    q_cmd.set_defaults(run=write_questionnaire)

    seed_cmd = sub.add_parser("seed", help="draft a station's observation log from its page")
    seed_cmd.add_argument("codes", nargs="+")
    seed_cmd.add_argument("--write", action="store_true",
                          help="write survey/<CODE>.jsonl instead of printing; refuses to "
                               "overwrite")
    seed_cmd.set_defaults(run=write_seed)

    validate_cmd = sub.add_parser("validate", help="check the observation log and its graphs")
    validate_cmd.add_argument("codes", nargs="*")
    validate_cmd.set_defaults(run=validate)

    graph_cmd = sub.add_parser("graph-report",
                               help="what the graph says beside what the prose says")
    graph_cmd.add_argument("codes", nargs="*")
    graph_cmd.set_defaults(run=graph_report)

    prose_cmd = sub.add_parser("prose", help="render a surveyed station the way Irish Rail could")
    prose_cmd.add_argument("codes", nargs="+")
    prose_cmd.set_defaults(run=write_prose)

    gtfs_cmd = sub.add_parser("gtfs", help="export every surveyed station as GTFS pathways")
    gtfs_cmd.add_argument("--out", default="out/gtfs")
    gtfs_cmd.set_defaults(run=write_gtfs)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
