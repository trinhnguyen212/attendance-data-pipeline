# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

---

# Project Overview

This project implements a production-style ETL pipeline for an Attendance Management System.

Technology Stack

- Python 3.11
- Pandas
- SQLAlchemy
- MySQL
- Docker Compose
- Pytest

Architecture

Source Database
        ↓
Extraction
        ↓
Staging Database
        ↓
Transformation
        ↓
Warehouse Database

The project demonstrates incremental ETL, data quality validation, referential integrity, and warehouse loading.

---

# Common Commands

## Environment

Start database

```bash
docker-compose up -d db
```

Seed source database

```bash
docker-compose run --rm app python -m scripts.seed_data
```

Reset database

```bash
docker-compose down -v
```

---

## Pipeline

Run ETL

```bash
docker-compose run --rm app python main.py
```

---

## Testing

Run all tests

```bash
docker-compose run --rm app pytest
```

Run one test

```bash
docker-compose run --rm app pytest tests/test_file.py::test_function
```

---

# ETL Architecture

The pipeline consists of three phases.

## 1. Extraction

File

```
pipeline/extractor.py
```

Responsibilities

- Extract from Source Database.
- Load into Staging Database.
- Use High-Water Mark incremental extraction.
- Create staging tables automatically if they do not exist.

Rules

- First execution performs a Full Load.
- Later executions perform Incremental Loads.
- If no new records exist, return an empty DataFrame.
- Never reload existing warehouse data.

High-Water Mark

- Stored in the Warehouse.
- Uses the latest `created_at` timestamp.
- Only records newer than the High-Water Mark should be extracted.

---

## 2. Staging Database

Purpose

The staging database is a temporary landing zone.

Rules

- Staging tables may not exist before the first pipeline run.
- Staging is cleared before each pipeline execution.
- Staging is cleared again after a successful pipeline execution.
- Staging should never be treated as permanent storage.

---

## 3. Transformation

File

```
pipeline/transformer.py
```

Responsibilities

- Clean data.
- Validate data.
- Remove duplicates.
- Enforce referential integrity.

Cleaning

- Trim whitespace.
- Validate attendance_status is binary (0 or 1).
- Remove duplicate attendance records.

Referential Integrity

Initial Load

- Warehouse dimension tables may not exist.
- Validate attendance using the current extracted users batch.

Incremental Load

- Warehouse dimension tables exist.
- Validate attendance using `warehouse.users`.

Implementation Requirement

Before querying warehouse users:

```python
inspector = inspect(warehouse_engine)

if inspector.has_table("users"):
    ...
```

Never query:

```sql
SELECT id FROM users
```

unless the table exists.

---

## 4. Loading

File

```
pipeline/loader.py
```

Dimension Tables

- users

Strategy

- Full Refresh
- Truncate then Load

Fact Tables

- attendance_results

Strategy

- Incremental Load
- UPSERT
- Preserve history

Never truncate fact tables during incremental loads.

---

# Data Quality Rules

Current rules

- attendance_status must be 0 or 1
- Duplicate attendance records removed
- Referential integrity enforced
- Whitespace removed from strings

Data Quality Gate must execute before transformation.

---

# Database Roles

## Source Database

System of record.

Contains operational data.

Never modify business logic here.

---

## Staging Database

Temporary landing zone.

Safe to truncate.

---

## Warehouse Database

Analytics database.

Contains cleaned data.

Acts as the source of truth for incremental loading.

---

# Coding Standards

Prefer

- SQLAlchemy
- Pandas
- Context managers
- Type hints
- Logging
- Small functions
- Custom exceptions

Avoid

- Duplicate business logic
- Hard-coded SQL
- Silent exception handling
- Large monolithic functions

---

# Logging

Every phase should log:

- Start
- Completion
- Number of records processed
- Warnings
- Errors

Important architectural decisions should also be logged.

Example

```
Using warehouse users for referential integrity.
```

or

```
Using current users batch for initial load.
```

---

# Required Test Scenarios

Every architectural change must preserve these tests.

## Test 1

Initial Full Load

Expected

- Full extract
- Warehouse created
- Warehouse populated successfully

---

## Test 2

No New Data

Expected

- Incremental extract
- No new records extracted
- No transformation
- Loader skips loading

---

## Test 3

New Records

Expected

- Incremental extraction
- Only new records extracted
- Referential integrity passes
- UPSERT loads new records

---

## Test 4

Updated Existing Record

Expected

- Existing warehouse row updated
- No duplicate primary key errors

---

## Test 5

Data Quality

Expected

- Invalid attendance_status rejected
- Duplicate attendance removed
- Referential integrity enforced

---

# Development Principles

Before changing ETL logic:

- Preserve the Source → Staging → Warehouse architecture.
- Prefer production ETL patterns over shortcuts.
- Explain architectural trade-offs before redesigning components.
- Consider the impact of changes across Extraction, Transformation, and Loading.
- Preserve backward compatibility unless explicitly asked to redesign.

---

# Do Not Change Without Explicit Request

Do not redesign these core behaviours unless explicitly requested:

- High-Water Mark incremental extraction
- Source → Staging → Warehouse architecture
- Staging truncation strategy
- Dimension full refresh
- Fact table UPSERT
- Data Quality Gate
- Incremental loading behaviour

---

# When Fixing Bugs

Do not patch only the symptom.

Identify:

1. Root cause
2. Architectural impact
3. Why the solution works
4. Whether existing test scenarios are preserved

Whenever possible, explain the reasoning before modifying the implementation.