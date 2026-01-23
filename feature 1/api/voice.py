from fastapi import APIRouter, UploadFile, File, HTTPException
from extractor import extract_order
from voice.stt import speech_to_text

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/order")
async def voice_order(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    text = speech_to_text(audio_bytes)
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio")
    parsed = extract_order(text)
    return {
        "transcript": text,
        "parsed": {
            "original_text": parsed.original_text,
            "language": parsed.language,
            "translated_text": parsed.translated_text,
            "medicines": [
                {
                    "name": m.name,
                    "matched_name": m.matched_name,
                    "dosage": m.dosage,
                    "quantity": m.quantity,
                }
                for m in parsed.medicines
            ],
        },
    }