#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
量化评估器

评估不同量化级别下模型的内存占用与性能表现
"""

import os
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO,
                  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("quant_evaluator")

# 量化级别及其对应的内存占用（近似值，单位MB）
QUANT_LEVELS = {
    "FP32": {"memory_mb": 8000, "speed_factor": 1.0},     # 全精度
    "FP16": {"memory_mb": 4000, "speed_factor": 1.2},     # 半精度
    "INT8": {"memory_mb": 2000, "speed_factor": 1.5},     # 8位量化
    "INT4": {"memory_mb": 1000, "speed_factor": 1.8}      # 4位量化
}

class QuantEvaluator:
    """
    量化评估器，分析不同量化级别的内存-性能权衡
    """
    
    def __init__(self):
        """初始化量化评估器"""
        self.quant_levels = QUANT_LEVELS
        self.system_memory_mb = self._get_system_memory()
        
        logger.info(f"量化评估器初始化完成，系统内存: {self.system_memory_mb} MB")
    
    def _get_system_memory(self) -> int:
        """
        获取系统总内存（MB）
        
        Returns:
            int: 系统总内存（MB）
        """
        try:
            import psutil
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except ImportError:
            # 如果无法导入psutil，假设系统有8GB内存
            logger.warning("无法导入psutil，使用默认内存大小8GB")
            return 8 * 1024
    
    def get_available_quant_levels(self, max_memory_mb: Optional[int] = None) -> Dict[str, Dict]:
        """
        获取在内存限制下可用的量化级别
        
        Args:
            max_memory_mb: 最大内存限制（MB），如果为None则使用系统内存的一半
            
        Returns:
            Dict[str, Dict]: 可用的量化级别及其属性
        """
        if max_memory_mb is None:
            # 默认使用系统内存的一半
            max_memory_mb = self.system_memory_mb // 2
        
        # 过滤出符合内存限制的量化级别
        available_levels = {}
        for level, props in self.quant_levels.items():
            if props["memory_mb"] <= max_memory_mb:
                available_levels[level] = props
        
        return available_levels
    
    def evaluate_memory_performance_tradeoff(self, max_memory_mb: Optional[int] = None) -> List[Dict]:
        """
        评估内存和性能的权衡关系
        
        Args:
            max_memory_mb: 最大内存限制（MB）
            
        Returns:
            List[Dict]: 内存-性能权衡分析结果
        """
        available_levels = self.get_available_quant_levels(max_memory_mb)
        
        # 不同量化级别的表现分析
        results = []
        for level, props in available_levels.items():
            memory_mb = props["memory_mb"]
            speed_factor = props["speed_factor"]
            
            # 计算效率比（性能/内存占用）
            efficiency = speed_factor / (memory_mb / 1000)  # 每GB内存的性能
            
            results.append({
                "quant_level": level,
                "memory_mb": memory_mb,
                "speed_factor": speed_factor,
                "efficiency_ratio": efficiency
            })
        
        # 按效率比排序
        results.sort(key=lambda x: x["efficiency_ratio"], reverse=True)
        return results
    
    def get_recommended_quant_level(self, max_memory_mb: Optional[int] = None) -> str:
        """
        获取推荐的量化级别
        
        Args:
            max_memory_mb: 最大内存限制（MB）
            
        Returns:
            str: 推荐的量化级别
        """
        results = self.evaluate_memory_performance_tradeoff(max_memory_mb)
        
        if not results:
            logger.warning("没有符合内存限制的量化级别")
            return "INT4"  # 返回最低量化级别
        
        # 返回效率比最高的级别
        return results[0]["quant_level"]
    
    def is_pareto_optimal(self, memory: float, speed: float, all_points: List[Tuple[float, float]]) -> bool:
        """
        判断点(memory, speed)是否为帕累托最优
        
        Args:
            memory: 内存占用
            speed: 速度因子
            all_points: 所有(内存, 速度)点集
            
        Returns:
            bool: 是否为帕累托最优
        """
        for other_memory, other_speed in all_points:
            if other_memory <= memory and other_speed >= speed:
                if other_memory < memory or other_speed > speed:
                    return False
        return True

    def get_pareto_optimal_levels(self) -> List[str]:
        """
        获取帕累托最优的量化级别
        
        Returns:
            List[str]: 帕累托最优的量化级别列表
        """
        # 构建所有点集(内存, 速度)
        all_points = [(props["memory_mb"], props["speed_factor"]) for _, props in self.quant_levels.items()]
        
        # 筛选帕累托最优点
        pareto_levels = []
        for level, props in self.quant_levels.items():
            if self.is_pareto_optimal(props["memory_mb"], props["speed_factor"], all_points):
                pareto_levels.append(level)
        
        return pareto_levels

# 单例模式
_quant_evaluator = None

def get_quant_evaluator() -> QuantEvaluator:
    """
    获取量化评估器实例
    
    Returns:
        QuantEvaluator: 量化评估器实例
    """
    global _quant_evaluator
    
    if _quant_evaluator is None:
        _quant_evaluator = QuantEvaluator()
    
    return _quant_evaluator 