# 09. What one letter cannot say
*~10 min read · issues #28, #31, #32, #33 · open as of 31 August 2026*

*Where we are:* the site grades stations (chapters 04 and 05) and says what each outage did to
step-free access (chapter 07). This chapter is about the four things still open, and it is
written as reasoning rather than as a backlog, because the reasoning is the part worth reading.

## The sharpest one: an F beside a sentence saying access was fine

Open Dublin Pearse's page today and you can read both of these:

> **F · 20% available**

> *An escalator is moving stairs, so it was not a step-free route to begin with and its being
> out did not remove one.*

Pearse's August notices are a lift at platform 2 for five days, which is inside the
planned-works grace and costs nothing, and an escalator at platform 2 for sixteen days when the
issue was filed and nineteen as measured on 31 August, which overran it. **The F is entirely escalator-driven.** As far as this feed shows, the step-free
route at Pearse has been fine since 13 August.

I first wrote this issue claiming the two statements contradict each other in public. They do
not, and the correction is worth stating because it changes what the fix has to be. The site's
own explainer is accurate: *"Availability is the share of the days watched on which nothing was
reported out at this station, no lift and no escalator"*, under a heading that reads "Lift and
escalator availability". Every word of that is true and the grade measures exactly what it says
it measures.

The problem is narrower and harder.

> **Concept: one number, two populations.** A grade compresses a measurement into a letter so it
> can be compared at a glance, and the compression is only honest if everyone reading it wants
> the same question answered. Here two readers want different questions answered by the same
> chip. A wheelchair user wants to know whether they could get to a platform, and for them
> Pearse's August was fine. Somebody with a heart condition, a stick, a pram or a suitcase
> wants to know whether they faced a flight of stairs, and for them Pearse's August was bad.
> One letter cannot answer both, and the fine print that reconciles them is not what people
> read. The chip is what people read. So the failure is not inaccuracy, it is that a single
> compressed number is being asked to serve two audiences whose answers genuinely differ.

Measured on the corpus in the issue (30 Aug 2026):

| | grade as shipped | lift notices only |
|---|---|---|
| Dublin Connolly | **C** (91%) | A (100%) |
| Dublin Pearse | **F** (21%) | A (100%) |
| national figure | 67% | 70% |

### The options, and why the obvious one is refused

1. **Escalators show but stop knocking.** They already have their own bar. The grade becomes
   step-free availability and the explainer says so. Pearse goes F to A, Connolly C to A, the
   national figure 67% to 70%. This makes the grade **narrower and more honest** rather than
   more forgiving: it stops claiming to measure something it measures badly.
2. **Weight escalators at some fraction.** Refused. There is nothing to calibrate a coefficient
   against, and it would turn the grade into a number nobody can reconstruct by counting days,
   which is the one property chapter 04 built the bands to have.
3. **Keep the grade, change the wording.** Cheapest, and the wording is already accurate, so it
   fixes almost nothing.
4. **Two grades.** The most accurate and the most complexity, and the site has been deliberate
   about carrying one number.

Option 1 is the recommendation, and the precedent is the water site. Its `KNOCK_CATS` is
**binary**: health-relevant quality notices knock the grade, discolouration shows on the bar and
does not. No coefficient. That is the honest way to say "this matters less" without inventing a
number calibrated against nothing.

Which completes the three-way picture on the question the whole back half of this series turns
on:

| | what is allowed to knock the grade | who decided |
|---|---|---|
| **uisce** (water) | health-relevant notices knock; discolouration shows and does not | the author, on a binary distinction the data supports |
| **esb** (power) | planned works excluded; storm days kept, and said out loud | the regulator excludes planned works, so the site follows; nothing identifies a storm day in the feed, so the site keeps them and states the difference |
| **lifts** | planned works excused a week then counted; escalators knock, and whether they should is **open** | nobody decided anything on our behalf, so every exclusion has to be argued from scratch |

Nobody excluded anything for this site. That is the whole difficulty: the power site could
inherit a regulator's exclusions, and the water site had a clean binary in its own data. Here
there is neither, and the argument has to be made in public.

### What makes option 1 honest rather than a dodge

Dropping escalators from the number and saying nothing else would be a real loss of
information. An escalator outage stops somebody. It is not only about wheelchair access:
elderly passengers, people with a heart or lung condition, luggage, a pram or a stick can be
genuinely stopped by a flight of stairs, and the site currently has no vocabulary for that
group at all.

So the fix is paired with **saying who an escalator outage did affect**, which is issue #33,
and the two should land together.

That is derivable rather than guessable: whether the platforms the escalator served still had a
lift, a ramp or a level route. Run against both cases on record, nobody was stranded. But
establishing that takes a field the derivation does not currently read, which is the other half
of #33.

## The journey has two legs, and the model sees one

`platformAccess` starts at the ticket office. How you get from the street to the concourse is a
**separate field**, `ticketOfficeAccess`, and the derivation does not reason about it.

Connolly makes the gap concrete. Its notice is "The Escalator at **the main concourse**", which
is the entrance leg, and Connolly's escalator is named in `ticketOfficeAccess` and nowhere else:

> "Escalator, lift or stairs from Amiens Street and from LUAS stop. Level access from car park."

Checking only the platform field published "Irish Rail's page for Dublin Connolly does not
mention an escalator" at the one station where that line rendered, and it was false. Chapter
07's branch fixed the *mention check* by reading both fields, and the station page now quotes
both, labelled, because a lift or an escalator can be on either leg.

But the **derivation still models only the platform leg**, and that is a real limit rather than
a tidy one: a lift outage at a station entrance would be reasoned about against prose describing
a different part of the building. No notice on record is of that shape, which is why it is an
issue rather than a bug, and `ticketOfficeAccess` is present at 143 of 152 stations, so there is
something to work with.

A rule worth writing down before it is needed, from the same issue: if an escalator is ever the
**only powered way up** at a station, its outage leaves stairs only, and that is a genuine loss
for exactly the group above, so it should knock whatever else is decided. There are zero such
stations today. Only Dublin Pearse and Tara Street name an escalator in `platformAccess`,
Connolly names one in `ticketOfficeAccess`, and all three also have lifts.

## The largest unclaimed win

A lift out does not strand a station. It strands a **platform**. And the other platform is
frequently at street or car park level and needs no lift at all, and Irish Rail's prose says
which one in plain words:

| station | lift serves | still step-free |
|---|---|---|
| Athy | platform 2 | "Level to platform 1" |
| Malahide | platform 2 | "Level to platform 1 (City Centre)" |
| Portlaoise | platform 1 | "Level to platform 2" |
| Skerries | platform 2 | "Level to platform 1" |
| Dublin Pearse | platform 2 | "Ramp to platform 1 (City Centre and northbound)" |
| Dublin Connolly | platforms 6, 7 | "Level access to platforms 1, 2, 3 and 4 from ticket office" |

**32 of the 57 stations that claim a lift name at least one platform reached without one, and
12 of the 21 that have had a notice do.** That is an order of magnitude more than
`STEP_FREE_ALTERNATIVES`, which has two entries.

It belongs in an archive because it bounds how bad a recorded outage was. "The lift to platform
2 was out for twelve days" and "the lift to platform 2 was out for twelve days, and platform 1
was level throughout" describe different events, and the site cannot currently tell them apart.

It is also safe to derive, unlike the connectives that caused the Hazelhatch misreading.
"Level to platform 1" is a direct statement, not an inference, and the model already works out
which platforms the lift serves, so the complement falls out of what is there. No new source,
no labelling, no hand-maintained file.

The wording has to keep two claims apart, and this is the part that would be easy to get wrong:
`STEP_FREE_ALTERNATIVES` says *"you can still reach this platform another way"*, same platform,
alternative route. This says *"that platform was unreachable, this one was not"*, a different
platform and therefore a different train. The second is weaker and must not be dressed as the
first.

### And what is refused

The obvious next step is to label which direction each platform faces, so the site could say
"you could still travel towards the city". It should not be taken, and the reason is a
statement about what this site is.

**This is an outage archive, not a travel planner.** A reader here is looking at what happened,
not deciding which train to catch, and a direction label only pays off for somebody planning a
journey.

It is also the expensive kind of fact. Only 10 of 57 stations name a direction in their prose,
and no source checked has the rest: chapter 06's GTFS carries no platform data for Irish Rail
at all, OpenStreetMap has no floor-level tags outside the Dublin termini, NaPTAN's `AccessArea`
is null on all 152 rail stops. So it would be roughly 120 platforms labelled **by hand**, which
is precisely the unprovenanced second source the scoping note warns against, bought for a
question this site does not answer.

## The small one

Issue #28: the lift and escalator strips on a bar are not labelled on the overview row, so a
reader cannot tell which is which without opening the station. Labelling was tried and rejected
once, because the label column shortened that one station's bar and knocked its day cells out
of line with every other row's. The labels stay on the drill-down, where the bars are tall. A
better answer has not been found yet, and with escalators possibly leaving the grade it may
change shape entirely.

## Where that leaves the site

Four open questions, three of which are about the same thing from different angles: the site
knows more about what a lift outage did than it is currently saying, and the one number on the
front is carrying more weight than one number can.

None of them is a bug. All of them are decisions that were made correctly against the question
being asked at the time, and that a later question has made uncomfortable. That is what the
`notes/` directory is for, and it is why these are issues with the numbers in them rather than
todos.

## Notes

- Issue #32, "The grade and the station page disagree about escalators" (30 Aug 2026):
  the correction to its own framing, the measured table, the four options, the `KNOCK_CATS`
  precedent, and the only-powered-way-up rule.
- Issue #33, "Model the entrance leg, and say who an escalator outage affected" (30 Aug 2026):
  the two fields, the Connolly quotation, `ticketOfficeAccess` present at 143 of 152.
- Issue #31, "Say which platform was still step-free when a lift was out" (30 Aug 2026): the
  six-station table, 32 of 57 and 12 of 21, the wording distinction, and the struck direction
  labelling.
- Issue #28, "Lift and escalator bars are not disambiguated in the bar views" (29 Aug 2026);
  the rejected label column is in `notes/site.md` § One bar per kind.
- `notes/station-access.md` §§ Escalators are not step-free, The other platform is often still
  step-free (30 Aug 2026).
- Pearse at F / 21% and the national 67% against 70% are as measured in issue #32 on
  30 Aug 2026. Re-measured 31 Aug 2026 the same figures read Pearse F / 20% and 67% aggregate;
  the corpus grew a day in between and the comparison is unchanged.
