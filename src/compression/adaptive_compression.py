#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自适应压缩调节模块

该模块根据系统内存状态自动调整压缩参数，实现内存压力与性能的平衡。
主要功能：
1. 内存监控与压力评估
2. 动态调整压缩级别
3. 资源特性感知的压缩策略
4. 压缩算法自动切换
5. 性能影响评估与调整
"""

import os
import sys
import time
import threading
import logging
import psutil
from typing import Dict, Any, Optional, Union, Tuple, List, Callable
from enum import Enum
import json

# 导入压缩相关模块
from src.compression.core import Compressor, compress, decompress
from src.compression.compressors import get_compressor, get_available_compressors
from src.compression.hardware_accel import get_best_hardware, HAS_CUDA

# 配置日志
logger = logging.getLogger("AdaptiveCompression")

# 内存压力级别定义
class MemoryPressureLevel(Enum):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存压力级别枚举"""
    LOW = 0      # 低压力：内存充足
    MEDIUM = 1   # 中等压力：内存适中
    HIGH = 2     # 高压力：内存紧张
    CRITICAL = 3 # 临界压力：内存不足

# 资源类型压缩优先级
class ResourcePriority(Enum):
    """资源压缩优先级枚举"""
    LOW = 0      # 低优先级：不太重要的资源，可以使用高压缩率
    MEDIUM = 1   # 中等优先级：一般资源，平衡压缩率和速度
    HIGH = 2     # 高优先级：重要资源，速度优先

# 默认压缩级别映射（按优先级和内存压力级别）
DEFAULT_LEVEL_MAP = {
    # 低优先级资源
    ResourcePriority.LOW: {
        MemoryPressureLevel.LOW: 3,      # 内存充足时使用中等压缩
        MemoryPressureLevel.MEDIUM: 5,   # 内存适中时增加压缩率
        MemoryPressureLevel.HIGH: 7,     # 内存紧张时使用高压缩
        MemoryPressureLevel.CRITICAL: 9  # 内存不足时使用最高压缩
    },
    # 中等优先级资源
    ResourcePriority.MEDIUM: {
        MemoryPressureLevel.LOW: 1,      # 内存充足时使用低压缩
        MemoryPressureLevel.MEDIUM: 3,   # 内存适中时使用中等压缩
        MemoryPressureLevel.HIGH: 5,     # 内存紧张时使用高压缩
        MemoryPressureLevel.CRITICAL: 7  # 内存不足时使用更高压缩
    },
    # 高优先级资源
    ResourcePriority.HIGH: {
        MemoryPressureLevel.LOW: 1,      # 内存充足时使用低压缩
        MemoryPressureLevel.MEDIUM: 1,   # 内存适中时仍使用低压缩
        MemoryPressureLevel.HIGH: 3,     # 内存紧张时使用中等压缩
        MemoryPressureLevel.CRITICAL: 5  # 内存不足时使用高压缩
    }
}

# 默认算法映射（按优先级和内存压力级别）
DEFAULT_ALGO_MAP = {
    # 低优先级资源
    ResourcePriority.LOW: {
        MemoryPressureLevel.LOW: "zstd",     # 内存充足时使用平衡的zstd
        MemoryPressureLevel.MEDIUM: "zstd",  # 内存适中时仍使用zstd
        MemoryPressureLevel.HIGH: "bzip2",   # 内存紧张时使用更高压缩的bzip2
        MemoryPressureLevel.CRITICAL: "lzma" # 内存不足时使用最高压缩的lzma
    },
    # 中等优先级资源
    ResourcePriority.MEDIUM: {
        MemoryPressureLevel.LOW: "lz4",      # 内存充足时使用快速的lz4
        MemoryPressureLevel.MEDIUM: "zstd",  # 内存适中时使用平衡的zstd
        MemoryPressureLevel.HIGH: "zstd",    # 内存紧张时仍使用zstd
        MemoryPressureLevel.CRITICAL: "bzip2"# 内存不足时使用高压缩的bzip2
    },
    # 高优先级资源
    ResourcePriority.HIGH: {
        MemoryPressureLevel.LOW: "lz4",      # 内存充足时使用快速的lz4
        MemoryPressureLevel.MEDIUM: "lz4",   # 内存适中时仍使用lz4
        MemoryPressureLevel.HIGH: "zstd",    # 内存紧张时使用平衡的zstd
        MemoryPressureLevel.CRITICAL: "zstd" # 内存不足时仍使用zstd
    }
}

class SmartCompressor:
    """智能压缩器，可根据系统内存状态自动调整压缩参数"""
    
    def __init__(self, 
                 default_algo: str = "zstd",
                 default_level: int = 3,
                 monitoring_interval: float = 10.0,
                 change_threshold: float = 0.05,
                 config_path: Optional[str] = "configs/compression_hardware.yaml",
                 use_hardware_accel: bool = True):
        """
        初始化智能压缩器
        
        Args:
            default_algo: 默认压缩算法
            default_level: 默认压缩级别
            monitoring_interval: 监控间隔（秒）
            change_threshold: 内存变化阈值，超过此值重新评估压缩级别
            config_path: 配置文件路径
            use_hardware_accel: 是否使用硬件加速
        """
        self.default_algo = default_algo
        self.default_level = default_level
        self.monitoring_interval = monitoring_interval
        self.change_threshold = change_threshold
        self.config_path = config_path
        self.use_hardware_accel = use_hardware_accel
        
        # 当前内存压力级别
        self.current_pressure_level = MemoryPressureLevel.MEDIUM
        
        # 最后一次内存使用量
        self.last_memory_percent = self._get_memory_usage()
        
        # 当前使用的压缩器
        self.compressor = None
        self.hardware_compressor = None
        
        # 压缩统计信息
        self.stats = {
            "level_adjustments": 0,      # 调整次数
            "algo_switches": 0,          # 算法切换次数
            "compression_count": 0,      # 压缩操作次数
            "decompression_count": 0,    # 解压操作次数
            "bytes_processed": 0,        # 处理的总字节数
            "bytes_output": 0,           # 输出的总字节数
            "time_spent": 0.0,           # 压缩耗时（秒）
            "average_ratio": 0.0,        # 平均压缩率
            "memory_samples": [],        # 内存采样历史
            "last_update": time.time()   # 上次更新时间
        }
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化压缩器
        self._init_compressor()
        
        # 启动监控线程
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._memory_monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"智能压缩器初始化完成，默认算法: {default_algo}, 级别: {default_level}")
        logger.info(f"监控间隔: {monitoring_interval}秒, 变化阈值: {change_threshold*100:.1f}%")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict: 配置信息
        """
        default_config = {
            "memory_thresholds": {
                "low": 0.5,      # 50%以下为低压力
                "medium": 0.7,   # 50-70%为中等压力
                "high": 0.85,    # 70-85%为高压力
                "critical": 0.85 # 85%以上为临界压力
            },
            "adjustment_interval": self.monitoring_interval,
            "memory_change_threshold": self.change_threshold,
            "default_algo": self.default_algo,
            "default_level": self.default_level,
            "level_map": DEFAULT_LEVEL_MAP,
            "algo_map": DEFAULT_ALGO_MAP
        }
        
        if not self.config_path or not os.path.exists(self.config_path):
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return default_config
        
        try:
            if self.config_path.endswith('.yaml'):
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            else:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 确保配置包含所有必要字段
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
                    
            logger.info(f"已加载压缩配置: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}，使用默认配置")
            return default_config
    
    def _init_compressor(self) -> None:
        """初始化压缩器"""
        # 创建基础压缩器
        self.compressor = Compressor(
            algo=self.default_algo,
            level=self.default_level,
            threads=None  # 自动选择线程数
        )
        
        # 如果启用硬件加速，创建硬件加速压缩器
        if self.use_hardware_accel:
            try:
                self.hardware_compressor = get_best_hardware(
                    algorithm=self.default_algo,
                    level=self.default_level
                )
                logger.info(f"已初始化硬件加速压缩器: {type(self.hardware_compressor).__name__}")
            except Exception as e:
                logger.warning(f"初始化硬件加速压缩器失败: {str(e)}，将使用标准压缩器")
                self.hardware_compressor = None
    
    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用率
        
        Returns:
            float: 内存使用百分比(0.0-1.0)
        """
        try:
            return psutil.virtual_memory().percent / 100.0
        except Exception as e:
            logger.error(f"获取内存使用率失败: {str(e)}")
            return 0.7  # 返回默认中等压力值
    
    def _get_pressure_level(self, memory_percent: float) -> MemoryPressureLevel:
        """
        根据内存使用率确定压力级别
        
        Args:
            memory_percent: 内存使用百分比(0.0-1.0)
            
        Returns:
            MemoryPressureLevel: 内存压力级别
        """
        thresholds = self.config.get("memory_thresholds", {
            "low": 0.5,
            "medium": 0.7,
            "high": 0.85,
            "critical": 0.85
        })
        
        if memory_percent < thresholds["low"]:
            return MemoryPressureLevel.LOW
        elif memory_percent < thresholds["medium"]:
            return MemoryPressureLevel.MEDIUM
        elif memory_percent < thresholds["high"]:
            return MemoryPressureLevel.HIGH
        else:
            return MemoryPressureLevel.CRITICAL
    
    def _memory_monitor_loop(self) -> None:
        """内存监控循环，定期检查内存状态并调整压缩参数"""
        while self.monitoring_active:
            try:
                # 获取当前内存使用率
                current_memory_percent = self._get_memory_usage()
                
                # 检查内存变化是否超过阈值
                memory_change = abs(current_memory_percent - self.last_memory_percent)
                if memory_change >= self.change_threshold:
                    logger.debug(f"内存使用率变化: {memory_change*100:.1f}%，从 {self.last_memory_percent*100:.1f}% 到 {current_memory_percent*100:.1f}%")
                    
                    # 更新内存压力级别
                    new_pressure_level = self._get_pressure_level(current_memory_percent)
                    if new_pressure_level != self.current_pressure_level:
                        old_level = self.current_pressure_level
                        self.current_pressure_level = new_pressure_level
                        logger.info(f"内存压力级别变化: {old_level.name} -> {new_pressure_level.name}, 内存使用率: {current_memory_percent*100:.1f}%")
                        
                        # 更新压缩级别
                        self._adjust_compression_params()
                    
                    # 更新最后一次内存使用率
                    self.last_memory_percent = current_memory_percent
                
                # 记录内存采样
                self.stats["memory_samples"].append({
                    "time": time.time(),
                    "memory_percent": current_memory_percent,
                    "pressure_level": self.current_pressure_level.name
                })
                
                # 保持历史采样数据在合理范围内
                if len(self.stats["memory_samples"]) > 100:
                    self.stats["memory_samples"] = self.stats["memory_samples"][-100:]
                
                # 等待下一次检查
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"内存监控异常: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def _adjust_compression_params(self) -> None:
        """根据当前内存压力级别调整压缩参数"""
        # 记录调整次数
        self.stats["level_adjustments"] += 1
        
        # 目前应用中等优先级的默认设置
        priority = ResourcePriority.MEDIUM
        
        # 获取新的压缩级别和算法
        new_level = self._get_adjusted_level(priority)
        new_algo = self._get_adjusted_algo(priority)
        
        # 检查是否需要更新压缩器
        if new_level != self.default_level or new_algo != self.default_algo:
            logger.info(f"调整压缩参数: 算法 {self.default_algo} -> {new_algo}, 级别 {self.default_level} -> {new_level}")
            
            # 记录算法切换
            if new_algo != self.default_algo:
                self.stats["algo_switches"] += 1
            
            # 更新默认参数
            self.default_algo = new_algo
            self.default_level = new_level
            
            # 重新初始化压缩器
            self._init_compressor()
    
    def _get_adjusted_level(self, priority: ResourcePriority) -> int:
        """
        根据资源优先级和当前内存压力级别获取调整后的压缩级别
        
        Args:
            priority: 资源优先级
            
        Returns:
            int: 调整后的压缩级别
        """
        # 从配置获取级别映射
        level_map = self.config.get("level_map", DEFAULT_LEVEL_MAP)
        
        # 转换枚举为索引
        priority_idx = priority.value
        pressure_idx = self.current_pressure_level.value
        
        # 获取默认映射
        default_map = DEFAULT_LEVEL_MAP[priority]
        
        # 如果配置中有对应映射，使用配置值
        if priority_idx in level_map and pressure_idx in level_map[priority_idx]:
            return level_map[priority_idx][pressure_idx]
        
        # 否则使用默认映射
        return default_map[self.current_pressure_level]
    
    def _get_adjusted_algo(self, priority: ResourcePriority) -> str:
        """
        根据资源优先级和当前内存压力级别获取调整后的压缩算法
        
        Args:
            priority: 资源优先级
            
        Returns:
            str: 调整后的压缩算法
        """
        # 从配置获取算法映射
        algo_map = self.config.get("algo_map", DEFAULT_ALGO_MAP)
        
        # 转换枚举为索引
        priority_idx = priority.value
        pressure_idx = self.current_pressure_level.value
        
        # 获取默认映射
        default_map = DEFAULT_ALGO_MAP[priority]
        
        # 如果配置中有对应映射，使用配置值
        if priority_idx in algo_map and pressure_idx in algo_map[priority_idx]:
            return algo_map[priority_idx][pressure_idx]
        
        # 否则使用默认映射
        return default_map[self.current_pressure_level]
    
    def adjust_level(self, free_mem: int) -> int:
        """
        根据内存余量动态调整压缩级别
        
        Args:
            free_mem: 空闲内存量(MB)
            
        Returns:
            int: 调整后的压缩级别
        """
        # 简单的基于阈值的调整逻辑
        if free_mem < 1000:  # <1GB
            self.level = 9    # 最高压缩率
            return 9
        elif free_mem < 3000:  # 1-3GB
            self.level = 5    # 平衡模式
            return 5
        else:  # >3GB
            self.level = 1    # 快速模式
            return 1
    
    def compress(self, 
                data: Union[bytes, bytearray], 
                resource_type: str = "default", 
                priority: Optional[ResourcePriority] = None) -> Tuple[bytes, Dict[str, Any]]:
        """
        压缩数据，自动选择最佳压缩参数
        
        Args:
            data: 要压缩的数据
            resource_type: 资源类型，用于选择合适的压缩策略
            priority: 资源优先级，如果为None则根据资源类型推断
            
        Returns:
            Tuple[bytes, Dict]: 压缩数据和元数据
        """
        start_time = time.time()
        
        # 根据资源类型推断优先级
        if priority is None:
            priority = self._get_priority_for_resource(resource_type)
        
        # 根据优先级和当前内存压力调整压缩参数
        algo = self._get_adjusted_algo(priority)
        level = self._get_adjusted_level(priority)
        
        # 使用硬件加速器（如果可用）
        if self.use_hardware_accel and self.hardware_compressor:
            compressed, metadata = self.hardware_compressor.compress(data)
        else:
            # 如果当前压缩器配置与需要的不同，创建临时压缩器
            if algo != self.default_algo or level != self.default_level:
                temp_compressor = Compressor(algo=algo, level=level)
                compressed, metadata = temp_compressor.compress(data, with_metadata=True)
            else:
                compressed, metadata = self.compressor.compress(data, with_metadata=True)
        
        # 更新统计信息
        compression_time = time.time() - start_time
        compression_ratio = len(compressed) / len(data) if len(data) > 0 else 1.0
        
        self.stats["compression_count"] += 1
        self.stats["bytes_processed"] += len(data)
        self.stats["bytes_output"] += len(compressed)
        self.stats["time_spent"] += compression_time
        
        # 更新平均压缩率
        total_input = self.stats["bytes_processed"]
        total_output = self.stats["bytes_output"]
        self.stats["average_ratio"] = total_output / total_input if total_input > 0 else 1.0
        
        # 添加智能压缩元数据
        metadata.update({
            "smart_compression": True,
            "resource_type": resource_type,
            "priority": priority.name,
            "memory_pressure": self.current_pressure_level.name,
            "compression_time": compression_time,
            "memory_percent": self.last_memory_percent
        })
        
        return compressed, metadata
    
    def decompress(self, 
                 compressed: Union[bytes, bytearray], 
                 metadata: Optional[Dict[str, Any]] = None) -> bytes:
        """
        解压数据
        
        Args:
            compressed: 压缩数据
            metadata: 压缩元数据
            
        Returns:
            bytes: 解压后的数据
        """
        start_time = time.time()
        
        # 使用硬件加速器（如果可用）
        if (self.use_hardware_accel and self.hardware_compressor and 
            metadata and metadata.get("smart_compression")):
            decompressed = self.hardware_compressor.decompress(compressed, metadata)
        else:
            # 使用标准压缩器
            decompressed = decompress(compressed, metadata)
        
        # 更新统计信息
        decompression_time = time.time() - start_time
        
        self.stats["decompression_count"] += 1
        self.stats["time_spent"] += decompression_time
        
        return decompressed
    
    def _get_priority_for_resource(self, resource_type: str) -> ResourcePriority:
        """
        根据资源类型确定优先级
        
        Args:
            resource_type: 资源类型
            
        Returns:
            ResourcePriority: 资源优先级
        """
        # 高优先级资源类型
        high_priority_types = [
            "model_weights", "attention_cache", "temp_buffers"
        ]
        
        # 中等优先级资源类型
        medium_priority_types = [
            "intermediate_cache", "subtitle", "file_cache"
        ]
        
        # 低优先级资源类型
        low_priority_types = [
            "log_data", "backup", "debug_info"
        ]
        
        if resource_type in high_priority_types:
            return ResourcePriority.HIGH
        elif resource_type in medium_priority_types:
            return ResourcePriority.MEDIUM
        elif resource_type in low_priority_types:
            return ResourcePriority.LOW
        else:
            # 默认为中等优先级
            return ResourcePriority.MEDIUM
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取压缩统计信息
        
        Returns:
            Dict: 压缩统计信息
        """
        # 更新最后更新时间
        self.stats["last_update"] = time.time()
        
        # 如果内存采样过多，只保留最新的50个
        if len(self.stats["memory_samples"]) > 50:
            self.stats["memory_samples"] = self.stats["memory_samples"][-50:]
        
        # 返回统计副本
        return dict(self.stats)
    
    def __del__(self):
        """析构函数，停止监控线程"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

# 全局智能压缩器实例
_smart_compressor = None

def get_smart_compressor() -> SmartCompressor:
    """
    获取全局智能压缩器实例
    
    Returns:
        SmartCompressor: 智能压缩器实例
    """
    global _smart_compressor
    if _smart_compressor is None:
        _smart_compressor = SmartCompressor()
    return _smart_compressor

def smart_compress(data: Union[bytes, bytearray], 
                 resource_type: str = "default",
                 priority: Optional[ResourcePriority] = None) -> Tuple[bytes, Dict[str, Any]]:
    """
    使用智能压缩器压缩数据
    
    Args:
        data: 要压缩的数据
        resource_type: 资源类型
        priority: 资源优先级
        
    Returns:
        Tuple[bytes, Dict]: 压缩数据和元数据
    """
    compressor = get_smart_compressor()
    return compressor.compress(data, resource_type, priority)

def smart_decompress(compressed: Union[bytes, bytearray], 
                   metadata: Optional[Dict[str, Any]] = None) -> bytes:
    """
    使用智能压缩器解压数据
    
    Args:
        compressed: 压缩数据
        metadata: 压缩元数据
        
    Returns:
        bytes: 解压后的数据
    """
    compressor = get_smart_compressor()
    return compressor.decompress(compressed, metadata)

def get_compression_stats() -> Dict[str, Any]:
    """
    获取智能压缩统计信息
    
    Returns:
        Dict: 智能压缩统计信息
    """
    compressor = get_smart_compressor()
    return compressor.get_stats()

# 当模块作为主程序运行时，执行简单的演示
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建智能压缩器
    compressor = SmartCompressor(monitoring_interval=5.0)
    
    # 创建测试数据
    test_data = b"Test data " * 1000
    
    # 压缩并解压测试数据
    compressed, metadata = compressor.compress(test_data, "test")
    decompressed = compressor.decompress(compressed, metadata)
    
    # 打印结果
    print(f"原始大小: {len(test_data)} 字节")
    print(f"压缩大小: {len(compressed)} 字节")
    print(f"压缩率: {len(compressed)/len(test_data):.2f}")
    print(f"数据完整性: {'通过' if decompressed == test_data else '失败'}")
    
    # 等待一段时间，让监控线程运行
    print("等待监控线程运行...")
    for _ in range(3):
        time.sleep(compressor.monitoring_interval)
        stats = compressor.get_stats()
        memory_percent = compressor._get_memory_usage()
        pressure_level = compressor.current_pressure_level
        print(f"内存使用率: {memory_percent*100:.1f}%, 压力级别: {pressure_level.name}")
        print(f"压缩级别: {compressor.default_level}, 算法: {compressor.default_algo}")
    
    # 打印最终统计信息
    stats = compressor.get_stats()
    print(f"\n最终统计信息:")
    print(f"  调整次数: {stats['level_adjustments']}")
    print(f"  算法切换: {stats['algo_switches']}")
    print(f"  压缩操作: {stats['compression_count']}")
    print(f"  解压操作: {stats['decompression_count']}")
    print(f"  平均压缩率: {stats['average_ratio']:.3f}") 