from sqlalchemy import text, inspect
import pandas as pd
import logging
from typing import Dict, Optional, Tuple
from config import get_connection_string, settings
from pipeline.exceptions import TransformationError
from db_manager import DatabaseManager
from pipeline.quality_checks import DataQualityGate

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, dq_threshold: Optional[float] = None) -> None:
        self.staging_engine = DatabaseManager.get_engine(settings.STAGING_DB)
        threshold = dq_threshold if dq_threshold is not None else settings.DQ_THRESHOLD
        self.dq_gate = DataQualityGate(threshold=threshold)

    def extract_from_staging(self, table_name: str) -> pd.DataFrame:
        """Load raw data from STAGING_DB into a Pandas DataFrame."""
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql(query, self.staging_engine)

    def clean_attendance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply cleaning, validation and deduplication to attendance data."""
        if df.empty:
            return df

        logger.info("Cleaning attendance data...")
        # 1. Validation: ensure attendance_status is binary (0 or 1)
        valid_mask = df['attendance_status'].isin([0, 1])
        df = df[valid_mask].copy()

        # 2. Deduplication:
        df = df.sort_values('created_at', ascending=False)
        df = df.drop_duplicates(subset=['user_id', 'attendance_id'], keep='first')

        return df

    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning for user data."""
        if df.empty:
            return df

        logger.info("Cleaning user data...")
        # Trim whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        return df

    def run(self) -> Dict[str, pd.DataFrame]:
        """Process the staging tables and return cleaned DataFrames."""
        try:
            # Extract
            raw_users = self.extract_from_staging("users")
            raw_attendance = self.extract_from_staging("attendance_results")

            # Data Quality Gate: Validate raw data before transformation
            self.dq_gate.validate(raw_users, "users")
            self.dq_gate.validate(raw_attendance, "attendance_results")

            # Transform
            clean_users = self.clean_users(raw_users)
            clean_attendance = self.clean_attendance(raw_attendance)

            # --- REFERENTIAL INTEGRITY SECTION ---
            # Ensure all user_ids in attendance exist in the Warehouse users table.
            if not clean_attendance.empty:
                warehouse_engine = DatabaseManager.get_engine(settings.WAREHOUSE_DB)
                inspector = inspect(warehouse_engine)

                if inspector.has_table("users"):
                    # Scenario: Incremental Load - Use Warehouse as the source of truth
                    with warehouse_engine.connect() as conn:
                        user_ids_df = pd.read_sql(text("SELECT id FROM users"), conn)
                        valid_user_ids = set(user_ids_df['id'])
                    logger.info(f"Referential Integrity: Using warehouse users (incremental load) - Loaded {len(valid_user_ids)} IDs")
                else:
                    # Scenario: Initial Full Load - Use current batch since warehouse table doesn't exist yet
                    valid_user_ids = set(clean_users['id']) if not clean_users.empty else set()
                    logger.info(f"Referential Integrity: Using current users batch (initial load) - {len(valid_user_ids)} IDs")

                # Apply validation filter
                initial_count = len(clean_attendance)
                clean_attendance = clean_attendance[clean_attendance['user_id'].isin(valid_user_ids)]
                dropped_count = initial_count - len(clean_attendance)

                if dropped_count > 0:
                    logger.warning(f"Referential Integrity: Dropped {dropped_count} attendance records with non-existent user_ids.")
            # --- END REFERENTIAL INTEGRITY SECTION ---

            logger.info(f"Transformation complete. {len(clean_attendance)} attendance records verified.")

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
