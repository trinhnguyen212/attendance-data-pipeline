class PipelineError(Exception):
    """Base class for all pipeline exceptions"""
    pass

class ExtractionError(PipelineError):
    """Raised when extraction phase fails"""
    pass

class TransformationError(PipelineError):
    """Raised when transformation phase fails"""
    pass

class LoadingError(PipelineError):
    """Raised when loading phase fails"""
    pass

class DataQualityError(PipelineError):
    """Raised when data quality fails the defined thresholds"""
    pass
