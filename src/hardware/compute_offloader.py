#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 计算任务卸载器

此模块提供计算任务卸载功能，优化CPU密集型任务的执行
"""

import os
import sys
import time
import logging
import platform
import threading
import multiprocessing
from typing import Dict, Any, List, Callable, Optional, Union, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "enable_offloading": True,
    "max_threads": max(2, multiprocessing.cpu_count() - 1),
    "priority_levels": {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4
    },
    "thread_allocation": {
        "ui": 1,
        "processing": 0.6,  # 占用剩余线程的百分比
        "background": 0.4   # 占用剩余线程的百分比
    }
}

class ComputeOffloader:
    """计算任务卸载器
    
    优化CPU密集型任务的执行，根据系统资源动态调整计算任务的执行方式
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化计算任务卸载器
        
        Args:
            config: 配置字典，可选
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        self.cpu_count = multiprocessing.cpu_count()
        self.thread_pool = {}
        self.task_queue = []
        self.lock = threading.Lock()
        self.initialized = False
        
        # 初始化线程池
        self._init_thread_pool()
        
        logger.info(f"计算任务卸载器已初始化 (CPU核心数: {self.cpu_count})")
        self.initialized = True
    
    def _init_thread_pool(self):
        """初始化线程池"""
        max_threads = self.config["max_threads"]
        
        # 预留UI线程
        ui_threads = self.config["thread_allocation"]["ui"]
        remaining_threads = max(1, max_threads - ui_threads)
        
        # 分配处理线程和后台线程
        processing_threads = max(1, int(remaining_threads * self.config["thread_allocation"]["processing"]))
        background_threads = max(1, remaining_threads - processing_threads)
        
        self.thread_pool = {
            "ui": ui_threads,
            "processing": processing_threads,
            "background": background_threads
        }
        
        logger.debug(f"线程池初始化完成: UI={ui_threads}, 处理={processing_threads}, 后台={background_threads}")
    
    def offload(self, func: Callable, args: Tuple = None, kwargs: Dict = None, 
                priority: str = "medium", task_type: str = "processing") -> threading.Thread:
        """卸载计算任务到后台线程
        
        Args:
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            priority: 优先级 ("high", "medium", "low")
            task_type: 任务类型 ("processing", "background")
            
        Returns:
            启动的线程对象
        """
        if not self.initialized:
            logger.warning("计算任务卸载器未初始化，任务将在主线程执行")
            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}
            func(*args, **kwargs)
            return None
        
        if not self.config["enable_offloading"]:
            logger.debug("任务卸载已禁用，任务将在主线程执行")
            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}
            func(*args, **kwargs)
            return None
        
        # 创建线程执行任务
        args = args or ()
        kwargs = kwargs or {}
        
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        
        with self.lock:
            self.task_queue.append({
                "thread": thread,
                "priority": self.config["priority_levels"].get(priority, 0.5),
                "task_type": task_type,
                "start_time": time.time()
            })
        
        logger.debug(f"已卸载计算任务 (优先级: {priority}, 类型: {task_type})")
        return thread
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态
        
        Returns:
            状态信息字典
        """
        with self.lock:
            active_tasks = len([t for t in self.task_queue if t["thread"].is_alive()])
            
        return {
            "enabled": self.config["enable_offloading"],
            "cpu_count": self.cpu_count,
            "thread_allocation": self.thread_pool,
            "active_tasks": active_tasks
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config: 新配置字典
        """
        with self.lock:
            self.config.update(config)
            self._init_thread_pool()
        
        logger.info("计算任务卸载器配置已更新")

# 全局实例
_offloader = None

def get_compute_offloader() -> ComputeOffloader:
    """获取计算任务卸载器的全局实例
    
    Returns:
        ComputeOffloader: 计算任务卸载器实例
    """
    global _offloader
    if _offloader is None:
        try:
            _offloader = ComputeOffloader()
        except Exception as e:
            logger.error(f"创建计算任务卸载器失败: {str(e)}")
            _offloader = None
    
    return _offloader

# 便捷函数
def offload_task(func, *args, **kwargs):
    """便捷函数，卸载任务到后台执行"""
    offloader = get_compute_offloader()
    if offloader:
        return offloader.offload(func, args, kwargs)
    else:
        # 如果卸载器不可用，直接执行
        return func(*args, **kwargs)

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(" VisionAI-ClipsMaster 计算任务卸载器测试 ")
    print("-" * 50)
    
    offloader = get_compute_offloader()
    print(f"CPU核心数: {offloader.cpu_count}")
    print(f"线程分配: {offloader.thread_pool}")
    
    # 测试任务
    def test_task(name, sleep_time):
        print(f"任务 {name} 开始执行")
        import time
        time.sleep(sleep_time)
        print(f"任务 {name} 执行完成")
        return f"任务 {name} 结果"
    
    # 卸载几个测试任务
    offloader.offload(test_task, args=("高优先级", 2), priority="high")
    offloader.offload(test_task, args=("中优先级", 3), priority="medium")
    offloader.offload(test_task, args=("低优先级", 1), priority="low")
    
    # 等待所有任务完成
    import time
    time.sleep(4)
    
    print("\n计算任务卸载器测试完成。") 