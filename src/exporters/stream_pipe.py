#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
流式处理管道模块

提供高效的数据流处理框架，支持零拷贝操作，用于视频和音频处理流程。
通过流水线设计模式，将复杂的处理流程分解为独立可组合的处理单元。
"""

import os
import time
import logging
import threading
import inspect
from typing import List, Dict, Any, Optional, Callable, Union, Tuple, TypeVar, Generic, Iterable
from enum import Enum, auto
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

from src.utils.log_handler import get_logger
from src.utils.exceptions import ProcessingError
from src.exporters.memmap_engine import get_memmap_engine

# 配置日志记录器
logger = get_logger("stream_pipe")

# 类型别名
T = TypeVar('T')  # 输入数据类型
U = TypeVar('U')  # 输出数据类型
ProcessorFunc = Callable[[Any], Any]  # 处理器函数类型


class ProcessingMode(Enum):
    """处理模式枚举"""
    BATCH = auto()      # 批处理模式
    STREAMING = auto()  # 流式处理模式
    PARALLEL = auto()   # 并行处理模式


class ProcessingStage(Enum):
    """处理阶段枚举"""
    INIT = auto()       # 初始化
    PRE_PROCESS = auto()  # 预处理
    PROCESS = auto()    # 主处理
    POST_PROCESS = auto()  # 后处理
    COMPLETE = auto()   # 完成


@dataclass
class PipelineContext:
    """管道上下文数据类"""
    start_time: float = 0.0  # 开始时间
    end_time: float = 0.0    # 结束时间
    duration: float = 0.0    # 持续时间
    stage: ProcessingStage = ProcessingStage.INIT  # 当前阶段
    stats: Dict[str, Any] = None  # 统计信息
    metadata: Dict[str, Any] = None  # 元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.stats is None:
            self.stats = {}
        if self.metadata is None:
            self.metadata = {}
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        return self
    
    def stop(self):
        """停止计时"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self
    
    def update_stage(self, stage: ProcessingStage):
        """更新阶段"""
        self.stage = stage
        return self


class Processor(Generic[T, U], ABC):
    """处理器抽象基类"""
    
    def __init__(self, name: str = None):
        """初始化处理器
        
        Args:
            name: 处理器名称，如果为None则使用类名
        """
        self.name = name or self.__class__.__name__
        self.next_processor = None
        self.context = PipelineContext()
    
    @abstractmethod
    def process(self, data: T) -> U:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        pass
    
    def __call__(self, data: T) -> U:
        """调用处理器
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        self.context.start()
        try:
            result = self.process(data)
            return result
        finally:
            self.context.stop()


class FunctionProcessor(Processor[T, U]):
    """函数处理器，将函数包装为处理器"""
    
    def __init__(self, func: Callable[[T], U], name: str = None):
        """初始化函数处理器
        
        Args:
            func: 处理函数
            name: 处理器名称，如果为None则使用函数名
        """
        super().__init__(name or func.__name__)
        self.func = func
    
    def process(self, data: T) -> U:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理函数返回的结果
        """
        return self.func(data)


class TransformProcessor(Processor[T, U]):
    """转换处理器，支持数据转换处理"""
    
    def __init__(self, transform_func: Callable[[T], U], name: str = None):
        """初始化转换处理器
        
        Args:
            transform_func: 转换函数
            name: 处理器名称
        """
        super().__init__(name or getattr(transform_func, "__name__", "Transform"))
        self.transform_func = transform_func
    
    def process(self, data: T) -> U:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            转换后的数据
        """
        return self.transform_func(data)


class FilterProcessor(Processor[T, Optional[T]]):
    """过滤处理器，可以过滤掉不符合条件的数据"""
    
    def __init__(self, predicate: Callable[[T], bool], name: str = None):
        """初始化过滤处理器
        
        Args:
            predicate: 判断函数，返回True表示保留，False表示过滤掉
            name: 处理器名称
        """
        super().__init__(name or "Filter")
        self.predicate = predicate
    
    def process(self, data: T) -> Optional[T]:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            如果符合条件则返回原数据，否则返回None
        """
        return data if self.predicate(data) else None


class CompositeProcessor(Processor[T, Any]):
    """组合处理器，可以组合多个处理器"""
    
    def __init__(self, processors: List[Processor] = None, name: str = None):
        """初始化组合处理器
        
        Args:
            processors: 处理器列表
            name: 处理器名称
        """
        super().__init__(name or "Composite")
        self.processors = processors or []
    
    def add_processor(self, processor: Processor) -> 'CompositeProcessor':
        """添加处理器
        
        Args:
            processor: 要添加的处理器
            
        Returns:
            自身，支持链式调用
        """
        self.processors.append(processor)
        return self
    
    def process(self, data: T) -> Any:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        result = data
        for processor in self.processors:
            result = processor(result)
            # 如果某个处理器返回None，中断处理链
            if result is None:
                break
        return result


class ZeroCopyPipeline:
    """零拷贝处理管道
    
    通过引用传递而非数据复制来提高处理效率，特别适用于大型视频/音频数据处理
    """
    
    def __init__(self):
        """初始化零拷贝管道"""
        self.buffers = []  # 处理器列表
        self.context = PipelineContext()
        self.mode = ProcessingMode.STREAMING
        self.error_handler = None
    
    def add_stage(self, processor) -> 'ZeroCopyPipeline':
        """添加处理阶段
        
        Args:
            processor: 处理器，可以是函数或Processor对象
            
        Returns:
            自身，支持链式调用
        """
        # 如果是函数，包装为处理器
        if callable(processor) and not isinstance(processor, Processor):
            processor = FunctionProcessor(processor)
            
        # 添加到处理器列表
        self.buffers.append(processor)
        
        logger.debug(f"添加处理阶段: {processor.name}")
        return self
    
    def execute(self, input_data) -> Any:
        """执行管道处理
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理后的结果
        """
        self.context.start().update_stage(ProcessingStage.PROCESS)
        
        try:
            # 使用第一个输入作为初始结果
            result = input_data
            
            # 依次通过每个处理器
            for proc in self.buffers:
                # 更新处理上下文
                stage_name = getattr(proc, 'name', str(proc))
                logger.debug(f"执行处理阶段: {stage_name}")
                
                # 执行处理
                result = proc(result)
                
                # 如果返回None，中断处理
                if result is None:
                    logger.warning(f"处理阶段 {stage_name} 返回None，中断处理")
                    break
            
            self.context.update_stage(ProcessingStage.COMPLETE)
            return result
            
        except Exception as e:
            logger.error(f"管道执行异常: {str(e)}")
            if self.error_handler:
                return self.error_handler(e, self.context)
            raise ProcessingError(f"管道执行失败: {str(e)}")
        finally:
            self.context.stop()
    
    def set_error_handler(self, handler: Callable[[Exception, PipelineContext], Any]) -> 'ZeroCopyPipeline':
        """设置错误处理器
        
        Args:
            handler: 错误处理函数
            
        Returns:
            自身，支持链式调用
        """
        self.error_handler = handler
        return self
    
    def set_mode(self, mode: ProcessingMode) -> 'ZeroCopyPipeline':
        """设置处理模式
        
        Args:
            mode: 处理模式
            
        Returns:
            自身，支持链式调用
        """
        self.mode = mode
        return self
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_duration': self.context.duration,
            'stage': self.context.stage.name,
            'mode': self.mode.name,
            'stages_count': len(self.buffers),
            'processors': []
        }
        
        # 收集各处理器的统计信息
        for proc in self.buffers:
            if hasattr(proc, 'context'):
                proc_stats = {
                    'name': proc.name,
                    'duration': proc.context.duration
                }
                stats['processors'].append(proc_stats)
        
        return stats


class VideoProcessor(Processor[np.ndarray, np.ndarray]):
    """视频处理器基类"""
    
    def __init__(self, name: str = None):
        """初始化视频处理器
        
        Args:
            name: 处理器名称
        """
        super().__init__(name or "VideoProcessor")
        self.memmap_engine = get_memmap_engine()
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """处理单帧
        
        Args:
            frame: 输入帧
            
        Returns:
            处理后的帧
        """
        pass
    
    def process(self, frames: np.ndarray) -> np.ndarray:
        """处理多帧
        
        Args:
            frames: 输入帧数组
            
        Returns:
            处理后的帧数组
        """
        # 如果输入是单帧
        if len(frames.shape) == 3:  # 高度x宽度x通道
            return self.process_frame(frames)
        
        # 如果是多帧（视频剪辑）
        result = np.zeros_like(frames)
        for i in range(len(frames)):
            result[i] = self.process_frame(frames[i])
        
        return result


class AudioProcessor(Processor[np.ndarray, np.ndarray]):
    """音频处理器基类"""
    
    def __init__(self, name: str = None):
        """初始化音频处理器
        
        Args:
            name: 处理器名称
        """
        super().__init__(name or "AudioProcessor")
    
    @abstractmethod
    def process_audio(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """处理音频
        
        Args:
            audio: 音频数据
            sample_rate: 采样率
            
        Returns:
            处理后的音频数据
        """
        pass
    
    def process(self, data: Tuple[np.ndarray, int]) -> Tuple[np.ndarray, int]:
        """处理音频数据
        
        Args:
            data: (音频数据, 采样率)元组
            
        Returns:
            处理后的(音频数据, 采样率)元组
        """
        audio, sample_rate = data
        processed_audio = self.process_audio(audio, sample_rate)
        return processed_audio, sample_rate


class StreamingPipeline(ZeroCopyPipeline):
    """流式处理管道
    
    支持流式处理大型数据，适用于视频和音频等媒体处理
    """
    
    def __init__(self, chunk_size: int = 30):
        """初始化流式处理管道
        
        Args:
            chunk_size: 分块大小，例如视频帧数
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.mode = ProcessingMode.STREAMING
    
    def process_stream(self, data_stream: Iterable[Any]) -> Iterable[Any]:
        """流式处理数据
        
        Args:
            data_stream: 数据流
            
        Yields:
            处理后的数据块
        """
        self.context.start().update_stage(ProcessingStage.PROCESS)
        
        try:
            # 处理每个数据块
            for chunk in data_stream:
                # 执行管道处理
                result = self.execute(chunk)
                
                # 生成处理结果
                if result is not None:
                    yield result
                    
            self.context.update_stage(ProcessingStage.COMPLETE)
            
        except Exception as e:
            logger.error(f"流式处理异常: {str(e)}")
            if self.error_handler:
                self.error_handler(e, self.context)
            else:
                raise ProcessingError(f"流式处理失败: {str(e)}")
        finally:
            self.context.stop()


# 工厂函数，便于创建常用类型的处理器
def create_processor(processor_type: str, *args, **kwargs) -> Processor:
    """创建处理器工厂函数
    
    Args:
        processor_type: 处理器类型
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        创建的处理器
    """
    processor_types = {
        'function': FunctionProcessor,
        'transform': TransformProcessor,
        'filter': FilterProcessor,
        'composite': CompositeProcessor,
        'video': VideoProcessor,
        'audio': AudioProcessor
    }
    
    processor_class = processor_types.get(processor_type.lower())
    if processor_class:
        return processor_class(*args, **kwargs)
    
    raise ValueError(f"未知的处理器类型: {processor_type}")


# 快捷函数
def create_pipeline() -> ZeroCopyPipeline:
    """创建零拷贝管道
    
    Returns:
        ZeroCopyPipeline实例
    """
    return ZeroCopyPipeline()


def create_streaming_pipeline(chunk_size: int = 30) -> StreamingPipeline:
    """创建流式处理管道
    
    Args:
        chunk_size: 分块大小
        
    Returns:
        StreamingPipeline实例
    """
    return StreamingPipeline(chunk_size=chunk_size)


# 简单示例
if __name__ == "__main__":
    # 定义一些示例处理器
    def double_value(x):
        return x * 2
    
    def add_ten(x):
        return x + 10
    
    def is_positive(x):
        return x > 0
    
    # 创建管道
    pipeline = ZeroCopyPipeline()
    
    # 添加处理阶段
    pipeline.add_stage(double_value)
    pipeline.add_stage(add_ten)
    pipeline.add_stage(FilterProcessor(is_positive, "PositiveFilter"))
    
    # 执行管道
    result = pipeline.execute(5)
    
    logger.info(f"处理结果: {result}")
    logger.info(f"处理统计: {pipeline.get_stats()}") 