#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全回退引擎模块

提供高效的内存和处理方式管理，在资源不足或硬件加速不可用时智能降级，
确保系统在不同环境下的稳定性和性能。主要功能包括：
1. 自动检测零拷贝能力
2. 资源不足时降级处理
3. 处理策略自适应选择
4. 错误恢复和降级处理链
"""

import os
import psutil
import time
import traceback
import logging
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

from src.utils.log_handler import get_logger
from src.utils.exceptions import ProcessingError
from src.exporters.memmap_engine import get_memmap_engine
from src.exporters.hw_detector import check_zero_copy_availability

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# 配置日志记录器
logger = get_logger("fallback_engine")

class ZeroCopyUnavailableError(ProcessingError):
    """零拷贝模式不可用错误"""
    
    def __init__(self, message=None, details=None):
        """初始化零拷贝不可用错误
        
        Args:
            message: 错误消息
            details: 详细信息
        """
        if message is None:
            message = "零拷贝处理不可用，将回退到传统处理方式"
            
        super().__init__(message, processor_name="ZeroCopyProcessor", details=details)

class ProcessingMode(Enum):
    """处理模式枚举"""
    ZERO_COPY = auto()     # 零拷贝模式，使用内存映射和指针传递
    TRADITIONAL = auto()   # 传统模式，完整数据复制
    HYBRID = auto()        # 混合模式，根据数据大小智能选择
    AUTO = auto()          # 自动模式，系统自动选择最佳方式

class FallbackEngine:
    """回退引擎"""
    
    def __init__(self):
        """初始化回退引擎"""
        self.memory_monitor = psutil.Process()
        
        # 配置回退阈值
        self.fallback_thresholds = {
            'memory': 0.9,          # 内存使用超过90%触发回退
            'large_file': 100 * 1024 * 1024,  # 100MB以上文件考虑零拷贝
            'recovery_wait': 5.0,   # 恢复等待时间（秒）
        }
        
        # 回退状态
        self.fallback_status = {
            'is_active': False,
            'active_fallbacks': [],
            'last_error': None,
            'error_count': 0,
            'last_check_time': time.time()
        }
        
        # 注册处理函数
        self.processing_functions = {}
        
        # 初始化零拷贝可用性
        self.zero_copy_available = check_zero_copy_availability()
        logger.info(f"零拷贝处理{'可用' if self.zero_copy_available else '不可用'}")
    
    def register_processor(self, 
                         name: str, 
                         zero_copy_func: Callable, 
                         traditional_func: Callable):
        """注册处理函数对
        
        Args:
            name: 处理器名称
            zero_copy_func: 零拷贝处理函数
            traditional_func: 传统处理函数
        """
        self.processing_functions[name] = {
            'zero_copy': zero_copy_func,
            'traditional': traditional_func
        }
        logger.debug(f"已注册处理器: {name}")
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用率(0-1)
        
        Returns:
            float: 内存使用率(0-1)
        """
        try:
            return psutil.virtual_memory().percent / 100.0
        except Exception as e:
            logger.error(f"获取内存使用率失败: {e}")
            return 0.0
    
    def should_use_zero_copy(self, data_size: Optional[int] = None) -> bool:
        """判断是否应使用零拷贝模式
        
        Args:
            data_size: 数据大小（字节）
            
        Returns:
            bool: 是否应使用零拷贝
        """
        # 如果零拷贝不可用，直接返回False
        if not self.zero_copy_available:
            return False
        
        # 内存使用率过高，不使用零拷贝以避免额外的映射开销
        if self.get_memory_usage() > 0.95:
            return False
        
        # 如果数据较大，优先使用零拷贝
        if data_size and data_size > self.fallback_thresholds['large_file']:
            return True
            
        # 内存使用率合理，可以使用零拷贝
        return self.get_memory_usage() < self.fallback_thresholds['memory']
    
    def safe_zero_copy(self, input_data, fallback_threshold=0.9):
        """安全的零拷贝处理函数
        
        尝试使用零拷贝处理，如不可用则回退到传统处理
        
        Args:
            input_data: 输入数据
            fallback_threshold: 回退阈值，内存使用超过此比例时回退
            
        Returns:
            处理结果
        """
        try:
            # 尝试零拷贝处理
            return self.zero_copy_process(input_data)
        except ZeroCopyUnavailableError:
            # 零拷贝不可用，检查内存使用情况
            if self.get_memory_usage() < fallback_threshold:
                # 内存充足，使用传统处理
                return self.traditional_process(input_data)
            # 内存不足，抛出异常
            raise
    
    def zero_copy_process(self, input_data):
        """零拷贝处理抽象方法
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
            
        Raises:
            ZeroCopyUnavailableError: 零拷贝处理不可用
            NotImplementedError: 未实现具体处理逻辑
        """
        if not self.zero_copy_available:
            raise ZeroCopyUnavailableError("零拷贝功能不可用")
        
        # 此方法需要在子类中实现具体的零拷贝处理逻辑
        raise NotImplementedError("零拷贝处理方法需要在子类中实现")
    
    def traditional_process(self, input_data):
        """传统处理抽象方法
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
            
        Raises:
            NotImplementedError: 未实现具体处理逻辑
        """
        # 此方法需要在子类中实现具体的传统处理逻辑
        raise NotImplementedError("传统处理方法需要在子类中实现")
    
    def process_with_fallback(self, 
                           name: str, 
                           input_data: Any, 
                           mode: ProcessingMode = ProcessingMode.AUTO,
                           **kwargs) -> Any:
        """带回退的处理
        
        根据处理模式和系统状态选择合适的处理方式
        
        Args:
            name: 处理器名称
            input_data: 输入数据
            mode: 处理模式
            **kwargs: 传递给处理函数的额外参数
            
        Returns:
            处理结果
            
        Raises:
            ProcessingError: 处理错误
        """
        # 更新回退状态
        self._update_fallback_status()
        
        if name not in self.processing_functions:
            raise ProcessingError(f"未注册的处理器: {name}")
        
        # 获取处理函数
        processor = self.processing_functions[name]
        zero_copy_func = processor['zero_copy']
        traditional_func = processor['traditional']
        
        # 确定处理模式
        use_zero_copy = False
        
        if mode == ProcessingMode.ZERO_COPY:
            use_zero_copy = True
        elif mode == ProcessingMode.TRADITIONAL:
            use_zero_copy = False
        elif mode == ProcessingMode.AUTO or mode == ProcessingMode.HYBRID:
            # 自动或混合模式，根据数据大小和内存使用情况选择
            data_size = self._estimate_data_size(input_data)
            use_zero_copy = self.should_use_zero_copy(data_size)
        
        # 记录选择的处理模式
        logger.debug(f"处理器 {name} 使用{'零拷贝' if use_zero_copy else '传统'}模式")
        
        try:
            # 尝试处理
            if use_zero_copy:
                try:
                    result = zero_copy_func(input_data, **kwargs)
                    # 成功后重置错误计数
                    self.fallback_status['error_count'] = 0
                    return result
                except (ZeroCopyUnavailableError, Exception) as e:
                    logger.warning(f"零拷贝处理失败: {e}, 回退到传统处理")
                    self.fallback_status['error_count'] += 1
                    self.fallback_status['last_error'] = str(e)
                    self.fallback_status['is_active'] = True
                    self.fallback_status['active_fallbacks'].append(name)
                    
                    # 回退到传统处理
                    return traditional_func(input_data, **kwargs)
            else:
                # 直接使用传统处理
                return traditional_func(input_data, **kwargs)
                
        except Exception as e:
            # 处理过程中出错
            logger.error(f"处理器 {name} 执行失败: {e}")
            self.fallback_status['error_count'] += 1
            self.fallback_status['last_error'] = str(e)
            
            # 构建错误详情
            error_details = {
                'processor': name,
                'mode': 'traditional' if not use_zero_copy else 'zero_copy',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
            raise ProcessingError(
                f"处理失败: {e}", 
                processor_name=name,
                details=error_details
            )
    
    def _estimate_data_size(self, data: Any) -> Optional[int]:
        """估计数据大小
        
        Args:
            data: 输入数据
            
        Returns:
            Optional[int]: 估计的数据大小（字节）
        """
        try:
            # 文件路径
            if isinstance(data, str) and os.path.isfile(data):
                return os.path.getsize(data)
            
            # 二进制数据
            elif isinstance(data, bytes):
                return len(data)
            
            # 数组或列表
            elif hasattr(data, 'nbytes'):  # numpy数组
                return data.nbytes
            elif hasattr(data, 'size'):  # 某些数组类型
                if hasattr(data, 'itemsize'):
                    return data.size * data.itemsize
                return data.size
                
            # 无法估计
            return None
            
        except Exception as e:
            logger.debug(f"数据大小估计失败: {e}")
            return None
    
    def _update_fallback_status(self):
        """更新回退状态"""
        # 检查是否需要更新状态
        current_time = time.time()
        if current_time - self.fallback_status['last_check_time'] < 10:
            # 10秒内不重复检查
            return
            
        # 更新检查时间
        self.fallback_status['last_check_time'] = current_time
        
        # 检查内存使用情况
        memory_usage = self.get_memory_usage()
        if memory_usage < self.fallback_thresholds['memory'] * 0.8:
            # 内存使用率较低，可以尝试退出回退状态
            if self.fallback_status['is_active']:
                logger.info(f"内存使用率已下降至 {memory_usage:.1%}，退出回退状态")
                self.fallback_status['is_active'] = False
                self.fallback_status['active_fallbacks'] = []
    
    def get_fallback_status(self) -> Dict[str, Any]:
        """获取回退状态
        
        Returns:
            Dict[str, Any]: 回退状态信息
        """
        # 添加当前内存使用情况
        status = self.fallback_status.copy()
        status['current_memory_usage'] = self.get_memory_usage()
        status['zero_copy_available'] = self.zero_copy_available
        return status


# 创建全局回退引擎实例
_fallback_engine = None

def get_fallback_engine() -> FallbackEngine:
    """获取全局回退引擎实例
    
    Returns:
        FallbackEngine: 回退引擎实例
    """
    global _fallback_engine
    if _fallback_engine is None:
        _fallback_engine = FallbackEngine()
    return _fallback_engine

def safe_zero_copy(input_data, fallback_threshold=0.9):
    """安全的零拷贝处理函数（全局）
    
    尝试使用零拷贝处理，如不可用则回退到传统处理
    
    Args:
        input_data: 输入数据
        fallback_threshold: 回退阈值，内存使用超过此比例时回退
        
    Returns:
        处理结果
    """
    try:
        # 尝试零拷贝处理
        return zero_copy_process(input_data)
    except ZeroCopyUnavailableError:
        # 零拷贝不可用，检查内存使用情况
        if get_memory_usage() < fallback_threshold:
            # 内存充足，使用传统处理
            return traditional_process(input_data)
        # 内存不足，抛出异常
        raise

def zero_copy_process(input_data):
    """零拷贝处理函数（全局）
    
    此函数需要由具体使用场景实现，这里只是一个接口
    
    Args:
        input_data: 输入数据
        
    Returns:
        处理结果
    
    Raises:
        ZeroCopyUnavailableError: 零拷贝处理不可用
    """
    # 检查零拷贝可用性（由hw_detector模块提供）
    if not check_zero_copy_availability():
        raise ZeroCopyUnavailableError("零拷贝处理不可用")
    
    # 这里应该实现具体的零拷贝处理逻辑
    # 如果实际使用时，应根据具体场景实现此函数
    raise NotImplementedError("零拷贝处理函数未实现")

def traditional_process(input_data):
    """传统处理函数（全局）
    
    此函数需要由具体使用场景实现，这里只是一个接口
    
    Args:
        input_data: 输入数据
        
    Returns:
        处理结果
    """
    # 这里应该实现具体的传统处理逻辑
    # 如果实际使用时，应根据具体场景实现此函数
    raise NotImplementedError("传统处理函数未实现")

def get_memory_usage() -> float:
    """获取当前内存使用率(0-1)
    
    Returns:
        float: 内存使用率(0-1)
    """
    try:
        return psutil.virtual_memory().percent / 100.0
    except Exception as e:
        logger.error(f"获取内存使用率失败: {e}")
        return 0.0 