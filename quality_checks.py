import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataQualityError(Exception):
    """Raised when data quality fails the defined thresholds"""
    pass

class DataQualityGate:
    def __init__(self, threshold: float = 0.1):
        """
        :param threshold: Maximum allowed percentage of invalid rows (0.1 = 10%)
        """
        self.threshold = threshold

    def validate(self, df: pd.DataFrame, table_name: str):
        """
        Run quality checks on a dataframe.
        """
        if df.empty:
            logger.warning(f"Quality Gate: {table_name} is empty. This might be an issue but we'll allow it.")
            return

        # 1. Check for nulls in critical columns
        # We define critical columns for this project
        critical_cols = {
            "users": ["id", "email"],
            "attendance_results": ["user_id", "attendance_id", "attendance_status"]
        }

        # Get cols for the current table
        cols = critical_cols.get(table_name, [])

        # Calculate null percentage
        null_count = 0
        for col in cols:
            null_count += df[col].isna().sum()

        null_pct = null_count / (len(df) * len(cols)) if len(cols) > 0 else 0

        # 2. Check for invalid values in specific columns
        # For attendance, we only allow 0 or 1
        invalid_val_count = 0
        if table_name == "attendance_results":
            invalid_val_count = len(df[~df['attendance_status'].isin([0, 1])])

        invalid_pct = invalid_val_count / len(df) if len(df) > 0 else 0

        # Check against threshold
        if null_pct > self.threshold or invalid_pct > self.threshold:
            error_msg = (
                f"Data Quality Failure for {table_name}: "
                f"Nulls: {null_pct:.2%}, Invalid Values: {invalid_pct:.2%}. "
                f"Threshold is {self.threshold:.2%}"
            )
            logger.error(error_msg)
            raise DataQualityError(error_msg)

        logger.info(f"Quality Gate passed for {table_name} (Nulls: {null_pct:.2%}, Invalid: {invalid_pct:.2%})")
