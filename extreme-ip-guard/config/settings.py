from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "Extreme IP Guard"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Next-Generation Cybersecurity IP Protection System"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./extreme_ip_guard.db"
    SECRET_KEY: str = "xig-ultra-secure-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MAX_REQUESTS_PER_MINUTE: int = 100
    DDOS_THRESHOLD: int = 500
    THREAT_SCORE_CRITICAL: int = 80
    THREAT_SCORE_HIGH: int = 60
    THREAT_SCORE_MEDIUM: int = 40
    THREAT_SCORE_LOW: int = 20

    AUTO_BLOCK_ENABLED: bool = True
    AUTO_BLOCK_THRESHOLD: int = 75
    SCAN_INTERVAL_SECONDS: int = 30

    GEOIP_DB_PATH: Optional[str] = None

    WEBSOCKET_HEARTBEAT: int = 15

    class Config:
        env_file = ".env"
        env_prefix = "XIG_"


settings = Settings()
