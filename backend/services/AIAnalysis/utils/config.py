from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env', extra='ignore')
    
    MISTRAL_API_KEY: str
    MONGO_URI: str
    DATABASE_NAME: str = "ai_analysis_db"
    NOTIFICATION_SERVICE_URL: Optional[str] = None
    USER_SERVICE_URL: Optional[str] = None
    SIMILARITY_THRESHOLD: float = 0.85

settings = Settings()
