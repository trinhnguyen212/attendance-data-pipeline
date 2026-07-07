import sqlalchemy
from extractor import IncrementalExtractor
from transformer import DataCleaner
from loader import WarehouseLoader

def run_pipeline():
    print("Starting Attendance Data Pipeline...")
    print("-" * 40)

    try:
        # 1. EXTRACT: Source -> Staging
        print("\n[Phase 1: Extraction]")
        extractor = IncrementalExtractor()
        extractor.run()

        # 2. TRANSFORM: Staging -> Pandas (Cleaned)
        print("\n[Phase 2: Transformation]")
        transformer = DataCleaner()
        cleaned_data = transformer.run()

        # 3. LOAD: Pandas (Cleaned) -> Warehouse
        print("\n[Phase 3: Loading]")
        loader = WarehouseLoader()
        loader.run(cleaned_data)

        print("-" * 40)
        print("Pipeline completed successfully!")

    except Exception as e:
        print("\nPipeline failed!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_pipeline()
