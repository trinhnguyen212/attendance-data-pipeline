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
        if df.empty:
            logger.info(f"No new records to load for table {table_name}. Skipping.")
            return

        logger.info(f"Loading {len(df)} rows into warehouse table {table_name}...")

        with self.warehouse_engine.connect() as conn:
            # 1. Ensure table exists with correct schema (including PKs)
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {settings.SOURCE_DB}.{table_name}"))

            # 2. If replacing data, truncate the table first
            if replace_data:
                conn.execute(text(f"TRUNCATE TABLE {table_name}"))
                conn.commit()
                # Load directly using to_sql for full refreshes
                df.to_sql(table_name, self.warehouse_engine, if_exists='append', index=False)
                return

            # 3. Incremental Load: Use a temporary table to perform UPSERT (ON DUPLICATE KEY UPDATE)
            # This prevents Duplicate Entry errors if the same record is extracted twice
            # or if a record was updated in the source.
            temp_table = f"temp_{table_name}"
            df.to_sql(temp_table, self.warehouse_engine, if_exists='replace', index=False)

            # Construct the UPSERT query
            columns = df.columns.tolist()
            col_list = ", ".join([f"`{c}`" for c in columns])
            update_list = ", ".join([f"`{c}`=VALUES(`{c}`)" for c in columns])

            upsert_query = text(f"""
                INSERT INTO {table_name} ({col_list})
                SELECT {col_list} FROM {temp_table}
                ON DUPLICATE KEY UPDATE {update_list}
            """)

            conn.execute(upsert_query)
            conn.execute(text(f"DROP TABLE {temp_table}"))
            conn.commit()

        logger.info(f"Successfully loaded {table_name} via UPSERT.")

    def run(self, cleaned_data: Dict[str, pd.DataFrame]) -> None:
        """Load all cleaned DataFrames into the warehouse."""
        try:
            # Dimension tables: Replace data (Full refresh)
            for table in settings.DIMENSION_TABLES:
                df = cleaned_data[table]
                self.load_table(table, df, replace_data=True)

            # Fact tables: Append (Maintaining history)
            for table in settings.FACT_TABLES:
                df = cleaned_data[table]
                self.load_table(table, df, replace_data=False)

            logger.info("Warehouse loading complete.")
        except Exception as e:
            logger.error(f"Loading phase failed: {e}")
            raise LoadingError(f"Failed to load cleaned data into warehouse: {e}") from e

if __name__ == "__main__":
    print("Loader requires data from the transformer. Run main.py instead.")

