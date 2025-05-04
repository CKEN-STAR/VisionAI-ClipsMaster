"""
基础工具类
提供项目中常用的通用功能
"""

import os
import sys
import time
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from loguru import logger

class BaseUtils:
    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载YAML文件失败 {file_path}: {str(e)}")
            return {}

    @staticmethod
    def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """保存数据到YAML文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"保存YAML文件失败 {file_path}: {str(e)}")
            return False

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {str(e)}")
            return {}

    @staticmethod
    def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
        """保存数据到JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {str(e)}")
            return False

    @staticmethod
    def get_project_root() -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent.parent

    @staticmethod
    def ensure_dir(directory: Union[str, Path]) -> bool:
        """确保目录存在，如果不存在则创建"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录失败 {directory}: {str(e)}")
            return False

    @staticmethod
    def get_timestamp() -> str:
        """获取当前时间戳字符串"""
        return time.strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def format_time(seconds: float) -> str:
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> str:
        """获取文件大小的人类可读格式"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except Exception as e:
            logger.error(f"获取文件大小失败 {file_path}: {str(e)}")
            return "0B"

    @staticmethod
    def is_valid_file(file_path: Union[str, Path], required_extensions: Optional[List[str]] = None) -> bool:
        """
        检查文件是否有效
        
        Args:
            file_path: 文件路径
            required_extensions: 允许的文件扩展名列表，如 ['.mp4', '.avi']
        """
        if not os.path.exists(file_path):
            return False
        
        if required_extensions:
            return Path(file_path).suffix.lower() in required_extensions
        
        return True

class Timer:
    """简单的计时器类"""
    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        if self.name:
            logger.info(f"{self.name} 耗时: {BaseUtils.format_time(elapsed)}")
        return False  # 不吞没异常

    def reset(self):
        """重置计时器"""
        self.start_time = None
        self.end_time = None

    def elapsed(self) -> float:
        """获取经过的时间（秒）"""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time 