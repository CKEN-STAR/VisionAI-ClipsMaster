#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令集优化路由器 - VisionAI-ClipsMaster
根据CPU支持的指令集选择最佳优化路径

该模块可以检测设备CPU支持的指令集，并为模型推理选择最佳的优化路径。
支持的优化路径包括：
- AVX512: 适用于支持AVX512指令集的现代Intel CPU
- AVX2: 适用于支持AVX2指令集的CPU
- AVX: 适用于支持AVX指令集的CPU
- SSE4.2: 适用于支持SSE4.2的CPU
- NEON: 适用于ARM处理器
- 基线: 基础实现，适用于不支持任何高级指令集的CPU
"""

import os
import sys
import platform
import logging
from typing import Dict, List, Set, Optional, Tuple, Union
import json
from pathlib import Path
import time
import numpy as np

# 添加项目根目录到路径（当作为脚本运行时）
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    sys.path.insert(0, str(project_root))
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# 设置日志
logger = logging.getLogger(__name__)

# 导入CPU特性检测器
from src.utils.cpu_feature import CPUFeatureDetector

# 尝试导入汇编优化包装器
try:
    from src.hardware.assembly_wrapper import get_platform_asm
    HAS_ASSEMBLY = True
except ImportError:
    HAS_ASSEMBLY = False
    logger.warning("未找到平台汇编优化模块，将使用标准实现")

# 尝试导入SIMD操作
try:
    from src.hardware.simd_wrapper import get_simd_operations as create_simd_operations
    HAS_SIMD = True
except ImportError:
    HAS_SIMD = False
    logger.warning("未找到SIMD向量化模块，将使用标准NumPy实现")

# 尝试导入内存对齐模块
try:
    from src.hardware.memory_aligner import (
        get_alignment_for_simd, create_aligned_array, align_array, is_aligned
    )
    HAS_MEMORY_ALIGNMENT = True
except ImportError:
    HAS_MEMORY_ALIGNMENT = False
    logger.warning("未找到内存对齐模块，将使用标准内存访问")

# 尝试导入指令级并行模块
try:
    from src.hardware.parallel_scheduler import ParallelScheduler, schedule_instructions
    HAS_PARALLEL_SCHEDULER = True
except ImportError:
    HAS_PARALLEL_SCHEDULER = False
    logger.warning("未找到指令级并行模块，将使用串行处理")

class OptimizationRouter:
    """指令集优化路由器，选择最佳的优化路径"""
    
    def __init__(self):
        """初始化优化路由器"""
        self.cpu_detector = CPUFeatureDetector()
        self.instruction_sets = self.cpu_detector.instruction_sets
        self.optimization_path = self._select_optimization_path()
        
        # 初始化平台汇编优化实例
        self.platform_asm = self._init_platform_asm()
        
        # 内存对齐配置
        self.memory_alignment = self._get_optimal_alignment()
        
        # 并行处理配置
        self.parallel_scheduler = self._init_parallel_scheduler()
        
    def _init_platform_asm(self):
        """初始化平台汇编优化实例"""
        if HAS_ASSEMBLY:
            try:
                return get_platform_asm()
            except Exception as e:
                logger.error(f"初始化平台汇编优化失败: {str(e)}")
                return None
        return None

    def _select_optimization_path(self) -> str:
        """
        根据CPU支持的指令集选择最佳优化路径
        
        Returns:
            str: 优化路径名称
        """
        # 检查AVX512支持
        if self.instruction_sets.get('avx512f', False):
            return 'avx512'
            
        # 检查AVX2支持
        if self.instruction_sets.get('avx2', False):
            return 'avx2'
            
        # 检查AVX支持
        if self.instruction_sets.get('avx', False):
            return 'avx'
            
        # 检查SSE4.2支持
        if self.instruction_sets.get('sse4_2', False):
            return 'sse4.2'
            
        # 检查NEON支持(ARM架构)
        if self.instruction_sets.get('neon', False):
            return 'neon'
            
        # 默认返回基线优化
        return 'baseline'
        
    def get_optimization_path(self) -> str:
        """
        获取当前选择的优化路径
        
        Returns:
            str: 优化路径名称
        """
        return self.optimization_path
        
    def get_optimization_level(self) -> Dict:
        """
        获取优化级别及相关信息
        
        Returns:
            Dict: 优化级别信息字典
        """
        levels = {
            'avx512': {
                'name': 'AVX512',
                'description': '激进优化 (8线程并行)',
                'parallel_threads': 8,
                'simd_width': 512,
                'performance_rating': 100,
                'simd_type': 'avx512',
                'ilp_enabled': True
            },
            'avx2': {
                'name': 'AVX2',
                'description': '平衡优化 (4线程)',
                'parallel_threads': 4,
                'simd_width': 256,
                'performance_rating': 80,
                'simd_type': 'avx2',
                'ilp_enabled': True
            },
            'avx': {
                'name': 'AVX',
                'description': '适度优化 (2线程)',
                'parallel_threads': 2,
                'simd_width': 256,
                'performance_rating': 70,
                'simd_type': 'avx',
                'ilp_enabled': True
            },
            'sse4.2': {
                'name': 'SSE4.2',
                'description': '基础向量优化',
                'parallel_threads': 2,
                'simd_width': 128,
                'performance_rating': 60,
                'simd_type': 'sse4.2',
                'ilp_enabled': True
            },
            'neon': {
                'name': 'NEON',
                'description': 'ARM特化优化',
                'parallel_threads': 4,
                'simd_width': 128,
                'performance_rating': 75,
                'simd_type': 'neon',
                'ilp_enabled': True
            },
            'baseline': {
                'name': '基线',
                'description': '基础实现',
                'parallel_threads': 1,
                'simd_width': 64,
                'performance_rating': 40,
                'simd_type': 'baseline',
                'ilp_enabled': False
            }
        }
        
        # 获取当前路径的详细信息
        current_level = levels.get(self.optimization_path, levels['baseline'])
        current_level['active'] = True
        
        return current_level
        
    def get_model_parameters(self, model_name: str) -> Dict:
        """
        获取特定模型的优化参数
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict: 优化参数
        """
        # 基础参数
        base_params = {
            'threads': 1,
            'batch_size': 1,
            'use_flash_attn': False,
            'compile_model': False,
            'use_ilp': False
        }
        
        # 根据优化路径设置特定参数
        if self.optimization_path == 'avx512':
            base_params['threads'] = 8
            base_params['batch_size'] = 4
            base_params['use_flash_attn'] = True
            base_params['compile_model'] = True
            base_params['use_ilp'] = True
            
        elif self.optimization_path == 'avx2':
            base_params['threads'] = 4
            base_params['batch_size'] = 2
            base_params['use_flash_attn'] = True
            base_params['compile_model'] = True
            base_params['use_ilp'] = True
            
        elif self.optimization_path == 'avx':
            base_params['threads'] = 2
            base_params['batch_size'] = 2
            base_params['use_ilp'] = True
            
        elif self.optimization_path == 'neon':
            base_params['threads'] = 4
            base_params['batch_size'] = 2
            base_params['use_ilp'] = True
            
        elif self.optimization_path == 'sse4.2':
            base_params['threads'] = 2
            base_params['use_ilp'] = True
            
        # 为特定模型进行调整
        if 'qwen' in model_name.lower():
            if self.optimization_path in ['avx512', 'avx2']:
                base_params['use_flash_attn'] = True
                
        elif 'mistral' in model_name.lower():
            if self.optimization_path in ['avx512', 'avx2', 'avx']:
                base_params['use_flash_attn'] = True
                
        return base_params
        
    def get_simd_operations(self):
        """
        获取适合当前优化路径的SIMD操作对象
        
        Returns:
            SimdOperations: SIMD操作对象，如果不可用则返回None
        """
        if not HAS_SIMD:
            return None
            
        # 获取当前优化路径对应的SIMD类型
        level = self.get_optimization_level()
        simd_type = level.get('simd_type', 'baseline')
        
        # 创建SIMD操作对象
        return create_simd_operations(simd_type)
        
    def get_assembly_operations(self):
        """
        获取适合当前平台的汇编优化操作对象
        
        Returns:
            PlatformAsm: 平台汇编优化对象，如果不可用则返回None
        """
        return self.platform_asm
        
    def export_config(self, config_path: Optional[str] = None) -> str:
        """
        导出优化配置到文件
        
        Args:
            config_path: 配置文件路径，如果不提供则使用默认路径
            
        Returns:
            str: 配置文件路径
        """
        if config_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, 'configs', 'optimization.json')
        
        # 创建配置目录(如果不存在)
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 获取当前配置
        config = {
            'optimization_path': self.optimization_path,
            'cpu_features': {k: v for k, v in self.instruction_sets.items() if v},
            'details': self.get_optimization_level(),
            'model_parameters': {
                'qwen2.5-7b-zh': self.get_model_parameters('qwen2.5-7b-zh'),
                'mistral-7b-en': self.get_model_parameters('mistral-7b-en')
            },
            'has_simd': HAS_SIMD,
            'has_assembly': HAS_ASSEMBLY
        }
        
        # 添加SIMD性能测试结果
        if HAS_SIMD:
            try:
                simd_ops = self.get_simd_operations()
                if simd_ops:
                    config['simd_performance'] = simd_ops.get_performance_stats()
            except Exception as e:
                logger.warning(f"获取SIMD性能统计时出错: {str(e)}")
                
        # 添加汇编库信息
        if HAS_ASSEMBLY and self.platform_asm:
            try:
                config['assembly_info'] = self.platform_asm.get_library_info()
            except Exception as e:
                logger.warning(f"获取汇编库信息时出错: {str(e)}")
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
        logger.info(f"优化配置已保存到: {config_path}")
        return config_path

    def _get_optimal_alignment(self) -> int:
        """
        获取当前平台的最佳内存对齐值
        
        Returns:
            int: 最佳内存对齐字节数
        """
        if HAS_MEMORY_ALIGNMENT:
            return get_alignment_for_simd(self.optimization_path)
        else:
            # 根据指令集提供默认对齐值
            if 'avx512' in self.optimization_path:
                return 64
            elif 'avx' in self.optimization_path:
                return 32
            elif 'sse' in self.optimization_path:
                return 16
            elif 'neon' in self.optimization_path:
                return 16
            else:
                return 8
                
    def get_memory_alignment(self) -> int:
        """
        获取当前平台推荐的内存对齐值
        
        Returns:
            int: 对齐字节数
        """
        return self.memory_alignment
        
    def align_array(self, array: np.ndarray) -> np.ndarray:
        """
        将数组对齐到最佳内存边界
        
        Args:
            array: 输入数组
            
        Returns:
            np.ndarray: 对齐后的数组（如果无法对齐则返回原数组）
        """
        if HAS_MEMORY_ALIGNMENT:
            return align_array(array, self.memory_alignment)
        return array
        
    def is_aligned(self, array: np.ndarray) -> bool:
        """
        检查数组是否已对齐到最佳边界
        
        Args:
            array: 要检查的数组
            
        Returns:
            bool: 是否已对齐
        """
        if HAS_MEMORY_ALIGNMENT:
            return is_aligned(array, self.memory_alignment)
        return True  # 无法检查时假设已对齐
        
    def create_aligned_array(self, shape, dtype=np.float32) -> np.ndarray:
        """
        创建对齐的数组
        
        Args:
            shape: 数组形状
            dtype: 数据类型
            
        Returns:
            np.ndarray: 对齐的数组
        """
        if HAS_MEMORY_ALIGNMENT:
            return create_aligned_array(shape, dtype, self.memory_alignment)
        else:
            return np.zeros(shape, dtype=dtype)
            
    def _init_parallel_scheduler(self):
        """初始化并行调度器"""
        if HAS_PARALLEL_SCHEDULER:
            try:
                n_jobs = self.get_optimization_level().get('parallel_threads', None)
                return ParallelScheduler(n_jobs=n_jobs)
            except Exception as e:
                logger.error(f"初始化并行调度器失败: {str(e)}")
                return None
        return None
        
    def schedule_parallel_tasks(self, func, data_list, **kwargs):
        """
        使用指令级并行调度任务
        
        Args:
            func: 要执行的函数
            data_list: 输入数据列表
            **kwargs: 传递给函数的额外参数
            
        Returns:
            List: 结果列表
        """
        if HAS_PARALLEL_SCHEDULER and self.parallel_scheduler:
            return self.parallel_scheduler.schedule_instructions(func, data_list, **kwargs)
        else:
            # 回退到串行处理
            return [func(item, **kwargs) for item in data_list]
            
    def get_optimization_info(self) -> Dict:
        """
        获取优化信息
        
        Returns:
            Dict: 优化信息
        """
        info = {
            'path': self.optimization_path,
            'level': self.get_optimization_level(),
            'instruction_sets': {k: v for k, v in self.instruction_sets.items() if v},
            'simd_available': HAS_SIMD,
            'assembly_available': HAS_ASSEMBLY,
            'memory_alignment': {
                'available': HAS_MEMORY_ALIGNMENT,
                'alignment': self.memory_alignment,
            },
            'parallel_scheduler': {
                'available': HAS_PARALLEL_SCHEDULER,
                'threads': self.get_optimization_level().get('parallel_threads', 1),
                'ilp_enabled': self.get_optimization_level().get('ilp_enabled', False)
            }
        }
        
        # 添加SIMD信息
        if HAS_SIMD:
            try:
                simd_ops = self.get_simd_operations()
                info['simd'] = simd_ops.get_info() if simd_ops else {}
            except:
                info['simd'] = {'error': '无法获取SIMD信息'}
                
        # 添加汇编信息
        if HAS_ASSEMBLY:
            try:
                asm_ops = self.get_assembly_operations()
                info['assembly'] = asm_ops.get_library_info() if asm_ops else {}
            except:
                info['assembly'] = {'error': '无法获取汇编信息'}
                
        return info

# 便捷函数

def select_optimization_path() -> str:
    """
    检测并选择最佳优化路径
    
    Returns:
        str: 优化路径名称
    """
    # 检测CPU支持的指令集
    isa = CPUFeatureDetector().instruction_sets
    
    # 按优先级选择优化路径
    if isa.get('avx512f', False):
        return 'avx512'
    elif isa.get('avx2', False):
        return 'avx2'
    elif isa.get('avx', False):
        return 'avx'
    elif isa.get('sse4_2', False):
        return 'sse4.2'
    elif isa.get('neon', False):
        return 'neon'
    else:
        return 'baseline'

def detect_instruction_sets() -> Dict[str, bool]:
    """
    检测CPU支持的指令集
    
    Returns:
        Dict[str, bool]: 指令集支持状态字典
    """
    return CPUFeatureDetector().instruction_sets

def get_optimization_info() -> Dict:
    """
    获取优化信息
    
    Returns:
        Dict: 包含指令集、优化路径和优化级别的信息
    """
    router = OptimizationRouter()
    return router.get_optimization_info()

def get_simd_operations():
    """
    获取适合当前系统的SIMD操作对象
    
    Returns:
        SimdOperations: SIMD操作对象，如果不可用则返回None
    """
    if not HAS_SIMD:
        return None
        
    # 获取优化路径
    path = select_optimization_path()
    
    # 根据路径获取SIMD类型
    simd_types = {
        'avx512': 'avx512',
        'avx2': 'avx2',
        'avx': 'avx',
        'sse4.2': 'sse4.2',
        'neon': 'neon',
        'baseline': 'baseline'
    }
    
    simd_type = simd_types.get(path, 'auto')
    
    # 创建SIMD操作对象
    return create_simd_operations(simd_type)

def get_assembly_operations():
    """
    获取适合当前平台的汇编优化操作对象
    
    Returns:
        PlatformAsm: 平台汇编优化对象，如果不可用则返回None
    """
    if not HAS_ASSEMBLY:
        return None
        
    try:
        return get_platform_asm()
    except Exception as e:
        logger.error(f"获取平台汇编优化失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=== VisionAI-ClipsMaster 指令集优化路由器 ===\n")
    
    # 创建优化路由器
    router = OptimizationRouter()
    
    # 显示当前选择的优化路径
    path = router.get_optimization_path()
    level = router.get_optimization_level()
    
    print(f"检测到的CPU: {router.cpu_detector.cpu_info.get('brand', 'Unknown')}")
    print(f"支持的指令集: {', '.join([k for k, v in router.instruction_sets.items() if v])}\n")
    
    print(f"选择的优化路径: {path}")
    print(f"优化级别: {level['name']} - {level['description']}")
    print(f"SIMD宽度: {level['simd_width']}位, 性能评级: {level['performance_rating']}/100")
    
    # 显示模型参数
    print("\n模型优化参数:")
    for model in ['qwen2.5-7b-zh', 'mistral-7b-en']:
        params = router.get_model_parameters(model)
        print(f"  {model}:")
        for k, v in params.items():
            print(f"    {k}: {v}")
    
    # 显示SIMD支持情况
    print(f"\nSIMD向量化支持: {'可用' if HAS_SIMD else '不可用'}")
    if HAS_SIMD:
        simd_ops = router.get_simd_operations()
        if simd_ops:
            print(f"SIMD类型: {simd_ops.simd_type}")
            print(f"SIMD库加载: {'成功' if simd_ops.simd_lib_loaded else '失败'}")
            
            # 运行简单性能测试
            try:
                stats = simd_ops.get_performance_stats()
                print("\nSIMD性能统计:")
                for key, value in stats.items():
                    if key != 'is_correct':  # 跳过详细的正确性检查结果
                        print(f"  {key}: {value}")
                        
                if stats.get('is_correct', False):
                    print("  计算结果验证: 正确")
                else:
                    print("  计算结果验证: 失败")
                    
                if stats.get('speedup', 0) > 1.0:
                    print(f"  性能提升: {stats.get('speedup', 0):.2f}倍")
            except:
                print("  无法获取性能统计")
    
    # 显示平台汇编优化支持情况
    print(f"\n平台汇编优化支持: {'可用' if HAS_ASSEMBLY else '不可用'}")
    if HAS_ASSEMBLY:
        asm_ops = router.get_assembly_operations()
        if asm_ops:
            info = asm_ops.get_library_info()
            print(f"汇编库可用: {'是' if info['available'] else '否'}")
            if info['available']:
                print(f"优化级别: {info['optimization_level']}")
                print(f"库版本: {info.get('version', '未知')}")
                
                # 运行简单性能测试
                print("\n运行简单汇编性能测试...")
                try:
                    size = 500
                    a = np.random.rand(size, size).astype(np.float32)
                    b = np.random.rand(size, size).astype(np.float32)
                    
                    # 计时
                    start = time.time()
                    result = asm_ops.optimized_matrix_multiply(a, b)
                    duration = time.time() - start
                    
                    print(f"矩阵乘法 ({size}x{size}) 耗时: {duration:.6f}秒")
                except Exception as e:
                    print(f"测试失败: {str(e)}")
    
    # 导出配置
    config_path = router.export_config()
    print(f"\n优化配置已保存到: {config_path}")
    
    # 显示决策矩阵
    print("\n指令集优化决策矩阵:")
    print("+--------------+------------+----------------+---------------+----------------+----------------+")
    print("| 指令集       | SIMD宽度   | 推荐线程数     | 批处理大小    | 性能评级       | 指令级并行     |")
    print("+--------------+------------+----------------+---------------+----------------+----------------+")
    print(f"| AVX512       | 512位      | 8              | 4             | 100/100        | 启用           |")
    print(f"| AVX2         | 256位      | 4              | 2             | 80/100         | 启用           |")
    print(f"| AVX          | 256位      | 2              | 2             | 70/100         | 启用           |")
    print(f"| SSE4.2       | 128位      | 2              | 1             | 60/100         | 启用           |")
    print(f"| NEON (ARM)   | 128位      | 4              | 2             | 75/100         | 启用           |")
    print(f"| 基线         | 64位       | 1              | 1             | 40/100         | 禁用           |")
    print("+--------------+------------+----------------+---------------+----------------+----------------+") 