# Attendance Data Pipeline

A professional ETL (Extract, Transform, Load) pipeline for processing attendance data.

## Architecture
The pipeline follows a three-layer architecture to ensure data quality and reliability:

1. **Source DB** $\rightarrow$ **Staging DB**: Incremental extraction using a high-water mark strategy (based on `created_at`).
2. **Staging DB** $\rightarrow$ **Pandas**: Data cleaning, validation, and deduplication.
3. **Pandas** $\rightarrow$ **Warehouse DB**: Loading cleaned "Gold" data for reporting.

## Features
- **Incremental Extraction**: Only fetches new records to optimize performance.
- **Deduplication**: Removes duplicate attendance entries, keeping the most recent.
- **Data Validation**: Ensures binary attendance statuses and referential integrity.
- **Layered Storage**: Separates raw data from cleaned warehouse data.

## Setup
1. Clone the repository.
2. Create a `.env` file based on the following variables:
   - `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
   - `DB_NAME` (Main DB)
   - `SOURCE_DB` (Source of truth)
   - `STAGING_DB` (Raw mirror)
   - `WAREHOUSE_DB` (Cleaned gold layer)
3. Run `python main.py` to execute the pipeline.

## Project Structure
- `main.py`: Orchestrates the Extract $\rightarrow$ Transform $\rightarrow$ Load flow.
- `extractor.py`: Manages the incremental data pull from source to staging.
- `transformer.py`: Performs data cleaning and business rule validation.
- `loader.py`: Pushes cleaned data into the final warehouse.
- `config.py`: Handles environment-based connection strings.
- `seed_data.py`: Utility to populate the source database with test data.
