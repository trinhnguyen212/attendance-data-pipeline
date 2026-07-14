import pandas as pd
import logging
from pipeline.exceptions import DataQualityError
from typing import Tuple

logger = logging.getLogger(__name__)

class DataQualityGate:
    def __init__(self, threshold: float = 0.1):
        """
        :param threshold: Maximum allowed percentage of invalid rows (0.1 = 10%)
        """
        self.threshold = threshold

    def validate(self, df: pd.DataFrame, table_name: str) -> Tuple[int, str]:
        """
        Run basic quality checks on a dataframe.
        Returns (num_invalid_rows, error_type).
        """
        if df.empty:
            logger.warning(f"Quality Gate: {table_name} is empty.")
            return 0, "empty"

        # Define critical columns for each table
        critical_cols = {
            "users": ["id", "email"],
            "attendance_results": ["user_id", "attendance_id", "attendance_status"]
        }

        cols = critical_cols.get(table_name, [])

        # Check for nulls in critical columns
        invalid_mask = df[cols].isnull().any(axis=1)
        invalid_count = invalid_mask.sum()

        error_pct = invalid_count / len(df) if len(df) > 0 else 0

        if error_pct > self.threshold:
            error_msg = (
                f"Data Quality Failure for {table_name}: "
                f"{error_pct:.2%} of rows had null critical fields. "
                f"Threshold is {self.threshold:.2%}"
            )
            logger.error(error_msg)
            raise DataQualityError(error_msg)

        if invalid_count > 0:
            logger.warning(f"Quality Gate: {table_name} had {invalid_count} null critical fields, but stayed under threshold.")
            return invalid_count, "null_critical_fields"

        logger.info(f"Quality Gate passed for {table_name}.")
        return 0, "pass"
