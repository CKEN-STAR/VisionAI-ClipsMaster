#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存探针C扩展包装器

此模块提供Python接口来调用C语言实现的高性能内存探针。
"""

import os
import sys
import ctypes
import logging
import platform
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# 配置日志
logger = logging.getLogger("ProbeWrapper")

# 支持平台
SUPPORTED_PLATFORMS = {
    "Windows": {
        "extension": ".dll",
        "prefix": "",
    },
    "Linux": {
        "extension": ".so",
        "prefix": "lib",
    },
    "Darwin": {  # macOS
        "extension": ".dylib",
        "prefix": "lib",
    }
}

# 内存探针结果数据结构
class MemoryProbeResult(ctypes.Structure):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """C语言内存探针结果的Python表示"""
    _fields_ = [
        ("current_memory", ctypes.c_uint64),  # 当前内存使用量（MB）
        ("peak_memory", ctypes.c_uint64),     # 峰值内存（MB）
        ("available_memory", ctypes.c_uint64), # 可用内存（MB）
        ("timestamp", ctypes.c_uint64),       # 检查时间戳
        ("threshold_exceeded", ctypes.c_int), # 是否超过阈值
        ("error_code", ctypes.c_int),         # 错误代码
    ]

# 内存探针C库包装器
class MemoryProbeWrapper:
    """C内存探针库的Python包装器"""
    
    def __init__(self):
        """初始化内存探针包装器"""
        self.lib = None
        self.initialized = False
        self._initialize()
        
    def _initialize(self) -> bool:
        """
        初始化C库
        
        Returns:
            bool: 初始化是否成功
        """
        if self.initialized:
            return True
            
        try:
            # 确定当前平台
            system = platform.system()
            if system not in SUPPORTED_PLATFORMS:
                logger.error(f"不支持的平台: {system}")
                return False
                
            platform_info = SUPPORTED_PLATFORMS[system]
            
            # 确定库文件路径
            probe_dir = Path(__file__).parent
            probe_root = probe_dir.parent.parent  # 项目根目录
            
            # 可能的库文件路径
            lib_paths = [
                # 当前目录
                probe_dir / f"{platform_info['prefix']}memory_probes{platform_info['extension']}",
                # lib目录
                probe_root / "lib" / f"{platform_info['prefix']}memory_probes{platform_info['extension']}",
                # build目录
                probe_root / "build" / "lib" / f"{platform_info['prefix']}memory_probes{platform_info['extension']}",
                # 系统路径
                Path(f"{platform_info['prefix']}memory_probes{platform_info['extension']}"),
            ]
            
            # 尝试加载库
            for lib_path in lib_paths:
                try:
                    logger.debug(f"尝试加载内存探针库: {lib_path}")
                    self.lib = ctypes.cdll.LoadLibrary(str(lib_path))
                    break
                except (OSError, ImportError) as e:
                    logger.debug(f"加载失败: {e}")
                    continue
            
            if not self.lib:
                logger.warning("未找到内存探针库，将尝试编译")
                if self._build_probe_library():
                    # 重新尝试加载
                    for lib_path in lib_paths:
                        try:
                            self.lib = ctypes.cdll.LoadLibrary(str(lib_path))
                            break
                        except (OSError, ImportError):
                            continue
            
            if not self.lib:
                logger.error("无法加载内存探针库")
                return False
                
            # 配置函数签名
            self._configure_functions()
            
            self.initialized = True
            logger.info("内存探针C库加载成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化内存探针库失败: {str(e)}")
            return False
            
    def _build_probe_library(self) -> bool:
        """
        尝试编译内存探针库
        
        Returns:
            bool: 编译是否成功
        """
        try:
            # 确定源文件和目标文件
            probe_dir = Path(__file__).parent
            source_file = probe_dir / "memory_probes.c"
            
            if not source_file.exists():
                logger.error(f"找不到源文件: {source_file}")
                return False
            
            # 确定平台
            system = platform.system()
            platform_info = SUPPORTED_PLATFORMS[system]
            
            # 构建目标文件路径
            build_dir = probe_dir.parent.parent / "build" / "lib"
            build_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = build_dir / f"{platform_info['prefix']}memory_probes{platform_info['extension']}"
            
            # 构建编译命令
            if system == "Windows":
                cmd = f'cl /LD "{source_file}" /Fe"{output_file}" /DMEMORY_PROBE_MAIN /I"C:\\Program Files (x86)\\Windows Kits\\10\\Include\\10.0.19041.0\\ucrt"'
            else:  # Linux/macOS
                cmd = f'gcc -shared -fPIC -o "{output_file}" "{source_file}" -DMEMORY_PROBE_MAIN'
            
            logger.info(f"编译内存探针库: {cmd}")
            
            # 执行编译
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"编译失败: {result.stderr}")
                return False
                
            logger.info(f"内存探针库编译成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"编译内存探针库时出错: {str(e)}")
            return False
            
    def _configure_functions(self):
        """配置C库函数签名"""
        if not self.lib:
            return
            
        # 配置check_memory_usage函数
        self.lib.check_memory_usage.argtypes = [
            ctypes.c_char_p,       # probe_name
            ctypes.c_uint64,       # threshold
            ctypes.POINTER(MemoryProbeResult)  # result
        ]
        self.lib.check_memory_usage.restype = ctypes.c_int
        
        # 配置fast_mem_check函数
        self.lib.fast_mem_check.argtypes = [ctypes.c_uint64]  # threshold
        self.lib.fast_mem_check.restype = None
        
        # 配置test_memory_probe函数
        self.lib.test_memory_probe.argtypes = []
        self.lib.test_memory_probe.restype = ctypes.c_int
        
    def check_memory(self, 
                    probe_name: str, 
                    threshold_mb: int = 0) -> Dict[str, Any]:
        """
        检查内存使用情况
        
        Args:
            probe_name: 探针名称
            threshold_mb: 内存阈值（MB），0表示不设阈值
            
        Returns:
            包含内存使用情况的字典
        """
        if not self.initialized:
            if not self._initialize():
                return {"error": "探针库未初始化"}
        
        if not self.lib:
            return {"error": "探针库未加载"}
            
        result = MemoryProbeResult()
        probe_name_bytes = probe_name.encode('utf-8')
        
        status = self.lib.check_memory_usage(
            probe_name_bytes, 
            ctypes.c_uint64(threshold_mb),
            ctypes.byref(result)
        )
        
        return {
            "current_memory_mb": result.current_memory,
            "peak_memory_mb": result.peak_memory,
            "available_memory_mb": result.available_memory,
            "timestamp": result.timestamp,
            "threshold_exceeded": bool(result.threshold_exceeded),
            "status": status,
            "probe_name": probe_name,
            "threshold_mb": threshold_mb
        }
        
    def fast_check(self, threshold_mb: int) -> None:
        """
        快速内存检查（无结果返回，仅在超过阈值时记录日志）
        
        Args:
            threshold_mb: 内存阈值（MB）
        """
        if not self.initialized:
            if not self._initialize():
                return
        
        if not self.lib:
            return
            
        self.lib.fast_mem_check(ctypes.c_uint64(threshold_mb))
        
    def test_probe(self) -> Dict[str, Any]:
        """
        测试内存探针
        
        Returns:
            测试结果
        """
        if not self.initialized:
            if not self._initialize():
                return {"error": "探针库未初始化"}
        
        if not self.lib:
            return {"error": "探针库未加载"}
            
        status = self.lib.test_memory_probe()
        
        return {
            "status": status,
            "test_success": status == 0
        }

# 全局单例
_PROBE_WRAPPER = None

def get_probe_wrapper() -> MemoryProbeWrapper:
    """获取内存探针包装器单例"""
    global _PROBE_WRAPPER
    if _PROBE_WRAPPER is None:
        _PROBE_WRAPPER = MemoryProbeWrapper()
    return _PROBE_WRAPPER

def check_memory(probe_name: str, threshold_mb: int = 0) -> Dict[str, Any]:
    """
    便捷函数：检查内存使用情况
    
    Args:
        probe_name: 探针名称
        threshold_mb: 内存阈值（MB），0表示不设阈值
        
    Returns:
        包含内存使用情况的字典
    """
    return get_probe_wrapper().check_memory(probe_name, threshold_mb)

def fast_check(threshold_mb: int) -> None:
    """
    便捷函数：快速内存检查
    
    Args:
        threshold_mb: 内存阈值（MB）
    """
    get_probe_wrapper().fast_check(threshold_mb)

if __name__ == "__main__":
    # 配置日志记录
    logging.basicConfig(level=logging.DEBUG, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 测试内存探针
    wrapper = get_probe_wrapper()
    
    # 测试探针初始化
    print("探针库初始化:", "成功" if wrapper.initialized else "失败")
    
    # 测试内存检查
    result = wrapper.check_memory("test_probe", 1000)
    print("\n内存检查结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # 测试内置的测试函数
    test_result = wrapper.test_probe()
    print("\n内置测试结果:", test_result)
    
    # 测试快速检查
    print("\n执行快速检查:")
    wrapper.fast_check(10000)  # 设置较高阈值以不触发警告 