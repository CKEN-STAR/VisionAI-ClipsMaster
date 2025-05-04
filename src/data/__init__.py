"""
数据处理核心模块

提供数据加载、处理和管理的核心功能。
包括数据湖、数据清洗、数据转换和特征工程等。
"""

from pathlib import Path
import os
import sys

# 确保数据目录存在
DATA_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(DATA_ROOT / "lake", exist_ok=True)
os.makedirs(DATA_ROOT / "cache", exist_ok=True)

# 导出公共API
from .hit_pattern_lake import HitPatternLake, convert_to_parquet

__all__ = [
    'HitPatternLake',
    'convert_to_parquet'
] 