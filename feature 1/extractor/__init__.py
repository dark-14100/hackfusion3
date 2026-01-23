from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from .preprocess import normalize_text
from .language import detect_language, translate_to_english
from .medicine import extract_medicines
from .dosage import extract_dosage
from .quantity import extract_quantity
from .llm_parser import llm_extract_order
from .product_index import find_product_by_name, find_best_product_for_name


@dataclass
class MedicineRequest:
    name: str
    matched_name: str                 # what user typed (maybe with typos)
    dosage: Optional[str]             # human‑friendly string
    quantity: Optional[int]
    dosage_details: Optional[Dict] = None  # full structured info
    product_id: Optional[str] = None
    pzn: Optional[str] = None
    price_rec: Optional[float] = None
    package_size: Optional[str] = None


@dataclass
class ParsedOrder:
    original_text: str
    normalized_text: str
    language: str
    translated_text: str
    medicines: List[MedicineRequest]
    meta: Dict


def _is_low_confidence(parsed: ParsedOrder) -> bool:
    """
    Heuristic: call LLM if we found no medicines, or if for all medicines
    we lack either dosage or quantity or any duration/frequency.
    """
    if not parsed.medicines:
        return True

    for m in parsed.medicines:
        has_dosage = bool(m.dosage)
        has_quantity = m.quantity is not None
        has_details = bool(
            m.dosage_details
            and (
                m.dosage_details.get("frequency")
                or m.dosage_details.get("duration")
            )
        )

        if has_dosage and has_quantity and has_details:
            return False

    return True


def _merge_llm_result(parsed: ParsedOrder, llm_data: Dict[str, Any]) -> ParsedOrder:
    """
    Replace parsed.medicines with LLM-derived medicines.

    For each LLM medicine:
    - Take m["canonical_name"] (whatever the model says)
    - Fuzzy-match it directly against all product names from products-export.csv
    - Use that product row (if good enough match) to fill product_id, pzn, etc.
    """
    llm_meds = llm_data.get("medicines", [])
    if not llm_meds:
        return parsed

    new_meds: List[MedicineRequest] = []

    for m in llm_meds:
        raw_name = m.get("raw_name") or ""
        canonical = m.get("canonical_name") or raw_name  # name from LLM
        strength = m.get("strength")
        form = m.get("form")
        frequency = m.get("frequency")
        duration = m.get("duration")
        quantity = m.get("quantity")

        # Build dosage string from LLM fields
        parts: List[str] = []
        if strength:
            parts.append(str(strength))
        if form:
            parts.append(str(form))
        if frequency:
            parts.append(str(frequency))
        if duration:
            parts.append(f"for {duration}")
        dosage_str = " ".join(parts) if parts else None

        dosage_details = {
            "raw": dosage_str,
            "strength": strength,
            "form": form,
            "frequency": frequency,
            "duration": duration,
        }

        # Directly match LLM name into CSV using fuzzy search
        product = find_best_product_for_name(canonical)
        catalog_name = product["name"] if product else canonical

        # DEBUG
        print(
            "LLM DEBUG:",
            "canonical=", repr(canonical),
            "→ catalog_name=", repr(catalog_name),
            "product=", product,
        )

        new_meds.append(
            MedicineRequest(
                name=catalog_name,
                matched_name=raw_name,
                dosage=dosage_str,
                quantity=quantity,
                dosage_details=dosage_details,
                product_id=product["product_id"] if product else None,
                pzn=product["pzn"] if product else None,
                price_rec=product["price_rec"] if product else None,
                package_size=product["package_size"] if product else None,
            )
        )

    parsed.medicines = new_meds
    return parsed

def extract_order(text: str) -> ParsedOrder:
    """
    Main entry point used by the FastAPI route.
    """
    original_text = text or ""
    normalized = normalize_text(original_text)

    lang = detect_language(original_text)
    translated = translate_to_english(original_text, lang)
    work_text = normalize_text(translated)

    # 1) Rule-based extraction
    meds = extract_medicines(work_text)  # [(canonical, matched_phrase)]
    results: List[MedicineRequest] = []

    for canonical_name, matched_phrase in meds:
        dosage_info = extract_dosage(work_text, canonical_name)
        dosage_str = dosage_info.get("raw") if dosage_info else None
        qty = extract_quantity(work_text, canonical_name)

        product = find_product_by_name(canonical_name)

        # DEBUG
        print(
            "RULE DEBUG:",
            "canonical_name=", repr(canonical_name),
            "product=", product,
        )

        results.append(
            MedicineRequest(
                name=canonical_name,
                matched_name=matched_phrase,
                dosage=dosage_str,
                quantity=qty,
                dosage_details=dosage_info,
                product_id=product["product_id"] if product else None,
                pzn=product["pzn"] if product else None,
                price_rec=product["price_rec"] if product else None,
                package_size=product["package_size"] if product else None,
            )
        )

    parsed = ParsedOrder(
        original_text=original_text,
        normalized_text=normalized,
        language=lang,
        translated_text=translated,
        medicines=results,
        meta={},
    )

    # 2) LLM fallback (assumes Ollama is running)
    if _is_low_confidence(parsed):
        llm_data = llm_extract_order(original_text)
        parsed = _merge_llm_result(parsed, llm_data)

    return parsed