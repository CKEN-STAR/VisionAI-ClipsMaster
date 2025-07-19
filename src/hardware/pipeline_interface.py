#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令流水线优化接口 - VisionAI-ClipsMaster
提供集成式接口，允许系统其他组件使用流水线优化功能

该模块适配各种数学操作到流水线优化实现，并与微架构调优和性能监控系统集成，
提供统一的性能优化体验。
"""

import logging
import numpy as np
from typing import Dict, List, Union, Optional, Tuple, Any

# 尝试导入流水线优化包装器
try:
    from src.hardware.pipeline_wrapper import (
        get_pipeline_optimizer,
        matrix_multiply as pipeline_matrix_multiply,
        vector_dot_product as pipeline_vector_dot_product,
        matrix_vector_multiply as pipeline_matrix_vector_multiply,
        is_pipeline_opt_available
    )
    HAS_PIPELINE_OPT = True
except ImportError:
    HAS_PIPELINE_OPT = False
    
# 尝试导入微架构调优器
try:
    from src.hardware.microarch_tuner import get_microarch_tuner
    HAS_MICROARCH_TUNER = True
except ImportError:
    HAS_MICROARCH_TUNER = False

# 尝试导入性能监控
try:
    from src.monitor.performance_tracker import track_performance
    HAS_PERF_TRACKER = True
except ImportError:
    HAS_PERF_TRACKER = False
    
    def track_performance(operation_name):
        """性能跟踪器不可用时的空装饰器"""
        def decorator(func):
            return func
        return decorator

# 配置日志
logger = logging.getLogger(__name__)

class PipelineInterface:
    """指令流水线优化高级接口类"""
    
    def __init__(self, enable_tracking: bool = True, 
                adapt_to_microarch: bool = True):
        """
        初始化流水线优化接口
        
        Args:
            enable_tracking: 是否启用性能跟踪
            adapt_to_microarch: 是否根据微架构调整参数
        """
        self.enable_tracking = enable_tracking
        self.adapt_to_microarch = adapt_to_microarch
        
        # 检查是否支持流水线优化
        self.pipeline_available = HAS_PIPELINE_OPT and is_pipeline_opt_available()
        
        # 获取优化器（如果可用）
        if self.pipeline_available:
            self.optimizer = get_pipeline_optimizer()
            logger.info(f"流水线优化支持级别: {self.optimizer.optimization_level}")
            
            # 如果需要，根据微架构调整参数
            if adapt_to_microarch and HAS_MICROARCH_TUNER:
                params = self.optimizer.optimize_for_microarch()
                logger.info(f"根据微架构优化参数: {params}")
        else:
            logger.warning("流水线优化不可用，将使用基础操作")
    
    @track_performance("matrix_multiply")
    def matrix_multiply(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        """
        优化的矩阵乘法
        
        Args:
            A: 第一个矩阵
            B: 第二个矩阵
            
        Returns:
            np.ndarray: 结果矩阵 C = A × B
        """
        if self.pipeline_available:
            return pipeline_matrix_multiply(A, B)
        else:
            return np.matmul(A, B)
    
    @track_performance("vector_dot_product")
    def vector_dot_product(self, A: np.ndarray, B: np.ndarray) -> float:
        """
        优化的向量点积
        
        Args:
            A: 第一个向量
            B: 第二个向量
            
        Returns:
            float: 点积结果
        """
        if self.pipeline_available:
            return pipeline_vector_dot_product(A, B)
        else:
            return float(np.dot(A, B))
    
    @track_performance("matrix_vector_multiply")
    def matrix_vector_multiply(self, A: np.ndarray, x: np.ndarray) -> np.ndarray:
        """
        优化的矩阵向量乘法
        
        Args:
            A: 矩阵
            x: 向量
            
        Returns:
            np.ndarray: 结果向量 y = A × x
        """
        if self.pipeline_available:
            return pipeline_matrix_vector_multiply(A, x)
        else:
            return np.dot(A, x)
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """
        获取优化状态信息
        
        Returns:
            Dict[str, Any]: 包含优化状态的字典
        """
        status = {
            'pipeline_available': self.pipeline_available,
            'performance_tracking': self.enable_tracking
        }
        
        # 添加更多详细信息（如果可用）
        if self.pipeline_available:
            # 添加优化器统计信息
            status.update(self.optimizer.get_stats())
            
            # 添加微架构信息（如果可用）
            if HAS_MICROARCH_TUNER:
                tuner = get_microarch_tuner()
                status['microarch'] = tuner.detected_arch
                status['arch_params'] = tuner.arch_params
        
        return status
    
    def clear_stats(self) -> None:
        """清除统计信息"""
        if self.pipeline_available:
            self.optimizer.stats = {"calls": 0, "fallbacks": 0, "total_time": 0.0}
            logger.info("已清除流水线优化统计信息")

# 全局单例
_pipeline_interface = None

def get_pipeline_interface() -> PipelineInterface:
    """
    获取流水线优化接口单例
    
    Returns:
        PipelineInterface: 流水线优化接口实例
    """
    global _pipeline_interface
    
    if _pipeline_interface is None:
        _pipeline_interface = PipelineInterface()
        
    return _pipeline_interface

def optimize_matrix_operations(matrices: List[np.ndarray]) -> List[np.ndarray]:
    """
    优化一组矩阵操作
    
    这是一个演示如何使用流水线接口进行批处理操作的示例函数
    
    Args:
        matrices: 要处理的矩阵列表
    
    Returns:
        List[np.ndarray]: 处理后的矩阵列表
    """
    interface = get_pipeline_interface()
    result = []
    
    for i in range(0, len(matrices) - 1, 2):
        if i + 1 < len(matrices):
            # 对每对矩阵执行乘法
            C = interface.matrix_multiply(matrices[i], matrices[i+1])
            result.append(C)
        else:
            # 奇数个矩阵，最后一个直接添加
            result.append(matrices[i])
    
    return result

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试流水线接口
    interface = get_pipeline_interface()
    status = interface.get_optimization_status()
    
    logger.info("流水线优化状态:")
    for k, v in status.items():
        logger.info(f"  {k}: {v}")
    
    # 如果可用，运行简单测试
    if interface.pipeline_available:
        # 创建测试数据
        A = np.random.rand(100, 100).astype(np.float32)
        B = np.random.rand(100, 100).astype(np.float32)
        v = np.random.rand(100).astype(np.float32)
        
        # 测试矩阵乘法
        C = interface.matrix_multiply(A, B)
        logger.info(f"矩阵乘法结果形状: {C.shape}")
        
        # 测试向量点积
        dot = interface.vector_dot_product(v, v)
        logger.info(f"向量点积结果: {dot:.4f}")
        
        # 测试矩阵向量乘法
        y = interface.matrix_vector_multiply(A, v)
        logger.info(f"矩阵向量乘法结果形状: {y.shape}")
        
        # 输出统计信息
        stats = interface.get_optimization_status()
        logger.info(f"操作后统计: 调用次数={stats.get('calls', 0)}, 平均时间={stats.get('avg_time', 0):.6f}秒") 