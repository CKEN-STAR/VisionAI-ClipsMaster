#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""硬件适配层

该模块检测当前硬件环境并提供适配不同硬件特性的量化选择方案。
主要功能包括：
1. 检测CPU/GPU特性
2. 识别硬件指令集支持
3. 确定适合的量化方法
4. 动态调整量化参数
5. 提供硬件兼容性报告
"""

import os
import sys
import platform
import json
from typing import Dict, List, Set, Tuple, Optional, Any
import psutil
import torch
import numpy as np
from loguru import logger
import cpuinfo

# 添加项目根目录到路径以解决导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.vram_detector import VRAMDetector
from src.utils.cpu_feature import CPUFeatureDetector
from src.utils.device_manager import HybridDevice, DeviceType

# 量化方法定义
QUANT_METHODS = {
    "Q2_K": {
        "description": "2-bit量化，小型模型",
        "memory_ratio": 0.125,
        "performance_impact": 0.4,
        "quality_ratio": 0.5,
        "min_vram_mb": 0,
        "min_ram_mb": 2048,
        "requires_avx": False,
        "requires_avx2": False,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "Q4_K_M": {
        "description": "4-bit量化，小型模型（内存优化版）",
        "memory_ratio": 0.25,
        "performance_impact": 0.3,
        "quality_ratio": 0.7,
        "min_vram_mb": 0,
        "min_ram_mb": 4096, 
        "requires_avx": True,
        "requires_avx2": False,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "Q4_K": {
        "description": "4-bit量化，小型模型",
        "memory_ratio": 0.25,
        "performance_impact": 0.25,
        "quality_ratio": 0.65,
        "min_vram_mb": 0,
        "min_ram_mb": 4096,
        "requires_avx": True,
        "requires_avx2": False,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "Q5_K": {
        "description": "5-bit量化，中型模型",
        "memory_ratio": 0.31,
        "performance_impact": 0.2,
        "quality_ratio": 0.8,
        "min_vram_mb": 2000,
        "min_ram_mb": 6144,
        "requires_avx": True,
        "requires_avx2": True,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "Q6_K": {
        "description": "6-bit量化，中大型模型",
        "memory_ratio": 0.375,
        "performance_impact": 0.15,
        "quality_ratio": 0.85,
        "min_vram_mb": 3000,
        "min_ram_mb": 8192,
        "requires_avx": True,
        "requires_avx2": True,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "Q8_0": {
        "description": "8-bit量化，大型模型",
        "memory_ratio": 0.5,
        "performance_impact": 0.1,
        "quality_ratio": 0.9,
        "min_vram_mb": 4000,
        "min_ram_mb": 12288,
        "requires_avx": True,
        "requires_avx2": True,
        "requires_avx512": False,
        "requires_cuda": False
    },
    "F16": {
        "description": "16-bit半精度浮点，完整模型",
        "memory_ratio": 1.0,
        "performance_impact": 0.05,
        "quality_ratio": 1.0,
        "min_vram_mb": 8000,
        "min_ram_mb": 16384,
        "requires_avx": True,
        "requires_avx2": True,
        "requires_avx512": False,
        "requires_cuda": True
    }
}

class HardwareAdapter:
    """硬件适配器类"""
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 vram_detector: Optional[VRAMDetector] = None,
                 cpu_detector: Optional[CPUFeatureDetector] = None,
                 device_manager: Optional[HybridDevice] = None):
        """初始化硬件适配器
        
        Args:
            config_path: 配置文件路径
            vram_detector: VRAM检测器实例
            cpu_detector: CPU特性检测器实例
            device_manager: 设备管理器实例
        """
        # 初始化依赖组件
        self.vram_detector = vram_detector or VRAMDetector()
        self.cpu_detector = cpu_detector or CPUFeatureDetector()
        self.device_manager = device_manager or HybridDevice()
        
        # 加载配置（如果提供）
        self.config = self._load_config(config_path) if config_path else {}
        
        # 初始化硬件特性缓存
        self.hardware_info = self._detect_hardware()
        
        # 兼容量化方法缓存
        self.compatible_methods = self._get_compatible_methods()
        
        # 初始化禁用方法集合
        self.disabled_methods: Set[str] = set()
        
        # 记录初始化日志
        logger.info(f"硬件适配器初始化完成，检测到：{self.hardware_info['cpu_model']}, "
                   f"RAM: {self.hardware_info['ram_total_gb']:.1f}GB, "
                   f"VRAM: {self.hardware_info['vram_total_mb']}MB")
        logger.info(f"支持的指令集: {', '.join(self.hardware_info['cpu_features'])}")
        logger.info(f"兼容的量化方法: {', '.join(self.compatible_methods.keys())}")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置信息
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已加载硬件适配配置: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"加载硬件适配配置失败: {str(e)}，将使用默认配置")
            return {}
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """检测硬件特性
        
        Returns:
            Dict: 硬件特性信息
        """
        hardware_info = {}
        
        # CPU信息
        cpu_info = cpuinfo.get_cpu_info()
        hardware_info['cpu_model'] = cpu_info.get('brand_raw', 'Unknown CPU')
        hardware_info['cpu_cores'] = psutil.cpu_count(logical=False)
        hardware_info['cpu_threads'] = psutil.cpu_count(logical=True)
        
        # CPU特性检测
        hardware_info['cpu_features'] = []
        if self.cpu_detector.has_avx():
            hardware_info['cpu_features'].append('AVX')
        if self.cpu_detector.has_avx2():
            hardware_info['cpu_features'].append('AVX2')
        if self.cpu_detector.has_avx512():
            hardware_info['cpu_features'].append('AVX512')
        
        # 构建CPU标志集合
        hardware_info['cpu_flags'] = set()
        if 'flags' in cpu_info:
            hardware_info['cpu_flags'] = set(cpu_info['flags'])
        
        # RAM信息
        memory = psutil.virtual_memory()
        hardware_info['ram_total_bytes'] = memory.total
        hardware_info['ram_total_gb'] = memory.total / (1024**3)
        hardware_info['ram_available_bytes'] = memory.available
        hardware_info['ram_available_gb'] = memory.available / (1024**3)
        
        # GPU/VRAM信息
        hardware_info['gpu_available'] = torch.cuda.is_available()
        hardware_info['vram_total_mb'] = 0
        hardware_info['gpu_name'] = 'None'
        
        if hardware_info['gpu_available']:
            try:
                hardware_info['gpu_name'] = torch.cuda.get_device_name(0)
                hardware_info['vram_total_mb'] = self.vram_detector.get_vram_mb()
            except Exception as e:
                logger.warning(f"获取GPU信息失败: {str(e)}")
                hardware_info['gpu_available'] = False
        
        # 操作系统信息
        hardware_info['os_system'] = platform.system()
        hardware_info['os_release'] = platform.release()
        hardware_info['os_version'] = platform.version()
        
        # 设备类型
        hardware_info['device_type'] = self.device_manager.select_device()
        
        return hardware_info
    
    def _get_compatible_methods(self) -> Dict[str, Dict]:
        """获取与当前硬件兼容的量化方法
        
        Returns:
            Dict: 兼容的量化方法字典
        """
        compatible = {}
        
        # 检查每种量化方法的兼容性
        for method_name, method_info in QUANT_METHODS.items():
            if self._is_method_compatible(method_name, method_info):
                compatible[method_name] = method_info
        
        return compatible
    
    def _is_method_compatible(self, method_name: str, method_info: Dict) -> bool:
        """检查量化方法是否与当前硬件兼容
        
        Args:
            method_name: 方法名称
            method_info: 方法信息
            
        Returns:
            bool: 是否兼容
        """
        # 检查内存需求
        if method_info['min_ram_mb'] > self.hardware_info['ram_total_bytes'] / (1024 * 1024):
            return False
        
        # 检查VRAM需求（如果使用GPU）
        if (method_info['requires_cuda'] and 
            (not self.hardware_info['gpu_available'] or 
             method_info['min_vram_mb'] > self.hardware_info['vram_total_mb'])):
            return False
        
        # 检查CPU指令集需求
        if method_info['requires_avx'] and 'AVX' not in self.hardware_info['cpu_features']:
            return False
        if method_info['requires_avx2'] and 'AVX2' not in self.hardware_info['cpu_features']:
            return False
        if method_info['requires_avx512'] and 'AVX512' not in self.hardware_info['cpu_features']:
            return False
        
        return True
    
    def check_quant_support(self, device_info: Dict[str, Any] = None) -> Dict[str, bool]:
        """检查硬件对量化方法的支持
        
        Args:
            device_info: 设备信息字典，如果为None则使用内部检测的信息
            
        Returns:
            Dict: 各量化方法的支持状态
        """
        # 如果没有提供设备信息，使用内部缓存的信息
        info = device_info if device_info is not None else self.hardware_info
        
        # 初始化结果字典，默认所有方法可用
        support_status = {method: True for method in QUANT_METHODS.keys()}
        
        # 检查GPU VRAM限制
        if 'gpu_vram' in info and info['gpu_vram'] < 2000:
            support_status['Q5_K'] = False
            support_status['Q6_K'] = False
            support_status['Q8_0'] = False
            support_status['F16'] = False
            logger.info("检测到GPU显存小于2GB，禁用高精度量化方法")
            self._disable_method('Q5_K')  # 依据图片中的示例代码
        
        # 检查CPU指令集
        cpu_flags = info.get('cpu_flags', set())
        if isinstance(cpu_flags, list):
            cpu_flags = set(cpu_flags)
        
        if 'avx512' not in cpu_flags and 'avx512f' not in cpu_flags:
            support_status['Q4_K_M'] = False
            logger.info("CPU不支持AVX512指令集，禁用Q4_K_M量化方法")
            self._disable_method('Q4_K_M')  # 依据图片中的示例代码
        
        if 'avx2' not in cpu_flags:
            support_status['Q5_K'] = False
            support_status['Q6_K'] = False
            logger.info("CPU不支持AVX2指令集，禁用高级量化方法")
        
        if 'avx' not in cpu_flags:
            support_status['Q4_K'] = False
            logger.info("CPU不支持AVX指令集，禁用中级量化方法")
        
        # 检查RAM限制
        ram_gb = info.get('ram_total_gb', 0)
        if ram_gb < 4:
            support_status['Q4_K'] = False
            support_status['Q5_K'] = False
            support_status['Q6_K'] = False
            support_status['Q8_0'] = False
            support_status['F16'] = False
            logger.info("系统内存小于4GB，仅启用最低级别量化方法")
        elif ram_gb < 8:
            support_status['Q6_K'] = False
            support_status['Q8_0'] = False
            support_status['F16'] = False
            logger.info("系统内存小于8GB，禁用高级量化方法")
        
        return support_status
    
    def _disable_method(self, method_name: str) -> None:
        """禁用特定量化方法
        
        Args:
            method_name: 要禁用的量化方法名称
        """
        if method_name in self.disabled_methods:
            return
        
        self.disabled_methods.add(method_name)
        logger.info(f"已禁用量化方法: {method_name}")
    
    def get_recommended_methods(self, language: str = 'zh') -> List[str]:
        """获取推荐的量化方法列表
        
        Args:
            language: 语言类型 (zh/en)
            
        Returns:
            List: 推荐的量化方法列表，按优先级排序
        """
        # 过滤出兼容且未被禁用的方法
        available_methods = {
            name: info for name, info in self.compatible_methods.items() 
            if name not in self.disabled_methods
        }
        
        # 为中文模型优先考虑质量因素
        if language == 'zh':
            methods = sorted(
                available_methods.items(),
                key=lambda x: (
                    -x[1]['quality_ratio'],           # 质量优先
                    x[1]['performance_impact'],       # 性能影响其次
                    x[1]['memory_ratio']              # 内存占用最后
                )
            )
        # 为英文模型平衡考虑质量和性能
        else:
            methods = sorted(
                available_methods.items(),
                key=lambda x: (
                    -x[1]['quality_ratio'] * 0.7 - (1 - x[1]['performance_impact']) * 0.3,  # 质量和性能的加权组合
                    x[1]['memory_ratio']              # 内存占用最后
                )
            )
        
        return [name for name, _ in methods]
    
    def get_fallback_chain(self) -> List[str]:
        """获取降级备选链
        
        当首选量化方法不可用时，按此顺序尝试备选方法
        
        Returns:
            List: 降级方法链
        """
        # 基础降级链：从高质量到低质量
        base_chain = ['Q8_0', 'Q6_K', 'Q5_K', 'Q4_K', 'Q4_K_M', 'Q2_K']
        
        # 过滤出可用方法
        return [
            method for method in base_chain 
            if method in self.compatible_methods and method not in self.disabled_methods
        ]
    
    def get_hardware_report(self) -> Dict[str, Any]:
        """生成硬件兼容性报告
        
        Returns:
            Dict: 硬件兼容性报告
        """
        report = {
            "hardware": {
                "cpu": self.hardware_info['cpu_model'],
                "cores": self.hardware_info['cpu_cores'],
                "threads": self.hardware_info['cpu_threads'],
                "features": self.hardware_info['cpu_features'],
                "ram_gb": round(self.hardware_info['ram_total_gb'], 1),
                "gpu": self.hardware_info['gpu_name'],
                "vram_mb": self.hardware_info['vram_total_mb'],
                "os": f"{self.hardware_info['os_system']} {self.hardware_info['os_version']}"
            },
            "compatibility": {
                "methods": {method: method not in self.disabled_methods 
                           for method in QUANT_METHODS.keys()},
                "optimal_methods": {
                    "zh": self.get_recommended_methods("zh")[0] if self.get_recommended_methods("zh") else None,
                    "en": self.get_recommended_methods("en")[0] if self.get_recommended_methods("en") else None
                },
                "fallback_chain": self.get_fallback_chain()
            },
            "recommendations": {
                "upgrade_suggestions": self._get_upgrade_suggestions(),
                "optimization_tips": self._get_optimization_tips()
            }
        }
        
        return report
    
    def _get_upgrade_suggestions(self) -> List[str]:
        """获取硬件升级建议
        
        Returns:
            List: 升级建议列表
        """
        suggestions = []
        
        # 内存建议
        if self.hardware_info['ram_total_gb'] < 8:
            suggestions.append("建议将系统内存升级到至少8GB以提升性能")
        
        # GPU建议
        if not self.hardware_info['gpu_available']:
            suggestions.append("添加支持CUDA的GPU将显著提升模型推理速度")
        elif self.hardware_info['vram_total_mb'] < 4000:
            suggestions.append("建议使用至少4GB显存的GPU来支持更高效的模型推理")
        
        # CPU建议
        if 'AVX2' not in self.hardware_info['cpu_features']:
            suggestions.append("升级到支持AVX2指令集的CPU将提升量化模型性能")
        
        return suggestions
    
    def _get_optimization_tips(self) -> List[str]:
        """获取优化建议
        
        Returns:
            List: 优化建议列表
        """
        tips = []
        
        # 内存优化
        if self.hardware_info['ram_total_gb'] < 16:
            tips.append("运行模型时关闭其他内存密集型应用")
            tips.append("使用系统分页文件/交换空间扩展可用内存")
        
        # GPU优化
        if self.hardware_info['gpu_available']:
            tips.append("保持GPU驱动更新以获得最佳性能")
            tips.append("使用专用GPU而非集成显卡来处理模型计算")
        
        # 低端设备建议
        if self.hardware_info['ram_total_gb'] < 4:
            tips.append("考虑使用更激进的模型剪枝或量化以适应低内存环境")
            tips.append("采用分段处理策略，避免一次加载整个模型")
        
        return tips


def get_hardware_adapter() -> HardwareAdapter:
    """获取硬件适配器单例
    
    Returns:
        HardwareAdapter: 硬件适配器实例
    """
    if not hasattr(get_hardware_adapter, "_instance") or get_hardware_adapter._instance is None:
        get_hardware_adapter._instance = HardwareAdapter()
    return get_hardware_adapter._instance


def check_quant_support(device_info: Dict[str, Any]) -> Dict[str, bool]:
    """检查硬件对量化方法的支持
    
    Args:
        device_info: 设备信息字典
        
    Returns:
        Dict: 各量化方法的支持状态
    """
    adapter = get_hardware_adapter()
    return adapter.check_quant_support(device_info)


def disable_method(method_name: str) -> None:
    """禁用特定量化方法
    
    Args:
        method_name: 要禁用的量化方法名称
    """
    adapter = get_hardware_adapter()
    adapter._disable_method(method_name)


def get_recommended_method(language: str = 'zh') -> str:
    """获取推荐的量化方法
    
    Args:
        language: 语言类型 (zh/en)
        
    Returns:
        str: 推荐的量化方法
    """
    adapter = get_hardware_adapter()
    methods = adapter.get_recommended_methods(language)
    return methods[0] if methods else "Q4_K"  # 默认回退到Q4_K


if __name__ == "__main__":
    """模块测试入口"""
    # 创建适配器实例
    adapter = HardwareAdapter()
    
    # 打印硬件报告
    report = adapter.get_hardware_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 检查量化方法兼容性
    support = adapter.check_quant_support()
    print("\n量化方法兼容性:")
    for method, supported in support.items():
        print(f"  {method}: {'✓' if supported else '✗'}")
    
    # 获取推荐方法
    print("\n推荐量化方法:")
    print(f"  中文模型: {get_recommended_method('zh')}")
    print(f"  英文模型: {get_recommended_method('en')}") 