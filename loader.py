import pandas as pd
from sqlalchemy import create_engine, text
from config import get_connection_string, WAREHOUSE_DB, SOURCE_DB

class WarehouseLoader:
    def __init__(self):
        self.warehouse_engine = create_engine(get_connection_string(WAREHOUSE_DB))

    def load_table(self, table_name, df, replace_data=False):
        """Loads a Pandas DataFrame into the WAREHOUSE_DB."""
        print(f"Loading {len(df)} rows into warehouse table {table_name}...")

        with self.warehouse_engine.connect() as conn:
            # 1. Ensure table exists with correct schema (including PKs)
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {SOURCE_DB}.{table_name}"))

            # 2. If replacing data, truncate the table first
            if replace_data:
                conn.execute(text(f"TRUNCATE TABLE {table_name}"))

            conn.commit()

        # 3. Load data using append (since table now exists with correct PK)
        df.to_sql(table_name, self.warehouse_engine, if_exists='append', index=False)
        print(f"Successfully loaded {table_name}.")

    def run(self, cleaned_data):
        """Load all cleaned DataFrames into the warehouse."""
        # Dimension tables: Replace data (Full refresh)
        self.load_table("users", cleaned_data["users"], replace_data=True)

        # Fact tables: Append (Maintaining history)
        self.load_table("attendance_results", cleaned_data["attendance_results"], replace_data=False)

        print("Warehouse loading complete.")

if __name__ == "__main__":
    print("Loader requires data from the transformer. Run main.py instead.")

