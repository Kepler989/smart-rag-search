"""
Application configuration using Pydantic Settings.
Loads from environment variables / .env file.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql+asyncpg://raguser:ragpassword@localhost:5432/ragdb"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 3600

    # --- Google Gemini ---
    google_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    llm_model: str = "gemini-2.5-flash"

    # --- RAG Configuration ---
    top_k_results: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 150

    # --- App ---
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,https://smart-rag-search-uxhg-five.vercel.app"

    # --- File Upload ---
    max_file_size_mb: int = 50
    upload_dir: str = "./uploads"

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
