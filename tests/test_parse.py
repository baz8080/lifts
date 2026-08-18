import json
import unittest
from pathlib import Path

from lift_status import parse
from tests.helpers import make_item

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseTopLevel(unittest.TestCase):
    def test_valid_list(self):
        body = json.dumps([make_item()])
        items = parse.parse_top_level(body)
        self.assertEqual(len(items), 1)

    def test_empty_list_is_a_genuine_success(self):
        # A real, honest "nothing to report" must be distinguishable from a
        # parse failure - this is exactly what NOT_A_LIST exists to protect.
        items = parse.parse_top_level("[]")
        self.assertEqual(items, [])
        self.assertIsNot(items, parse.NOT_A_LIST)

    def test_object_root_is_not_a_list(self):
        result = parse.parse_top_level(json.dumps({"messages": [make_item()]}))
        self.assertIs(result, parse.NOT_A_LIST)

    def test_malformed_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            parse.parse_top_level("{not valid json")

    def test_sample_response_fixture_parses_cleanly(self):
        body = (FIXTURES / "sample_response.json").read_text()
        items = parse.parse_top_level(body)
        self.assertEqual(len(items), 6)
        for item in items:
            self.assertEqual(parse.check_item_schema(item), [])
            valid, reason = parse.identity_fields_valid(item)
            self.assertTrue(valid, reason)


class TestCheckItemSchema(unittest.TestCase):
    def test_well_formed_item_has_no_drift(self):
        self.assertEqual(parse.check_item_schema(make_item()), [])

    def test_unexpected_field_is_flagged(self):
        item = make_item()
        item["newField"] = "surprise"
        problems = parse.check_item_schema(item)
        self.assertTrue(any("unexpected" in p for p in problems))

    def test_missing_non_identity_field_is_flagged(self):
        item = make_item()
        del item["products"]
        problems = parse.check_item_schema(item)
        self.assertTrue(any("missing" in p and "products" in p for p in problems))

    def test_non_dict_item_is_flagged(self):
        self.assertEqual(parse.check_item_schema("not a dict"), ["item is not an object"])


class TestIdentityFieldsValid(unittest.TestCase):
    def test_well_formed_item_is_valid(self):
        valid, reason = parse.identity_fields_valid(make_item())
        self.assertTrue(valid, reason)

    def test_missing_location_codes_is_invalid(self):
        item = make_item()
        del item["locationCodes"]
        valid, reason = parse.identity_fields_valid(item)
        self.assertFalse(valid)
        self.assertIn("locationCodes", reason)

    def test_empty_location_codes_is_invalid(self):
        item = make_item(codes=[])
        valid, _ = parse.identity_fields_valid(item)
        self.assertFalse(valid)

    def test_blank_head_is_invalid(self):
        item = make_item(head="   ")
        valid, _ = parse.identity_fields_valid(item)
        self.assertFalse(valid)

    def test_non_dict_is_invalid(self):
        valid, reason = parse.identity_fields_valid(["not", "a", "dict"])
        self.assertFalse(valid)


class TestDeriveIdentityKey(unittest.TestCase):
    def test_stable_across_location_code_reordering_and_case(self):
        a = make_item(codes=["MHIDE", "DUBP"])
        b = make_item(codes=["dubp", " mhide "])
        self.assertEqual(parse.derive_identity_key(a), parse.derive_identity_key(b))

    def test_different_head_changes_the_key(self):
        a = make_item(head="Station A - Lift out of order")
        b = make_item(head="Station A - Lift working again soon")
        self.assertNotEqual(parse.derive_identity_key(a), parse.derive_identity_key(b))

    def test_different_start_changes_the_key(self):
        # Documented limitation: a corrected start time looks like a new
        # message, not an edit to the existing one.
        a = make_item(start="2026-01-01T00:00:00")
        b = make_item(start="2026-01-01T00:05:00")
        self.assertNotEqual(parse.derive_identity_key(a), parse.derive_identity_key(b))

    def test_text_and_end_changes_do_not_change_the_key(self):
        a = make_item(text="original text", end="2026-12-31T23:59:00")
        b = make_item(text="updated text, different wording", end="2027-01-15T23:59:00")
        self.assertEqual(parse.derive_identity_key(a), parse.derive_identity_key(b))


class TestParseDublinDatetime(unittest.TestCase):
    def test_normal_value(self):
        utc, ambiguous = parse.parse_dublin_datetime("2026-01-15T12:00:00")
        self.assertEqual(utc, "2026-01-15T12:00:00Z")  # winter: no DST offset
        self.assertFalse(ambiguous)

    def test_summer_offset_applied(self):
        utc, ambiguous = parse.parse_dublin_datetime("2026-06-15T12:00:00")
        self.assertEqual(utc, "2026-06-15T11:00:00Z")  # IST is UTC+1
        self.assertFalse(ambiguous)

    def test_dst_fall_back_ambiguous(self):
        # Last Sunday of October 2026 = Oct 25: 01:00-01:59 happens twice.
        utc, ambiguous = parse.parse_dublin_datetime("2026-10-25T01:30:00")
        self.assertTrue(ambiguous)
        self.assertIsNotNone(utc)

    def test_dst_spring_forward_imaginary(self):
        # Last Sunday of March 2026 = Mar 29: 01:00-01:59 never happens.
        utc, ambiguous = parse.parse_dublin_datetime("2026-03-29T01:30:00")
        self.assertTrue(ambiguous)

    def test_malformed_value_returns_none(self):
        utc, ambiguous = parse.parse_dublin_datetime("not a date")
        self.assertIsNone(utc)
        self.assertFalse(ambiguous)

    def test_missing_value_returns_none(self):
        utc, ambiguous = parse.parse_dublin_datetime(None)
        self.assertIsNone(utc)
        self.assertFalse(ambiguous)


class TestNormalizeItem(unittest.TestCase):
    def test_round_trips_expected_fields(self):
        item = make_item()
        n = parse.normalize_item(item)
        self.assertEqual(n["head"], item["head"])
        self.assertEqual(n["start_raw"], item["start"])
        self.assertIsNotNone(n["start_utc"])
        self.assertEqual(json.loads(n["location_codes"]), ["TEST"])


if __name__ == "__main__":
    unittest.main()
