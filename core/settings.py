# src/core/settings.py

from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from src.domain.models.db_config_model import DatabaseConfig

load_dotenv()  # Loads .env file


class Settings(BaseSettings):
    @property
    def colors_auto_training_db(self) -> DatabaseConfig:
        return DatabaseConfig(
            dialect="postgresql",
            username=self.COLORS_DB_USER,
            password=self.COLORS_DB_PASSWORD,
            host=self.COLORS_DB_HOST,
            port=self.COLORS_DB_PORT,
            database=self.COLORS_DB_NAME,
            options={"sslmode": self.COLORS_DB_SSLMODE},
        )

    class Config:
        env_file = ".env"  # Optional with load_dotenv, but good for pydantic to know


# Singleton
@lru_cache()
def app_settings() -> Settings:
    return Settings()
