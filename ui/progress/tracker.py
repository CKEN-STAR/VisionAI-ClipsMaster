"""
进度跟踪器
提供任务进度跟踪和显示功能
"""

import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

@dataclass
class ProgressInfo:
    """进度信息"""
    task_id: str
    current: int
    total: int
    message: str = ""
    start_time: float = 0.0
    estimated_time_left: float = 0.0
    
    @property
    def percentage(self) -> float:
        """获取百分比"""
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100.0)
    
    @property
    def is_complete(self) -> bool:
        """是否完成"""
        return self.current >= self.total

class ProgressTracker(QObject):
    """进度跟踪器"""
    
    progress_updated = pyqtSignal(str, int, int, str)  # task_id, current, total, message
    task_completed = pyqtSignal(str)                   # task_id
    task_started = pyqtSignal(str, str)                # task_id, message
    
    def __init__(self):
        super().__init__()
        self.active_tasks: Dict[str, ProgressInfo] = {}
        self.completed_tasks: Dict[str, ProgressInfo] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
    
    def start_task(self, task_id: str, total: int, message: str = "") -> bool:
        """
        开始任务
        
        Args:
            task_id: 任务ID
            total: 总步数
            message: 任务描述
            
        Returns:
            是否成功开始
        """
        try:
            if task_id in self.active_tasks:
                print(f"[WARN] 任务 {task_id} 已存在")
                return False
            
            progress_info = ProgressInfo(
                task_id=task_id,
                current=0,
                total=total,
                message=message,
                start_time=time.time()
            )
            
            self.active_tasks[task_id] = progress_info
            
            # 发送开始信号
            self.task_started.emit(task_id, message)
            
            print(f"[OK] 任务 {task_id} 已开始: {message}")
            return True
            
        except Exception as e:
            print(f"[WARN] 开始任务失败: {e}")
            return False
    
    def update_progress(self, task_id: str, current: int, message: str = "") -> bool:
        """
        更新进度
        
        Args:
            task_id: 任务ID
            current: 当前进度
            message: 进度消息
            
        Returns:
            是否成功更新
        """
        try:
            if task_id not in self.active_tasks:
                print(f"[WARN] 任务 {task_id} 不存在")
                return False
            
            progress_info = self.active_tasks[task_id]
            progress_info.current = current
            if message:
                progress_info.message = message
            
            # 计算预估剩余时间
            if current > 0:
                elapsed_time = time.time() - progress_info.start_time
                if progress_info.total > 0:
                    estimated_total_time = elapsed_time * progress_info.total / current
                    progress_info.estimated_time_left = max(0, estimated_total_time - elapsed_time)
            
            # 发送更新信号
            self.progress_updated.emit(task_id, current, progress_info.total, progress_info.message)
            
            # 调用回调函数
            self._call_callbacks(task_id, progress_info)
            
            # 检查是否完成
            if progress_info.is_complete:
                self.complete_task(task_id)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 更新进度失败: {e}")
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功完成
        """
        try:
            if task_id not in self.active_tasks:
                print(f"[WARN] 任务 {task_id} 不存在")
                return False
            
            progress_info = self.active_tasks[task_id]
            progress_info.current = progress_info.total
            progress_info.estimated_time_left = 0.0
            
            # 移动到完成列表
            self.completed_tasks[task_id] = progress_info
            del self.active_tasks[task_id]
            
            # 发送完成信号
            self.task_completed.emit(task_id)
            
            # 调用回调函数
            self._call_callbacks(task_id, progress_info)
            
            print(f"[OK] 任务 {task_id} 已完成")
            return True
            
        except Exception as e:
            print(f"[WARN] 完成任务失败: {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                print(f"[OK] 任务 {task_id} 已取消")
                return True
            return False
        except Exception as e:
            print(f"[WARN] 取消任务失败: {e}")
            return False
    
    def get_progress(self, task_id: str) -> Optional[ProgressInfo]:
        """获取任务进度"""
        return self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
    
    def get_all_active_tasks(self) -> Dict[str, ProgressInfo]:
        """获取所有活动任务"""
        return self.active_tasks.copy()
    
    def get_all_completed_tasks(self) -> Dict[str, ProgressInfo]:
        """获取所有完成任务"""
        return self.completed_tasks.copy()
    
    def add_callback(self, task_id: str, callback: Callable[[ProgressInfo], None]):
        """添加任务回调"""
        if task_id not in self.callbacks:
            self.callbacks[task_id] = []
        self.callbacks[task_id].append(callback)
    
    def add_global_callback(self, callback: Callable[[str, ProgressInfo], None]):
        """添加全局回调"""
        self.global_callbacks.append(callback)
    
    def _call_callbacks(self, task_id: str, progress_info: ProgressInfo):
        """调用回调函数"""
        try:
            # 调用任务特定回调
            if task_id in self.callbacks:
                for callback in self.callbacks[task_id]:
                    try:
                        callback(progress_info)
                    except Exception as e:
                        print(f"[WARN] 回调函数执行失败: {e}")
            
            # 调用全局回调
            for callback in self.global_callbacks:
                try:
                    callback(task_id, progress_info)
                except Exception as e:
                    print(f"[WARN] 全局回调函数执行失败: {e}")
                    
        except Exception as e:
            print(f"[WARN] 调用回调函数失败: {e}")
    
    def clear_completed_tasks(self):
        """清理已完成的任务"""
        try:
            cleared_count = len(self.completed_tasks)
            self.completed_tasks.clear()
            print(f"[OK] 已清理 {cleared_count} 个完成的任务")
        except Exception as e:
            print(f"[WARN] 清理完成任务失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            total_active = len(self.active_tasks)
            total_completed = len(self.completed_tasks)
            
            # 计算平均完成时间
            if self.completed_tasks:
                total_time = sum(
                    time.time() - task.start_time 
                    for task in self.completed_tasks.values()
                )
                avg_completion_time = total_time / len(self.completed_tasks)
            else:
                avg_completion_time = 0.0
            
            return {
                'active_tasks': total_active,
                'completed_tasks': total_completed,
                'total_tasks': total_active + total_completed,
                'average_completion_time': avg_completion_time,
                'callbacks_registered': len(self.callbacks),
                'global_callbacks': len(self.global_callbacks)
            }
            
        except Exception as e:
            print(f"[WARN] 获取统计信息失败: {e}")
            return {}

# 全局进度跟踪器实例
_progress_tracker: Optional[ProgressTracker] = None

def get_progress_tracker() -> ProgressTracker:
    """获取全局进度跟踪器"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker

def start_progress_task(task_id: str, total: int, message: str = "") -> bool:
    """开始进度任务"""
    tracker = get_progress_tracker()
    return tracker.start_task(task_id, total, message)

def update_progress_task(task_id: str, current: int, message: str = "") -> bool:
    """更新进度任务"""
    tracker = get_progress_tracker()
    return tracker.update_progress(task_id, current, message)

def complete_progress_task(task_id: str) -> bool:
    """完成进度任务"""
    tracker = get_progress_tracker()
    return tracker.complete_task(task_id)

def get_task_progress(task_id: str) -> Optional[ProgressInfo]:
    """获取任务进度"""
    tracker = get_progress_tracker()
    return tracker.get_progress(task_id)

__all__ = [
    'ProgressInfo',
    'ProgressTracker',
    'get_progress_tracker',
    'start_progress_task',
    'update_progress_task',
    'complete_progress_task',
    'get_task_progress'
]
