import pandas as pd
import logging
from typing import Optional, Any
from sqlalchemy import text
from config import get_connection_string, settings
from pipeline.exceptions import ExtractionError
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class IncrementalExtractor:
    def __init__(self) -> None:
        self.source_engine = DatabaseManager.get_engine(settings.SOURCE_DB)
        self.staging_engine = DatabaseManager.get_engine(settings.STAGING_DB)

    def _get_high_water_mark(self, table_name: str) -> Optional[Any]:
        """Fetch the latest created_at timestamp from the staging table."""
        try:
            with self.staging_engine.connect() as conn:
                query = text(f"SELECT MAX(created_at) FROM {table_name}")
                result = conn.execute(query).scalar()
                return result
        except Exception:
            # Table might not exist or be empty
            return None

    def extract_table(self, table_name: str) -> int:
        """Extracts new data from SOURCE_DB to STAGING_DB based on created_at."""
        logger.info(f"Extracting {table_name}...")

        hwm = self._get_high_water_mark(table_name)

        # 1. Load from source
        if hwm:
            logger.info(f"Incremental extract from {hwm}...")
            query = text(f"SELECT * FROM {table_name} WHERE created_at > :hwm")
            df = pd.read_sql(query, self.source_engine, params={"hwm": hwm})
        else:
            logger.info("Full extract (no high-water mark found)...")
            query = text(f"SELECT * FROM {table_name}")
            df = pd.read_sql(query, self.source_engine)

        # 2. Ensure staging table exists (copy structure from source)
        with self.staging_engine.connect() as conn:
            # Use SOURCE_DB since it's the definition of truth
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {settings.SOURCE_DB}.{table_name}"))
            conn.commit()

        if df.empty:
            logger.info(f"No new data found for {table_name}.")
            return 0

        # 3. Load into staging
        df.to_sql(table_name, self.staging_engine, if_exists='append', index=False)
        logger.info(f"Successfully extracted {len(df)} rows into {table_name}.")
        return len(df)


    def run(self) -> None:
        """Orchestrate the extraction of all key tables."""
        try:
            total_rows = 0
            for table in settings.EXTRACT_TABLES:
                total_rows += self.extract_table(table)
            logger.info(f"Extraction complete. Total rows extracted: {total_rows}")
        except Exception as e:
            logger.error(f"Extraction phase failed: {e}")
            raise ExtractionError(f"Failed to extract data from source: {e}") from e

if __name__ == "__main__":
    extractor = IncrementalExtractor()
    extractor.run()
