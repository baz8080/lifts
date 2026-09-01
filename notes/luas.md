# Adding Luas: what exists, and what it would take - 2026-09-01

Barry asked what adding Luas (www.luas.ie) as a second operator would involve,
whether TFI has an official lift-status API, and noted that
https://www.luas.ie/traffic-info/ is currently empty. This note records what
the sources turned out to be, which parts of this codebase assume a single
operator, and the probe to run before writing any code.

A caveat on method first: the session that did this research ran behind an
egress proxy that blocks luas.ie, m.luas.ie, luasforecasts.rpa.ie,
transportforireland.ie, data.gov.ie and wikipedia.org outright (403 on
CONNECT). Everything below about live endpoints comes from search results,
GitHub mirrors and client libraries - ncremins/luas-api, ShaneHastings'
Simple-LUAS, the luas.py package - not from fetching the endpoints. That is
exactly why the probe at the end exists, and why it runs on the Pi.

## There is no API for this

Ireland's GTFS-Realtime feed (`api.nationaltransport.ie/gtfsr/v2`, key via
developer.nationaltransport.ie) covers Luas since v2, but it serves only two
of the three GTFS-R feed types: TripUpdates and Vehicles. **The Alerts feed,
where a lift outage would live, is absent** - there is no service-alert
channel at all, for any Irish operator. This is the same conclusion the wider
search in `notes/station-access.md` § Why scraping prose is the only option
reached from the static side: the formats that would carry this are not
published here.

One thing changed since that note: the NTA has announced that the current
GTFS-R API will be replaced by a new Travel Information platform. Alerts could
appear there. It joins NeTEx on the short list of things worth re-checking,
and nothing else on that list moved.

## The three places lift status actually appears

All three are prose.

1. **https://www.luas.ie/travel-updates/** is the canonical page. It carries a
   dedicated lifts-and-escalators section, and - unlike anything Irish Rail
   publishes - an **explicit all-clear**: as of mid-2026 the page states that
   all lifts and escalators are in full working order.
   `m.luas.ie/service-disruption-info.html` is a simpler mobile variant of the
   same content. luas.ie is a Typo3 site; whether the section is static HTML
   or script-loaded is unknown until probed.

2. **The RPA forecasting API** at `luasforecasts.rpa.ie` - the feed behind
   every Luas app, listed on data.gov.ie under CC-BY 4.0, no key required.
   Two endpoints matter:
   - `xml/get.ashx?action=forecast&stop=<abv>&encrypt=false` returns per-stop
     XML whose `<message>` element is a line-wide banner ("Green Line services
     operating normally").
   - `mobilecontent/news.ashx` is a news feed that has historically carried
     exactly the target text - "The lift at Dundrum is out of service" appears
     in its indexed output. Its format (fields, dates, ids, whether items
     expire) is documented nowhere searchable.

3. **traffic-info/** - the page Barry found empty - appears to be a
   roadworks/traffic widget, not a lift channel. Dismissed.

## Better than the Irish Rail feed twice, worse once

- **An explicit all-clear exists.** The Irish Rail feed only ever signals by
  absence, which is why the site says "no longer listed" and never "fixed". A
  source that states "everything works" distinguishes a quiet day from a
  broken scrape in a way the current feed cannot.
- **A true denominator exists.** luas.ie's accessibility page enumerates which
  stops have lifts: Kilmacud, Balally, Ranelagh, Charlemont, Dundrum,
  Phibsborough (two lifts), Connolly, and the rest of the elevated and cutting
  stops. Most of the ~67 stops are street-level with ramps and have no lift at
  all. Irish Rail publishes no such roll - the reason the site aggregates over
  "stations listed in the month". A Luas grade could be measured against the
  real population of lifted stops.
- **Worse: no structure at all.** No location codes, no start or end dates, no
  fields - identity would have to be derived from notice prose plus stop-name
  matching against the small lifted-stop roll. Irish Rail's feed is odd but it
  is at least JSON with named fields.

## What this codebase assumes today

A second operator breaks assumptions end to end. The load-bearing spots:

- The raw JSONL record (`lift_status/store.py:write_raw`) and the
  `messages-<date>.jsonl` filename carry **no source field**, and `rebuild`
  replays every line through the Irish Rail parser blind.
- `runs`, `messages` and `unidentifiable_items` have no operator column, and
  `messages.identity_key` is UNIQUE with no operator discriminator
  (`store.py`, `parse.derive_identity_key`).
- `parse.py` is Irish-Rail-shaped throughout: the root must be a JSON list,
  `KNOWN_FIELDS` trips schema drift on any other payload, timestamps are
  offset-less Dublin wall-clock, and the columns are literally `products` and
  `eventStops`.
- `lift_site.model.KIND_PATTERNS` matches Irish Rail's exact wording -
  "Lift(s) out of order|service". Luas writes "The lift at X is out of
  service"; every such notice would classify as `None` and vanish.
- Stations are keyed by **bare location code** through `Outage.code`,
  `data.js`, the `h/<CODE>.js` shards, the slugs and the `lift_access`
  lookups. Both operators use short uppercase abbreviations, so a colliding
  code would silently merge two stations into one row, one shard, one grade.
- One horizon, one staleness banner, one national aggregate; the per-month
  arrays in `data.js` are positional with no room for an operator tag.
- `lift_access` is irishrail.ie-specific end to end (the Nuxt payload walker,
  the `platformAccess` prose model). Luas facts would come from the luas.ie
  accessibility page instead - and the fixed lift roll makes that a much
  smaller job than the Irish Rail scrape was.

## Two integration shapes

- **Shared DB**: add a `source` column to the raw record and all three
  tables, fold the source into the identity key, and default a missing
  `source` to `irishrail` during replay. That default is the entire
  migration, because the raw logs are the source of truth and existing lines
  have no such field.
- **Separate data dir per operator**: `--data-dir` already parameterises
  everything, so a Luas collector writes its own logs and its own
  `lift_status.db`, `lift_site` grows a second loader, and codes get an
  operator prefix at the `Outage` boundary. No SQLite migration, no raw-log
  semantics change. Cost: two horizons that the staleness banner has to
  report per operator instead of once.

The second is the smaller first step and the recommendation here. Either way
the site needs per-operator sections or labels: the national headline cannot
silently pool two networks, and neither can the availability denominator.

## The probe, before any code

Whether the collector reads news.ashx, the forecast message, or scrapes
travel-updates depends on facts nobody has published: which of the three
actually lists lift outages, in what wording, with what structure, and whether
the all-clear is machine-detectable. Two weeks of captures answers all of it.

On the Pi, `~/luas-probe/probe.sh` - one JSON line per fetch, body verbatim
and unparsed, `sort_keys=True` so logs merge with `sort -u`, and a failed
fetch still writes a line, all mirroring the collector's own invariants:

```sh
#!/bin/sh
# Probe Luas lift-status candidate feeds; one JSON line per fetch, body verbatim.
set -u
DIR="$HOME/luas-probe"
mkdir -p "$DIR"
day=$(date -u +%Y%m%d)

fetch() {
    url="$1"; label="$2"
    : > "$DIR/.err"
    status=$(curl -sS -m 30 -o "$DIR/.body" -w '%{http_code}' "$url" 2>"$DIR/.err") || status=""
    python3 - "$label" "$url" "$status" "$DIR/.body" "$DIR/.err" <<'PY' >> "$DIR/probe-$day.jsonl"
import json, sys
from datetime import datetime, timezone
label, url, status, body_file, err_file = sys.argv[1:6]
body = open(body_file, encoding="utf-8", errors="replace").read()
err = open(err_file, encoding="utf-8", errors="replace").read().strip()
print(json.dumps({
    "body": body or None,
    "curl_error": err or None,
    "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "http_status": int(status) if status.isdigit() and status != "000" else None,
    "source": label,
    "url": url,
}, sort_keys=True))
PY
    rm -f "$DIR/.body" "$DIR/.err"
}

fetch 'https://luasforecasts.rpa.ie/mobilecontent/news.ashx' news
fetch 'https://luasforecasts.rpa.ie/xml/get.ashx?action=forecast&stop=ran&encrypt=false' forecast-green
fetch 'https://luasforecasts.rpa.ie/xml/get.ashx?action=forecast&stop=tal&encrypt=false' forecast-red
fetch 'https://www.luas.ie/travel-updates/' travel-updates
fetch 'https://m.luas.ie/service-disruption-info.html' mobile-disruption
```

Two forecast stops because the `<message>` banner is line-wide: Ranelagh
covers the Green line, Tallaght the Red - polling all ~67 stops would answer
nothing more. Cron, every three hours at an off-peak minute in the collector's
habit of not landing on :00:

```
17 */3 * * * /home/pi/luas-probe/probe.sh
```

Volume is dominated by the travel-updates HTML: at 8 fetches a day for a
month, on the order of 10-20 MB total. Gzip the day files after a week if it
grates.

Two one-off fetches by hand, no cron: `https://www.luas.ie/accessibility/`
for the lifted-stop roll, and one `action=forecast` with a bogus stop code to
see what an error response looks like.

After two weeks, grep the bodies for `lift|escalator` and read what came
back. That decides the source, the identity scheme, and whether the explicit
all-clear survives into whichever feed wins.

## Watch items

- The NTA's replacement Travel Information platform - the one plausible route
  to a structured alerts feed.
- NeTEx / SIRI-FM appearing for Ireland, already on the list in
  `notes/station-access.md` § The regulation.
