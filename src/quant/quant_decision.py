#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化决策算法
根据系统内存状态动态决定最佳量化级别
"""

import os
import sys
import psutil
from typing import Dict, Optional, Tuple, Any
from loguru import logger

# 添加项目根目录到路径以解决导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.quant_config_loader import get_quant_config
from src.utils.memory_guard import MemoryGuard, QuantizationManager
from src.memory.hardware_adapter import HardwareAdapter, get_hardware_adapter

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

class QuantDecisionEngine:
    """量化决策引擎：根据内存状态和模型需求做出最佳量化决策"""
    
    def __init__(self, memory_guard: Optional[MemoryGuard] = None):
        """
        初始化量化决策引擎
        
        Args:
            memory_guard: 内存监控模块实例，如不提供将创建新实例
        """
        self.memory_guard = memory_guard or MemoryGuard()
        self.quant_config = get_quant_config()
        self.quant_manager = QuantizationManager(self.memory_guard)
        self.hardware_adapter = get_hardware_adapter()
        
        # 初始化决策记录
        self.decision_history = []
        self.max_history_length = 50
        
        # 内部阈值缓存 - 确保可以动态更新
        self._thresholds = {}
        self._load_thresholds_from_config()
        
        # 记录硬件报告
        logger.info("量化决策引擎已初始化，正在使用硬件适配层")
        hardware_report = self.hardware_adapter.get_hardware_report()
        logger.info(f"硬件配置: CPU: {hardware_report['hardware']['cpu']}, "
                   f"RAM: {hardware_report['hardware']['ram_gb']}GB, "
                   f"GPU: {hardware_report['hardware']['gpu']}")
    
    def _load_thresholds_from_config(self):
        """从配置文件加载阈值"""
        config = self.quant_config.get_config()
        self._thresholds = config.get("auto_select_thresholds", {})
        logger.debug(f"已加载量化阈值配置: {self._thresholds}")
    
    def update_thresholds(self, new_thresholds: Dict[str, float]) -> bool:
        """
        更新量化阈值设置
        
        Args:
            new_thresholds: 新的阈值设置
            
        Returns:
            bool: 是否更新成功
        """
        if not isinstance(new_thresholds, dict):
            logger.error(f"无效的阈值设置: {new_thresholds}")
            return False
            
        # 验证阈值值
        for k, v in new_thresholds.items():
            if not isinstance(v, (int, float)) or v < 0 or v > 1:
                logger.error(f"无效的阈值值: {k}={v}，值必须在0和1之间")
                return False
        
        # 更新阈值
        self._thresholds.update(new_thresholds)
        logger.info(f"量化阈值已更新: {new_thresholds}")
        return True
    
    def get_device_stats(self) -> Dict[str, Any]:
        """获取当前设备状态"""
        memory = psutil.virtual_memory()
        
        stats = {
            "memory_total": memory.total,
            "memory_available": memory.available,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "cpu_count": psutil.cpu_count(logical=False),
            "pid": os.getpid(),
            "process_memory": psutil.Process(os.getpid()).memory_info().rss
        }
        
        # 添加GPU信息（如果可用）
        if self.hardware_adapter.hardware_info['gpu_available']:
            stats.update({
                "gpu_available": True,
                "gpu_name": self.hardware_adapter.hardware_info['gpu_name'],
                "vram_total_mb": self.hardware_adapter.hardware_info['vram_total_mb']
            })
        else:
            stats["gpu_available"] = False
        
        return stats
    
    def select_best_quant_level(self, 
                              model_type: str = "zh", 
                              min_quality: float = 0.0,
                              memory_limit: Optional[float] = None) -> str:
        """
        选择最佳量化级别
        
        Args:
            model_type: 模型类型 (zh/en)
            min_quality: 最低质量要求 (0.0-1.0)
            memory_limit: 内存限制（GB，可选）
            
        Returns:
            str: 推荐的量化级别
        """
        # 获取设备信息
        device_stats = self.get_device_stats()
        
        # 首先使用硬件适配层获取推荐方法
        recommended_method = self.hardware_adapter.get_recommended_methods(model_type)
        
        if recommended_method:
            # 使用硬件适配层推荐的首选方法
            quant_level = recommended_method[0]
            logger.info(f"基于硬件分析推荐的量化级别: {quant_level} (模型类型: {model_type})")
            
            # 记录到决策历史
            self._record_decision(quant_level, device_stats, {"method": "hardware_adapter", "model_type": model_type})
            
            return quant_level
        
        # 如果硬件适配层无法提供推荐，则使用传统方法
        logger.warning("硬件适配层无法提供推荐，使用传统内存阈值方法")
        
        # 获取可用内存百分比
        available_memory_percent = device_stats["memory_available"] / device_stats["memory_total"]
        
        # 根据阈值选择量化级别
        quant_level = self._select_by_thresholds(available_memory_percent, model_type)
        
        # 记录到决策历史
        self._record_decision(quant_level, device_stats, {"method": "memory_threshold", "model_type": model_type})
        
        return quant_level
    
    def _select_by_thresholds(self, available_memory_percent: float, model_type: str) -> str:
        """根据内存阈值选择量化级别
        
        Args:
            available_memory_percent: 可用内存百分比 (0.0-1.0)
            model_type: 模型类型 (zh/en)
            
        Returns:
            str: 选择的量化级别
        """
        # 获取模型特定配置
        model_config = self.quant_config.get_model_specific_config(model_type)
        threshold_config = model_config.get("thresholds", self._thresholds)
        
        # 确定量化级别
        if available_memory_percent >= threshold_config.get("high", 0.7):
            return model_config.get("high_level", "Q8_0")
        elif available_memory_percent >= threshold_config.get("medium", 0.5):
            return model_config.get("medium_level", "Q5_K")
        elif available_memory_percent >= threshold_config.get("low", 0.3):
            return model_config.get("low_level", "Q4_K")
        else:
            return model_config.get("critical_level", "Q2_K")
    
    def _record_decision(self, 
                        level: str, 
                        stats: Dict[str, Any], 
                        meta: Dict[str, Any]) -> None:
        """记录决策到历史记录
        
        Args:
            level: 选择的量化级别
            stats: 设备状态
            meta: 元数据
        """
        import time

        # 创建决策记录
        record = {
            "timestamp": time.time(),
            "level": level,
            "stats": stats,
            "meta": meta
        }
        
        # 添加到历史记录
        self.decision_history.append(record)
        
        # 限制历史记录长度
        if len(self.decision_history) > self.max_history_length:
            self.decision_history = self.decision_history[-self.max_history_length:]
    
    def get_fallback_chain(self, 
                          starting_level: Optional[str] = None, 
                          model_type: str = "zh") -> list:
        """
        获取降级备选链
        
        Args:
            starting_level: 起始量化级别，如果为None则使用当前首选
            model_type: 模型类型 (zh/en)
            
        Returns:
            list: 降级备选链列表
        """
        # 使用硬件适配层的降级链
        fallback_chain = self.hardware_adapter.get_fallback_chain()
        
        if fallback_chain:
            logger.info(f"使用硬件适配层的降级链: {fallback_chain}")
            return fallback_chain
        
        # 如果硬件适配层无法提供降级链，使用默认降级顺序
        logger.warning("硬件适配层无法提供降级链，使用默认降级顺序")
        default_chain = ["Q8_0", "Q6_K", "Q5_K", "Q4_K", "Q4_K_M", "Q2_K"]
        
        # 如果指定了起始级别，从该级别开始降级
        if starting_level and starting_level in default_chain:
            start_idx = default_chain.index(starting_level)
            return default_chain[start_idx:]
        
        return default_chain
    
    def estimate_memory_usage(self, quant_level: str, model_size_params: int) -> float:
        """
        估计给定量化级别下的内存使用量
        
        Args:
            quant_level: 量化级别
            model_size_params: 模型参数数量（百万）
            
        Returns:
            float: 估计内存使用量（GB）
        """
        # 获取量化方法信息
        quant_info = next((m for m in self.hardware_adapter.compatible_methods.values() 
                          if m['description'].startswith(quant_level.split('_')[0])), None)
        
        if quant_info:
            memory_ratio = quant_info.get('memory_ratio', 0.25)  # 默认为0.25
        else:
            # 使用默认内存比例
            memory_ratios = {
                "Q2": 0.125,
                "Q4": 0.25,
                "Q5": 0.31,
                "Q6": 0.375,
                "Q8": 0.5,
                "F16": 1.0
            }
            prefix = quant_level.split('_')[0]
            memory_ratio = memory_ratios.get(prefix, 0.25)
        
        # 计算原始FP16模型大小
        fp16_size_gb = model_size_params * 2 / 1024  # 2字节/参数，结果为GB
        
        # 估计量化后的大小
        quantized_size_gb = fp16_size_gb * memory_ratio
        
        # 加上运行时开销（假设为20%）
        total_estimate_gb = quantized_size_gb * 1.2
        
        return total_estimate_gb
    
    def can_fit_in_memory(self, quant_level: str, model_size_params: int) -> bool:
        """
        检查给定量化级别的模型是否能装入内存
        
        Args:
            quant_level: 量化级别
            model_size_params: 模型参数数量（百万）
            
        Returns:
            bool: 是否能装入内存
        """
        # 估计内存使用
        estimated_gb = self.estimate_memory_usage(quant_level, model_size_params)
        
        # 获取可用内存（GB）
        available_gb = psutil.virtual_memory().available / (1024**3)
        
        # 保留安全余量（1GB或可用内存的10%，取大者）
        safety_margin = max(1.0, available_gb * 0.1)
        
        # 检查是否能装入
        can_fit = (estimated_gb + safety_margin) <= available_gb
        
        logger.info(f"量化级别 {quant_level} 估计需要 {estimated_gb:.2f}GB, "
                   f"可用内存: {available_gb:.2f}GB, {'可以' if can_fit else '不能'}装入")
        
        return can_fit


# 创建全局实例
_quant_decision_engine = None

def get_quant_decision_engine() -> QuantDecisionEngine:
    """获取量化决策引擎单例"""
    global _quant_decision_engine
    if _quant_decision_engine is None:
        _quant_decision_engine = QuantDecisionEngine()
    return _quant_decision_engine


def quant_decision_engine() -> QuantDecisionEngine:
    """兼容旧API，获取量化决策引擎单例"""
    return get_quant_decision_engine()


if __name__ == "__main__":
    """模块测试"""
    engine = QuantDecisionEngine()
    
    # 输出硬件信息
    hardware_report = engine.hardware_adapter.get_hardware_report()
    print("\n硬件信息:")
    print(f"CPU: {hardware_report['hardware']['cpu']}")
    print(f"内存: {hardware_report['hardware']['ram_gb']}GB")
    print(f"GPU: {hardware_report['hardware']['gpu']}")
    print(f"指令集: {', '.join(hardware_report['hardware']['features'])}")
    
    # 测试不同模型选择
    print("\n量化级别推荐:")
    print(f"中文模型: {engine.select_best_quant_level('zh')}")
    print(f"英文模型: {engine.select_best_quant_level('en')}")
    
    # 测试降级链
    print("\n降级备选链:")
    print(f"中文: {engine.get_fallback_chain(model_type='zh')}")
    print(f"英文: {engine.get_fallback_chain(model_type='en')}")
    
    # 测试内存估计
    print("\n模型内存估计 (7B参数):")
    for level in ["Q2_K", "Q4_K", "Q5_K", "Q8_0", "F16"]:
        mem = engine.estimate_memory_usage(level, 7000)
        print(f"{level}: {mem:.2f}GB") 