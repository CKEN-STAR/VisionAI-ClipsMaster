"""
VisionAI-ClipsMaster SDK - Python客户端

用于轻松与VisionAI-ClipsMaster API交互的SDK
"""

from .client import ClipsMasterClient, APIError, ClipRequest, TaskStatus

__version__ = "1.0.0"
__author__ = "VisionAI Team"

__all__ = ["ClipsMasterClient", "APIError", "ClipRequest", "TaskStatus"] 