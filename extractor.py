import pandas as pd
from sqlalchemy import create_engine, text
from config import get_connection_string, SOURCE_DB, STAGING_DB

class IncrementalExtractor:
    def __init__(self):
        self.source_engine = create_engine(get_connection_string(SOURCE_DB))
        self.staging_engine = create_engine(get_connection_string(STAGING_DB))

    def _get_high_water_mark(self, table_name):
        """Fetch the latest created_at timestamp from the staging table."""
        try:
            with self.staging_engine.connect() as conn:
                query = text(f"SELECT MAX(created_at) FROM {table_name}")
                result = conn.execute(query).scalar()
                return result
        except Exception:
            # Table might not exist or be empty
            return None

    def extract_table(self, table_name):
        """Extracts new data from SOURCE_DB to STAGING_DB based on created_at."""
        print(f"Extracting {table_name}...")

        hwm = self._get_high_water_mark(table_name)

        # 1. Load from source
        if hwm:
            print(f"Incremental extract from {hwm}...")
            query = f"SELECT * FROM {table_name} WHERE created_at > '{hwm}'"
        else:
            print("Full extract (no high-water mark found)...")
            query = f"SELECT * FROM {table_name}"

        df = pd.read_sql(query, self.source_engine)

        # 2. Ensure staging table exists (copy structure from source)
        with self.staging_engine.connect() as conn:
            # Use SOURCE_DB since it's the definition of truth
            conn.execute(text(f"CREATE TABLE IF NOT EXISTS {table_name} LIKE {SOURCE_DB}.{table_name}"))
            conn.commit()

        if df.empty:
            print(f"No new data found for {table_name}.")
            return 0

        # 3. Load into staging
        df.to_sql(table_name, self.staging_engine, if_exists='append', index=False)
        print(f"Successfully extracted {len(df)} rows into {table_name}.")
        return len(df)


    def run(self):
        """Orchestrate the extraction of all key tables."""
        tables = ["users", "attendance_results"]
        total_rows = 0
        for table in tables:
            total_rows += self.extract_table(table)
        print(f"Extraction complete. Total rows extracted: {total_rows}")

if __name__ == "__main__":
    extractor = IncrementalExtractor()
    extractor.run()
