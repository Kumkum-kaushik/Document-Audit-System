# PURPOSE:        Central configuration — maps each verification track to its
#                 pipeline components (extractor key, ruleset key, reference key).
# ARCHITECTURE:   CONFIG
# CALLED BY:      main.py, extractors.py (select_extractor reads extractor key),
#                 reference.py (load_reference reads reference key)
# CALLS NEXT:     Nothing — this is a pure data module, imported by others.
# INPUT->OUTPUT:  N/A (module-level constants; no function call needed)

# ---------------------------------------------------------------------------
# PIPELINE_CONFIG
#   Top-level dict with one entry per verification track.
#   Each entry tells the pipeline:
#     "extractor"  -> which key to pass to select_extractor()  in extractors.py
#     "ruleset"    -> which validation logic to use            in validation.py
#     "reference"  -> which dataset to load                    in reference.py
# ---------------------------------------------------------------------------
# learning source control
#lenarn learn
PIPELINE_CONFIG = {
    "emi_emc_verification": {
        "extractor":  "emi_emc",       # -> extract_emi_emc() in extractors.py
        "ruleset":    "emi_emc_rules", # -> _validate_emi_emc() in validation.py
        "reference":  "emi_emc",       # -> EMC_REFERENCE list  in reference.py
    },
    "safety_verification": {
        "extractor":  "safety",        # -> extract_safety() in extractors.py
        "ruleset":    "safety_rules",  # -> _validate_safety() in validation.py
        "reference":  "safety",        # -> SAFETY_REFERENCE list in reference.py
    },
}

# ---------------------------------------------------------------------------
# DOC_TYPE_TO_CONFIG
#   The classifier returns short labels ("emi_emc", "safety").
#   This mapping bridges those labels to the full config key above.
#   Used by main.py after classify_document() returns.
# ---------------------------------------------------------------------------
DOC_TYPE_TO_CONFIG = {
    "emi_emc": "emi_emc_verification",
    "safety":  "safety_verification",
}
