from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "PathoScope"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://pathoscope:password@localhost:5432/pathoscope_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Email/SMS Configuration
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # SMS Gateway
    SMS_GATEWAY_URL: Optional[str] = None
    SMS_API_KEY: Optional[str] = None

    # TEK Distribution Server
    TEK_DISTRIBUTION_URL: Optional[str] = None
    TEK_API_KEY: Optional[str] = None

    # Security Settings
    BCRYPT_ROUNDS: int = 12
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # Token Settings
    VERIFICATION_TOKEN_LENGTH: int = 32
    TOKEN_EXPIRE_HOURS: int = 72

    # Data Retention
    TEK_RETENTION_DAYS: int = 14
    AUDIT_LOG_RETENTION_DAYS: int = 365

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()