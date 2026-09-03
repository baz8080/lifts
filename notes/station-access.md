# What a station has, and what an outage means - 2026-08-30

The site could count lift outages but had no idea what a station *was*. A
station with no lift and no notice read exactly like a station whose lift was
working, and the national figure had no denominator: "66% across the stations
listed" says nothing until you know how many stations there are. Issue #24.

This note records what the sources turned out to be, and the one reading
mistake that nearly shipped.

## "and" is a sequence, not a choice

Irish Rail's station pages carry a `platformAccess` field. It is prose, written
by hand, and its **"and" lists a route you traverse, not alternatives you pick
between**.

> Hazelhatch and Celbridge: "All platforms can be accessed via lifts and ramps"

You need both. The ramp gets you along; the lift does the level change. There
is no way to most platforms there without the lift. This session first read
that sentence as a disjunction and concluded a lift outage at Hazelhatch left
access intact - the exact opposite of the truth, and in the one direction that
strands a reader on a platform. Barry, who knows the station, caught it.

Checked across all 61 stations whose prose mentions a lift, the conjunctive
reading holds everywhere:

- **"and" as a sequence: 29 stations.** "Lift and footbridge to platform 2"
  (Malahide, Skerries, Portlaoise, Maynooth, Monasterevin, Portarlington,
  Templemore, Tullamore, Balbriggan, Laytown) is lift up, cross, lift down.
  Same for "Lifts and footbridge to all platforms" (Ballybrophy, Clontarf Road,
  Gort) and "Platforms accessible via stairs and lifts" (Clondalkin, Grand
  Canal Dock, Kishoge).
- **"or" is a real disjunction, but it is nearly always "or stairs": 11
  stations.** Adamstown, Bayside, Clonsilla, Glenageary, Howth Junction,
  Shankill, Blackrock, Booterstown, Bray, Tara Street. Stairs are not a
  step-free alternative, so the lift is still the only way.
- **Two stations, of 61, name a step-free way round a lift for the same
  platform.** Raheny, "Lift or ramp to platform 1", and Cork, "Ramp or lift to
  platform 5A, 5B and 6". They are the whole of
  `lift_access.model.STEP_FREE_ALTERNATIVES`.

So the question issue #24 set out to answer - *when a lift is out, is there
another accessible way in?* - has a near-constant answer on this network:
**no**. That is worth publishing, and it means no route engine is needed. The
model works out which platforms a lift serves, assumes an outage removes
step-free access to them, and carves out the two exceptions by hand.

`lift_access/model.py` deliberately does not parse connectives at all. Adding an
entry to the exception list is a human decision in a diff, never a parser
output, and `tests/test_site_real.py` fails if any published verdict claims an
alternative that is not in it.

## The chip

The two exceptions get a small green pill, "Step-free route", on the overview
row, the app's station detail and the static station page, and the card that
quotes the prose says which line earned it. It deliberately does not say
"accessible station" and does not use the international access symbol: both
would read as a far bigger claim than the reviewed list makes, which is only
that Irish Rail's page names a step-free way to a platform there that does not
use the lift.

Neither Raheny nor Cork has ever had a notice in the corpus, so the chip has
never rendered on the live site. `tests/test_site_render.py` is the only thing
exercising it, which is why it is tested rather than left to be discovered.

## Three things a review caught

**A summary sentence is not a per-platform claim.** Pearse opens "Via ramps,
stairs, escalators, and lifts." - a lift, no platform number. Counted as
covering the station, it made the page's own "Ramp to platform 1" a lift
platform, and a notice about platform 1 published "Platform 1 is reached by
lift". Specific beats general now: a bare-lift segment means every platform only
when no other segment names one.

**A reviewed entry expires with the page it quotes.** `STEP_FREE_ALTERNATIVES`
cites a sentence, and these pages are refetched monthly because Irish Rail
rewords them. If the sentence is gone the entry stops applying and the verdict
becomes `unknown`, not `lost`: the review said there was a way round, and a
reworded page is not evidence there is not. `tests/test_site_real.py` fails
loudly so somebody looks again.

**A partial fetch is refused, not warned about.** `latest_snapshot` reads the
newest file, so a snapshot written during an irishrail.ie wobble shadows the
last good one permanently, and the damage is invisible: those stations lose
their verdicts to "not in the station snapshot" and the denominator quietly
shrinks. Nobody spots 38 empty bodies in an 8 MB diff. Transient failures are
retried, and if any station is still missing nothing is written at all.

## It is an inference, and the page says so

Every access line on the site is worked out from a page somebody typed. This
project has already found a typo in it (Rush and Lusk, platform 1 twice), a
self-contradiction (Greystones), a station whose page says "Level" while its
lifts break (Limerick Junction), and an escalator omitted from the field that
should carry it (Connolly). Presenting derived sentences in a confident voice on
top of that would be claiming more than is known.

So the card carries a caveat in the site's own words: worked out from Irish
Rail's page, written by hand, wrong before, a careful reading rather than a
survey, and blind to whatever the page leaves out. The app shows verdicts
without that card, so the caveat travels in `data.js` and renders there too.

And it asks. A static site has no feedback channel, so the caveat ends in a
prefilled GitHub issue link: "Know this station? Tell us what this gets wrong."
People who use these stations know things no source here records, and a filed
issue is auditable in the way this project asks every other claim to be. It is
also the only route by which a fact that exists nowhere machine-readable can
ever reach the site.

## What the second review caught

Three of its findings were the first review's own findings, reappearing in the
code written to fix them. Worth recording as a habit rather than three bugs.

- **A stale reviewed entry forfeited every other platform.** The first review
  found that a notice naming platforms the page does not list a lift at was
  discarding the platforms it *did* know, and that was fixed by partitioning.
  The drift check added afterwards repeated it: a reworded Cork page would have
  taken platform 7 down with 5A. Same partition now.
- **The app caveat was shown where no derivation ran.** The first review found
  the step-free chip rendering for a station absent from the snapshot. The
  caveat added afterwards was a single global flag and did the same thing, so
  "worked out from Irish Rail's page" could sit above "this station is not in
  the station snapshot". It is gated per station now.
- **The correction link pointed at pages that do not exist.** The permalink was
  slugged from the snapshot's station name while pages are named from the
  newest notice's, which differ at Clondalkin and Hazelhatch. Both the slug and
  the issue title now come from what the page is actually called.

And one that was nobody's fault twice over: **a notice naming both machines
read as unknown.** `classify` puts lift first, so "Lifts and escalators out of
order" is a lift notice whose text names an escalator, and the premise guard
fired on it. The worst case for a reader became the least informative verdict.
The guard now distinguishes a text naming only the *other* machine, which means
the head is probably wrong, from one naming both, which is a combined outage:
whatever else broke, the lift is out, so the platforms are lost. The escalator
branch still withdraws on both, because "an escalator was never step-free" is no
comfort if a lift went with it.

Two more from the same pass were latent with no instance in the data, and were
taken anyway because the fix was a token each and the failure would have been
silent. A block tag carrying an attribute, `<br class="x">` from a CMS paste,
missed the separator pattern and joined two access lines, which manufactures a
false *specific* and defeats specific-beats-general from the other side. And a
body that is not UTF-8, or an index that is an HTML error page, raises a
`ValueError` that neither `HTTPError` nor `OSError` catches, aborting a run whose
entire job is to report which stations it could not get.

One was left. `has_lift` tests `denies_lift` before `claims_lift`, so a
per-platform "no lift on this side" would silence a lift the same page claims
elsewhere. Fixing it properly means making the denial per-platform, which is a
modelling decision with no data to design against: Dromod is the only station
using the phrase and it genuinely has no lift. It fails to `unknown` rather than
to a false claim. Left until something real turns up.

## The safe direction

A reader told access is gone when it was not has made one wasted check. A reader
told access remains when it is gone is stranded. Every rule here leans the same
way: default to "gone", say "unknown" freely, and never infer "remains".

## The lift-call sentence is boilerplate

> "To access the lift, you must call via the help point at each landing of the
> lift shaft. Please see lift call operation page for steps to call the lift."

Pasted template text at dozens of stations. At **three** it is the only mention
of a lift - Greystones, Killiney, Donabate - so matching on the word "lift"
invents lifts nobody claimed. It is stripped before anything else. This is also
what dissolves the Greystones contradiction: "Footbridge **only** to platform 2"
is the real claim and the lift sentence is template.

Dromod carries the one explicit negative: "(no lift at this station)".

## Escalators are not step-free, and what that does and does not prove

**What is deduced.** An escalator is moving stairs. It was therefore never a
step-free route, so its going out of service cannot remove one. That is valid,
and it is all the site says now.

**What was being claimed and is not proven.** The first version published "this
did not remove step-free access" for every escalator outage. That is a claim
about the *station's* access state, not about the escalator, and it needs the
station's own prose to support it. Nothing checked. The escalator branch returned
before the `station is None` guard, so it was the only path in the module that
made a confident claim without consulting the source, while every other path can
fall back to `unknown`. At Connolly it happened to be true - level access to
platforms 1 to 4, a ramp to 5, a lift to 6 and 7 - but the code never looked.

**The premise the deduction rests on** is that "escalator" in a hand-written head
means an escalator. Checked across the corpus: 0 disagreements between head and
text in 228 messages, and both escalator notices name the machine unambiguously.
That is a strong prior and not a proof, so `verdict` now returns `unknown` when a
notice headed as one machine names the other in its text. It has never fired.

**The journey has two legs and the derivation sees one.** `platformAccess`
starts at the ticket office. `ticketOfficeAccess` is how you get from the street
to the concourse, and it is a separate field. Connolly's notice is "The
Escalator at **the main concourse**" - the entrance leg - and Connolly's
escalator is named in `ticketOfficeAccess` and nowhere else:

> "Escalator, lift or stairs from Amiens Street and from LUAS stop. Level access
> from car park."

Checking only `platformAccess` published "Irish Rail's page for Dublin Connolly
does not mention an escalator" at the one station where that line rendered, and
it was false. The escalator check now reads both fields and the station page
quotes both, labelled, because a lift or an escalator can be on either leg.

**Settled 2026-09-03: both legs.** The paragraph below stood until then; § *The
entrance leg, and who an escalator served* has what replaced it.

**The derivation still models only the platform leg**, and that is a real limit
rather than a tidy one: a lift outage at a station entrance would be reasoned
about against prose that describes a different part of the building. No notice
on record is of that shape, and issue #33 carries it.

**Where the source is silent.** Only 2 of 152 station pages mention an escalator
at all, and **Connolly's does not** - though we know it has one, because it
broke. So the prose is demonstrably not a complete inventory of vertical
circulation, and "no travelator is mentioned anywhere" is close to worthless as
evidence that none exists. A flat moving walkway *is* step-free, and one called
an escalator in a notice would break the deduction. None is named in any of the
152 pages, which is the most that can be said. Where the page does not mention an
escalator, the verdict now says so rather than implying the machine's role is
known.

**Settled 2026-09-03: the grade.** It counted escalator outages at the same
weight as lift outages, so the grade and the station page disagreed in public:
Dublin Pearse graded F, the worst band, on the strength of an escalator alone
(issue #32). Escalator days are off the total now and the grade is named lift
availability; `site.md` § *The grade is lift availability* has the numbers, the
rejected options and the one escalator case that should knock, which
`tests/test_site_real.py` guards. It was not settled from `platformAccess`,
which mentions an escalator at 2 of 147 stations.

## The other platform is often still step-free, and the prose says so

Built 2026-09-01 (issue #31); the rule is at the end of this section. Recorded
first because it was the largest unclaimed win here, bigger than the exception
list by an order of magnitude.

A lift out does not strand a station, it strands a *platform*. The other
platform is frequently at street or car park level and needs no lift at all,
and Irish Rail's prose says which one in plain words:

| station | lift serves | still step-free |
|---|---|---|
| Athy | platform 2 | "Level to platform 1" |
| Malahide | platform 2 | "Level to platform 1 (City Centre)" |
| Portlaoise | platform 1 | "Level to platform 2" |
| Skerries | platform 2 | "Level to platform 1" |
| Dublin Pearse | platform 2 | "Ramp to platform 1 (City Centre and northbound)" |
| Dublin Connolly | platforms 6, 7 | "Level access to platforms 1, 2, 3 and 4 from ticket office" |

**32 of the 57 stations that claim a lift name at least one platform reached
without one, and 12 of the 21 that have had a notice do.**

This is a different claim from `STEP_FREE_ALTERNATIVES`, and the wording has to
keep them apart. The exception list says *"you can still reach this platform
another way"*. This says *"you cannot reach that platform, but this one is
still fine"*. The second is weaker and is about a different train.

It is also safe to derive, unlike the connectives: "Level to platform 1" is a
direct statement, not an inference. The model already knows which platforms the
lift serves, so the complement falls out.

### Not the direction, and not by hand

The obvious next step looks like labelling which direction each platform faces,
so the site could say "you could still travel towards the city". It should not
be taken. **This is an outage archive, not a travel planner.** A reader here is
looking at what happened, not deciding which train to catch, and a direction
label only pays off for somebody planning a journey.

It is also the expensive kind of fact. Only 10 of 57 stations name a direction
in their prose, and no source checked has the rest: GTFS carries no platform
data for Irish Rail at all, OSM has no `level` tags outside the Dublin termini,
NaPTAN's `AccessArea` is null on all 152 rail stops. So it would be roughly 120
platforms labelled by hand - the unprovenanced file `accessible-routes.md`
warns against - bought for a question this site does not answer.

The archive-shaped version of the same fact needs no labelling at all: "the
lift to platform 2 was out for twelve days, and platform 1 was level
throughout" bounds how bad the outage was, which is exactly what an archive is
for. That is derivable from the prose today.

### The rule, as built (2026-09-01)

`step_free_platforms(station)` splits the prose on `SENTENCE`, the split
`implicated` already uses. A sentence contributes its platforms if it says
`level` or `ramp(s)`, names a platform number, and mentions no lift ("lifts and
ramps" is a sequence), no stairs, staircase, stairway or step, no footbridge,
subway or escalator, and no "from platform" (a
between-platforms link says nothing about the street leg: Dún Laoghaire's "Ramp
access from Platform 2 to Platform 3").

Only the stair wording excludes a sentence on the 2026-08-30 corpus (Gorey's
"Level, stairs only to platform 2", Connolly's "Ramp or stairs to platform 5").
The rest are guards against a rewording, drawn from wording the pages already
use: 34 stations say step, 39 footbridge, 3 subway (the Irish word for a
pedestrian underpass - Athlone's "Steps or lift and subway to platforms No. 2
and 3"), 2 escalator. "Level crossing" was in the list and came out on
2026-09-01: it appears nowhere in the prose, so it guarded against nothing.

Containment, not an anchored "Level to": Cork's "Platforms 1, 2, 3 and 4 are
level" is as direct a statement, and a dry run over all 152 stations found no
sentence it reads wrongly. Sentences naming no number drop out - Limerick
Junction's bare "Level", Dromod's "Level to main platform", Garryduff's "Ramp to
Southbound platform" - which is consistent with direction staying out of scope.

The note fires only on the plain-loss branch of `verdict`, and is withheld
wherever the two hand-written sources disagree: at a lift-served platform, which
neutralises Rush and Lusk's typo ("Level access to platform 1" beside "Lift and
footbridge to platform 1"); at a platform the notice itself names (Athy's names
1 and 2 where the page calls 1 level); and at a general lift claim, which gets
no note at all (Bray, Lansdowne Road, Longford, Dalkey).

The wording - "Platform 1 needed no lift, so it kept step-free access: 'Level to
platform 1'." - is deliberately not the exception list's "another step-free
way", which means the *same* platform stays reachable. Five lost verdicts gain
it on the corpus as of 2026-09-01 (Pearse, Dún Laoghaire, Malahide,
Portarlington, Tullamore); Athy's and Skerries' notices name the level platform
themselves. It is re-derived from the live prose at every build, so a reworded
page withdraws it.

## When it says "unknown"

Both sources are hand-written and they disagree. On the corpus as of
2026-08-30, six of 24 notices come back unknown, and every one is a real
discrepancy worth not papering over:

| station | why |
|---|---|
| Limerick Junction | `platformAccess` is the single word "Level", yet it has lift notices, and OSM maps two lifts |
| Greystones (x2) | prose names no lift outside the boilerplate |
| Rush and Lusk | prose says "Level access to platform 1 / Lift and footbridge to platform 1" - platform 1 twice, plainly a typo; the notice names platform 2 |
| Portlaoise | prose puts the lift at platform 1; the notice says platform 2 |
| Carlow | prose puts the lift at platform 2; the notice says platform 1 |

A lift notice that names the way in is unknown where `ticketOfficeAccess` puts
no lift there, or is blank. No notice on the corpus is of that shape.

A notice naming more platforms than the page accounts for keeps what it knows
rather than forfeiting everything: Athy's notice names 1 and 2, the page has a
lift at 2 and calls 1 level, and platform 2 is still knowable.

## The entrance leg, and who an escalator served - 2026-09-03

Issue #33, the two follow-ups #30 left. Built on the corpus to 3 September:
28 notices, three of them escalators (Pearse, Connolly, Tara Street).

### Which leg a notice is about is read from its own text

`leg_named` reads the notice: a platform number or the word "platform" is the
platform leg; failing that, `concourse`, `entrance`, `booking hall`, `ticket
office`, `ticket hall`, `car park` or `street level` is the entrance leg; a
notice naming neither is unlocated. A platform wins over an entrance word,
because `platformAccess` starts at the ticket office: "the lift from the
concourse to platform 2" is that field's leg.

Over the 24 distinct notice texts on record: 19 platform, 1 entrance (Connolly's
"at the main concourse"), 4 unlocated (Malahide's "at Malahide Station",
Docklands' "The lift is currently out of service", Tullamore, and Clonsilla's
"on P2", which nothing here reads as a platform). No false entrance hits. The
entrance list is built from one real example and the vocabulary of
`ticketOfficeAccess` itself; a notice saying "main hall" or "foyer" falls to
unlocated, which is the reading the site had before.

### What `ticketOfficeAccess` has in it

All 152 stations carry the field. 9 are blank (the Northern Ireland stations),
26 say there is no ticket office, 89 say level, 21 say ramp. **Four name a
lift**: Connolly ("Escalator, lift or stairs from Amiens Street and from LUAS
stop. / Level access from car park. / Via main concourse."), Clondalkin ("Level
or via lift"), Docklands ("Lift to ticket office") and Grand Canal Dock
("Through main entrance building into the booking hall on platform 2 via stairs
or lift"). **One names an escalator**: Connolly. The field is literally how to
reach the ticket office, so "No ticket office" says nothing about the door, and
is read as the page naming no lift there.

Two shapes caught in the dry run. Kilcoole's field is the two words "Not level",
which a filter that only looks for the word would quote as a level way in;
`NEGATED` excludes any level or ramp sentence carrying "no" or "not", except a
"No" before a number, which is how Carrigaloe and Dalkey label a platform. Grand Canal Dock's lift sentence names
platform 2 on its way to naming the lift, so the entrance picker takes the first
lift sentence whatever platforms it mentions; there is one way in.

And one caught in review: Pearse's way-in field names no lift, but its
`platformAccess` carries "Lifts/stairs/Escalators from the Pearse Street
entrance". A notice naming that entrance must not be told the page names no
lift there. `entrance_lift_sentence` reads both fields, and a lift notice whose
entrance lift is named only on the platform side falls through to the platform
reading, which is what it got before this change.

### A lift notice on the entrance leg

Read against `ticketOfficeAccess` and nothing else, before the platform-leg lift
claim is consulted, because a page can put a lift on the way in and claim none
to the platforms. Where the field names a lift: **lost**, quoting the sentence,
"so step-free access into the station was gone while this was listed", plus a
level or ramped sentence from the same field when there is one that names no
lift and nothing stepped (Connolly's "Level access from car park"). Where it
names none, or is blank: **unknown**, saying which. Clondalkin's "Level or via
lift" comes out lost, the Hazelhatch reading: the module does not parse
connectives, and the quote lets a reader see the page's own words. The entrance
note is worded "needed no lift" and never "kept step-free access", which the
real-corpus guard from #31 reads against `lift_platforms`.

No lift notice on record names the way in, so this is machinery for a notice
that has not arrived, built because the escalator sentence below could not be
written honestly without it.

### Who an escalator outage affected

The deduction stays and is all that is *known*: an escalator has steps, so it
was never a step-free route, so losing it cannot lose one. The sentence now goes
on to say who did lose something - "Anyone who finds a flight of stairs hard,
or has a buggy, a suitcase or a stick, did lose a way up" - and then what the
page puts on the same leg, because a lift to the platforms says nothing about
the way in:

| notice | leg | what the page puts there |
|---|---|---|
| Pearse, "at platform 2" | platform | "Lift or stairs to platform 2 (southbound)" |
| Tara Street, "at platform 2" | platform | "Both platforms can be accessed by lifts, stairs or escalator" |
| Connolly, "at the main concourse" | entrance | "Escalator, lift or stairs from Amiens Street and from LUAS stop", and "Level access from car park" |

The lift sentence is picked specific-before-general, as `read_platform_access`
reads the page, which is what keeps Pearse's summary "Via ramps, stairs,
escalators, and lifts." out of the quote, and the phrase names the platforms
the quoted sentence puts a lift at rather than the notice's (Athy's "Lift to
platform 2" beside a notice naming 1 and 2). A platform the page calls level is
a disagreement, not a way round: a level platform has no level change for an
escalator to make, so the sentence says the notice and the page disagree, the
rule every other disagreement here follows. A platform with neither gets "names
no lift or level way to platform N, so nothing on it says there was another way
up", and a station whose page claims no lift at all says so by name. That last
is the only-powered-way-up shape, which no station has and
`tests/test_site_real.py` still guards for the grade. An unlocated escalator
notice says the notice does not say where the escalator is.

Every sentence says what the page *names*. None says a lift was working, which
the page cannot know; a real-corpus test forbids "still had", "remains",
"available" and "working" in every verdict.

### The one thing the site knows that the page does not

A lift notice at the same station listed while the escalator was. Quoting "the
page puts a lift on the way to platform 2 as well" under a row that shows that
lift out would be the page contradicting itself, so `render.shard`, the one
place that holds all of a station's outages, sets `lift_listed_too` and the
sentence becomes "..., though a lift notice at this station overlapped this
one". It says no more than that: the flag is station-wide, so which lift was out
is not established and the sentence does not say. Half-open intervals, with
`listed_in`'s one exception for a notice first seen at the last poll: Pearse's
lift came down at the poll its escalator went up (13 August, 10:30Z), which is
touching, not overlapping, and there are zero overlaps on the corpus. The
real-corpus test asserts the flag against the station's own rows, not against
that count. `report` has no listings and never sets it.

### On the page

The label reads "A way up lost, not step-free access" in place of "Not a
step-free route", which read as nothing happened. The box loses its green
border for a neutral one: neither the red of a loss nor the green of a way
round. The access card's caveat says which list each leg is read against.

### Rejected

- **Parsing "or" as a choice on the entrance leg.** The module refuses
  connectives everywhere else for a reason that holds here: "Level or via lift"
  may well be a choice, but nothing distinguishes it from a sequence in the
  text, and the safe reading costs one wasted check.
- **A hand-reviewed list of entrance alternatives**, like `STEP_FREE_ALTERNATIVES`.
  Four fields name a lift and none has had a notice; nothing to review yet.
- **A fifth verdict state** for an escalator with no other way up. The label
  carries the distinction the reader needs, and the grade rule for that case is
  settled in `site.md` and guarded.
- **Weighting the grade** for the people an escalator serves. #43 settled the
  grade as the lift bar's; this is the page saying who is off it.

A future notice of the shape "lift at the Townsend Street entrance" at Tara
Street would read as the entrance leg against a field that does not mention that
entrance (the stairs-only line sits in `platformAccess`) and come out unknown.
That is the safe direction.

## The sources, and the ones that are closed

The three checks `accessible-routes.md` scoped are answered. They are struck
there, not here.

**What is used:** `https://www.irishrail.ie/en-ie/station/<slug>/_payload.json`.
Server-rendered Nuxt, named fields, no HTML parsing. `robots.txt` disallows only
`/stations.csv`. The find-a-station payload carries `kontentStations`, the full
list of 152 slugs, so nothing is crawled.

**The join is free.** Each payload carries `stationCode`, and it is exactly the
`locationCodes` code space the message feed uses. All 15 codes with lift
notices matched, 15/15. The name-to-code mapping the scope worried about is not
needed.

**The site already held half of this.** `messages.text_raw` names the platform -
"The lift at platform 2", "The lifts at platform 1 and 4" - and nothing parsed
it. `head` says only "Dublin Pearse - Lift out of order".

**Two fields that look useful and are not:**

- `alert` / `alertStart` / `alertEnd`. 131 stations carry one and they are never
  cleared: `alertEnd` values run back to 2014, 2015 and 2021. It is the last
  alert ever posted, not a live one.
- `wheelchairAvailability` means "a wheelchair can be borrowed here", not "this
  station is accessible". Pearse says Yes, Docklands says No. Never surface it
  as accessibility.

## Why scraping prose is the only option, not the lazy one

Scraping a marketing site for accessibility facts should be a last resort, and
this is the record that it is one. Four independent consumers of Irish public
transport data hit the same wall, which is much stronger evidence that the data
was never created than that the searching was bad.

### The formats that exist for exactly this, and that Ireland does not publish

- **NeTEx** is the European standard for a station's static equipment and
  accessibility: lifts, escalators, ramps, entrances, and the paths between
  them. **SIRI-FM** (Facility Monitoring) is its realtime companion, and it is
  precisely a live "is this lift working" feed.
- Neither is published for Ireland. Searched data.gov.ie and the NTA's
  `transitData/PT_Data.html` catalogue on 2026-08-30: 24 GTFS archives, NaPTAN,
  PTIMS, and nothing else. The only "accessibility" strings on the NTA data page
  are navigation menu links.

### The regulation, and the hole in it

Delegated Regulation (EU) 2017/1926 requires each member state to run a National
Access Point publishing the listed travel data types, with NeTEx as the required
representation. The Annex applies to those data types **"provided they exist in
digital machine-readable format"**.

That is the whole story. The duty is to publish what you hold, not to create it.
If Irish Rail never captured a lift inventory in machine-readable form, nothing
compels them to start, and the obligation is satisfied by publishing timetables.
So the absence is lawful and permanent-looking rather than an oversight somebody
will fix.

### What the mapping apps have to work with, which is nothing

Google Maps, Apple Maps, Transit, Citymapper and Moovit all consume GTFS for
transit directions, and accessible routing in all of them rests on three fields.
Checked against the live Irish Rail feed:

| field | purpose | present? |
|---|---|---|
| `stops.txt` `wheelchair_boarding` | can you board here | **no, column absent** |
| `trips.txt` `wheelchair_accessible` | does the vehicle take a wheelchair | **no, column absent** |
| `pathways.txt` | step-free route, entrance to platform | **no, file absent** |

So none of them can offer wheelchair routing on Irish Rail. That is a gap in the
input, not in their products. Their place-level accessibility pins come from
their own pipelines instead - Google from Places and Local Guides, Apple from
its own surveys - which is the same shape as the OpenStreetMap result below:
crowd-sourced, patchy, no platform detail, and no idea a lift is out today.

### Where that leaves this

The only machine-readable statement of what an Irish rail station has is a
free-text CMS field on irishrail.ie, written by hand, with no schema, no
versioning and no obligation to be accurate. This project has already found a
typo in it (Rush and Lusk naming platform 1 twice), a self-contradiction
(Greystones), and a station whose page says "Level" while its lifts break
(Limerick Junction).

Which makes the dated snapshots in `lifts-data/stations/` the only versioned
machine-readable record of Irish rail station access that appears to exist. That
was not the intent and it is a poor substitute for the operator holding one, but
it is a reason to keep the monthly refresh running beyond keeping the derivation
fresh.

**Do not re-run these searches.** GTFS, GTFS-Realtime, NaPTAN, PTIMS, the NTA
developer API and OpenStreetMap are all checked and recorded, here and in
`accessible-routes.md`. If anything changes it will be because Ireland starts
publishing NeTEx, and that is the one thing worth checking again.

## OpenStreetMap: carried, measured, removed

It was here as a second opinion on Irish Rail's prose and it is gone. Recorded
at this length so nobody adds it back on the same hunch, because the hunch is a
good one and it is wrong.

**What it could do.** It is the only machine-readable station graph that exists
for this network. Around Pearse: named `Platform 1` and `Platform 2` ways, four
`highway=elevator` nodes carrying `level` tags, escalators as `highway=steps` +
`conveying`, `highway=corridor`, `wheelchair` tags. A routable topology, the
thing GTFS `pathways.txt` would have been. It also spots 13 stations where the
prose mentions no lift and OSM maps one, Limerick Junction among them.

**What it could not do.** Three measurements, all against the real data:

1. **It changed no verdict.** `has_lift()` was consulted in exactly one place,
   as `!= "yes"`, and OSM could only move a station from `no` to `unknown`.
   Both fail that test. Checked with a synthetic digest mapping a lift at all
   152 stations: 24 outages, 0 verdicts changed.
2. **Its one signal was redundant.** A station in those 13 that has a notice
   already returns `unknown` without it, because `claims_lift` is false.
   Limerick Junction: same verdict, same wording, with or without.
3. **It could not answer the street-side question**, which is the only thing
   that would have earned its keep. "Which platform is reachable without a
   lift" needs `level` tags on platforms. Sampled over 12 stations that have
   had notices: 12 of 12 had platforms mapped, **2 of 12** carried a `level`
   tag, both Dublin termini. Everywhere else there is platform geometry and no
   vertical information, so the graph is not traversable.

Irish Rail's prose answers that same question at 32 of 57 stations, in words.

**So it went.** It cost about 60 lines, a monthly HTTP budget against a service
that rate-limits, and the one place the raw-artefact invariant was bent - the
raw map extracts total roughly 450 MB, so the digest had to be derived rather
than verbatim. For nothing that reached a reader.

The one thing that would bring it back: the day the site says **"this station
has no lift"** out loud, those 13 stations become a wrong claim rather than a
silent one. Nothing says that today, and the site is an outage archive, so
nothing may ever need to.

## The snapshot

`lifts-data/stations/irishrail-<date>.jsonl` holds every payload **verbatim**,
one per line, `sort_keys=True`, the shape `store.write_raw` uses. 7.8 MB plain,
which git stores at about 2 MB and which greps and diffs. Never edited; the
derivation is always recomputed from it.

Refreshed monthly by `.github/workflows/stations.yml`, which opens a PR rather
than pushing: a reworded station page can move a verdict from "no step-free
access" to "unknown" and back, and that is not a change to land unread. Never on
the Pi, never in the 30-minute poll loop.

## Reading the report

`python -m lift_access --data-dir <dir> report` prints every notice's verdict
beside the prose it came from, and `--all` prints every station that claims a
lift. It is the only real check on a derivation built out of somebody's
hand-written sentences, and it is how the Hazelhatch reading was caught. Read it
when a refresh changes anything.
