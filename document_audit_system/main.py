# PURPOSE:        Wire every pipeline stage together and run the full audit
#                 for two hardcoded fake documents (one EMC, one Safety).
# ARCHITECTURE:   Entry point  —  orchestrates all other modules in sequence
# CALLED BY:      User:  python main.py
# CALLS NEXT:     classifier -> extractors -> normalizer -> reference
#                             -> validation -> reporting  (in that order)
# INPUT->OUTPUT:  hardcoded fake docs  ->  printed audit summaries for both

# ---------------------------------------------------------------------------
# Pipeline imports — one import per stage, in pipeline order
# ---------------------------------------------------------------------------
from classifier  import classify_document   # Stage 1: CLASSIFICATION
from extractors  import select_extractor    # Stage 2: EXTRACTION (factory)
from normalizer  import normalize           # Stage 3: NORMALIZATION
from reference   import load_reference      # Stage 4: REFERENCE DATA
from validation  import validate            # Stage 5: VALIDATION
from reporting   import generate_report     # Stage 6: REPORTING


# ===========================================================================
# FAKE DOCUMENT 1 — EMC / EMI Test Report
# ===========================================================================
# In the real system this would be a file path:
#   doc = {"path": "data/sample_pdfs/emc_report.pdf", "type": "emi_emc_report"}
# pdfplumber would read it; the extractor would pull the table rows.
#
# Here we embed the records directly so the skeleton runs without any file I/O.
# The records below deliberately include a mix of PASS and FAIL values.
# ===========================================================================
EMC_DOC = {
    "type":  "emi_emc_report",
    "title": "EMC Test Report — G3 Timer (IEC 61326-1)",
    "records": [
        # --- PASS: measured Class A matches reference Class A ---
        {
            "test_sub_type":      "EFT",
            "line_type":          "Power",
            "standard_reference": "IEC 61000-4-4",
            "measured_level":     "±2 kV",
            "measured_class":     "Class A",
        },
        # --- FAIL: Surge requires Class A but device measured Class B ---
        {
            "test_sub_type":      "Surge",
            "line_type":          "Power",
            "standard_reference": "IEC 61000-4-5",
            "measured_level":     "±2 kV",
            "measured_class":     "Class B",   # <-- deliberate fail
        },
        # --- PASS: ESD Contact requires Class B, measured Class B ---
        {
            "test_sub_type":      "ESD",
            "line_type":          "Contact",
            "standard_reference": "IEC 61000-4-2",
            "measured_level":     "±4 kV",
            "measured_class":     "Class B",
        },
        # --- PASS: CS requires Class A, measured Class A ---
        {
            "test_sub_type":      "CS",
            "line_type":          "Power",
            "standard_reference": "IEC 61000-4-6",
            "measured_level":     "3Vrms",
            "measured_class":     "Class A",
        },
        # --- FAIL: RS requires Class A but device only achieved Class B ---
        {
            "test_sub_type":      "RS",
            "line_type":          "Radiated",
            "standard_reference": "IEC 61000-4-3",
            "measured_level":     "10 V/m",
            "measured_class":     "Class B",   # <-- deliberate fail
        },
    ],
}


# ===========================================================================
# FAKE DOCUMENT 2 — Safety Test Report for variant "G3 Timer"
# ===========================================================================
# product_variant drives the applicability gate in safety validation.
# "Insulation Resistance" is only required for LTC9A, so it will be
# graded NOT_APPLICABLE for G3 Timer even though a result was observed.
# ===========================================================================
SAFETY_DOC = {
    "type":            "safety_report",
    "title":           "Safety Test Report — G3 Timer",
    "product_variant": "G3 Timer",
    "records": [
        # --- PASS ---
        {"test_name": "Single Fault Test",    "observed_result": "No fire hazard observed"},
        # --- PASS ---
        {"test_name": "Bonding Impedance",    "observed_result": "Impedance < 0.1 Ohm"},
        # --- FAIL: wrong observation text ---
        {"test_name": "Protective Impedance", "observed_result": "Slightly out of tolerance"},
        # --- PASS ---
        {"test_name": "Dielectric Strength",  "observed_result": "No breakdown observed"},
        # --- NOT_APPLICABLE: G3 Timer is not in applicable_to for this test ---
        {"test_name": "Insulation Resistance","observed_result": "Resistance > 7 MOhm"},
    ],
}


# ===========================================================================
# run_pipeline()
# ===========================================================================
# This function is the beating heart of the onboarding demo.
# Read it top to bottom to follow exactly how data moves through the system.
# ===========================================================================

def run_pipeline(doc):
    """
    Execute the full 6-stage audit pipeline for a single document dict.

    Each step prints a one-line trace so you can see what's happening
    at every stage without opening the individual modules.

    Returns the summary dict from generate_report() (counts + details).
    """

    print(f"\n{'>'*3}  Processing: {doc.get('title', 'Unknown document')}")

    # ------------------------------------------------------------------
    # STAGE 1 — CLASSIFY
    # Input:  raw document dict
    # Output: short string label — "emi_emc" | "safety"
    # ------------------------------------------------------------------
    doc_type = classify_document(doc)
    print(f"  [1] Classifier     -> doc_type = '{doc_type}'")

    # ------------------------------------------------------------------
    # STAGE 2 — SELECT EXTRACTOR  (factory lookup)
    # Input:  doc_type string
    # Output: extractor function (e.g. extract_emi_emc)
    # ------------------------------------------------------------------
    extractor_fn = select_extractor(doc_type)
    print(f"  [2] Extractor      -> selected '{extractor_fn.__name__}'")

    # ------------------------------------------------------------------
    # STAGE 3 — EXTRACT  (call the selected extractor)
    # Input:  raw document dict
    # Output: list of raw record dicts
    # ------------------------------------------------------------------
    raw_records = extractor_fn(doc)
    print(f"  [3] Extraction     -> {len(raw_records)} raw records extracted")

    # ------------------------------------------------------------------
    # STAGE 4 — NORMALIZE
    # Input:  list of raw record dicts (strings like "±2 kV", "class b")
    # Output: list of normalized record dicts (parsed values, canonical strings)
    # ------------------------------------------------------------------
    normalized_records = normalize(raw_records)
    print(f"  [4] Normalization  -> {len(normalized_records)} records normalized")

    # ------------------------------------------------------------------
    # STAGE 5 — LOAD REFERENCE DATA
    # Input:  doc_type string
    # Output: list of reference row dicts
    #
    # Real system: pd.read_excel(..., engine="odf", header=1)
    # ------------------------------------------------------------------
    reference_rows = load_reference(doc_type)
    print(f"  [5] Reference      -> {len(reference_rows)} reference rows loaded")

    # ------------------------------------------------------------------
    # STAGE 6 — VALIDATE
    # Input:  normalized records + reference rows + doc_type
    # Output: list of result dicts with PASS/FAIL/NOT_APPLICABLE verdicts
    # ------------------------------------------------------------------
    product_variant = doc.get("product_variant")  # None for EMC docs
    results = validate(normalized_records, reference_rows, doc_type, product_variant)
    print(f"  [6] Validation     -> {len(results)} test verdicts produced")

    # ------------------------------------------------------------------
    # STAGE 7 — GENERATE REPORT  (terminal stage)
    # Input:  results list
    # Output: printed audit summary  +  returned summary dict
    # ------------------------------------------------------------------
    summary = generate_report(results, doc_label=doc.get("title", doc_type))

    return summary


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  DOCUMENT AUDIT SYSTEM  —  Onboarding Demo")
    print("  Running two fake documents through the full pipeline")
    print("=" * 65)

    emc_summary    = run_pipeline(EMC_DOC)
    safety_summary = run_pipeline(SAFETY_DOC)

    # Final cross-document overview
    print("FINAL OVERVIEW")
    print("-" * 40)
    for s in (emc_summary, safety_summary):
        print(
            f"  {s['doc_label'][:45]:<45}  "
            f"{s['pass']}P / {s['fail']}F / {s['not_applicable']}N/A  "
            f"-> {s['overall']}"
        )
    print()
