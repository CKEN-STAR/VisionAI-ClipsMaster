#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据流分析器模块

对视频导出流程中的各种操作性能进行分析，识别潜在瓶颈，并提供优化建议。
支持细粒度操作分析、热点识别、内存使用分析和数据流可视化功能。
"""

import os
import time
import json
import logging
import functools
from typing import Dict, List, Any, Tuple, Optional, Callable, Union
from datetime import datetime
from collections import defaultdict, Counter
import traceback
import threading
import gc
import sys

from src.utils.log_handler import get_logger

# 配置日志记录器
logger = get_logger("dataflow_analyzer")

# 全局性能数据存储，使用线程本地存储确保线程安全
_local_profile_data = threading.local()

# 分析模块名称映射
MODULE_NAMES = {
    'video_export': '视频导出模块',
    'audio_export': '音频导出模块',
    'xml_export': 'XML导出模块',
    'subtitle_export': '字幕导出模块',
    'image_export': '图像导出模块'
}

class OperationContext:
    """操作上下文类，用于记录单个操作的性能数据"""
    
    def __init__(self, name: str, module: str, category: str = "operation"):
        """初始化操作上下文
        
        Args:
            name: 操作名称
            module: 所属模块
            category: 操作类别
        """
        self.name = name
        self.module = module
        self.category = category
        self.start_time = time.time()
        self.end_time = None
        self.duration = 0
        self.memory_before = 0
        self.memory_after = 0
        self.memory_delta = 0
        self.success = None
        self.error = None
    
    def finish(self, success: bool = True, error: Optional[str] = None):
        """完成操作记录
        
        Args:
            success: 操作是否成功
            error: 错误信息（如有）
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """将操作数据转换为字典格式
        
        Returns:
            Dict: 操作数据字典
        """
        return {
            'name': self.name,
            'module': self.module,
            'category': self.category,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'memory_before': self.memory_before,
            'memory_after': self.memory_after,
            'memory_delta': self.memory_delta,
            'success': self.success,
            'error': self.error
        }


class ProfileData:
    """性能数据类，用于存储和分析模块的性能数据"""
    
    def __init__(self, module_name: str):
        """初始化性能数据
        
        Args:
            module_name: 模块名称
        """
        self.module_name = module_name
        self.operations = []  # 操作列表
        self.start_time = time.time()
        self.end_time = None
        self.total_duration = 0
        self.memory_usage = []
        self.bottlenecks = []
        self.optimization_suggestions = []
        self.metadata = {}
        self.data_throughput = 0  # 数据吞吐量(MB/s)
    
    def add_operation(self, op: OperationContext):
        """添加操作记录
        
        Args:
            op: 操作上下文对象
        """
        self.operations.append(op)
    
    def record_memory_usage(self, stage: str, usage_mb: float):
        """记录内存使用情况
        
        Args:
            stage: 阶段名称
            usage_mb: 内存使用量(MB)
        """
        self.memory_usage.append({
            'stage': stage,
            'time': time.time() - self.start_time,
            'usage_mb': usage_mb
        })
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def finish(self):
        """完成性能分析并计算总统计信息"""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        self._analyze_bottlenecks()
    
    def _analyze_bottlenecks(self):
        """分析性能瓶颈并生成优化建议"""
        # 按耗时排序操作
        sorted_ops = sorted(self.operations, key=lambda x: x.duration, reverse=True)
        
        # 识别最慢的操作
        if sorted_ops:
            total_op_time = sum(op.duration for op in self.operations)
            
            # 找出耗时超过总时间10%的操作
            for op in sorted_ops:
                if op.duration > total_op_time * 0.1:
                    self.bottlenecks.append({
                        'operation': op.name,
                        'duration': op.duration,
                        'percentage': (op.duration / total_op_time) * 100 if total_op_time > 0 else 0
                    })
                    
                    # 生成优化建议
                    if op.category == 'io':
                        self.optimization_suggestions.append(
                            f"IO密集操作'{op.name}'耗时较长，考虑使用异步IO或缓冲策略"
                        )
                    elif op.category == 'cpu':
                        self.optimization_suggestions.append(
                            f"CPU密集操作'{op.name}'耗时较长，考虑使用并行处理或算法优化"
                        )
                    elif op.category == 'memory':
                        self.optimization_suggestions.append(
                            f"内存操作'{op.name}'效率低下，检查内存泄漏或考虑流式处理"
                        )
            
            # 分析数据吞吐量
            if 'data_size_mb' in self.metadata and self.total_duration > 0:
                self.data_throughput = self.metadata['data_size_mb'] / self.total_duration
                
                if self.data_throughput < 5:  # 低于5MB/s视为慢
                    self.optimization_suggestions.append(
                        f"数据吞吐量较低({self.data_throughput:.2f}MB/s)，考虑批处理或减少数据转换次数"
                    )
    
    def to_dict(self) -> Dict[str, Any]:
        """将性能数据转换为字典格式
        
        Returns:
            Dict: 性能数据字典
        """
        return {
            'module_name': self.module_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_duration': self.total_duration,
            'operations': [op.to_dict() for op in self.operations],
            'memory_usage': self.memory_usage,
            'bottlenecks': self.bottlenecks,
            'optimization_suggestions': self.optimization_suggestions,
            'metadata': self.metadata,
            'data_throughput': self.data_throughput
        }
    
    def save_to_file(self, file_path: Optional[str] = None) -> str:
        """将性能数据保存到文件
        
        Args:
            file_path: 文件路径，若为None则自动生成
            
        Returns:
            str: 保存的文件路径
        """
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"profile_{self.module_name}_{timestamp}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"性能分析数据已保存至: {file_path}")
        return file_path


def profile_operation(module: str, category: str = "operation"):
    """性能分析装饰器
    
    Args:
        module: 模块名称
        category: 操作类别
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 初始化操作上下文
            op_context = OperationContext(
                name=func.__name__,
                module=module,
                category=category
            )
            
            # 确保性能数据存在
            if not hasattr(_local_profile_data, 'data'):
                _local_profile_data.data = {}
            
            if module not in _local_profile_data.data:
                _local_profile_data.data[module] = ProfileData(module)
            
            try:
                # 执行操作
                result = func(*args, **kwargs)
                op_context.finish(success=True)
                return result
            except Exception as e:
                # 记录错误
                error_msg = str(e)
                op_context.finish(success=False, error=error_msg)
                raise
            finally:
                # 保存操作记录
                if module in _local_profile_data.data:
                    _local_profile_data.data[module].add_operation(op_context)
        
        return wrapper
    
    return decorator


def start_profiling(module_name: str) -> None:
    """开始对指定模块进行性能分析
    
    Args:
        module_name: 模块名称
    """
    # 初始化线程本地存储
    if not hasattr(_local_profile_data, 'data'):
        _local_profile_data.data = {}
    
    # 创建或重置性能数据
    _local_profile_data.data[module_name] = ProfileData(module_name)
    logger.info(f"开始分析模块: {module_name}")


def stop_profiling(module_name: str) -> Optional[ProfileData]:
    """停止对指定模块的性能分析
    
    Args:
        module_name: 模块名称
        
    Returns:
        ProfileData: 性能数据对象
    """
    if (hasattr(_local_profile_data, 'data') and 
            module_name in _local_profile_data.data):
        profile_data = _local_profile_data.data[module_name]
        profile_data.finish()
        logger.info(f"完成分析模块: {module_name}, 总耗时: {profile_data.total_duration:.2f}秒")
        return profile_data
    return None


def get_current_profile_data(module_name: str) -> Optional[ProfileData]:
    """获取当前模块的性能分析数据
    
    Args:
        module_name: 模块名称
        
    Returns:
        ProfileData: 性能数据对象
    """
    if (hasattr(_local_profile_data, 'data') and 
            module_name in _local_profile_data.data):
        return _local_profile_data.data[module_name]
    return None


def get_memory_usage() -> float:
    """获取当前进程的内存使用量(MB)
    
    Returns:
        float: 内存使用量(MB)
    """
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def analyze_copy_operations() -> List[Dict[str, Any]]:
    """识别所有数据拷贝与热点
    
    分析导出过程中的数据复制操作，识别耗时较长的拷贝操作。
    
    Returns:
        List: 热点数据操作列表
    """
    # 获取视频导出模块的性能数据
    profile_data = profile_module('video_export')
    
    # 过滤出复制操作并按耗时排序
    return [
        op for op in profile_data
        if 'copy' in op['name'].lower()
        and op['duration'] > 0.1  # 超过100ms的拷贝操作
    ]


def profile_module(module_name: str) -> List[Dict[str, Any]]:
    """获取指定模块的性能数据
    
    Args:
        module_name: 模块名称
        
    Returns:
        List: 性能数据列表
    """
    if module_name == 'video_export':
        # 模拟视频导出模块的性能数据
        return [
            {'name': 'video_reencode', 'duration': 1.2, 'memory_delta': 45.6},
            {'name': 'subtitle_merge', 'duration': 0.3, 'memory_delta': 12.1},
            {'name': 'copy_stream_data', 'duration': 0.8, 'memory_delta': 28.3},
            {'name': 'audio_normalize', 'duration': 0.5, 'memory_delta': 18.7},
            {'name': 'copy_frame_buffer', 'duration': 0.6, 'memory_delta': 32.4}
        ]
    elif module_name == 'audio_export':
        # 模拟音频导出模块的性能数据
        return [
            {'name': 'audio_downsample', 'duration': 0.4, 'memory_delta': 8.2},
            {'name': 'copy_audio_chunks', 'duration': 0.7, 'memory_delta': 15.3},
            {'name': 'audio_compress', 'duration': 0.9, 'memory_delta': 12.7}
        ]
    # 其他模块返回空列表
    return []


def summarize_performance(module_name: str) -> Dict[str, Any]:
    """生成性能摘要
    
    Args:
        module_name: 模块名称
        
    Returns:
        Dict: 性能摘要
    """
    # 获取性能数据
    profile_data = get_current_profile_data(module_name)
    if not profile_data:
        return {'error': f"未找到模块'{module_name}'的性能数据"}
    
    # 生成摘要
    data = profile_data.to_dict()
    summary = {
        'module_name': data['module_name'],
        'total_duration': data['total_duration'],
        'operation_count': len(data['operations']),
        'bottlenecks': data['bottlenecks'],
        'suggestions': data['optimization_suggestions'],
        'data_throughput': data['data_throughput']
    }
    
    # 添加热点操作
    top_operations = sorted(
        data['operations'], 
        key=lambda x: x['duration'], 
        reverse=True
    )[:5]  # 获取耗时最长的5个操作
    
    summary['top_operations'] = [{
        'name': op['name'],
        'duration': op['duration'],
        'category': op['category']
    } for op in top_operations]
    
    return summary


def visualization_helper(module_name: str, output_path: Optional[str] = None) -> Optional[str]:
    """生成性能可视化图表
    
    Args:
        module_name: 模块名称
        output_path: 输出文件路径（可选）
        
    Returns:
        str: 生成的图表文件路径
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.error("无法生成可视化图表: 缺少matplotlib库")
        return None
    
    # 获取性能数据
    profile_data = get_current_profile_data(module_name)
    if not profile_data:
        logger.error(f"未找到模块'{module_name}'的性能数据")
        return None
    
    data = profile_data.to_dict()
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 操作耗时图
    operations = sorted(data['operations'], key=lambda x: x['duration'], reverse=True)[:10]
    names = [op['name'] for op in operations]
    durations = [op['duration'] for op in operations]
    
    ax1.barh(names, durations, color='skyblue')
    ax1.set_xlabel('耗时 (秒)')
    ax1.set_title(f"{MODULE_NAMES.get(module_name, module_name)} - 操作耗时分析")
    
    # 内存使用图
    if data['memory_usage']:
        times = [m['time'] for m in data['memory_usage']]
        usages = [m['usage_mb'] for m in data['memory_usage']]
        
        ax2.plot(times, usages, 'r-', marker='o')
        ax2.set_xlabel('时间 (秒)')
        ax2.set_ylabel('内存使用 (MB)')
        ax2.set_title('内存使用趋势')
        ax2.grid(True)
    
    plt.tight_layout()
    
    # 保存图表
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"profile_{module_name}_viz_{timestamp}.png"
    
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"性能可视化图表已保存至: {output_path}")
    return output_path


if __name__ == "__main__":
    # 演示用例
    logger.info("数据流分析器演示")
    
    # 分析复制操作
    hot_spots = analyze_copy_operations()
    logger.info(f"找到 {len(hot_spots)} 个数据复制热点")
    for idx, hot_spot in enumerate(hot_spots, 1):
        logger.info(f"{idx}. {hot_spot['name']} - 耗时: {hot_spot['duration']:.2f}秒")
    
    # 模拟使用装饰器进行性能分析
    logger.info("\n使用装饰器分析操作示例:")
    
    @profile_operation(module="demo_module", category="cpu")
    def test_cpu_operation():
        """CPU密集测试操作"""
        logger.info("执行CPU密集操作...")
        result = 0
        for i in range(1000000):
            result += i
        return result
    
    # 开始分析
    start_profiling("demo_module")
    
    # 执行操作
    test_cpu_operation()
    
    # 结束分析
    profile_result = stop_profiling("demo_module")
    
    # 打印分析结果
    if profile_result:
        logger.info(f"操作总数: {len(profile_result.operations)}")
        logger.info(f"总耗时: {profile_result.total_duration:.4f}秒")
        
        if profile_result.bottlenecks:
            logger.info("识别到的性能瓶颈:")
            for bottleneck in profile_result.bottlenecks:
                logger.info(f"- {bottleneck['operation']}:"
                            f" {bottleneck['duration']:.4f}秒"
                            f" ({bottleneck['percentage']:.1f}%)")
        
        if profile_result.optimization_suggestions:
            logger.info("优化建议:")
            for suggestion in profile_result.optimization_suggestions:
                logger.info(f"- {suggestion}") 