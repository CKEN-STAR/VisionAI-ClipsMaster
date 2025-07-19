#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存探针模块 - 用于在关键代码点注入内存监控

此模块提供自动化内存探针，可以植入到代码的关键位置以监控内存使用情况。
探针设计为轻量级，对性能影响最小化，同时能够在内存超出阈值时触发警报。
"""

import os
import sys
import time
import gc
import inspect
import threading
import logging
import functools
import traceback
from typing import Dict, Any, Callable, Optional, List, Set, Tuple
import psutil

# 导入异常类
from src.utils.exceptions import MemoryOverflowError, MemoryError, ClipMasterError

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryProbes")

# 全局内存探针管理器
_PROBE_MANAGER = None

# 内存探针配置
PROBE_CONFIG = {
    "threshold_warning": 0.75,      # 警告阈值，系统内存使用率
    "threshold_critical": 0.90,      # 危险阈值，系统内存使用率
    "check_interval": 0.5,          # 探针检查间隔（秒）
    "gc_threshold": 0.85,           # 触发垃圾回收的内存阈值
    "enable_backtrace": True,       # 是否启用堆栈跟踪
    "log_level": "INFO",            # 日志级别
    "auto_inject": True,            # 是否自动注入探针
    "injection_points": [           # 默认注入点配置
        {
            "module": "src.core.model_loader", 
            "function": "load_model",
            "level": "critical"
        },
        {
            "module": "src.memory.compressed_allocator", 
            "function": "allocate",
            "level": "high"
        },
        {
            "module": "src.core.shard_policy_manager", 
            "function": "load_shard",
            "level": "high"
        },
        {
            "module": "src.utils.file_handler", 
            "function": "read_large_file",
            "level": "medium"
        }
    ]
}

class MemoryProbe:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存探针类 - 用于在特定代码点监控内存使用情况"""
    
    def __init__(self, 
                name: str, 
                level: str = "medium",
                threshold_override: Optional[float] = None,
                callback: Optional[Callable] = None):
        """
        初始化内存探针
        
        Args:
            name: 探针名称，通常为被监控的函数名
            level: 探针级别，可选 "low", "medium", "high", "critical"
            threshold_override: 覆盖默认阈值的特定阈值
            callback: 超过阈值时的回调函数
        """
        self.name = name
        self.level = level
        self.threshold_override = threshold_override
        self.callback = callback
        self.creation_time = time.time()
        self.last_check_time = 0
        self.last_memory_usage = 0
        self.check_count = 0
        
        # 根据级别设置检查频率
        level_factors = {
            "low": 2.0,
            "medium": 1.0,
            "high": 0.5,
            "critical": 0.25
        }
        self.check_factor = level_factors.get(level, 1.0)
        
        # 获取当前调用栈信息
        self.creation_stack = traceback.extract_stack() if PROBE_CONFIG["enable_backtrace"] else None
        
        logger.debug(f"创建内存探针: {name} (级别: {level})")
        
    def check(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检查内存使用情况
        
        Args:
            context: 可选的上下文信息
            
        Returns:
            包含内存使用情况的字典
        """
        now = time.time()
        
        # 根据探针级别和配置的间隔判断是否需要检查
        interval = PROBE_CONFIG["check_interval"] * self.check_factor
        if self.last_check_time > 0 and (now - self.last_check_time) < interval:
            return {"skipped": True}
            
        self.last_check_time = now
        self.check_count += 1
        
        # 获取当前内存使用情况
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100.0
        memory_available_mb = memory.available / (1024 * 1024)
        
        # 记录数据
        result = {
            "probe_name": self.name,
            "memory_usage": memory_usage,
            "memory_available_mb": memory_available_mb,
            "timestamp": now,
            "check_count": self.check_count,
            "threshold_warning": PROBE_CONFIG["threshold_warning"],
            "threshold_critical": PROBE_CONFIG["threshold_critical"],
            "level": self.level,
            "context": context or {}
        }
        
        # 获取特定阈值或使用全局阈值
        warning_threshold = self.threshold_override or PROBE_CONFIG["threshold_warning"]
        critical_threshold = self.threshold_override * 1.2 if self.threshold_override else PROBE_CONFIG["threshold_critical"]
        
        # 检查是否超过阈值
        if memory_usage >= critical_threshold:
            self._handle_critical(result)
        elif memory_usage >= warning_threshold:
            self._handle_warning(result)
        elif memory_usage >= PROBE_CONFIG["gc_threshold"]:
            # 主动触发垃圾回收以防止达到警告阈值
            gc.collect()
            
        # 更新内存使用记录
        self.last_memory_usage = memory_usage
        
        return result
        
    def _handle_warning(self, data: Dict[str, Any]) -> None:
        """处理警告级别的内存使用"""
        context_str = ""
        if data.get("context"):
            context_str = f" (上下文: {data['context']})"
            
        logger.warning(f"内存警告: 探针 {self.name} 检测到内存使用率 {data['memory_usage']*100:.1f}%{context_str}")
        
        # 调用自定义回调
        if self.callback:
            try:
                self.callback(data)
            except Exception as e:
                logger.error(f"内存探针回调错误: {str(e)}")
                
    def _handle_critical(self, data: Dict[str, Any]) -> None:
        """处理危险级别的内存使用"""
        context_str = ""
        if data.get("context"):
            context_str = f" (上下文: {data['context']})"
            
        # 获取堆栈信息
        current_stack = traceback.extract_stack() if PROBE_CONFIG["enable_backtrace"] else None
        stack_trace = "".join(traceback.format_list(current_stack)) if current_stack else "不可用"
            
        logger.error(f"内存危险: 探针 {self.name} 检测到内存使用率 {data['memory_usage']*100:.1f}%{context_str}")
        logger.error(f"堆栈跟踪: \n{stack_trace}")
        
        # 尝试释放内存
        gc.collect()
        
        # 调用自定义回调
        if self.callback:
            try:
                self.callback(data)
            except Exception as e:
                logger.error(f"内存探针回调错误: {str(e)}")

class MemoryProbeManager:
    """内存探针管理器 - 管理所有的探针并提供自动注入功能"""
    
    def __init__(self):
        """初始化内存探针管理器"""
        self.probes: Dict[str, MemoryProbe] = {}
        self.active_decorators: Set[str] = set()
        self.monitor_thread = None
        self.stop_monitor = threading.Event()
        self.lock = threading.Lock()
        
        # 设置日志级别
        log_level = getattr(logging, PROBE_CONFIG.get("log_level", "INFO"))
        logger.setLevel(log_level)
        
        # 自动注入标志
        self.auto_inject_done = False
        
        logger.info("内存探针管理器初始化完成")
        
    def register_probe(self, 
                     name: str, 
                     level: str = "medium",
                     threshold_override: Optional[float] = None,
                     callback: Optional[Callable] = None) -> MemoryProbe:
        """
        注册新的内存探针
        
        Args:
            name: 探针名称
            level: 探针级别
            threshold_override: 覆盖默认阈值的特定阈值
            callback: 超过阈值时的回调函数
            
        Returns:
            创建的内存探针对象
        """
        with self.lock:
            if name in self.probes:
                return self.probes[name]
                
            probe = MemoryProbe(name, level, threshold_override, callback)
            self.probes[name] = probe
            return probe
            
    def get_probe(self, name: str) -> Optional[MemoryProbe]:
        """
        获取已注册的探针
        
        Args:
            name: 探针名称
            
        Returns:
            内存探针对象，如果不存在则返回None
        """
        return self.probes.get(name)
        
    def check_probe(self, name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        检查指定探针的内存使用情况
        
        Args:
            name: 探针名称
            context: 上下文信息
            
        Returns:
            内存检查结果
        """
        probe = self.get_probe(name)
        if not probe:
            probe = self.register_probe(name)
            
        return probe.check(context)
        
    def memory_probe_decorator(self, level: str = "medium"):
        """
        装饰器: 为函数添加内存探针
        
        Args:
            level: 探针级别
            
        Returns:
            装饰器函数
        """
        def decorator(func):
            # 构建唯一的探针名称
            module_name = func.__module__
            func_name = func.__name__
            probe_name = f"{module_name}.{func_name}"
            
            # 记录装饰器使用
            self.active_decorators.add(probe_name)
            
            # 注册探针
            probe = self.register_probe(probe_name, level)
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 调用前检查
                context = {
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "phase": "entry"
                }
                entry_result = probe.check(context)
                
                # 检查是否超过危险阈值
                if entry_result.get("memory_usage", 0) >= PROBE_CONFIG["threshold_critical"]:
                    # 确定函数名和位置
                    func_info = f"{func.__module__}.{func.__name__}"
                    caller_frame = inspect.currentframe().f_back
                    caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
                    
                    # 抛出内存异常
                    raise MemoryOverflowError(
                        f"内存不足，无法执行 {func_info} (调用位置: {caller_info})"
                    )
                
                # 执行原函数
                try:
                    result = func(*args, **kwargs)
                    
                    # 调用后检查
                    context["phase"] = "exit"
                    probe.check(context)
                    
                    return result
                    
                except Exception as e:
                    # 如果是内存相关异常，添加更多上下文信息
                    if isinstance(e, (MemoryError, MemoryOverflowError)):
                        context["phase"] = "error"
                        context["error"] = str(e)
                        probe.check(context)
                    raise
                    
            return wrapper
        return decorator
    
    def start_monitoring(self):
        """启动后台监控线程，定期检查所有探针"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
            
        self.stop_monitor.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitoring_task,
            daemon=True,
            name="MemoryProbeMonitor"
        )
        self.monitor_thread.start()
        logger.info("内存探针监控线程已启动")
        
    def stop_monitoring(self):
        """停止监控线程"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitor.set()
            self.monitor_thread.join(timeout=2.0)
            logger.info("内存探针监控线程已停止")
            
    def _monitoring_task(self):
        """监控线程主任务"""
        while not self.stop_monitor.is_set():
            try:
                # 取得系统内存用量
                memory = psutil.virtual_memory()
                memory_usage = memory.percent / 100.0
                
                # 如果内存使用超过警告阈值，检查所有探针
                if memory_usage >= PROBE_CONFIG["threshold_warning"]:
                    logger.warning(f"系统内存使用率: {memory_usage*100:.1f}%, 检查所有探针")
                    self._check_all_probes()
                
                # 休眠
                time.sleep(PROBE_CONFIG["check_interval"])
                
            except Exception as e:
                logger.error(f"内存探针监控线程异常: {str(e)}")
                time.sleep(5.0)  # 出错后休眠时间更长
    
    def _check_all_probes(self):
        """检查所有注册的探针"""
        for name, probe in list(self.probes.items()):
            try:
                probe.check({"source": "monitor_thread"})
            except Exception as e:
                logger.error(f"检查探针 {name} 时发生错误: {str(e)}")
                
    def inject_probes(self):
        """自动注入探针到配置的代码点"""
        if self.auto_inject_done:
            return
            
        try:
            injection_count = 0
            
            # 根据配置注入探针
            for injection_point in PROBE_CONFIG["injection_points"]:
                module_name = injection_point.get("module")
                function_name = injection_point.get("function")
                level = injection_point.get("level", "medium")
                
                if not module_name or not function_name:
                    continue
                    
                try:
                    # 动态导入模块
                    module = __import__(module_name, fromlist=[""])
                    
                    # 获取原始函数
                    original_func = getattr(module, function_name, None)
                    if not original_func or not callable(original_func):
                        logger.warning(f"无法注入探针: {module_name}.{function_name} 不存在或不可调用")
                        continue
                        
                    # 注册探针
                    probe_name = f"{module_name}.{function_name}"
                    probe = self.register_probe(probe_name, level)
                    
                    # 创建装饰后的函数
                    @functools.wraps(original_func)
                    def wrapped_func(*args, **kwargs):
                        # 调用前检查
                        context = {
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys()),
                            "phase": "entry"
                        }
                        entry_result = probe.check(context)
                        
                        # 检查是否超过危险阈值
                        if entry_result.get("memory_usage", 0) >= PROBE_CONFIG["threshold_critical"]:
                            # 如果是关键函数，可能需要阻止执行
                            if level == "critical":
                                func_info = f"{module_name}.{function_name}"
                                raise MemoryOverflowError(
                                    f"内存不足，无法执行关键函数 {func_info}"
                                )
                        
                        # 执行原函数
                        try:
                            result = original_func(*args, **kwargs)
                            
                            # 调用后检查
                            context["phase"] = "exit"
                            probe.check(context)
                            
                            return result
                            
                        except Exception as e:
                            # 如果是内存相关异常，添加更多上下文信息
                            if isinstance(e, (MemoryError, MemoryOverflowError)):
                                context["phase"] = "error"
                                context["error"] = str(e)
                                probe.check(context)
                            raise
                    
                    # 替换原始函数
                    setattr(module, function_name, wrapped_func)
                    injection_count += 1
                    logger.info(f"已注入内存探针: {module_name}.{function_name} (级别: {level})")
                    
                except ImportError:
                    logger.warning(f"无法导入模块以注入探针: {module_name}")
                except Exception as e:
                    logger.error(f"注入探针失败 {module_name}.{function_name}: {str(e)}")
            
            logger.info(f"自动注入完成: 已注入 {injection_count} 个内存探针")
            self.auto_inject_done = True
            
        except Exception as e:
            logger.error(f"自动注入探针过程中发生错误: {str(e)}")

def get_probe_manager() -> MemoryProbeManager:
    """获取内存探针管理器的单例实例"""
    global _PROBE_MANAGER
    if _PROBE_MANAGER is None:
        _PROBE_MANAGER = MemoryProbeManager()
    return _PROBE_MANAGER

def mem_probe(name: str = None, level: str = "medium") -> Dict[str, Any]:
    """
    内存检查点探针
    
    Args:
        name: 探针名称，如果为None则使用调用者函数名
        level: 探针级别
        
    Returns:
        内存检查结果
    """
    if name is None:
        # 获取调用者帧
        caller_frame = inspect.currentframe().f_back
        caller_module = inspect.getmodule(caller_frame)
        module_name = caller_module.__name__ if caller_module else "unknown"
        function_name = caller_frame.f_code.co_name
        name = f"{module_name}.{function_name}"
    
    # 获取探针管理器并检查
    manager = get_probe_manager()
    
    # 获取调用位置
    caller_frame = inspect.currentframe().f_back
    file_name = caller_frame.f_code.co_filename
    line_number = caller_frame.f_lineno
    location = f"{os.path.basename(file_name)}:{line_number}"
    
    # 检查内存
    result = manager.check_probe(name, {"location": location})
    
    # 如果内存使用超过危险阈值，可以考虑触发保护措施
    if result.get("memory_usage", 0) >= PROBE_CONFIG["threshold_critical"]:
        # 在关键函数内触发垃圾回收
        gc.collect()
        
        # 如果是高危探针，可以抛出异常
        if level == "critical":
            raise MemoryOverflowError(f"内存超限在函数: {name} (位置: {location})")
    
    return result

# 装饰器: 为函数添加内存探针
def probe_memory(level: str = "medium"):
    """
    装饰器: 为函数添加内存探针
    
    Args:
        level: 探针级别
        
    Returns:
        装饰后的函数
    """
    return get_probe_manager().memory_probe_decorator(level)

# 自动注入探针
def auto_inject_probes():
    """自动注入探针到预配置的代码点"""
    if PROBE_CONFIG["auto_inject"]:
        manager = get_probe_manager()
        manager.inject_probes()
        manager.start_monitoring()

# 在模块导入时自动注入探针
if PROBE_CONFIG["auto_inject"]:
    # 延迟注入以避免循环导入
    threading.Timer(1.0, auto_inject_probes).start() 