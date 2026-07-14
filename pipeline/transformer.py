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

    def clean_attendance(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Apply cleaning, validation and deduplication to attendance data."""
        logger.info("Cleaning attendance data...")
        initial_count = len(df)
        drops = {"total": 0}

        if df.empty:
            return df, drops

        # 1. Validation: ensure attendance_status is binary (0 or 1)
        valid_mask = df['attendance_status'].isin([0, 1])
        invalid_count = len(df) - valid_mask.sum()
        df = df[valid_mask]
        drops["invalid_status"] = invalid_count

        # 2. Deduplication:
        # Identify records with identical user_id and attendance_id.
        df = df.sort_values('created_at', ascending=False)
        pre_dedup_count = len(df)
        df = df.drop_duplicates(subset=['user_id', 'attendance_id'], keep='first')
        drops["duplicates"] = pre_dedup_count - len(df)

        final_count = len(df)
        logger.info(f"Cleaned attendance data: {initial_count} -> {final_count} rows (Removed {initial_count - final_count} invalid/duplicates).")
        return df, drops

    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning for user data."""
        logger.info("Cleaning user data...")
        # Trim whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        return df

    def run(self) -> Tuple[Dict[str, pd.DataFrame], Dict[str, int]]:
        """Process the staging tables and return cleaned DataFrames and drop metrics."""
        try:
            # Extract
            raw_users = self.extract_from_staging("users")
            raw_attendance = self.extract_from_staging("attendance_results")

            # Data Quality Gate: Validate raw data before transformation
            u_invalid, _ = self.dq_gate.validate(raw_users, "users")
            a_invalid, _ = self.dq_gate.validate(raw_attendance, "attendance_results")

            # Transform
            clean_users = self.clean_users(raw_users)
            clean_attendance, att_drops = self.clean_attendance(raw_attendance)

            # Integrity Check: Ensure all user_ids in attendance exist in users table
            valid_user_ids = set(clean_users['id'])
            pre_integrity_count = len(clean_attendance)
            clean_attendance = clean_attendance[clean_attendance['user_id'].isin(valid_user_ids)]
            integrity_drops = pre_integrity_count - len(clean_attendance)

            logger.info(f"Integrity check complete. {len(clean_attendance)} attendance records verified against users.")

            metrics = {
                "null_critical_fields": u_invalid + a_invalid,
                "invalid_status": att_drops.get("invalid_status", 0),
                "duplicates": att_drops.get("duplicates", 0),
                "referential_integrity": integrity_drops
            }

            return {
                "users": clean_users,
                "attendance_results": clean_attendance
            }, metrics
        except Exception as e:
            logger.error(f"Transformation phase failed: {e}")
            raise TransformationError(f"Failed to clean and validate data: {e}") from e

if __name__ == "__main__":
    cleaner = DataCleaner()
    results, metrics = cleaner.run()
    print("Transformation complete.")
