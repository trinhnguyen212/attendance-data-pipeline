import sqlalchemy
import logging
import time
from pipeline.extractor import IncrementalExtractor
from pipeline.transformer import DataCleaner
from pipeline.loader import WarehouseLoader
from pipeline.exceptions import PipelineError, ExtractionError, TransformationError, LoadingError
from pipeline.observability import RunReport

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    logger.info("Starting Attendance Data Pipeline...")
    logger.info("-" * 40)

    # Initialize observability report
    report = RunReport()

    try:
        # 1. EXTRACT: Source -> Staging
        logger.info("[Phase 1: Extraction]")
        extractor = IncrementalExtractor()
        extracted_counts = extractor.run()
        report.extracted_rows = extracted_counts

        # 2. TRANSFORM: Staging -> Pandas (Cleaned)
        logger.info("[Phase 2: Transformation]")
        transformer = DataCleaner()
        cleaned_data, transformation_metrics = transformer.run()
        report.rows_dropped = transformation_metrics

        # 3. LOAD: Pandas (Cleaned) -> Warehouse
        logger.info("[Phase 3: Loading]")
        loader = WarehouseLoader()
        loaded_counts = loader.run(cleaned_data)
        report.loaded_rows = loaded_counts

        logger.info("-" * 40)
        logger.info("Pipeline completed successfully!")

        report.finalize(status="success")

    except ExtractionError as e:
        logger.critical(f"CRITICAL ERROR during Extraction: {e}")
        report.finalize(status=f"failed: extraction_error")
    except TransformationError as e:
        logger.critical(f"CRITICAL ERROR during Transformation: {e}")
        report.finalize(status=f"failed: transformation_error")
    except LoadingError as e:
        logger.critical(f"CRITICAL ERROR during Loading: {e}")
        report.finalize(status=f"failed: loading_error")
    except PipelineError as e:
        logger.critical(f"General Pipeline Error: {e}")
        report.finalize(status=f"failed: pipeline_error")
    except Exception as e:
        logger.error("Unexpected system failure!")
        logger.error(f"Error: {e}", exc_info=True)
        report.finalize(status=f"failed: unexpected_error")
    finally:
        # Save the run report to JSON
        report.save()
        logger.info(f"Run report saved. Total extracted: {sum(report.extracted_rows.values())}, Total loaded: {sum(report.loaded_rows.values())}")

if __name__ == "__main__":
    run_pipeline()
