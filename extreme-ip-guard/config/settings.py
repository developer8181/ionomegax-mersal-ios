"""
Extreme IP Guard - Configuration Settings
Centralized configuration with environment variable support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Extreme IP Guard"
    APP_VERSION: str = "1.0.0"
    APP_CODENAME: str = "Sentinel"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8443
    SECRET_KEY: str = "xipg-s3cr3t-k3y-ch4ng3-1n-pr0duct10n"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'xipguard.db'}"

    THREAT_SCORE_THRESHOLD: float = 70.0
    AUTO_BLOCK_THRESHOLD: float = 90.0
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 100
    DDOS_DETECTION_WINDOW: int = 10
    DDOS_PACKET_THRESHOLD: int = 1000
    PORT_SCAN_THRESHOLD: int = 15
    PORT_SCAN_WINDOW: int = 30
    BRUTE_FORCE_THRESHOLD: int = 10
    BRUTE_FORCE_WINDOW: int = 300
    ANOMALY_SENSITIVITY: float = 2.5

    GEOIP_DB_PATH: Optional[str] = None
    THREAT_FEEDS_ENABLED: bool = True
    THREAT_FEED_UPDATE_INTERVAL: int = 3600

    LOG_LEVEL: str = "INFO"
    MAX_LOG_ENTRIES: int = 100000
    AUDIT_LOG_ENABLED: bool = True

    WEBSOCKET_HEARTBEAT: int = 30
    MAX_WEBSOCKET_CONNECTIONS: int = 100

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "XIPGuard@2026!"

    class Config:
        env_prefix = "XIPG_"
        env_file = ".env"


settings = Settings()
