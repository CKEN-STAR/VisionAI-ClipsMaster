#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境感知适配器

根据当前运行环境（操作系统、硬件资源等）自动调整配置参数，
优化应用性能并确保跨平台兼容性。
"""

import os
import sys
import platform
import tempfile
import json
import yaml
import socket
import psutil
import logging
from typing import Dict, Any, Optional, Union, List, Tuple
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.path_resolver import (
        resolve_special_path, 
        normalize_path, 
        get_app_data_dir,
        get_temp_dir
    )
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def resolve_special_path(path):
        return os.path.abspath(os.path.expanduser(path))
    
    def normalize_path(path):
        return os.path.abspath(path)
    
    def get_app_data_dir(app_name="VisionAI-ClipsMaster"):
        if platform.system() == "Windows":
            base_dir = os.environ.get("APPDATA", "")
            if not base_dir:
                base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
            return os.path.join(base_dir, app_name)
        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), 
                             "Library", "Application Support", app_name)
        else:
            base_dir = os.environ.get("XDG_CONFIG_HOME", "")
            if not base_dir:
                base_dir = os.path.join(os.path.expanduser("~"), ".config")
            return os.path.join(base_dir, app_name)
    
    def get_temp_dir(prefix="visionai_"):
        temp_dir = os.path.join(tempfile.gettempdir(), f"{prefix}{os.getpid()}")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

# 设置日志记录器
logger = get_logger("env_adapter")

def detect_system_info() -> Dict[str, Any]:
    """
    检测系统环境信息
    
    Returns:
        Dict[str, Any]: 系统环境信息字典
    """
    system_info = {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": sys.platform,
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor() or "Unknown"
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "build_date": platform.python_build()[1]
        },
        "hardware": {
            "cpu_count": psutil.cpu_count(logical=False) or 1,
            "logical_cpu_count": psutil.cpu_count(logical=True) or 1,
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_total": psutil.disk_usage('/').total,
            "disk_free": psutil.disk_usage('/').free
        },
        "network": {
            "hostname": socket.gethostname(),
            "has_internet": check_internet_connection()
        },
        "user": {
            "home_dir": os.path.expanduser("~"),
            "username": os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
        },
        "paths": {
            "temp_dir": tempfile.gettempdir(),
            "app_data_dir": get_app_data_dir()
        }
    }
    
    # 检测GPU信息
    try:
        gpu_info = detect_gpu()
        if gpu_info:
            system_info["hardware"]["gpu"] = gpu_info
    except Exception as e:
        logger.warning(f"无法检测GPU信息: {str(e)}")
    
    return system_info

def check_internet_connection() -> bool:
    """
    检查互联网连接
    
    Returns:
        bool: 如果有互联网连接则返回True
    """
    try:
        # 尝试连接到一个可靠的服务
        socket.create_connection(("www.baidu.com", 80), timeout=3)
        return True
    except OSError:
        try:
            # 备用连接
            socket.create_connection(("www.google.com", 80), timeout=3)
            return True
        except OSError:
            return False

def detect_gpu() -> Optional[Dict[str, Any]]:
    """
    检测系统GPU信息
    
    Returns:
        Optional[Dict[str, Any]]: GPU信息，如果没有找到则返回None
    """
    gpu_info = {}
    
    # 尝试检测NVIDIA GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["type"] = "CUDA"
            gpu_info["count"] = torch.cuda.device_count()
            gpu_info["name"] = torch.cuda.get_device_name(0)
            gpu_info["memory_total"] = torch.cuda.get_device_properties(0).total_memory
            return gpu_info
    except ImportError:
        pass
    
    # 尝试直接使用pynvml
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_info["type"] = "NVIDIA"
            gpu_info["count"] = device_count
            gpu_info["name"] = pynvml.nvmlDeviceGetName(handle)
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_info["memory_total"] = memory_info.total
            pynvml.nvmlShutdown()
            return gpu_info
    except (ImportError, Exception):
        pass
    
    # 尝试检测AMD GPU
    try:
        from ctypes import cdll
        try:
            cdll.LoadLibrary('libatiadlxx.so')
            gpu_info["type"] = "AMD"
            gpu_info["count"] = 1  # 简化版，实际上需要更多代码来准确获取
            return gpu_info
        except OSError:
            try:
                cdll.LoadLibrary('atiadlxx.dll')
                gpu_info["type"] = "AMD"
                gpu_info["count"] = 1  # 简化版
                return gpu_info
            except OSError:
                pass
    except (ImportError, Exception):
        pass
    
    # 尝试检测DirectX (Windows)
    if platform.system() == "Windows":
        try:
            import win32com.client
            dxdiag = win32com.client.Dispatch("DxDiag.DxDiagProvider")
            dxdiag.Initialize()
            info = dxdiag.GetResults()
            if "DisplayDevices" in info:
                for device in info["DisplayDevices"]:
                    gpu_info["type"] = "DirectX"
                    gpu_info["name"] = device["DeviceName"]
                    gpu_info["count"] = 1
                    return gpu_info
        except (ImportError, Exception):
            pass
    
    # 尝试检测Metal (MacOS)
    if platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                    capture_output=True, text=True)
            if result.returncode == 0:
                gpu_info["type"] = "Metal"
                gpu_info["count"] = 1  # 简化版
                return gpu_info
        except (FileNotFoundError, Exception):
            pass
    
    return None

def get_optimal_cpu_threads() -> int:
    """
    获取系统最佳线程数
    
    Returns:
        int: 推荐的线程数
    """
    logical_cpus = psutil.cpu_count(logical=True)
    physical_cpus = psutil.cpu_count(logical=False)
    
    if not physical_cpus:
        physical_cpus = 1
    
    if not logical_cpus:
        logical_cpus = physical_cpus
    
    # 计算最佳线程数，但不超过逻辑CPU数量
    # 通常保留1-2个核心给系统使用
    if logical_cpus > 4:
        return max(logical_cpus - 2, physical_cpus)
    else:
        return max(logical_cpus - 1, 1)

def get_optimal_memory_limit() -> int:
    """
    计算系统最佳内存使用限制（MB）
    
    Returns:
        int: 建议的内存限制（MB）
    """
    total_memory_mb = psutil.virtual_memory().total // (1024 * 1024)
    available_memory_mb = psutil.virtual_memory().available // (1024 * 1024)
    
    # 计算合理的内存限制，确保系统有足够的剩余内存
    # 对于低内存系统 (<4GB)，最多使用60%
    # 对于中内存系统 (4-16GB)，最多使用70%
    # 对于高内存系统 (>16GB)，最多使用80%
    
    if total_memory_mb < 4 * 1024:  # 小于4GB
        memory_limit = min(int(total_memory_mb * 0.6), available_memory_mb * 0.8)
    elif total_memory_mb < 16 * 1024:  # 4-16GB
        memory_limit = min(int(total_memory_mb * 0.7), available_memory_mb * 0.8)
    else:  # 大于16GB
        memory_limit = min(int(total_memory_mb * 0.8), available_memory_mb * 0.8)
    
    return int(memory_limit)

def get_optimal_disk_cache_size() -> int:
    """
    计算系统最佳磁盘缓存大小（MB）
    
    Returns:
        int: 建议的磁盘缓存大小（MB）
    """
    disk_free_mb = psutil.disk_usage('/').free // (1024 * 1024)
    
    # 根据可用磁盘空间设置合理的缓存大小
    # 但确保不超过可用空间的10%，且至少预留5GB空间
    max_cache_size = min(disk_free_mb * 0.1, disk_free_mb - 5 * 1024)
    
    # 合理的最小和最大缓存限制
    min_cache = 1024  # 最小1GB
    max_cache = 102400  # 最大100GB
    
    optimal_cache = max(min_cache, min(int(max_cache_size), max_cache))
    return optimal_cache

def get_optimal_temp_dir() -> str:
    """
    获取最佳临时目录路径
    
    Returns:
        str: 临时目录路径
    """
    system = platform.system()
    
    # 根据系统类型确定最佳临时目录
    if system == "Windows":
        # 优先选择较大空间的磁盘
        try:
            drives = get_windows_drives()
            if drives:
                # 选择剩余空间最大的盘
                largest_drive = max(drives, key=lambda d: d["free_space"])
                temp_dir = os.path.join(largest_drive["path"], "Temp", "VisionAI")
                os.makedirs(temp_dir, exist_ok=True)
                return temp_dir
        except Exception:
            # 使用普通临时目录作为备选
            pass
    
    # Linux/macOS或Windows备选方案
    base_temp = tempfile.gettempdir()
    app_temp = os.path.join(base_temp, "VisionAI-ClipsMaster")
    os.makedirs(app_temp, exist_ok=True)
    return app_temp

def get_windows_drives() -> List[Dict[str, Any]]:
    """
    获取Windows系统的所有驱动器信息
    
    Returns:
        List[Dict[str, Any]]: 驱动器信息列表
    """
    if platform.system() != "Windows":
        return []
    
    drives = []
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            try:
                drive_info = psutil.disk_usage(drive_path)
                drives.append({
                    "path": drive_path,
                    "total_space": drive_info.total,
                    "free_space": drive_info.free,
                    "used_space": drive_info.used,
                    "percent_used": drive_info.percent
                })
            except Exception:
                # 忽略无法访问的驱动器
                pass
    
    return drives

def adapt_for_environment(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据运行环境自动调整配置
    
    Args:
        config: 原始配置字典
        
    Returns:
        Dict[str, Any]: 调整后的配置字典
    """
    if not isinstance(config, dict):
        logger.error("配置必须是字典类型")
        return config
    
    # 获取系统信息
    system_info = detect_system_info()
    
    # 复制配置以避免修改原始对象
    adapted_config = config.copy()
    
    # 根据操作系统调整路径
    if system_info["os"]["system"] == "Windows":
        # Windows路径适配
        if "storage" in adapted_config and "temp_dir" in adapted_config["storage"]:
            temp_env = os.environ.get("TEMP", "")
            if temp_env:
                adapted_config["storage"]["temp_dir"] = os.path.join(temp_env, "VisionAI-ClipsMaster")
            else:
                adapted_config["storage"]["temp_dir"] = "C:\\Temp\\VisionAI-ClipsMaster"
    
    elif system_info["os"]["system"] == "Darwin":
        # macOS路径适配
        if "storage" in adapted_config and "temp_dir" in adapted_config["storage"]:
            adapted_config["storage"]["temp_dir"] = "/tmp/clipsmaster"
    
    else:
        # Linux/UNIX路径适配
        if "storage" in adapted_config and "temp_dir" in adapted_config["storage"]:
            adapted_config["storage"]["temp_dir"] = "/tmp/clipsmaster"
    
    # 根据硬件资源调整性能参数
    if "performance" not in adapted_config:
        adapted_config["performance"] = {}
    
    # 设置CPU线程数
    optimal_threads = get_optimal_cpu_threads()
    adapted_config["performance"]["cpu_threads"] = optimal_threads
    
    # 设置内存限制
    optimal_memory = get_optimal_memory_limit()
    adapted_config["performance"]["memory_limit_mb"] = optimal_memory
    
    # 设置缓存大小
    optimal_cache = get_optimal_disk_cache_size()
    if "cache" not in adapted_config:
        adapted_config["cache"] = {}
    adapted_config["cache"]["size_limit_mb"] = optimal_cache
    
    # GPU适配
    if "hardware" in system_info and "gpu" in system_info["hardware"]:
        # 如果有GPU，启用GPU加速
        gpu_info = system_info["hardware"]["gpu"]
        if "gpu" not in adapted_config:
            adapted_config["gpu"] = {}
        
        adapted_config["gpu"]["enabled"] = True
        adapted_config["gpu"]["type"] = gpu_info.get("type", "auto")
        
        # 调整GPU内存限制（如果是NVIDIA或CUDA，预留一部分内存给系统）
        if gpu_info.get("type") in ["NVIDIA", "CUDA"] and "memory_total" in gpu_info:
            total_gpu_memory_mb = gpu_info["memory_total"] // (1024 * 1024)
            # 仅使用GPU内存的75%，避免内存溢出
            adapted_config["gpu"]["memory_limit_mb"] = int(total_gpu_memory_mb * 0.75)
    else:
        # 无GPU时，禁用GPU加速
        if "gpu" not in adapted_config:
            adapted_config["gpu"] = {}
        adapted_config["gpu"]["enabled"] = False
    
    # 网络适配
    if "network" not in adapted_config:
        adapted_config["network"] = {}
    
    adapted_config["network"]["has_internet"] = system_info["network"]["has_internet"]
    
    # 如果没有网络连接，禁用在线功能
    if not system_info["network"]["has_internet"]:
        adapted_config["network"]["online_features_enabled"] = False
        adapted_config["network"]["auto_update"] = False
    
    # 存储适配
    if "storage" not in adapted_config:
        adapted_config["storage"] = {}
    
    # 设置最佳临时目录
    adapted_config["storage"]["temp_dir"] = get_optimal_temp_dir()
    
    # 设置应用数据目录
    adapted_config["storage"]["app_data_dir"] = system_info["paths"]["app_data_dir"]
    
    # 语言适配（基于操作系统语言设置）
    if "ui" not in adapted_config:
        adapted_config["ui"] = {}
    
    if "language" not in adapted_config["ui"] or adapted_config["ui"]["language"] == "auto":
        import locale
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale:
                lang_code = system_locale.split('_')[0].lower()
                # 仅在支持的语言中设置
                supported_languages = ["zh", "en", "ja", "ko", "es", "fr", "de", "ru"]
                if lang_code in supported_languages:
                    adapted_config["ui"]["language"] = lang_code
                else:
                    adapted_config["ui"]["language"] = "en"  # 默认英语
            else:
                adapted_config["ui"]["language"] = "en"
        except Exception:
            adapted_config["ui"]["language"] = "en"
    
    # 日志配置
    if "logging" not in adapted_config:
        adapted_config["logging"] = {}
    
    # 设置日志目录
    logs_dir = os.path.join(adapted_config["storage"].get("app_data_dir", "."), "logs")
    adapted_config["logging"]["logs_dir"] = logs_dir
    
    # 设置合理的日志级别（开发环境详细，生产环境简洁）
    if "level" not in adapted_config["logging"] or adapted_config["logging"]["level"] == "auto":
        # 检测是否是开发环境
        is_dev = os.environ.get("VISIONAI_ENV", "").lower() == "development"
        adapted_config["logging"]["level"] = "debug" if is_dev else "info"
    
    logger.info(f"已根据环境完成配置适配: {system_info['os']['system']} {system_info['os']['release']}")
    
    return adapted_config


# 便捷函数
def get_adapted_config(config_file: str) -> Dict[str, Any]:
    """
    加载并适配配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        Dict[str, Any]: 适配后的配置
    """
    # 解析文件路径
    config_path = resolve_special_path(config_file)
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        return {}
    
    try:
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            ext = os.path.splitext(config_path)[1].lower()
            
            if ext in ['.json']:
                config = json.load(f)
            elif ext in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                logger.error(f"不支持的配置文件格式: {config_path}")
                return {}
        
        # 适配配置
        adapted_config = adapt_for_environment(config)
        return adapted_config
    
    except Exception as e:
        logger.error(f"加载或适配配置文件失败: {config_path}, 错误: {str(e)}")
        return {}


# 测试函数
if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 显示系统信息
    system_info = detect_system_info()
    print("系统信息:")
    print(json.dumps(system_info, indent=2, ensure_ascii=False))
    
    # 测试配置适配
    test_config = {
        "app_name": "VisionAI-ClipsMaster",
        "storage": {
            "temp_dir": "./temp"
        },
        "performance": {
            "cpu_threads": 4
        }
    }
    
    adapted_config = adapt_for_environment(test_config)
    print("\n适配后的配置:")
    print(json.dumps(adapted_config, indent=2, ensure_ascii=False)) 