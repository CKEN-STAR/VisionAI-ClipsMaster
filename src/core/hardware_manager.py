#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 硬件资源管理器

管理系统硬件资源，提供硬件信息查询和性能监控功能
"""

import os
import sys
import platform
import logging
import subprocess
import re
import json
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入硬件监控库
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logger.warning("未找到psutil库，将使用基本硬件检测功能")
    HAS_PSUTIL = False

try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    logger.warning("未找到GPUtil库，GPU检测功能将受限")
    HAS_GPUTIL = False


class HardwareManager:
    """硬件资源管理器，负责获取和监控系统硬件资源"""
    
    # 单例实例
    _instance = None
    
    @classmethod
    def instance(cls) -> 'HardwareManager':
        """获取单例实例
        
    Returns:
            HardwareManager: 硬件管理器实例
        """
        if cls._instance is None:
            cls._instance = HardwareManager()
        return cls._instance
    
    def __init__(self):
        """初始化硬件资源管理器"""
        # 初始化时进行基本检测
        self.system_info = self._detect_system_info()
        self.cpu_info = self._detect_cpu_info()
        self.memory_info = self._detect_memory_info()
        self.gpu_info = self._detect_gpu_info()
        
        # 资源使用监控变量
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 2.0  # 默认2秒更新一次
        self.usage_history = {
            'cpu': [],
            'memory': [],
            'gpu': []
        }
        self.max_history_size = 60  # 保存最近60个数据点
    
    def _detect_system_info(self) -> Dict[str, Any]:
        """检测系统基本信息
        
        Returns:
            Dict[str, Any]: 系统信息字典
        """
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        # 系统特定信息
        if info['platform'] == 'Windows':
            info['windows_edition'] = platform.win32_edition() if hasattr(platform, 'win32_edition') else 'Unknown'
        elif info['platform'] == 'Linux':
            try:
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('PRETTY_NAME='):
                            info['linux_distro'] = line.split('=')[1].strip().strip('"')
            except:
                info['linux_distro'] = 'Unknown'
        elif info['platform'] == 'Darwin':
            info['mac_version'] = platform.mac_ver()[0]
        
        return info
    
    def _detect_cpu_info(self) -> Dict[str, Any]:
        """检测CPU信息
        
        Returns:
            Dict[str, Any]: CPU信息字典
        """
        info = {
            'cores': os.cpu_count(),
            'frequency': None,
            'model': None,
            'vendor': None
        }
        
        if HAS_PSUTIL:
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    info['frequency'] = cpu_freq.current / 1000.0  # 转换为GHz
            except:
                pass
        
        # 系统特定的CPU信息获取
        if self.system_info['platform'] == 'Windows':
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True, text=True, check=True
                )
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        info['model'] = lines[1].strip()
            except:
                pass
        elif self.system_info['platform'] == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            info['model'] = line.split(':')[1].strip()
                            break
            except:
                pass
        elif self.system_info['platform'] == 'Darwin':
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, check=True
                )
                if result.stdout:
                    info['model'] = result.stdout.strip()
            except:
                pass
        
        return info
    
    def _detect_memory_info(self) -> Dict[str, Any]:
        """检测内存信息
        
        Returns:
            Dict[str, Any]: 内存信息字典（单位MB）
        """
        info = {
            'total': None,
            'available': None,
            'used': None
        }
        
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                info['total'] = mem.total / (1024 * 1024)  # 转换为MB
                info['available'] = mem.available / (1024 * 1024)
                info['used'] = mem.used / (1024 * 1024)
            except:
                pass
        
        return info
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """检测GPU信息
    
    Returns:
            Dict[str, Any]: GPU信息字典
        """
        info = {
            'available': False,
            'devices': []
        }
        
        # 通过GPUtil检测NVIDIA显卡
        if HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    info['available'] = True
                    for gpu in gpus:
                        info['devices'].append({
                            'id': gpu.id,
                            'name': gpu.name,
                            'memory_total': gpu.memoryTotal,  # MB
                            'memory_used': gpu.memoryUsed,    # MB
                            'temperature': gpu.temperature,   # °C
                            'load': gpu.load                  # 利用率 0.0-1.0
                        })
            except:
                pass
        
        # 如果GPUtil检测失败，尝试其他方法
        if not info['available']:
            # 尝试检测NVIDIA显卡
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader"],
                    capture_output=True, text=True, check=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    info['available'] = True
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            # 解析NVIDIA-SMI输出
                            name = parts[0]
                            total_memory = int(parts[1].split(' ')[0])
                            used_memory = int(parts[2].split(' ')[0])
                            info['devices'].append({
                                'id': len(info['devices']),
                                'name': name,
                                'memory_total': total_memory,
                                'memory_used': used_memory,
                                'temperature': None,
                                'load': None
                            })
            except:
                pass
            
            # Windows系统尝试检测AMD/Intel显卡
            if self.system_info['platform'] == 'Windows' and not info['available']:
                try:
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM"],
                        capture_output=True, text=True, check=True
                    )
                    if result.stdout:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) >= 2:
                            for line in lines[1:]:
                                parts = line.strip().split()
                                if len(parts) >= 2:
                                    try:
                                        ram = int(parts[-1]) / (1024 * 1024)  # 转换为MB
                                        name = ' '.join(parts[:-1])
                                        if ram > 128:  # 忽略集成显卡
                                            info['available'] = True
                                            info['devices'].append({
                                                'id': len(info['devices']),
                                                'name': name,
                                                'memory_total': ram,
                                                'memory_used': None,
                                                'temperature': None,
                                                'load': None
                                            })
                                    except:
                                        pass
                except:
                    pass
        
        return info
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息
        
        Returns:
            Dict[str, Any]: CPU信息字典
        """
        # 刷新CPU使用率信息
        if HAS_PSUTIL:
            try:
                self.cpu_info['usage_percent'] = psutil.cpu_percent(interval=0.1)
            except:
                self.cpu_info['usage_percent'] = None
        
        return self.cpu_info
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息
        
    Returns:
            Dict[str, Any]: 内存信息字典
        """
        # 刷新内存使用情况
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                self.memory_info['available'] = mem.available / (1024 * 1024)  # MB
                self.memory_info['used'] = mem.used / (1024 * 1024)  # MB
                self.memory_info['percent'] = mem.percent
            except:
                pass
        
        return self.memory_info
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息
        
        Returns:
            Dict[str, Any]: GPU信息字典
        """
        # 刷新GPU使用情况
        if HAS_GPUTIL and self.gpu_info['available']:
            try:
                gpus = GPUtil.getGPUs()
                for i, gpu in enumerate(gpus):
                    if i < len(self.gpu_info['devices']):
                        self.gpu_info['devices'][i].update({
                            'memory_used': gpu.memoryUsed,
                            'temperature': gpu.temperature,
                            'load': gpu.load
                        })
            except:
                pass
        
        return self.gpu_info
    
    def has_gpu(self) -> bool:
        """检查是否有可用的GPU
    
    Returns:
            bool: 是否有GPU可用
        """
        return self.gpu_info['available']
    
    def get_suitable_device(self) -> str:
        """获取适合的计算设备
        
        Returns:
            str: 设备类型，'gpu' 或 'cpu'
        """
        if self.has_gpu():
            # 检查GPU是否足够空闲
            for device in self.gpu_info['devices']:
                # 如果GPU内存使用率低于80%，认为可用
                if 'memory_used' in device and 'memory_total' in device:
                    if device['memory_used'] / device['memory_total'] < 0.8:
                        return 'gpu'
        
        return 'cpu'
    
    def get_memory_usage(self) -> Tuple[float, float]:
        """获取当前内存使用情况
        
        Returns:
            Tuple[float, float]: (已用内存MB, 总内存MB)
        """
        mem_info = self.get_memory_info()
        return (
            mem_info.get('used', 0), 
            mem_info.get('total', 0)
        )
    
    def get_cpu_usage(self) -> float:
        """获取当前CPU使用率
        
    Returns:
            float: CPU使用率百分比
        """
        cpu_info = self.get_cpu_info()
        return cpu_info.get('usage_percent', 0)
    
    def start_monitoring(self, interval: float = 2.0):
        """开始硬件资源监控
        
        Args:
            interval: 监控间隔(秒)
        """
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_interval = interval
        
        # 清空历史数据
        for key in self.usage_history:
            self.usage_history[key] = []
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止硬件资源监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            self.monitor_thread = None
    
    def _monitor_loop(self):
        """资源监控循环"""
        while self.monitoring:
            try:
                # 获取CPU使用率
                cpu_usage = self.get_cpu_usage()
                self.usage_history['cpu'].append((time.time(), cpu_usage))
                
                # 获取内存使用情况
                mem_info = self.get_memory_info()
                if mem_info['total']:
                    mem_usage = mem_info['used'] / mem_info['total'] * 100
                    self.usage_history['memory'].append((time.time(), mem_usage))
                
                # 获取GPU使用情况
                if self.has_gpu():
                    gpu_info = self.get_gpu_info()
                    for device in gpu_info['devices']:
                        if 'load' in device:
                            gpu_usage = device['load'] * 100  # 转为百分比
                            self.usage_history['gpu'].append((time.time(), gpu_usage))
                            break
                
                # 限制历史数据大小
                for key in self.usage_history:
                    if len(self.usage_history[key]) > self.max_history_size:
                        self.usage_history[key] = self.usage_history[key][-self.max_history_size:]
                
                # 休眠指定时间
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"资源监控出错: {e}")
                time.sleep(5)  # 出错后等待一段时间再继续
    
    def get_usage_history(self) -> Dict[str, List[Tuple[float, float]]]:
        """获取资源使用历史数据
        
        Returns:
            Dict[str, List[Tuple[float, float]]]: 资源使用历史数据
                键为资源类型(cpu/memory/gpu)，值为时间戳和使用率的元组列表
        """
        return {k: v.copy() for k, v in self.usage_history.items()}
    
    def estimate_performance_level(self) -> str:
        """估计系统性能等级
        
        Returns:
            str: 性能等级 'low', 'medium', 'high'
        """
        score = 0
        
        # CPU评分 (1-10分)
        cpu_score = 0
        if self.cpu_info['cores']:
            # 每个核心1分，最多6分
            cpu_score += min(6, self.cpu_info['cores'])
            
            # CPU频率加分
            if self.cpu_info['frequency']:
                if self.cpu_info['frequency'] > 3.0:
                    cpu_score += 3
                elif self.cpu_info['frequency'] > 2.0:
                    cpu_score += 2
                else:
                    cpu_score += 1
        
        # 内存评分 (1-10分)
        memory_score = 0
        if self.memory_info['total']:
            total_gb = self.memory_info['total'] / 1024  # 转为GB
            
            if total_gb > 16:
                memory_score = 10
            elif total_gb > 8:
                memory_score = 7
            elif total_gb > 4:
                memory_score = 4
            else:
                memory_score = 2
        
        # GPU评分 (0-10分)
        gpu_score = 0
        if self.has_gpu():
            # 有GPU就有5分基础分
            gpu_score = 5
            
            # 检查GPU内存大小
            for device in self.gpu_info['devices']:
                if 'memory_total' in device:
                    gpu_mem_gb = device['memory_total'] / 1024  # 转为GB
                    
                    if gpu_mem_gb > 8:
                        gpu_score += 5
                    elif gpu_mem_gb > 4:
                        gpu_score += 3
                    elif gpu_mem_gb > 2:
                        gpu_score += 1
                    
                    break  # 只考虑第一个GPU
        
        # 总评分 (CPU占比40%，内存占比30%，GPU占比30%)
        score = cpu_score * 0.4 + memory_score * 0.3 + gpu_score * 0.3
        
        # 评分等级划分
        if score > 7:
            return 'high'
        elif score > 4:
            return 'medium'
        else:
            return 'low'


# 全局硬件管理器实例
hardware_manager = HardwareManager.instance()

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取硬件信息
    manager = HardwareManager()
    
    print("系统信息:")
    print(json.dumps(manager.system_info, indent=2))
    
    print("\nCPU信息:")
    print(json.dumps(manager.get_cpu_info(), indent=2))
    
    print("\n内存信息:")
    print(json.dumps(manager.get_memory_info(), indent=2))
    
    print("\nGPU信息:")
    print(json.dumps(manager.get_gpu_info(), indent=2))
    
    print(f"\nGPU可用: {manager.has_gpu()}")
    print(f"推荐设备: {manager.get_suitable_device()}")
    print(f"性能等级: {manager.estimate_performance_level()}")
    
    # 测试监控功能
    print("\n开始资源监控(5秒)...")
    manager.start_monitoring(interval=1.0)
    time.sleep(5)
    manager.stop_monitoring()
    
    history = manager.get_usage_history()
    print(f"CPU使用历史: {len(history['cpu'])}个数据点")
    print(f"内存使用历史: {len(history['memory'])}个数据点")
    print(f"GPU使用历史: {len(history['gpu'])}个数据点") 