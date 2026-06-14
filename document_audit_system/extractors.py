# PURPOSE:        Pull structured test records out of a document for each track.
# ARCHITECTURE:   EXTRACTION  (second pipeline stage, after classification)
# CALLED BY:      main.py  — after classify_document() returns the doc_type
# CALLS NEXT:     normalizer.py  — main.py passes extracted records to normalize()
# INPUT->OUTPUT:  document dict  ->  list of raw record dicts
#                 (one dict per test row, keys vary by track — see each function)


# ---------------------------------------------------------------------------
# EMC / EMI extractor
# ---------------------------------------------------------------------------

def extract_emi_emc(doc):
    """
    Extract raw EMC test records from the document.

    Real-system equivalent
    ----------------------
    Uses pdfplumber to locate the results table in the PDF, then iterates
    table rows and converts each to a dict:

        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            table = pdf.pages[2].extract_table()   # page index may vary
        headers = table[0]
        records = [dict(zip(headers, row)) for row in table[1:]]

    Each raw record would look like:
        {
          "test_sub_type":      "EFT",
          "line_type":          "Power",
          "standard_reference": "IEC 61000-4-4",
          "measured_level":     "±2 kV",   # raw string, not yet parsed
          "measured_class":     "class a", # raw string, may have casing issues
        }

    Skeleton behaviour
    ------------------
    The fake doc already has a 'records' list baked in (see main.py).
    We just return it so downstream stages receive the same shape of data.
    """
    records = doc.get("records", [])

    # Sanity check: warn if expected fields are missing from any row
    required_fields = {"test_sub_type", "line_type", "standard_reference",
                       "measured_level", "measured_class"}
    for i, rec in enumerate(records):
        missing = required_fields - rec.keys()
        if missing:
            print(f"  [extractor WARNING] EMC record {i} missing fields: {missing}")

    return records


# ---------------------------------------------------------------------------
# Safety extractor
# ---------------------------------------------------------------------------

def extract_safety(doc):
    """
    Extract raw safety test records from the document.

    Real-system equivalent
    ----------------------
    Similar pdfplumber approach, but safety reports use a two-column layout
    (Test Name | Observation), so extraction targets a different table region.

    Each raw record would look like:
        {
          "test_name":       "Single Fault Test",
          "observed_result": "No fire hazard observed",  # raw string
        }

    Skeleton behaviour
    ------------------
    Same as extract_emi_emc: returns the pre-baked 'records' list from the doc.
    """
    records = doc.get("records", [])

    required_fields = {"test_name", "observed_result"}
    for i, rec in enumerate(records):
        missing = required_fields - rec.keys()
        if missing:
            print(f"  [extractor WARNING] Safety record {i} missing fields: {missing}")

    return records


# ---------------------------------------------------------------------------
# Factory: select_extractor
# ---------------------------------------------------------------------------

# Registry maps the short doc_type label (from classifier) to an extractor fn.
# In the real system this dict is built dynamically from PIPELINE_CONFIG in config.py.
_EXTRACTOR_REGISTRY = {
    "emi_emc": extract_emi_emc,
    "safety":  extract_safety,
}


def select_extractor(doc_type):
    """
    Return the extractor function registered for doc_type.

    This is the "factory" step: the pipeline never hard-codes which extractor
    to use — it always routes through this function so that adding a new
    document type only requires:
      1. Writing a new extract_*() function above.
      2. Adding it to _EXTRACTOR_REGISTRY.

    Parameters
    ----------
    doc_type : str
        Short label returned by classify_document() — "emi_emc" or "safety".

    Returns
    -------
    callable
        The extractor function. main.py then calls  records = extractor(doc).
    """
    if doc_type not in _EXTRACTOR_REGISTRY:
        raise ValueError(
            f"select_extractor: no extractor registered for doc_type='{doc_type}'. "
            f"Registered types: {list(_EXTRACTOR_REGISTRY.keys())}"
        )
    return _EXTRACTOR_REGISTRY[doc_type]
