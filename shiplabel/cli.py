"""Command-line interface for normalizing a batch of shipping labels stored as CSV.

Address lines don't fit naturally into a flat CSV row, so this reads any
column named address_line1, address_line2, ... (in that numeric order)
into the address_lines tuple that format_label expects, and writes the
result back out the same way, using as many numbered columns as the
widest row in the batch actually needs.
"""

import argparse
import csv
import re
import sys

from .formatter import format_label

_ADDRESS_LINE_RE = re.compile(r"^address_line(\d+)$", re.IGNORECASE)

_FIXED_FIELDS = ("name", "company", "city", "state", "postal_code", "country", "phone")


def _address_line_columns(fieldnames):
    numbered = []
    for name in fieldnames or ():
        match = _ADDRESS_LINE_RE.match(name)
        if match:
            numbered.append((int(match.group(1)), name))
    numbered.sort()
    return [name for _, name in numbered]


def _row_to_record(row, address_columns):
    record = {field: row.get(field, "") or "" for field in _FIXED_FIELDS}
    record["address_lines"] = tuple(row.get(col, "") for col in address_columns)
    return record


def _read_records(handle):
    reader = csv.DictReader(handle)
    address_columns = _address_line_columns(reader.fieldnames)
    return [_row_to_record(row, address_columns) for row in reader]


def _write_records(handle, records):
    max_lines = max((len(record["address_lines"]) for record in records), default=0)
    address_fields = [f"address_line{i + 1}" for i in range(max_lines)]
    fieldnames = ["name", "company", *address_fields, "city", "state", "postal_code", "country", "phone"]

    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    for record in records:
        row = {field: record[field] for field in _FIXED_FIELDS}
        lines = record["address_lines"]
        for i, field in enumerate(address_fields):
            row[field] = lines[i] if i < len(lines) else ""
        writer.writerow(row)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="shiplabel",
        description="Normalize a CSV of shipping label records with shiplabel.format_label.",
    )
    parser.add_argument("input", help="input CSV file, or - for stdin")
    parser.add_argument(
        "output", nargs="?", default="-", help="output CSV file, or - for stdout (default)"
    )
    args = parser.parse_args(argv)

    if args.input == "-":
        records = _read_records(sys.stdin)
    else:
        with open(args.input, newline="", encoding="utf-8") as handle:
            records = _read_records(handle)

    normalized = [format_label(record) for record in records]

    if args.output == "-":
        _write_records(sys.stdout, normalized)
    else:
        with open(args.output, "w", newline="", encoding="utf-8") as handle:
            _write_records(handle, normalized)


if __name__ == "__main__":
    main()
