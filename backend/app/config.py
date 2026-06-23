import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kerala Police Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    
    # JWT Auth — override with a long random string in production!
    SECRET_KEY: str = "secret-key-keep-it-safe-and-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours (single shift)
    
    # Databases
    # Defaults to SQLite locally for easy testing without PG setup
    DATABASE_URL: str = "sqlite+aiosqlite:///./kpip.db"
    
    NEO4J_URI: str = "bolt://127.0.0.1:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "prosecutorreport"
    
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen:8b"
    
    # Model Cache Paths for Air-Gapped Intranet Environments
    NER_MODEL_PATH: str = "dslim/bert-base-NER"
    TRANSLATION_MODEL_PATH: str = "ai4bharat/indictrans2-indic-en-1B"
    SENTENCE_TRANSFORMER_MODEL_PATH: str = "all-MiniLM-L6-v2"
    DISABLE_INDIC_TRANS: str = "0"
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:5174",  # Vite dev server (fallback port)
        "http://localhost:5175",  # Vite dev server (fallback port 2)
        "http://localhost:5176",  # Vite dev server (fallback port 3)
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        raise ValueError(v)

    # Directories
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
    )

    # PP Form template directory — set PP_DIR env var to point to your local
    # "PP & Uo Note Dummy" folder. Leave empty to disable PP/UO Note features.
    PP_DIR: str = ""

    # PP_TEMPLATE is derived from PP_DIR at runtime (see below)
    PP_TEMPLATE: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()

# Derive PP_TEMPLATE from PP_DIR if not explicitly set
if settings.PP_DIR and not settings.PP_TEMPLATE:
    settings.PP_TEMPLATE = os.path.join(settings.PP_DIR, "PP Form details.docx")

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
if settings.PP_DIR:
    os.makedirs(settings.PP_DIR, exist_ok=True)
