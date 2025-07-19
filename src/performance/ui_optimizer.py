#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI响应性优化器
实现异步处理、进度显示和取消功能
"""

import time
import asyncio
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressInfo:
    """进度信息"""
    current: int
    total: int
    percentage: float
    message: str
    estimated_time_remaining_ms: Optional[float] = None

@dataclass
class UITask:
    """UI任务"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    cancellable: bool = True
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    completion_callback: Optional[Callable[[Any], None]] = None
    error_callback: Optional[Callable[[Exception], None]] = None

class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks = {}
        self.task_queue = []
        self.task_results = {}
        self.task_lock = threading.RLock()
        self.executor = None
        self.running = False
        
    def start(self):
        """启动任务管理器"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("异步任务管理器已启动")
    
    def stop(self):
        """停止任务管理器"""
        self.running = False
        
        # 取消所有活动任务
        with self.task_lock:
            for task_id in list(self.active_tasks.keys()):
                self.cancel_task(task_id)
        
        logger.info("异步任务管理器已停止")
    
    def submit_task(self, task: UITask) -> str:
        """提交任务"""
        with self.task_lock:
            # 按优先级插入队列
            inserted = False
            for i, queued_task in enumerate(self.task_queue):
                if task.priority > queued_task.priority:
                    self.task_queue.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.task_queue.append(task)
            
            logger.info(f"任务已提交: {task.name} (ID: {task.id})")
            return task.id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.task_lock:
            # 从队列中移除
            for i, task in enumerate(self.task_queue):
                if task.id == task_id:
                    if task.cancellable:
                        del self.task_queue[i]
                        logger.info(f"任务已从队列中取消: {task_id}")
                        return True
                    else:
                        logger.warning(f"任务不可取消: {task_id}")
                        return False
            
            # 取消活动任务
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                if task_info['task'].cancellable:
                    task_info['cancelled'] = True
                    logger.info(f"活动任务已标记为取消: {task_id}")
                    return True
                else:
                    logger.warning(f"活动任务不可取消: {task_id}")
                    return False
        
        return False
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        with self.task_lock:
            # 检查队列中的任务
            for task in self.task_queue:
                if task.id == task_id:
                    return TaskStatus.PENDING
            
            # 检查活动任务
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                if task_info.get('cancelled'):
                    return TaskStatus.CANCELLED
                return TaskStatus.RUNNING
            
            # 检查已完成任务
            if task_id in self.task_results:
                result = self.task_results[task_id]
                if result.get('success'):
                    return TaskStatus.COMPLETED
                else:
                    return TaskStatus.FAILED
        
        return TaskStatus.PENDING
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        with self.task_lock:
            if task_id in self.task_results:
                return self.task_results[task_id].get('result')
        return None
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取活动任务列表"""
        with self.task_lock:
            active_list = []
            for task_id, task_info in self.active_tasks.items():
                active_list.append({
                    'id': task_id,
                    'name': task_info['task'].name,
                    'start_time': task_info['start_time'],
                    'progress': task_info.get('progress'),
                    'cancelled': task_info.get('cancelled', False)
                })
            return active_list
    
    def _worker_loop(self):
        """工作线程循环"""
        while self.running:
            try:
                # 检查是否有可执行的任务
                if len(self.active_tasks) < self.max_concurrent_tasks and self.task_queue:
                    with self.task_lock:
                        if self.task_queue:
                            task = self.task_queue.pop(0)
                            self._start_task(task)
                
                # 检查已完成的任务
                self._check_completed_tasks()
                
                time.sleep(0.1)  # 100ms检查间隔
                
            except Exception as e:
                logger.error(f"任务管理器工作循环错误: {e}")
                time.sleep(1)
    
    def _start_task(self, task: UITask):
        """启动任务"""
        task_info = {
            'task': task,
            'start_time': time.time(),
            'thread': None,
            'cancelled': False,
            'progress': None
        }
        
        def task_wrapper():
            try:
                # 创建进度更新函数
                def update_progress(current: int, total: int, message: str = ""):
                    if task_info.get('cancelled'):
                        raise InterruptedError("任务已被取消")
                    
                    progress = ProgressInfo(
                        current=current,
                        total=total,
                        percentage=current / total * 100 if total > 0 else 0,
                        message=message,
                        estimated_time_remaining_ms=self._estimate_remaining_time(
                            task_info['start_time'], current, total
                        )
                    )
                    
                    task_info['progress'] = progress
                    
                    if task.progress_callback:
                        task.progress_callback(progress)
                
                # 执行任务
                if 'progress_callback' in task.kwargs:
                    task.kwargs['progress_callback'] = update_progress
                
                result = task.func(*task.args, **task.kwargs)
                
                # 保存结果
                with self.task_lock:
                    self.task_results[task.id] = {
                        'success': True,
                        'result': result,
                        'completion_time': time.time()
                    }
                
                # 调用完成回调
                if task.completion_callback:
                    task.completion_callback(result)
                
                logger.info(f"任务完成: {task.name} (ID: {task.id})")
                
            except InterruptedError:
                logger.info(f"任务被取消: {task.name} (ID: {task.id})")
                with self.task_lock:
                    self.task_results[task.id] = {
                        'success': False,
                        'result': None,
                        'error': "任务被取消",
                        'completion_time': time.time()
                    }
            except Exception as e:
                logger.error(f"任务执行失败: {task.name} (ID: {task.id}) - {e}")
                
                with self.task_lock:
                    self.task_results[task.id] = {
                        'success': False,
                        'result': None,
                        'error': str(e),
                        'completion_time': time.time()
                    }
                
                # 调用错误回调
                if task.error_callback:
                    task.error_callback(e)
        
        # 启动任务线程
        task_thread = threading.Thread(target=task_wrapper, daemon=True)
        task_info['thread'] = task_thread
        
        self.active_tasks[task.id] = task_info
        task_thread.start()
        
        logger.info(f"任务已启动: {task.name} (ID: {task.id})")
    
    def _check_completed_tasks(self):
        """检查已完成的任务"""
        with self.task_lock:
            completed_tasks = []
            
            for task_id, task_info in self.active_tasks.items():
                thread = task_info['thread']
                if thread and not thread.is_alive():
                    completed_tasks.append(task_id)
            
            # 移除已完成的任务
            for task_id in completed_tasks:
                del self.active_tasks[task_id]
    
    def _estimate_remaining_time(self, start_time: float, current: int, total: int) -> Optional[float]:
        """估算剩余时间"""
        if current <= 0 or total <= 0:
            return None
        
        elapsed_time = time.time() - start_time
        if elapsed_time <= 0:
            return None
        
        progress_rate = current / elapsed_time
        remaining_items = total - current
        
        if progress_rate > 0:
            remaining_time_seconds = remaining_items / progress_rate
            return remaining_time_seconds * 1000  # 转换为毫秒
        
        return None

class UIOptimizer:
    """UI优化器"""
    
    def __init__(self):
        self.task_manager = AsyncTaskManager()
        self.response_time_targets = {
            'ui_update': 16,  # 60 FPS
            'user_interaction': 100,  # 100ms响应
            'data_loading': 500,  # 500ms数据加载
            'heavy_computation': 2000  # 2秒重计算
        }
        self.performance_monitor = {}
        
    def start(self):
        """启动UI优化器"""
        self.task_manager.start()
        logger.info("UI优化器已启动")
    
    def stop(self):
        """停止UI优化器"""
        self.task_manager.stop()
        logger.info("UI优化器已停止")
    
    def submit_background_task(self, task: UITask) -> str:
        """提交后台任务"""
        return self.task_manager.submit_task(task)
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        return self.task_manager.cancel_task(task_id)
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        return self.task_manager.get_task_status(task_id)
    
    def monitor_response_time(self, operation: str, target_ms: Optional[float] = None):
        """响应时间监控装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = (time.time() - start_time) * 1000
                    
                    # 记录性能数据
                    if operation not in self.performance_monitor:
                        self.performance_monitor[operation] = []
                    
                    self.performance_monitor[operation].append(execution_time)
                    
                    # 检查是否超过目标时间
                    target = target_ms or self.response_time_targets.get(operation, 1000)
                    if execution_time > target:
                        logger.warning(f"响应时间超标: {operation} {execution_time:.1f}ms > {target}ms")
            
            return wrapper
        return decorator
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {}
        
        for operation, times in self.performance_monitor.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times),
                    'target_ms': self.response_time_targets.get(operation, 1000)
                }
        
        # 添加任务管理器统计
        stats['task_manager'] = {
            'active_tasks': len(self.task_manager.active_tasks),
            'queued_tasks': len(self.task_manager.task_queue),
            'completed_tasks': len(self.task_manager.task_results)
        }
        
        return stats

# 全局UI优化器实例
_ui_optimizer = None

def get_ui_optimizer() -> UIOptimizer:
    """获取全局UI优化器实例"""
    global _ui_optimizer
    if _ui_optimizer is None:
        _ui_optimizer = UIOptimizer()
        _ui_optimizer.start()
    return _ui_optimizer
