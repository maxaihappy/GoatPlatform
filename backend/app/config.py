"""Application configuration from environment."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Settings loaded from environment."""

    # API (Cloud Run sets PORT; we use it when present)
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def port(self) -> int:
        """Port to bind (Cloud Run sets PORT)."""
        return int(os.environ.get("PORT", self.api_port))

    # OpenAI (script generation, thumbnail if using DALL-E)
    openai_api_key: Optional[str] = None
    use_mock_script: bool = False  # If True, use hardcoded script for local testing without API key

    # ElevenLabs (voice commentary)
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"  # Adam-style default

    # Runway / video generation (optional; use placeholder if not set)
    runway_api_key: Optional[str] = None
    use_placeholder_clips: bool = True  # Use stock/placeholder when no Runway key

    # YouTube Data API
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    youtube_upload_enabled: bool = False  # Only upload when credentials + flag set

    # Storage (local or S3-style; for clips and final video)
    storage_path: str = "./storage"
    output_path: str = "./output"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
