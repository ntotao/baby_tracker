from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Baby Tracker Bot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Telegram
    TELEGRAM_TOKEN: str
    TELEGRAM_ADMIN_ID: Optional[int] = None
    WEBAPP_URL: str = "https://your-domain.com" # Required for Web App Button
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/babytracker.db"
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "changethis_in_production"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
