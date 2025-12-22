"""
UI层GPU检测适配器
提供 get_gpu_detector()，向后兼容从 ui.hardware.gpu_detector 导入。
底层使用 src.utils.gpu_detector.SafeGPUDetector。
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    # 依赖顶层包结构：src 为有效包
    from src.utils.gpu_detector import SafeGPUDetector  # type: ignore
except Exception as e:
    SafeGPUDetector = None  # type: ignore
    logger.warning(f"导入SafeGPUDetector失败: {e}")


def get_gpu_detector():
    """返回一个GPU检测器实例。
    若底层导入失败，返回None，调用方需自行降级到CPU。
    """
    if SafeGPUDetector is None:
        return None
    try:
        return SafeGPUDetector()
    except Exception as e:
        logger.warning(f"创建SafeGPUDetector失败: {e}")
        return None


__all__ = ["get_gpu_detector"]

