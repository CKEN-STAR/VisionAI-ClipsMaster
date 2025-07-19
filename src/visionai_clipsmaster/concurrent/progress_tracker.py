#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 进度跟踪器模块

提供实时进度监控和跟踪功能，支持：
1. 任务进度实时更新
2. 进度历史记录
3. 进度可视化数据
4. 内存优化存储
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

class ProgressStatus(Enum):
    """进度状态"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

@dataclass
class ProgressUpdate:
    """进度更新数据"""
    task_id: str
    current_step: int
    total_steps: int
    percentage: float
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    status: ProgressStatus = ProgressStatus.IN_PROGRESS
    
    def __post_init__(self):
        if self.total_steps > 0:
            self.percentage = (self.current_step / self.total_steps) * 100
        else:
            self.percentage = 0.0

@dataclass
class TaskProgress:
    """任务进度信息"""
    task_id: str
    task_name: str
    status: ProgressStatus
    current_step: int = 0
    total_steps: int = 0
    percentage: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    last_update: Optional[float] = None
    message: str = ""
    error_message: str = ""
    
    def get_elapsed_time(self) -> float:
        """获取已用时间"""
        if self.start_time is None:
            return 0.0
        end_time = self.end_time or time.time()
        return end_time - self.start_time
        
    def get_estimated_remaining_time(self) -> Optional[float]:
        """估算剩余时间"""
        if self.percentage <= 0 or self.start_time is None:
            return None
            
        elapsed = self.get_elapsed_time()
        if elapsed <= 0:
            return None
            
        # 基于当前进度估算剩余时间
        remaining_percentage = 100 - self.percentage
        time_per_percentage = elapsed / self.percentage
        return remaining_percentage * time_per_percentage

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, 
                 update_interval: float = 1.0,
                 enable_real_time: bool = True,
                 enable_persistence: bool = True,
                 max_history: int = 1000):
        """初始化进度跟踪器
        
        Args:
            update_interval: 更新间隔（秒）
            enable_real_time: 是否启用实时更新
            enable_persistence: 是否启用持久化
            max_history: 最大历史记录数
        """
        self.update_interval = update_interval
        self.enable_real_time = enable_real_time
        self.enable_persistence = enable_persistence
        self.max_history = max_history
        
        # 任务进度存储
        self.tasks: Dict[str, TaskProgress] = {}
        
        # 进度历史记录（使用deque限制内存使用）
        self.progress_history: Dict[str, deque] = {}
        
        # 回调函数
        self.update_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        # 控制标志
        self.is_running = True
        self.monitor_thread = None
        self.lock = threading.RLock()
        
        # 启动实时监控
        if enable_real_time:
            self.start_monitoring()
            
        logger.info("进度跟踪器初始化完成")
        
    def create_task(self, task_id: str, task_name: str, total_steps: int = 100) -> TaskProgress:
        """创建新任务
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            total_steps: 总步数
            
        Returns:
            TaskProgress: 任务进度对象
        """
        with self.lock:
            task_progress = TaskProgress(
                task_id=task_id,
                task_name=task_name,
                status=ProgressStatus.NOT_STARTED,
                total_steps=total_steps,
                start_time=time.time()
            )
            
            self.tasks[task_id] = task_progress
            self.progress_history[task_id] = deque(maxlen=self.max_history)
            
            logger.debug(f"创建任务: {task_id} - {task_name}")
            return task_progress
            
    def start_task(self, task_id: str) -> bool:
        """开始任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功开始
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
            task = self.tasks[task_id]
            task.status = ProgressStatus.IN_PROGRESS
            task.start_time = time.time()
            task.last_update = time.time()
            
            logger.debug(f"开始任务: {task_id}")
            self._trigger_update_callbacks(task)
            return True
            
    def update_progress(self, task_id: str, current_step: int, message: str = "") -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            current_step: 当前步数
            message: 进度消息
            
        Returns:
            bool: 是否成功更新
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
            task = self.tasks[task_id]
            task.current_step = current_step
            task.message = message
            task.last_update = time.time()
            
            # 计算百分比
            if task.total_steps > 0:
                task.percentage = (current_step / task.total_steps) * 100
            else:
                task.percentage = 0.0
                
            # 添加到历史记录
            progress_update = ProgressUpdate(
                task_id=task_id,
                current_step=current_step,
                total_steps=task.total_steps,
                percentage=task.percentage,
                message=message,
                status=task.status
            )
            
            self.progress_history[task_id].append(progress_update)
            
            logger.debug(f"更新进度: {task_id} - {task.percentage:.1f}%")
            self._trigger_update_callbacks(task)
            
            # 检查是否完成
            if current_step >= task.total_steps:
                self.complete_task(task_id)
                
            return True
            
    def complete_task(self, task_id: str, message: str = "") -> bool:
        """完成任务
        
        Args:
            task_id: 任务ID
            message: 完成消息
            
        Returns:
            bool: 是否成功完成
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
            task = self.tasks[task_id]
            task.status = ProgressStatus.COMPLETED
            task.percentage = 100.0
            task.end_time = time.time()
            task.message = message or "任务完成"
            
            logger.info(f"任务完成: {task_id}")
            self._trigger_completion_callbacks(task)
            return True
            
    def fail_task(self, task_id: str, error_message: str = "") -> bool:
        """任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
            
        Returns:
            bool: 是否成功标记失败
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
            task = self.tasks[task_id]
            task.status = ProgressStatus.FAILED
            task.end_time = time.time()
            task.error_message = error_message
            task.message = "任务失败"
            
            logger.error(f"任务失败: {task_id} - {error_message}")
            self._trigger_completion_callbacks(task)
            return True
            
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        with self.lock:
            if task_id not in self.tasks:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
            task = self.tasks[task_id]
            task.status = ProgressStatus.CANCELLED
            task.end_time = time.time()
            task.message = "任务已取消"
            
            logger.info(f"任务已取消: {task_id}")
            self._trigger_completion_callbacks(task)
            return True
            
    def get_task_progress(self, task_id: str) -> Optional[TaskProgress]:
        """获取任务进度
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskProgress]: 任务进度对象
        """
        with self.lock:
            return self.tasks.get(task_id)
            
    def get_all_tasks(self) -> Dict[str, TaskProgress]:
        """获取所有任务进度"""
        with self.lock:
            return self.tasks.copy()
            
    def get_task_history(self, task_id: str) -> List[ProgressUpdate]:
        """获取任务历史记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[ProgressUpdate]: 进度更新历史
        """
        with self.lock:
            if task_id not in self.progress_history:
                return []
            return list(self.progress_history[task_id])
            
    def add_update_callback(self, callback: Callable[[TaskProgress], None]):
        """添加进度更新回调"""
        self.update_callbacks.append(callback)
        
    def add_completion_callback(self, callback: Callable[[TaskProgress], None]):
        """添加任务完成回调"""
        self.completion_callbacks.append(callback)
        
    def _trigger_update_callbacks(self, task: TaskProgress):
        """触发更新回调"""
        for callback in self.update_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"进度更新回调执行失败: {e}")
                
    def _trigger_completion_callbacks(self, task: TaskProgress):
        """触发完成回调"""
        for callback in self.completion_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"任务完成回调执行失败: {e}")
                
    def start_monitoring(self):
        """启动监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
            
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.debug("进度监控已启动")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                # 这里可以添加定期的监控逻辑
                # 例如：检查超时任务、清理历史记录等
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"进度监控异常: {e}")
                time.sleep(5)
                
    def shutdown(self):
        """关闭进度跟踪器"""
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        logger.info("进度跟踪器已关闭")
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total_tasks = len(self.tasks)
            completed_tasks = len([t for t in self.tasks.values() if t.status == ProgressStatus.COMPLETED])
            failed_tasks = len([t for t in self.tasks.values() if t.status == ProgressStatus.FAILED])
            in_progress_tasks = len([t for t in self.tasks.values() if t.status == ProgressStatus.IN_PROGRESS])
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "is_running": self.is_running
            }
