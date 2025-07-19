#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微架构探测与调优模块 - VisionAI-ClipsMaster
根据CPU微架构(Intel/AMD/ARM)特性细粒度优化缓存使用和内存访问

此模块提供以下功能:
1. 精确识别CPU微架构(Ice Lake/Zen/Skylake等)
2. 根据微架构特性自动调整预取距离
3. 优化缓存行大小设置
4. 调整分支预测策略
5. 配置循环展开因子
"""

import os
import sys
import platform
import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import re

# 设置日志
logger = logging.getLogger(__name__)

# 尝试导入cpuinfo库
try:
    import cpuinfo
    HAS_CPUINFO = True
except ImportError:
    HAS_CPUINFO = False
    logger.warning("py-cpuinfo库不可用，微架构检测能力受限")

# 尝试导入CPU特性检测器
try:
    from src.utils.cpu_feature import CPUFeatureDetector
    HAS_CPU_DETECTOR = True
except ImportError:
    HAS_CPU_DETECTOR = False
    logger.warning("CPU特性检测器不可用，将使用基础微架构检测")

# Intel微架构代号和对应优化参数
INTEL_ARCHS = {
    # 新架构
    'alder lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 12
    },
    'rocket lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 11
    },
    'tiger lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 11
    },
    'ice lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'moderate',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 10
    },
    # 经典架构
    'skylake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 9
    },
    'kaby lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 9
    },
    'coffee lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 9
    },
    'broadwell': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 8
    },
    'haswell': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 7
    },
    # 老架构
    'ivy bridge': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 4,
        'branch_prediction': 'conservative',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 6
    },
    'sandy bridge': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 4,
        'branch_prediction': 'conservative',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 5
    },
    # 服务器系列
    'cascade lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 9
    },
    'cooper lake': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 10
    },
    # 默认Intel架构
    'intel': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 0
    }
}

# AMD微架构代号和对应优化参数
AMD_ARCHS = {
    # 新一代Zen架构
    'zen 4': {
        'cache_line_size': 64,
        'prefetch_distance': 256,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 4
    },
    'zen 3': {
        'cache_line_size': 64,
        'prefetch_distance': 256,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 3
    },
    'zen 2': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 2
    },
    'zen+': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 1
    },
    'zen': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 1
    },
    # 经典架构
    'excavator': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 4,
        'branch_prediction': 'conservative',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 0
    },
    'bulldozer': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 2,
        'branch_prediction': 'conservative',
        'simd_alignment': 16,
        'memory_pattern': 'standard',
        'generation': 0
    },
    # EPYC服务器系列
    'epyc': {
        'cache_line_size': 64,
        'prefetch_distance': 256,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 3
    },
    # 默认AMD架构
    'amd': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 0
    }
}

# ARM微架构代号和对应优化参数
ARM_ARCHS = {
    # Apple Silicon
    'apple m1': {
        'cache_line_size': 128,
        'prefetch_distance': 256,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 1
    },
    'apple m2': {
        'cache_line_size': 128,
        'prefetch_distance': 256,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 64,
        'memory_pattern': 'non_temporal',
        'generation': 2
    },
    # ARM Cortex系列
    'cortex-a76': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 76
    },
    'cortex-a78': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 8,
        'branch_prediction': 'aggressive',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 78
    },
    # 高通骁龙系列
    'kryo': {
        'cache_line_size': 64,
        'prefetch_distance': 128,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 32,
        'memory_pattern': 'standard',
        'generation': 0
    },
    # 默认ARM架构
    'arm': {
        'cache_line_size': 64,
        'prefetch_distance': 64,
        'loop_unroll_factor': 4,
        'branch_prediction': 'moderate',
        'simd_alignment': 16,
        'memory_pattern': 'standard',
        'generation': 0
    }
}

class MicroArchTuner:
    """CPU微架构调优器"""
    
    def __init__(self):
        """初始化微架构调优器"""
        self.cpu_info = self._get_cpu_info()
        self.detected_arch = "unknown"
        self.arch_params = {}
        
        # 检测微架构并加载优化参数
        self._detect_microarchitecture()
        
        logger.info(f"检测到CPU微架构: {self.detected_arch}")
        
    def _get_cpu_info(self) -> Dict:
        """获取CPU详细信息"""
        cpu_info = {
            'brand': 'Unknown',
            'vendor': 'Unknown',
            'family': 'Unknown',
            'model': 0,
            'stepping': 0,
            'arch': platform.machine(),
            'cores': os.cpu_count() or 1
        }
        
        if HAS_CPUINFO:
            try:
                info = cpuinfo.get_cpu_info()
                cpu_info.update({
                    'brand': info.get('brand_raw', 'Unknown'),
                    'vendor': info.get('vendor_id', 'Unknown'),
                    'family': info.get('family', 0),
                    'model': info.get('model', 0),
                    'stepping': info.get('stepping', 0),
                    'flags': info.get('flags', []),
                    'arch': info.get('arch', platform.machine()),
                    'cores': info.get('count', os.cpu_count() or 1)
                })
            except Exception as e:
                logger.warning(f"cpuinfo获取CPU信息失败: {str(e)}")
        
        return cpu_info
    
    def _detect_microarchitecture(self):
        """检测CPU微架构"""
        brand = self.cpu_info.get('brand', '').lower()
        vendor = self.cpu_info.get('vendor', '').lower()
        
        # 默认架构参数
        if 'intel' in vendor or 'intel' in brand:
            self.arch_params = INTEL_ARCHS['intel'].copy()
            self.detected_arch = "intel"
        elif 'amd' in vendor or 'amd' in brand:
            self.arch_params = AMD_ARCHS['amd'].copy()
            self.detected_arch = "amd"
        elif 'arm' in vendor or 'arm' in self.cpu_info.get('arch', '').lower() or 'aarch64' in self.cpu_info.get('arch', '').lower():
            self.arch_params = ARM_ARCHS['arm'].copy()
            self.detected_arch = "arm"
        else:
            # 未知架构，使用通用配置
            self.arch_params = {
                'cache_line_size': 64,
                'prefetch_distance': 64,
                'loop_unroll_factor': 4,
                'branch_prediction': 'conservative',
                'simd_alignment': 16,
                'memory_pattern': 'standard',
                'generation': 0
            }
            return
        
        # 尝试匹配具体微架构
        if 'intel' in vendor or 'intel' in brand:
            for arch_name, params in INTEL_ARCHS.items():
                if arch_name != 'intel' and arch_name in brand:
                    self.arch_params = params.copy()
                    self.detected_arch = arch_name
                    return
            
            # 如果没有直接匹配，尝试通过型号推断
            family = self.cpu_info.get('family', 0)
            model = self.cpu_info.get('model', 0)
            
            # Intel Core系列推断
            if 'core' in brand:
                if family == 6:
                    # 按型号推断架构
                    if model >= 140:
                        self.arch_params = INTEL_ARCHS['alder lake'].copy()
                        self.detected_arch = "alder lake"
                    elif model >= 110:
                        self.arch_params = INTEL_ARCHS['tiger lake'].copy()
                        self.detected_arch = "tiger lake"
                    elif model >= 106:
                        self.arch_params = INTEL_ARCHS['ice lake'].copy()
                        self.detected_arch = "ice lake"
                    elif model >= 85:
                        self.arch_params = INTEL_ARCHS['coffee lake'].copy()
                        self.detected_arch = "coffee lake"
                    elif model >= 78:
                        self.arch_params = INTEL_ARCHS['kaby lake'].copy()
                        self.detected_arch = "kaby lake"
                    elif model >= 69:
                        self.arch_params = INTEL_ARCHS['skylake'].copy()
                        self.detected_arch = "skylake"
                    elif model >= 60:
                        self.arch_params = INTEL_ARCHS['broadwell'].copy()
                        self.detected_arch = "broadwell"
                    elif model >= 45:
                        self.arch_params = INTEL_ARCHS['haswell'].copy()
                        self.detected_arch = "haswell"
                    elif model >= 42:
                        self.arch_params = INTEL_ARCHS['ivy bridge'].copy()
                        self.detected_arch = "ivy bridge"
                    elif model >= 37:
                        self.arch_params = INTEL_ARCHS['sandy bridge'].copy()
                        self.detected_arch = "sandy bridge"
        
        elif 'amd' in vendor or 'amd' in brand:
            for arch_name, params in AMD_ARCHS.items():
                if arch_name != 'amd' and arch_name in brand:
                    self.arch_params = params.copy()
                    self.detected_arch = arch_name
                    return
            
            # Ryzen系列推断
            if 'ryzen' in brand:
                ryzen_gen = 0
                if 'ryzen 9' in brand or 'ryzen 7' in brand or 'ryzen 5' in brand or 'ryzen 3' in brand:
                    # 尝试从型号中提取信息
                    model_match = re.search(r'\d(\d{3})', brand)
                    if model_match:
                        model_num = model_match.group(1)
                        if model_num.startswith('7'):
                            self.arch_params = AMD_ARCHS['zen 4'].copy()
                            self.detected_arch = "zen 4"
                        elif model_num.startswith('5'):
                            self.arch_params = AMD_ARCHS['zen 3'].copy()
                            self.detected_arch = "zen 3"
                        elif model_num.startswith('3'):
                            self.arch_params = AMD_ARCHS['zen 2'].copy()
                            self.detected_arch = "zen 2"
                        elif model_num.startswith('2'):
                            self.arch_params = AMD_ARCHS['zen+'].copy()
                            self.detected_arch = "zen+"
                        else:
                            self.arch_params = AMD_ARCHS['zen'].copy()
                            self.detected_arch = "zen"
        
        elif 'arm' in vendor or 'arm' in self.cpu_info.get('arch', '').lower() or 'aarch64' in self.cpu_info.get('arch', '').lower():
            for arch_name, params in ARM_ARCHS.items():
                if arch_name != 'arm' and arch_name in brand:
                    self.arch_params = params.copy()
                    self.detected_arch = arch_name
                    return
            
            # Apple Silicon检测
            if 'apple' in brand:
                if 'm2' in brand:
                    self.arch_params = ARM_ARCHS['apple m2'].copy()
                    self.detected_arch = "apple m2"
                elif 'm1' in brand:
                    self.arch_params = ARM_ARCHS['apple m1'].copy()
                    self.detected_arch = "apple m1"
    
    def get_tuning_params(self) -> Dict[str, Any]:
        """
        获取根据当前CPU微架构优化的参数
        
        Returns:
            Dict[str, Any]: 优化参数字典
        """
        return self.arch_params.copy()
    
    def tune_for_microarch(self) -> Dict[str, Any]:
        """
        根据CPU微架构调整参数
        
        Returns:
            Dict[str, Any]: 配置参数字典
        """
        logger.info(f"根据CPU微架构调整参数: {self.detected_arch}")
        
        uarch = self.cpu_info.get('brand_raw', '').lower()
        config = {
            'cache_line_size': self.arch_params['cache_line_size'],
            'prefetch_distance': self.arch_params['prefetch_distance'],
            'loop_unroll_factor': self.arch_params['loop_unroll_factor'],
            'branch_prediction': self.arch_params['branch_prediction'],
            'simd_alignment': self.arch_params['simd_alignment'],
            'memory_pattern': self.arch_params['memory_pattern']
        }
        
        # Intel架构特殊调整
        if 'gold' in uarch:  # Intel Gold系列
            config['cache_line_size'] = 64
            config['prefetch_distance'] = 128
        elif 'epyc' in uarch:  # AMD EPYC
            config['cache_line_size'] = 64
            config['prefetch_distance'] = 256
            
        # 确保缓存行大小是2的幂
        config['cache_line_size'] = max(16, min(128, config['cache_line_size']))
        
        # 确保预取距离合理
        config['prefetch_distance'] = max(config['cache_line_size'], 
                                         min(512, config['prefetch_distance']))
        
        return config
    
    def get_memory_access_pattern(self) -> str:
        """
        获取推荐的内存访问模式
        
        Returns:
            str: 内存访问模式 (standard/streaming/random/mixed)
        """
        # 基于架构推荐最佳内存访问模式
        if self.detected_arch in ['alder lake', 'tiger lake', 'zen 4', 'zen 3', 'apple m2', 'apple m1']:
            return 'streaming'  # 现代架构支持流式访问优化
        elif self.detected_arch in ['skylake', 'kaby lake', 'zen 2', 'zen+']:
            return 'mixed'  # 中间代架构使用混合模式
        else:
            return 'standard'  # 较老架构使用标准模式
    
    def get_simd_width(self) -> int:
        """
        获取当前架构的最佳SIMD宽度
        
        Returns:
            int: SIMD宽度(位)
        """
        # 基于架构返回最佳SIMD宽度
        if self.arch_params.get('simd_alignment', 0) >= 64:
            return 512  # AVX-512支持
        elif self.arch_params.get('simd_alignment', 0) >= 32:
            return 256  # AVX/AVX2支持
        else:
            return 128  # SSE/NEON支持
            
    def optimize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据微架构优化应用配置
        
        Args:
            config: 原始配置字典
            
        Returns:
            Dict[str, Any]: 优化后的配置
        """
        arch_params = self.get_tuning_params()
        
        # 合并配置，保留原始键值
        optimized = config.copy()
        
        # 仅优化性能相关参数
        if 'performance' in optimized:
            perf_config = optimized['performance']
            if isinstance(perf_config, dict):
                # 优化内存和计算相关配置
                if 'memory' in perf_config:
                    perf_config['memory'].update({
                        'prefetch_enabled': True,
                        'prefetch_distance': arch_params['prefetch_distance'],
                        'alignment': arch_params['simd_alignment'],
                        'access_pattern': self.get_memory_access_pattern()
                    })
                
                # 优化计算配置
                if 'compute' in perf_config:
                    perf_config['compute'].update({
                        'unroll_factor': arch_params['loop_unroll_factor'],
                        'simd_width': self.get_simd_width(),
                        'branch_strategy': arch_params['branch_prediction']
                    })
        
        return optimized

# 全局单例
_microarch_tuner = None

def get_microarch_tuner() -> MicroArchTuner:
    """
    获取微架构调优器单例
    
    Returns:
        MicroArchTuner: 微架构调优器实例
    """
    global _microarch_tuner
    
    if _microarch_tuner is None:
        _microarch_tuner = MicroArchTuner()
        
    return _microarch_tuner

def tune_for_microarch() -> Dict[str, Any]:
    """
    根据CPU微架构调整参数
    
    Returns:
        Dict[str, Any]: 优化参数字典
    """
    tuner = get_microarch_tuner()
    return tuner.tune_for_microarch()

def get_optimal_memory_pattern() -> str:
    """
    获取当前架构的最佳内存访问模式
    
    Returns:
        str: 内存访问模式
    """
    tuner = get_microarch_tuner()
    return tuner.get_memory_access_pattern()

# 测试入口
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试微架构调优
    tuner = get_microarch_tuner()
    print(f"检测到CPU微架构: {tuner.detected_arch}")
    
    # 获取优化参数
    params = tuner.tune_for_microarch()
    print("优化参数:")
    for k, v in params.items():
        print(f"  {k}: {v}")
        
    # 测试内存访问模式
    memory_pattern = tuner.get_memory_access_pattern()
    print(f"推荐内存访问模式: {memory_pattern}")
    
    # 测试SIMD宽度
    simd_width = tuner.get_simd_width()
    print(f"推荐SIMD宽度: {simd_width}位") 