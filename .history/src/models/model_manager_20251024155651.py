#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
统一管理模型加载、切换和设备检测
支持Qwen2.5和Mistral系列模型
"""

import os
import sys
import json
import yaml
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
        """从configs/model_config.yaml动态加载模型配置"""
        try:
            # 加载全局配置
            config_file = project_root / "configs" / "model_config.yaml"
            if not config_file.exists():
                logger.warning(f"配置文件不存在: {config_file}")
                return self._get_fallback_configs()

            with open(config_file, 'r', encoding='utf-8') as f:
                global_config = yaml.safe_load(f)

            # 提取可用模型列表
            available_models = global_config.get('available_models', {})
            model_configs = {}

            # 加载中文模型配置
            for model_name in available_models.get('chinese', []):
                config = self._load_single_model_config(model_name)
                if config:
                    model_configs[model_name] = config

            # 加载英文模型配置
            for model_name in available_models.get('english', []):
                config = self._load_single_model_config(model_name)
                if config:
                    model_configs[model_name] = config

            self.model_configs = model_configs
            logger.info(f"已加载 {len(self.model_configs)} 个模型配置")
            return self.model_configs

        except Exception as e:
            logger.error(f"加载模型配置失败: {e}")
            return self._get_fallback_configs()

    def _load_single_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """加载单个模型的配置文件"""
        try:
            config_file = project_root / "configs" / "models" / "available_models" / f"{model_name}.yaml"
            if not config_file.exists():
                logger.warning(f"模型配置文件不存在: {config_file}")
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 提取关键信息
            model_info = config.get('model', {})
            hw_req = config.get('hardware_requirements', {})

            # 获取第一个设备等级的硬件要求
            first_tier = None
            for key in hw_req.keys():
                if key.endswith('_tier'):
                    first_tier = hw_req[key]
                    break

            return {
                "name": model_info.get('display_name', model_name),
                "language": model_info.get('language', 'unknown'),
                "memory_required": self._parse_memory(first_tier.get('min_vram') if first_tier else '4GB'),
                "device_requirements": {
                    "min_vram": self._parse_memory(first_tier.get('min_vram') if first_tier else '4GB'),
                    "min_ram": self._parse_memory(first_tier.get('min_memory') if first_tier else '4GB')
                },
                "path": config.get('paths', {}).get('base', f"models/{model_name}"),
                "type": "LLM"
            }

        except Exception as e:
            logger.error(f"加载模型配置失败 {model_name}: {e}")
            return None

    def _parse_memory(self, memory_str: str) -> int:
        """解析内存字符串为MB"""
        if not memory_str:
            return 4000

        memory_str = str(memory_str).upper().replace(' ', '')
        if 'GB' in memory_str:
            return int(float(memory_str.replace('GB', '')) * 1024)
        elif 'MB' in memory_str:
            return int(memory_str.replace('MB', ''))
        else:
            return 4000

    def _get_fallback_configs(self) -> Dict[str, Any]:
        """获取回退配置（当配置文件加载失败时使用）"""
        logger.warning("使用回退配置")
        return {
            "qwen3-0.6b-zh": {
                "name": "Qwen3-0.6B-Instruct",
                "language": "zh",
                "memory_required": 3000,
                "device_requirements": {
                    "min_vram": 3000,
                    "min_ram": 3000
                },
                "path": "models/qwen/qwen3-0.6b",
                "type": "LLM"
            },
            "mistral-7b-en": {
                "name": "Mistral-7B-Instruct",
                "language": "en",
                "memory_required": 3500,
                "device_requirements": {
                    "min_vram": 3000,
                    "min_ram": 3000
                },
                "path": "models/mistral/mistral-7b",
                "type": "LLM"
            }
        }
    
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
