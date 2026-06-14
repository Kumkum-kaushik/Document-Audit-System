# PURPOSE:        Parse raw string values extracted from documents into canonical
#                 Python types so validation can compare apples to apples.
# ARCHITECTURE:   NORMALIZATION  (sits between Extraction and Validation)
# CALLED BY:      main.py  — after extract() returns raw records
# CALLS NEXT:     validation.py  — main.py passes normalized records to validate()
# INPUT->OUTPUT:  list of raw record dicts  ->  list of normalized record dicts
#
# Why normalization is a separate stage
# --------------------------------------
# Raw text from a PDF may say "±2 kV", "2kV", "2 KV" — all meaning the same
# thing.  The extractor captures the raw string; the normalizer converts it
# to a structured value so validation logic is simple equality/comparison,
# not fragile string matching.

import re


# ---------------------------------------------------------------------------
# Individual field normalizers
# ---------------------------------------------------------------------------

def _normalize_level(value):
    """
    Parse an electrical level string into a structured dict.

    Examples:
        "±2 kV"  ->  {"sign": "±", "magnitude": 2.0,  "unit": "kV"}
        "10 V/m" ->  {"sign": "+", "magnitude": 10.0, "unit": "V/m"}
        "3Vrms"  ->  {"sign": "+", "magnitude": 3.0,  "unit": "Vrms"}

    If the value does not match the pattern it is returned unchanged so
    that unknown formats don't silently disappear.
    """
    if not isinstance(value, str):
        return value  # already parsed or None — pass through

    # Pattern: optional sign (± + -), digits/decimal, optional space, unit chars
    pattern = r'^([±+\-]?)\s*([\d.]+)\s*([a-zA-Z/]+)$'
    match = re.match(pattern, value.strip())

    if match:
        sign_str, magnitude_str, unit = match.groups()
        # Treat empty sign as positive
        sign = sign_str if sign_str else "+"
        return {
            "sign":      sign,
            "magnitude": float(magnitude_str),
            "unit":      unit,
        }

    # Fallback: return raw string so nothing is silently lost
    return value


def _normalize_class(value):
    """
    Canonicalise performance class strings to "Class X" (title-case).

    Examples:
        "class a"   -> "Class A"
        "CLASS B"   -> "Class B"
        "Class B"   -> "Class B"   (already canonical, no change)
        "Compliant" -> "Compliant" (not a class string, pass through)
    """
    if isinstance(value, str) and "class" in value.lower():
        # Split on whitespace and take the last token as the class letter
        parts = value.strip().split()
        letter = parts[-1].upper()
        return f"Class {letter}"

    return value  # not a class string — return unchanged


def _normalize_observation(value):
    """
    Strip leading/trailing whitespace from safety observation strings.
    The real system might also do synonym mapping here
    (e.g.  "Pass" -> "No fire hazard observed" is NOT done here —
     that kind of semantic mapping belongs in the ruleset, not the normalizer).
    """
    if isinstance(value, str):
        return value.strip()
    return value


# ---------------------------------------------------------------------------
# Top-level normalize() — the only function main.py calls
# ---------------------------------------------------------------------------

def normalize(records):
    """
    Walk every record and normalise known fields.
    Unknown fields are copied through unchanged so nothing is lost.

    The function is track-agnostic: it checks for field names that appear
    in either EMC or safety records and applies the right parser to each.

    Parameters
    ----------
    records : list[dict]
        Raw records returned by an extractor function.

    Returns
    -------
    list[dict]
        New list of dicts; input records are not mutated.
    """
    normalized = []

    for raw in records:
        # Copy so we never mutate the original fake-doc dict in main.py
        rec = dict(raw)

        # --- EMC-specific fields ---
        if "measured_level" in rec:
            rec["measured_level"] = _normalize_level(rec["measured_level"])

        if "measured_class" in rec:
            rec["measured_class"] = _normalize_class(rec["measured_class"])

        # --- Safety-specific fields ---
        if "observed_result" in rec:
            rec["observed_result"] = _normalize_observation(rec["observed_result"])

        normalized.append(rec)

    return normalized
