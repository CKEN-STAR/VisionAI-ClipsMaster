#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时日志写入引擎

提供高性能、低延迟的日志写入功能，支持批量缓冲和异步写入。
集成结构化日志系统，提供实时日志记录能力。
"""

import os
import json
import time
import queue
import threading
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_temp_log_directory

# 模块日志记录器
logger = get_module_logger("log_writer")

class AsyncLogWriter:
    """
    异步日志写入器
    
    在后台线程中处理日志写入操作，避免阻塞主线程。
    支持批量写入和失败重试。
    """
    
    def __init__(self, log_dir: Union[str, Path] = None, 
                 file_prefix: str = "realtime",
                 max_queue_size: int = 10000,
                 flush_interval: float = 1.0,
                 retry_interval: float = 0.5,
                 max_retries: int = 3):
        """
        初始化异步日志写入器
        
        Args:
            log_dir: 日志文件目录（默认使用跨平台日志目录）
            file_prefix: 日志文件前缀
            max_queue_size: 最大队列大小
            flush_interval: 强制刷新间隔（秒）
            retry_interval: 重试间隔（秒）
            max_retries: 最大重试次数
        """
        # 使用跨平台日志目录
        if log_dir is None:
            self.log_dir = get_log_directory() / "realtime"
        else:
            self.log_dir = Path(log_dir)
            
        self.file_prefix = file_prefix
        self.flush_interval = flush_interval
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前日志文件
        self._current_log_file = None
        self._current_date = None
        self._update_log_file()
        
        # 写入队列和线程
        self.queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(
            target=self._worker_loop, 
            daemon=True,
            name="AsyncLogWriter"
        )
        self.worker_thread.start()
        
        # 统计信息
        self.stats = {
            "enqueued": 0,
            "written": 0,
            "errors": 0,
            "retries": 0,
            "batches": 0,
            "queue_full_events": 0
        }
        
    def _update_log_file(self):
        """更新当前日志文件路径（按日期分割）"""
        today = datetime.datetime.now().date()
        
        # 如果日期变化或尚未设置日志文件
        if self._current_date != today or self._current_log_file is None:
            self._current_date = today
            date_str = today.strftime("%Y-%m-%d")
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            self._current_log_file = self.log_dir / f"{self.file_prefix}_{date_str}_{timestamp}.jsonl"
            logger.info(f"切换日志文件: {self._current_log_file}")
            
    def write_batch(self, entries: List[Any]):
        """
        批量写入日志条目
        
        Args:
            entries: 要写入的日志条目列表
        """
        if not entries:
            return
            
        try:
            self.queue.put_nowait(entries)
            self.stats["enqueued"] += len(entries)
        except queue.Full:
            # 队列已满，尝试直接写入
            logger.warning("写入队列已满，执行同步写入")
            self._write_to_file(entries)
            self.stats["queue_full_events"] += 1
            
    def _worker_loop(self):
        """工作线程主循环"""
        last_flush_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                # 尝试从队列获取条目，超时后检查刷新间隔
                try:
                    entries = self.queue.get(timeout=0.1)
                    self._write_entries(entries)
                    self.queue.task_done()
                except queue.Empty:
                    # 队列为空，检查是否需要强制刷新
                    pass
                    
                # 检查是否需要更新日志文件（日期变化）
                self._update_log_file()
                
                # 检查是否需要刷新文件（定时刷新）
                current_time = time.time()
                if current_time - last_flush_time > self.flush_interval:
                    os.fsync(self._current_log_file.open('a').fileno())
                    last_flush_time = current_time
                    
            except Exception as e:
                logger.error(f"日志写入线程发生错误: {str(e)}")
                self.stats["errors"] += 1
                time.sleep(0.1)  # 避免错误情况下的CPU占用
                
        # 线程结束前，处理剩余条目
        self._drain_queue()
                
    def _write_entries(self, entries: List[Any]):
        """写入日志条目并处理重试"""
        retries = 0
        while retries <= self.max_retries:
            try:
                self._write_to_file(entries)
                self.stats["written"] += len(entries)
                self.stats["batches"] += 1
                break
            except Exception as e:
                retries += 1
                self.stats["retries"] += 1
                logger.error(f"写入日志失败 (尝试 {retries}/{self.max_retries}): {str(e)}")
                
                if retries <= self.max_retries:
                    time.sleep(self.retry_interval)
                else:
                    logger.error(f"日志写入重试失败，丢弃 {len(entries)} 条日志")
                    self.stats["errors"] += 1
                    
    def _write_to_file(self, entries: List[Any]):
        """将条目写入文件"""
        self._update_log_file()
        
        with open(self._current_log_file, 'a', encoding='utf-8') as f:
            for entry in entries:
                if isinstance(entry, dict):
                    # 处理字典对象：转换为JSON
                    json_str = json.dumps(entry, ensure_ascii=False)
                    f.write(json_str + '\n')
                elif isinstance(entry, str):
                    # 处理字符串：直接写入
                    f.write(entry + '\n')
                else:
                    # 处理其他类型：转换为字符串
                    f.write(str(entry) + '\n')
                    
    def _drain_queue(self):
        """清空队列中的所有条目"""
        remaining = []
        
        # 从队列中获取所有剩余条目
        while not self.queue.empty():
            try:
                entries = self.queue.get_nowait()
                if isinstance(entries, list):
                    remaining.extend(entries)
                else:
                    remaining.append(entries)
                self.queue.task_done()
            except queue.Empty:
                break
                
        # 一次性写入所有剩余条目
        if remaining:
            logger.info(f"写入 {len(remaining)} 条剩余日志条目")
            try:
                self._write_to_file(remaining)
            except Exception as e:
                logger.error(f"写入剩余日志条目失败: {str(e)}")
                
    def get_stats(self) -> Dict[str, int]:
        """获取写入统计信息"""
        stats = self.stats.copy()
        stats["queue_size"] = self.queue.qsize()
        return stats
        
    def shutdown(self):
        """关闭异步写入器"""
        logger.info("关闭异步日志写入器")
        self.stop_event.set()
        
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
            
        # 确保所有日志都已写入
        self._drain_queue()
        
    def __del__(self):
        """析构函数"""
        self.shutdown()


class RealtimeLogger:
    """
    实时日志记录器
    
    提供高性能的实时日志记录功能，支持批量缓冲和定期刷新。
    """
    
    BUFFER_SIZE = 1000  # 内存缓冲1000条日志
    
    def __init__(self, log_dir: Union[str, Path] = None, 
                 file_prefix: str = "realtime",
                 buffer_size: int = None,
                 auto_flush_interval: float = 5.0):
        """
        初始化实时日志记录器
        
        Args:
            log_dir: 日志文件目录（默认使用跨平台日志目录）
            file_prefix: 日志文件前缀
            buffer_size: 内存缓冲大小
            auto_flush_interval: 自动刷新间隔（秒）
        """
        # 使用跨平台日志目录
        if log_dir is None:
            log_dir = get_log_directory() / "realtime" 
            
        # 设置缓冲区大小
        self.buffer_size = buffer_size or self.BUFFER_SIZE
        
        # 创建异步写入器
        self.writer = AsyncLogWriter(
            log_dir=log_dir,
            file_prefix=file_prefix
        )
        
        # 创建定时刷新线程
        self.flush_timer = None
        if auto_flush_interval > 0:
            self.flush_timer = threading.Timer(
                auto_flush_interval, 
                self._auto_flush
            )
            self.flush_timer.daemon = True
            self.flush_timer.start()
            
        # 线程锁，保护缓冲区
        self.buffer_lock = threading.RLock()
        
    def log(self, entry: Any):
        """
        记录日志条目
        
        Args:
            entry: 日志条目，可以是字典、字符串或其他可序列化对象
        """
        with self.buffer_lock:
            self.buffer.append(entry)
            
            # 如果缓冲区达到阈值，自动刷新
            if len(self.buffer) >= self.buffer_size:
                self.flush()
                
    def flush(self):
        """刷新缓冲区，将日志写入文件"""
        with self.buffer_lock:
            if not self.buffer:
                return
                
            # 发送到异步写入器
            self.writer.write_batch(self.buffer.copy())
            
            # 清空缓冲区
            self.buffer.clear()
            
    def _auto_flush(self):
        """定时自动刷新"""
        self.flush()
        
        # 重新设置定时器
        if self.auto_flush_interval > 0 and not getattr(self, '_shutting_down', False):
            self.flush_timer = threading.Timer(
                self.auto_flush_interval, 
                self._auto_flush
            )
            self.flush_timer.daemon = True
            self.flush_timer.start()
            
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = self.writer.get_stats()
        stats["buffer_size"] = len(self.buffer)
        return stats
        
    def shutdown(self):
        """关闭日志记录器"""
        # 标记正在关闭
        self._shutting_down = True
        
        # 取消定时器
        if self.flush_timer and self.flush_timer.is_alive():
            self.flush_timer.cancel()
            
        # 最后刷新
        self.flush()
        
        # 关闭写入器
        self.writer.shutdown()
        
    def __del__(self):
        """析构函数"""
        self.shutdown()


# 全局实时日志记录器
_realtime_logger = None

def get_realtime_logger() -> RealtimeLogger:
    """
    获取实时日志记录器单例
    
    返回全局共享的实时日志记录器实例，确保在整个应用中只有一个实例。
    
    Returns:
        RealtimeLogger: 实时日志记录器实例
    """
    global _realtime_logger
    if _realtime_logger is None:
        # 使用跨平台日志目录
        log_dir = get_log_directory() / "realtime"
        _realtime_logger = RealtimeLogger(log_dir=log_dir)
    return _realtime_logger


if __name__ == "__main__":
    # 测试代码
    import random
    
    # 创建实时日志记录器
    logger = RealtimeLogger(log_dir="logs/test_realtime")
    
    # 测试记录1000条日志
    for i in range(1000):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": random.choice(["INFO", "WARNING", "ERROR"]),
            "message": f"测试日志消息 {i}",
            "data": {
                "value": random.randint(1, 100),
                "name": f"test-{i}"
            }
        }
        logger.log(log_entry)
        
        # 随机延迟
        if random.random() < 0.1:
            time.sleep(0.01)
            
    # 确保所有日志都写入
    logger.flush()
    
    # 显示统计信息
    stats = logger.get_stats()
    print("日志统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    # 关闭日志记录器
    logger.shutdown()
    print("日志记录器已关闭") 