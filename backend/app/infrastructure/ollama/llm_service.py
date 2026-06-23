import app.core.paths  # Configures Python path for importing existing modules
import httpx
from app.config import settings

class LLMService:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL

    async def check_ollama(self) -> bool:
        """Check if Ollama server is running and reachable."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.ollama_url}/api/tags", timeout=3.0)
                return resp.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> list:
        """Get list of models installed in Ollama."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.ollama_url}/api/tags", timeout=3.0)
                if resp.status_code == 200:
                    return [m.get("name", "") for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

    async def resolve_model(self, preferred_model: str = None) -> str:
        """Resolve which model to use based on preferred name and what is installed."""
        if not preferred_model:
            preferred_model = settings.OLLAMA_MODEL
            
        models = await self.get_available_models()
        if not models:
            return ""
            
        if preferred_model in models:
            return preferred_model
            
        preferred_base = preferred_model.split(":", 1)[0].lower()
        for m in models:
            if m.lower().startswith(preferred_base):
                return m
                
        fallback_bases = ["qwen", "qwen2.5", "gemma", "llama3", "mistral", "phi3"]
        for base in fallback_bases:
            for m in models:
                if m.lower().startswith(base):
                    return m
                    
        return models[0]
