import csv
import os
from functools import lru_cache
from typing import Dict, List, TypedDict, Optional

from rapidfuzz import fuzz, process

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PRODUCTS_CSV = os.path.join(DATA_DIR, "products-export.csv")


class Product(TypedDict):
    product_id: str
    name: str
    name_normalized: str
    pzn: str
    price_rec: float
    package_size: str
    description: str


def _normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())


@lru_cache(maxsize=1)
def load_products() -> List[Product]:
    products: List[Product] = []
    with open(PRODUCTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_name = row["product name"].strip()
            try:
                price = float(str(row["price rec"]).replace(",", "."))
            except ValueError:
                price = 0.0

            products.append(
                {
                    "product_id": str(row["product id"]).strip(),
                    "name": raw_name,
                    "name_normalized": _normalize_name(raw_name),
                    "pzn": str(row["pzn"]).strip(),
                    "price_rec": price,
                    "package_size": str(row["package size"]).strip(),
                    "description": row.get("descriptions", "").strip(),
                }
            )
    return products


@lru_cache(maxsize=1)
def product_name_list() -> List[str]:
    return [p["name"] for p in load_products()]


def find_product_by_name(canonical_name: str) -> Optional[Dict[str, object]]:
    """
    Exact normalized match; used by the rule-based path.
    """
    norm = _normalize_name(canonical_name)
    for p in load_products():
        if p["name_normalized"] == norm:
            return p
    return None


def find_best_product_for_name(name: str, threshold: int = 50) -> Optional[Product]:
    """
    Fuzzy-match an arbitrary name (e.g. from LLM) directly against all product
    names from products-export.csv and return the best row.

    Uses token_set_ratio so that short generic names can match longer
    branded product names.
    """
    if not name:
        return None

    names = product_name_list()
    if not names:
        return None

    # We compare lowercased strings but keep the original index
    lowered = [n.lower() for n in names]

    match = process.extractOne(
        name.lower(),
        lowered,
        scorer=fuzz.token_set_ratio,   # better for subset/superset matches
    )
    if not match:
        print("BEST MATCH DEBUG: no match for", repr(name))
        return None

    _, score, idx = match
    print("BEST MATCH DEBUG:", "query=", repr(name), "score=", score, "matched=", repr(names[idx]))

    if score < threshold:
        return None

    return load_products()[idx]