from typing import List, Optional
from pydantic import BaseModel

class MedicineRequest(BaseModel):
    name: str               # normalized request like "paracetamol"
    matched_name: str       # canonical name from DB (for now same as name)
    dosage: Optional[str]
    quantity: Optional[int]

class ParsedOrderResponse(BaseModel):
    original_text: str
    language: str
    translated_text: str
    medicines: List[MedicineRequest]

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None