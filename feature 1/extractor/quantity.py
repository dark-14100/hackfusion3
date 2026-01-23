"""Quantity extraction utilities."""

import re
from typing import Optional

# number + optional unit (digits)
QUANTITY_PATTERN = re.compile(
    r"\b(\d+)\s*(strip|strips|box|boxes|pack|packs|tablet[s]?|tab[s]?|capsule[s]?|cap[s]?|pill[s]?|dose[s]?)?\b",
    re.IGNORECASE,
)

# number words (one, two, three, etc.)
NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

WORD_QUANTITY_PATTERN = re.compile(
    r"\b(" + "|".join(NUMBER_WORDS.keys()) + r")\s*(strip|strips|box|boxes|pack|packs|tablet[s]?|tab[s]?|capsule[s]?|cap[s]?|pill[s]?|dose[s]?)?\b",
    re.IGNORECASE,
)

WINDOW_SIZE = 40


def _extract_digit_quantity(window: str) -> Optional[int]:
    for match in QUANTITY_PATTERN.finditer(window):
        num_str = match.group(1)
        try:
            return int(num_str)
        except ValueError:
            continue
    return None


def _extract_word_quantity(window: str) -> Optional[int]:
    for match in WORD_QUANTITY_PATTERN.finditer(window):
        word = match.group(1).lower()
        value = NUMBER_WORDS.get(word)
        if value is not None:
            return value
    return None


def _extract_in_window(text: str, start_idx: int, end_idx: int) -> Optional[int]:
    window_start = max(0, start_idx - WINDOW_SIZE)
    window_end = min(len(text), end_idx + WINDOW_SIZE)
    window = text[window_start:window_end]

    # Prefer explicit digits if present
    qty = _extract_digit_quantity(window)
    if qty is not None:
        return qty

    # Fallback: number words
    qty = _extract_word_quantity(window)
    if qty is not None:
        return qty

    return None


def extract_quantity(text: str, medicine_name: str) -> Optional[int]:
    if not text:
        return None

    lowered = text.lower()
    med_lower = medicine_name.lower()

    idx = lowered.find(med_lower)
    if idx != -1:
        qty = _extract_in_window(lowered, idx, idx + len(med_lower))
        if qty is not None:
            return qty

    # Fallback: any quantity in the entire text
    qty = _extract_digit_quantity(lowered)
    if qty is not None:
        return qty

    qty = _extract_word_quantity(lowered)
    if qty is not None:
        return qty

    return None