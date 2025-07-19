#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 批量处理器模块

提供高效的批量任务处理能力，支持：
1. 大文件分块处理
2. 批量任务管理
3. 内存优化处理
4. 4GB内存设备兼容
"""

import os
import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Iterator
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

class BatchStatus(Enum):
    """批处理状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchTask:
    """批处理任务"""
    task_id: str
    task_func: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: int = 0
    max_retries: int = 3
    timeout: Optional[float] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}

@dataclass
class BatchResult:
    """批处理结果"""
    batch_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_time: float
    results: List[Any]
    errors: List[str]

class ChunkedProcessor:
    """分块处理器"""
    
    def __init__(self, chunk_size_mb: int = 100):
        """初始化分块处理器
        
        Args:
            chunk_size_mb: 分块大小（MB）
        """
        self.chunk_size_bytes = chunk_size_mb * 1024 * 1024
        
    def process_file_in_chunks(self, file_path: str, processor_func: Callable, 
                              chunk_overlap: int = 0) -> List[Any]:
        """分块处理文件
        
        Args:
            file_path: 文件路径
            processor_func: 处理函数
            chunk_overlap: 块重叠大小（字节）
            
        Returns:
            List[Any]: 处理结果列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        file_size = os.path.getsize(file_path)
        results = []
        
        logger.info(f"开始分块处理文件: {file_path}, 大小: {file_size / (1024**2):.2f}MB")
        
        with open(file_path, 'rb') as f:
            chunk_num = 0
            position = 0
            
            while position < file_size:
                # 计算当前块大小
                remaining = file_size - position
                current_chunk_size = min(self.chunk_size_bytes, remaining)
                
                # 读取数据块
                f.seek(position)
                chunk_data = f.read(current_chunk_size)
                
                try:
                    # 处理数据块
                    chunk_result = processor_func(chunk_data, chunk_num, position)
                    results.append(chunk_result)
                    
                    logger.debug(f"块 {chunk_num} 处理完成, 位置: {position}-{position + current_chunk_size}")
                    
                except Exception as e:
                    logger.error(f"块 {chunk_num} 处理失败: {e}")
                    results.append(None)
                
                # 移动到下一块
                position += current_chunk_size - chunk_overlap
                chunk_num += 1
                
        logger.info(f"文件分块处理完成: {len(results)} 个块")
        return results
        
    def process_text_in_chunks(self, text: str, processor_func: Callable,
                              chunk_size_chars: int = 10000, 
                              chunk_overlap_chars: int = 100) -> List[Any]:
        """分块处理文本
        
        Args:
            text: 输入文本
            processor_func: 处理函数
            chunk_size_chars: 块大小（字符数）
            chunk_overlap_chars: 块重叠大小（字符数）
            
        Returns:
            List[Any]: 处理结果列表
        """
        text_length = len(text)
        results = []
        
        logger.info(f"开始分块处理文本: 长度 {text_length} 字符")
        
        chunk_num = 0
        position = 0
        
        while position < text_length:
            # 计算当前块大小
            remaining = text_length - position
            current_chunk_size = min(chunk_size_chars, remaining)
            
            # 提取文本块
            end_position = position + current_chunk_size
            chunk_text = text[position:end_position]
            
            try:
                # 处理文本块
                chunk_result = processor_func(chunk_text, chunk_num, position)
                results.append(chunk_result)
                
                logger.debug(f"文本块 {chunk_num} 处理完成, 位置: {position}-{end_position}")
                
            except Exception as e:
                logger.error(f"文本块 {chunk_num} 处理失败: {e}")
                results.append(None)
            
            # 移动到下一块
            position += current_chunk_size - chunk_overlap_chars
            chunk_num += 1
            
        logger.info(f"文本分块处理完成: {len(results)} 个块")
        return results

class LargeFileProcessor:
    """大文件处理器"""
    
    def __init__(self, max_file_size_gb: float = 5.0, temp_dir: Optional[str] = None):
        """初始化大文件处理器
        
        Args:
            max_file_size_gb: 最大文件大小限制（GB）
            temp_dir: 临时目录
        """
        self.max_file_size_bytes = max_file_size_gb * 1024 * 1024 * 1024
        self.temp_dir = Path(temp_dir) if temp_dir else Path.cwd() / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
    def can_process_file(self, file_path: str) -> bool:
        """检查是否可以处理文件"""
        if not os.path.exists(file_path):
            return False
            
        file_size = os.path.getsize(file_path)
        return file_size <= self.max_file_size_bytes
        
    def process_large_file(self, file_path: str, processor_func: Callable,
                          chunk_size_mb: int = 100) -> Any:
        """处理大文件
        
        Args:
            file_path: 文件路径
            processor_func: 处理函数
            chunk_size_mb: 分块大小（MB）
            
        Returns:
            Any: 处理结果
        """
        if not self.can_process_file(file_path):
            raise ValueError(f"文件过大或不存在: {file_path}")
            
        # 使用分块处理器
        chunked_processor = ChunkedProcessor(chunk_size_mb)
        return chunked_processor.process_file_in_chunks(file_path, processor_func)

class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        """初始化批量处理器
        
        Args:
            max_workers: 最大工作线程数
            max_queue_size: 最大队列大小
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 任务管理
        self.batches: Dict[str, Dict[str, Any]] = {}
        self.batch_counter = 0
        
        # 线程池（延迟初始化）
        self._executor = None
        
        logger.info(f"批量处理器初始化完成: max_workers={max_workers}")
        
    @property
    def executor(self):
        """获取线程池执行器（延迟初始化）"""
        if self._executor is None:
            # 直接使用threading模块实现
            import threading
            import queue as queue_module

            class SimpleExecutor:
                def __init__(self, max_workers):
                    self.max_workers = max_workers
                    self.task_queue = queue_module.Queue()
                    self.workers = []
                    self.shutdown_flag = False
                    self._start_workers()

                def _start_workers(self):
                    for i in range(self.max_workers):
                        worker = threading.Thread(target=self._worker, daemon=True)
                        worker.start()
                        self.workers.append(worker)

                def _worker(self):
                    while not self.shutdown_flag:
                        try:
                            task_func, args, kwargs = self.task_queue.get(timeout=1)
                            try:
                                task_func(*args, **kwargs)
                            except Exception as e:
                                logger.error(f"批处理任务执行失败: {e}")
                            finally:
                                self.task_queue.task_done()
                        except queue_module.Empty:
                            continue

                def submit(self, fn, *args, **kwargs):
                    self.task_queue.put((fn, args, kwargs))

                def shutdown(self, wait=True):
                    self.shutdown_flag = True
                    if wait:
                        for worker in self.workers:
                            worker.join(timeout=5)

            self._executor = SimpleExecutor(self.max_workers)
        return self._executor
        
    def submit_batch(self, tasks: List[BatchTask], batch_id: Optional[str] = None) -> str:
        """提交批量任务
        
        Args:
            tasks: 任务列表
            batch_id: 批次ID（可选）
            
        Returns:
            str: 批次ID
        """
        if batch_id is None:
            batch_id = f"batch_{self.batch_counter}_{int(time.time())}"
            self.batch_counter += 1
            
        # 创建批次记录
        batch_info = {
            "batch_id": batch_id,
            "tasks": tasks,
            "status": BatchStatus.PENDING,
            "start_time": None,
            "end_time": None,
            "results": [],
            "errors": [],
            "completed_count": 0,
            "failed_count": 0
        }
        
        self.batches[batch_id] = batch_info
        
        # 提交任务到线程池
        self._process_batch_async(batch_id)
        
        logger.info(f"批量任务已提交: {batch_id}, 任务数: {len(tasks)}")
        return batch_id
        
    def _process_batch_async(self, batch_id: str):
        """异步处理批次"""
        def process_batch():
            batch_info = self.batches[batch_id]
            batch_info["status"] = BatchStatus.PROCESSING
            batch_info["start_time"] = time.time()
            
            try:
                # 处理所有任务
                for task in batch_info["tasks"]:
                    try:
                        result = task.task_func(*task.args, **task.kwargs)
                        batch_info["results"].append(result)
                        batch_info["completed_count"] += 1
                        
                    except Exception as e:
                        error_msg = f"任务 {task.task_id} 失败: {str(e)}"
                        batch_info["errors"].append(error_msg)
                        batch_info["failed_count"] += 1
                        logger.error(error_msg)
                
                # 更新批次状态
                batch_info["status"] = BatchStatus.COMPLETED
                batch_info["end_time"] = time.time()
                
                logger.info(f"批次处理完成: {batch_id}")
                
            except Exception as e:
                batch_info["status"] = BatchStatus.FAILED
                batch_info["end_time"] = time.time()
                logger.error(f"批次处理失败: {batch_id}, 错误: {e}")
        
        # 提交到线程池
        self.executor.submit(process_batch)
        
    def get_batch_status(self, batch_id: str) -> Optional[BatchStatus]:
        """获取批次状态"""
        if batch_id not in self.batches:
            return None
        return self.batches[batch_id]["status"]
        
    def get_batch_result(self, batch_id: str) -> Optional[BatchResult]:
        """获取批次结果"""
        if batch_id not in self.batches:
            return None
            
        batch_info = self.batches[batch_id]
        
        if batch_info["status"] not in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            return None
            
        total_time = 0
        if batch_info["start_time"] and batch_info["end_time"]:
            total_time = batch_info["end_time"] - batch_info["start_time"]
            
        total_tasks = len(batch_info["tasks"])
        success_rate = (batch_info["completed_count"] / total_tasks * 100) if total_tasks > 0 else 0
        
        return BatchResult(
            batch_id=batch_id,
            total_tasks=total_tasks,
            completed_tasks=batch_info["completed_count"],
            failed_tasks=batch_info["failed_count"],
            success_rate=success_rate,
            total_time=total_time,
            results=batch_info["results"],
            errors=batch_info["errors"]
        )
        
    def cancel_batch(self, batch_id: str) -> bool:
        """取消批次"""
        if batch_id not in self.batches:
            return False
            
        batch_info = self.batches[batch_id]
        if batch_info["status"] == BatchStatus.PROCESSING:
            batch_info["status"] = BatchStatus.CANCELLED
            logger.info(f"批次已取消: {batch_id}")
            return True
            
        return False
        
    def shutdown(self, wait: bool = True):
        """关闭批量处理器"""
        if self._executor:
            self._executor.shutdown(wait=wait)
            logger.info("批量处理器已关闭")
