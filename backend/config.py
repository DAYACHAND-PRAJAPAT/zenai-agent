"""
config.py
Loads all API keys and settings from environment variables (.env file).
Every other module imports its settings from here — never hardcode keys elsewhere.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file in the project root


class Settings:
    # --- Groq (fast + reasoning LLMs) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_FAST_MODEL: str = os.getenv("GROQ_FAST_MODEL", "gemma2-9b-it")
    GROQ_REASONING_MODEL: str = os.getenv("GROQ_REASONING_MODEL", "llama-3.3-70b-versatile")

    # --- Pinecone (vector DB for RAG) ---
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "zenai-knowledge-base")

    # --- Supabase (Postgres DB) ---
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # --- App config ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))

    def validate(self) -> list[str]:
        """Returns a list of missing required settings. Call this at startup."""
        missing = []
        required = {
            "GROQ_API_KEY": self.GROQ_API_KEY,
            "PINECONE_API_KEY": self.PINECONE_API_KEY,
            "SUPABASE_URL": self.SUPABASE_URL,
            "SUPABASE_KEY": self.SUPABASE_KEY,
            "DATABASE_URL": self.DATABASE_URL,
        }
        for name, value in required.items():
            if not value:
                missing.append(name)
        return missing


settings = Settings()
