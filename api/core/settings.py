# src/core/settings.py

from functools import lru_cache

from domain.models.db_config_model import DatabaseConfig
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()  # Loads .env file


class Settings(BaseSettings):
    development_mode: bool = True  # Set to False in production

    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT: int = 30  # Timeout in seconds for Groq API requests
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Colors Auto Training DB settings

    COLORS_DB_USER: str
    COLORS_DB_PASSWORD: str
    COLORS_DB_HOST: str
    COLORS_DB_PORT: int
    COLORS_DB_NAME: str

    @property
    def colors_auto_training_db(self) -> DatabaseConfig:
        return DatabaseConfig(
            dialect="mysql+pymysql",
            username=self.COLORS_DB_USER,
            password=self.COLORS_DB_PASSWORD,
            host=self.COLORS_DB_HOST,
            port=self.COLORS_DB_PORT,
            database=self.COLORS_DB_NAME,
            options={},
        )

    class Config:
        env_file = "../.env"  # Optional with load_dotenv, but good for pydantic to know


# Singleton
@lru_cache()
def app_settings() -> Settings:
    return Settings()
