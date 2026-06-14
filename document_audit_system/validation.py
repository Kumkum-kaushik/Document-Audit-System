# PURPOSE:        Compare normalized extracted records against reference standards
#                 and produce a PASS / FAIL / NOT_APPLICABLE verdict for each test.
# ARCHITECTURE:   VALIDATION  (fourth pipeline stage)
# CALLED BY:      main.py  — after load_reference() returns the reference rows
# CALLS NEXT:     reporting.py  — main.py passes results to generate_report()
# INPUT->OUTPUT:  (normalized records, reference rows, doc_type, variant?)
#                     ->  list of result dicts, one per test


# ---------------------------------------------------------------------------
# Result dict shape (same for both tracks, so reporting.py needs one renderer):
#
#   For EMC:
#     { "test_sub_type": str, "line_type": str, "standard_reference": str,
#       "verdict": "PASS"|"FAIL"|"NOT_APPLICABLE",
#       "expected": str, "actual": str, "reason": str }
#
#   For Safety:
#     { "test_name": str,
#       "verdict": "PASS"|"FAIL"|"NOT_APPLICABLE",
#       "expected": str, "actual": str, "reason": str }
# ---------------------------------------------------------------------------


# ===========================================================================
# EMC validation
# ===========================================================================

def _validate_emi_emc(normalized, reference):
    """
    Join normalized EMC records to reference rows on the composite key:
        (test_sub_type, line_type, standard_reference)

    Then compare measured_class (from the document) to pass_criteria
    (from the reference).  Both are already canonical "Class X" strings
    after normalization, so a simple equality check is sufficient.

    Steps
    -----
    1. Build a lookup dict from reference for O(1) access per record.
    2. For each normalized record, retrieve the matching reference row.
    3. If no reference row exists → FAIL with a diagnostic reason.
    4. If row found → compare measured_class to pass_criteria.
    """

    # Step 1 — index reference by the join key
    ref_lookup = {
        (r["test_sub_type"], r["line_type"], r["standard_reference"]): r
        for r in reference
    }

    results = []

    for rec in normalized:
        # The join key — all three fields must match
        key = (
            rec.get("test_sub_type"),
            rec.get("line_type"),
            rec.get("standard_reference"),
        )

        ref_row = ref_lookup.get(key)

        # --- Step 3: no matching reference row ---
        if ref_row is None:
            results.append({
                "test_sub_type":      key[0],
                "line_type":          key[1],
                "standard_reference": key[2],
                "verdict":  "FAIL",
                "expected": "N/A — no reference row found",
                "actual":   str(rec.get("measured_class")),
                "reason":   (
                    "No reference row matched on "
                    f"test_sub_type='{key[0]}', line_type='{key[1]}', "
                    f"standard_reference='{key[2]}'. "
                    "Check the reference .ods file."
                ),
            })
            continue

        # --- Step 4: compare performance class ---
        expected = ref_row["pass_criteria"]          # e.g. "Class A"
        actual   = rec.get("measured_class", "")     # normalized to "Class X"

        if actual == expected:
            verdict = "PASS"
            reason  = f"Measured '{actual}' satisfies required '{expected}'"
        else:
            verdict = "FAIL"
            reason  = f"Measured '{actual}' does NOT meet required '{expected}'"

        results.append({
            "test_sub_type":      key[0],
            "line_type":          key[1],
            "standard_reference": key[2],
            "verdict":  verdict,
            "expected": expected,
            "actual":   str(actual),
            "reason":   reason,
        })

    return results


# ===========================================================================
# Safety validation
# ===========================================================================

def _validate_safety(normalized, reference, product_variant):
    """
    Two-gate validation for safety tests.

    Gate 1 — Applicability  (mirrors Sheet2 of Safety_testing_list.ods)
        If the product_variant is NOT in ref_row["applicable_to"],
        verdict = NOT_APPLICABLE.  The test is skipped entirely.

    Gate 2 — Observation match  (mirrors Sheet1 of Safety_testing_list.ods)
        If applicable, compare the extracted observed_result (already
        whitespace-stripped by the normalizer) against the reference
        "observation" field.

    Join key: test_name
    """

    # Build lookup by test_name for O(1) access
    ref_lookup = {r["test_name"]: r for r in reference}

    results = []

    for rec in normalized:
        test_name = rec.get("test_name")
        ref_row   = ref_lookup.get(test_name)

        # No reference row at all — flag as FAIL with explanation
        if ref_row is None:
            results.append({
                "test_name": test_name,
                "verdict":   "FAIL",
                "expected":  "N/A — test not in reference",
                "actual":    str(rec.get("observed_result")),
                "reason":    f"test_name='{test_name}' not found in reference data",
            })
            continue

        # ---- Gate 1: applicability check ----
        applicable_variants = ref_row.get("applicable_to", [])
        if product_variant not in applicable_variants:
            results.append({
                "test_name": test_name,
                "verdict":   "NOT_APPLICABLE",
                "expected":  "N/A",
                "actual":    "N/A",
                "reason":    (
                    f"Test '{test_name}' is not required for "
                    f"variant '{product_variant}'. "
                    f"Applicable to: {applicable_variants}"
                ),
            })
            continue

        # ---- Gate 2: observation match ----
        expected = ref_row["observation"]
        actual   = rec.get("observed_result", "")

        # Case-insensitive exact match.
        # Real system may use fuzzy matching for minor wording differences.
        if actual.strip().lower() == expected.strip().lower():
            verdict = "PASS"
            reason  = "Observed result matches reference observation"
        else:
            verdict = "FAIL"
            reason  = f"Expected: '{expected}'  |  Got: '{actual}'"

        results.append({
            "test_name": test_name,
            "verdict":   verdict,
            "expected":  expected,
            "actual":    actual,
            "reason":    reason,
        })

    return results


# ===========================================================================
# Public entry point — the only function main.py calls
# ===========================================================================

def validate(normalized, reference, doc_type, product_variant=None):
    """
    Dispatch to the correct validation logic based on doc_type.

    Parameters
    ----------
    normalized      : list[dict]  Normalized records from normalizer.py
    reference       : list[dict]  Reference rows from reference.py
    doc_type        : str         "emi_emc" or "safety"
    product_variant : str | None  Required for safety track (e.g. "G3 Timer")

    Returns
    -------
    list[dict]
        One result dict per normalized record.  Each dict contains
        'verdict', 'expected', 'actual', and 'reason'.
    """
    if doc_type == "emi_emc":
        return _validate_emi_emc(normalized, reference)

    elif doc_type == "safety":
        if product_variant is None:
            raise ValueError(
                "validate(): safety track requires product_variant "
                "(e.g. 'G3 Timer', 'G3 Counter', 'LTC9A')."
            )
        return _validate_safety(normalized, reference, product_variant)

    else:
        raise ValueError(
            f"validate(): unknown doc_type='{doc_type}'. "
            "Expected 'emi_emc' or 'safety'."
        )
