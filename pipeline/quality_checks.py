import pandas as pd
import logging
import pandera as pa
from pandas import DataFrame
from pipeline.exceptions import DataQualityError
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Define the expected schema for users
USERS_SCHEMA = pa.DataFrameSchema({
    "id": pa.Column(int, nullable=False),
    "email": pa.Column(str, nullable=False, checks=pa.Check.str_matches(r'[^@]+@[^@]+\.[^@]+')),
    "first_name": pa.Column(str, nullable=True),
    "last_name": pa.Column(str, nullable=True),
})

# Define the expected schema for attendance
ATTENDANCE_SCHEMA = pa.DataFrameSchema({
    "user_id": pa.Column(int, nullable=False),
    "attendance_id": pa.Column(int, nullable=False),
    "attendance_status": pa.Column(int, nullable=False, checks=pa.Check.isin([0, 1])),
})

class DataQualityGate:
    def __init__(self, threshold: float = 0.1):
        """
        :param threshold: Maximum allowed percentage of invalid rows (0.1 = 10%)
        """
        self.threshold = threshold

    def validate(self, df: pd.DataFrame, table_name: str) -> Tuple[int, str]:
        """
        Run quality checks on a dataframe using Pandera.
        Returns (num_invalid_rows, error_type).
        """
        if df.empty:
            logger.warning(f"Quality Gate: {table_name} is empty.")
            return 0, "empty"

        schema = USERS_SCHEMA if table_name == "users" else ATTENDANCE_SCHEMA

        try:
            schema.validate(df, lazy=True)
            logger.info(f"Quality Gate passed for {table_name}.")
            return 0, "pass"
        except pa.errors.SchemaErrors as err:
            invalid_count = len(err.failure_cases)
            # Calculate error percentage relative to dataframe size
            error_pct = invalid_count / len(df) if len(df) > 0 else 0

            if error_pct > self.threshold:
                error_msg = (
                    f"Data Quality Failure for {table_name}: "
                    f"{error_pct:.2%} of rows failed validation. "
                    f"Threshold is {self.threshold:.2%}"
                )
                logger.error(error_msg)
                raise DataQualityError(error_msg)

            logger.warning(f"Quality Gate: {table_name} had {invalid_count} schema violations, but stayed under threshold.")
            return invalid_count, "schema_violation"
