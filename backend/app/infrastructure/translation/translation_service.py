import app.core.paths  # Configures Python path for importing existing modules
from app.infrastructure.documents.utils import translate_ml_to_en, is_malayalam
from app.config import settings

class TranslationService:
    def is_malayalam(self, text: str) -> bool:
        """Check if the text contains Malayalam characters."""
        return is_malayalam(text)

    def translate(self, text: str, use_ollama: bool = False, batch_engines: list = None) -> str:
        """Translate Malayalam text to English using IndicTrans2 / Google Translate fallback."""
        return translate_ml_to_en(
            text,
            use_ollama=use_ollama,
            ollama_url=settings.OLLAMA_URL,
            batch_engines=batch_engines
        )
