import logging
from sqlalchemy import create_engine, text
from config import get_connection_string
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton manager for SQLAlchemy engines to avoid redundant connections."""
    _engines = {}

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying database connection... Attempt {retry_state.attempt_number}"
        )
    )
    def get_engine(cls, db_name: str):
        """
        Returns a cached SQLAlchemy engine for the given database name.
        Uses exponential backoff to retry connection if the DB is temporarily unavailable.
        """
        if db_name not in cls._engines:
            connection_string = get_connection_string(db_name)
            engine = create_engine(connection_string)

            # Verify connection immediately to ensure the engine is valid
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            cls._engines[db_name] = engine

        return cls._engines[db_name]
