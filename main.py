import sqlalchemy
import logging
import time
from sqlalchemy import text
from pipeline.extractor import IncrementalExtractor
from pipeline.transformer import DataCleaner
from pipeline.loader import WarehouseLoader
from pipeline.exceptions import PipelineError, ExtractionError, TransformationError, LoadingError
from db_manager import DatabaseManager
from config import settings

logger = logging.getLogger(__name__)

def clear_staging() -> None:
    """
    Truncates all staging tables to ensure that only the current batch of data
    is processed. This prevents data duplication in the warehouse if a previous
    run failed after extraction but before loading.
    """
    logger.info("Clearing staging area...")
    staging_engine = DatabaseManager.get_engine(settings.STAGING_DB)
    with staging_engine.connect() as conn:
        for table in settings.EXTRACT_TABLES:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table}"))
                logger.info(f"Truncated staging table: {table}")
            except sqlalchemy.exc.ProgrammingError as e:
                # Error 1146 is "Table doesn't exist".
                # This is expected on the very first run of the pipeline.
                if "1146" in str(e):
                    logger.info(f"Staging table {table} does not exist yet. Skipping truncation.")
                else:
                    raise e
        conn.commit()

def run_pipeline() -> None:
    logger.info("Starting Attendance Data Pipeline...")
    logger.info("-" * 40)

    try:
        # 0. PRE-CLEANUP: Ensure staging is empty before starting.
        # This guarantees that the Transformer only sees data from the current incremental pull.
        clear_staging()

        # 1. EXTRACT: Source -> Staging
        logger.info("[Phase 1: Extraction]")
        extractor = IncrementalExtractor()
        extractor.run()

        # 2. TRANSFORM: Staging -> Pandas (Cleaned)
        logger.info("[Phase 2: Transformation]")
        transformer = DataCleaner()
        cleaned_data = transformer.run()

        # 3. LOAD: Pandas (Cleaned) -> Warehouse
        logger.info("[Phase 3: Loading]")
        loader = WarehouseLoader()
        loader.run(cleaned_data)

        # 4. POST-CLEANUP: Clear staging after successful load to keep environment lean.
        clear_staging()

        logger.info("-" * 40)
        logger.info("Pipeline completed successfully!")

    except ExtractionError as e:
        logger.critical(f"CRITICAL ERROR during Extraction: {e}")
    except TransformationError as e:
        logger.critical(f"CRITICAL ERROR during Transformation: {e}")
    except LoadingError as e:
        logger.critical(f"CRITICAL ERROR during Loading: {e}")
    except PipelineError as e:
        logger.critical(f"General Pipeline Error: {e}")
    except Exception as e:
        logger.error("Unexpected system failure!")
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run_pipeline()
