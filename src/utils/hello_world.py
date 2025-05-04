"""环境验证模块。

此模块提供了系统环境和性能测试功能，用于验证系统配置和PyTorch性能。
包括系统信息检查、内存状态检查、GPU可用性检查以及矩阵运算性能测试。
"""

import platform
import time
from typing import Dict, Union, Optional

import psutil
import torch

from .log_handler import get_logger

logger = get_logger()


def get_system_info() -> Dict[str, str]:
    """获取系统基本信息。

    Returns:
        Dict[str, str]: 包含系统和Python版本信息的字典。
    """
    return {
        "os": f"{platform.system()} {platform.version()}",
        "python_version": platform.python_version()
    }


def get_memory_info() -> Dict[str, float]:
    """获取系统内存信息。

    Returns:
        Dict[str, float]: 包含总内存和可用内存信息的字典（单位：GB）。
    """
    memory = psutil.virtual_memory()
    return {
        "total_gb": memory.total / (1024**3),
        "available_gb": memory.available / (1024**3)
    }


def get_gpu_info() -> Optional[Dict[str, Union[str, float]]]:
    """获取GPU信息。

    Returns:
        Optional[Dict[str, Union[str, float]]]: 如果GPU可用，返回GPU信息字典；否则返回None。
    """
    if not torch.cuda.is_available():
        return None

    device = torch.cuda.get_device_properties(0)
    return {
        "cuda_version": torch.version.cuda,
        "device_name": torch.cuda.get_device_name(0),
        "memory_gb": device.total_memory / (1024**3)
    }


def run_performance_test(matrix_size: int = 2000) -> Dict[str, Union[float, str]]:
    """运行矩阵乘法性能测试。

    Args:
        matrix_size (int): 测试矩阵的大小，默认为2000。

    Returns:
        Dict[str, Union[float, str]]: 包含性能测试结果的字典。

    Note:
        如果GPU可用，会同时测试GPU和CPU性能并计算加速比。
        如果只有CPU可用，则只测试CPU性能。
    """
    results = {}
    
    try:
        # CPU测试
        x_cpu = torch.randn(matrix_size, matrix_size)
        start_time = time.time()
        torch.matmul(x_cpu, x_cpu.t())
        cpu_time = time.time() - start_time
        results["cpu_time"] = cpu_time

        # GPU测试（如果可用）
        if torch.cuda.is_available():
            try:
                x_gpu = torch.randn(matrix_size, matrix_size).cuda()
                torch.cuda.synchronize()

                start_time = time.time()
                torch.matmul(x_gpu, x_gpu.t())
                torch.cuda.synchronize()
                gpu_time = time.time() - start_time

                results["gpu_time"] = gpu_time
                results["speedup"] = cpu_time / gpu_time
            except RuntimeError as e:
                logger.error(f"GPU性能测试失败: {e}")
                results["gpu_error"] = str(e)
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        results["error"] = str(e)

    return results


def validate_environment() -> None:
    """验证系统环境并运行性能测试。

    此函数会检查系统配置、内存状态、GPU可用性，并运行性能测试。
    所有结果都会通过日志记录，如果发生错误也会被捕获和记录。
    """
    try:
        # 系统信息
        sys_info = get_system_info()
        logger.info("系统信息:")
        logger.info(f"操作系统: {sys_info['os']}")
        logger.info(f"Python版本: {sys_info['python_version']}")

        # 内存信息
        mem_info = get_memory_info()
        logger.info("内存信息:")
        logger.info(f"系统内存: 总计 {mem_info['total_gb']:.1f}GB, "
                   f"可用 {mem_info['available_gb']:.1f}GB")

        # PyTorch和GPU信息
        logger.info(f"PyTorch版本: {torch.__version__}")
        logger.info(f"CUDA是否可用: {torch.cuda.is_available()}")

        gpu_info = get_gpu_info()
        if gpu_info:
            logger.info("GPU信息:")
            logger.info(f"CUDA版本: {gpu_info['cuda_version']}")
            logger.info(f"当前GPU设备: {gpu_info['device_name']}")
            logger.info(f"GPU显存: {gpu_info['memory_gb']:.1f}GB")

        # 性能测试
        matrix_size = 2000
        logger.info(f"\n执行{matrix_size}x{matrix_size}矩阵乘法性能测试:")
        results = run_performance_test(matrix_size)

        if "error" in results:
            logger.error(f"性能测试失败: {results['error']}")
            return

        logger.info(f"CPU计算时间: {results['cpu_time']:.3f}秒")
        if "gpu_time" in results:
            logger.info(f"GPU计算时间: {results['gpu_time']:.3f}秒")
            logger.info(f"GPU加速比: {results['speedup']:.1f}x")
        elif "gpu_error" in results:
            logger.error(f"GPU测试失败: {results['gpu_error']}")

    except Exception as e:
        logger.error(f"环境验证失败: {e}")


if __name__ == "__main__":
    validate_environment()
