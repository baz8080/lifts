"""What a station has, and what a notice means, on the real published prose.

Every fixture below is the `platformAccess` HTML Irish Rail was serving on
2026-08-30, and every notice text is one the collector actually recorded. The
point of the file is the first class: "lifts and ramps" at Hazelhatch must read
as a sequence you need all of, not a choice between two, because reading it the
other way tells a wheelchair user access remains at a station where it is gone.
"""

from __future__ import annotations

import unittest

from lift_access import model

# platformAccess, verbatim, keyed by station code.
PROSE = {
    "HZLCH": "<p>All platforms can be accessed via lifts and ramps</p>",
    "BBRHY": "<p>Lifts and footbridge to all platforms</p>",
    "MHIDE": (
        "<p>Level to platform 1 (City Centre)<br>\nLift and footbridge to platform 2</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        'lift shaft. <a href="/lift-call-operation">Please see lift call operation page '
        "for steps to call the lift.</a></p>"
    ),
    "SKRES": (
        "<p>Level to platform 1<br>\nLift and footbridge to platform 2</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft.</p>"
    ),
    "CLDKN": (
        "<p>Platforms accessible via stairs and lifts.</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft.</p>"
    ),
    "ATHY": "<p>Level to platform 1<br>\nLift to platform 2</p>",
    "ADMTN": "<p>Via stairs or lift</p>",
    "RAHNY": (
        "<p>Lift or ramp to platform 1 (City Centre and Southbound)<br>\n"
        "Ramp to platform 2 (Northbound)</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft.</p>"
    ),
    "CORK": (
        "<ul>\n  <li>Platforms 1, 2, 3 and 4 are level</li>\n"
        "  <li>Ramp or lift to platform 5A, 5B and 6</li>\n</ul>\n"
        "<p>Blind passenger using lift call system to access lifts to and from subway at "
        "Kent Station Cork.<br>Link: <a href=\"https://youtu.be/x\">YouTube Video</a></p>"
    ),
    "LMRKJ": "<p>Level</p>",
    "RLUSK": (
        "<p>Level access to platform 1<br>\nLift and footbridge to platform 1</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft.</p>"
    ),
    "GSTNS": (
        "<ul>\n  <li>Level to platform 1 (northbound)</li>\n"
        "  <li>Footbridge only to platform 2 (southbound)<br>\n</li>\n"
        "  <li>To access the lift, you must call via the help point at each landing of "
        'the lift shaft. <a href="/lift-call-operation">Please see lift call operation '
        "page for steps to call the lift.</a></li>\n</ul>"
    ),
    "KILNY": (
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft. Please see lift call operation page for steps to call the lift.</p>"
    ),
    "DBATE": (
        "<p>Level access 05:45hrs - 00:30hrs Mon-Sun</p>\n<p>In order to access the lift, "
        "the customer is first required to call via the help point located at each "
        "landing of the lift shaft.</p>"
    ),
    "DRMOD": (
        "<p>Level to main platform<br>\nFootbridge to platform 2 "
        "(no lift at this station)</p>"
    ),
    "DCKLS": "<p>Lift to platforms</p>",
    "PTLSE": "<p>Level to platform 2<br>\nLift and footbridge to platform 1</p>",
    # Pearse opens with a summary sentence naming every mode in the station.
    "PERSE": (
        "<p>Via ramps, stairs, escalators, and lifts.</p>\n"
        "<p>Ramp to platform 1 (City Centre and northbound)<br>\n"
        "Lift or stairs to platform 2 (southbound)</p>\n"
        "<p>Lifts/stairs/Escalators from the Pearse Street entrance</p>"
    ),
    # Connolly has escalator notices on record and a page that never mentions one.
    "CNLLY": (
        "<ul>\n  <li>Level access to platforms 1, 2, 3 and 4 from ticket office.</li>\n"
        "  <li>Ramp or stairs to platform 5.</li>\n"
        "  <li>Lift or stairs to platforms 6 and 7.</li>\n</ul>"
    ),
    "BLANK": "",
}

NAMES = {"HZLCH": "Hazelhatch and Celbridge", "LMRKJ": "Limerick Junction"}

# ticketOfficeAccess: the street-to-concourse leg, a separate field. Connolly's
# escalator is named here and nowhere else, and Connolly is one of only two
# stations that has escalator notices.
ENTRY = {
    "CNLLY": "<p>Escalator, lift or stairs from Amiens Street and from LUAS stop.<br>"
    "Level access from car park.</p>",
    "PERSE": "<p>Level, through main entrance to the booking hall</p>",
}


def station(code):
    lift_platforms, claims, denies = model.read_platform_access(PROSE[code])
    return model.Station(
        code=code,
        name=NAMES.get(code, code.title()),
        slug=code.lower(),
        latitude=None,
        longitude=None,
        platform_access=model.plain(PROSE[code]),
        ticket_office_access=model.plain(ENTRY.get(code, "")),
        lift_platforms=lift_platforms,
        claims_lift=claims,
        denies_lift=denies,
    )


class StepFreeAccessIsLost(unittest.TestCase):
    """The default, and the reason this module exists."""

    def assert_lost(self, code, text, platforms):
        result = model.verdict(station(code), "lift", text)
        self.assertEqual(result.state, "lost", f"{code}: {result.detail}")
        self.assertEqual(result.platforms, platforms)

    def test_hazelhatch_and_is_a_sequence_not_a_choice(self):
        # "lifts and ramps" means you need both. Read as a disjunction this says
        # the ramps remain, which is the one error worth engineering against.
        self.assert_lost(
            "HZLCH",
            "The lift to Platform 2 and 3 is currently out of service.",
            ("2", "3"),
        )

    def test_a_lift_and_a_footbridge_are_one_route(self):
        self.assert_lost(
            "MHIDE", "The lift at platform 2 is currently out of service.", ("2",)
        )

    def test_stairs_are_not_a_step_free_alternative(self):
        self.assert_lost("ADMTN", "The lift is currently out of service.", ())

    def test_all_platforms_when_the_prose_names_none(self):
        result = model.verdict(station("BBRHY"), "lift", "Lifts are out of service.")
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ())

    def test_the_notice_platform_wins_when_the_prose_says_every_platform(self):
        self.assert_lost(
            "CLDKN", "The lift at platform 4 is currently out of service.", ("4",)
        )

    def test_docklands_names_no_platform_at_either_end(self):
        result = model.verdict(station("DCKLS"), "lift", "The lift is currently out of service.")
        self.assertEqual(result.state, "lost")

    def test_a_notice_naming_more_platforms_than_the_page_keeps_what_it_knows(self):
        # Athy's notice names 1 and 2; the page has a lift at 2 and calls 1 level.
        # Platform 2 is still knowable and must not be forfeited with platform 1.
        result = model.verdict(
            station("ATHY"), "lift", "Lifts at platforms 1 and 2 are currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))
        self.assertIn("also names platform 1", result.detail)

    def test_skerries_the_same_way(self):
        result = model.verdict(
            station("SKRES"),
            "lift",
            "The lifts at platforms  1 and 2 are currently out of service.",
        )
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))


class TheTwoExceptions(unittest.TestCase):
    """The only stations whose own prose names a step-free way round a lift."""

    def test_raheny_platform_one_has_a_ramp(self):
        result = model.verdict(
            station("RAHNY"), "lift", "The lift at platform 1 is currently out of service."
        )
        self.assertEqual(result.state, "alternative")
        self.assertIn("ramp", result.detail.lower())

    def test_cork_has_a_ramp_to_the_high_platforms(self):
        result = model.verdict(
            station("CORK"), "lift", "The lift to platform 5A and 5B is out of service."
        )
        self.assertEqual(result.state, "alternative")

    def test_the_list_is_the_only_way_to_reach_that_verdict(self):
        # Nothing outside STEP_FREE_ALTERNATIVES may ever say access remains.
        for code in ("HZLCH", "BBRHY", "MHIDE", "SKRES", "CLDKN", "ATHY", "ADMTN", "DCKLS"):
            result = model.verdict(station(code), "lift", "The lift is out of service.")
            self.assertNotEqual(result.state, "alternative", code)

    def test_every_entry_names_a_station_and_platform(self):
        for code, platform in model.STEP_FREE_ALTERNATIVES:
            self.assertTrue(code.isupper() and platform)


class ASummarySentenceIsNotAPerPlatformClaim(unittest.TestCase):
    """Specific beats general, or a summary line swallows the whole station."""

    def test_pearse_does_not_put_a_lift_on_the_ramp_platform(self):
        # "Via ramps, stairs, escalators, and lifts." names a lift and no
        # platform. Counted as covering everything, it makes the page's own
        # "Ramp to platform 1" a lift platform and reports it as access lost.
        self.assertEqual(station("PERSE").lift_platforms, frozenset({"2"}))

    def test_the_ramp_platform_is_a_disagreement_not_a_loss(self):
        result = model.verdict(
            station("PERSE"), "lift", "The lift at platform 1 is currently out of service."
        )
        self.assertEqual(result.state, "unknown")
        self.assertIn("does not list a lift at", result.detail)

    def test_the_lift_platform_still_reads_as_lost(self):
        result = model.verdict(
            station("PERSE"), "lift", "The lift at platform 2 is currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))

    def test_a_station_that_names_no_platform_still_means_all_of_them(self):
        for code in ("BBRHY", "DCKLS", "CLDKN"):
            self.assertEqual(station(code).lift_platforms, frozenset({model.ALL_PLATFORMS}), code)


class AReviewedEntryExpiresWithThePageItQuotes(unittest.TestCase):
    """The station pages are refetched monthly because they get reworded."""

    def test_the_quoted_sentence_is_what_keeps_the_entry_alive(self):
        live = model.verdict(
            station("RAHNY"), "lift", "The lift at platform 1 is out of service."
        )
        self.assertEqual(live.state, "alternative")

    def test_a_reworded_page_withdraws_the_claim(self):
        # The ramp is removed during works and the page is rewritten. Saying
        # "another step-free way remains" on a sentence that has been deleted is
        # the one error this module exists to prevent.
        reworded = station("RAHNY")._replace(
            platform_access="Lift to platform 1\nRamp to platform 2"
        )
        result = model.verdict(reworded, "lift", "The lift at platform 1 is out of service.")
        self.assertEqual(result.state, "unknown")
        self.assertIn("no longer on Irish Rail's page", result.detail)

    def test_a_stale_entry_forfeits_its_own_platform_and_no_others(self):
        # Cork has entries for 5A, 5B and 6. A reworded page must not take
        # platform 7 down with them: 7 has no entry, is lift-served, and is lost.
        cork = model.Station(
            "CORK", "Cork (Kent)", "cork", None, None,
            "Platforms 1, 2, 3 and 4 are level\nLift to platform 5A, 5B, 6 and 7", "",
            frozenset({"5A", "5B", "6", "7"}), True, False,
        )
        result = model.verdict(cork, "lift", "The lift at platform 5A and 7 is out of service.")
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("7",))
        self.assertIn("needs reviewing again", result.detail)

    def test_a_stale_entry_alone_is_still_unknown(self):
        reworded = station("RAHNY")._replace(platform_access="Lift to platform 1")
        result = model.verdict(reworded, "lift", "The lift at platform 1 is out.")
        self.assertEqual(result.state, "unknown")

    def test_it_does_not_quietly_become_a_loss_instead(self):
        # "unknown" and not "lost": the review said there was a way round, and a
        # reworded page is not evidence that there is not.
        reworded = station("RAHNY")._replace(platform_access="Lift to platform 1")
        self.assertNotEqual(
            model.verdict(reworded, "lift", "The lift at platform 1 is out.").state, "lost"
        )

    def test_every_entry_still_matches_the_prose_it_quotes(self):
        # Fixture-level guard; tests/test_site_real.py checks the live snapshot.
        for (code, _), quoted in model.STEP_FREE_ALTERNATIVES.items():
            if code in PROSE:
                self.assertIn(quoted, " ".join(model.plain(PROSE[code]).split()), code)


class SentenceScopedPatternsStayOnOneLine(unittest.TestCase):
    """`[^.]` is a class holding one literal dot, so it matches newlines too."""

    def test_a_notice_does_not_borrow_a_platform_from_another_line(self):
        # plain() turns the <br> the feed puts in `text` into a newline.
        self.assertEqual(
            model.affected_platforms(
                "The lift is currently out of service<br>Trains depart from platform 3"
            ),
            (),
        )

    def test_it_still_reads_a_platform_in_the_same_sentence(self):
        self.assertEqual(
            model.affected_platforms("The lift at platform 2 is out of service."), ("2",)
        )

    def test_boilerplate_cannot_swallow_the_line_after_it(self):
        prose = (
            "<p>To access the lift, you must call via the help point<br>"
            "Level to platform 1<br>Lift to platform 2</p>"
        )
        self.assertIn("Level to platform 1", model.segments(prose))

    def test_a_platform_range_is_not_read_as_its_endpoints(self):
        # "1 to 4" as (1, 4) drops the two in the middle and would report them
        # as lift-free. Under-reading sends them to `unknown`, which is safe;
        # expanding the range would be inventing platform numbers.
        self.assertEqual(model.platforms_named("Lift to platforms 1 to 4"), ("1",))

    def test_the_separators_that_are_really_used_still_work(self):
        self.assertEqual(
            model.platforms_named("Ramp or lift to platform 5A, 5B and 6"), ("5A", "5B", "6")
        )
        self.assertEqual(
            model.platforms_named("Ramp access from Platform 2 to Platform 3"), ("2", "3")
        )


class WhenItCannotTell(unittest.TestCase):
    def assert_unknown(self, code, text):
        result = model.verdict(station(code), "lift", text)
        self.assertEqual(result.state, "unknown", f"{code}: {result.detail}")
        return result

    def test_limerick_junction_says_level_but_has_a_lift_notice(self):
        self.assert_unknown(
            "LMRKJ", "The lifts at platform 1 and 4 are temporarily unavailable."
        )

    def test_rush_and_lusk_lists_platform_one_twice(self):
        result = self.assert_unknown(
            "RLUSK", "The lift on platform 2 is currently out of service."
        )
        self.assertIn("platform 2", result.detail)

    def test_portlaoise_puts_the_lift_at_the_other_platform(self):
        self.assert_unknown("PTLSE", "The lift on platform 2 is currently out of service.")

    def test_a_station_with_no_prose_at_all(self):
        self.assert_unknown("BLANK", "The lift is currently out of service.")

    def test_a_station_missing_from_the_snapshot(self):
        result = model.verdict(None, "lift", "The lift is out of service.")
        self.assertEqual(result.state, "unknown")


class TheLiftCallSentenceIsBoilerplate(unittest.TestCase):
    """Template text that mentions a lift is not a claim that one exists."""

    def test_stations_whose_only_lift_is_the_template(self):
        for code in ("GSTNS", "KILNY", "DBATE"):
            self.assertEqual(model.has_lift(station(code)), "no", code)

    def test_dromod_says_outright_that_it_has_none(self):
        self.assertEqual(model.has_lift(station("DRMOD")), "no")
        self.assertTrue(station("DRMOD").denies_lift)

    def test_the_real_claim_survives_the_stripping(self):
        for code in ("MHIDE", "SKRES", "RAHNY", "RLUSK"):
            self.assertEqual(model.has_lift(station(code)), "yes", code)

    def test_irish_rails_page_is_the_only_source(self):
        # OpenStreetMap was carried here as a second opinion and removed once it
        # was measured. notes/station-access.md says what it can and cannot do,
        # so this is a reminder rather than a bare assertion about an argument.
        self.assertEqual(model.has_lift.__code__.co_argcount, 1)

    def test_greystones_keeps_its_footbridge_sentence(self):
        self.assertIn("Footbridge only to platform 2", station("GSTNS").platform_access)


class ReadingThePlatformNumbers(unittest.TestCase):
    def test_the_forms_the_feed_actually_uses(self):
        cases = {
            "The lift at platform 2 is out.": ("2",),
            "The lift on platform 1 is out.": ("1",),
            "The lift to Platform 2 and 3 is out.": ("2", "3"),
            "The lifts at platforms 1 and 2 are out.": ("1", "2"),
            "The lifts at platforms  1 and 2 are out.": ("1", "2"),
            "The lifts at platform 1 and 4 are out.": ("1", "4"),
            "The lift on platform 2 at Portarlington is out.": ("2",),
            "The lifts at Malahide Station are out.": (),
            "The lift is currently out of service.": (),
            "Lifts are temporarily unavailable due to planned works.": (),
        }
        for text, expected in cases.items():
            self.assertEqual(model.affected_platforms(text), expected, text)

    def test_the_forms_the_station_pages_use(self):
        self.assertEqual(model.platforms_named("Ramp to platform No.1"), ("1",))
        self.assertEqual(
            model.platforms_named("Steps or lift and subway to platforms No. 2 and 3"), ("2", "3")
        )
        self.assertEqual(
            model.platforms_named("Ramp or lift to platform 5A, 5B and 6"), ("5A", "5B", "6")
        )
        self.assertEqual(
            model.platforms_named("Level to platform 1, 2 & 3"), ("1", "2", "3")
        )

    def test_a_lift_segment_with_no_number_covers_the_station(self):
        self.assertIn(model.ALL_PLATFORMS, station("BBRHY").lift_platforms)
        self.assertIn(model.ALL_PLATFORMS, station("DCKLS").lift_platforms)

    def test_a_lift_segment_with_numbers_covers_only_those(self):
        self.assertEqual(station("ATHY").lift_platforms, frozenset({"2"}))
        self.assertEqual(station("MHIDE").lift_platforms, frozenset({"2"}))


class EscalatorsAreNotStepFree(unittest.TestCase):
    """What is deduced, and what is not claimed.

    The deduction is sound and narrow: an escalator has steps, so it was never a
    step-free route, so its going out cannot remove one. What does not follow is
    that the station still *has* step-free access - that is a claim about the
    station, needs the station's own prose, and was being published for every
    escalator outage without anything behind it. Connolly's page does not mention
    an escalator at all.
    """

    def test_it_states_the_deduction_about_the_escalator(self):
        result = model.verdict(
            station("HZLCH"), "escalator", "The escalator at platform 2 is unavailable."
        )
        self.assertEqual(result.state, "escalator")
        self.assertIn("was not a step-free route to begin with", result.detail)

    def test_it_does_not_claim_the_station_still_has_step_free_access(self):
        result = model.verdict(
            station("HZLCH"), "escalator", "The escalator at platform 2 is unavailable."
        )
        for overclaim in ("step-free access unaffected", "access remains", "still step-free"):
            self.assertNotIn(overclaim, result.detail.lower())

    def test_connollys_escalator_is_found_on_the_other_leg(self):
        # It is named in ticketOfficeAccess and nowhere else. Checking only
        # platformAccess published "the page does not mention an escalator" at
        # the one station where that line rendered, and it was false.
        result = model.verdict(
            station("CNLLY"), "escalator", "The Escalator at the main concourse is out."
        )
        self.assertNotIn("does not mention an escalator", result.detail)

    def test_it_still_says_so_when_neither_leg_names_one(self):
        result = model.verdict(
            station("ATHY"), "escalator", "The escalator is out of service."
        )
        self.assertIn("does not mention an escalator", result.detail)

    def test_it_stays_quiet_when_the_page_does_mention_one(self):
        result = model.verdict(
            station("PERSE"), "escalator", "The escalator at platform 2 is unavailable."
        )
        self.assertNotIn("does not mention an escalator", result.detail)

    def test_it_still_reports_the_platform(self):
        result = model.verdict(
            station("HZLCH"), "escalator", "The escalator at platform 2 is unavailable."
        )
        self.assertEqual(result.platforms, ("2",))


class TheHeadIsHandWrittenAndMayBeWrong(unittest.TestCase):
    """The whole escalator deduction rests on the word meaning what it says."""

    def test_an_escalator_head_naming_only_a_lift_is_not_deduced_about(self):
        result = model.verdict(
            station("PERSE"), "escalator", "The lift at platform 2 is currently out of service."
        )
        self.assertEqual(result.state, "unknown")
        self.assertIn("names the other machine", result.detail)

    def test_a_lift_head_naming_only_an_escalator_is_not_either(self):
        result = model.verdict(
            station("ATHY"), "lift", "The escalator at platform 2 is out of service."
        )
        self.assertEqual(result.state, "unknown")

    def test_both_machines_out_is_still_a_lost_lift(self):
        # The worst case for a reader must not become the least informative
        # verdict. Whatever else broke, the lift is out, so the platform is lost.
        result = model.verdict(
            station("ATHY"), "lift", "The lift and escalator at platform 2 are out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))

    def test_both_machines_out_withdraws_the_escalator_deduction(self):
        # "An escalator was never step-free" is no comfort if a lift went too.
        result = model.verdict(
            station("PERSE"), "escalator", "The lift and escalator at platform 2 are out."
        )
        self.assertEqual(result.state, "unknown")

    def test_an_agreeing_notice_is_unaffected(self):
        self.assertEqual(
            model.verdict(station("ATHY"), "lift", "The lift at platform 2 is out.").state, "lost"
        )


if __name__ == "__main__":
    unittest.main()
