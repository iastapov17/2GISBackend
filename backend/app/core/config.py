from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Dostup.City API"
    DEBUG: bool = True
    
    DGIS_API_KEY: str = ""
    DGIS_ROUTING_URL: str = "https://routing.api.2gis.com/routing/7.0.0/global"
    
    DATABASE_URL: str = "sqlite:///./dostup_city.db"
    
    CORS_ORIGINS: List[str] = ["*"]
    
    DEFAULT_CALM_WEIGHTS: dict = {
        "noise": 0.4,
        "crowd": 0.3,
        "snow": 0.2,
        "distance": 0.1
    }
    
    NOISE_THRESHOLD_DB: int = 75
    CROWD_THRESHOLD: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

