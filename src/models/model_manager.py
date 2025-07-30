#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
统一管理模型加载、切换和设备检测
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class ModelManager:
    """模型管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化模型管理器
        
        Args:
            config_path: 模型配置文件路径
        """
        self.config_path = config_path
        self.current_model = None
        self.current_device = "cpu"
        self.model_configs = {}
        self.load_model_configs()
        
        logger.info("模型管理器初始化完成")
    
    def load_model_configs(self) -> Dict[str, Any]:
        """加载模型配置"""
        try:
            # 默认模型配置
            default_configs = {
                "qwen2.5-7b-zh": {
                    "name": "Qwen2.5-7B-Instruct",
                    "language": "zh",
                    "memory_required": 8000,  # MB
                    "device_requirements": {
                        "min_vram": 8000,
                        "min_ram": 16000
                    },
                    "path": "models/qwen2.5-7b-instruct",
                    "type": "LLM"
                },
                "mistral-7b-en": {
                    "name": "Mistral-7B-Instruct",
                    "language": "en", 
                    "memory_required": 7000,  # MB
                    "device_requirements": {
                        "min_vram": 7000,
                        "min_ram": 14000
                    },
                    "path": "models/mistral-7b-instruct",
                    "type": "LLM"
                }
            }
            
            # 如果有配置文件，尝试加载
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_configs = json.load(f)
                    default_configs.update(file_configs)
            
            self.model_configs = default_configs
            logger.info(f"已加载 {len(self.model_configs)} 个模型配置")
            return self.model_configs
            
        except Exception as e:
            logger.error(f"加载模型配置失败: {e}")
            self.model_configs = {}
            return {}
    
    def load_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.model_configs
    
    def detect_device(self) -> str:
        """检测可用设备"""
        try:
            # 尝试检测CUDA
            try:
                import torch
                if torch.cuda.is_available():
                    device_name = torch.cuda.get_device_name(0)
                    vram = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024  # MB
                    self.current_device = "cuda"
                    logger.info(f"检测到GPU: {device_name} ({vram:.0f}MB)")
                    return f"cuda ({device_name})"
                else:
                    self.current_device = "cpu"
                    logger.info("未检测到可用GPU，使用CPU")
                    return "cpu"
            except ImportError:
                self.current_device = "cpu"
                logger.info("PyTorch未安装，使用CPU")
                return "cpu"
                
        except Exception as e:
            logger.error(f"设备检测失败: {e}")
            self.current_device = "cpu"
            return "cpu"
    
    def load_model_for_language(self, language: str) -> Dict[str, Any]:
        """为指定语言加载模型
        
        Args:
            language: 语言代码 (zh/en)
            
        Returns:
            模型信息字典
        """
        try:
            # 根据语言选择模型
            model_name = None
            for name, config in self.model_configs.items():
                if config.get("language") == language:
                    model_name = name
                    break
            
            if not model_name:
                # 默认模型
                model_name = "qwen2.5-7b-zh" if language == "zh" else "mistral-7b-en"
            
            model_config = self.model_configs.get(model_name, {})
            
            # 检测设备
            device = self.detect_device()
            
            # 模拟模型加载
            model_info = {
                "model_name": model_name,
                "language": language,
                "device": device,
                "config": model_config,
                "status": "loaded",
                "memory_usage": model_config.get("memory_required", 0)
            }
            
            self.current_model = model_info
            logger.info(f"已为语言 {language} 加载模型: {model_name}")
            
            return model_info
            
        except Exception as e:
            logger.error(f"为语言 {language} 加载模型失败: {e}")
            return {"status": "failed", "error": str(e)}
    
    def switch_to_cpu_mode(self) -> bool:
        """切换到CPU模式"""
        try:
            self.current_device = "cpu"
            if self.current_model:
                self.current_model["device"] = "cpu"
            logger.info("已切换到CPU模式")
            return True
        except Exception as e:
            logger.error(f"切换到CPU模式失败: {e}")
            return False
    
    def switch_to_gpu_mode(self) -> bool:
        """切换到GPU模式"""
        try:
            device = self.detect_device()
            if "cuda" in device:
                self.current_device = "cuda"
                if self.current_model:
                    self.current_model["device"] = "cuda"
                logger.info("已切换到GPU模式")
                return True
            else:
                logger.warning("无可用GPU，保持CPU模式")
                return False
        except Exception as e:
            logger.error(f"切换到GPU模式失败: {e}")
            return False
    
    def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """获取当前模型信息"""
        return self.current_model
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.model_configs.keys())
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            import psutil
            
            # 系统内存信息
            memory = psutil.virtual_memory()
            
            # 模型内存使用
            model_memory = 0
            if self.current_model:
                model_memory = self.current_model.get("memory_usage", 0)
            
            return {
                "total_memory_mb": memory.total / 1024 / 1024,
                "available_memory_mb": memory.available / 1024 / 1024,
                "used_memory_mb": memory.used / 1024 / 1024,
                "model_memory_mb": model_memory,
                "memory_percent": memory.percent
            }
            
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {e}")
            return {"error": str(e)}
    
    def unload_current_model(self) -> bool:
        """卸载当前模型"""
        try:
            if self.current_model:
                logger.info(f"卸载模型: {self.current_model.get('model_name', 'unknown')}")
                self.current_model = None
                return True
            else:
                logger.info("没有已加载的模型")
                return True
        except Exception as e:
            logger.error(f"卸载模型失败: {e}")
            return False

# 全局实例
_model_manager = None

def get_model_manager() -> ModelManager:
    """获取全局模型管理器实例"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

if __name__ == "__main__":
    # 测试模型管理器
    manager = ModelManager()
    
    print("=== 模型管理器测试 ===")
    
    # 测试设备检测
    device = manager.detect_device()
    print(f"检测到设备: {device}")
    
    # 测试模型配置加载
    configs = manager.load_model_config()
    print(f"加载了 {len(configs)} 个模型配置")
    
    # 测试为中文加载模型
    zh_model = manager.load_model_for_language("zh")
    print(f"中文模型: {zh_model}")
    
    # 测试内存使用
    memory_info = manager.get_memory_usage()
    print(f"内存使用: {memory_info}")
    
    # 测试模式切换
    cpu_switch = manager.switch_to_cpu_mode()
    print(f"切换到CPU模式: {cpu_switch}")
