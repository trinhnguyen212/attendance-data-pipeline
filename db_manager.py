from sqlalchemy import create_engine
from config import get_connection_string

class DatabaseManager:
    """Singleton manager for SQLAlchemy engines to avoid redundant connections."""
    _engines = {}

    @classmethod
    def get_engine(cls, db_name: str):
        """Returns a cached SQLAlchemy engine for the given database name."""
        if db_name not in cls._engines:
            connection_string = get_connection_string(db_name)
            cls._engines[db_name] = create_engine(connection_string)
        return cls._engines[db_name]
