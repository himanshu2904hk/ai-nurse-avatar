"""
################################################################################
#                                                                              #
#                         APPLICATION CONFIGURATION                            #
#                                                                              #
#   Loads settings from .env file using Pydantic.                              #
#   All environment variables are defined here.                                #
#                                                                              #
################################################################################
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                        ENVIRONMENT SETTINGS                               ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                         APPLICATION                                     │
    # └────────────────────────────────────────────────────────────────────────┘
    APP_NAME: str = "Patient Pre-Assessment System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                          SECURITY                                       │
    # └────────────────────────────────────────────────────────────────────────┘
    AVATAR_API_KEY: str = "change-this-in-production"

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                         DATABASE                                        │
    # └────────────────────────────────────────────────────────────────────────┘
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "patient_preassessment"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_POOL_SIZE: int = 5

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                          TAVUS                                          │
    # └────────────────────────────────────────────────────────────────────────┘
    TAVUS_API_KEY: Optional[str] = None
    TAVUS_PERSONA_ID: Optional[str] = None
    TAVUS_REPLICA_ID: Optional[str] = None

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                       PYDANTIC CONFIG                                   │
    # └────────────────────────────────────────────────────────────────────────┘
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields in .env
    )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         SETTINGS INSTANCE                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
