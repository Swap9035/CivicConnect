from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    
    mongo_uri: str = "mongodb://localhost:27017"
    database_name: str = "superuserdb"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    initial_admin_email: str = "superadmin@gov.in"
    initial_admin_password: str = "TempAdmin@123"
    service_port: int = 8002

settings = Settings()
