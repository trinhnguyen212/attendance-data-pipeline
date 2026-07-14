import logging
import sys
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pythonjsonlogger import jsonlogger

class Settings(BaseSettings):
    """
    Application settings managed by Pydantic.
    Automatically loads environment variables from .env file.
    """
    # Database Credentials
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str

    # Database Targets
    SOURCE_DB: str
    STAGING_DB: str
    WAREHOUSE_DB: str

    # Pipeline Parameters
    DQ_THRESHOLD: float = 0.1
    EXTRACT_TABLES: List[str] = ["users", "attendance_results"]
    DIMENSION_TABLES: List[str] = ["users"]
    FACT_TABLES: List[str] = ["attendance_results"]

    # Pydantic configuration for environment loading
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

def setup_logging():
    """
    Configures structured JSON logging for production observability.
    """
    logger = logging.getLogger()

    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Use JSON formatter for structured logs
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

# Initialize settings and logging once
settings = Settings()
setup_logging()

def get_connection_string(db_name: Optional[str] = None) -> str:
    """
    Helper to build the SQLAlchemy connection string using validated settings.
    """
    target_db = db_name if db_name else settings.DB_NAME
    return f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{target_db}"
