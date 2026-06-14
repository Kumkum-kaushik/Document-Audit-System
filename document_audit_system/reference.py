# PURPOSE:        Provide reference standard data (expected values / pass criteria)
#                 that the validation engine compares extracted results against.
# ARCHITECTURE:   CONFIG / Reference-data layer  (loaded just before validation)
# CALLED BY:      main.py  — load_reference() is called after normalization
# CALLS NEXT:     validation.py  — the returned list is passed straight to validate()
# INPUT->OUTPUT:  doc_type string  ->  list of reference row dicts


# ===========================================================================
# HOW THE REAL SYSTEM LOADS THIS DATA
# ===========================================================================
#
# The real system reads two .ods (OpenDocument Spreadsheet) files instead of
# the hard-coded lists below.  The key call is:
#
#   import pandas as pd
#
#   df = pd.read_excel(
#       "data/reference/Standard_list_IEC_merged.ods",
#       sheet_name = "Standards",
#       engine     = "odf",   # requires the 'odfpy' package
#       header     = 1,       # ← row 2 is the header (row 1 holds approval roles)
#   )
#   emc_rows = df.to_dict(orient="records")
#
# And for the two-sheet safety file:
#
#   sheet1 = pd.read_excel("data/reference/Safety_testing_list.ods",
#                          sheet_name=0, engine="odf", header=1)
#   sheet2 = pd.read_excel("data/reference/Safety_testing_list.ods",
#                          sheet_name=1, engine="odf", header=1)
#   # JOIN on "Test Name" to attach applicability info to each Sheet1 row
#   merged = sheet1.merge(sheet2, on="Test Name", how="left")
#   safety_rows = merged.to_dict(orient="records")
#
# The skeleton below reproduces the exact same dict structure those calls
# would produce, so every downstream module works identically.
# ===========================================================================


# ---------------------------------------------------------------------------
# EMC / EMI reference data
# Mirrors rows in:  Standard_list_IEC_merged.ods  →  sheet "Standards"
#
# JOIN KEY used by validation.py:  (test_sub_type, line_type, standard_reference)
# ---------------------------------------------------------------------------
EMC_REFERENCE = [
    # EFT – Electrical Fast Transient (IEC 61000-4-4)
    {
        "test_sub_type":      "EFT",
        "line_type":          "Power",
        "standard_reference": "IEC 61000-4-4",
        "standard_test_level": "±2 kV",
        "pass_criteria":      "Class A",   # <-- validation compares against this
        "remarks":            "IEC 61326-1 Table A.1",
    },
    {
        "test_sub_type":      "EFT",
        "line_type":          "Signal",
        "standard_reference": "IEC 61000-4-4",
        "standard_test_level": "±1 kV",
        "pass_criteria":      "Class B",
        "remarks":            "IEC 61326-1 Table A.1",
    },
    # ESD – Electrostatic Discharge (IEC 61000-4-2)
    {
        "test_sub_type":      "ESD",
        "line_type":          "Contact",
        "standard_reference": "IEC 61000-4-2",
        "standard_test_level": "±4 kV",
        "pass_criteria":      "Class B",
        "remarks":            "IEC 61326-1 Table A.1",
    },
    {
        "test_sub_type":      "ESD",
        "line_type":          "Air",
        "standard_reference": "IEC 61000-4-2",
        "standard_test_level": "±8 kV",
        "pass_criteria":      "Class B",
        "remarks":            "IEC 61326-1 Table A.1",
    },
    # Surge (IEC 61000-4-5)
    {
        "test_sub_type":      "Surge",
        "line_type":          "Power",
        "standard_reference": "IEC 61000-4-5",
        "standard_test_level": "±2 kV",
        "pass_criteria":      "Class A",   # measured Class B in fake doc → FAIL
        "remarks":            "IEC 61326-1 Table A.1",
    },
    # CS – Conducted Susceptibility (IEC 61000-4-6)
    {
        "test_sub_type":      "CS",
        "line_type":          "Power",
        "standard_reference": "IEC 61000-4-6",
        "standard_test_level": "3Vrms",
        "pass_criteria":      "Class A",
        "remarks":            "IEC 61326-1 Table A.2",
    },
    # RS – Radiated Susceptibility (IEC 61000-4-3)
    {
        "test_sub_type":      "RS",
        "line_type":          "Radiated",
        "standard_reference": "IEC 61000-4-3",
        "standard_test_level": "10 V/m",
        "pass_criteria":      "Class A",   # measured Class B in fake doc → FAIL
        "remarks":            "IEC 61326-1 Table A.2",
    },
]


# ---------------------------------------------------------------------------
# Safety reference data
# Mirrors rows in:  Safety_testing_list.ods
#   Sheet1  – test names + expected observations
#   Sheet2  – applicability per product variant
#
# JOIN KEY used by validation.py:  test_name
# After joining, each row carries both the expected observation (Sheet1)
# and the applicable_to list (Sheet2).
# ---------------------------------------------------------------------------
SAFETY_REFERENCE = [
    {
        "test_name":     "Single Fault Test",
        "observation":   "No fire hazard observed",    # expected observation
        # applicable_to: variants that MUST perform this test (from Sheet2)
        "applicable_to": ["G3 Timer", "G3 Counter", "LTC9A"],
    },
    {
        "test_name":     "Bonding Impedance",
        "observation":   "Impedance < 0.1 Ohm",
        "applicable_to": ["G3 Timer", "G3 Counter"],  # LTC9A → NOT_APPLICABLE
    },
    {
        "test_name":     "Protective Impedance",
        "observation":   "Within rated safety tolerances",
        "applicable_to": ["G3 Timer", "LTC9A"],       # G3 Counter → NOT_APPLICABLE
    },
    {
        "test_name":     "Dielectric Strength",
        "observation":   "No breakdown observed",
        "applicable_to": ["G3 Timer", "G3 Counter", "LTC9A"],
    },
    {
        "test_name":     "Insulation Resistance",
        "observation":   "Resistance > 7 MOhm",
        "applicable_to": ["LTC9A"],  # G3 Timer is NOT in this list → NOT_APPLICABLE
    },
]


# ---------------------------------------------------------------------------
# load_reference() — the only function main.py calls from this module
# ---------------------------------------------------------------------------

def load_reference(doc_type):
    """
    Return the reference list for the given doc_type.

    In the real system this function would:
      1. Look up the .ods file path from PIPELINE_CONFIG in config.py.
      2. Call pd.read_excel(..., engine="odf", header=1).
      3. Return df.to_dict(orient="records").

    Here it just returns the hard-coded list above.

    Parameters
    ----------
    doc_type : str
        "emi_emc"  or  "safety"  (short label from classifier).

    Returns
    -------
    list[dict]
        One dict per reference row; keys match what validation.py expects.
    """
    if doc_type == "emi_emc":
        return EMC_REFERENCE
    elif doc_type == "safety":
        return SAFETY_REFERENCE
    else:
        raise ValueError(
            f"load_reference: no reference data registered for doc_type='{doc_type}'. "
            "Expected 'emi_emc' or 'safety'."
        )
