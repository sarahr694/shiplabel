# shiplabel

Order data going into a shipping label rarely comes in clean. Names are
typed in all caps or all lowercase, "CA" and "California" both show up
in the same export, ZIP+4 codes lose their dash, and phone numbers
carry a `+1` or don't. If you print labels straight from that data you
get inconsistent, unprofessional-looking output, and if you try to
dedupe or match records against it you get false negatives.

`shiplabel` is a small formatter that takes one messy record and
returns a normalized one. There's no I/O in it and no shipping carrier
integration - it just does the string cleanup that every label
pipeline ends up needing, in one place, with tests.

## Usage

```python
from shiplabel import format_label

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

format_label(raw)
# {
#     "name": "Jane Doe",
#     "company": "acme corp",
#     "address_lines": ("123 main st", "suite 400"),
#     "city": "San Francisco",
#     "state": "CA",
#     "postal_code": "94110-5678",
#     "country": "US",
#     "phone": "(555) 123-4567",
# }
```

Every function in `shiplabel.formatter` is pure: same input, same
output, no mutation of arguments, no reliance on the clock, the
filesystem, or the network. `format_label` composes the smaller
functions (`normalize_name`, `normalize_state`, `normalize_postal_code`,
`normalize_phone`, ...) which are also exported individually, in case
you only need to clean up one field rather than a whole record.

## What it normalizes

- **Name** - collapses whitespace, fixes case, canonicalizes suffixes
  (`JR.` / `jr` / `Jr` all become `Jr`), handles hyphenated and
  apostrophe names like `mary-jane o'brien`.
- **State** - maps full US state names to their two-letter code;
  leaves non-US regions upper-cased.
- **Postal code** - reformats US ZIP+4 to `12345-6789` regardless of
  whether the dash was present, and Canadian codes to `A1A 1A1`.
- **Phone** - strips a leading `+1` / `1` country code and formats US
  and Canadian numbers as `(555) 123-4567`.
- **Country** - maps common aliases (`USA`, `U.S.`, `United States`,
  ...) to ISO 3166-1 alpha-2 codes.
- **Address lines** - drops blank lines, trims each remaining one.

Anything that doesn't match a known shape (a postal code that isn't 5
or 9 digits, a phone number that isn't 10 digits) is returned trimmed
rather than rejected, since a formatter that throws on the long tail of
real-world data is more dangerous than one that passes an odd value
through for a human to look at.

## CLI

`shiplabel` also installs a command that normalizes a whole CSV file of
records at once:

```
shiplabel orders.csv normalized.csv
```

Either argument can be `-` for stdin/stdout, and the output defaults to
stdout if omitted:

```
cat orders.csv | shiplabel - > normalized.csv
```

The CSV columns are `name`, `company`, `city`, `state`, `postal_code`,
`country`, `phone`, plus any number of `address_line1`, `address_line2`,
... columns (a flat CSV row has no natural place for a list, so address
lines are numbered instead). The output uses as many numbered address
columns as the widest row in the batch needs; shorter rows get blank
cells in the rest.

## Running the tests

The test suite uses only `unittest` from the standard library:

```
python -m unittest discover tests
```

## Status

Early. Covers US and Canadian addresses. No support for international
address formats beyond passthrough.
