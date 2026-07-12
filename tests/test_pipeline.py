import pytest
import pandas as pd
from sqlalchemy import create_engine, text
from config import get_connection_string, SOURCE_DB, STAGING_DB, WAREHOUSE_DB
from main import run_pipeline
from scripts import seed_data

def test_end_to_end_pipeline():
    """
    Integration test:
    1. Clear all target databases.
    2. Seed the source database.
    3. Run the pipeline.
    4. Verify the final warehouse state.
    """
    print("\nStarting End-to-End Integration Test...")

    # 1. Setup: Clear target tables
    source_engine = create_engine(get_connection_string(SOURCE_DB))
    staging_engine = create_engine(get_connection_string(STAGING_DB))
    warehouse_engine = create_engine(get_connection_string(WAREHOUSE_DB))

    tables = ["users", "attendance_results"]

    with staging_engine.connect() as conn:
        for t in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
            conn.commit()

    with warehouse_engine.connect() as conn:
        for t in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
            conn.commit()

    # 2. Seed: Populate source with fresh test data
    # Note: We call the function from seed_data.py
    seed_data.seed_data()
    print("Source database seeded.")

    # 3. Execute: Run the full pipeline
    try:
        run_pipeline()
    except Exception as e:
        pytest.fail(f"Pipeline crashed during integration test: {e}")

    # 4. Verify: Check Warehouse counts
    # Assuming seed_data.py creates a known number of users (e.g., 10)
    # and attendance records (e.g., 50)
    with warehouse_engine.connect() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        att_count = conn.execute(text("SELECT COUNT(*) FROM attendance_results")).scalar()

        print(f"Verification: Users in warehouse: {user_count}, Attendance in warehouse: {att_count}")

        # These thresholds should be adjusted based on the actual logic in seed_data.py
        assert user_count > 0, "Warehouse users table is empty!"
        assert att_count > 0, "Warehouse attendance table is empty!"

    print("End-to-End Integration Test PASSED ✅")
