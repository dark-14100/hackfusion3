import re
from typing import Optional, Dict, Any

from .dosage_normalizer import normalize_form_token, normalize_unit_token

WINDOW_SIZE = 60  # characters around medicine mention

# --- patterns ---

# 1) Strength: number + unit, e.g. "500 mg"
STRENGTH_PATTERN = re.compile(
    r"\b(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|mcg|g|ml)\b",
    re.IGNORECASE,
)

# 1b) Fallback: plain number, e.g. "650" (we'll assume mg)
STRENGTH_NUMBER_ONLY_PATTERN = re.compile(
    r"\b(?P<amount>\d{2,4})\b"
)

# 2) Form: capture a word, we will normalize by fuzzy matching
FORM_PATTERN = re.compile(
    r"\b(?P<form>\w{4,12})\b",  # broad; e.g. "tablet", "tlablet"
    re.IGNORECASE,
)

# 3) Frequency patterns
FREQ_NL_PATTERN = re.compile(
    r"\b(?P<count>once|twice|thrice|\d+\s*(?:time|times))\s*(?:a|per)?\s*(?:day|daily)\b",
    re.IGNORECASE,
)

FREQ_INTERVAL_PATTERN = re.compile(
    r"\b(?:q\s*(?P<q_hours>\d+)\s*h|every\s*(?P<every_hours>\d+)\s*(?:hour|hours|hr|hrs))\b",
    re.IGNORECASE,
)

FREQ_TIME_OF_DAY_PATTERN = re.compile(
    r"\b(at night|before bed|in the morning|at bedtime|after dinner|before breakfast)\b",
    re.IGNORECASE,
)

# 4) Duration: "for 5 days", "x 3 weeks", etc. Unit will be normalized.
DURATION_PATTERN = re.compile(
    r"\b(?:for|x)\s*(?P<num>\d+)\s*(?P<Unit>\w{3,10})\b",
    re.IGNORECASE,
)


def _find_first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0) if m else None


def _parse_strength(text: str) -> Optional[str]:
    # First try number + unit (e.g., "500 mg")
    m = STRENGTH_PATTERN.search(text)
    if m:
        return f"{m.group('amount')}{m.group('unit').lower()}"

    # Fallback: plain number near context, assume mg (e.g., "650")
    m2 = STRENGTH_NUMBER_ONLY_PATTERN.search(text)
    if m2:
        amount = m2.group("amount")
        return f"{amount}mg"

    return None


def _parse_form(text: str) -> Optional[str]:
    """
    Extract and normalize dosage form (tablet, capsule, etc.).
    Uses fuzzy normalization so 'tlablet' -> 'tablet'.
    """
    m = FORM_PATTERN.search(text)
    if not m:
        return None

    raw = m.group("form").lower()
    normalized = normalize_form_token(raw)
    return normalized  # could return raw if you want fallback


def _parse_frequency(text: str) -> Optional[str]:
    parts = []

    nl = _find_first(FREQ_NL_PATTERN, text)
    if nl:
        parts.append(nl.lower())

    interval = FREQ_INTERVAL_PATTERN.search(text)
    if interval:
        if interval.group("q_hours"):
            parts.append(f"every {interval.group('q_hours')}h")
        elif interval.group("every_hours"):
            parts.append(f"every {interval.group('every_hours')}h")

    tod = _find_first(FREQ_TIME_OF_DAY_PATTERN, text)
    if tod:
        parts.append(tod.lower())

    if not parts:
        return None

    # De‑duplicate while preserving order
    seen = set()
    uniq = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return ", ".join(uniq)


def _parse_duration(text: str) -> Optional[str]:
    """
    Extract and normalize duration like "for 5 days", "x 3 weeks".
    Uses fuzzy normalization for the unit, so "dyas" -> "day" -> "5 days".
    """
    m = DURATION_PATTERN.search(text)
    if not m:
        return None

    num = m.group("num")
    raw_unit = m.group("Unit").lower()

    unit = normalize_unit_token(raw_unit)
    if not unit:
        return None

    # pluralize when needed
    if num == "1":
        return f"{num} {unit}"
    else:
        return f"{num} {unit}s"


def _build_raw_text(
    strength: Optional[str],
    form: Optional[str],
    frequency: Optional[str],
    duration: Optional[str],
) -> Optional[str]:
    parts = []
    if strength:
        parts.append(strength)
    if form:
        parts.append(form)
    if frequency:
        parts.append(frequency)
    if duration:
        parts.append(f"for {duration}")
    if not parts:
        return None
    return " ".join(parts)


def _extract_in_window(text: str) -> Dict[str, Any]:
    strength = _parse_strength(text)
    form = _parse_form(text)
    frequency = _parse_frequency(text)
    duration = _parse_duration(text)
    raw = _build_raw_text(strength, form, frequency, duration)

    return {
        "raw": raw,
        "strength": strength,
        "form": form,
        "frequency": frequency,
        "duration": duration,
    }


def extract_dosage(text: str, medicine_name: str) -> Optional[Dict[str, Any]]:
    """
    Full‑fledged dosage extraction.

    Returns dict:
    {
        "raw": "500mg tablet twice a day for 5 days",
        "strength": "500mg",
        "form": "tablet",
        "frequency": "twice a day",
        "duration": "5 days"
    }
    """
    if not text:
        return None

    lowered = text.lower()
    med_lower = medicine_name.lower()

    idx = lowered.find(med_lower)
    if idx != -1:
        start = max(0, idx - WINDOW_SIZE)
        end = min(len(text), idx + len(med_lower) + WINDOW_SIZE)
        window = text[start:end]
        details = _extract_in_window(window)
        if any(details.values()):
            return details

    # Fallback: whole text
    details = _extract_in_window(text)
    if any(details.values()):
        return details

    return None