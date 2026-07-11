import pandas as pd
import logging
from typing import Dict
from config import get_connection_string, STAGING_DB
from exceptions import TransformationError
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self) -> None:
        self.staging_engine = DatabaseManager.get_engine(STAGING_DB)

    def extract_from_staging(self, table_name: str) -> pd.DataFrame:
        """Load raw data from STAGING_DB into a Pandas DataFrame."""
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql(query, self.staging_engine)

    def clean_attendance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply cleaning, validation and deduplication to attendance data."""
        logger.info("Cleaning attendance data...")
        initial_count = len(df)

        # 1. Validation: ensure attendance_status is binary (0 or 1)
        # Keep only rows where status is 0 or 1. Others are dropped.
        df = df[df['attendance_status'].isin([0, 1])]

        # 2. Deduplication:
        # Identify records with identical user_id and attendance_id.
        # Keep only the most recent entry based on created_at.
        df = df.sort_values('created_at', ascending=False)
        df = df.drop_duplicates(subset=['user_id', 'attendance_id'], keep='first')

        final_count = len(df)
        logger.info(f"Cleaned attendance data: {initial_count} -> {final_count} rows (Removed {initial_count - final_count} invalid/duplicates).")
        return df

    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning for user data."""
        logger.info("Cleaning user data...")
        # Trim whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            # Use apply with a lambda for maximum compatibility across pandas versions
            # This handles NaNs and mixed types more robustly than .str.strip()
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        # Handle nulls in non-critical columns (example)
        # Note: For unique columns like phone_number, we keep them as NaN/None
        # because filling with 'Unknown' would trigger a UNIQUE constraint violation.
        if 'phone_number' in df.columns:
            # Removed the .fillna('Unknown') to avoid duplicate entry errors in the database
            pass
        return df



    def run(self) -> Dict[str, pd.DataFrame]:
        """Process the staging tables and return cleaned DataFrames."""
        try:
            # Extract
            raw_users = self.extract_from_staging("users")
            raw_attendance = self.extract_from_staging("attendance_results")

            # Transform
            clean_users = self.clean_users(raw_users)
            clean_attendance = self.clean_attendance(raw_attendance)

            # Integrity Check: Ensure all user_ids in attendance exist in users table
            valid_user_ids = set(clean_users['id'])
            clean_attendance = clean_attendance[clean_attendance['user_id'].isin(valid_user_ids)]

            logger.info(f"Integrity check complete. {len(clean_attendance)} attendance records verified against users.")

            return {
                "users": clean_users,
                "attendance_results": clean_attendance
            }
        except Exception as e:
            logger.error(f"Transformation phase failed: {e}")
            raise TransformationError(f"Failed to clean and validate data: {e}") from e

if __name__ == "__main__":
    cleaner = DataCleaner()
    results = cleaner.run()
    print("Transformation complete.")
