from typing import Optional

def speech_to_text(audio_bytes: bytes) -> Optional[str]:
    """
    Temporary STT mock.

    For hackathon v1, we assume the uploaded 'audio' is actually UTF-8 text.
    This lets us test the voice pipeline end-to-end without a real STT model.
    """
    if not audio_bytes:
        return None

    try:
        text = audio_bytes.decode("utf-8").strip()
        return text or None
    except UnicodeDecodeError:
        return None