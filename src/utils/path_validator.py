#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
路径验证工具，确保数据和模型的物理隔离
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PathValidator:
    """路径验证器，用于确保数据和模型的物理隔离"""
    
    def __init__(self, config_path: str = "config/data_paths.json"):
        """
        初始化路径验证器
        
        Args:
            config_path: 数据路径配置文件路径
        """
        self.config_path = Path(config_path)
        self.load_config()
        
    def load_config(self) -> None:
        """加载路径配置"""
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
            
    def validate_all_paths(self) -> bool:
        """
        验证所有路径的物理隔离
        
        Returns:
            bool: 是否所有路径都符合要求
        """
        try:
            # 验证训练数据路径
            if not self._validate_training_paths():
                return False
                
            # 验证输入输出路径
            if not self._validate_io_paths():
                return False
                
            # 验证模型路径
            if not self._validate_model_paths():
                return False
                
            return True
        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            return False
            
    def _validate_training_paths(self) -> bool:
        """验证训练数据路径的隔离"""
        try:
            en_path = Path(self.config["training"]["en"]["subtitles"])
            zh_path = Path(self.config["training"]["zh"]["subtitles"])
            
            # 确保路径存在
            if not en_path.exists() or not zh_path.exists():
                logger.error("Training directories do not exist")
                return False
                
            # 确保是不同的目录
            if en_path.samefile(zh_path):
                logger.error("English and Chinese training paths are the same")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Training path validation failed: {e}")
            return False
            
    def _validate_io_paths(self) -> bool:
        """验证输入输出路径的隔离"""
        try:
            paths = [
                Path(self.config["input"]["en_videos"]),
                Path(self.config["input"]["zh_videos"]),
                Path(self.config["output"]["en_generated"]),
                Path(self.config["output"]["zh_generated"])
            ]
            
            # 确保所有路径都存在
            for path in paths:
                if not path.exists():
                    logger.error(f"Path does not exist: {path}")
                    return False
                    
            # 确保所有路径都是不同的
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    if paths[i].samefile(paths[j]):
                        logger.error(f"Paths are the same: {paths[i]} and {paths[j]}")
                        return False
                        
            return True
        except Exception as e:
            logger.error(f"IO path validation failed: {e}")
            return False
            
    def _validate_model_paths(self) -> bool:
        """验证模型路径的隔离"""
        try:
            en_paths = [
                Path(self.config["models"]["en"]["base"]),
                Path(self.config["models"]["en"]["quantized"])
            ]
            
            zh_paths = [
                Path(self.config["models"]["zh"]["base"]),
                Path(self.config["models"]["zh"]["quantized"])
            ]
            
            # 确保所有路径都存在
            for path in en_paths + zh_paths:
                if not path.exists():
                    logger.error(f"Model path does not exist: {path}")
                    return False
                    
            # 确保英文和中文模型路径是隔离的
            for en_path in en_paths:
                for zh_path in zh_paths:
                    if en_path.samefile(zh_path):
                        logger.error(f"English and Chinese model paths overlap: {en_path}")
                        return False
                        
            return True
        except Exception as e:
            logger.error(f"Model path validation failed: {e}")
            return False
            
    def ensure_path_exists(self, path: str) -> bool:
        """
        确保路径存在，如果不存在则创建
        
        Args:
            path: 要确保存在的路径
            
        Returns:
            bool: 是否成功确保路径存在
        """
        try:
            path = Path(path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to ensure path exists: {e}")
            return False
            
    def get_path(self, path_key: str) -> Optional[Path]:
        """
        获取配置中的路径
        
        Args:
            path_key: 路径键名，例如 "training.en.subtitles"
            
        Returns:
            Optional[Path]: 路径对象，如果不存在则返回None
        """
        try:
            keys = path_key.split(".")
            value = self.config
            for key in keys:
                value = value[key]
            return Path(value)
        except Exception as e:
            logger.error(f"Failed to get path {path_key}: {e}")
            return None

def validate_paths() -> bool:
    """
    验证所有路径的物理隔离
    
    Returns:
        bool: 是否所有路径都符合要求
    """
    try:
        validator = PathValidator()
        return validator.validate_all_paths()
    except Exception as e:
        logger.error(f"Path validation failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if validate_paths():
        logger.info("All paths are properly isolated")
    else:
        logger.error("Path validation failed") 