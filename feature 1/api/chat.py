from typing import List, Dict, Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from extractor import extract_order

router = APIRouter()


class ChatOrderRequest(BaseModel):
    message: str


class MedicineOut(BaseModel):
    name: str
    matched_name: str
    dosage: Optional[str]
    quantity: Optional[int]
    dosage_details: Optional[Dict[str, Any]] = None
    product_id: Optional[str] = None
    pzn: Optional[str] = None
    price_rec: Optional[float] = None
    package_size: Optional[str] = None


class ParsedOrderOut(BaseModel):
    original_text: str
    normalized_text: str
    language: str
    translated_text: str
    medicines: List[MedicineOut]
    meta: Dict[str, Any]


@router.post("/chat/order", response_model=ParsedOrderOut)
def parse_order(req: ChatOrderRequest) -> ParsedOrderOut:
    parsed = extract_order(req.message)
    # Convert dataclass to dict and then validate
    parsed_dict = {
        "original_text": parsed.original_text,
        "normalized_text": parsed.normalized_text,
        "language": parsed.language,
        "translated_text": parsed.translated_text,
        "medicines": [
            {
                "name": m.name,
                "matched_name": m.matched_name,
                "dosage": m.dosage,
                "quantity": m.quantity,
                "dosage_details": m.dosage_details,
                "product_id": m.product_id,
                "pzn": m.pzn,
                "price_rec": m.price_rec,
                "package_size": m.package_size
            }
            for m in parsed.medicines
        ],
        "meta": parsed.meta
    }
    return ParsedOrderOut.model_validate(parsed_dict)