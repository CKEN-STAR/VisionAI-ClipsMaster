"""
环境验证模块
用于检查系统环境、依赖项和硬件配置是否满足运行要求
"""

import os
import sys
import platform
import psutil
import logging
from typing import Dict, List, Tuple, Optional
import pkg_resources
from loguru import logger

def check_python_version() -> Tuple[bool, str]:
    """检查Python版本是否满足要求"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    is_valid = current_version >= required_version
    message = f"Python版本: {'.'.join(map(str, current_version))} "
    message += "✓" if is_valid else f"✗ (需要 >= {'.'.join(map(str, required_version))})"
    return is_valid, message

def check_cuda_availability() -> Tuple[bool, str]:
    """检查CUDA是否可用及其版本"""
    try:
        import torch
        if not torch.cuda.is_available():
            return False, "CUDA: 不可用 ✗"
        
        cuda_version = torch.version.cuda
        device_count = torch.cuda.device_count()
        device_names = [torch.cuda.get_device_name(i) for i in range(device_count)]
        
        message = f"CUDA: {cuda_version} ✓\n"
        message += f"GPU数量: {device_count}\n"
        message += "设备列表:\n"
        for i, name in enumerate(device_names):
            message += f"  - GPU {i}: {name}\n"
        
        return True, message
    except ImportError:
        return False, "CUDA: PyTorch未安装，跳过CUDA检查"

def check_memory() -> Tuple[bool, str]:
    """检查系统内存是否满足要求"""
    required_memory_gb = 4
    memory = psutil.virtual_memory()
    total_gb = memory.total / (1024 ** 3)
    available_gb = memory.available / (1024 ** 3)
    
    is_valid = available_gb >= required_memory_gb
    message = f"系统内存: 总计 {total_gb:.1f}GB, 可用 {available_gb:.1f}GB "
    message += "✓" if is_valid else f"✗ (需要至少 {required_memory_gb}GB 可用内存)"
    
    return is_valid, message

def check_disk_space() -> Tuple[bool, str]:
    """检查磁盘空间是否满足要求"""
    required_space_gb = 10
    disk = psutil.disk_usage(os.getcwd())
    free_gb = disk.free / (1024 ** 3)
    
    is_valid = free_gb >= required_space_gb
    message = f"磁盘空间: 可用 {free_gb:.1f}GB "
    message += "✓" if is_valid else f"✗ (需要至少 {required_space_gb}GB 可用空间)"
    
    return is_valid, message

def check_dependencies() -> Tuple[bool, str]:
    """检查依赖项是否正确安装"""
    required_packages = {
        'numpy': '1.24.0',
        'pyyaml': '6.0.1',
        'loguru': '0.7.2',
    }
    
    optional_packages = {
        'torch': '2.1.0',
        'transformers': '4.36.0',
        'opencv-python': '4.8.0',
        'PyQt6': '6.4.2',
    }
    
    messages = []
    all_valid = True
    
    # 检查必需包
    for package, required_version in required_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            is_valid = pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(required_version)
            status = "✓" if is_valid else "✗"
            messages.append(f"{package}: {installed_version} {status}")
            all_valid &= is_valid
        except pkg_resources.DistributionNotFound:
            messages.append(f"{package}: 未安装 ✗")
            all_valid = False
    
    # 检查可选包
    messages.append("\n可选包:")
    for package, required_version in optional_packages.items():
        try:
            installed_version = pkg_resources.get_distribution(package).version
            is_valid = pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(required_version)
            status = "✓" if is_valid else "!"
            messages.append(f"{package}: {installed_version} {status}")
        except pkg_resources.DistributionNotFound:
            messages.append(f"{package}: 未安装")
    
    return all_valid, "\n".join(messages)

def validate_environment() -> bool:
    """
    验证完整的运行环境
    返回: bool, 环境是否满足所有要求
    """
    logger.info("开始环境验证...")
    
    checks = [
        ("Python版本检查", check_python_version()),
        ("CUDA环境检查", check_cuda_availability()),
        ("内存检查", check_memory()),
        ("磁盘空间检查", check_disk_space()),
        ("依赖项检查", check_dependencies())
    ]
    
    all_valid = True
    
    logger.info("系统信息:")
    logger.info(f"操作系统: {platform.system()} {platform.version()}")
    logger.info(f"处理器: {platform.processor()}")
    
    for check_name, (is_valid, message) in checks:
        logger.info(f"\n{check_name}:")
        logger.info(message)
        all_valid &= is_valid
    
    if all_valid:
        logger.success("\n✅ 环境验证通过!")
    else:
        logger.error("\n❌ 环境验证失败，请检查上述错误信息")
    
    return all_valid

def setup_logging():
    """配置日志系统"""
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    
    logger.remove()  # 移除默认的处理器
    logger.add(
        sys.stdout,
        format=log_format,
        level="INFO",
        colorize=True
    )
    logger.add(
        "logs/environment.log",
        format=log_format,
        level="DEBUG",
        rotation="1 day",
        retention="1 week"
    )

if __name__ == "__main__":
    setup_logging()
    validate_environment() 