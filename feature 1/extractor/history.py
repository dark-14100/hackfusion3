# extractor/history.py
import csv
import os
from functools import lru_cache
from typing import Dict, List, TypedDict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_CSV = os.path.join(DATA_DIR, "Consumer Order History 1.csv")

class HistoryRow(TypedDict):
    patient_id: str
    age: int
    gender: str
    purchase_date: str
    product_name: str
    quantity: int
    total_price_eur: float
    dosage_frequency: str
    prescription_required: bool

@lru_cache(maxsize=1)
def load_history() -> Dict[str, List[HistoryRow]]:
    by_patient: Dict[str, List[HistoryRow]] = {}

    with open(HISTORY_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qty = int(row["Quantity"])
            except ValueError:
                qty = 0
            try:
                total_price = float(str(row["Total Price (EUR)"]).replace(",", "."))
            except ValueError:
                total_price = 0.0

            rec: HistoryRow = {
                "patient_id": row["Patient ID"].strip(),
                "age": int(row["Patient Age"]),
                "gender": row["Patient Gender"].strip(),
                "purchase_date": row["Purchase Date"].strip(),
                "product_name": row["Product Name"].strip(),
                "quantity": qty,
                "total_price_eur": total_price,
                "dosage_frequency": row["Dosage Frequency"].strip(),
                "prescription_required": row["Prescription Required"].strip().lower() == "yes",
            }
            by_patient.setdefault(rec["patient_id"], []).append(rec)

    return by_patient

def get_history_for_patient(patient_id: str) -> List[HistoryRow]:
    return load_history().get(patient_id, [])