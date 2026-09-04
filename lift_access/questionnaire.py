"""A per-station form for whoever knows the station, prefilled with what the repo knows.

Generated rather than written, so the station-specific questions come from the
data: the page's own sentences, the derivation's reading of them, every notice
the feed has carried about the place, the business case's description where it
has one, and the draft observations for the person to correct. The definitions
come first because the sources already in hand disagree for want of them.
`notes/step-free-graph.md` § The questionnaire.
"""

from __future__ import annotations

from . import model, nta, seed

# The page-versus-feed disagreements `notes/station-access.md` records, so the
# form asks the one person who can settle each.
PAGE_DISCREPANCIES = {
    "LMRKJ": "Irish Rail's page says only \"Level\", yet the station has had lift notices. "
             "How many lifts are there, and what do they connect?",
    "GSTNS": "Irish Rail's page names no lift outside the lift-call boilerplate, yet the "
             "station has had lift notices. Where is the lift, and what does it serve?",
    "RLUSK": "Irish Rail's page says \"Level access to platform 1\" and \"Lift and footbridge "
             "to platform 1\", platform 1 twice, and a notice named platform 2. Which "
             "platform does the lift serve?",
    "PTLSE": "Irish Rail's page puts the lift at platform 1 and a notice said platform 2. "
             "Which is right?",
    "CRLOW": "Irish Rail's page puts the lift at platform 2 and a notice said platform 1. "
             "Which is right?",
    "CNLLY": "Irish Rail's page never mentions an escalator on the way to the platforms, "
             "yet the station has had escalator notices. Where are the escalators, and "
             "what is beside each?",
}

DEFINITIONS = """\
## Read this first: what the words mean on this form

- **Step-free** means a way from the public road to the platform edge with no
  step on it, over level ground, a ramp, a lift or an open gate, that a person
  can use **un-assisted**. A lift you call from a help point still counts.
- An escalator, a footbridge, a subway, a staff-operated barrow crossing, a
  locked wicket gate, or a route where "a companion is needed" is **not**
  step-free. Those are **assisted** routes: please record them, they are not
  counted.
- Getting **to** each platform from the road and getting **between** platforms
  are asked separately, because they are built and fixed separately.
- The step and gap between platform and train are asked separately and do not
  change the answer about the station.
- If you are not sure, say so. "Not sure" is a better answer than a guess,
  and every answer is recorded with your name and the date so it can be
  checked later.
"""

COMMON = """\
## The questions every station gets

1. **Entrances.** List each way into the station: what it is called on the
   signs, which street it is on, and whether it is level with the footpath, a
   ramp, or steps. Note any gate and its opening hours.
2. **Platforms.** The platform numbers as signed, and which trains each serves
   (towards where).
3. **From each entrance to each platform.** The route, as the sequence you
   would walk it: level walk, ramp, stairs (how many), footbridge, subway,
   lift, escalator, gate. If there are two routes, give both.
4. **Each lift.** The two places it connects, whether you call it from a help
   point, its hours, and whether it is the only step-free way to what it
   serves.
5. **Each escalator.** What it connects, whether it runs up, down or both, and
   what is beside it: stairs, a lift, or nothing.
6. **Each ramp.** Roughly how long and how steep. Could a wheelchair user
   manage it alone?
7. **Each gate or crossing.** Wicket gate, barrow crossing or level crossing;
   who may use it; whether a wheelchair fits through.
8. **When the lift is out.** What does a wheelchair user actually do at this
   station today?
9. **Getting on the train.** The step and gap at each platform, and where the
   boarding ramp is kept.
10. **You.** Your name or organisation, the date, and whether this is from a
    visit or from memory.
"""


def _quote_block(prose):
    lines = [line for line in (prose or "").split("\n") if line.strip()]
    if not lines:
        return "> *(blank)*\n"
    return "".join(f"> {line}\n" for line in lines)


def render(station, notices=(), lines=None, snapshot_name=None):
    """The form for one station as Markdown.

    `notices` is (kind, head, text) triples; `lines` the seeded observations,
    or None to seed them here.
    """
    if lines is None and snapshot_name:
        lines = seed.observations(station, snapshot_name)
    out = [f"# {station.name} ({station.code}): step-free access questionnaire\n"]
    out.append(
        "This form asks what Irish Rail's own page cannot say. Everything below "
        "that is already known is shown so you can correct it rather than start "
        "from nothing. Answers go in the log with your name and the date.\n"
    )
    out.append(DEFINITIONS)
    out.append("## What Irish Rail's page says today\n")
    out.append("**Into the station** (the page's `ticketOfficeAccess`):\n")
    out.append(_quote_block(station.ticket_office_access))
    out.append("\n**To the platforms** (the page's `platformAccess`):\n")
    out.append(_quote_block(station.platform_access))
    out.append("\nIs this right? What does it leave out?\n")

    out.append("\n## How this site reads that page\n")
    serves = station.lift_platforms
    if model.ALL_PLATFORMS in serves:
        out.append("- The page claims a lift without naming a platform, so the site reads "
                   "it as serving every platform.\n")
    elif serves:
        out.append(f"- A lift on the way to platform {model._join(sorted(serves))}.\n")
    elif station.denies_lift:
        out.append("- The page says there is no lift.\n")
    else:
        out.append("- No lift named.\n")
    level = model.step_free_platforms(station)
    for label, sentence in level:
        out.append(f"- Platform {label} reached without a lift: \"{sentence}\".\n")
    entrance = model.entrance_step_free(station)
    if entrance:
        out.append(f"- A level or ramped way in: \"{entrance}\".\n")
    entrance_lift = model.entrance_lift_sentence(station)
    if entrance_lift:
        out.append(f"- A lift on the way in: \"{entrance_lift}\".\n")
    out.append("\nIf any of that is wrong, which part, and what is true instead?\n")

    if station.code in PAGE_DISCREPANCIES:
        out.append("\n## Something the page and the notices disagree about\n")
        out.append(PAGE_DISCREPANCIES[station.code] + "\n")

    if station.code in nta.CONTEXT or station.code in nta.STATIONS:
        out.append("\n## What the Station Accessibility Programme said\n")
        if station.code in nta.STATIONS:
            rank, _ = nta.STATIONS[station.code]
            out.append(
                f"{station.name} is number {rank} of the 51 stations the programme lists "
                f"as not yet meeting the accessibility standard ({nta.PUBLISHER}, "
                f"{nta.DATE}, Table 6-2).\n"
            )
        if station.code in nta.CONTEXT:
            page, text = nta.CONTEXT[station.code]
            out.append(f"\nIts description of the station, written in 2024 (page {page}"
                       f"; progress since: {nta.DELIVERY.get(station.code, 'not stated')}):\n\n")
            out.append(f"> {text}\n\n")
            out.append("This was written in 2024. What has changed since?\n")

    distinct = []
    for kind, head, text in notices:
        if (kind, text) not in [(k, t) for k, _, t in distinct]:
            distinct.append((kind, head, text))
    if distinct:
        out.append("\n## Notices the feed has carried about this station\n")
        out.append("For each one: which machine is this, and which two places does it "
                   "connect?\n")
        for kind, head, text in distinct:
            body = model.plain(text) or "(no text)"
            out.append(f"\n- **{head}** ({kind})\n  > {' '.join(body.split())}\n")

    out.append("\n" + COMMON)

    if lines:
        out.append("\n## Draft observations, read off the page, for you to correct\n")
        out.append(
            "One per line, in the log's own form. Each is what the page says, at low "
            "confidence. Correct a line by adding a new one with the same id; a fact "
            "that is wrong outright gets a `retract` line.\n\n```\n"
        )
        out.append(seed.dumps(lines))
        out.append("```\n")
    return "".join(out)
