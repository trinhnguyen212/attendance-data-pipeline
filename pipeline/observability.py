import json
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

@dataclass
class RunReport:
    """
    Tracks the lineage and quality metrics of a single pipeline execution.
    """
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "started"

    # Extraction Metrics
    extracted_rows: Dict[str, int] = field(default_factory=dict)

    # Transformation Metrics
    rows_dropped: Dict[str, int] = field(default_factory=lambda: {
        "null_critical_fields": 0,
        "invalid_status": 0,
        "duplicates": 0,
        "referential_integrity": 0
    })

    # Loading Metrics
    loaded_rows: Dict[str, int] = field(default_factory=dict)

    def finalize(self, status: str = "success"):
        self.end_time = datetime.now()
        self.status = status

    def get_duration(self) -> float:
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['duration_seconds'] = self.get_duration()

        # Calculate total rows processed
        total_extracted = sum(self.extracted_rows.values())
        total_loaded = sum(self.loaded_rows.values())
        data['total_extracted'] = total_extracted
        data['total_loaded'] = total_loaded
        data['net_drop_rate'] = (
            (total_extracted - total_loaded) / total_extracted
            if total_extracted > 0 else 0
        )

        return data

    def save(self, path: str = None):
        if path is None:
            timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
            path = f"run_report_{timestamp}.json"

        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)
