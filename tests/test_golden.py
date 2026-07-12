import pytest
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from config import get_connection_string, SOURCE_DB, STAGING_DB, WAREHOUSE_DB
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
    staging_engine = create_engine(get_connection_string(STAGING_DB))

    # 1. Setup: Load Golden Input
    users_df = pd.read_csv("tests/golden/input_users.csv")

    # Align simplified golden schema with production schema
    # Production columns: id, shortcode, first_name, last_name, email, password, role_id, gender, address, birth_date
    if 'name' in users_df.columns:
        users_df['first_name'] = users_df['name']
        users_df['last_name'] = ''
        users_df = users_df.drop(columns=['name'])

    # Add other missing production columns as NaN
    for col in ['shortcode', 'password', 'role_id', 'gender', 'address', 'birth_date']:
        if col not in users_df.columns:
            users_df[col] = np.nan

    # Ensure columns are in a consistent order for the database
    prod_cols = ['id', 'shortcode', 'first_name', 'last_name', 'email', 'password', 'role_id', 'gender', 'address', 'birth_date']
    users_df = users_df[prod_cols]

    with source_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS attendance_results"))
        conn.execute(text("CREATE TABLE users (id BIGINT PRIMARY KEY, shortcode VARCHAR(10) NULL, first_name VARCHAR(50) NULL, last_name VARCHAR(50) NULL, email VARCHAR(100) NULL, password VARCHAR(255) NULL, role_id INT NULL, gender VARCHAR(10) NULL, address TEXT NULL, birth_date DATE NULL)"))
        conn.execute(text("CREATE TABLE attendance_results (row_id BIGINT AUTO_INCREMENT PRIMARY KEY, attendance_id BIGINT NULL, user_id BIGINT NULL, attendance_status INT NULL, created_at DATETIME NULL)"))
        conn.commit()

    with staging_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS attendance_results"))
        conn.commit()

    with warehouse_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.execute(text("DROP TABLE IF EXISTS attendance_results"))
        conn.commit()

    users_df.to_sql("users", source_engine, if_exists="append", index=False)

    att_df = pd.read_csv("tests/golden/input_attendance.csv")
    # Tables already dropped/created in the previous block
    att_df.to_sql("attendance_results", source_engine, if_exists="append", index=False)

    # 2. Execute pipeline
    run_pipeline()

    # 3. Verify: Compare Warehouse results to Expected output
    with warehouse_engine.connect() as conn:
        # Reconstruct the simplified 'name' column from first_name and last_name
        actual_users = pd.read_sql("SELECT id, TRIM(CONCAT(first_name, ' ', last_name)) as name, email FROM users", conn)
        actual_att = pd.read_sql("SELECT user_id, attendance_id, attendance_status, created_at FROM attendance_results", conn)

    expected_users = pd.read_csv("tests/golden/expected_users.csv")
    expected_att = pd.read_csv("tests/golden/expected_attendance.csv")

    # Ensure created_at is converted to datetime for comparison
    actual_att['created_at'] = pd.to_datetime(actual_att['created_at'])
    expected_att['created_at'] = pd.to_datetime(expected_att['created_at'])

    # Ensure column types match for comparison (especially for nulls/NaNs)
    pd.testing.assert_frame_equal(actual_users.sort_values('id').reset_index(drop=True),
                                  expected_users.sort_values('id').reset_index(drop=True),
                                  check_dtype=False)

    pd.testing.assert_frame_equal(actual_att.sort_values('user_id').reset_index(drop=True),
                                  expected_att.sort_values('user_id').reset_index(drop=True),
                                  check_dtype=False)

    print("\nGolden Dataset Verification PASSED ✅")
