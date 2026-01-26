"""
Application configuration using Pydantic Settings
Works with:
- Local .env files
- Railway system environment variables
"""

import os
import json
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "Cabin Rentals API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ------------------------------------------------------------------
    # Supabase
    # ------------------------------------------------------------------
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ------------------------------------------------------------------
    # Drupal Database (optional)
    # ------------------------------------------------------------------
    DRUPAL_DB_HOST: str = ""
    DRUPAL_DB_NAME: str = ""
    DRUPAL_DB_USER: str = ""
    DRUPAL_DB_PASSWORD: str = ""
    DRUPAL_DB_PORT: int = 3306

    # ------------------------------------------------------------------
    # CORS
    # Must be provided via env in production
    # Supports:
    # - JSON array: ["https://a.com","https://b.com"]
    # - Comma list: https://a.com,https://b.com
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []

        # Try JSON first
        try:
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            # Fallback to comma-separated
            return [
                origin.strip()
                for origin in self.CORS_ORIGINS.split(",")
                if origin.strip()
            ]

    # ------------------------------------------------------------------
    # API Keys
    # ------------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Streamline PMS
    # Example URL: https://yourcompany.streamlinevrs.com
    # ------------------------------------------------------------------
    STREAMLINE_API_URL: str = ""
    STREAMLINE_TOKEN_KEY: str = ""
    STREAMLINE_TOKEN_SECRET: str = ""

    # ------------------------------------------------------------------
    # Cloudflare R2
    # ------------------------------------------------------------------
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str = ""

    class Config:
        env_file = ".env"          # Used locally only
        case_sensitive = True
        extra = "ignore"


# ----------------------------------------------------------------------
# Instantiate settings
# ----------------------------------------------------------------------
settings = Settings()

# ----------------------------------------------------------------------
# Optional debug (enable temporarily if needed)
# ----------------------------------------------------------------------
if settings.DEBUG:
    print("ENVIRONMENT:", settings.ENVIRONMENT)
    print("CORS_ORIGINS RAW:", os.getenv("CORS_ORIGINS"))
    print("CORS_ORIGINS PARSED:", settings.cors_origins_list)
