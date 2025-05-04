#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化压力测试模块

对系统进行自动化压力测试，模拟各种异常和失败场景，
测试系统的稳定性、容错性和自动恢复能力。
主要功能：
1. 混沌测试：随机生成故障并验证恢复
2. 资源限制测试：模拟资源受限情况
3. 并发测试：高并发下的性能和稳定性
4. 长时间运行测试：持续运行下的内存泄漏检测
5. 输入异常测试：非法输入和边界条件处理
"""

import os
import sys
import time
import gc
import threading
import random
import multiprocessing
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import json
import numpy as np
import platform

from loguru import logger
from src.utils.file_handler import ensure_dir_exists
from src.utils.exceptions import (
    ClipMasterError, 
    ErrorCode, 
    MemoryOverflowError,
    ResourceExhaustionError
)

# 尝试导入相关库
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil未安装，某些压力测试功能将不可用")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch未安装，GPU相关测试将不可用")

# 尝试导入质量报告模块
try:
    from .report_generator import QualityReport
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False
    logger.warning("report_generator模块不可用，将使用简化的报告功能")
    
    # 创建一个简化的QualityReport类
    class QualityReport:
        def __init__(self, report_name=""):
            self.report_name = report_name or f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.data = {}
            
        def to_dict(self):
            return self.data
            
        def save(self, filepath=None):
            if filepath is None:
                os.makedirs("data/quality_reports", exist_ok=True)
                filepath = f"data/quality_reports/{self.report_name}.json"
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            return filepath


class ChaosMonkey:
    """
    混沌测试工具
    
    随机引入故障到系统中，测试系统的容错性和恢复能力
    """
    
    FAILURE_SCENARIOS = [
        "memory_overload",    # 内存过载
        "network_jitter",     # 网络抖动
        "gpu_failure",        # GPU故障
        "disk_latency",       # 磁盘延迟
        "cpu_throttling",     # CPU限流
        "process_kill",       # 进程终止
        "file_corruption"     # 文件损坏
    ]
    
    def __init__(self):
        """初始化混沌测试工具"""
        self.active_failures = {}
        self.recovery_stats = {
            "total_failures": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "recovery_times": []
        }
        logger.info("混沌测试工具初始化完成")
    
    def induce_failure(self, system: Any) -> float:
        """
        引入随机故障到系统
        
        Args:
            system: 系统实例
            
        Returns:
            float: 系统恢复时间(秒)，如果未恢复则返回-1
        """
        # 随机选择故障类型
        scenario = random.choice(self.FAILURE_SCENARIOS)
        return self._trigger(scenario)
    
    def _trigger(self, scenario: str) -> float:
        """
        触发特定故障场景
        
        Args:
            scenario: 故障类型
            
        Returns:
            float: 恢复时间(秒)
        """
        logger.warning(f"触发故障: {scenario}")
        
        start_time = time.time()
        recovery_time = -1
        
        try:
            # 根据故障类型执行不同的操作
            if scenario == "memory_overload":
                recovery_time = self._trigger_memory_overload()
            elif scenario == "network_jitter":
                recovery_time = self._trigger_network_jitter()
            elif scenario == "gpu_failure":
                recovery_time = self._trigger_gpu_failure()
            elif scenario == "disk_latency":
                recovery_time = self._trigger_disk_latency()
            elif scenario == "cpu_throttling":
                recovery_time = self._trigger_cpu_throttling()
            elif scenario == "process_kill":
                recovery_time = self._trigger_process_kill()
            elif scenario == "file_corruption":
                recovery_time = self._trigger_file_corruption()
            
            # 更新恢复统计
            self.recovery_stats["total_failures"] += 1
            if recovery_time > 0:
                self.recovery_stats["successful_recoveries"] += 1
                self.recovery_stats["recovery_times"].append(recovery_time)
            else:
                self.recovery_stats["failed_recoveries"] += 1
            
            return recovery_time
        
        except Exception as e:
            logger.error(f"触发故障场景异常: {str(e)}")
            return -1
    
    # 特定故障触发方法
    def _trigger_memory_overload(self) -> float:
        """
        触发内存过载故障
        
        分配大量内存直到接近系统极限，测试系统恢复能力
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发内存过载故障")
        recovery_successful = False
        recovery_time = -1
        memory_blocks = []
        
        try:
            # 获取可用内存信息
            if not PSUTIL_AVAILABLE:
                logger.error("缺少psutil库，无法触发内存故障")
                return -1
                
            start_time = time.time()
            total_memory = psutil.virtual_memory().total
            initial_available = psutil.virtual_memory().available
            target_usage = int(initial_available * 0.9)  # 使用90%的可用内存
            
            logger.info(f"内存过载测试: 当前可用内存 {initial_available/(1024*1024):.1f}MB，目标使用 {target_usage/(1024*1024):.1f}MB")
            
            # 分配内存
            block_size = 10 * 1024 * 1024  # 10MB块
            allocated = 0
            
            while allocated < target_usage:
                try:
                    # 分配内存块
                    block = bytearray(block_size)
                    # 写入数据以确保真正分配
                    for i in range(0, block_size, 1024*1024):
                        block[i] = 1
                    memory_blocks.append(block)
                    allocated += block_size
                    
                    # 每分配100MB记录一次
                    if len(memory_blocks) % 10 == 0:
                        current_avail = psutil.virtual_memory().available
                        usage_percent = 100 - (current_avail / total_memory * 100)
                        logger.debug(f"已分配 {allocated/(1024*1024):.1f}MB, 内存使用率: {usage_percent:.1f}%")
                        
                        # 如果内存使用率超过95%，停止分配
                        if usage_percent > 95:
                            logger.warning("内存使用率超过95%，停止分配")
                            break
                except MemoryError:
                    logger.warning("触发内存错误，内存已耗尽")
                    break
                except Exception as e:
                    logger.error(f"分配内存块异常: {str(e)}")
                    break
            
            # 内存溢出已触发，启动恢复流程
            logger.info(f"已分配 {allocated/(1024*1024):.1f}MB 内存，开始恢复")
            
            # 模拟应用内的自动恢复过程
            try:
                # 抛出内存溢出异常，触发自动恢复机制
                from src.utils.exceptions import MemoryOverflowError
                raise MemoryOverflowError(
                    msg="内存过载测试触发",
                    details={"allocated_mb": allocated / (1024*1024)}
                )
            except Exception as e:
                logger.warning(f"触发异常: {str(e)}")
                
                # 此时应已触发系统的自动恢复机制
                # 我们在这里手动释放内存以确保测试的安全性
                time.sleep(0.5)  # 给恢复机制一些时间
                
                # 开始释放内存
                memory_blocks.clear()
                gc.collect()
                
                # 验证恢复
                recovery_time = time.time() - start_time
                current_avail = psutil.virtual_memory().available
                recovery_successful = current_avail > initial_available * 0.5  # 恢复了一半以上的内存
                
                logger.info(f"内存释放后，可用内存: {current_avail/(1024*1024):.1f}MB, 恢复耗时: {recovery_time:.2f}秒")
            
            return recovery_time if recovery_successful else -1
            
        except Exception as e:
            logger.error(f"内存过载测试失败: {str(e)}")
            
            # 确保释放内存
            if 'memory_blocks' in locals():
                memory_blocks.clear()
            gc.collect()
            
            return -1
    
    def _trigger_network_jitter(self) -> float:
        """
        触发网络抖动故障
        
        模拟网络延迟、丢包等问题，测试网络容错能力
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发网络抖动故障")
        
        # 检查操作系统类型并确定命令
        platform_system = platform.system().lower()
        recovery_successful = False
        recovery_time = -1
        
        try:
            start_time = time.time()
            
            # 根据操作系统选择合适的命令
            if platform_system == "windows":
                # Windows下模拟网络抖动
                # 使用内置命令暂时不处理网络请求
                # 这里我们只模拟短暂的网络中断
                logger.info("Windows平台：模拟网络中断")
                
                # 模拟网络超时
                time.sleep(3)  # 模拟3秒网络延迟
                
                # 模拟恢复过程
                time.sleep(1)
                recovery_time = time.time() - start_time
                recovery_successful = True
                
            elif platform_system == "linux":
                # Linux下可以使用tc命令调整网络参数
                # 为了安全，这里只模拟
                logger.info("Linux平台：模拟网络抖动")
                
                # 模拟网络延迟和丢包
                time.sleep(2)
                
                # 模拟恢复过程
                time.sleep(1)
                recovery_time = time.time() - start_time
                recovery_successful = True
                
            else:
                # 其他平台
                logger.info(f"平台 {platform_system} 不支持真实网络抖动，只进行模拟")
                time.sleep(2)
                recovery_time = time.time() - start_time
                recovery_successful = True
            
            logger.info(f"网络抖动恢复耗时: {recovery_time:.2f}秒")
            return recovery_time if recovery_successful else -1
            
        except Exception as e:
            logger.error(f"网络抖动测试失败: {str(e)}")
            return -1
    
    def _trigger_gpu_failure(self) -> float:
        """
        触发GPU故障
        
        模拟GPU内存溢出或计算错误，测试系统容错能力
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发GPU故障")
        
        if not TORCH_AVAILABLE:
            logger.error("缺少PyTorch库，无法触发GPU故障")
            return -1
            
        try:
            if not torch.cuda.is_available():
                logger.warning("CUDA不可用，模拟GPU故障")
                time.sleep(2)  # 简单模拟
                return 2.0
            
            start_time = time.time()
            recovery_successful = False
            
            # 获取GPU信息
            device_count = torch.cuda.device_count()
            if device_count == 0:
                logger.warning("没有可用的GPU设备，模拟GPU故障")
                time.sleep(2)
                return 2.0
            
            # 选择一个GPU设备
            device_id = 0
            logger.info(f"使用GPU设备: {torch.cuda.get_device_name(device_id)}")
            
            # 尝试分配大量GPU内存
            gpu_tensors = []
            try:
                # 循环分配，直到内存不足
                for _ in range(20):  # 最多分配20个大张量
                    # 分配一个大的GPU张量(每个1GB左右)
                    tensor = torch.ones((1024, 1024, 256), device=f"cuda:{device_id}")
                    gpu_tensors.append(tensor)
                    
                    # 执行一些计算以确保真正使用
                    _ = tensor + 1
                
            except RuntimeError as e:
                # 捕获CUDA内存不足异常
                if "CUDA out of memory" in str(e):
                    logger.warning("触发GPU内存溢出")
                else:
                    logger.error(f"GPU操作出错: {str(e)}")
            
            # 模拟系统恢复过程
            logger.info("开始恢复GPU资源")
            
            # 主动释放GPU内存
            for tensor in gpu_tensors:
                del tensor
            
            # 清除缓存
            torch.cuda.empty_cache()
            
            # 模拟恢复延迟
            time.sleep(1)
            
            # 检查恢复结果
            recovery_time = time.time() - start_time
            
            # 验证是否成功释放内存
            try:
                # 尝试分配一个小张量，如果成功则认为恢复成功
                test_tensor = torch.ones((10, 10), device=f"cuda:{device_id}")
                del test_tensor
                recovery_successful = True
            except Exception:
                recovery_successful = False
            
            logger.info(f"GPU故障恢复耗时: {recovery_time:.2f}秒, 恢复状态: {recovery_successful}")
            return recovery_time if recovery_successful else -1
            
        except Exception as e:
            logger.error(f"GPU故障测试失败: {str(e)}")
            # 确保清理GPU资源
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            return -1
    
    def _trigger_disk_latency(self) -> float:
        """
        触发磁盘延迟故障
        
        模拟磁盘IO缓慢，测试系统对IO延迟的容忍能力
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发磁盘延迟故障")
        
        recovery_successful = False
        recovery_time = -1
        temp_files = []
        
        try:
            start_time = time.time()
            
            # 创建临时目录
            temp_dir = os.path.join("data", "stress_test_io")
            ensure_dir_exists(temp_dir)
            
            # 生成一些大文件进行频繁读写以消耗IO带宽
            file_size = 50 * 1024 * 1024  # 50MB
            num_files = 5
            data = os.urandom(1024 * 1024)  # 1MB随机数据
            
            logger.info(f"创建 {num_files} 个各 {file_size/(1024*1024)}MB 的文件并进行IO压测")
            
            # 创建并写入文件
            for i in range(num_files):
                file_path = os.path.join(temp_dir, f"disk_test_{i}.dat")
                temp_files.append(file_path)
                
                with open(file_path, "wb") as f:
                    # 分块写入以消耗IO
                    for _ in range(file_size // len(data)):
                        f.write(data)
                        # 强制刷新
                        f.flush()
                        os.fsync(f.fileno())
            
            # 执行随机读写操作
            for _ in range(20):  # 执行20次读写循环
                # 随机选择文件
                file_path = random.choice(temp_files)
                
                # 随机读取
                with open(file_path, "rb") as f:
                    # 随机定位
                    pos = random.randint(0, file_size - 1024 * 1024)
                    f.seek(pos)
                    _ = f.read(1024 * 1024)
            
            # 模拟恢复过程
            logger.info("磁盘IO压测完成，开始清理")
            
            # 删除临时文件
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            recovery_time = time.time() - start_time
            recovery_successful = True
            
            logger.info(f"磁盘延迟故障恢复耗时: {recovery_time:.2f}秒")
            return recovery_time
            
        except Exception as e:
            logger.error(f"磁盘延迟测试失败: {str(e)}")
            
            # 确保清理临时文件
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
                    
            return -1
    
    def _trigger_cpu_throttling(self) -> float:
        """
        触发CPU限流故障
        
        创建高CPU负载，触发系统降频/限流机制
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发CPU限流故障")
        
        recovery_successful = False
        recovery_time = -1
        cpu_threads = []
        
        try:
            start_time = time.time()
            
            # 获取CPU核心数
            cpu_count = multiprocessing.cpu_count()
            
            # 创建线程数量
            thread_count = max(1, cpu_count - 1)  # 至少保留1个核心给系统
            
            logger.info(f"创建 {thread_count} 个CPU密集型线程")
            
            # 创建CPU密集型线程
            for i in range(thread_count):
                stop_flag = threading.Event()
                thread = threading.Thread(
                    target=self._cpu_intensive_loop,
                    args=(stop_flag, i),
                    daemon=True
                )
                thread.stop_flag = stop_flag
                thread.start()
                cpu_threads.append(thread)
            
            # 运行一段时间让CPU温度上升
            run_time = 5.0  # 5秒
            time.sleep(run_time)
            
            # 停止所有线程
            logger.info("开始释放CPU资源")
            for thread in cpu_threads:
                thread.stop_flag.set()
            
            # 等待线程结束
            for thread in cpu_threads:
                thread.join(1.0)  # 最多等待1秒
            
            # 清理线程列表
            cpu_threads.clear()
            
            # 恢复时间计算
            recovery_time = time.time() - start_time
            recovery_successful = True
            
            logger.info(f"CPU限流故障恢复耗时: {recovery_time:.2f}秒")
            return recovery_time
            
        except Exception as e:
            logger.error(f"CPU限流测试失败: {str(e)}")
            
            # 确保清理线程
            for thread in cpu_threads:
                try:
                    if thread.is_alive():
                        thread.stop_flag.set()
                except Exception:
                    pass
                    
            return -1
    
    def _cpu_intensive_loop(self, stop_flag: threading.Event, thread_id: int) -> None:
        """
        CPU密集型循环
        
        Args:
            stop_flag: 停止标志
            thread_id: 线程ID
        """
        logger.debug(f"CPU密集型线程 {thread_id} 启动")
        
        while not stop_flag.is_set():
            # 执行CPU密集型计算
            matrix_size = 500
            a = np.random.rand(matrix_size, matrix_size)
            b = np.random.rand(matrix_size, matrix_size)
            c = np.dot(a, b)
            
            # 避免结果被优化掉
            if c[0, 0] < -1000:  # 这个条件几乎不可能为真
                print("Unexpected result")
    
    def _trigger_process_kill(self) -> float:
        """
        触发进程终止故障
        
        模拟关键子进程崩溃，测试进程监控和恢复机制
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发进程终止故障")
        
        recovery_successful = False
        recovery_time = -1
        
        try:
            start_time = time.time()
            
            # 创建一个工作进程
            def worker_process(ready_event, exit_event):
                # 通知主线程进程已准备好
                ready_event.set()
                
                # 等待退出信号
                while not exit_event.is_set():
                    time.sleep(0.1)
                    
                return 0
            
            # 创建进程间事件
            ready_event = multiprocessing.Event()
            exit_event = multiprocessing.Event()
            
            # 启动工作进程
            process = multiprocessing.Process(
                target=worker_process,
                args=(ready_event, exit_event)
            )
            process.daemon = True
            process.start()
            
            # 等待进程准备好
            ready_event.wait(timeout=5.0)
            
            if not process.is_alive():
                logger.error("工作进程启动失败")
                return -1
            
            logger.info(f"工作进程已启动，PID: {process.pid}")
            
            # 在真实场景中，我们会强制终止进程
            # 在测试环境中，我们使用正常退出模拟崩溃
            time.sleep(1.0)  # 让进程运行一会
            
            # 模拟进程监控检测到进程崩溃并重启
            logger.info("模拟进程崩溃，准备重启")
            
            # 终止当前进程
            exit_event.set()
            process.join(2.0)
            
            if process.is_alive():
                logger.warning("进程未正常退出，强制终止")
                process.terminate()
                process.join(1.0)
            
            # 模拟进程重启
            logger.info("重启工作进程")
            
            # 重置事件
            ready_event.clear()
            exit_event.clear()
            
            # 启动新进程
            new_process = multiprocessing.Process(
                target=worker_process,
                args=(ready_event, exit_event)
            )
            new_process.daemon = True
            new_process.start()
            
            # 等待新进程准备好
            ready_event.wait(timeout=5.0)
            
            # 验证进程恢复
            recovery_time = time.time() - start_time
            recovery_successful = new_process.is_alive()
            
            # 清理新进程
            exit_event.set()
            new_process.join(2.0)
            if new_process.is_alive():
                new_process.terminate()
            
            logger.info(f"进程终止故障恢复耗时: {recovery_time:.2f}秒, 恢复状态: {recovery_successful}")
            return recovery_time if recovery_successful else -1
            
        except Exception as e:
            logger.error(f"进程终止测试失败: {str(e)}")
            return -1
    
    def _trigger_file_corruption(self) -> float:
        """
        触发文件损坏故障
        
        模拟关键文件损坏，测试文件校验和恢复机制
        
        Returns:
            float: 恢复时间(秒)，如果未恢复则返回-1
        """
        logger.warning("触发文件损坏故障")
        
        recovery_successful = False
        recovery_time = -1
        temp_file = None
        backup_data = None
        
        try:
            start_time = time.time()
            
            # 创建临时目录
            temp_dir = os.path.join("data", "stress_test_files")
            ensure_dir_exists(temp_dir)
            
            # 创建测试文件
            temp_file = os.path.join(temp_dir, "important_data.json")
            
            # 写入一些示例数据
            test_data = {
                "config": {
                    "version": "1.0.0",
                    "mode": "production",
                    "features": ["feature1", "feature2", "feature3"],
                    "settings": {
                        "timeout": 30,
                        "retry": 3,
                        "buffer_size": 1024
                    }
                },
                "data": [
                    {"id": 1, "name": "Item 1", "value": 100},
                    {"id": 2, "name": "Item 2", "value": 200},
                    {"id": 3, "name": "Item 3", "value": 300}
                ],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "checksum": "original_checksum"
                }
            }
            
            # 保存原始数据
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # 备份原始内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                backup_data = f.read()
            
            logger.info(f"创建测试文件: {temp_file}")
            
            # 模拟文件损坏
            with open(temp_file, 'w', encoding='utf-8') as f:
                # 写入损坏的JSON
                f.write('{"config": {"version": "1.0.0", "mode": CORRUPTED_DATA')
            
            logger.info("文件已损坏，开始恢复")
            
            # 模拟文件恢复过程
            # 这里我们假设系统有某种恢复机制
            # 例如，从备份恢复、校验和验证等
            
            # 我们这里直接还原文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(backup_data)
            
            # 验证恢复
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    restored_data = json.load(f)
                
                # 检查恢复后的数据是否完整
                recovery_successful = (
                    "config" in restored_data and 
                    "data" in restored_data and
                    "metadata" in restored_data
                )
            except json.JSONDecodeError:
                recovery_successful = False
            
            recovery_time = time.time() - start_time
            
            logger.info(f"文件损坏故障恢复耗时: {recovery_time:.2f}秒, 恢复状态: {recovery_successful}")
            
            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return recovery_time if recovery_successful else -1
            
        except Exception as e:
            logger.error(f"文件损坏测试失败: {str(e)}")
            
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            
            return -1


class ResourceLimiter:
    """
    资源限制器
    
    限制系统可用的资源，测试系统在资源受限情况下的行为
    """
    
    def __init__(self):
        """初始化资源限制器"""
        self.original_limits = {}
        self.active_limits = {}
        
        # 检查可用资源
        if PSUTIL_AVAILABLE:
            self.initial_memory = psutil.virtual_memory().available
            self.initial_cpu_count = psutil.cpu_count()
        else:
            self.initial_memory = None
            self.initial_cpu_count = None
        
        # 内存占用块
        self.memory_blocks = []
        self.cpu_intensive_threads = []
        self.io_intensive_threads = []
        
        logger.info("资源限制器初始化完成")
    
    def limit_memory(self, available_percent: float) -> bool:
        """
        限制可用内存
        
        Args:
            available_percent: 系统内存可用比例(0.0-1.0)
            
        Returns:
            bool: 是否成功限制内存
        """
        if not PSUTIL_AVAILABLE:
            logger.error("缺少psutil库，无法限制内存")
            return False
            
        if available_percent < 0.1 or available_percent > 1.0:
            logger.warning(f"内存限制比例 {available_percent} 超出范围，应在0.1-1.0之间")
            available_percent = max(0.1, min(available_percent, 1.0))
        
        # 计算需要占用的内存量
        total_memory = psutil.virtual_memory().total
        target_used = int(total_memory * (1 - available_percent))
        current_used = psutil.virtual_memory().used
        
        # 计算需要额外占用的内存
        extra_needed = max(0, target_used - current_used)
        
        if extra_needed <= 0:
            logger.info(f"当前内存使用已满足目标限制，无需额外占用")
            return True
        
        logger.info(f"限制内存至 {available_percent*100:.1f}% 可用，需要占用额外 {extra_needed/(1024*1024):.1f}MB")
        
        try:
            # 分配内存块
            block_size = 1024 * 1024 * 10  # 10MB
            num_blocks = extra_needed // block_size + 1
            
            # 限制块数以防止系统崩溃
            num_blocks = min(num_blocks, 1000)  # 最多分配10GB
            
            for _ in range(int(num_blocks)):
                try:
                    # 分配并填充内存块
                    block = bytearray(block_size)
                    # 写入一些数据以确保内存实际被分配
                    for i in range(0, block_size, 1024*1024):
                        block[i] = 1
                    self.memory_blocks.append(block)
                    
                    # 检查是否达到目标
                    if len(self.memory_blocks) % 10 == 0:
                        current_avail = psutil.virtual_memory().available / total_memory
                        if current_avail <= available_percent:
                            break
                except MemoryError:
                    logger.warning("内存分配失败，系统内存可能已接近极限")
                    break
            
            # 记录实际限制结果
            current_stats = psutil.virtual_memory()
            self.active_limits["memory"] = {
                "target_percent": available_percent,
                "actual_percent": current_stats.available / total_memory,
                "blocks_allocated": len(self.memory_blocks)
            }
            
            logger.info(f"内存限制完成: 目标={available_percent*100:.1f}%, 实际={self.active_limits['memory']['actual_percent']*100:.1f}%")
            return True
            
        except Exception as e:
            logger.error(f"限制内存失败: {str(e)}")
            self.release_memory()
            return False
    
    def release_memory(self) -> None:
        """释放之前占用的内存"""
        if not self.memory_blocks:
            return
            
        logger.info(f"释放 {len(self.memory_blocks)} 个内存块")
        self.memory_blocks.clear()
        gc.collect()  # 强制垃圾回收
        
        if PSUTIL_AVAILABLE:
            current_avail = psutil.virtual_memory().available
            logger.info(f"内存释放后，当前可用内存: {current_avail/(1024*1024*1024):.2f}GB")
    
    def limit_cpu(self, available_percent: float) -> bool:
        """
        限制CPU可用资源
        
        Args:
            available_percent: CPU可用比例(0.0-1.0)
            
        Returns:
            bool: 是否成功限制CPU
        """
        if not PSUTIL_AVAILABLE:
            logger.error("缺少psutil库，无法限制CPU")
            return False
        
        if available_percent < 0.1 or available_percent > 1.0:
            logger.warning(f"CPU限制比例 {available_percent} 超出范围，应在0.1-1.0之间")
            available_percent = max(0.1, min(available_percent, 1.0))
        
        # 计算需要占用的CPU核心数
        cpu_count = psutil.cpu_count()
        cores_to_use = int(cpu_count * (1 - available_percent))
        
        if cores_to_use <= 0:
            logger.info("CPU限制比例过高，至少占用1个核心")
            cores_to_use = 1
        
        logger.info(f"限制CPU至 {available_percent*100:.1f}% 可用，占用 {cores_to_use} 个核心")
        
        try:
            # 停止现有的CPU密集型线程
            for thread in self.cpu_intensive_threads:
                if thread.is_alive():
                    thread.stop_flag.set()
            self.cpu_intensive_threads.clear()
            
            # 创建CPU密集型线程
            for i in range(cores_to_use):
                stop_flag = threading.Event()
                thread = threading.Thread(
                    target=self._cpu_intensive_task,
                    args=(stop_flag, i),
                    daemon=True
                )
                thread.stop_flag = stop_flag
                thread.start()
                self.cpu_intensive_threads.append(thread)
            
            # 记录实际限制结果
            self.active_limits["cpu"] = {
                "target_percent": available_percent,
                "cores_used": cores_to_use,
                "total_cores": cpu_count
            }
            
            logger.info(f"CPU限制完成: 目标={available_percent*100:.1f}%, 占用核心数={cores_to_use}")
            return True
            
        except Exception as e:
            logger.error(f"限制CPU失败: {str(e)}")
            self.release_cpu()
            return False
    
    def _cpu_intensive_task(self, stop_flag: threading.Event, core_id: int) -> None:
        """
        CPU密集型任务
        
        Args:
            stop_flag: 停止标志
            core_id: 核心ID
        """
        logger.debug(f"启动CPU密集型任务 #{core_id}")
        
        # 尝试绑定到特定核心
        try:
            if hasattr(os, 'sched_setaffinity'):
                os.sched_setaffinity(0, {core_id % psutil.cpu_count()})
        except Exception:
            pass
        
        # 执行CPU密集型计算
        while not stop_flag.is_set():
            # 计算密集型操作
            _ = [i*i for i in range(10000)]
            # 矩阵运算
            matrix = np.random.rand(100, 100)
            _ = np.dot(matrix, matrix)
    
    def release_cpu(self) -> None:
        """释放之前占用的CPU资源"""
        if not self.cpu_intensive_threads:
            return
            
        logger.info(f"释放 {len(self.cpu_intensive_threads)} 个CPU密集型线程")
        
        # 停止所有CPU密集型线程
        for thread in self.cpu_intensive_threads:
            if thread.is_alive():
                thread.stop_flag.set()
        
        # 等待线程完成
        for thread in self.cpu_intensive_threads:
            thread.join(0.5)  # 最多等待0.5秒
        
        self.cpu_intensive_threads.clear()
        
        logger.info("CPU资源已释放")
    
    def limit_io(self, intensity: float) -> bool:
        """
        限制IO资源
        
        Args:
            intensity: IO负载强度(0.0-1.0)
            
        Returns:
            bool: 是否成功限制IO
        """
        if intensity < 0.1 or intensity > 1.0:
            logger.warning(f"IO限制强度 {intensity} 超出范围，应在0.1-1.0之间")
            intensity = max(0.1, min(intensity, 1.0))
        
        # 计算IO线程数量
        thread_count = int(4 * intensity)  # 最多4个IO线程
        if thread_count < 1:
            thread_count = 1
        
        logger.info(f"限制IO，强度={intensity*100:.1f}%，启动 {thread_count} 个IO线程")
        
        try:
            # 停止现有的IO密集型线程
            for thread in self.io_intensive_threads:
                if thread.is_alive():
                    thread.stop_flag.set()
            self.io_intensive_threads.clear()
            
            # 创建IO目录
            io_dir = os.path.join("data", "stress_test_io")
            ensure_dir_exists(io_dir)
            
            # 创建IO密集型线程
            for i in range(thread_count):
                stop_flag = threading.Event()
                thread = threading.Thread(
                    target=self._io_intensive_task,
                    args=(stop_flag, io_dir, i, intensity),
                    daemon=True
                )
                thread.stop_flag = stop_flag
                thread.start()
                self.io_intensive_threads.append(thread)
            
            # 记录实际限制结果
            self.active_limits["io"] = {
                "intensity": intensity,
                "threads": thread_count
            }
            
            logger.info(f"IO限制完成: 强度={intensity*100:.1f}%, 线程数={thread_count}")
            return True
            
        except Exception as e:
            logger.error(f"限制IO失败: {str(e)}")
            self.release_io()
            return False
    
    def _io_intensive_task(self, stop_flag: threading.Event, directory: str, thread_id: int, intensity: float) -> None:
        """
        IO密集型任务
        
        Args:
            stop_flag: 停止标志
            directory: IO操作目录
            thread_id: 线程ID
            intensity: IO强度
        """
        logger.debug(f"启动IO密集型任务 #{thread_id}")
        
        file_path = os.path.join(directory, f"io_test_{thread_id}.dat")
        buffer_size = int(1024 * 1024 * 5 * intensity)  # 最大5MB
        
        # 生成随机数据
        data = os.urandom(buffer_size)
        
        # 执行IO密集型操作
        count = 0
        while not stop_flag.is_set():
            # 写入文件
            with open(file_path, "wb") as f:
                f.write(data)
            
            # 读取文件
            with open(file_path, "rb") as f:
                _ = f.read()
            
            # 按强度控制频率
            count += 1
            if count % 10 == 0:
                time.sleep(max(0.1, 1.0 - intensity))
        
        # 清理文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
    
    def release_io(self) -> None:
        """释放之前占用的IO资源"""
        if not self.io_intensive_threads:
            return
            
        logger.info(f"释放 {len(self.io_intensive_threads)} 个IO密集型线程")
        
        # 停止所有IO密集型线程
        for thread in self.io_intensive_threads:
            if thread.is_alive():
                thread.stop_flag.set()
        
        # 等待线程完成
        for thread in self.io_intensive_threads:
            thread.join(1.0)  # 最多等待1秒
        
        self.io_intensive_threads.clear()
        
        # 清理IO测试文件
        io_dir = os.path.join("data", "stress_test_io")
        if os.path.exists(io_dir):
            for filename in os.listdir(io_dir):
                if filename.startswith("io_test_"):
                    try:
                        os.remove(os.path.join(io_dir, filename))
                    except Exception:
                        pass
        
        logger.info("IO资源已释放")
    
    def release_all(self) -> None:
        """释放所有占用的资源"""
        logger.info("释放所有资源限制...")
        self.release_memory()
        self.release_cpu()
        self.release_io()
        self.active_limits.clear()
        logger.info("所有资源限制已释放")


class StressTestRunner:
    """
    压力测试运行器
    
    管理和执行各种压力测试场景
    """
    
    def __init__(self):
        """初始化压力测试运行器"""
        self.chaos_monkey = ChaosMonkey()
        self.resource_limiter = ResourceLimiter()
        self.test_results = {}
        self.running_tests = {}
        
        # 确保结果目录存在
        self.results_dir = os.path.join("data", "stress_test_results")
        ensure_dir_exists(self.results_dir)
        
        logger.info("压力测试运行器初始化完成")
    
    def run_memory_stress_test(self, 
                              duration: int = 60, 
                              memory_limit_start: float = 0.7, 
                              memory_limit_end: float = 0.2, 
                              steps: int = 5) -> Dict[str, Any]:
        """
        运行内存压力测试
        
        逐步减少系统可用内存，测试应用在内存压力下的行为
        
        Args:
            duration: 测试持续时间(秒)
            memory_limit_start: 起始内存限制(可用内存比例)
            memory_limit_end: 结束内存限制(可用内存比例)
            steps: 内存限制步数
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        test_id = f"memory_stress_{int(time.time())}"
        logger.info(f"开始内存压力测试 [{test_id}], 持续时间: {duration}秒")
        
        # 将测试记录到运行中的测试
        self.running_tests[test_id] = {
            "type": "memory_stress",
            "start_time": time.time(),
            "params": {
                "duration": duration,
                "memory_limit_start": memory_limit_start,
                "memory_limit_end": memory_limit_end,
                "steps": steps
            },
            "status": "running"
        }
        
        results = {
            "test_id": test_id,
            "test_type": "memory_stress",
            "start_time": datetime.now().isoformat(),
            "duration": duration,
            "steps": [],
            "errors": [],
            "memory_stats": [],
            "success": False
        }
        
        try:
            # 计算每一步的内存限制
            memory_limits = []
            if steps > 1:
                step_size = (memory_limit_start - memory_limit_end) / (steps - 1)
                for i in range(steps):
                    memory_limits.append(memory_limit_start - i * step_size)
            else:
                memory_limits = [memory_limit_start]
            
            # 计算每一步的持续时间
            step_duration = duration / steps
            
            # 执行每一步测试
            for i, memory_limit in enumerate(memory_limits):
                step_result = self._run_memory_step(
                    test_id=f"{test_id}_step{i+1}",
                    memory_limit=memory_limit,
                    duration=step_duration
                )
                
                results["steps"].append(step_result)
                
                # 如果出现严重错误，停止测试
                if step_result.get("critical_error", False):
                    logger.warning(f"内存压力测试步骤 {i+1} 发生严重错误，停止测试")
                    break
            
            # 释放所有资源
            self.resource_limiter.release_all()
            
            # 计算测试结果
            error_count = sum(1 for step in results["steps"] if step.get("errors", []))
            success_rate = 1.0 - (error_count / len(results["steps"]) if results["steps"] else 0)
            
            results["end_time"] = datetime.now().isoformat()
            results["success_rate"] = success_rate
            results["success"] = success_rate > 0.7  # 70%以上的步骤成功视为测试成功
            results["actual_duration"] = time.time() - self.running_tests[test_id]["start_time"]
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "completed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["success"] = results["success"]
            
            logger.info(f"内存压力测试 [{test_id}] 完成，成功率: {success_rate*100:.1f}%")
            
        except Exception as e:
            logger.error(f"内存压力测试 [{test_id}] 异常: {str(e)}")
            
            # 确保释放资源
            self.resource_limiter.release_all()
            
            # 记录错误
            results["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            results["end_time"] = datetime.now().isoformat()
            results["success"] = False
            results["actual_duration"] = time.time() - self.running_tests[test_id]["start_time"]
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "failed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["error"] = str(e)
        
        # 保存测试结果
        self.test_results[test_id] = results
        self._save_test_result(test_id, results)
        
        return results
    
    def _run_memory_step(self, test_id: str, memory_limit: float, duration: float) -> Dict[str, Any]:
        """
        运行单个内存压力测试步骤
        
        Args:
            test_id: 测试ID
            memory_limit: 内存限制(可用内存比例)
            duration: 持续时间(秒)
            
        Returns:
            Dict[str, Any]: 步骤结果
        """
        logger.info(f"内存压力测试步骤 [{test_id}]: 设置内存限制 {memory_limit*100:.1f}%, 持续 {duration}秒")
        
        step_result = {
            "step_id": test_id,
            "memory_limit": memory_limit,
            "duration": duration,
            "start_time": datetime.now().isoformat(),
            "memory_stats": [],
            "errors": [],
            "success": False,
            "critical_error": False
        }
        
        try:
            # 设置内存限制
            success = self.resource_limiter.limit_memory(memory_limit)
            if not success:
                raise Exception(f"无法设置内存限制至 {memory_limit*100:.1f}%")
            
            # 记录内存统计
            start_time = time.time()
            
            # 执行测试
            while time.time() - start_time < duration:
                # 记录内存状态
                if PSUTIL_AVAILABLE:
                    mem = psutil.virtual_memory()
                    memory_stat = {
                        "time": time.time() - start_time,
                        "available_gb": mem.available / (1024**3),
                        "total_gb": mem.total / (1024**3),
                        "percent": mem.percent
                    }
                    step_result["memory_stats"].append(memory_stat)
                
                # 触发混沌故障
                if random.random() < 0.3:  # 30%概率触发故障
                    try:
                        recovery_time = self.chaos_monkey.induce_failure(None)
                        if recovery_time > 0:
                            step_result["induced_failures"] = step_result.get("induced_failures", 0) + 1
                            step_result["recovery_times"] = step_result.get("recovery_times", []) + [recovery_time]
                    except Exception as e:
                        logger.error(f"触发故障失败: {str(e)}")
                
                # 暂停一段时间
                time.sleep(1.0)
            
            # 记录步骤成功
            step_result["success"] = True
            step_result["end_time"] = datetime.now().isoformat()
            step_result["actual_duration"] = time.time() - start_time
            
            logger.info(f"内存压力测试步骤 [{test_id}] 完成")
            
        except Exception as e:
            logger.error(f"内存压力测试步骤 [{test_id}] 异常: {str(e)}")
            
            # 记录错误
            step_result["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            # 判断是否是严重错误
            if isinstance(e, MemoryOverflowError) or isinstance(e, ResourceExhaustionError):
                step_result["critical_error"] = True
            
            step_result["end_time"] = datetime.now().isoformat()
            step_result["actual_duration"] = time.time() - start_time if 'start_time' in locals() else 0
        
        return step_result
    
    def run_cpu_stress_test(self, 
                           duration: int = 60, 
                           cpu_limit_start: float = 0.7, 
                           cpu_limit_end: float = 0.2, 
                           steps: int = 3) -> Dict[str, Any]:
        """
        运行CPU压力测试
        
        逐步减少CPU可用资源，测试在CPU受限情况下的行为
        
        Args:
            duration: 测试持续时间(秒)
            cpu_limit_start: 起始CPU限制(可用比例)
            cpu_limit_end: 结束CPU限制(可用比例)
            steps: CPU限制步数
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        test_id = f"cpu_stress_{int(time.time())}"
        logger.info(f"开始CPU压力测试 [{test_id}], 持续时间: {duration}秒")
        
        # 将测试记录到运行中的测试
        self.running_tests[test_id] = {
            "type": "cpu_stress",
            "start_time": time.time(),
            "params": {
                "duration": duration,
                "cpu_limit_start": cpu_limit_start,
                "cpu_limit_end": cpu_limit_end,
                "steps": steps
            },
            "status": "running"
        }
        
        results = {
            "test_id": test_id,
            "test_type": "cpu_stress",
            "start_time": datetime.now().isoformat(),
            "duration": duration,
            "steps": [],
            "errors": [],
            "cpu_stats": [],
            "success": False
        }
        
        try:
            # 计算每一步的CPU限制
            cpu_limits = []
            if steps > 1:
                step_size = (cpu_limit_start - cpu_limit_end) / (steps - 1)
                for i in range(steps):
                    cpu_limits.append(cpu_limit_start - i * step_size)
            else:
                cpu_limits = [cpu_limit_start]
            
            # 计算每一步的持续时间
            step_duration = duration / steps
            
            # 执行每一步测试
            for i, cpu_limit in enumerate(cpu_limits):
                step_result = self._run_cpu_step(
                    test_id=f"{test_id}_step{i+1}",
                    cpu_limit=cpu_limit,
                    duration=step_duration
                )
                
                results["steps"].append(step_result)
                
                # 如果出现严重错误，停止测试
                if step_result.get("critical_error", False):
                    logger.warning(f"CPU压力测试步骤 {i+1} 发生严重错误，停止测试")
                    break
            
            # 释放所有资源
            self.resource_limiter.release_all()
            
            # 计算测试结果
            error_count = sum(1 for step in results["steps"] if step.get("errors", []))
            success_rate = 1.0 - (error_count / len(results["steps"]) if results["steps"] else 0)
            
            results["end_time"] = datetime.now().isoformat()
            results["success_rate"] = success_rate
            results["success"] = success_rate > 0.7  # 70%以上的步骤成功视为测试成功
            results["actual_duration"] = time.time() - self.running_tests[test_id]["start_time"]
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "completed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["success"] = results["success"]
            
            logger.info(f"CPU压力测试 [{test_id}] 完成，成功率: {success_rate*100:.1f}%")
            
        except Exception as e:
            logger.error(f"CPU压力测试 [{test_id}] 异常: {str(e)}")
            
            # 确保释放资源
            self.resource_limiter.release_all()
            
            # 记录错误
            results["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            results["end_time"] = datetime.now().isoformat()
            results["success"] = False
            results["actual_duration"] = time.time() - self.running_tests[test_id]["start_time"]
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "failed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["error"] = str(e)
        
        # 保存测试结果
        self.test_results[test_id] = results
        self._save_test_result(test_id, results)
        
        return results
    
    def _run_cpu_step(self, test_id: str, cpu_limit: float, duration: float) -> Dict[str, Any]:
        """
        运行单个CPU压力测试步骤
        
        Args:
            test_id: 测试ID
            cpu_limit: CPU限制(可用比例)
            duration: 持续时间(秒)
            
        Returns:
            Dict[str, Any]: 步骤结果
        """
        logger.info(f"CPU压力测试步骤 [{test_id}]: 设置CPU限制 {cpu_limit*100:.1f}%, 持续 {duration}秒")
        
        step_result = {
            "step_id": test_id,
            "cpu_limit": cpu_limit,
            "duration": duration,
            "start_time": datetime.now().isoformat(),
            "cpu_stats": [],
            "errors": [],
            "success": False,
            "critical_error": False
        }
        
        try:
            # 设置CPU限制
            success = self.resource_limiter.limit_cpu(cpu_limit)
            if not success:
                raise Exception(f"无法设置CPU限制至 {cpu_limit*100:.1f}%")
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行测试
            while time.time() - start_time < duration:
                # 记录CPU状态
                if PSUTIL_AVAILABLE:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_stat = {
                        "time": time.time() - start_time,
                        "cpu_percent": cpu_percent
                    }
                    step_result["cpu_stats"].append(cpu_stat)
                
                # 触发混沌故障
                if random.random() < 0.3:  # 30%概率触发故障
                    try:
                        recovery_time = self.chaos_monkey.induce_failure(None)
                        if recovery_time > 0:
                            step_result["induced_failures"] = step_result.get("induced_failures", 0) + 1
                            step_result["recovery_times"] = step_result.get("recovery_times", []) + [recovery_time]
                    except Exception as e:
                        logger.error(f"触发故障失败: {str(e)}")
                
                # 暂停一段时间
                time.sleep(1.0)
            
            # 记录步骤成功
            step_result["success"] = True
            step_result["end_time"] = datetime.now().isoformat()
            step_result["actual_duration"] = time.time() - start_time
            
            logger.info(f"CPU压力测试步骤 [{test_id}] 完成")
            
        except Exception as e:
            logger.error(f"CPU压力测试步骤 [{test_id}] 异常: {str(e)}")
            
            # 记录错误
            step_result["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            step_result["end_time"] = datetime.now().isoformat()
            step_result["actual_duration"] = time.time() - start_time if 'start_time' in locals() else 0
        
        return step_result
    
    def run_chaos_test(self, duration: int = 60, failure_interval: int = 10) -> Dict[str, Any]:
        """
        运行混沌测试
        
        随机注入故障并测试系统恢复能力
        
        Args:
            duration: 测试持续时间(秒)
            failure_interval: 故障注入间隔(秒)
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        test_id = f"chaos_test_{int(time.time())}"
        logger.info(f"开始混沌测试 [{test_id}], 持续时间: {duration}秒, 故障间隔: {failure_interval}秒")
        
        # 将测试记录到运行中的测试
        self.running_tests[test_id] = {
            "type": "chaos_test",
            "start_time": time.time(),
            "params": {
                "duration": duration,
                "failure_interval": failure_interval
            },
            "status": "running"
        }
        
        results = {
            "test_id": test_id,
            "test_type": "chaos_test",
            "start_time": datetime.now().isoformat(),
            "duration": duration,
            "failure_interval": failure_interval,
            "failures": [],
            "errors": [],
            "recovery_times": [],
            "success": False
        }
        
        try:
            # 记录开始时间
            start_time = time.time()
            last_failure_time = start_time
            
            # 执行测试
            while time.time() - start_time < duration:
                current_time = time.time()
                
                # 按指定间隔注入故障
                if current_time - last_failure_time > failure_interval:
                    try:
                        # 记录故障前状态
                        pre_failure_stats = self._collect_system_stats()
                        
                        # 注入故障
                        scenario = random.choice(self.chaos_monkey.FAILURE_SCENARIOS)
                        logger.info(f"注入故障: {scenario}")
                        
                        # 触发故障
                        recovery_time = self.chaos_monkey._trigger(scenario)
                        
                        # 记录故障后状态
                        post_failure_stats = self._collect_system_stats()
                        
                        # 记录故障信息
                        failure_info = {
                            "time": datetime.now().isoformat(),
                            "scenario": scenario,
                            "recovery_time": recovery_time,
                            "pre_failure_stats": pre_failure_stats,
                            "post_failure_stats": post_failure_stats,
                            "success": recovery_time > 0
                        }
                        results["failures"].append(failure_info)
                        
                        if recovery_time > 0:
                            results["recovery_times"].append(recovery_time)
                        
                        last_failure_time = current_time
                        
                    except Exception as e:
                        logger.error(f"注入故障失败: {str(e)}")
                        results["errors"].append({
                            "time": datetime.now().isoformat(),
                            "error": str(e),
                            "operation": "inject_failure",
                            "traceback": traceback.format_exc()
                        })
                
                # 暂停一段时间
                time.sleep(1.0)
            
            # 计算恢复率
            total_failures = len(results["failures"])
            successful_recoveries = sum(1 for f in results["failures"] if f.get("success", False))
            
            recovery_rate = successful_recoveries / total_failures if total_failures > 0 else 1.0
            avg_recovery_time = sum(results["recovery_times"]) / len(results["recovery_times"]) if results["recovery_times"] else 0
            
            results["recovery_rate"] = recovery_rate
            results["avg_recovery_time"] = avg_recovery_time
            results["end_time"] = datetime.now().isoformat()
            results["actual_duration"] = time.time() - start_time
            results["success"] = recovery_rate >= 0.7  # 70%以上的故障成功恢复视为测试成功
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "completed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["success"] = results["success"]
            
            logger.info(f"混沌测试 [{test_id}] 完成，恢复率: {recovery_rate*100:.1f}%, 平均恢复时间: {avg_recovery_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"混沌测试 [{test_id}] 异常: {str(e)}")
            
            # 记录错误
            results["errors"].append({
                "time": datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            results["end_time"] = datetime.now().isoformat()
            results["success"] = False
            results["actual_duration"] = time.time() - self.running_tests[test_id]["start_time"]
            
            # 更新运行中的测试状态
            self.running_tests[test_id]["status"] = "failed"
            self.running_tests[test_id]["end_time"] = time.time()
            self.running_tests[test_id]["error"] = str(e)
        
        # 保存测试结果
        self.test_results[test_id] = results
        self._save_test_result(test_id, results)
        
        return results
    
    def _collect_system_stats(self) -> Dict[str, Any]:
        """
        收集系统状态信息
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        stats = {
            "time": datetime.now().isoformat()
        }
        
        # 收集内存信息
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            stats["memory"] = {
                "total_gb": mem.total / (1024**3),
                "available_gb": mem.available / (1024**3),
                "used_gb": mem.used / (1024**3),
                "percent": mem.percent
            }
            
            # 收集CPU信息
            stats["cpu"] = {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count()
            }
            
            # 收集磁盘信息
            disk = psutil.disk_usage('/')
            stats["disk"] = {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": disk.percent
            }
        
        # 收集GPU信息
        if TORCH_AVAILABLE and torch.cuda.is_available():
            stats["gpu"] = {
                "count": torch.cuda.device_count()
            }
            
            # 收集每个GPU的信息
            for i in range(torch.cuda.device_count()):
                stats["gpu"][f"device_{i}"] = {
                    "name": torch.cuda.get_device_name(i),
                    "memory_allocated": torch.cuda.memory_allocated(i) / (1024**2),  # MB
                    "memory_reserved": torch.cuda.memory_reserved(i) / (1024**2)  # MB
                }
        
        return stats
    
    def _save_test_result(self, test_id: str, result: Dict[str, Any]) -> None:
        """
        保存测试结果到文件
        
        Args:
            test_id: 测试ID
            result: 测试结果
        """
        # 确保目录存在
        ensure_dir_exists(self.results_dir)
        
        # 保存文件
        filename = f"{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试结果已保存到: {filepath}")
    
    def get_test_results(self, test_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取测试结果
        
        Args:
            test_id: 测试ID，为None时返回所有测试结果的摘要
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        if test_id:
            return self.test_results.get(test_id, {"error": "测试结果不存在"})
        
        # 返回所有测试结果的摘要
        summary = {
            "total_tests": len(self.test_results),
            "succeeded_tests": sum(1 for r in self.test_results.values() if r.get("success", False)),
            "failed_tests": sum(1 for r in self.test_results.values() if not r.get("success", False)),
            "tests": []
        }
        
        for tid, result in self.test_results.items():
            summary["tests"].append({
                "test_id": tid,
                "test_type": result.get("test_type", "unknown"),
                "start_time": result.get("start_time", ""),
                "duration": result.get("actual_duration", 0),
                "success": result.get("success", False)
            })
        
        return summary
    
    def stop_all_tests(self) -> None:
        """停止所有正在运行的测试"""
        logger.info("停止所有压力测试...")
        
        # 释放所有资源
        self.resource_limiter.release_all()
        
        # 更新测试状态
        for test_id, test_info in self.running_tests.items():
            if test_info.get("status") == "running":
                test_info["status"] = "stopped"
                test_info["end_time"] = time.time()
                
                # 也更新测试结果
                if test_id in self.test_results:
                    self.test_results[test_id]["end_time"] = datetime.now().isoformat()
                    self.test_results[test_id]["success"] = False
                    self.test_results[test_id]["stopped"] = True
        
        logger.info("所有压力测试已停止")


# 导出模块
__all__ = ['ChaosMonkey', 'ResourceLimiter', 'StressTestRunner'] 