# PURPOSE:        Inspect a document and decide which verification track it belongs to.
# ARCHITECTURE:   CLASSIFICATION  (first stage after the document enters the pipeline)
# CALLED BY:      main.py  — called as the very first pipeline step
# CALLS NEXT:     main.py then calls select_extractor() in extractors.py
# INPUT->OUTPUT:  document dict  ->  "emi_emc"  |  "safety"


def classify_document(doc):
    """
    Return the short document-type label used by every downstream stage.

    Real-system equivalent
    ----------------------
    The real classifier opens the PDF with pdfplumber, extracts the first
    two pages of text, and looks for keyword signals:

        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = " ".join(p.extract_text() or "" for p in pdf.pages[:2])

        if "IEC 61326" in text or "EMI" in text or "EMC" in text:
            return "emi_emc"
        elif "safety" in text.lower() or "IEC 62368" in text:
            return "safety"

    Skeleton behaviour
    ------------------
    We simply inspect the 'type' key in the fake document dict.
    The logic mirrors what keyword matching would produce.
    """

    doc_type_str = doc.get("type", "").lower()

    # Keywords that signal the EMC/EMI verification track
    emc_signals = {"emc", "emi", "emi_emc", "emi_emc_report"}
    if any(sig in doc_type_str for sig in emc_signals):
        return "emi_emc"

    # Keywords that signal the safety verification track
    safety_signals = {"safety", "safety_report"}
    if any(sig in doc_type_str for sig in safety_signals):
        return "safety"

    # If neither track matched, the pipeline cannot continue
    raise ValueError(
        f"classify_document: cannot determine track for doc type='{doc_type_str}'. "
        "Expected 'emi_emc' or 'safety' somewhere in the type field."
    )
