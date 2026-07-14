import pandas as pd
import logging
from typing import Dict
from sqlalchemy import text
from config import get_connection_string, settings
from pipeline.exceptions import LoadingError
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class WarehouseLoader:
    def __init__(self) -> None:
        self.warehouse_engine = DatabaseManager.get_engine(settings.WAREHOUSE_DB)

    def load_table(self, table_name: str, df: pd.DataFrame, replace_data: bool = False) -> None:
        """Loads a Pandas DataFrame into the WAREHOUSE_DB."""
        logger.info(f"Loading {len(df)} rows into warehouse table {table_name}...")

        with self.warehouse_engine.connect() as conn:
            # 1. Ensure table exists with correct schema (including PKs)
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {settings.SOURCE_DB}.{table_name}"))

            # 2. If replacing data, truncate the table first
            if replace_data:
                conn.execute(text(f"TRUNCATE TABLE {table_name}"))

            conn.commit()

        # 3. Load data using append (since table now exists with correct PK)
        df.to_sql(table_name, self.warehouse_engine, if_exists='append', index=False)
        logger.info(f"Successfully loaded {table_name}.")

    def run(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """Load all cleaned DataFrames into the warehouse. Returns rows loaded per table."""
        try:
            loaded_counts = {}
            # Dimension tables: Replace data (Full refresh)
            for table in settings.DIMENSION_TABLES:
                df = cleaned_data[table]
                self.load_table(table, df, replace_data=True)
                loaded_counts[table] = len(df)

            # Fact tables: Append (Maintaining history)
            for table in settings.FACT_TABLES:
                df = cleaned_data[table]
                self.load_table(table, df, replace_data=False)
                loaded_counts[table] = len(df)

            logger.info("Warehouse loading complete.")
            return loaded_counts
        except Exception as e:
            logger.error(f"Loading phase failed: {e}")
            raise LoadingError(f"Failed to load cleaned data into warehouse: {e}") from e

if __name__ == "__main__":
    print("Loader requires data from the transformer. Run main.py instead.")

