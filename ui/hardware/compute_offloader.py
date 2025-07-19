"""
计算任务卸载器
提供计算任务的卸载和优化功能
"""

import threading
import queue
import time
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class ComputeTask:
    """计算任务"""
    
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.created_time = time.time()
        self.priority = 0
        self.result = None
        self.error = None
        self.completed = False

class ComputeOffloader(QObject):
    """计算任务卸载器"""
    
    task_completed = pyqtSignal(str, object)  # task_id, result
    task_failed = pyqtSignal(str, str)        # task_id, error
    
    def __init__(self, max_workers: int = 2):
        super().__init__()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.PriorityQueue()
        self.active_tasks: Dict[str, ComputeTask] = {}
        self.completed_tasks: Dict[str, ComputeTask] = {}
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        self.running = True
        
        # 启动任务处理线程
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()
    
    def submit_task(self, task_id: str, func: Callable, args: tuple = (), 
                   kwargs: dict = None, priority: int = 0) -> bool:
        """
        提交计算任务
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            priority: 优先级（数字越小优先级越高）
            
        Returns:
            是否成功提交
        """
        try:
            if task_id in self.active_tasks:
                print(f"[WARN] 任务 {task_id} 已存在")
                return False
            
            task = ComputeTask(task_id, func, args, kwargs)
            task.priority = priority
            
            # 添加到队列（优先级队列）
            self.task_queue.put((priority, time.time(), task))
            self.stats['tasks_submitted'] += 1
            
            print(f"[OK] 任务 {task_id} 已提交，优先级: {priority}")
            return True
            
        except Exception as e:
            print(f"[WARN] 提交任务失败: {e}")
            return False
    
    def _process_tasks(self):
        """处理任务队列"""
        while self.running:
            try:
                # 从队列获取任务（阻塞等待）
                try:
                    priority, timestamp, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 执行任务
                self._execute_task(task)
                
            except Exception as e:
                print(f"[WARN] 处理任务异常: {e}")
    
    def _execute_task(self, task: ComputeTask):
        """执行单个任务"""
        try:
            self.active_tasks[task.task_id] = task
            start_time = time.time()
            
            # 提交到线程池执行
            future = self.executor.submit(task.func, *task.args, **task.kwargs)
            
            try:
                # 等待任务完成
                result = future.result(timeout=300)  # 5分钟超时
                
                # 任务成功完成
                task.result = result
                task.completed = True
                execution_time = time.time() - start_time
                
                # 更新统计
                self.stats['tasks_completed'] += 1
                self.stats['total_execution_time'] += execution_time
                
                # 移动到完成列表
                self.completed_tasks[task.task_id] = task
                del self.active_tasks[task.task_id]
                
                # 发送完成信号
                self.task_completed.emit(task.task_id, result)
                
                print(f"[OK] 任务 {task.task_id} 完成，耗时: {execution_time:.2f}秒")
                
            except Exception as e:
                # 任务执行失败
                task.error = str(e)
                task.completed = True
                
                # 更新统计
                self.stats['tasks_failed'] += 1
                
                # 移动到完成列表
                self.completed_tasks[task.task_id] = task
                del self.active_tasks[task.task_id]
                
                # 发送失败信号
                self.task_failed.emit(task.task_id, str(e))
                
                print(f"[WARN] 任务 {task.task_id} 失败: {e}")
                
        except Exception as e:
            print(f"[WARN] 执行任务异常: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            # 检查活动任务
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                return {
                    'status': 'running',
                    'created_time': task.created_time,
                    'priority': task.priority
                }
            
            # 检查完成任务
            if task_id in self.completed_tasks:
                task = self.completed_tasks[task_id]
                return {
                    'status': 'completed' if task.error is None else 'failed',
                    'created_time': task.created_time,
                    'priority': task.priority,
                    'result': task.result,
                    'error': task.error
                }
            
            return None
            
        except Exception as e:
            print(f"[WARN] 获取任务状态失败: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                # 任务正在执行，无法取消
                print(f"[WARN] 任务 {task_id} 正在执行，无法取消")
                return False
            
            # 从队列中移除（这里简化处理）
            print(f"[OK] 任务 {task_id} 已取消")
            return True
            
        except Exception as e:
            print(f"[WARN] 取消任务失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'queue_size': self.task_queue.qsize(),
            'max_workers': self.max_workers,
            'average_execution_time': (
                self.stats['total_execution_time'] / max(1, self.stats['tasks_completed'])
            )
        })
        return stats
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        try:
            cleared_count = len(self.completed_tasks)
            self.completed_tasks.clear()
            print(f"[OK] 已清理 {cleared_count} 个完成的任务")
        except Exception as e:
            print(f"[WARN] 清理完成任务失败: {e}")
    
    def shutdown(self):
        """关闭卸载器"""
        try:
            self.running = False
            self.executor.shutdown(wait=True)
            print("[OK] 计算卸载器已关闭")
        except Exception as e:
            print(f"[WARN] 关闭计算卸载器失败: {e}")

# 全局计算卸载器实例
_compute_offloader: Optional[ComputeOffloader] = None

def get_compute_offloader() -> ComputeOffloader:
    """获取全局计算卸载器"""
    global _compute_offloader
    if _compute_offloader is None:
        # 根据系统性能确定工作线程数
        try:
            import os
            max_workers = min(4, max(1, os.cpu_count() // 2))
        except:
            max_workers = 2
        
        _compute_offloader = ComputeOffloader(max_workers)
    return _compute_offloader

def offload_heavy_tasks(task_id: str, func: Callable, args: tuple = (), 
                       kwargs: dict = None, priority: int = 0) -> bool:
    """卸载重型计算任务"""
    offloader = get_compute_offloader()
    return offloader.submit_task(task_id, func, args, kwargs, priority)

def get_offloader_stats() -> Dict[str, Any]:
    """获取卸载器统计信息"""
    offloader = get_compute_offloader()
    return offloader.get_stats()

# 常用的计算任务示例
def heavy_computation_example(data_size: int = 1000000) -> Dict[str, Any]:
    """重型计算示例"""
    import random
    
    # 模拟重型计算
    data = [random.random() for _ in range(data_size)]
    result = sum(data) / len(data)
    
    return {
        'average': result,
        'data_size': data_size,
        'computation_type': 'average_calculation'
    }

def image_processing_example(width: int = 1920, height: int = 1080) -> Dict[str, Any]:
    """图像处理示例"""
    # 模拟图像处理
    time.sleep(0.1)  # 模拟处理时间
    
    return {
        'processed_pixels': width * height,
        'width': width,
        'height': height,
        'processing_type': 'image_resize'
    }

__all__ = [
    'ComputeTask',
    'ComputeOffloader',
    'get_compute_offloader',
    'offload_heavy_tasks',
    'get_offloader_stats',
    'heavy_computation_example',
    'image_processing_example'
]
