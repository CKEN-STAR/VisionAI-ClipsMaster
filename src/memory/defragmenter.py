#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存碎片整理模块

该模块负责整理和紧凑化内存，尤其是在大量资源释放后，确保VisionAI-ClipsMaster
在内存受限环境(4GB RAM/无GPU)下运行稳定。
主要功能：
1. 提供内存碎片整理方法
2. 自动按计划执行整理
3. 在大量资源释放后触发整理
4. 支持不同操作系统平台
"""

import os
import sys
import gc
import time
import ctypes
import logging
import threading
import platform
import psutil
import atexit
import signal
from typing import Dict, Tuple, Optional, Any

# 配置日志
logger = logging.getLogger("MemoryDefragmenter")

class MemoryDefragmenter:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存碎片整理器，负责整理和紧凑化系统内存"""
    
    def __init__(self):
        """初始化内存碎片整理器"""
        # 配置
        self.config = {
            "auto_compact_interval": 3600,    # 自动整理间隔(秒)，默认1小时
            "resource_release_threshold": 500, # 资源释放阈值(MB)，超过该值触发整理
            "post_compact_delay": 2,          # 整理后延迟(秒)
            "use_aggressive_mode": False,     # 是否使用激进模式
            "monitor_interval": 60            # 监控间隔(秒)
        }
        
        # 状态跟踪
        self.status = {
            "last_auto_compact": 0,           # 上次自动整理时间
            "last_trigger_compact": 0,        # 上次触发整理时间
            "total_compacts": 0,              # 总整理次数
            "released_since_compact": 0,      # 上次整理后释放的内存(MB)
            "is_compacting": False            # 是否正在整理
        }
        
        # 监控互斥锁
        self.lock = threading.RLock()
        
        # 启动监控线程
        self.should_stop = False
        self.monitor_thread = threading.Thread(
            target=self._run_monitor,
            daemon=True,
            name="memory-defragmenter-monitor"
        )
        self.monitor_thread.start()
        
        logger.info("内存碎片整理器初始化完成")
    
    def compact_memory(self) -> bool:
        """
        执行内存碎片整理
        
        Returns:
            bool: 是否整理成功
        """
        if self.status["is_compacting"]:
            logger.warning("内存碎片整理正在进行中，跳过本次请求")
            return False
            
        with self.lock:
            self.status["is_compacting"] = True
            
        try:
            start_time = time.time()
            logger.info("开始内存碎片整理...")
            
            # 记录整理前内存使用情况
            before_usage = self._get_memory_usage()
            
            # 1. 强制执行垃圾回收
            collected = gc.collect(generation=2)  # 完整收集
            
            # 2. 针对不同操作系统执行特定整理
            if sys.platform == 'win32':
                # Windows平台
                self._compact_windows_memory()
            elif sys.platform == 'darwin':
                # macOS平台
                self._compact_macos_memory()
            else:
                # Linux及其他平台
                self._compact_linux_memory()
            
            # 3. 再次执行垃圾回收
            gc.collect()
            
            # 记录整理后内存使用情况
            after_usage = self._get_memory_usage()
            
            # 计算减少的内存
            reduced_mb = max(0, before_usage["used_mb"] - after_usage["used_mb"])
            
            # 整理完成
            elapsed = time.time() - start_time
            logger.info(f"内存碎片整理完成，耗时: {elapsed:.2f}秒，回收对象: {collected}个，减少内存: {reduced_mb:.2f}MB")
            
            # 更新状态
            current_time = time.time()
            self.status["last_auto_compact"] = current_time
            self.status["last_trigger_compact"] = current_time
            self.status["total_compacts"] += 1
            self.status["released_since_compact"] = 0
            
            # 整理后短暂延迟，让系统稳定
            if self.config["post_compact_delay"] > 0:
                time.sleep(self.config["post_compact_delay"])
            
            return True
            
        except Exception as e:
            logger.error(f"内存碎片整理失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            self.status["is_compacting"] = False
    
    def _compact_windows_memory(self) -> None:
        """Windows平台特定的内存整理"""
        try:
            # 使用SetProcessWorkingSetSize整理内存
            # 参数(-1, 0, 0):
            # -1：当前进程
            # 0：最小工作集大小(设为0表示尽可能减小)
            # 0：最大工作集大小(设为0表示尽可能减小)
            ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, 0, 0)
            
            # 如果使用激进模式，尝试额外的技术
            if self.config["use_aggressive_mode"]:
                # 空间交换堆紧凑化
                ctypes.windll.psapi.EmptyWorkingSet(-1)
                
                # 尝试使用HEAP_COMPACT标志紧凑化堆
                try:
                    # HEAP_COMPACT = 0x00000004
                    for i in range(10):  # 对多个堆执行操作
                        handle = ctypes.windll.kernel32.GetProcessHeap()
                        if handle:
                            ctypes.windll.kernel32.HeapCompact(handle, 0x00000004)
                except:
                    pass  # 忽略错误，这是额外尝试
            
            logger.debug("Windows内存整理完成")
            
        except Exception as e:
            logger.warning(f"Windows内存整理失败: {str(e)}")
    
    def _compact_macos_memory(self) -> None:
        """macOS平台特定的内存整理"""
        try:
            # macOS特定的内存释放技术
            # 使用mach_vm系统调用
            if self.config["use_aggressive_mode"]:
                try:
                    # 尝试使用malloc_trim (可能需要安装特定库)
                    import ctypes.util
                    libc = ctypes.CDLL(ctypes.util.find_library('c'))
                    if hasattr(libc, 'malloc_trim'):
                        libc.malloc_trim(0)
                except:
                    pass
            
            logger.debug("macOS内存整理完成")
            
        except Exception as e:
            logger.warning(f"macOS内存整理失败: {str(e)}")
    
    def _compact_linux_memory(self) -> None:
        """Linux平台特定的内存整理"""
        try:
            # 使用malloc_trim释放空闲内存
            try:
                import ctypes.util
                libc = ctypes.CDLL(ctypes.util.find_library('c'))
                if hasattr(libc, 'malloc_trim'):
                    libc.malloc_trim(0)
            except:
                pass
                
            # 如果使用激进模式，使用更激进的方法
            if self.config["use_aggressive_mode"]:
                # 使用MADV_DONTNEED对大块内存进行建议
                try:
                    os.system('sync')  # 刷新文件系统缓冲区
                except:
                    pass
            
            logger.debug("Linux内存整理完成")
            
        except Exception as e:
            logger.warning(f"Linux内存整理失败: {str(e)}")
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """
        获取当前内存使用情况
        
        Returns:
            Dict: 内存使用信息
        """
        try:
            # 使用psutil获取内存信息
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            # 计算使用的物理内存(MB)
            used_mb = memory_info.rss / (1024 * 1024)
            
            # 系统内存信息
            system_memory = psutil.virtual_memory()
            system_total_mb = system_memory.total / (1024 * 1024)
            system_available_mb = system_memory.available / (1024 * 1024)
            
            return {
                "used_mb": used_mb,
                "system_total_mb": system_total_mb,
                "system_available_mb": system_available_mb,
                "percent": used_mb / system_total_mb * 100 if system_total_mb > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"获取内存使用信息失败: {str(e)}")
            return {
                "used_mb": 0,
                "system_total_mb": 0,
                "system_available_mb": 0,
                "percent": 0
            }
    
    def _run_monitor(self) -> None:
        """内存监控线程函数"""
        monitor_interval = self.config["monitor_interval"]
        auto_compact_interval = self.config["auto_compact_interval"]
        
        while not self.should_stop:
            try:
                current_time = time.time()
                
                # 检查是否需要自动整理
                if (auto_compact_interval > 0 and 
                    current_time - self.status["last_auto_compact"] >= auto_compact_interval):
                    logger.info("定时触发内存碎片整理")
                    self.compact_memory()
                
                # 检查是否由于大量资源释放而需要整理
                if (self.status["released_since_compact"] >= self.config["resource_release_threshold"] and
                    current_time - self.status["last_trigger_compact"] >= 60):  # 至少间隔1分钟
                    logger.info(f"大量资源释放({self.status['released_since_compact']}MB)触发内存碎片整理")
                    self.compact_memory()
                
                # 休眠
                time.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"内存监控线程异常: {str(e)}")
                time.sleep(monitor_interval)
    
    def update_config(self, new_config: Dict[str, any]) -> None:
        """
        更新配置
        
        Args:
            new_config: 新配置
        """
        with self.lock:
            # 更新配置
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
                    
            logger.info(f"已更新内存碎片整理器配置: {new_config}")
    
    def notify_resource_released(self, size_mb: float) -> None:
        """
        通知有资源被释放
        
        Args:
            size_mb: 释放的资源大小(MB)
        """
        with self.lock:
            self.status["released_since_compact"] += size_mb
    
    def get_status(self) -> Dict[str, any]:
        """
        获取内存碎片整理器状态
        
        Returns:
            Dict: 状态信息
        """
        with self.lock:
            # 获取当前内存使用情况
            memory_usage = self._get_memory_usage()
            
            # 复制状态并添加内存使用信息
            status = dict(self.status)
            status.update({
                "memory_usage": memory_usage,
                "config": dict(self.config)
            })
            
            return status
    
    def stop(self) -> None:
        """停止监控线程"""
        self.should_stop = True
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            logger.info("内存碎片整理器监控线程已停止")
    
    def __del__(self):
        """析构函数"""
        self.stop()


# 内存碎片整理函数(便捷接口)
def compact_memory() -> bool:
    """
    整理内存碎片(便捷函数)
    
    执行内存碎片整理以优化内存使用，减少内存占用。
    在大量资源释放后或长时间运行后调用此函数可以显著提高系统稳定性。
    
    Returns:
        bool: 是否成功整理
    """
    # 获取碎片整理器实例并执行整理
    defragmenter = get_memory_defragmenter()
    return defragmenter.compact_memory()


# 单例模式
_memory_defragmenter = None

def get_memory_defragmenter() -> MemoryDefragmenter:
    """获取内存碎片整理器单例"""
    global _memory_defragmenter
    if _memory_defragmenter is None:
        _memory_defragmenter = MemoryDefragmenter()
    return _memory_defragmenter


# 注册退出处理函数，确保在应用程序退出时正确关闭碎片整理器
def register_shutdown_handler() -> None:
    """
    注册退出处理函数，确保在应用程序退出时正确关闭碎片整理器
    """
    global _memory_defragmenter
    
    def _cleanup():
        """退出时清理资源"""
        if _memory_defragmenter is not None:
            logger.info("应用程序退出，停止内存碎片整理器...")
            _memory_defragmenter.stop()
    
    # 注册atexit处理函数
    atexit.register(_cleanup)
    
    # 注册信号处理函数(在Linux/macOS上)
    if sys.platform != 'win32':
        try:
            # 注册SIGTERM信号处理
            signal.signal(signal.SIGTERM, lambda sig, frame: _cleanup())
            # 注册SIGINT信号处理
            signal.signal(signal.SIGINT, lambda sig, frame: _cleanup())
        except Exception as e:
            logger.warning(f"注册信号处理函数失败: {str(e)}")


# 在模块导入时自动注册退出处理函数
register_shutdown_handler()


# 直接执行时的测试代码
if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试内存碎片整理
    print("===== 内存碎片整理测试 =====")
    
    # 分配一些内存用于测试
    print("分配测试内存...")
    test_data = []
    for i in range(10):
        # 每次分配约10MB
        data = [0] * (10 * 1024 * 1024 // 8)  # 约10MB
        test_data.append(data)
        print(f"已分配 {(i+1)*10}MB 测试内存")
    
    # 显示内存使用情况
    defragmenter = get_memory_defragmenter()
    memory_before = defragmenter._get_memory_usage()
    print(f"\n整理前内存使用: {memory_before['used_mb']:.2f}MB")
    
    # 释放部分内存
    print("\n释放部分测试内存...")
    for i in range(5):
        test_data[i] = None
    
    # 执行内存碎片整理
    print("\n执行内存碎片整理...")
    defragmenter.compact_memory()
    
    # 再次显示内存使用情况
    memory_after = defragmenter._get_memory_usage()
    print(f"\n整理后内存使用: {memory_after['used_mb']:.2f}MB")
    print(f"内存减少: {max(0, memory_before['used_mb'] - memory_after['used_mb']):.2f}MB")
    
    print("\n内存碎片整理测试完成!")

def defragment_memory(threshold_mb: float = 50.0, aggressive: bool = False) -> Dict[str, Any]:
    """
    执行内存碎片整理
    
    Args:
        threshold_mb: 触发碎片整理的阈值(MB)
        aggressive: 是否执行激进的碎片整理
        
    Returns:
        Dict: 碎片整理结果信息
    """
    start_time = time.time()
    # 记录初始状态
    initial_objects = len(gc.get_objects())
    
    # 触发完整的垃圾回收
    gc.collect(0)  # 收集第0代（最新的对象）
    gc.collect(1)  # 收集第1代
    gc.collect(2)  # 收集第2代（最老的对象）
    
    if aggressive:
        # 在激进模式下，再次执行一次完整收集
        gc.collect()
        
    # 计算结果
    end_time = time.time()
    final_objects = len(gc.get_objects())
    objects_freed = initial_objects - final_objects
    duration = end_time - start_time
    
    result = {
        "initial_objects": initial_objects,
        "final_objects": final_objects,
        "objects_freed": objects_freed,
        "duration_seconds": duration,
        "aggressive_mode": aggressive
    }
    
    logger.info(f"内存碎片整理完成: 释放了{objects_freed}个对象, 耗时{duration:.2f}秒")
    return result 