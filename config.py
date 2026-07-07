import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
SOURCE_DB = os.getenv("SOURCE_DB")
STAGING_DB = os.getenv("STAGING_DB")
WAREHOUSE_DB = os.getenv("WAREHOUSE_DB")

def get_connection_string(db_name=None):
    """Helper to build the SQLAlchemy connection string"""
    target_db = db_name if db_name else DB_NAME
    return f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{target_db}"

