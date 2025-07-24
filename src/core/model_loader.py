#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模型加载器

负责加载、管理和提供大模型接口。
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List

from src.utils.config_manager import get_config

# 配置日志
logging.basicConfig(level=logging.INFO,
                  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("model_loader")

class ModelLoader:
    """模型加载器
    
    负责加载和管理大模型，支持中英文模型的按需加载。
    """
    
    def __init__(self):
        """初始化模型加载器"""
        # 加载配置
        self.config = get_config("models")
        
        # 模型缓存
        self.models = {}
        
        # 模拟一些模型属性
        self.chinese_model_path = "models/chinese/Qwen2.5-7B"
        self.english_model_path = "models/english/Mistral-7B" 
        
        logger.info("模型加载器初始化完成")
    
    def load_chinese_model(self) -> Dict[str, Any]:
        """加载中文模型
        
        Returns:
            Dict[str, Any]: 加载的模型信息
        """
        model_config = self.config.get("chinese", {})
        
        if "chinese" in self.models:
            logger.info("中文模型已加载，直接返回")
            return self.models["chinese"]
        
        # 模拟模型加载过程
        logger.info(f"加载中文模型: {model_config.get('name')}")
        time.sleep(0.5)  # 模拟加载时间
        
        # 模拟模型对象
        model = {
            "name": model_config.get("name"),
            "loaded_at": time.time(),
            "quantized": model_config.get("use_quantization", False),
            "quant_level": model_config.get("quantization_level", 0) if model_config.get("use_quantization", False) else None
        }
        
        # 缓存模型
        self.models["chinese"] = model
        
        logger.info("中文模型加载完成")
        return model
    
    def load_english_model(self) -> Dict[str, Any]:
        """加载英文模型
        
        Returns:
            Dict[str, Any]: 加载的模型信息
        """
        model_config = self.config.get("english", {})
        
        if "english" in self.models:
            logger.info("英文模型已加载，直接返回")
            return self.models["english"]
        
        # 模拟模型加载过程
        logger.info(f"加载英文模型: {model_config.get('name')}")
        time.sleep(0.5)  # 模拟加载时间
        
        # 模拟模型对象
        model = {
            "name": model_config.get("name"),
            "loaded_at": time.time(),
            "quantized": model_config.get("use_quantization", False),
            "quant_level": model_config.get("quantization_level", 0) if model_config.get("use_quantization", False) else None
        }
        
        # 缓存模型
        self.models["english"] = model
        
        logger.info("英文模型加载完成")
        return model
    
    def unload_model(self, language: str) -> bool:
        """卸载指定语言的模型
        
        Args:
            language: 模型语言，支持"chinese"或"english"
            
        Returns:
            bool: 是否成功卸载
        """
        if language in self.models:
            logger.info(f"卸载{language}模型")
            del self.models[language]
            return True
        
        return False
    
    def unload_all_models(self) -> None:
        """卸载所有模型"""
        logger.info("卸载所有模型")
        self.models = {}

    def load_quantized_model(self, model_name: str, quantization: str = "Q4_K_M") -> Dict[str, Any]:
        """加载量化模型

        Args:
            model_name: 模型名称
            quantization: 量化级别 (Q2_K, Q4_K_M, Q5_K, Q8_0等)

        Returns:
            Dict[str, Any]: 加载的量化模型信息
        """
        try:
            logger.info(f"开始加载量化模型: {model_name}, 量化级别: {quantization}")

            # 检查是否已经加载
            cache_key = f"{model_name}_{quantization}"
            if cache_key in self.models:
                logger.info(f"量化模型已缓存，直接返回: {cache_key}")
                return self.models[cache_key]

            # 验证量化级别
            supported_quantizations = ["Q2_K", "Q4_K_M", "Q5_K", "Q8_0", "F16", "F32"]
            if quantization not in supported_quantizations:
                logger.warning(f"不支持的量化级别: {quantization}, 使用默认Q4_K_M")
                quantization = "Q4_K_M"

            # 模拟量化模型加载过程
            start_time = time.time()

            # 根据量化级别计算内存占用和加载时间
            quantization_info = self._get_quantization_info(quantization)
            load_time = quantization_info["load_time"]
            memory_usage = quantization_info["memory_mb"]

            # 模拟加载延迟
            time.sleep(load_time)

            # 创建量化模型对象
            quantized_model = {
                "name": model_name,
                "quantization": quantization,
                "memory_usage_mb": memory_usage,
                "load_time": time.time() - start_time,
                "loaded_at": time.time(),
                "status": "loaded",
                "precision": quantization_info["precision"],
                "performance_score": quantization_info["performance"],
                "cache_key": cache_key
            }

            # 缓存模型
            self.models[cache_key] = quantized_model

            logger.info(f"量化模型加载完成: {model_name}, 内存占用: {memory_usage}MB, 耗时: {quantized_model['load_time']:.2f}s")
            return quantized_model

        except Exception as e:
            logger.error(f"加载量化模型失败: {e}")
            return {
                "name": model_name,
                "quantization": quantization,
                "status": "failed",
                "error": str(e),
                "loaded_at": time.time()
            }

    def _get_quantization_info(self, quantization: str) -> Dict[str, Any]:
        """获取量化级别信息

        Args:
            quantization: 量化级别

        Returns:
            Dict[str, Any]: 量化信息
        """
        quantization_map = {
            "Q2_K": {
                "precision": "2-bit",
                "memory_mb": 2800,  # 约2.8GB
                "load_time": 0.3,
                "performance": 0.75
            },
            "Q4_K_M": {
                "precision": "4-bit",
                "memory_mb": 4100,  # 约4.1GB
                "load_time": 0.5,
                "performance": 0.85
            },
            "Q5_K": {
                "precision": "5-bit",
                "memory_mb": 5200,  # 约5.2GB
                "load_time": 0.7,
                "performance": 0.92
            },
            "Q8_0": {
                "precision": "8-bit",
                "memory_mb": 7500,  # 约7.5GB
                "load_time": 1.0,
                "performance": 0.98
            },
            "F16": {
                "precision": "16-bit float",
                "memory_mb": 13000,  # 约13GB
                "load_time": 1.5,
                "performance": 0.99
            },
            "F32": {
                "precision": "32-bit float",
                "memory_mb": 26000,  # 约26GB
                "load_time": 2.0,
                "performance": 1.0
            }
        }

        return quantization_map.get(quantization, quantization_map["Q4_K_M"])

    def get_model_memory_usage(self) -> Dict[str, float]:
        """获取所有已加载模型的内存占用

        Returns:
            Dict[str, float]: 模型内存占用信息 (MB)
        """
        memory_usage = {}
        total_memory = 0.0

        for model_key, model_info in self.models.items():
            memory_mb = model_info.get("memory_usage_mb", 0)
            memory_usage[model_key] = memory_mb
            total_memory += memory_mb

        memory_usage["total"] = total_memory
        return memory_usage

    def check_memory_limit(self, limit_mb: float = 3800) -> Dict[str, Any]:
        """检查内存使用是否超过限制

        Args:
            limit_mb: 内存限制 (MB)，默认3.8GB

        Returns:
            Dict[str, Any]: 内存检查结果
        """
        memory_usage = self.get_model_memory_usage()
        total_memory = memory_usage.get("total", 0)

        result = {
            "total_memory_mb": total_memory,
            "limit_mb": limit_mb,
            "within_limit": total_memory <= limit_mb,
            "usage_percentage": (total_memory / limit_mb) * 100 if limit_mb > 0 else 0,
            "available_mb": max(0, limit_mb - total_memory),
            "models": memory_usage
        }

        if not result["within_limit"]:
            logger.warning(f"内存使用超限: {total_memory:.1f}MB > {limit_mb:.1f}MB")

        return result

# 模型加载器实例
_model_loader = None

def get_model_loader() -> ModelLoader:
    """获取模型加载器实例（单例模式）
    
    Returns:
        ModelLoader: 模型加载器实例
    """
    global _model_loader
    
    if _model_loader is None:
        _model_loader = ModelLoader()
    
    return _model_loader 