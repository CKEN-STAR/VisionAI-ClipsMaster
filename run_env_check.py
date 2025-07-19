#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 环境检测工具

独立的环境检测工具，用于检查系统环境是否适合运行VisionAI-ClipsMaster。
此脚本不依赖于主应用程序的其他部分，可以单独运行。
"""

import os
import sys
import json
import platform
import argparse
import logging
import subprocess
import time
import re
import ctypes
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("env_checker")

def detect_environment() -> Dict[str, Any]:
    """精准识别运行时环境

    检测系统硬件和软件配置，判断是否满足应用需求。
    自动识别CPU、GPU、内存、操作系统等关键信息，
    用于后续性能优化和功能启用的决策。

    Returns:
        Dict[str, Any]: 包含环境详细信息的字典
    """
    # 获取CPU信息
    cpu_info = platform.processor()
    
    # 获取GPU信息
    gpu_info = get_gpu_info()
    
    # 获取内存信息 (以GB为单位)
    try:
        import psutil
        ram_total = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        # 如果没有psutil库，尝试其他方法获取内存信息
        ram_total = get_memory_fallback()
    
    # 获取操作系统信息
    os_info = platform.platform()
    
    # 获取存储空间信息
    storage_info = get_storage_info()
    
    # 构建环境信息字典
    environment = {
        "cpu": cpu_info,
        "gpu": gpu_info,
        "ram": ram_total,
        "os": os_info,
        "storage": storage_info,
        "detection_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 添加编程环境信息
    environment["python_version"] = platform.python_version()
    environment["is_64bit"] = platform.machine().endswith('64')
    
    # 判断是否为Docker容器
    environment["is_docker"] = is_running_in_docker()
    
    # 判断是否有网络连接
    environment["has_network"] = check_network_connectivity()
    
    # 获取CPU核心数
    try:
        environment["cpu_cores"] = os.cpu_count() or 0
    except:
        environment["cpu_cores"] = 0
    
    logger.info(f"已完成环境检测: CPU={cpu_info}, RAM={ram_total:.2f}GB, GPU={gpu_info}")
    
    return environment


def get_gpu_info() -> str:
    """
    获取GPU信息
    
    Returns:
        str: GPU型号名称，如果没有检测到则返回"集成显卡"
    """
    system = platform.system()
    
    # 检测NVIDIA GPU
    try:
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            output = subprocess.check_output([nvidia_smi, "--query-gpu=name", "--format=csv,noheader"]).decode().strip()
            if output:
                return output
    except:
        pass
    
    # 检测其他GPU
    if system == "Windows":
        try:
            # 尝试使用wmic
            output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "Name"], 
                                         stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore').strip()
            # 提取第一个非空行，跳过标题行
            lines = [line.strip() for line in output.split('\n') if line.strip()]
            if len(lines) > 1:
                return lines[1]  # 第一行是"Name"标题
        except:
            pass
    elif system == "Linux":
        try:
            # 尝试从lspci获取
            output = subprocess.check_output(["lspci", "-v"], stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            # 查找VGA控制器
            vga_match = re.search(r"VGA compatible controller: (.*?)(?:\\n|$)", output)
            if vga_match:
                return vga_match.group(1).strip()
        except:
            pass
    elif system == "Darwin":
        try:
            # 在macOS上获取GPU信息
            output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], 
                                         stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            # 提取型号名称
            chip_match = re.search(r"Chipset Model: (.*?)(?:\\n|$)", output)
            if chip_match:
                return chip_match.group(1).strip()
        except:
            pass
    
    # 如果所有方法都失败，返回默认值
    return "集成显卡"


def get_memory_fallback() -> float:
    """
    在没有psutil库的情况下获取内存大小
    
    Returns:
        float: 内存大小(GB)
    """
    system = platform.system()
    
    if system == "Windows":
        try:
            # Windows下使用ctypes获取内存信息
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", c_ulonglong),
                    ("ullAvailPhys", c_ulonglong),
                    ("ullTotalPageFile", c_ulonglong),
                    ("ullAvailPageFile", c_ulonglong),
                    ("ullTotalVirtual", c_ulonglong),
                    ("ullAvailVirtual", c_ulonglong),
                    ("ullAvailExtendedVirtual", c_ulonglong),
                ]
            
            memoryStatus = MEMORYSTATUSEX()
            memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
            
            return memoryStatus.ullTotalPhys / (1024**3)  # 转换为GB
        except:
            pass
    elif system == "Linux":
        try:
            # Linux下从/proc/meminfo读取
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            
            # 提取MemTotal
            match = re.search(r"MemTotal:\\\\\\1+(\\\\\\1+) kB", meminfo)
            if match:
                return int(match.group(1)) / (1024**2)  # 从kB转换为GB
        except:
            pass
    elif system == "Darwin":
        try:
            # macOS下使用sysctl
            output = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
            return int(output) / (1024**3)  # 转换为GB
        except:
            pass
    
    # 如果所有方法都失败，返回默认值
    return 4.0  # 假设4GB内存


def get_storage_info() -> Dict[str, Any]:
    """
    获取存储空间信息
    
    Returns:
        Dict[str, Any]: 存储空间信息
    """
    try:
        # 获取当前目录存储信息
        path = os.path.abspath(os.curdir)
        
        if platform.system() == "Windows":
            # Windows下使用ctypes获取磁盘空间
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes)
            )
            total = total_bytes.value
            free = free_bytes.value
        else:
            # Linux/macOS
            stats = os.statvfs(path)
            total = stats.f_frsize * stats.f_blocks
            free = stats.f_frsize * stats.f_bavail
        
        # 计算已用空间
        used = total - free
        
        return {
            "total_gb": total / (1024**3),
            "free_gb": free / (1024**3),
            "used_gb": used / (1024**3),
            "used_percent": (used / total) * 100 if total > 0 else 0
        }
    except Exception as e:
        logger.warning(f"获取存储空间信息失败: {e}")
        return {
            "total_gb": 0,
            "free_gb": 0,
            "used_gb": 0,
            "used_percent": 0
        }


def is_running_in_docker() -> bool:
    """
    检测是否在Docker容器中运行
    
    Returns:
        bool: 是否在Docker容器中
    """
    # 方法1: 检查cgroup
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read() or '.scope' in f.read()
    except:
        pass
    
    # 方法2: 检查是否存在/.dockerenv文件
    if os.path.exists('/.dockerenv'):
        return True
    
    return False


def check_network_connectivity() -> bool:
    """
    检查网络连接
    
    Returns:
        bool: 是否有网络连接
    """
    try:
        # 尝试连接到一个可靠的服务器
        if platform.system() == "Windows":
            output = subprocess.check_output(["ping", "-n", "1", "-w", "1000", "8.8.8.8"], 
                                         stderr=subprocess.DEVNULL)
        else:
            output = subprocess.check_output(["ping", "-c", "1", "-W", "1", "8.8.8.8"], 
                                         stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def get_device_tier(device_info: Dict[str, Any]) -> str:
    """
    根据设备信息确定设备等级
    
    Args:
        device_info: 设备信息字典
        
    Returns:
        str: 设备等级 ('entry', 'mid', 'high', 'premium')
    """
    ram = device_info.get("ram", 0)
    has_gpu = device_info.get("gpu", "集成显卡") != "集成显卡" and "Intel" not in device_info.get("gpu", "")
    
    if ram >= 32 and has_gpu:
        return "premium"
    elif ram >= 16 and has_gpu:
        return "high"
    elif ram >= 8:
        return "mid"
    else:
        return "entry"


def get_supported_features(device_tier: str, has_gpu: bool) -> Tuple[List[str], List[str], List[str]]:
    """
    获取设备支持的功能
    
    Args:
        device_tier: 设备等级
        has_gpu: 是否有独立GPU
        
    Returns:
        Tuple[List[str], List[str], List[str]]: 支持的功能、受限功能、不支持的功能
    """
    all_features = [
        "basic_processing",  # 基本视频处理
        "4k_processing",     # 4K视频处理
        "real_time_enhancement",  # 实时视频增强
        "batch_processing",  # 批量处理
        "multi_language"     # 多语言处理
    ]
    
    supported = []
    limited = []
    unsupported = []
    
    # 所有等级都支持基本处理和多语言
    supported.append("basic_processing")
    supported.append("multi_language")
    
    if device_tier in ["premium", "high"]:
        # 顶级和高端设备支持所有功能
        supported.append("4k_processing")
        supported.append("real_time_enhancement")
        supported.append("batch_processing")
    elif device_tier == "mid":
        # 中端设备支持批量处理，4K可能受限，实时增强可能不支持
        supported.append("batch_processing")
        if has_gpu:
            limited.append("4k_processing")
            limited.append("real_time_enhancement")
        else:
            limited.append("4k_processing")
            unsupported.append("real_time_enhancement")
    else:
        # 入门级设备，批量处理受限，其他高级功能不支持
        limited.append("batch_processing")
        unsupported.append("4k_processing")
        unsupported.append("real_time_enhancement")
    
    return supported, limited, unsupported


def get_upgrade_recommendations(device_info: Dict[str, Any], 
                              limited_features: List[str], 
                              unsupported_features: List[str]) -> List[str]:
    """
    生成升级建议
    
    Args:
        device_info: 设备信息
        limited_features: 受限功能
        unsupported_features: 不支持的功能
        
    Returns:
        List[str]: 升级建议列表
    """
    recommendations = []
    
    ram = device_info.get("ram", 0)
    cpu_cores = device_info.get("cpu_cores", 0)
    has_gpu = device_info.get("gpu", "集成显卡") != "集成显卡" and "Intel" not in device_info.get("gpu", "")
    storage_free = device_info.get("storage", {}).get("free_gb", 0)
    
    if ram < 8:
        recommendations.append("建议至少升级至8GB内存以支持更多功能")
    elif ram < 16 and ("4k_processing" in limited_features or "4k_processing" in unsupported_features):
        recommendations.append("建议升级至16GB或更高内存以获得更好的4K处理能力")
    
    if not has_gpu:
        if "real_time_enhancement" in unsupported_features:
            recommendations.append("建议添加支持CUDA或ROCm的独立GPU以启用实时增强功能")
        elif "4k_processing" in limited_features:
            recommendations.append("建议添加独立GPU以提升4K视频处理能力")
    
    if cpu_cores < 4:
        recommendations.append("建议使用至少4核CPU以提升处理速度")
    
    if storage_free < 20:
        recommendations.append("建议确保至少20GB可用存储空间以支持批量处理")
    
    return recommendations


def generate_compatibility_report(device_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成完整的兼容性报告
    
    Args:
        device_info: 设备信息
        
    Returns:
        Dict[str, Any]: 兼容性报告
    """
    # 确定设备等级
    device_tier = get_device_tier(device_info)
    
    # 确定GPU支持
    gpu_info = device_info.get("gpu", "集成显卡")
    has_gpu = gpu_info != "集成显卡" and "Intel" not in gpu_info
    
    # 获取支持的功能
    supported, limited, unsupported = get_supported_features(device_tier, has_gpu)
    
    # 生成升级建议
    recommendations = get_upgrade_recommendations(device_info, limited, unsupported)
    
    # 生成性能预期
    expected_performance = get_expected_performance(device_tier)
    
    # 组装报告
    return {
        "device_tier": device_tier,
        "expected_performance": expected_performance,
        "supported_features": supported,
        "limited_features": limited,
        "unsupported_features": unsupported,
        "recommendations": recommendations
    }


def get_expected_performance(device_tier: str) -> Dict[str, Any]:
    """
    获取预期性能指标
    
    Args:
        device_tier: 设备等级
        
    Returns:
        Dict[str, Any]: 性能指标
    """
    performance = {
        "entry": {
            "fps": 15,
            "processing_speed": "0.5x实时",
            "max_resolution": "1080p",
            "concurrent_tasks": 1
        },
        "mid": {
            "fps": 30,
            "processing_speed": "1x实时",
            "max_resolution": "2K",
            "concurrent_tasks": 2
        },
        "high": {
            "fps": 45,
            "processing_speed": "2x实时",
            "max_resolution": "4K",
            "concurrent_tasks": 4
        },
        "premium": {
            "fps": 60,
            "processing_speed": "3x实时",
            "max_resolution": "4K+",
            "concurrent_tasks": 8
        }
    }
    
    return performance.get(device_tier, performance["entry"])


def get_optimal_config(device_info: Dict[str, Any], compatibility: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据设备信息生成最佳应用配置
    
    Args:
        device_info: 设备信息
        compatibility: 兼容性报告
        
    Returns:
        Dict[str, Any]: 最佳应用配置
    """
    device_tier = compatibility.get("device_tier", "entry")
    ram = device_info.get("ram", 4)
    gpu = device_info.get("gpu", "集成显卡")
    cpu_cores = device_info.get("cpu_cores", 2)
    has_gpu = gpu != "集成显卡" and "Intel" not in gpu
    
    # 确定批处理大小
    batch_size = 1
    if device_tier == "premium":
        batch_size = 16
    elif device_tier == "high":
        batch_size = 8
    elif device_tier == "mid" and ram >= 8:
        batch_size = 4
    
    # 确定线程数
    threads = min(max(2, cpu_cores), 8)
    
    # 确定预览质量
    preview_quality = "low"  # 默认低质量
    if device_tier in ["premium", "high"]:
        preview_quality = "high"
    elif device_tier == "mid":
        preview_quality = "medium"
    
    # 确定是否使用模型量化
    use_quantization = ram < 16
    use_low_memory = ram < 8
    
    # 确定首选模型
    # 默认使用英文Mistral模型，但如果系统语言是中文则使用Qwen
    system_locale = get_system_locale()
    is_chinese = "zh" in system_locale.lower()
    
    if is_chinese:
        if ram >= 16 and has_gpu:
            preferred_model = "qwen2.5-7b"
        else:
            preferred_model = "qwen2.5-1.8b"  # 轻量版
    else:
        if ram >= 16 and has_gpu:
            preferred_model = "mistral-7b"
        else:
            preferred_model = "mistral-instruct"  # 轻量版
    
    return {
        "general": {
            "debug_mode": False,
            "log_level": "INFO",
            "data_dir": str(Path.home() / ".visionai" / "data"),
            "temp_dir": str(Path.home() / ".visionai" / "temp"),
            "max_history": 100
        },
        "performance": {
            "threads": threads,
            "use_gpu": has_gpu,
            "memory_limit": int(ram * 0.7 * 1024),  # MB, 最多使用70%内存
            "batch_size": batch_size,
            "preview_quality": preview_quality
        },
        "models": {
            "use_quantization": use_quantization,
            "use_low_memory": use_low_memory,
            "preferred_model": preferred_model
        }
    }


def get_system_locale() -> str:
    """
    检测系统语言环境
    
    Returns:
        str: 系统语言代码
    """
    try:
        import locale
        return locale.getdefaultlocale()[0] or "en_US"
    except:
        return "en_US"  # 默认英语


def check_and_print_environment(verbose: bool = False, save_report: bool = False):
    """
    检测并打印环境信息
    
    Args:
        verbose: 是否显示详细信息
        save_report: 是否保存报告
    """
    # 获取环境信息
    environment = detect_environment()
    
    # 生成兼容性报告
    compatibility = generate_compatibility_report(environment)
    
    # 生成最佳配置
    optimal_config = get_optimal_config(environment, compatibility)
    
    # 打印标题
    print("\n" + "=" * 70)
    print("VisionAI-ClipsMaster 环境兼容性报告")
    print("=" * 70)
    
    # 确定设备等级显示名称
    tier = compatibility.get("device_tier", "entry")
    tier_names = {
        "entry": "入门级",
        "mid": "中端",
        "high": "高端", 
        "premium": "顶级"
    }
    tier_display = tier_names.get(tier, "未知")
    
    # 打印基本环境信息
    print(f"\n📊 设备摘要: {tier_display}设备 - "
          f"CPU: {environment.get('cpu', 'Unknown')}, "
          f"RAM: {environment.get('ram', 0):.1f}GB, "
          f"GPU: {environment.get('gpu', 'Unknown')}")
    
    # 获取硬件信息
    print("\n🖥️  硬件信息:")
    print(f"  CPU: {environment.get('cpu', 'Unknown')}")
    print(f"  GPU: {environment.get('gpu', 'Unknown')}")
    print(f"  内存: {environment.get('ram', 0):.2f} GB")
    print(f"  磁盘可用空间: {environment.get('storage', {}).get('free_gb', 0):.2f} GB")
    
    # 获取操作系统信息
    print(f"\n💻 操作系统: {environment.get('os', 'Unknown')}")
    print(f"  Python版本: {environment.get('python_version', 'Unknown')}")
    
    # 打印设备等级
    print(f"\n📱 设备等级: {tier_display}")
    
    # 打印功能支持状态
    print("\n✅ 功能支持状态:")
    features = [
        ("basic_processing", "基本视频处理"),
        ("4k_processing", "4K视频处理"),
        ("real_time_enhancement", "实时视频增强"),
        ("batch_processing", "批量处理"),
        ("multi_language", "多语言支持")
    ]
    
    for feature_id, feature_name in features:
        if feature_id in compatibility.get("supported_features", []):
            print(f"  {feature_name}: ✓ 支持")
        elif feature_id in compatibility.get("limited_features", []):
            print(f"  {feature_name}: ⚠ 受限支持")
        else:
            print(f"  {feature_name}: ✗ 不支持")
    
    # 打印预期性能
    performance = compatibility.get("expected_performance", {})
    print("\n⚡ 预期性能:")
    print(f"  处理速度: {performance.get('processing_speed', '未知')}")
    print(f"  最大分辨率: {performance.get('max_resolution', '未知')}")
    print(f"  并发任务数: {performance.get('concurrent_tasks', 1)}")
    
    # 打印优化建议
    if compatibility.get("recommendations", []):
        print("\n💡 优化建议:")
        for i, rec in enumerate(compatibility["recommendations"], 1):
            print(f"  {i}. {rec}")
    
    # 打印应用推荐配置
    if verbose:
        print("\n⚙️ 推荐应用配置:")
        print(f"  使用GPU加速: {'是' if optimal_config['performance']['use_gpu'] else '否'}")
        print(f"  使用线程数: {optimal_config['performance']['threads']}")
        print(f"  批处理大小: {optimal_config['performance']['batch_size']}")
        print(f"  预览质量: {optimal_config['performance']['preview_quality']}")
        print(f"  内存限制: {optimal_config['performance']['memory_limit'] / 1024:.1f} GB")
        print(f"  使用量化模型: {'是' if optimal_config['models']['use_quantization'] else '否'}")
        print(f"  低内存模式: {'是' if optimal_config['models']['use_low_memory'] else '否'}")
        print(f"  推荐模型: {optimal_config['models']['preferred_model']}")
    
    # 保存报告
    if save_report:
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / "environment_report.json"
        
        report = {
            "environment": environment,
            "compatibility": compatibility,
            "optimal_config": optimal_config
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存至: {report_path}")
    
    # 结论
    print("\n" + "-" * 70)
    if tier in ["high", "premium"]:
        print("✅ 结论: 当前设备完全适合运行VisionAI-ClipsMaster的所有功能。")
    elif tier == "mid":
        print("✅ 结论: 当前设备可以运行VisionAI-ClipsMaster的大部分功能，但高级功能可能受限。")
    else:
        print("⚠️ 结论: 当前设备可以运行基本功能，但高级功能将受到限制。建议参考优化建议。")
    print("=" * 70 + "\n")


def main():
    """主函数入口"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster环境检测工具")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("-s", "--save", action="store_true", help="保存报告到文件")
    parser.add_argument("-j", "--json", action="store_true", help="输出JSON格式结果")
    args = parser.parse_args()
    
    if args.json:
        # 输出JSON格式结果
        environment = detect_environment()
        compatibility = generate_compatibility_report(environment)
        optimal_config = get_optimal_config(environment, compatibility)
        
        report = {
            "environment": environment,
            "compatibility": compatibility,
            "optimal_config": optimal_config
        }
        
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # 输出人类可读格式
        check_and_print_environment(verbose=args.verbose, save_report=args.save)


if __name__ == "__main__":
    main() 