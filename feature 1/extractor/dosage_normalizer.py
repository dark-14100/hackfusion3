# extractor/dosage_normalizer.py
from typing import Optional
from rapidfuzz import fuzz, process

CANONICAL_FORMS = [
    "tablet", "capsule", "syrup", "suspension",
    "injection", "drop",
]
CANONICAL_UNITS = [
    "day", "week", "month",
]

FUZZY_THRESHOLD_FORM = 85
FUZZY_THRESHOLD_UNIT = 85


def normalize_form_token(token: str) -> Optional[str]:
    """
    Map a potentially misspelled form token to a canonical form using fuzzy matching.
    e.g. 'tlablet' -> 'tablet'
    """
    token = token.lower().strip()
    if not token:
        return None

    match = process.extractOne(token, CANONICAL_FORMS, scorer=fuzz.ratio)
    if match:
        word, score, _ = match
        if score >= FUZZY_THRESHOLD_FORM:
            return word
    return None


def normalize_unit_token(token: str) -> Optional[str]:
    """
    Map a potentially misspelled time unit token to a canonical unit.
    e.g. 'dyas' -> 'day'
    """
    token = token.lower().strip()
    if not token:
        return None

    match = process.extractOne(token, CANONICAL_UNITS, scorer=fuzz.ratio)
    if match:
        word, score, _ = match
        if score >= FUZZY_THRESHOLD_UNIT:
            return word
    return None