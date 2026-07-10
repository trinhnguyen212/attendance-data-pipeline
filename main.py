import sqlalchemy
import logging
from extractor import IncrementalExtractor
from transformer import DataCleaner
from loader import WarehouseLoader

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    logger.info("Starting Attendance Data Pipeline...")
    logger.info("-" * 40)

    try:
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

        logger.info("-" * 40)
        logger.info("Pipeline completed successfully!")

    except Exception as e:
        logger.error("Pipeline failed!")
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run_pipeline()
