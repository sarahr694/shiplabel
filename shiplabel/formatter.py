"""Normalize messy shipping label input into a consistent shape.

Every function here is pure: given the same input it returns the same
output, and it never touches a file, a clock, or the network. That is
what makes a batch of a few hundred thousand orders from three
different checkout carts safe to run through this without surprises.
"""

import re

# Suffixes get a canonical form regardless of how they were typed in
# (jr, JR, jr., Jr. all become "Jr").
_CANONICAL_SUFFIXES = {
    "jr": "Jr",
    "sr": "Sr",
    "ii": "II",
    "iii": "III",
    "iv": "IV",
}

# Aliases seen in real order exports, mapped to ISO 3166-1 alpha-2.
_COUNTRY_ALIASES = {
    "us": "US",
    "usa": "US",
    "u.s.a.": "US",
    "u.s.": "US",
    "united states": "US",
    "united states of america": "US",
    "ca": "CA",
    "canada": "CA",
    "uk": "GB",
    "u.k.": "GB",
    "gb": "GB",
    "great britain": "GB",
    "united kingdom": "GB",
}

_US_STATE_ALIASES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT",
    "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI",
    "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME",
    "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
    "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
    "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM",
    "new york": "NY", "north carolina": "NC", "north dakota": "ND",
    "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
    "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
    "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
    "district of columbia": "DC",
}
_US_STATE_CODES = set(_US_STATE_ALIASES.values())


def normalize_whitespace(text):
    """Collapse any run of whitespace to a single space and trim the ends."""
    if not text:
        return ""
    return " ".join(text.split())


def _capitalize_word(word):
    # Split on hyphens and apostrophes so "mary-jane" and "o'brien" both
    # get every piece capitalized, not just the first letter of the whole word.
    pieces = re.split(r"([-'])", word)
    return "".join(
        p if p in ("-", "'") else (p[:1].upper() + p[1:].lower())
        for p in pieces
    )


def normalize_name(name):
    """Turn a raw name string into consistent title case.

    Handles the messy cases that show up in real checkout forms:
    all caps, all lowercase, extra internal whitespace, and generation
    suffixes typed in any case or with a trailing period.
    """
    cleaned = normalize_whitespace(name)
    if not cleaned:
        return ""
    words = []
    for word in cleaned.split(" "):
        key = word.lower().rstrip(".")
        if key in _CANONICAL_SUFFIXES:
            words.append(_CANONICAL_SUFFIXES[key])
        else:
            words.append(_capitalize_word(word))
    return " ".join(words)


def normalize_address_lines(lines):
    """Strip and drop blank lines from a sequence of address lines.

    Returns a tuple rather than a list so a caller can't mutate the
    result and expect a second call to reflect that.
    """
    if not lines:
        return ()
    return tuple(
        normalize_whitespace(line)
        for line in lines
        if line and line.strip()
    )


def normalize_country(country):
    """Map common country name variants to an ISO 3166-1 alpha-2 code.

    Falls back to a trimmed, title-cased version of the input when the
    value isn't a known alias, rather than raising, since a formatter
    that crashes on an unrecognized country is worse than one that
    passes the value through for a human to fix.
    """
    cleaned = normalize_whitespace(country)
    if not cleaned:
        return ""
    key = cleaned.lower()
    if key in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[key]
    if len(cleaned) == 2:
        return cleaned.upper()
    return cleaned.title()


def normalize_state(state, country="US"):
    """Map a US state name or abbreviation to its two-letter code.

    For non-US countries there is no shared abbreviation scheme, so the
    value is just whitespace-normalized and upper-cased, which matches
    how Canadian provinces are printed on labels (ON, BC, QC, ...).
    """
    cleaned = normalize_whitespace(state)
    if not cleaned:
        return ""
    if normalize_country(country) != "US":
        return cleaned.upper()
    upper = cleaned.upper()
    if upper in _US_STATE_CODES:
        return upper
    return _US_STATE_ALIASES.get(cleaned.lower(), cleaned.title())


def normalize_postal_code(postal_code, country="US"):
    """Normalize a postal code for the given country.

    US ZIP+4 codes are reformatted to the standard 12345-6789 shape
    even if the dash was dropped or replaced with a space. Canadian
    postal codes are upper-cased and spaced as A1A 1A1. Anything else
    is just trimmed and upper-cased, since ZIP-style validation
    doesn't apply.
    """
    cleaned = normalize_whitespace(postal_code).upper()
    if not cleaned:
        return ""
    code = cleaned.upper()
    country_code = normalize_country(country)

    if country_code == "US":
        digits = re.sub(r"[^0-9]", "", code)
        if len(digits) == 9:
            return f"{digits[:5]}-{digits[5:]}"
        if len(digits) == 5:
            return digits
        return code

    if country_code == "CA":
        compact = re.sub(r"[^A-Z0-9]", "", code)
        if len(compact) == 6:
            return f"{compact[:3]} {compact[3:]}"
        return code

    return code


def normalize_phone(phone, country="US"):
    """Format a phone number for the given country.

    US and Canadian numbers are reduced to their 10 significant digits
    (a leading country code "1" is dropped) and printed as
    (555) 123-4567. Numbers that don't match that shape, and numbers
    for other countries, are returned with only the non-digit
    separators stripped so nothing is silently discarded.
    """
    cleaned = normalize_whitespace(phone)
    if not cleaned:
        return ""
    digits = re.sub(r"[^0-9]", "", cleaned)
    country_code = normalize_country(country)

    if country_code in ("US", "CA"):
        if len(digits) == 11 and digits[0] == "1":
            digits = digits[1:]
        if len(digits) == 10:
            return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"

    return digits if digits else cleaned


def format_label(record):
    """Normalize a raw shipping label record into a consistent shape.

    `record` is a mapping that may contain any of: name, company,
    address_lines (a sequence of strings), city, state, postal_code,
    country, phone. Missing keys are treated as empty. The input
    mapping is never modified; a new dict is always returned.
    """
    country = normalize_country(record.get("country", "US") or "US")
    return {
        "name": normalize_name(record.get("name", "")),
        "company": normalize_whitespace(record.get("company", "")),
        "address_lines": normalize_address_lines(record.get("address_lines", ())),
        "city": normalize_whitespace(record.get("city", "")).title(),
        "state": normalize_state(record.get("state", ""), country),
        "postal_code": normalize_postal_code(record.get("postal_code", ""), country),
        "country": country,
        "phone": normalize_phone(record.get("phone", ""), country),
    }
