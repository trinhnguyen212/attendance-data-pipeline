# Attendance Data Pipeline

A production-grade ETL pipeline designed to move attendance data from a source system into a data warehouse.

## 🚀 Overview

This project implements a three-phase ETL process to ensure data quality and consistency:

1. **Extraction**: Incremental pull from the Source database to a Staging database using high-water marks.
2. **Transformation**: Data cleaning, binary status validation, and deduplication using Pandas.
3. **Loading**: Final persistence of cleaned "Gold" data into the Warehouse database.

## 🛠️ Tech Stack

- **Python 3.11+**
- **Pandas**: For data transformation and cleaning.
- **SQLAlchemy**: For database orchestration.
- **MySQL**: Source, Staging, and Warehouse layers.
- **Pytest**: For unit and regression testing.

## 🚦 Quick Start

The fastest way to run this project is via Docker.

1. **Clone and Setup**
   ```bash
   git clone https://github.com/trinhnguyen212/attendance-data-pipeline.git
   cd attendance-data-pipeline
   ```

2. **Start the Infrastructure**
   ```bash
   docker-compose up -d db
   ```

3. **Seed the Source Database**
   ```bash
   docker-compose run --rm app python scripts/seed_data.py
   ```

4. **Run the Pipeline**
   ```bash
   docker-compose run --rm app python main.py
   ```

## 📂 Project Structure

- `main.py`: Pipeline orchestrator.
- `pipeline/extractor.py`: Handles incremental pulls from Source $\rightarrow$ Staging.
- `pipeline/transformer.py`: Handles cleaning and validation.
- `pipeline/quality_checks.py`: Basic data quality gates.
- `pipeline/loader.py`: Final loading into the Warehouse.
- `tests/`: Suite of unit and regression tests.
