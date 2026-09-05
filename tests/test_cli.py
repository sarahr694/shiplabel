import csv
import io
import tempfile
import unittest
from pathlib import Path

from shiplabel import cli


class ReadRecordsTests(unittest.TestCase):
    def test_reads_numbered_address_lines_in_order(self):
        handle = io.StringIO(
            "name,address_line1,address_line2,city\n"
            "jane doe,123 main st,suite 400,san francisco\n"
        )
        records = cli._read_records(handle)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["address_lines"], ("123 main st", "suite 400"))
        self.assertEqual(records[0]["city"], "san francisco")

    def test_missing_fixed_columns_default_to_empty(self):
        handle = io.StringIO("name\njane doe\n")
        records = cli._read_records(handle)
        self.assertEqual(records[0]["company"], "")
        self.assertEqual(records[0]["address_lines"], ())


class WriteRecordsTests(unittest.TestCase):
    def test_pads_address_lines_to_widest_row(self):
        records = [
            {
                "name": "Jane Doe",
                "company": "",
                "address_lines": ("123 Main St", "Suite 400"),
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94110",
                "country": "US",
                "phone": "",
            },
            {
                "name": "John Roe",
                "company": "",
                "address_lines": ("456 Oak Ave",),
                "city": "Reno",
                "state": "NV",
                "postal_code": "89501",
                "country": "US",
                "phone": "",
            },
        ]
        handle = io.StringIO()
        cli._write_records(handle, records)
        rows = list(csv.DictReader(io.StringIO(handle.getvalue())))
        self.assertIn("address_line2", rows[0])
        self.assertEqual(rows[0]["address_line2"], "Suite 400")
        self.assertEqual(rows[1]["address_line2"], "")

    def test_no_address_columns_when_no_records(self):
        handle = io.StringIO()
        cli._write_records(handle, [])
        header = handle.getvalue().splitlines()[0]
        self.assertNotIn("address_line", header)


class MainTests(unittest.TestCase):
    def test_round_trip_through_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / "in.csv"
            out_path = Path(tmp) / "out.csv"
            in_path.write_text(
                "name,address_line1,city,state,postal_code,country,phone\n"
                "jane doe,123 main st,san francisco,california,941105678,"
                "United States,1-555-123-4567\n",
                encoding="utf-8",
            )
            cli.main([str(in_path), str(out_path)])
            rows = list(csv.DictReader(out_path.open(newline="", encoding="utf-8")))
            self.assertEqual(rows[0]["name"], "Jane Doe")
            self.assertEqual(rows[0]["state"], "CA")
            self.assertEqual(rows[0]["postal_code"], "94110-5678")
            self.assertEqual(rows[0]["phone"], "(555) 123-4567")


if __name__ == "__main__":
    unittest.main()
