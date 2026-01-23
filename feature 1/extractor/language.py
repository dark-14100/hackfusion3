from typing import Literal

SupportedLanguage = Literal["en", "unknown"]

def detect_language(text: str) -> SupportedLanguage:
    """
    Very naive placeholder. Later you can plug in a model or API.
    """
    if not text:
        return "unknown"
    # For hackathon v1, assume English.
    return "en"

def translate_to_english(text: str, lang: SupportedLanguage) -> str:
    """
    If the text is not English, translate it. For now, just return text.
    In the future, call a translation API or model here.
    """
    return text or ""