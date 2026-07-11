import pytest
import pandas as pd
import numpy as np
from transformer import DataCleaner

@pytest.fixture
def cleaner():
    return DataCleaner()

# =============================================================================
# EDGE-CASE MATRIX: User Cleaning
# =============================================================================

@pytest.mark.parametrize("input_data, expected_name, expected_email", [
    # Case: Normal cleaning
    ({'name': ['  Alice  '], 'email': [' alice@example.com ']}, 'Alice', 'alice@example.com'),
    # Case: The Giant (Very long strings)
    ({'name': ['A' * 1000], 'email': ['B' * 1000]}, 'A' * 1000, 'B' * 1000),
    # Case: The Weird (Emojis and special characters)
    ({'name': ['User 🚀🔥'], 'email': ['test@example.com']}, 'User 🚀🔥', 'test@example.com'),
    # Case: The Null (Handling NaNs in string columns)
    ({'name': [np.nan], 'email': [None]}, np.nan, None),
])
def test_clean_users_matrix(cleaner, input_data, expected_name, expected_email):
    df = pd.DataFrame(input_data)
    result = cleaner.clean_users(df)

    actual_name = result['name'].iloc[0]
    actual_email = result['email'].iloc[0]

    # Professional way to compare NaN in Pandas
    if pd.isna(expected_name):
        assert pd.isna(actual_name)
    else:
        assert actual_name == expected_name

    if pd.isna(expected_email):
        assert pd.isna(actual_email)
    else:
        assert actual_email == expected_email

def test_clean_users_empty(cleaner):
    # Case: The Void (Empty DataFrame)
    df = pd.DataFrame(columns=['id', 'name', 'email'])
    result = cleaner.clean_users(df)
    assert len(result) == 0
    assert list(result.columns) == ['id', 'name', 'email']

# =============================================================================
# EDGE-CASE MATRIX: Attendance Cleaning
# =============================================================================

@pytest.mark.parametrize("status_list, expected_count", [
    ([0, 1, 0, 1], 4),     # All valid
    ([0, 1, 2, 3], 2),     # Some invalid (2, 3 should be dropped)
    ([2, 3, 4], 0),        # All invalid
    ([], 0),               # The Void
])
def test_clean_attendance_validation_matrix(cleaner, status_list, expected_count):
    data = {
        'user_id': range(len(status_list)),
        'attendance_id': range(len(status_list)),
        'attendance_status': status_list,
        'created_at': ['2023-01-01'] * len(status_list)
    }
    df = pd.DataFrame(data)
    result = cleaner.clean_attendance(df)
    assert len(result) == expected_count

def test_clean_attendance_deduplication_extreme(cleaner):
    # Case: The Duplicate (Extreme case: 10 identical records)
    data = {
        'user_id': [1] * 10,
        'attendance_id': [101] * 10,
        'attendance_status': [0] * 9 + [1], # Last one is the update
        'created_at': [f"2023-01-01 10:00:0{i}" for i in range(10)]
    }
    df = pd.DataFrame(data)
    result = cleaner.clean_attendance(df)

    assert len(result) == 1
    assert result['attendance_status'].iloc[0] == 1
    assert result['created_at'].iloc[0] == "2023-01-01 10:00:09"

# =============================================================================
# EDGE-CASE MATRIX: Pipeline Integrity (The run() method)
# =============================================================================

def test_transformer_run_ghost_users(cleaner):
    # Case: The Ghost (User exists in attendance but NOT in users table)
    users_df = pd.DataFrame({'id': [1], 'name': ['Alice']})
    attendance_df = pd.DataFrame({
        'user_id': [1, 999], # 999 is a ghost user
        'attendance_id': [101, 102],
        'attendance_status': [1, 1],
        'created_at': ['2023-01-01', '2023-01-01']
    })

    cleaner.extract_from_staging = lambda table: users_df if table == "users" else attendance_df

    results = cleaner.run()

    # Assert: Ghost user 999 should be purged
    assert len(results['attendance_results']) == 1
    assert 999 not in results['attendance_results']['user_id'].values

def test_transformer_run_empty_source(cleaner):
    # Case: The Void (Both tables empty)
    users_df = pd.DataFrame(columns=['id', 'name'])
    attendance_df = pd.DataFrame(columns=['user_id', 'attendance_id', 'attendance_status', 'created_at'])

    cleaner.extract_from_staging = lambda table: users_df if table == "users" else attendance_df

    results = cleaner.run()

    assert len(results['users']) == 0
    assert len(results['attendance_results']) == 0
