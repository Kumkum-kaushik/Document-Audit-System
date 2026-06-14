# PURPOSE:        Format validation results into a human-readable audit summary
#                 and return a structured summary dict for programmatic use.
# ARCHITECTURE:   REPORTING  (final pipeline stage)
# CALLED BY:      main.py  — called with the results list from validate()
# CALLS NEXT:     Nothing — this is the terminal stage of the pipeline.
# INPUT->OUTPUT:  list of result dicts  ->  printed audit report  +  summary dict
#
# Why a separate reporting module?
# ---------------------------------
# Keeping formatting logic here means validation.py never needs to know about
# presentation, and this module can be swapped for an HTML/JSON renderer without
# touching any other stage.


# ---------------------------------------------------------------------------
# Verdict markers — change these to switch the visual style everywhere
# ---------------------------------------------------------------------------
MARKERS = {
    "PASS":           "[PASS]",
    "FAIL":           "[FAIL]",
    "NOT_APPLICABLE": "[ N/A]",
}

SEPARATOR_WIDE = "=" * 65
SEPARATOR_THIN = "-" * 65


def _test_label(result):
    """
    Build a short identifying label for a result dict.
    Works for both EMC results (use sub-type + line + standard)
    and Safety results (use test_name).
    """
    if "test_sub_type" in result:
        return (
            f"{result['test_sub_type']} / "
            f"{result['line_type']} / "
            f"{result['standard_reference']}"
        )
    return result.get("test_name", "(unknown test)")


def generate_report(results, doc_label="Document"):
    """
    Print a per-test breakdown followed by a summary line.
    Returns a summary dict so callers can inspect counts programmatically
    or forward the data to a downstream system (e.g. a database insert,
    a JSON file write, or an email trigger).

    Parameters
    ----------
    results   : list[dict]  Result dicts from validation.py
    doc_label : str         Human-readable name for this document (used in header)

    Returns
    -------
    dict  with keys: doc_label, total, pass, fail, not_applicable, details
    """

    # Tally verdicts for the summary line
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    na_count   = sum(1 for r in results if r["verdict"] == "NOT_APPLICABLE")
    total      = len(results)

    # ---- Header ----
    print(f"\n{SEPARATOR_WIDE}")
    print(f"  AUDIT REPORT  —  {doc_label}")
    print(SEPARATOR_WIDE)

    # ---- Per-test lines ----
    for i, result in enumerate(results, start=1):
        verdict = result["verdict"]
        marker  = MARKERS.get(verdict, f"[{verdict}]")
        label   = _test_label(result)

        print(f"\n  {marker}  {label}")
        print(f"            Expected : {result['expected']}")
        print(f"            Actual   : {result['actual']}")
        print(f"            Reason   : {result['reason']}")

    # ---- Summary footer ----
    print(f"\n{SEPARATOR_THIN}")
    overall = "PASS" if fail_count == 0 else "FAIL"
    print(
        f"  SUMMARY  |  {total} tests  "
        f"|  {pass_count} PASS  "
        f"|  {fail_count} FAIL  "
        f"|  {na_count} N/A  "
        f"|  OVERALL: {overall}"
    )
    print(f"{SEPARATOR_WIDE}\n")

    # Return structured data — useful if main.py wants to inspect results
    return {
        "doc_label":       doc_label,
        "total":           total,
        "pass":            pass_count,
        "fail":            fail_count,
        "not_applicable":  na_count,
        "overall":         overall,
        "details":         results,  # full result list for downstream use
    }
