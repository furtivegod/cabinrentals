"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Cabin Rentals API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    

    # Supabase (for migrations and client)
    SUPABASE_URL: str = "https://cueenbvreqsnqwpajufv.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1ZWVuYnZyZXFzbnF3cGFqdWZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY1ODcxNDEsImV4cCI6MjA4MjE2MzE0MX0.wssHqwBGUFz3sbQ7A6zxli1R4lMTFgImn5iaUEdGvpg"
    
    # Drupal Database (for migrations only - optional)
    DRUPAL_DB_HOST: str = ""
    DRUPAL_DB_NAME: str = ""
    DRUPAL_DB_USER: str = ""
    DRUPAL_DB_PASSWORD: str = ""
    DRUPAL_DB_PORT: int = 3306
    
    # CORS - can be set as JSON string or comma-separated string
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list, handling both JSON and comma-separated formats"""
        if not self.CORS_ORIGINS:
            return []
        try:
            # Try parsing as JSON first
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except (json.JSONDecodeError, TypeError):
            # If not JSON, treat as comma-separated string
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    
    # Streamline PMS
    STREAMLINE_API_URL: str = ""
    STREAMLINE_API_KEY: str = ""
    
    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""
    
    # JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis (for background jobs)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env that aren't in the model


settings = Settings()

