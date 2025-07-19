#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增强版动态模型加载器
专门针对4GB内存约束下的稳定运行进行优化
"""

import os
import gc
import time
import psutil
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import OrderedDict
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class ModelLoadRequest:
    """模型加载请求"""
    model_name: str
    language: str
    priority: int = 0
    force_load: bool = False
    memory_limit: int = 3800  # MB
    timeout: int = 30  # 秒

@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    language: str
    memory_usage: int
    load_time: float
    last_used: float
    is_active: bool
    model_object: Any = None

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, memory_limit: int = 3800):
        """
        初始化内存监控器
        
        Args:
            memory_limit: 内存限制(MB)
        """
        self.memory_limit = memory_limit * 1024 * 1024  # 转换为字节
        self.process = psutil.Process()
        
    def get_current_memory(self) -> int:
        """获取当前内存使用量(字节)"""
        try:
            return self.process.memory_info().rss
        except Exception as e:
            logger.error(f"获取内存信息失败: {str(e)}")
            return 0
    
    def get_available_memory(self) -> int:
        """获取可用内存(字节)"""
        current = self.get_current_memory()
        return max(0, self.memory_limit - current)
    
    def is_memory_available(self, required: int) -> bool:
        """检查是否有足够内存"""
        available = self.get_available_memory()
        return available >= required
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        current = self.get_current_memory()
        return {
            "current_mb": current / 1024 / 1024,
            "limit_mb": self.memory_limit / 1024 / 1024,
            "available_mb": (self.memory_limit - current) / 1024 / 1024,
            "usage_percent": (current / self.memory_limit) * 100
        }

class LRUModelCache:
    """LRU模型缓存"""
    
    def __init__(self, max_models: int = 2):
        """
        初始化LRU缓存
        
        Args:
            max_models: 最大缓存模型数量
        """
        self.max_models = max_models
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, model_name: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        with self.lock:
            if model_name in self.cache:
                # 移动到最近使用位置
                model_info = self.cache.pop(model_name)
                self.cache[model_name] = model_info
                model_info.last_used = time.time()
                return model_info
            return None
    
    def put(self, model_name: str, model_info: ModelInfo) -> Optional[ModelInfo]:
        """添加模型到缓存，返回被移除的模型"""
        with self.lock:
            evicted_model = None
            
            # 如果模型已存在，更新它
            if model_name in self.cache:
                self.cache.pop(model_name)
            
            # 如果缓存已满，移除最少使用的模型
            elif len(self.cache) >= self.max_models:
                oldest_name, evicted_model = self.cache.popitem(last=False)
                logger.info(f"从缓存中移除模型: {oldest_name}")
            
            # 添加新模型
            self.cache[model_name] = model_info
            model_info.last_used = time.time()
            
            return evicted_model
    
    def remove(self, model_name: str) -> Optional[ModelInfo]:
        """从缓存中移除模型"""
        with self.lock:
            return self.cache.pop(model_name, None)
    
    def get_cached_models(self) -> List[str]:
        """获取缓存中的模型列表"""
        with self.lock:
            return list(self.cache.keys())
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

class EnhancedModelLoader:
    """增强版动态模型加载器"""
    
    def __init__(self, memory_limit: int = 3800):
        """
        初始化增强版模型加载器
        
        Args:
            memory_limit: 内存限制(MB)
        """
        self.memory_limit = memory_limit
        self.memory_monitor = MemoryMonitor(memory_limit)
        self.model_cache = LRUModelCache(max_models=2)
        self.load_lock = threading.RLock()
        
        # 当前活动模型
        self.active_model = None
        self.active_language = None
        
        # 加载统计
        self.load_stats = {
            "total_loads": 0,
            "successful_loads": 0,
            "failed_loads": 0,
            "cache_hits": 0,
            "memory_evictions": 0
        }
        
        logger.info(f"增强版模型加载器初始化完成，内存限制: {memory_limit}MB")
    
    def load_model(self, request: ModelLoadRequest) -> bool:
        """
        加载模型
        
        Args:
            request: 模型加载请求
            
        Returns:
            bool: 是否加载成功
        """
        with self.load_lock:
            try:
                logger.info(f"开始加载模型: {request.model_name}")
                self.load_stats["total_loads"] += 1
                
                # 检查缓存
                cached_model = self.model_cache.get(request.model_name)
                if cached_model and not request.force_load:
                    logger.info(f"从缓存加载模型: {request.model_name}")
                    self.active_model = cached_model
                    self.active_language = request.language
                    self.load_stats["cache_hits"] += 1
                    return True
                
                # 检查内存需求
                required_memory = request.memory_limit * 1024 * 1024  # 转换为字节
                if not self._ensure_memory_available(required_memory):
                    logger.error(f"内存不足，无法加载模型: {request.model_name}")
                    self.load_stats["failed_loads"] += 1
                    return False
                
                # 实际加载模型
                model_object = self._load_model_object(request)
                if not model_object:
                    self.load_stats["failed_loads"] += 1
                    return False
                
                # 创建模型信息
                model_info = ModelInfo(
                    name=request.model_name,
                    language=request.language,
                    memory_usage=self._estimate_model_memory(model_object),
                    load_time=time.time(),
                    last_used=time.time(),
                    is_active=True,
                    model_object=model_object
                )
                
                # 添加到缓存
                evicted_model = self.model_cache.put(request.model_name, model_info)
                if evicted_model:
                    self._unload_model_object(evicted_model)
                    self.load_stats["memory_evictions"] += 1
                
                # 更新活动模型
                self.active_model = model_info
                self.active_language = request.language
                
                self.load_stats["successful_loads"] += 1
                logger.info(f"模型加载成功: {request.model_name}")
                
                # 打印内存统计
                memory_stats = self.memory_monitor.get_memory_stats()
                logger.info(f"内存使用: {memory_stats['current_mb']:.1f}MB / {memory_stats['limit_mb']:.1f}MB ({memory_stats['usage_percent']:.1f}%)")
                
                return True
                
            except Exception as e:
                logger.error(f"加载模型失败: {str(e)}")
                self.load_stats["failed_loads"] += 1
                return False
    
    def switch_language(self, language: str) -> bool:
        """
        切换到指定语言的模型
        
        Args:
            language: 语言代码(zh/en)
            
        Returns:
            bool: 是否切换成功
        """
        try:
            # 获取语言对应的模型名称
            from configs.model_config import load_model_config
            config = load_model_config()
            default_models = config.get("default_models", {})
            
            if language not in default_models:
                logger.error(f"不支持的语言: {language}")
                return False
            
            model_name = default_models[language]
            
            # 如果当前已经是该语言，无需切换
            if self.active_language == language and self.active_model and self.active_model.name == model_name:
                logger.info(f"当前已经是{language}语言模型: {model_name}")
                return True
            
            # 创建加载请求
            request = ModelLoadRequest(
                model_name=model_name,
                language=language,
                priority=1,
                force_load=False
            )
            
            return self.load_model(request)
            
        except Exception as e:
            logger.error(f"语言切换失败: {str(e)}")
            return False
    
    def get_current_model(self) -> Optional[Any]:
        """获取当前活动模型对象"""
        if self.active_model:
            return self.active_model.model_object
        return None
    
    def get_load_stats(self) -> Dict[str, Any]:
        """获取加载统计信息"""
        memory_stats = self.memory_monitor.get_memory_stats()
        return {
            **self.load_stats,
            "memory_stats": memory_stats,
            "cached_models": self.model_cache.get_cached_models(),
            "active_model": self.active_model.name if self.active_model else None,
            "active_language": self.active_language
        }

    def _ensure_memory_available(self, required_memory: int) -> bool:
        """确保有足够的内存可用"""
        try:
            # 检查当前可用内存
            if self.memory_monitor.is_memory_available(required_memory):
                return True

            logger.info("内存不足，尝试释放缓存模型")

            # 尝试释放非活动模型
            cached_models = self.model_cache.get_cached_models()
            for model_name in cached_models:
                if model_name != (self.active_model.name if self.active_model else None):
                    model_info = self.model_cache.remove(model_name)
                    if model_info:
                        self._unload_model_object(model_info)
                        logger.info(f"释放模型内存: {model_name}")

                        # 强制垃圾回收
                        gc.collect()

                        # 再次检查内存
                        if self.memory_monitor.is_memory_available(required_memory):
                            return True

            # 如果仍然内存不足，尝试释放当前活动模型
            if self.active_model:
                logger.warning("释放当前活动模型以腾出内存")
                self._unload_model_object(self.active_model)
                self.active_model = None
                self.active_language = None
                gc.collect()

                if self.memory_monitor.is_memory_available(required_memory):
                    return True

            return False

        except Exception as e:
            logger.error(f"内存管理失败: {str(e)}")
            return False

    def _load_model_object(self, request: ModelLoadRequest) -> Optional[Any]:
        """加载实际的模型对象"""
        try:
            logger.info(f"开始加载模型对象: {request.model_name}")

            # 根据语言选择对应的模型加载器
            if request.language == "zh":
                return self._load_qwen_model(request)
            elif request.language == "en":
                return self._load_mistral_model(request)
            else:
                logger.error(f"不支持的语言: {request.language}")
                return None

        except Exception as e:
            logger.error(f"加载模型对象失败: {str(e)}")
            return None

    def _load_qwen_model(self, request: ModelLoadRequest) -> Optional[Any]:
        """加载Qwen模型"""
        try:
            from src.models.qwen import QwenLLM
            from configs.model_config import get_qwen_config

            config = get_qwen_config()
            if not config:
                logger.error("无法获取Qwen模型配置")
                return None

            model = QwenLLM(config)
            logger.info("Qwen模型加载成功")
            return model

        except Exception as e:
            logger.error(f"加载Qwen模型失败: {str(e)}")
            return None

    def _load_mistral_model(self, request: ModelLoadRequest) -> Optional[Any]:
        """加载Mistral模型"""
        try:
            from src.models.mistral import MistralLLM
            from configs.model_config import get_mistral_config

            config = get_mistral_config()
            if not config:
                logger.error("无法获取Mistral模型配置")
                return None

            model = MistralLLM(config)
            logger.info("Mistral模型加载成功")
            return model

        except Exception as e:
            logger.error(f"加载Mistral模型失败: {str(e)}")
            return None

    def _unload_model_object(self, model_info: ModelInfo):
        """卸载模型对象"""
        try:
            if model_info.model_object:
                # 如果模型有特定的卸载方法，调用它
                if hasattr(model_info.model_object, 'unload'):
                    model_info.model_object.unload()
                elif hasattr(model_info.model_object, 'cleanup'):
                    model_info.model_object.cleanup()

                # 清除引用
                model_info.model_object = None
                model_info.is_active = False

                logger.info(f"模型已卸载: {model_info.name}")

        except Exception as e:
            logger.error(f"卸载模型失败: {str(e)}")

    def _estimate_model_memory(self, model_object: Any) -> int:
        """估算模型内存使用量"""
        try:
            # 尝试获取模型的内存使用量
            if hasattr(model_object, 'get_memory_usage'):
                return model_object.get_memory_usage()

            # 使用通用方法估算
            import sys
            return sys.getsizeof(model_object)

        except Exception as e:
            logger.error(f"估算模型内存失败: {str(e)}")
            return 1024 * 1024 * 1024  # 默认1GB

    def cleanup(self):
        """清理资源"""
        try:
            logger.info("开始清理模型加载器资源")

            # 卸载所有缓存的模型
            cached_models = self.model_cache.get_cached_models()
            for model_name in cached_models:
                model_info = self.model_cache.remove(model_name)
                if model_info:
                    self._unload_model_object(model_info)

            # 清空缓存
            self.model_cache.clear()

            # 重置活动模型
            self.active_model = None
            self.active_language = None

            # 强制垃圾回收
            gc.collect()

            logger.info("模型加载器资源清理完成")

        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

# 全局模型加载器实例
_global_loader = None

def get_enhanced_model_loader(memory_limit: int = 3800) -> EnhancedModelLoader:
    """获取全局增强版模型加载器实例"""
    global _global_loader
    if _global_loader is None:
        _global_loader = EnhancedModelLoader(memory_limit)
    return _global_loader

def cleanup_global_loader():
    """清理全局模型加载器"""
    global _global_loader
    if _global_loader:
        _global_loader.cleanup()
        _global_loader = None
