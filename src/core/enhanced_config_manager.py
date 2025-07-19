#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的配置管理器
提供更强的错误处理和回退机制，确保系统稳定性
"""

import gc
import time
import logging
from typing import Dict, Any, Optional
from .adaptive_model_config import AdaptiveModelConfigManager, ModelMode, AdaptiveConfig
from .hardware_detector import HardwareDetector, PerformanceLevel


class EnhancedConfigManager:
    """增强的配置管理器，提供更强的稳定性保证"""
    
    def __init__(self):
        """初始化增强配置管理器"""
        self.logger = logging.getLogger(__name__)
        self.base_manager = None
        self.fallback_config = None
        self.initialization_attempts = 0
        self.max_attempts = 3
        
    def initialize_with_retry(self) -> AdaptiveConfig:
        """带重试机制的初始化"""
        for attempt in range(self.max_attempts):
            try:
                self.initialization_attempts = attempt + 1
                self.logger.info(f"配置管理器初始化尝试 {attempt + 1}/{self.max_attempts}")
                
                # 强制垃圾回收
                gc.collect()
                
                # 创建基础管理器
                self.base_manager = AdaptiveModelConfigManager()
                config = self.base_manager.initialize()
                
                if config and self._validate_config_safety(config):
                    self.logger.info("配置管理器初始化成功")
                    return config
                else:
                    self.logger.warning(f"配置验证失败，尝试 {attempt + 1}")
                    if self.base_manager:
                        del self.base_manager
                        self.base_manager = None
                    
            except Exception as e:
                self.logger.error(f"初始化尝试 {attempt + 1} 失败: {e}")
                if self.base_manager:
                    del self.base_manager
                    self.base_manager = None
                
                # 等待一段时间再重试
                if attempt < self.max_attempts - 1:
                    time.sleep(1)
        
        # 所有尝试都失败，返回安全的回退配置
        self.logger.warning("所有初始化尝试都失败，使用回退配置")
        return self._get_safe_fallback_config()
    
    def set_mode_with_retry(self, mode: ModelMode) -> AdaptiveConfig:
        """带重试机制的模式设置"""
        if not self.base_manager:
            return self._get_safe_fallback_config()
        
        for attempt in range(2):  # 最多重试2次
            try:
                config = self.base_manager.set_mode(mode)
                if config and self._validate_config_safety(config):
                    return config
                else:
                    self.logger.warning(f"模式切换验证失败，尝试 {attempt + 1}")
                    
            except Exception as e:
                self.logger.error(f"模式切换尝试 {attempt + 1} 失败: {e}")
                
                # 等待一段时间再重试
                if attempt < 1:
                    time.sleep(0.5)
        
        # 切换失败，返回当前配置或回退配置
        self.logger.warning("模式切换失败，返回安全配置")
        return self._get_safe_fallback_config()
    
    def _validate_config_safety(self, config: AdaptiveConfig) -> bool:
        """验证配置的安全性"""
        try:
            # 检查基本配置有效性
            if not config or not config.mistral_config or not config.qwen_config:
                return False
            
            # 检查内存配置合理性
            mistral_memory = config.mistral_config.max_memory_gb
            qwen_memory = config.qwen_config.max_memory_gb
            
            if mistral_memory <= 0 or qwen_memory <= 0:
                return False
            
            # 检查内存使用是否在安全范围内
            if config.concurrent_models:
                total_memory = mistral_memory + qwen_memory
            else:
                total_memory = max(mistral_memory, qwen_memory)
            
            # 对于不同性能等级使用不同的安全阈值
            if config.hardware_info.performance_level == PerformanceLevel.LOW:
                safe_limit = 2.0  # 4GB设备的安全限制
            elif config.hardware_info.performance_level == PerformanceLevel.MEDIUM:
                safe_limit = 4.0  # 8GB设备的安全限制
            else:
                safe_limit = 6.0  # 高配设备的安全限制
            
            if total_memory > safe_limit:
                self.logger.warning(f"内存配置超出安全限制: {total_memory}GB > {safe_limit}GB")
                return False
            
            # 检查量化等级是否有效
            valid_quantizations = ["Q2_K", "Q4_K_M", "Q5_K", "FP16", "FP32"]
            if (config.mistral_config.quantization.value not in valid_quantizations or
                config.qwen_config.quantization.value not in valid_quantizations):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置安全性验证失败: {e}")
            return False
    
    def _get_safe_fallback_config(self) -> AdaptiveConfig:
        """获取安全的回退配置"""
        if self.fallback_config:
            return self.fallback_config
        
        try:
            # 创建最保守的配置
            from .adaptive_model_config import ModelConfig, QuantizationLevel
            
            # 检测硬件信息
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            # 创建最小内存配置
            mistral_config = ModelConfig(
                model_name="mistral-7b",
                quantization=QuantizationLevel.Q2_K,
                max_memory_gb=1.0,  # 最小内存分配
                context_length=512,
                batch_size=1,
                num_threads=2,
                use_gpu=False,
                gpu_layers=0
            )
            
            qwen_config = ModelConfig(
                model_name="qwen2.5-7b",
                quantization=QuantizationLevel.Q2_K,
                max_memory_gb=1.0,  # 最小内存分配
                context_length=512,
                batch_size=1,
                num_threads=2,
                use_gpu=False,
                gpu_layers=0
            )
            
            self.fallback_config = AdaptiveConfig(
                mode=ModelMode.MEMORY,
                hardware_info=hardware_info,
                mistral_config=mistral_config,
                qwen_config=qwen_config,
                concurrent_models=False,
                dynamic_loading=True,
                memory_threshold=0.95,
                monitor_interval=30,
                auto_cleanup=True,
                expected_bleu_score=0.65,
                max_startup_time=15,
                max_switch_time=5
            )
            
            self.logger.info("创建安全回退配置成功")
            return self.fallback_config
            
        except Exception as e:
            self.logger.error(f"创建回退配置失败: {e}")
            # 如果连回退配置都创建失败，返回None
            return None
    
    def get_hardware_info(self):
        """获取硬件信息"""
        if self.base_manager and self.base_manager.hardware_info:
            return self.base_manager.hardware_info
        
        # 如果基础管理器不可用，直接检测硬件
        try:
            detector = HardwareDetector()
            return detector.detect_hardware()
        except Exception as e:
            self.logger.error(f"硬件信息获取失败: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.base_manager:
                if hasattr(self.base_manager, 'stop_monitoring'):
                    self.base_manager.stop_monitoring()
                del self.base_manager
                self.base_manager = None
            
            # 强制垃圾回收
            gc.collect()
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")


def create_enhanced_config_manager() -> EnhancedConfigManager:
    """创建增强配置管理器的工厂函数"""
    return EnhancedConfigManager()


if __name__ == "__main__":
    # 测试增强配置管理器
    logging.basicConfig(level=logging.INFO)
    
    manager = create_enhanced_config_manager()
    config = manager.initialize_with_retry()
    
    if config:
        print(f"配置创建成功: {config.mode.value}")
        print(f"内存限制: {config.mistral_config.max_memory_gb}GB")
    else:
        print("配置创建失败")
    
    manager.cleanup()
