from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='ignore')
    
    MISTRAL_API_KEY: str  # kept for backwards compat / embeddings
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "mistralai/mistral-7b-instruct-v0.1"
    MONGO_URI: str
    DATABASE_NAME: str = "ai_analysis_db"
    NOTIFICATION_SERVICE_URL: Optional[str] = None
    USER_SERVICE_URL: Optional[str] = None
    SIMILARITY_THRESHOLD: float = 0.85

settings = Settings()

