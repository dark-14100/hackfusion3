# Feature 1 - Prescription Extraction API

This module contains a FastAPI-based service for extracting structured information (medicine name, dosage, quantity, etc.) from raw prescription text.

## Structure

- `main.py` – FastAPI app and HTTP endpoints
- `extractor/` – text preprocessing and extraction logic
- `data/medicines.csv` – list of known medicine names
- `schemas.py` – Pydantic models for request/response
- `requirements.txt` – Python dependencies for this feature
