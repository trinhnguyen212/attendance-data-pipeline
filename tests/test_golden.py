import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from config import get_connection_string, SOURCE_DB, WAREHOUSE_DB
from main import run_pipeline
import os

def test_golden_dataset_regression():
    """
    Regression test:
    1. Load Golden Input into Source DB.
    2. Run the pipeline.
    3. Compare Warehouse result with Golden Expected Output.
    """
    source_engine = create_engine(get_connection_string(SOURCE_DB))
    warehouse_engine = create_engine(get_connection_string(WAREHOUSE_DB))

    # 1. Setup: Load Golden Input
    # Use if_exists="replace" to ensure tables are created and cleared
    users_df = pd.read_csv("tests/golden/input_users.csv")
    users_df.to_sql("users", source_engine, if_exists="replace", index=False)

    att_df = pd.read_csv("tests/golden/input_attendance.csv")
    att_df.to_sql("attendance_results", source_engine, if_exists="replace", index=False)

    # 2. Execute pipeline
    run_pipeline()

    # 3. Verify: Compare Warehouse results to Expected output
    with warehouse_engine.connect() as conn:
        actual_users = pd.read_sql("SELECT id, name, email FROM users", conn)
        actual_att = pd.read_sql("SELECT user_id, attendance_id, attendance_status, created_at FROM attendance_results", conn)

    expected_users = pd.read_csv("tests/golden/expected_users.csv")
    expected_att = pd.read_csv("tests/golden/expected_attendance.csv")

    # Ensure column types match for comparison (especially for nulls/NaNs)
    pd.testing.assert_frame_equal(actual_users.sort_values('id').reset_index(drop=True),
                                  expected_users.sort_values('id').reset_index(drop=True),
                                  check_dtype=False)

    pd.testing.assert_frame_equal(actual_att.sort_values('user_id').reset_index(drop=True),
                                  expected_att.sort_values('user_id').reset_index(drop=True),
                                  check_dtype=False)

    print("\nGolden Dataset Verification PASSED ✅")
