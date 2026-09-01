import unittest

from shiplabel import formatter


class NormalizeNameTests(unittest.TestCase):
    def test_collapses_whitespace_and_fixes_case(self):
        self.assertEqual(formatter.normalize_name("  jOHN   smith  "), "John Smith")

    def test_canonicalizes_suffix(self):
        self.assertEqual(formatter.normalize_name("john smith JR."), "John Smith Jr")

    def test_handles_hyphen_and_apostrophe(self):
        self.assertEqual(formatter.normalize_name("mary-jane o'brien"), "Mary-Jane O'Brien")

    def test_empty_input(self):
        self.assertEqual(formatter.normalize_name(""), "")
        self.assertEqual(formatter.normalize_name(None), "")


class NormalizePostalCodeTests(unittest.TestCase):
    def test_us_zip_plus_four_without_dash(self):
        self.assertEqual(formatter.normalize_postal_code("941105678"), "94110-5678")

    def test_us_zip_five(self):
        self.assertEqual(formatter.normalize_postal_code(" 94110 "), "94110")

    def test_canadian_postal_code(self):
        self.assertEqual(formatter.normalize_postal_code("k1a0b1", "CA"), "K1A 0B1")


class NormalizePhoneTests(unittest.TestCase):
    def test_strips_formatting_and_country_code(self):
        self.assertEqual(formatter.normalize_phone("+1 (555) 123-4567"), "(555) 123-4567")

    def test_ten_digits_no_formatting(self):
        self.assertEqual(formatter.normalize_phone("5551234567"), "(555) 123-4567")

    def test_unrecognized_shape_passes_through_digits(self):
        self.assertEqual(formatter.normalize_phone("12345"), "12345")


class NormalizeStateTests(unittest.TestCase):
    def test_full_name_to_code(self):
        self.assertEqual(formatter.normalize_state("california"), "CA")

    def test_already_a_code(self):
        self.assertEqual(formatter.normalize_state("ca"), "CA")

    def test_non_us_country_is_upper_cased_only(self):
        self.assertEqual(formatter.normalize_state("on", "CA"), "ON")


class FormatLabelTests(unittest.TestCase):
    def test_full_record(self):
        raw = {
            "name": "  jane   DOE ",
            "company": "  acme corp  ",
            "address_lines": ["123 main st", "", "  suite 400 "],
            "city": "san francisco",
            "state": "california",
            "postal_code": "941105678",
            "country": "United States",
            "phone": "1-555-123-4567",
        }
        result = formatter.format_label(raw)
        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["company"], "acme corp")
        self.assertEqual(result["address_lines"], ("123 main st", "suite 400"))
        self.assertEqual(result["city"], "San Francisco")
        self.assertEqual(result["state"], "CA")
        self.assertEqual(result["postal_code"], "94110-5678")
        self.assertEqual(result["country"], "US")
        self.assertEqual(result["phone"], "(555) 123-4567")

    def test_does_not_mutate_input(self):
        raw = {"name": "jane doe", "address_lines": ["a", "b"]}
        raw_copy = dict(raw)
        formatter.format_label(raw)
        self.assertEqual(raw, raw_copy)

    def test_missing_keys_default_to_empty(self):
        result = formatter.format_label({})
        self.assertEqual(result["name"], "")
        self.assertEqual(result["address_lines"], ())
        self.assertEqual(result["country"], "US")


if __name__ == "__main__":
    unittest.main()
