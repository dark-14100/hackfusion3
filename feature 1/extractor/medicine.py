import os
from functools import lru_cache
from typing import List, Tuple, Dict

from rapidfuzz import fuzz, process

from .preprocess import normalize_text
from .product_index import product_name_list

FUZZY_THRESHOLD = 85  # 0–100, tweakable


@lru_cache(maxsize=1)
def _load_medicine_names() -> List[str]:
    """
    Load normalized product names from products-export.csv via product_index.
    """
    names: List[str] = []
    for name in product_name_list():
        names.append(normalize_text(name))
    return names


def _generate_ngrams(words: List[str], max_n: int = 3) -> List[str]:
    """
    Generate unigrams, bigrams, trigrams from user text to match
    multi-word medicines like 'paracetamol 500 mg'.
    """
    phrases: List[str] = []
    n_words = len(words)
    for n in range(1, max_n + 1):
        for i in range(n_words - n + 1):
            phrase = " ".join(words[i : i + n])
            phrases.append(phrase)
    return phrases


def extract_medicines(text: str) -> List[Tuple[str, str]]:
    """
    Fuzzy matching implementation using rapidfuzz against real product names
    from products-export.csv.

    Returns:
      List of (canonical_name, matched_phrase_in_text)
    """
    norm_text = normalize_text(text)
    if not norm_text:
        return []

    medicine_names = _load_medicine_names()
    words = norm_text.split()
    ngrams = _generate_ngrams(words, max_n=3)

    found_raw: List[Tuple[str, str, int]] = []  # (canonical, phrase, score)

    for phrase in ngrams:
        # small pre-filter: only names starting with same first char as phrase
        first = phrase[0]
        candidates = [n for n in medicine_names if n and n[0] == first] or medicine_names

        match = process.extractOne(
            phrase,
            candidates,
            scorer=fuzz.ratio,
        )
        if not match:
            continue
        canonical_name, score, _ = match
        if score >= FUZZY_THRESHOLD:
            found_raw.append((canonical_name, phrase, score))

    # Pick best-scoring phrase per canonical name
    best_by_name: Dict[str, Tuple[str, int]] = {}
    for canonical, phrase, score in found_raw:
        current = best_by_name.get(canonical)
        if current is None or score > current[1]:
            best_by_name[canonical] = (phrase, score)

    unique: List[Tuple[str, str]] = []
    for canonical, (phrase, _) in best_by_name.items():
        unique.append((canonical, phrase))

    return unique
