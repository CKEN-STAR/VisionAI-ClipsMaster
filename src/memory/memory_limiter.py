#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存限制模拟器

提供跨平台的内存使用限制功能，用于测试系统在内存受限环境下的表现。
支持Linux(cgroups)和Windows(Job Object API)两种实现。
与自动恢复系统集成，模拟内存不足场景触发恢复机制。
"""

import os
import sys
import uuid
import psutil
import logging
import threading
import time
import tempfile
import shutil
import platform
from typing import Optional, Dict, Any, List, Callable, Tuple

# 项目模块导入
from src.utils.log_handler import get_logger
from src.utils.memory_guard import get_memory_guard
from src.utils.exceptions import MemoryOverflowError

# 设置日志
logger = get_logger("memory_limiter")

# 确定当前操作系统
CURRENT_OS = platform.system()  # 'Windows', 'Linux', 'Darwin'

class MemoryLimiter:
    """内存限制模拟器基类"""
    
    def __init__(self, limit_mb: int = 4096, check_interval: float = 2.0):
        """
        初始化内存限制模拟器
        
        Args:
            limit_mb: 内存限制(MB)
            check_interval: 检查间隔(秒)
        """
        self.limit_mb = limit_mb
        self.check_interval = check_interval
        self.enabled = False
        self.monitor_thread = None
        self.current_usage_mb = 0
        self.peak_usage_mb = 0
        self.overflow_callbacks = []
        # 记录原始进程ID(为子进程限制做准备)
        self.original_pid = os.getpid()
        
        # 初始化资源跟踪
        self._init_tracking()
        
        logger.info(f"内存限制模拟器初始化完成: 限制={limit_mb}MB, 检查间隔={check_interval}秒")
    
    def _init_tracking(self):
        """初始化资源跟踪"""
        # 创建临时目录用于存储资源使用信息
        self.tracking_dir = os.path.join(
            tempfile.gettempdir(), 
            f"visionai_memory_limiter_{str(uuid.uuid4())[:8]}"
        )
        os.makedirs(self.tracking_dir, exist_ok=True)
        
        # 记录进程信息
        self.tracked_processes = {self.original_pid: "main"}
        self._update_process_info()
        
        logger.debug(f"资源跟踪初始化: {self.tracking_dir}")
    
    def _update_process_info(self):
        """更新进程信息文件"""
        process_info_file = os.path.join(self.tracking_dir, "processes.txt")
        try:
            with open(process_info_file, 'w') as f:
                for pid, name in self.tracked_processes.items():
                    f.write(f"{pid}:{name}\n")
        except Exception as e:
            logger.warning(f"更新进程信息失败: {e}")
    
    def register_overflow_callback(self, callback: Callable):
        """
        注册内存溢出回调函数
        
        Args:
            callback: 回调函数，当内存使用超过限制时调用
        """
        self.overflow_callbacks.append(callback)
        logger.debug(f"已注册内存溢出回调: {callback.__name__}")
    
    def start(self):
        """启动内存限制模拟"""
        if self.enabled:
            logger.warning("内存限制模拟器已经在运行")
            return
        
        # 启动监控线程
        self.enabled = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_memory_usage,
            daemon=True,
            name="memory-limiter-monitor"
        )
        self.monitor_thread.start()
        
        logger.info("内存限制模拟器已启动")
    
    def stop(self):
        """停止内存限制模拟"""
        if not self.enabled:
            logger.warning("内存限制模拟器未在运行")
            return
        
        self.enabled = False
        if self.monitor_thread:
            # 等待监控线程退出
            self.monitor_thread.join(timeout=3.0)
            self.monitor_thread = None
        
        # 清理资源
        self._cleanup()
        
        logger.info("内存限制模拟器已停止")
    
    def _cleanup(self):
        """清理资源"""
        try:
            if os.path.exists(self.tracking_dir):
                shutil.rmtree(self.tracking_dir)
        except Exception as e:
            logger.warning(f"清理临时目录失败: {e}")
    
    def _monitor_memory_usage(self):
        """监控内存使用情况"""
        logger.debug("内存监控线程启动")
        
        while self.enabled:
            try:
                # 获取当前进程内存使用情况
                usage_mb = self._get_memory_usage()
                self.current_usage_mb = usage_mb
                
                # 更新峰值
                if usage_mb > self.peak_usage_mb:
                    self.peak_usage_mb = usage_mb
                
                # 检查是否超过限制
                if usage_mb > self.limit_mb:
                    logger.warning(
                        f"内存使用超过限制: {usage_mb:.1f}MB > {self.limit_mb}MB"
                    )
                    self._trigger_overflow(usage_mb)
                
                # 记录内存使用
                usage_ratio = usage_mb / self.limit_mb * 100
                if usage_ratio > 80:
                    log_level = logging.WARNING
                elif usage_ratio > 60:
                    log_level = logging.INFO
                else:
                    log_level = logging.DEBUG
                
                logger.log(
                    log_level, 
                    f"内存使用: {usage_mb:.1f}MB / {self.limit_mb}MB ({usage_ratio:.1f}%)"
                )
                
            except Exception as e:
                logger.error(f"内存监控异常: {e}")
            
            # 睡眠指定时间
            time.sleep(self.check_interval)
    
    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用情况
        
        Returns:
            float: 内存使用量(MB)
        """
        try:
            # 获取当前进程
            process = psutil.Process(self.original_pid)
            # 获取内存使用(包括子进程)
            memory_info = process.memory_info()
            # 返回MB单位
            return memory_info.rss / (1024 * 1024)
        except Exception as e:
            logger.error(f"获取内存使用信息失败: {e}")
            return 0.0
    
    def _trigger_overflow(self, current_usage: float):
        """
        触发内存溢出处理
        
        Args:
            current_usage: 当前内存使用量(MB)
        """
        # 构建溢出信息
        overflow_info = {
            "current_usage_mb": current_usage,
            "limit_mb": self.limit_mb,
            "overflow_mb": current_usage - self.limit_mb,
            "peak_usage_mb": self.peak_usage_mb,
            "timestamp": time.time(),
            "pid": self.original_pid
        }
        
        # 调用所有注册的回调
        for callback in self.overflow_callbacks:
            try:
                callback(overflow_info)
            except Exception as e:
                logger.error(f"调用内存溢出回调失败: {e}")
        
        # 触发内存警告(不会立即终止进程)
        logger.critical(
            f"内存使用超限! 当前: {current_usage:.1f}MB, 限制: {self.limit_mb}MB, "
            f"超出: {current_usage - self.limit_mb:.1f}MB"
        )
        
    def track_process(self, pid: int, name: str = None):
        """
        跟踪子进程的内存使用
        
        Args:
            pid: 进程ID
            name: 进程名称(可选)
        """
        if not name:
            try:
                name = psutil.Process(pid).name()
            except:
                name = f"process_{pid}"
        
        self.tracked_processes[pid] = name
        self._update_process_info()
        logger.debug(f"添加进程跟踪: {pid} - {name}")
        
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            "enabled": self.enabled,
            "limit_mb": self.limit_mb,
            "current_usage_mb": self.current_usage_mb,
            "peak_usage_mb": self.peak_usage_mb,
            "usage_percentage": (self.current_usage_mb / self.limit_mb * 100) if self.limit_mb else 0,
            "tracked_processes": len(self.tracked_processes),
            "platform": CURRENT_OS
        }


class LinuxMemoryLimiter(MemoryLimiter):
    """Linux系统下的内存限制模拟器(使用cgroups)"""
    
    def __init__(self, limit_mb: int = 4096, check_interval: float = 2.0):
        """初始化Linux内存限制模拟器"""
        super().__init__(limit_mb, check_interval)
        
        # cgroup路径
        self.cgroup_path = None
        # 进程列表文件
        self.tasks_file = None
        # 内存限制文件
        self.memory_limit_file = None
        
        # 初始化cgroup
        self._setup_cgroup()
    
    def _setup_cgroup(self):
        """设置cgroup内存限制"""
        try:
            # 检查cgroup文件系统是否挂载
            if not os.path.exists("/sys/fs/cgroup/memory"):
                logger.warning("cgroup内存子系统未挂载，将使用模拟模式")
                return
            
            # 创建自定义cgroup
            group_name = f"visionai_memory_test_{str(uuid.uuid4())[:8]}"
            self.cgroup_path = f"/sys/fs/cgroup/memory/{group_name}"
            
            # 创建cgroup目录
            os.makedirs(self.cgroup_path, exist_ok=True)
            
            # 设置内存限制
            self.memory_limit_file = os.path.join(self.cgroup_path, "memory.limit_in_bytes")
            with open(self.memory_limit_file, 'w') as f:
                # 转换为字节
                limit_bytes = self.limit_mb * 1024 * 1024
                f.write(str(limit_bytes))
            
            # 设置OOM控制(0表示触发OOM killer)
            oom_control_file = os.path.join(self.cgroup_path, "memory.oom_control")
            with open(oom_control_file, 'w') as f:
                f.write("0")
            
            # 设置进程列表文件
            self.tasks_file = os.path.join(self.cgroup_path, "tasks")
            
            # 将当前进程添加到cgroup
            with open(self.tasks_file, 'w') as f:
                f.write(str(os.getpid()))
            
            logger.info(f"cgroup内存限制已设置: {self.limit_mb}MB, 路径: {self.cgroup_path}")
            
        except Exception as e:
            logger.error(f"设置cgroup失败: {e}")
            self.cgroup_path = None
            self.tasks_file = None
            self.memory_limit_file = None
            
            # 回退到基础实现
            logger.info("使用基础内存限制模拟")
    
    def track_process(self, pid: int, name: str = None):
        """添加进程到cgroup"""
        super().track_process(pid, name)
        
        if self.tasks_file and os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'a') as f:
                    f.write(f"{pid}\n")
                logger.debug(f"进程 {pid} 已添加到cgroup")
            except Exception as e:
                logger.warning(f"添加进程 {pid} 到cgroup失败: {e}")
    
    def _cleanup(self):
        """清理cgroup资源"""
        if self.cgroup_path and os.path.exists(self.cgroup_path):
            try:
                # 移除当前进程
                if self.tasks_file and os.path.exists(self.tasks_file):
                    with open("/sys/fs/cgroup/memory/tasks", 'w') as f:
                        f.write(str(os.getpid()))
                
                # 删除cgroup
                os.rmdir(self.cgroup_path)
                logger.debug(f"cgroup已清理: {self.cgroup_path}")
            except Exception as e:
                logger.warning(f"清理cgroup失败: {e}")
        
        # 调用父类清理
        super()._cleanup()


class WindowsMemoryLimiter(MemoryLimiter):
    """Windows系统下的内存限制模拟器(使用Job Object API)"""
    
    def __init__(self, limit_mb: int = 4096, check_interval: float = 2.0):
        """初始化Windows内存限制模拟器"""
        super().__init__(limit_mb, check_interval)
        
        # Job Object句柄
        self.job_handle = None
        
        # 初始化Job Object
        self._setup_job_object()
    
    def _setup_job_object(self):
        """设置Job Object内存限制"""
        try:
            # 尝试导入Windows特定模块
            import win32job
            import win32api
            import win32con
            import pywintypes
            
            # 创建Job Object
            job_name = f"VisionAIMemoryTest_{str(uuid.uuid4())[:8]}"
            self.job_handle = win32job.CreateJobObject(None, job_name)
            
            # 设置基本限制信息
            basic_limit_info = win32job.QueryInformationJobObject(
                self.job_handle, win32job.JobObjectBasicLimitInformation
            )
            
            # 启用UI限制
            basic_limit_info['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_JOB_MEMORY
            
            # 设置扩展限制信息
            extended_info = win32job.QueryInformationJobObject(
                self.job_handle, win32job.JobObjectExtendedLimitInformation
            )
            
            # 更新基本限制
            extended_info['BasicLimitInformation'] = basic_limit_info
            
            # 设置内存限制
            extended_info['ProcessMemoryLimit'] = self.limit_mb * 1024 * 1024
            extended_info['JobMemoryLimit'] = self.limit_mb * 1024 * 1024
            
            # 应用限制
            win32job.SetInformationJobObject(
                self.job_handle,
                win32job.JobObjectExtendedLimitInformation,
                extended_info
            )
            
            # 将当前进程添加到Job Object
            current_process = win32api.GetCurrentProcess()
            win32job.AssignProcessToJobObject(self.job_handle, current_process)
            
            logger.info(f"Windows Job Object内存限制已设置: {self.limit_mb}MB")
            
        except ImportError:
            logger.warning("未找到pywin32模块，无法使用Job Object API")
            self.job_handle = None
        except Exception as e:
            logger.error(f"设置Job Object失败: {e}")
            self.job_handle = None
            
            # 回退到基础实现
            logger.info("使用基础内存限制模拟")
    
    def track_process(self, pid: int, name: str = None):
        """添加进程到Job Object"""
        super().track_process(pid, name)
        
        if self.job_handle:
            try:
                import win32job
                import win32api
                
                # 获取进程句柄
                process_handle = win32api.OpenProcess(
                    win32job.PROCESS_ALL_ACCESS, False, pid
                )
                
                # 添加到Job Object
                win32job.AssignProcessToJobObject(self.job_handle, process_handle)
                logger.debug(f"进程 {pid} 已添加到Job Object")
            except Exception as e:
                logger.warning(f"添加进程 {pid} 到Job Object失败: {e}")
    
    def _cleanup(self):
        """清理Job Object资源"""
        if self.job_handle:
            try:
                import win32job
                
                # 终止Job Object
                win32job.TerminateJobObject(self.job_handle, 0)
                # 关闭句柄
                win32job.CloseHandle(self.job_handle)
                self.job_handle = None
                logger.debug("Job Object已清理")
            except Exception as e:
                logger.warning(f"清理Job Object失败: {e}")
        
        # 调用父类清理
        super()._cleanup()


class MacOSMemoryLimiter(MemoryLimiter):
    """macOS系统下的内存限制模拟器(模拟实现)"""
    
    def __init__(self, limit_mb: int = 4096, check_interval: float = 2.0):
        """初始化macOS内存限制模拟器"""
        super().__init__(limit_mb, check_interval)
        logger.info("macOS没有直接的内存限制API，使用基础内存监控模拟")


def create_memory_limiter(limit_mb: int = 4096, check_interval: float = 2.0) -> MemoryLimiter:
    """
    创建适合当前操作系统的内存限制模拟器
    
    Args:
        limit_mb: 内存限制(MB)
        check_interval: 检查间隔(秒)
    
    Returns:
        MemoryLimiter: 内存限制模拟器实例
    """
    if CURRENT_OS == "Linux":
        return LinuxMemoryLimiter(limit_mb, check_interval)
    elif CURRENT_OS == "Windows":
        return WindowsMemoryLimiter(limit_mb, check_interval)
    elif CURRENT_OS == "Darwin":  # macOS
        return MacOSMemoryLimiter(limit_mb, check_interval)
    else:
        logger.warning(f"未知操作系统: {CURRENT_OS}，使用基础内存限制模拟")
        return MemoryLimiter(limit_mb, check_interval)


# 全局内存限制模拟器实例
_memory_limiter = None

def get_memory_limiter(limit_mb: int = 4096) -> MemoryLimiter:
    """
    获取全局内存限制模拟器实例
    
    Args:
        limit_mb: 内存限制(MB)，仅在首次调用时有效
    
    Returns:
        MemoryLimiter: 内存限制模拟器实例
    """
    global _memory_limiter
    if _memory_limiter is None:
        _memory_limiter = create_memory_limiter(limit_mb)
    return _memory_limiter


def memory_stress_test(target_mb: int, duration: float = 10.0, step_mb: int = 100) -> Dict[str, Any]:
    """
    执行内存压力测试
    
    Args:
        target_mb: 目标内存占用(MB)
        duration: 持续时间(秒)
        step_mb: 每步增加内存(MB)
    
    Returns:
        Dict: 测试结果
    """
    logger.info(f"开始内存压力测试: 目标={target_mb}MB, 持续={duration}秒, 步长={step_mb}MB")
    
    # 记录开始时间
    start_time = time.time()
    
    # 分配的内存块
    memory_blocks = []
    
    # 当前已分配内存
    allocated_mb = 0
    
    # 测试结果
    result = {
        "target_mb": target_mb,
        "max_allocated_mb": 0,
        "duration": 0,
        "success": False,
        "error": None
    }
    
    try:
        # 获取内存限制模拟器
        limiter = get_memory_limiter()
        
        # 记录内存使用情况
        initial_usage = limiter.current_usage_mb
        logger.info(f"初始内存使用: {initial_usage:.1f}MB")
        
        # 逐步分配内存
        while allocated_mb < target_mb and (time.time() - start_time) < duration:
            # 计算剩余时间
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            
            # 计算本次分配大小
            if remaining <= 0:
                break
                
            block_size = min(step_mb, target_mb - allocated_mb)
            if block_size <= 0:
                break
                
            # 分配内存
            try:
                memory_block = bytearray(block_size * 1024 * 1024)
                # 写入数据确保实际分配
                for i in range(0, len(memory_block), 4096):
                    memory_block[i] = 1
                
                memory_blocks.append(memory_block)
                allocated_mb += block_size
                
                logger.info(f"已分配内存: {allocated_mb}MB / {target_mb}MB")
                
                # 短暂休眠让监控有时间反应
                time.sleep(0.1)
                
            except MemoryError as e:
                logger.warning(f"内存分配失败: {e}")
                result["error"] = "MemoryError"
                break
        
        # 如果达到目标，维持一段时间
        if allocated_mb >= target_mb:
            logger.info(f"已达到目标内存分配: {allocated_mb}MB，保持{remaining:.1f}秒")
            # 等待剩余时间
            remaining_time = max(0, duration - (time.time() - start_time))
            if remaining_time > 0:
                time.sleep(remaining_time)
            
            result["success"] = True
        
        # 更新结果
        result["max_allocated_mb"] = allocated_mb
        result["duration"] = time.time() - start_time
        
        return result
        
    except Exception as e:
        logger.error(f"内存压力测试异常: {e}")
        result["error"] = str(e)
        return result
        
    finally:
        # 释放内存
        del memory_blocks
        # 强制垃圾回收
        import gc
        gc.collect()
        logger.info("内存压力测试结束，已释放内存")


# 与自动恢复系统集成
def integrate_with_recovery_system():
    """将内存限制模拟器与自动恢复系统集成"""
    try:
        from src.core.auto_recovery import get_auto_recovery, auto_heal
        from src.utils.exceptions import MemoryOverflowError
        
        # 获取内存限制模拟器
        limiter = get_memory_limiter()
        
        # 获取自动恢复系统
        recovery = get_auto_recovery()
        
        # 定义内存溢出回调
        def memory_overflow_callback(info: Dict[str, Any]):
            """内存溢出回调函数"""
            logger.warning(f"触发内存溢出回调: 使用={info['current_usage_mb']:.1f}MB, 限制={info['limit_mb']}MB")
            
            # 创建内存溢出异常
            error = MemoryOverflowError(
                f"模拟内存溢出: {info['current_usage_mb']:.1f}MB > {info['limit_mb']}MB"
            )
            
            # 触发自动恢复
            auto_heal(error, {
                "source": "memory_limiter",
                "overflow_info": info
            })
        
        # 注册回调
        limiter.register_overflow_callback(memory_overflow_callback)
        
        logger.info("内存限制模拟器已与自动恢复系统集成")
        return True
        
    except ImportError:
        logger.warning("自动恢复系统不可用，跳过集成")
        return False
    except Exception as e:
        logger.error(f"集成自动恢复系统失败: {e}")
        return False


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 创建内存限制模拟器(2GB限制)
    limiter = get_memory_limiter(2048)
    
    # 启动限制器
    limiter.start()
    
    try:
        # 执行内存压力测试(尝试分配1.5GB)
        result = memory_stress_test(1536, duration=30.0, step_mb=128)
        print(f"测试结果: {result}")
    finally:
        # 停止限制器
        limiter.stop() 