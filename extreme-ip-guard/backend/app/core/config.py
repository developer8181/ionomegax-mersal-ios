from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "Extreme IP Guard"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./extreme_ipguard.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Network monitoring
    MONITORING_INTERVAL: int = 5  # seconds
    MAX_CONNECTIONS_PER_IP: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Threat thresholds
    ANOMALY_SCORE_THRESHOLD: float = 0.75
    PORT_SCAN_THRESHOLD: int = 20
    BRUTE_FORCE_THRESHOLD: int = 10
    DDoS_THRESHOLD: int = 1000  # requests per minute
    
    # Geo blocking
    BLOCKED_COUNTRIES: List[str] = []
    
    # Alert settings
    MAX_ALERTS_STORED: int = 10000
    ALERT_RETENTION_DAYS: int = 90
    
    # ML Model paths
    MODEL_PATH: str = "./ml_models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
