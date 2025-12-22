#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志处理模块 - 简化版（UI演示用）
"""

import logging
import os
import sys
from pathlib import Path

# 确保日志目录存在
logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
logs_dir.mkdir(exist_ok=True)

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(logs_dir / "visionai.log", encoding="utf-8")
    ]
)

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)

def check_spacy() -> bool:
    """检查spaCy是否可用

    Returns:
        bool: 是否可用
    """
    logger = get_logger("utils.log_handler")
    try:
        import spacy
        version = getattr(spacy, "__version__", "未知")
        logger.info(f"spaCy可用: 版本 {version}")
        return True
    except ImportError:
        logger.warning("spaCy未安装，将使用备用方法进行NLP处理")
        return False



class LogHandler:
    """简易性能日志处理器，兼容中间件调用接口。"""
    def __init__(self):
        self.logger = get_logger("performance")

    def log_performance_metric(self, metric_name: str, value: float, unit: str = "ms", **kwargs):
        try:
            extra = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            suffix = f" ({extra})" if extra else ""
            self.logger.info(f"{metric_name}: {value:.2f}{unit}{suffix}")
        except Exception:
            # 兜底，避免影响主流程
            self.logger.info(f"{metric_name}: {value}{unit}")
