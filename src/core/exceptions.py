"""
异常导入桥接模块

从utils.exceptions导入所有异常类，使其可以通过core.exceptions访问
"""

from src.utils.exceptions import (
    ClipMasterError,
    ErrorCode,
    MemoryOverflowError,
    ModelCorruptionError,
    UserInputError,
    ResourceError,
    HybridContentError,
    LanguageDetectionError,
    NarrativeAnalysisError,
    VideoProcessError,
    AudioProcessError,
    InvalidSRTError,
    ModelLoadError,
    SecurityError,
    ValidationError,
    FileOperationError,
    ProcessTimeoutError as TimeoutError,
    ResourceExhaustionError,
)

__all__ = [
    'ClipMasterError',
    'ErrorCode',
    'MemoryOverflowError',
    'ModelCorruptionError',
    'UserInputError',
    'ResourceError',
    'HybridContentError',
    'LanguageDetectionError',
    'NarrativeAnalysisError',
    'VideoProcessError',
    'AudioProcessError',
    'InvalidSRTError',
    'ModelLoadError',
    'SecurityError',
    'ValidationError',
    'FileOperationError',
    'TimeoutError',
    'ResourceExhaustionError',
]

class QualityCheckError(Exception):
    """质量检查错误基类"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}
        
    def __str__(self):
        return f"{self.__class__.__name__}: {super().__str__()}"

class QualityThresholdError(QualityCheckError):
    """质量阈值未达到错误"""
    def __init__(self, message: str, threshold: float, actual: float, metric: str, details: dict = None):
        details = details or {}
        details.update({
            'threshold': threshold,
            'actual': actual,
            'metric': metric
        })
        super().__init__(message, details)

class ProbeInsertionError(QualityCheckError):
    """探针插入错误"""
    pass

class MetricsCollectionError(QualityCheckError):
    """指标收集错误"""
    pass
