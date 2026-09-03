"""What a station has, and what a notice means, on the real published prose.

Every fixture below is the `platformAccess` HTML Irish Rail was serving on
2026-08-30, and every notice text is one the collector actually recorded. The
point of the file is the first class: "lifts and ramps" at Hazelhatch must read
as a sequence you need all of, not a choice between two, because reading it the
other way tells a wheelchair user access remains at a station where it is gone.
"""

from __future__ import annotations

import re
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
    "DLERY": (
        "<p>Lift to Platforms 1 &amp; 2</p>\n"
        "<p>Level to Platform 3. Ramp access from Platform 2 to Platform 3.</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft. Please see lift call operation page for steps to call the lift.</p>"
    ),
    # A general lift claim beside a level line: two claims that disagree.
    "BRAY": (
        "<p>Level to platform 1, 2 &amp; 3</p>\n"
        "<p>Use the lift or stairs to travel between platforms</p>\n"
        "<p>To access the lift, you must call via the help point at each landing of the "
        "lift shaft. Please see lift call operation page for steps to call the lift.</p>"
    ),
    "BLANK": "",
}

NAMES = {"HZLCH": "Hazelhatch and Celbridge", "LMRKJ": "Limerick Junction"}

# ticketOfficeAccess: the street-to-concourse leg, a separate field. Connolly's
# escalator is named here and nowhere else. Four of 152 pages put a lift on this
# leg; three of them are here. A station absent from this dict has a blank one.
ENTRY = {
    "CNLLY": "<p>Escalator, lift or stairs from Amiens Street and from LUAS stop.<br>"
    "Level access from car park.</p>",
    "PERSE": "<p>Level, through main entrance to the booking hall</p>",
    "DCKLS": "<p>Lift to ticket office</p>",
    "CLDKN": "<p>Level or via lift</p>",
    "ATHY": "<p>Level from station entrance and concourse</p>",
}
# Grand Canal Dock's names a platform on its way to naming the lift; Kilcoole's
# is the two words that would read as level to a filter that only looks for it.
GCDK_ENTRY = "Through main entrance building into the booking hall on platform 2 via stairs or lift"
KCOOL_ENTRY = "Not level"


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


class TheOtherPlatformKeptStepFreeAccess(unittest.TestCase):
    """A *different* platform never needed the lift, and it must read as one:
    the wording never borrows STEP_FREE_ALTERNATIVES'. Issue #31.
    """

    def test_malahide_platform_one_was_level_throughout(self):
        result = model.verdict(
            station("MHIDE"), "lift", "The lift at platform 2 is currently out of service."
        )
        self.assertEqual(result.state, "lost")
        # The parenthetical is quoted, not read: direction stayed out of scope.
        self.assertIn(
            'Platform 1 needed no lift, so it kept step-free access: '
            '"Level to platform 1 (City Centre)".',
            result.detail,
        )
        self.assertNotIn("another step-free way", result.detail)

    def test_connolly_keeps_the_four_level_platforms_in_one_plural_sentence(self):
        result = model.verdict(
            station("CNLLY"), "lift", "The lift to platforms 6 and 7 is out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertIn(
            'Platforms 1, 2, 3 and 4 needed no lift, so they kept step-free access: '
            '"Level access to platforms 1, 2, 3 and 4 from ticket office".',
            result.detail,
        )

    def test_corks_predicate_form_counts(self):
        # An anchored "Level to" would lose the predicate form.
        self.assertEqual(
            model.step_free_platforms(station("CORK")),
            tuple((p, "Platforms 1, 2, 3 and 4 are level") for p in ("1", "2", "3", "4")),
        )

    def test_dun_laoghaire_quotes_the_level_sentence_not_the_link_between_platforms(self):
        result = model.verdict(
            station("DLERY"), "lift", "The lift at platform 1 is currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertIn('kept step-free access: "Level to Platform 3".', result.detail)
        # A between-platforms link says nothing about the street leg.
        self.assertNotIn("Ramp access", result.detail)

    def test_every_quote_is_a_verbatim_substring_of_the_prose(self):
        for code in ("MHIDE", "CNLLY", "CORK", "DLERY", "PERSE"):
            for _platform, sentence in model.step_free_platforms(station(code)):
                self.assertIn(sentence, station(code).platform_access, code)

    def test_rush_and_lusks_typo_neutralizes_itself(self):
        # "Level access to platform 1" sits beside "Lift and footbridge to
        # platform 1", and a lift-served platform never gets the note.
        result = model.verdict(
            station("RLUSK"), "lift", "The lift on platform 1 is currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertNotIn("kept step-free access", result.detail)

    def test_a_notice_naming_the_level_platform_silences_the_note(self):
        # Athy's notice names 1 and 2; the page calls 1 level. Don't pick a side.
        result = model.verdict(
            station("ATHY"), "lift", "Lifts at platforms 1 and 2 are currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertNotIn("kept step-free access", result.detail)

    def test_a_general_lift_claim_beside_a_level_line_gets_no_note(self):
        result = model.verdict(
            station("BRAY"), "lift", "The lift at platform 4 is currently out of service."
        )
        self.assertEqual(result.state, "lost")
        self.assertNotIn("kept step-free access", result.detail)

    def test_the_sentences_that_must_not_qualify(self):
        # A sequence, two with no platform number, and one with steps in it.
        for code in ("HZLCH", "LMRKJ", "DRMOD", "ADMTN", "CLDKN"):
            self.assertEqual(model.step_free_platforms(station(code)), (), code)

    def test_reworded_prose_with_steps_in_it_never_qualifies(self):
        # The pages are reworded a few times a year, and the singular step is
        # real prose today (Tipperary: "Low step via wicket gate from car park").
        for prose in (
            "Ramp with one step to platform 1",
            "Level access via the staircase to platform 1",
            "Stairway and ramp to platform 2",
        ):
            reworded = station("ATHY")._replace(platform_access=prose)
            self.assertEqual(model.step_free_platforms(reworded), (), prose)

    def test_only_a_lost_verdict_carries_the_note(self):
        cases = (
            ("RAHNY", "lift", "The lift at platform 1 is out of service."),
            ("PTLSE", "lift", "The lift on platform 2 is currently out of service."),
            ("PERSE", "escalator", "The escalator at platform 2 is unavailable."),
        )
        for code, kind, text in cases:
            result = model.verdict(station(code), kind, text)
            self.assertNotEqual(result.state, "lost", code)
            self.assertNotIn("kept step-free access", result.detail, code)

    def test_a_reworded_page_drops_the_note(self):
        reworded = station("MHIDE")._replace(
            platform_access="Lift and footbridge to platform 2"
        )
        result = model.verdict(reworded, "lift", "The lift at platform 2 is out of service.")
        self.assertEqual(result.state, "lost")
        self.assertNotIn("kept step-free access", result.detail)


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

    def test_a_stale_entry_still_reports_the_platforms_the_page_omits(self):
        # Two separate reasons to distrust the reading, and the reader is owed
        # both: the "lost" path says so and the stale-only path used to drop it.
        reworded = station("RAHNY")._replace(platform_access="Lift to platform 1")
        result = model.verdict(reworded, "lift", "The lift at platform 1 and 3 is out.")
        self.assertEqual(result.state, "unknown")
        self.assertIn("needs reviewing again", result.detail)
        self.assertIn("does not list a lift at", result.detail)

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

    def test_a_block_tag_with_attributes_still_breaks_the_line(self):
        # A CMS paste gives <br class="x">, which missed the block pattern and
        # was stripped as an ordinary tag, joining two access lines. The merged
        # segment names a lift and platforms 1 and 2, so platform 1 becomes
        # lift-served and its notice reads "reached by lift" on a ramp platform:
        # the false specific that specific-beats-general exists to prevent.
        merged = '<p>Ramp to platform 1<br class="sep">\nLift to platform 2</p>'
        self.assertEqual(
            model.segments(merged), ["Ramp to platform 1", "Lift to platform 2"]
        )
        self.assertEqual(model.read_platform_access(merged)[0], frozenset({"2"}))

    def test_a_styled_paragraph_is_still_a_paragraph(self):
        self.assertEqual(
            model.segments('<p style="a">Level to platform 1</p><p style="b">Lift to 2</p>'),
            ["Level to platform 1", "Lift to 2"],
        )

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
        for overclaim in FORBIDDEN:
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


class TellingPeopleWhatToUseInsteadIsNotASecondFailure(unittest.TestCase):
    """The forfeit above must not fire on the wording that states things clearest.

    "The escalator is out of service. Please use the lift" names both machines
    and says outright what broke. Reading the second sentence as a second outage
    forfeits exactly the notices that need no forfeiting.
    """

    def test_an_escalator_notice_may_point_at_the_lift(self):
        result = model.verdict(
            station("PERSE"),
            "escalator",
            "The escalator at platform 2 is out of service. Please use the lift.",
        )
        self.assertEqual(result.state, "escalator")
        self.assertEqual(result.platforms, ("2",))

    def test_a_lift_notice_may_point_at_the_escalator(self):
        result = model.verdict(
            station("ATHY"),
            "lift",
            "The lift at platform 2 is out of order. Customers should use the escalator.",
        )
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))

    def test_a_sentence_that_says_both_is_still_a_forfeit(self):
        # One sentence carrying an instruction and an outage names two machines
        # and cannot be told apart, so it keeps the old answer.
        result = model.verdict(
            station("PERSE"),
            "escalator",
            "Please use the stairs as the lift and escalator are out of service.",
        )
        self.assertEqual(result.state, "unknown")

    def test_the_second_sentence_may_still_report_a_second_outage(self):
        result = model.verdict(
            station("PERSE"),
            "escalator",
            "The escalator is out of service. The lift is also out of order.",
        )
        self.assertEqual(result.state, "unknown")


FORBIDDEN = ("access remains", "still step-free", "step-free access unaffected", "still had",
             "remains", "was working", "available", "unaffected")


class WhichLegANoticeNames(unittest.TestCase):
    """Read from the notice's own text, and a platform wins over an entrance word."""

    def test_a_platform_number_is_the_platform_leg(self):
        self.assertEqual(model.leg_named("The lift at platform 2 is out."), "platform")

    def test_the_bare_word_platform_is_too(self):
        self.assertEqual(model.leg_named("The lifts at the platforms are out."), "platform")

    def test_the_main_concourse_is_the_entrance_leg(self):
        self.assertEqual(
            model.leg_named("The Escalator at the main concourse is currently out of service."),
            "entrance",
        )

    def test_a_platform_wins_over_an_entrance_word(self):
        # platformAccess starts at the ticket office, so anything on the way
        # to a platform is that field's leg whatever else the sentence names.
        self.assertEqual(
            model.leg_named("The lift from the concourse to platform 2 is out."), "platform"
        )

    def test_the_forms_the_feed_uses_for_the_entrance(self):
        for text in ("lift at the station entrance", "lift to the ticket office",
                     "lift to the booking hall", "lift from the car park"):
            self.assertEqual(model.leg_named(text), "entrance", text)

    def test_a_station_name_locates_nothing(self):
        self.assertIsNone(model.leg_named("The lifts at Malahide Station are out of service."))

    def test_no_location_is_none(self):
        self.assertIsNone(model.leg_named("Lifts are temporarily unavailable."))
        self.assertIsNone(model.leg_named(""))
        self.assertIsNone(model.leg_named(None))

    def test_clonsillas_p2_is_not_read_as_a_platform(self):
        # The abbreviation is outside PLATFORM_RUN and AFFECTED alike; the notice
        # falls to unlocated, which keeps today's reading.
        self.assertIsNone(model.leg_named("The lift on P2 is out of service currently."))

    def test_every_verdict_carries_the_leg(self):
        cases = (
            ("PERSE", "lift", "The lift at platform 2 is out.", "platform"),
            ("CNLLY", "lift", "The lift at the main concourse is out.", "entrance"),
            ("DCKLS", "lift", "The lift is currently out of service.", None),
            ("CNLLY", "escalator", "The Escalator at the main concourse is out.", "entrance"),
            ("PERSE", "escalator", "The escalator at platform 2 is out.", "platform"),
            ("HZLCH", "escalator", "The escalator is out.", None),
        )
        for code, kind, text, leg in cases:
            self.assertEqual(model.verdict(station(code), kind, text).leg, leg, text)
        missing = model.verdict(None, "lift", "The lift at the entrance is out.")
        self.assertEqual(missing.leg, "entrance")


class ALiftOnTheWayIn(unittest.TestCase):
    """A lift notice that names the way in is read against ticketOfficeAccess."""

    TEXT = "The lift at the main concourse is currently out of service."

    def test_connolly_loses_step_free_access_into_the_station(self):
        result = model.verdict(station("CNLLY"), "lift", self.TEXT)
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.leg, "entrance")
        self.assertEqual(result.platforms, ())
        self.assertIn(
            'puts a lift there too: "Escalator, lift or stairs from Amiens Street and from '
            'LUAS stop", so step-free access into the station was gone',
            result.detail,
        )

    def test_connolly_also_names_the_level_way_from_the_car_park(self):
        result = model.verdict(station("CNLLY"), "lift", self.TEXT)
        self.assertIn(
            'also names a way in that needed no lift: "Level access from car park".',
            result.detail,
        )

    def test_the_entrance_note_is_not_the_platform_note(self):
        # test_the_kept_platform_note_never_overclaims keys on that phrase and
        # reads it against lift_platforms, which Docklands has as "*".
        for code in ("CNLLY", "DCKLS"):
            result = model.verdict(station(code), "lift", self.TEXT)
            self.assertNotIn("kept step-free access", result.detail, code)

    def test_docklands_has_no_level_way_in_to_name(self):
        result = model.verdict(station("DCKLS"), "lift", "The lift to the ticket office is out.")
        self.assertEqual((result.state, result.leg), ("lost", "entrance"))
        self.assertIn('"Lift to ticket office"', result.detail)
        self.assertNotIn("needed no lift", result.detail)

    def test_grand_canal_docks_sentence_names_a_platform_and_still_counts(self):
        gcdk = station("HZLCH")._replace(ticket_office_access=GCDK_ENTRY)
        result = model.verdict(gcdk, "lift", "The lift to the booking hall is out.")
        self.assertEqual(result.state, "lost")
        self.assertIn(f'"{GCDK_ENTRY}"', result.detail)

    def test_level_or_via_lift_is_read_as_a_sequence(self):
        # The module does not parse connectives; Clondalkin's "or" gets the
        # Hazelhatch reading, and the quote shows a reader the page's words.
        result = model.verdict(station("CLDKN"), "lift", "The lift at the entrance is out.")
        self.assertEqual(result.state, "lost")
        self.assertIn('"Level or via lift"', result.detail)

    def test_a_page_with_no_entrance_lift_is_unknown(self):
        result = model.verdict(station("ATHY"), "lift", "The lift at the entrance is out.")
        self.assertEqual((result.state, result.leg), ("unknown", "entrance"))
        self.assertIn("names no lift on the way in", result.detail)

    def test_an_entrance_lift_named_on_the_platform_side_is_still_an_entrance_lift(self):
        # Pearse's way-in field names no lift; its platformAccess names lifts
        # from the Pearse Street entrance. The page must not be reported as
        # naming none, and the notice must not be read on the platform leg,
        # which published the ramp platform as kept from a booking hall this
        # lift may be the way to.
        result = model.verdict(
            station("PERSE"), "lift", "The lift from the Pearse Street entrance is out."
        )
        self.assertEqual((result.state, result.leg, result.platforms), ("lost", "entrance", ()))
        self.assertIn('"Lifts/stairs/Escalators from the Pearse Street entrance"', result.detail)
        self.assertIn("step-free access into the station was gone", result.detail)
        self.assertNotIn("kept step-free access", result.detail)
        self.assertNotIn("names no lift", result.detail)
        self.assertTrue(model.entrance_lift(station("PERSE")))

    def test_a_blank_entrance_field_is_unknown(self):
        result = model.verdict(station("HZLCH"), "lift", "The lift at the entrance is out.")
        self.assertEqual(result.state, "unknown")
        self.assertIn("says nothing about the way in", result.detail)

    def test_it_is_read_before_the_platform_lift_claim(self):
        # Greystones claims no lift to the platforms; a page that did put one on
        # the way in must not fall into "does not mention a lift".
        gstns = station("GSTNS")._replace(ticket_office_access="Lift to ticket office")
        result = model.verdict(gstns, "lift", "The lift at the entrance is out.")
        self.assertEqual(result.state, "lost")

    def test_not_level_is_never_quoted_as_a_level_way_in(self):
        for negated in (KCOOL_ENTRY, "No level access", "No ramp", "Level access not available"):
            kcool = station("DCKLS")._replace(
                ticket_office_access="Lift to ticket office\n" + negated
            )
            self.assertIsNone(model.entrance_step_free(kcool), negated)
            result = model.verdict(kcool, "lift", self.TEXT)
            self.assertNotIn("needed no lift", result.detail, negated)

    def test_a_numbered_platform_is_not_a_negation(self):
        # Carrigaloe and Dalkey write the label without a dot; Athlone with one,
        # which the sentence splitter must not take for a full stop.
        for sentence in ("Ramp to platform No 1 (for northbound routes and city centre)",
                         "Via the main gate (top of ramp) to platform No 2 (Northbound)",
                         "Level to platforms No. 2 and 3"):
            self.assertEqual(model._sentences(sentence), [sentence])
            self.assertEqual(model._level_sentences(sentence), (sentence,))
        self.assertEqual(model._sentences("Ramp to platform 1. No lift to platform 2."),
                         ["Ramp to platform 1", "No lift to platform 2"])
        # Only the label: a word that happens to end in "no." still ends a sentence.
        self.assertEqual(model._sentences("Access via the casino. Lift to platform 2."),
                         ["Access via the casino", "Lift to platform 2"])

    def test_a_concourse_lift_the_page_puts_on_the_platform_leg_is_read_there(self):
        # The page's own sentence names the platform, so the platform reading
        # is the right one: platform 2 lost, platform 1 kept.
        prose = "Level to platform 1\nLift from the concourse to platform 2"
        lift_platforms, claims, denies = model.read_platform_access(prose)
        st = station("ATHY")._replace(
            platform_access=prose, lift_platforms=lift_platforms,
            claims_lift=claims, denies_lift=denies,
        )
        self.assertIsNone(model.entrance_lift_sentence(st))
        result = model.verdict(st, "lift", "The lift at the concourse is out of service.")
        self.assertEqual((result.state, result.leg, result.platforms), ("lost", "entrance", ("2",)))
        self.assertIn("Platform 2 is reached by lift", result.detail)
        # Pearse's entrance sentence names no platform and stays an entrance lift.
        self.assertIsNotNone(model.entrance_lift_sentence(station("PERSE")))

    def test_the_lift_call_boilerplate_is_not_an_entrance_lift(self):
        boiler = station("ATHY")._replace(
            ticket_office_access=model.plain(PROSE["KILNY"])
        )
        self.assertFalse(model.entrance_lift(boiler))
        self.assertEqual(model.verdict(boiler, "lift", self.TEXT).state, "unknown")

    def test_an_unlocated_lift_notice_keeps_the_platform_reading(self):
        result = model.verdict(station("DCKLS"), "lift", "The lift is currently out of service.")
        self.assertEqual((result.state, result.leg), ("lost", None))
        self.assertIn("no platform had step-free access", result.detail)

    def test_a_missing_station_is_still_unknown(self):
        result = model.verdict(None, "lift", self.TEXT)
        self.assertEqual(result.state, "unknown")
        self.assertIn("not in the station snapshot", result.detail)

    def test_the_flag_changes_nothing_for_a_lift_notice(self):
        for text in (self.TEXT, "The lift at platform 6 is out."):
            plain = model.verdict(station("CNLLY"), "lift", text)
            flagged = model.verdict(station("CNLLY"), "lift", text, lift_listed_too=True)
            self.assertEqual(plain, flagged)


class WhoAnEscalatorOutageAffected(unittest.TestCase):
    """The deduction says who lost nothing; the rest says who did, and what the
    page puts on the same leg. Issue #33."""

    def verdict(self, code, text, **kw):
        result = model.verdict(station(code), "escalator", text, **kw)
        self.assertEqual(result.state, "escalator")
        return result

    def test_it_names_the_people_who_lost_a_way_up(self):
        result = self.verdict("PERSE", "The escalator at platform 2 is unavailable.")
        self.assertIn("was not a step-free route to begin with", result.detail)
        self.assertIn("a buggy, a suitcase or a stick, did lose a way up.", result.detail)

    def test_pearse_quotes_the_platform_two_lift_line_not_the_summary(self):
        result = self.verdict("PERSE", "The escalator at platform 2 is unavailable.")
        self.assertIn(
            'puts a lift on the way to platform 2 as well: "Lift or stairs to platform 2 '
            '(southbound)".',
            result.detail,
        )
        self.assertNotIn("Via ramps", result.detail)

    def test_a_general_lift_line_is_quoted_where_the_page_names_no_platform(self):
        result = self.verdict("HZLCH", "The escalator at platform 2 is unavailable.")
        self.assertIn('"All platforms can be accessed via lifts and ramps"', result.detail)

    def test_connolly_reads_the_entrance_leg(self):
        result = self.verdict("CNLLY", "The Escalator at the main concourse is out.")
        self.assertEqual(result.leg, "entrance")
        self.assertIn(
            'on the way into the station as well: "Escalator, lift or stairs from Amiens '
            'Street and from LUAS stop".',
            result.detail,
        )
        self.assertIn('a level way into the station: "Level access from car park".', result.detail)
        # Its platform lift is on the other leg and says nothing about the way in.
        self.assertNotIn("platforms 6 and 7", result.detail)

    def test_a_level_platform_with_an_escalator_is_a_disagreement(self):
        # A level platform has no level change for an escalator to make, so the
        # page's level line is not quoted as a way round; the sources disagree.
        result = self.verdict("ATHY", "The escalator at platform 1 is out.")
        self.assertIn(
            'calls platform 1 level: "Level to platform 1", so the notice and the page '
            "disagree about it.",
            result.detail,
        )
        self.assertNotIn("puts a lift", result.detail)
        self.assertNotIn("names a level way", result.detail)

    def test_a_general_lift_claim_is_not_put_on_the_way_to_a_level_platform(self):
        # Bray: "Level to platform 1, 2 & 3" beside "Use the lift or stairs to
        # travel between platforms". The disagreement is what gets said.
        result = self.verdict("BRAY", "The escalator at platform 1 is out of service.")
        self.assertNotIn("puts a lift", result.detail)
        self.assertIn('calls platform 1 level: "Level to platform 1, 2 & 3"', result.detail)
        # And with no platform named, the general claim stands as a general claim.
        bare = self.verdict("BRAY", "The escalator at the platforms is out of service.")
        self.assertIn("puts a lift on the way to the platforms as well", bare.detail)

    def test_the_lift_phrase_names_the_platforms_the_sentence_puts_a_lift_at(self):
        result = self.verdict("ATHY", "The escalators at platforms 1 and 2 are out.")
        self.assertIn('puts a lift on the way to platform 2 as well: "Lift to platform 2".',
                      result.detail)
        self.assertNotIn("platforms 1 and 2 as well", result.detail)
        # Both facts stand: the lift to 2 and the disagreement about 1.
        self.assertIn("calls platform 1 level", result.detail)
        bare = self.verdict("PERSE", "The escalator to the platforms is out.")
        self.assertIn("puts a lift on the way to platform 2 as well", bare.detail)
        general = self.verdict("HZLCH", "The escalators at platforms 1 and 2 are out.")
        self.assertIn("puts a lift on the way to platforms 1 and 2 as well", general.detail)

    def test_pearses_entrance_lift_is_found_on_the_platform_side_of_the_page(self):
        result = self.verdict("PERSE", "The escalator at the Pearse Street entrance is out.")
        self.assertEqual(result.leg, "entrance")
        self.assertIn(
            'on the way into the station as well: "Lifts/stairs/Escalators from the Pearse '
            'Street entrance".',
            result.detail,
        )

    def test_a_station_that_claims_no_lift_says_so(self):
        result = self.verdict("DRMOD", "The escalator at platform 2 is out.")
        self.assertIn(
            f"names no lift at {station('DRMOD').name} and no level way to platform 2, "
            "so nothing on it says there was another way up.",
            result.detail,
        )
        self.assertNotIn("(no lift at this station)", result.detail)

    def test_a_lift_platform_with_neither_says_the_page_is_silent(self):
        result = self.verdict("ATHY", "The escalator at platform 3 is out.")
        self.assertIn("names no lift or level way to platform 3", result.detail)

    def test_an_unlocated_escalator_says_the_notice_does_not_say_where(self):
        result = self.verdict("HZLCH", "The escalator is out of service.")
        self.assertIsNone(result.leg)
        self.assertIn("does not say where the escalator is", result.detail)
        self.assertNotIn("puts a lift", result.detail)

    def test_every_named_platform_is_accounted_for(self):
        # Greystones: platform 1 level, platform 2 footbridge only, no lift
        # claimed. A notice naming both must not go quiet about platform 2
        # because platform 1 had something to say.
        result = self.verdict("GSTNS", "The escalators at platforms 1 and 2 are out.")
        self.assertIn('calls platform 1 level: "Level to platform 1 (northbound)"', result.detail)
        self.assertIn(
            f"names no lift at {station('GSTNS').name} and no level way to platform 2",
            result.detail,
        )
        # Athy claims a lift: the silent platform gets the other wording.
        result = self.verdict("ATHY", "The escalators at platforms 1 and 3 are out.")
        self.assertIn("calls platform 1 level", result.detail)
        self.assertIn("names no lift or level way to platform 3", result.detail)

    def test_one_level_sentence_is_quoted_once_for_many_platforms(self):
        result = self.verdict("BRAY", "The escalators at platforms 1 and 2 are out.")
        self.assertIn(
            'calls platforms 1 and 2 level: "Level to platform 1, 2 & 3", so the notice and '
            "the page disagree about them.",
            result.detail,
        )
        self.assertEqual(result.detail.count('"Level to platform 1, 2 & 3"'), 1)

    def test_a_missing_station_gets_the_deduction_alone(self):
        result = model.verdict(None, "escalator", "The escalator at platform 2 is out.")
        self.assertEqual(result.state, "escalator")
        self.assertNotIn("Irish Rail's page", result.detail)
        self.assertIn("did lose a way up", result.detail)

    def test_a_concurrent_lift_notice_withdraws_the_lift_line(self):
        result = self.verdict(
            "PERSE", "The escalator at platform 2 is unavailable.", lift_listed_too=True
        )
        self.assertNotIn('"Lift or stairs', result.detail)
        self.assertIn(
            "puts a lift on the way to platform 2 as well, though a lift notice at this "
            "station overlapped this one.",
            result.detail,
        )
        # Station-wide flag: it must not say which lift was out.
        self.assertNotIn("was out", result.detail)
        entrance = self.verdict(
            "CNLLY", "The Escalator at the main concourse is out.", lift_listed_too=True
        )
        self.assertIn("overlapped this one", entrance.detail)
        self.assertIn('"Level access from car park"', entrance.detail)

    def test_the_page_silent_on_escalators_still_says_so(self):
        result = self.verdict("HZLCH", "The escalator at platform 2 is unavailable.")
        self.assertTrue(result.detail.endswith("does not mention an escalator."))

    def test_it_never_infers_the_lift_was_working(self):
        cases = (
            ("PERSE", "The escalator at platform 2 is unavailable."),
            ("CNLLY", "The Escalator at the main concourse is out."),
            ("HZLCH", "The escalator is out of service."),
            ("ATHY", "The escalator at platform 1 is out."),
            ("DRMOD", "The escalator at platform 2 is out."),
        )
        for code, text in cases:
            detail = self.verdict(code, text).detail.lower()
            for phrase in FORBIDDEN:
                self.assertNotIn(phrase, detail, (code, phrase))

    def test_every_quote_is_a_verbatim_substring_of_the_prose(self):
        cases = (
            ("PERSE", "The escalator at platform 2 is unavailable."),
            ("CNLLY", "The Escalator at the main concourse is out."),
            ("HZLCH", "The escalator at platform 2 is unavailable."),
            ("ATHY", "The escalator at platform 1 is out."),
        )
        for code, text in cases:
            st = station(code)
            prose = f"{st.platform_access}\n{st.ticket_office_access}"
            quotes = re.findall(r'"([^"]+)"', self.verdict(code, text).detail)
            self.assertTrue(quotes, code)
            for quote in quotes:
                self.assertIn(quote, prose, code)


if __name__ == "__main__":
    unittest.main()
