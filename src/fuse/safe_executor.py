"""
安全熔断执行器 (Safe Circuit Breaker Executor)
-----------------------------------------
用于在低资源环境中保护系统运行，防止内存溢出和资源耗尽。
支持自动释放资源、强制GC、进程熔断和统一的资源管理。

设计原则:
1. 低资源优先 - 在4GB内存环境下保障稳定运行
2. 安全熔断 - 危险操作前检查，超限时自动中断
3. 资源隔离 - 确保模型和视频处理的内存互不影响
"""

import os
import gc
import time
import signal
import threading
import traceback
import logging
import psutil
import torch
from typing import Callable, Dict, Any, Optional, Union, List

# 配置日志记录
logger = logging.getLogger("safe_executor")

class MemoryTracker:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存追踪器，监控系统和进程内存使用"""
    
    def __init__(self, critical_threshold_gb=3.5, warning_threshold_gb=3.0):
        """
        初始化内存追踪器
        
        Args:
            critical_threshold_gb: 临界阈值(GB)，超过此值触发紧急操作
            warning_threshold_gb: 警告阈值(GB)，超过此值发出警告
        """
        self.critical_threshold = critical_threshold_gb * 1024 * 1024 * 1024  # 转换为字节
        self.warning_threshold = warning_threshold_gb * 1024 * 1024 * 1024
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> Dict[str, Union[float, bool]]:
        """获取当前内存使用情况"""
        # 获取进程内存使用
        process_mem = self.process.memory_info().rss
        
        # 获取系统内存使用
        system_mem = psutil.virtual_memory()
        
        return {
            "process_gb": process_mem / (1024 * 1024 * 1024),
            "system_used_gb": system_mem.used / (1024 * 1024 * 1024),
            "system_available_gb": system_mem.available / (1024 * 1024 * 1024),
            "is_warning": process_mem > self.warning_threshold,
            "is_critical": process_mem > self.critical_threshold,
            "percent_used": system_mem.percent
        }
    
    def is_memory_critical(self) -> bool:
        """检查是否达到内存临界状态"""
        return self.get_memory_usage()["is_critical"]
    
    def is_memory_warning(self) -> bool:
        """检查是否达到内存警告状态"""
        return self.get_memory_usage()["is_warning"]


class FuseExecutor:
    """
    安全熔断执行器，负责安全地执行可能导致资源紧张的操作
    支持自动熔断、资源释放和操作审计
    """
    
    def __init__(self):
        """初始化执行器"""
        self.action_lock = threading.RLock()  # 可重入锁防止并发执行危险操作
        self.memory_tracker = MemoryTracker()
        self.registered_actions = {}
        self.registered_resources = {}
        self.last_gc_time = time.time()
        self.gc_interval = 60  # 60秒的GC间隔，避免过于频繁
        
    def register_action(self, action_name: str, handler: Callable):
        """注册可执行的操作"""
        self.registered_actions[action_name] = handler
        logger.info(f"注册操作: {action_name}")
    
    def register_resource(self, resource_id: str, resource: Any, release_func: Callable):
        """注册需要管理的资源及其释放函数"""
        self.registered_resources[resource_id] = {
            "resource": resource,
            "release_func": release_func,
            "last_used": time.time()
        }
        logger.info(f"注册资源: {resource_id}")
    
    def update_resource_usage(self, resource_id: str):
        """更新资源最后使用时间"""
        if resource_id in self.registered_resources:
            self.registered_resources[resource_id]["last_used"] = time.time()
    
    def release_resource(self, resource_id: str):
        """释放特定资源"""
        if resource_id in self.registered_resources:
            try:
                self.registered_resources[resource_id]["release_func"](
                    self.registered_resources[resource_id]["resource"]
                )
                logger.info(f"已释放资源: {resource_id}")
            except Exception as e:
                logger.error(f"释放资源 {resource_id} 错误: {str(e)}")
            
    def release_inactive_resources(self, max_idle_time: int = 300):
        """释放长时间未使用的资源"""
        current_time = time.time()
        for resource_id, data in list(self.registered_resources.items()):
            if current_time - data["last_used"] > max_idle_time:
                self.release_resource(resource_id)
                del self.registered_resources[resource_id]
                
    def execute_action(self, action: str, **kwargs):
        """
        带安全熔断的操作执行
        Args:
            action: 操作名称
            **kwargs: 传递给操作处理函数的参数
        """
        with self.action_lock:  # 防止并发执行危险操作
            # 操作前检查资源状态
            memory_status = self.memory_tracker.get_memory_usage()
            if memory_status["is_critical"]:
                # 内存紧张，采取紧急措施
                self._emergency_memory_release()
                
            # 定期GC
            current_time = time.time()
            if current_time - self.last_gc_time > self.gc_interval:
                self._perform_gc()
                self.last_gc_time = current_time
            
            # 清理闲置资源
            self.release_inactive_resources()
            
            # 执行预设操作
            if action == 'kill_process':
                # 找到并终止占用内存最大的进程（通常是当前程序自身的子进程）
                pid = self._find_largest_mem_process()
                if pid:
                    os.kill(pid, signal.SIGTERM)
                    logger.warning(f"已终止进程 {pid}")
                return
                
            elif action == 'force_gc':
                # 强制进行完整的垃圾回收
                self._perform_gc()
                return
                
            elif action == 'release_models':
                # 释放暂时不用的模型
                # 寻找并释放非活动模型资源
                for resource_id in list(self.registered_resources.keys()):
                    if "model_" in resource_id and resource_id != kwargs.get("keep", ""):
                        self.release_resource(resource_id)
                return
                
            # 执行注册的自定义操作
            elif action in self.registered_actions:
                try:
                    # 首先验证操作资源需求
                    if not self._validate_resource_requirements(action, **kwargs):
                        logger.error(f"操作 {action} 资源需求验证失败，中止执行")
                        return False
                    
                    # 执行操作
                    result = self.registered_actions[action](**kwargs)
                    
                    # 验证操作结果
                    if not self._validate_operation_result(action, result):
                        logger.warning(f"操作 {action} 结果验证失败")
                        return False
                    
                    return result
                except Exception as e:
                    logger.error(f"执行操作 {action} 错误: {str(e)}\n{traceback.format_exc()}")
                    return False
            else:
                logger.error(f"未知操作: {action}")
                return False
    
    def _perform_gc(self):
        """执行完整的垃圾回收"""
        logger.info("执行垃圾回收")
        gc.collect()
        # 如果有CUDA环境，清空CUDA缓存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def _emergency_memory_release(self):
        """紧急内存释放，在内存接近阈值时调用"""
        logger.warning("触发紧急内存释放")
        # 1. 强制GC
        self._perform_gc()
        
        # 2. 释放所有非必要资源
        for resource_id in list(self.registered_resources.keys()):
            # 可以配置某些资源为关键资源，不在紧急情况下释放
            if not resource_id.startswith("critical_"):
                self.release_resource(resource_id)
                del self.registered_resources[resource_id]
        
        # 3. 如果启用了CUDA，额外清理
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                torch.cuda.memory_summary(device=i)
    
    def _find_largest_mem_process(self):
        """找到占用内存最大的子进程"""
        # 获取当前进程ID
        current_pid = os.getpid()
        current_process = psutil.Process(current_pid)
        
        # 获取所有子进程
        children = current_process.children(recursive=True)
        
        # 如果有子进程，找出内存占用最大的
        if children:
            max_mem_process = max(children, key=lambda p: p.memory_info().rss)
            return max_mem_process.pid
        
        return None
    
    def _validate_resource_requirements(self, action: str, **kwargs) -> bool:
        """验证操作所需的资源是否满足要求"""
        # 1. 检查内存状态
        memory_status = self.memory_tracker.get_memory_usage()
        
        # 2. 根据操作类型检查特定需求
        # 例如：加载模型需要至少2GB可用内存
        if "load_model" in action and memory_status["system_available_gb"] < 2.0:
            logger.warning(f"内存不足，无法执行 {action}，可用: {memory_status['system_available_gb']:.2f}GB")
            return False
            
        # 3. 检查特定资源是否已注册
        required_resources = kwargs.get("required_resources", [])
        for resource in required_resources:
            if resource not in self.registered_resources:
                logger.warning(f"缺少所需资源: {resource}")
                return False
                
        return True
        
    def _validate_operation_result(self, action: str, result: Any) -> bool:
        """验证操作结果是否符合预期"""
        # 这里可以针对不同操作类型实现特定的结果验证逻辑
        if result is None and action not in ['force_gc', 'kill_process', 'release_models']:
            return False
            
        return True


# 单例模式
_executor_instance = None

def get_executor() -> FuseExecutor:
    """获取执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = FuseExecutor()
    return _executor_instance


# 提供简便的功能函数
def safe_execute(action: str, **kwargs):
    """安全执行指定操作"""
    return get_executor().execute_action(action, **kwargs)

def register_action(action_name: str, handler: Callable):
    """注册新操作"""
    get_executor().register_action(action_name, handler)

def register_resource(resource_id: str, resource: Any, release_func: Callable):
    """注册需要管理的资源"""
    get_executor().register_resource(resource_id, resource, release_func)

def release_resource(resource_id: str):
    """释放特定资源"""
    get_executor().release_resource(resource_id)

def force_gc():
    """强制进行垃圾回收"""
    get_executor().execute_action("force_gc")

def release_models(keep: Optional[str] = None):
    """释放模型资源，可选保留指定模型"""
    get_executor().execute_action("release_models", keep=keep) 