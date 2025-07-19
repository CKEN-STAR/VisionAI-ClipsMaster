#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自检容错系统

提供全面的自检和错误恢复机制，确保VisionAI-ClipsMaster在各种异常情况下能够稳定运行。
"""

import os
import sys
import time
import logging
import threading
import subprocess
import traceback
from typing import Dict, List, Callable, Optional, Any, Tuple
from enum import Enum
from datetime import datetime

# 导入平台适配层
from .platform_adapter import get_memory_usage, get_cpu_usage, get_disk_usage

# 配置日志
logger = logging.getLogger("self_check")

class ComponentStatus(Enum):
    """组件状态枚举"""
    NORMAL = "正常"
    WARNING = "警告"
    ERROR = "错误"
    CRITICAL = "严重"
    UNKNOWN = "未知"

class CheckResult:
    """检查结果类"""
    
    def __init__(self, status: ComponentStatus, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化检查结果
        
        Args:
            status: 组件状态
            message: 状态描述
            details: 详细信息
        """
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        return f"{self.status.value}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        }

class Watchdog:
    """监视器组件
    
    检测各个关键进程和线程的存活状态，在发现异常时自动重启服务。
    """
    
    def __init__(self, check_interval: float = 5.0):
        """初始化监视器
        
        Args:
            check_interval: 检查间隔时间（秒）
        """
        self.check_interval = check_interval
        self.last_heartbeat = time.time()
        self.monitored_threads: Dict[str, Dict[str, Any]] = {}
        self.stop_flag = threading.Event()
        self.watchdog_thread = None
        self.alerts = []
        self.max_alerts = 100  # 最多保存的警报数量
        
        # 组件状态
        self.component_status: Dict[str, CheckResult] = {}
        
        logger.info(f"初始化监视器，检查间隔：{check_interval}秒")
    
    def start(self):
        """启动监视器"""
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            logger.warning("监视器已经在运行中")
            return
        
        logger.info("启动监视器")
        self.stop_flag.clear()
        self.watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="watchdog-thread",
            daemon=True
        )
        self.watchdog_thread.start()
    
    def stop(self):
        """停止监视器"""
        logger.info("停止监视器")
        self.stop_flag.set()
        
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=2.0)
    
    def _watchdog_loop(self):
        """监视器主循环"""
        logger.info("监视器循环开始运行")
        
        while not self.stop_flag.is_set():
            try:
                # 检查所有监控项
                self._check_all_components()
                
                # 检查心跳
                self._check_heartbeat()
                
                # 检查监控的线程
                self._check_monitored_threads()
                
            except Exception as e:
                logger.error(f"监视器循环异常: {e}")
                logger.debug(traceback.format_exc())
            
            # 等待下一次检查
            time.sleep(self.check_interval)
    
    def _check_all_components(self):
        """检查所有组件状态"""
        # 检查数据采集线程
        self._check_data_collection()
        
        # 检查缓冲区
        self._check_buffer_status()
        
        # 检查通信通道
        self._check_communication_channels()
        
        # 检查系统资源
        self._check_system_resources()
    
    def _check_heartbeat(self):
        """检查心跳状态"""
        current_time = time.time()
        heartbeat_age = current_time - self.last_heartbeat
        
        if heartbeat_age > self.check_interval * 2:
            # 心跳超时，记录警告
            logger.warning(f"心跳超时: {heartbeat_age:.1f}秒")
            self._add_alert(ComponentStatus.WARNING, "心跳超时", {
                "age": heartbeat_age,
                "threshold": self.check_interval * 2
            })
    
    def _check_monitored_threads(self):
        """检查被监控的线程"""
        for thread_name, thread_info in list(self.monitored_threads.items()):
            thread = thread_info.get("thread")
            if not thread or not thread.is_alive():
                # 线程已经停止，尝试重启
                logger.warning(f"检测到线程停止: {thread_name}")
                self._add_alert(ComponentStatus.WARNING, f"线程停止: {thread_name}")
                
                restart_func = thread_info.get("restart_func")
                if restart_func and callable(restart_func):
                    try:
                        logger.info(f"尝试重启线程: {thread_name}")
                        new_thread = restart_func()
                        if new_thread:
                            self.monitored_threads[thread_name]["thread"] = new_thread
                            logger.info(f"线程已重启: {thread_name}")
                            self._add_alert(ComponentStatus.NORMAL, f"线程已重启: {thread_name}")
                    except Exception as e:
                        logger.error(f"重启线程失败: {thread_name}, 错误: {e}")
                        self._add_alert(ComponentStatus.ERROR, f"重启线程失败: {thread_name}", {
                            "error": str(e)
                        })
    
    def _check_data_collection(self):
        """检查数据采集线程状态"""
        # 这里实现具体的数据采集线程检查逻辑
        # 例如检查最后一次数据采集时间、数据量等
        # 示例实现
        pass
    
    def _check_buffer_status(self):
        """检查缓冲区状态"""
        # 这里实现具体的缓冲区检查逻辑
        # 例如检查缓冲区大小、数据处理延迟等
        # 示例实现
        pass
    
    def _check_communication_channels(self):
        """检查通信通道状态"""
        # 这里实现具体的通信通道检查逻辑
        # 例如检查网络连接、消息队列状态等
        # 示例实现
        pass
    
    def _check_system_resources(self):
        """检查系统资源状态"""
        try:
            # 获取内存使用情况
            mem_info = get_memory_usage()
            
            # 检查内存使用率
            if mem_info["percent"] > 90:
                logger.warning(f"内存使用率过高: {mem_info['percent']:.1f}%")
                self._add_alert(ComponentStatus.WARNING, "内存使用率过高", {
                    "percent": mem_info["percent"],
                    "used_mb": mem_info["used"],
                    "total_mb": mem_info["total"]
                })
                
                # 尝试释放内存
                self._try_free_memory()
            
            # 获取CPU使用率
            cpu_percent = get_cpu_usage()
            
            # 检查CPU使用率
            if cpu_percent > 90:
                logger.warning(f"CPU使用率过高: {cpu_percent:.1f}%")
                self._add_alert(ComponentStatus.WARNING, "CPU使用率过高", {
                    "percent": cpu_percent
                })
            
            # 获取磁盘使用情况
            disk_info = get_disk_usage()
            
            # 检查磁盘空间
            if disk_info["percent"] > 90:
                logger.warning(f"磁盘使用率过高: {disk_info['percent']:.1f}%")
                self._add_alert(ComponentStatus.WARNING, "磁盘使用率过高", {
                    "percent": disk_info["percent"],
                    "free_gb": disk_info["free"],
                    "total_gb": disk_info["total"]
                })
        
        except Exception as e:
            logger.error(f"检查系统资源异常: {e}")
    
    def _try_free_memory(self):
        """尝试释放内存"""
        logger.info("尝试释放内存")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # TODO: 可以添加更多内存释放策略，如卸载不必要的模型等
    
    def register_thread(self, thread_name: str, thread: threading.Thread, 
                      restart_func: Optional[Callable[[], threading.Thread]] = None):
        """注册需要监控的线程
        
        Args:
            thread_name: 线程名称
            thread: 线程对象
            restart_func: 重启线程的函数
        """
        logger.info(f"注册监控线程: {thread_name}")
        self.monitored_threads[thread_name] = {
            "thread": thread,
            "restart_func": restart_func,
            "last_check": time.time()
        }
    
    def unregister_thread(self, thread_name: str):
        """取消注册监控线程
        
        Args:
            thread_name: 线程名称
        """
        if thread_name in self.monitored_threads:
            logger.info(f"取消注册监控线程: {thread_name}")
            del self.monitored_threads[thread_name]
    
    def heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
    
    def check_alive(self):
        """检查监视器是否活跃
        
        如果监视器长时间未更新心跳，会尝试重启监控服务。
        
        Returns:
            是否存活
        """
        current_time = time.time()
        if current_time - self.last_heartbeat > self.check_interval * 2:
            logger.critical("监控进程无响应，尝试重启")
            self._restart_monitor_service()
            return False
        return True
    
    def _restart_monitor_service(self):
        """重启监控服务"""
        logger.critical("正在重启监控服务")
        
        # 尝试使用优雅的方式重启
        try:
            # 这里实现具体的重启逻辑
            # 在实际应用中，可能需要根据应用的架构来实现
            # 例如通过进程管理器或系统服务管理器重启
            
            # 示例实现：直接重启当前监控线程
            if self.watchdog_thread and not self.watchdog_thread.is_alive():
                self.start()
                logger.info("监控服务已重启")
                return
            
            # 如果上面的方法不起作用，可以尝试更激进的方法
            # 例如重启整个应用
            self._emergency_restart()
            
        except Exception as e:
            logger.error(f"重启监控服务失败: {e}")
            logger.debug(traceback.format_exc())
    
    def _emergency_restart(self):
        """紧急重启"""
        logger.critical("执行紧急重启")
        
        # 这里可以实现紧急重启的逻辑
        # 在实际应用中，可能涉及到保存状态、通知管理员等操作
        
        # 示例实现：记录状态并退出
        try:
            # 保存当前状态
            self._save_emergency_state()
            
            # 在实际应用中，可能会重启整个进程或应用
            # os.execv(sys.executable, ['python'] + sys.argv)
            
            # 本示例中只是记录信息
            logger.critical("紧急重启模拟执行完成")
            
        except Exception as e:
            logger.error(f"紧急重启失败: {e}")
    
    def _save_emergency_state(self):
        """保存紧急状态"""
        try:
            emergency_file = "emergency_state.log"
            with open(emergency_file, "w") as f:
                f.write(f"紧急状态保存时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"监控线程状态: {'活跃' if self.watchdog_thread and self.watchdog_thread.is_alive() else '停止'}\n")
                f.write(f"最后心跳时间: {datetime.fromtimestamp(self.last_heartbeat).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"注册的线程数量: {len(self.monitored_threads)}\n")
                
                # 保存线程状态
                f.write("\n线程状态:\n")
                for thread_name, thread_info in self.monitored_threads.items():
                    thread = thread_info.get("thread")
                    thread_alive = thread and thread.is_alive()
                    f.write(f"- {thread_name}: {'活跃' if thread_alive else '停止'}\n")
                
                # 保存最近警报
                f.write("\n最近警报:\n")
                for alert in self.alerts[-10:]:
                    f.write(f"- {alert['datetime']} {alert['status']}: {alert['message']}\n")
            
            logger.info(f"紧急状态已保存到 {emergency_file}")
            
        except Exception as e:
            logger.error(f"保存紧急状态失败: {e}")
    
    def _add_alert(self, status: ComponentStatus, message: str, details: Optional[Dict[str, Any]] = None):
        """添加警报
        
        Args:
            status: 组件状态
            message: 状态描述
            details: 详细信息
        """
        # 创建检查结果
        result = CheckResult(status, message, details)
        
        # 添加到警报列表
        self.alerts.append(result.to_dict())
        
        # 如果超过最大数量，移除最早的警报
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
    
    def get_alerts(self, limit: int = 10, status_filter: Optional[ComponentStatus] = None) -> List[Dict[str, Any]]:
        """获取警报列表
        
        Args:
            limit: 返回的警报数量
            status_filter: 状态过滤器
        
        Returns:
            警报列表
        """
        if status_filter:
            filtered_alerts = [a for a in self.alerts if a['status'] == status_filter.value]
        else:
            filtered_alerts = self.alerts
        
        return filtered_alerts[-limit:]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要
        
        Returns:
            状态摘要字典
        """
        # 计算各状态数量
        status_counts = {status.value: 0 for status in ComponentStatus}
        for alert in self.alerts:
            status_counts[alert['status']] += 1
        
        # 获取系统资源信息
        try:
            mem_info = get_memory_usage()
            cpu_percent = get_cpu_usage()
            disk_info = get_disk_usage()
        except:
            mem_info = {"percent": 0, "used": 0, "total": 0}
            cpu_percent = 0
            disk_info = {"percent": 0, "free": 0, "total": 0}
        
        return {
            "status_counts": status_counts,
            "thread_count": len(self.monitored_threads),
            "active_threads": sum(1 for info in self.monitored_threads.values() 
                                if info.get("thread") and info.get("thread").is_alive()),
            "watchdog_alive": self.watchdog_thread and self.watchdog_thread.is_alive(),
            "last_heartbeat_age": time.time() - self.last_heartbeat,
            "memory_percent": mem_info["percent"],
            "cpu_percent": cpu_percent,
            "disk_percent": disk_info["percent"],
            "alert_count": len(self.alerts)
        }


class SystemSelfCheck:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """系统自检类
    
    提供全面的系统自检功能，包括组件检查、性能分析、错误诊断等。
    """
    
    def __init__(self):
        """初始化系统自检类"""
        self.watchdog = Watchdog()
        self.check_handlers = {}
        self.recovery_handlers = {}
        
        # 注册默认检查处理器
        self._register_default_handlers()
        
        logger.info("初始化系统自检")
    
    def _register_default_handlers(self):
        """注册默认检查处理器"""
        # 注册系统资源检查
        self.register_check("system_resources", self._check_system_resources)
        
        # 注册数据采集检查
        self.register_check("data_collection", self._check_data_collection)
        
        # 注册缓冲区检查
        self.register_check("buffer_status", self._check_buffer_status)
        
        # 注册通信通道检查
        self.register_check("communication", self._check_communication)
        
        # 注册模型状态检查
        self.register_check("model_status", self._check_model_status)
        
        # 注册恢复处理器
        self.register_recovery("restart_service", self._restart_service)
        self.register_recovery("free_memory", self._free_memory)
        self.register_recovery("reset_buffer", self._reset_buffer)
    
    def start(self):
        """启动自检系统"""
        logger.info("启动系统自检")
        self.watchdog.start()
    
    def stop(self):
        """停止自检系统"""
        logger.info("停止系统自检")
        self.watchdog.stop()
    
    def register_check(self, check_name: str, check_func: Callable[[], CheckResult]):
        """注册检查处理器
        
        Args:
            check_name: 检查名称
            check_func: 检查函数
        """
        logger.info(f"注册检查处理器: {check_name}")
        self.check_handlers[check_name] = check_func
    
    def unregister_check(self, check_name: str):
        """取消注册检查处理器
        
        Args:
            check_name: 检查名称
        """
        if check_name in self.check_handlers:
            logger.info(f"取消注册检查处理器: {check_name}")
            del self.check_handlers[check_name]
    
    def register_recovery(self, recovery_name: str, recovery_func: Callable[[str, Dict[str, Any]], bool]):
        """注册恢复处理器
        
        Args:
            recovery_name: 恢复处理器名称
            recovery_func: 恢复函数
        """
        logger.info(f"注册恢复处理器: {recovery_name}")
        self.recovery_handlers[recovery_name] = recovery_func
    
    def run_all_checks(self) -> Dict[str, CheckResult]:
        """运行所有检查
        
        Returns:
            检查结果字典
        """
        logger.info("运行所有系统检查")
        results = {}
        
        for check_name, check_func in self.check_handlers.items():
            try:
                logger.debug(f"运行检查: {check_name}")
                result = check_func()
                results[check_name] = result
                
                # 如果检查结果为错误或严重，尝试恢复
                if result.status in [ComponentStatus.ERROR, ComponentStatus.CRITICAL]:
                    self._try_recovery(check_name, result)
                
            except Exception as e:
                logger.error(f"运行检查异常: {check_name}, 错误: {e}")
                logger.debug(traceback.format_exc())
                
                # 创建错误结果
                results[check_name] = CheckResult(
                    ComponentStatus.ERROR,
                    f"检查过程异常: {e}",
                    {"exception": str(e), "traceback": traceback.format_exc()}
                )
        
        return results
    
    def _try_recovery(self, check_name: str, result: CheckResult):
        """尝试恢复
        
        Args:
            check_name: 检查名称
            result: 检查结果
        """
        logger.warning(f"检测到问题，尝试恢复: {check_name}, 状态: {result.status.value}")
        
        # 根据检查名称选择合适的恢复处理器
        if check_name == "system_resources":
            recovery_func = self.recovery_handlers.get("free_memory")
        elif check_name == "data_collection":
            recovery_func = self.recovery_handlers.get("restart_service")
        elif check_name == "buffer_status":
            recovery_func = self.recovery_handlers.get("reset_buffer")
        elif check_name == "communication":
            recovery_func = self.recovery_handlers.get("restart_service")
        elif check_name == "model_status":
            recovery_func = self.recovery_handlers.get("restart_service")
        else:
            recovery_func = None
        
        # 执行恢复
        if recovery_func:
            try:
                logger.info(f"执行恢复操作: {check_name}")
                success = recovery_func(check_name, result.details)
                
                if success:
                    logger.info(f"恢复操作成功: {check_name}")
                else:
                    logger.warning(f"恢复操作未能解决问题: {check_name}")
                
            except Exception as e:
                logger.error(f"恢复操作异常: {check_name}, 错误: {e}")
                logger.debug(traceback.format_exc())
        else:
            logger.warning(f"未找到合适的恢复处理器: {check_name}")
    
    def _check_system_resources(self) -> CheckResult:
        """检查系统资源
        
        Returns:
            检查结果
        """
        try:
            # 获取内存使用情况
            mem_info = get_memory_usage()
            
            # 获取CPU使用率
            cpu_percent = get_cpu_usage()
            
            # 获取磁盘使用情况
            disk_info = get_disk_usage()
            
            # 检查内存使用率
            if mem_info["percent"] > 90:
                return CheckResult(
                    ComponentStatus.WARNING,
                    f"内存使用率过高: {mem_info['percent']:.1f}%",
                    {
                        "mem_percent": mem_info["percent"],
                        "mem_used": mem_info["used"],
                        "mem_total": mem_info["total"],
                        "cpu_percent": cpu_percent,
                        "disk_percent": disk_info["percent"]
                    }
                )
            
            # 检查CPU使用率
            if cpu_percent > 90:
                return CheckResult(
                    ComponentStatus.WARNING,
                    f"CPU使用率过高: {cpu_percent:.1f}%",
                    {
                        "mem_percent": mem_info["percent"],
                        "cpu_percent": cpu_percent,
                        "disk_percent": disk_info["percent"]
                    }
                )
            
            # 检查磁盘使用率
            if disk_info["percent"] > 90:
                return CheckResult(
                    ComponentStatus.WARNING,
                    f"磁盘使用率过高: {disk_info['percent']:.1f}%",
                    {
                        "mem_percent": mem_info["percent"],
                        "cpu_percent": cpu_percent,
                        "disk_percent": disk_info["percent"],
                        "disk_free": disk_info["free"]
                    }
                )
            
            # 所有资源正常
            return CheckResult(
                ComponentStatus.NORMAL,
                "系统资源正常",
                {
                    "mem_percent": mem_info["percent"],
                    "cpu_percent": cpu_percent,
                    "disk_percent": disk_info["percent"]
                }
            )
            
        except Exception as e:
            logger.error(f"检查系统资源异常: {e}")
            return CheckResult(
                ComponentStatus.ERROR,
                f"检查系统资源异常: {e}",
                {"exception": str(e)}
            )
    
    def _check_data_collection(self) -> CheckResult:
        """检查数据采集
        
        Returns:
            检查结果
        """
        # 这里实现具体的数据采集检查逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        return CheckResult(ComponentStatus.NORMAL, "数据采集正常")
    
    def _check_buffer_status(self) -> CheckResult:
        """检查缓冲区状态
        
        Returns:
            检查结果
        """
        # 这里实现具体的缓冲区检查逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        return CheckResult(ComponentStatus.NORMAL, "缓冲区状态正常")
    
    def _check_communication(self) -> CheckResult:
        """检查通信通道
        
        Returns:
            检查结果
        """
        # 这里实现具体的通信通道检查逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        return CheckResult(ComponentStatus.NORMAL, "通信通道正常")
    
    def _check_model_status(self) -> CheckResult:
        """检查模型状态
        
        Returns:
            检查结果
        """
        # 这里实现具体的模型状态检查逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        return CheckResult(ComponentStatus.NORMAL, "模型状态正常")
    
    def _restart_service(self, check_name: str, details: Dict[str, Any]) -> bool:
        """重启服务
        
        Args:
            check_name: 检查名称
            details: 详细信息
        
        Returns:
            是否成功
        """
        logger.info(f"重启服务: {check_name}")
        
        # 这里实现具体的服务重启逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        
        return True
    
    def _free_memory(self, check_name: str, details: Dict[str, Any]) -> bool:
        """释放内存
        
        Args:
            check_name: 检查名称
            details: 详细信息
        
        Returns:
            是否成功
        """
        logger.info("尝试释放内存")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 这里可以添加更多内存释放策略
        # 例如卸载不必要的模型、清理缓存等
        
        return True
    
    def _reset_buffer(self, check_name: str, details: Dict[str, Any]) -> bool:
        """重置缓冲区
        
        Args:
            check_name: 检查名称
            details: 详细信息
        
        Returns:
            是否成功
        """
        logger.info("重置缓冲区")
        
        # 这里实现具体的缓冲区重置逻辑
        # 示例实现，实际应用中需要根据具体需求实现
        
        return True


# 创建全局自检实例
_global_self_check = None

def get_self_check() -> SystemSelfCheck:
    """获取全局自检实例
    
    Returns:
        全局自检实例
    """
    global _global_self_check
    
    if _global_self_check is None:
        _global_self_check = SystemSelfCheck()
    
    return _global_self_check

def start_self_check():
    """启动全局自检"""
    self_check = get_self_check()
    self_check.start()
    return self_check

def stop_self_check():
    """停止全局自检"""
    global _global_self_check
    
    if _global_self_check:
        _global_self_check.stop()
        _global_self_check = None

# 导出主要类和函数
__all__ = [
    'Watchdog', 'SystemSelfCheck', 'ComponentStatus', 'CheckResult',
    'get_self_check', 'start_self_check', 'stop_self_check'
] 