#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能验证套件 - VisionAI-ClipsMaster
提供全面的指令流水线优化性能验证和基准测试

该模块用于:
1. 验证各种指令集优化的实际性能提升
2. 确保在不同硬件配置上达到预期的加速比
3. 生成详细的性能报告
4. 支持自动化CI/CD流程的性能回归测试
"""

import os
import sys
import time
import json
import logging
import platform
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable, Any
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# 导入指令流水线优化模块
try:
    from src.hardware.pipeline_wrapper import (
        get_pipeline_optimizer, 
        matrix_multiply,
        vector_dot_product, 
        matrix_vector_multiply,
        is_pipeline_opt_available
    )
    HAS_PIPELINE_OPT = True
except ImportError:
    HAS_PIPELINE_OPT = False

# 导入微架构检测模块
try:
    from src.hardware.microarch_tuner import get_microarch_tuner
    HAS_MICROARCH_TUNER = True
except ImportError:
    HAS_MICROARCH_TUNER = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('perf-verify')

# 性能标准常量 (每种指令集的最低加速比要求)
PERFORMANCE_STANDARDS = {
    'AVX512': 5.0,  # AVX512需要至少5倍加速
    'AVX2': 3.0,    # AVX2需要至少3倍加速
    'AVX': 1.5,     # AVX需要至少1.5倍加速
    'SSE4.2': 1.3,  # SSE4.2需要至少1.3倍加速
    'NEON': 2.0,    # ARM NEON需要至少2倍加速
    'default': 1.0  # 默认情况下不需要加速
}

class TimeitResult:
    """计时测试结果类"""
    
    def __init__(self, 
                 operation: str, 
                 baseline_time: float, 
                 optimized_time: float,
                 speedup: float,
                 data_size: Tuple[int, ...],
                 instruction_set: str):
        self.operation = operation
        self.baseline_time = baseline_time
        self.optimized_time = optimized_time
        self.speedup = speedup
        self.data_size = data_size
        self.instruction_set = instruction_set
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'operation': self.operation,
            'baseline_time': round(self.baseline_time, 6),
            'optimized_time': round(self.optimized_time, 6),
            'speedup': round(self.speedup, 2),
            'data_size': self.data_size,
            'instruction_set': self.instruction_set,
            'timestamp': self.timestamp
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"{self.operation} ({self.instruction_set}): "
                f"基准={self.baseline_time:.6f}秒, "
                f"优化={self.optimized_time:.6f}秒, "
                f"加速比={self.speedup:.2f}x")

def timeit(func: Callable, number: int = 3) -> float:
    """简单的计时器，运行函数多次并返回平均执行时间"""
    times = []
    for _ in range(number):
        start = time.time()
        func()
        end = time.time()
        times.append(end - start)
    return sum(times) / len(times)

def detect_instruction_set() -> str:
    """检测当前系统支持的最高指令集"""
    # 如果有微架构调优器，使用它检测
    if HAS_MICROARCH_TUNER:
        tuner = get_microarch_tuner()
        if hasattr(tuner, 'supported_instruction_sets'):
            sets = tuner.supported_instruction_sets()
            if sets:
                return sets[0]  # 返回最高级指令集
    
    # 否则通过pipeline_optimizer检测
    if HAS_PIPELINE_OPT:
        optimizer = get_pipeline_optimizer()
        level = optimizer.optimization_level
        
        # 根据优化级别猜测指令集
        if level == 2:
            return 'AVX2'
        elif level == 1:
            return 'SSE4.2'
    
    # 回退到CPU信息解析
    cpu_info = platform.processor().lower()
    
    if 'arm' in cpu_info or 'aarch64' in cpu_info:
        return 'NEON'
    
    # 尝试运行具体的测试以检测指令集
    try:
        import cpuinfo
        info = cpuinfo.get_cpu_info()
        flags = info.get('flags', [])
        
        if 'avx512' in ' '.join(flags):
            return 'AVX512'
        elif 'avx2' in ' '.join(flags):
            return 'AVX2'
        elif 'avx' in ' '.join(flags):
            return 'AVX'
        elif 'sse4_2' in ' '.join(flags):
            return 'SSE4.2'
    except ImportError:
        pass
    
    return 'default'

def test_matrix_multiply(sizes: List[Tuple[int, int, int]] = None) -> List[TimeitResult]:
    """测试矩阵乘法性能
    
    Args:
        sizes: 要测试的矩阵大小列表，每个元素是(M, K, N)表示矩阵A(M×K)乘以矩阵B(K×N)
        
    Returns:
        List[TimeitResult]: 测试结果列表
    """
    if not HAS_PIPELINE_OPT:
        logger.error("无法进行矩阵乘法测试：流水线优化模块不可用")
        return []
    
    # 默认测试大小
    if sizes is None:
        sizes = [
            (100, 100, 100),    # 小矩阵
            (500, 500, 500),    # 中等矩阵
            (1000, 1000, 1000)  # 大矩阵
        ]
    
    results = []
    instruction_set = detect_instruction_set()
    
    for size in sizes:
        M, K, N = size
        
        # 创建随机测试数据
        A = np.random.rand(M, K).astype(np.float32)
        B = np.random.rand(K, N).astype(np.float32)
        
        # 基准测试（使用NumPy）
        baseline_func = lambda: np.matmul(A, B)
        baseline_time = timeit(baseline_func, number=5)
        
        # 优化版本测试
        optimized_func = lambda: matrix_multiply(A, B)
        optimized_time = timeit(optimized_func, number=5)
        
        # 计算加速比
        speedup = baseline_time / optimized_time if optimized_time > 0 else 0
        
        # 创建结果
        result = TimeitResult(
            operation=f"矩阵乘法 {M}×{K}×{N}",
            baseline_time=baseline_time,
            optimized_time=optimized_time,
            speedup=speedup,
            data_size=(M, K, N),
            instruction_set=instruction_set
        )
        
        logger.info(str(result))
        results.append(result)
    
    return results

def test_vector_dot_product(sizes: List[int] = None) -> List[TimeitResult]:
    """测试向量点积性能
    
    Args:
        sizes: 要测试的向量大小列表
        
    Returns:
        List[TimeitResult]: 测试结果列表
    """
    if not HAS_PIPELINE_OPT:
        logger.error("无法进行向量点积测试：流水线优化模块不可用")
        return []
    
    # 默认测试大小
    if sizes is None:
        sizes = [1000, 10000, 100000, 1000000]
    
    results = []
    instruction_set = detect_instruction_set()
    
    for size in sizes:
        # 创建随机测试数据
        v1 = np.random.rand(size).astype(np.float32)
        v2 = np.random.rand(size).astype(np.float32)
        
        # 基准测试（使用NumPy）
        baseline_func = lambda: np.dot(v1, v2)
        baseline_time = timeit(baseline_func, number=10)
        
        # 优化版本测试
        optimized_func = lambda: vector_dot_product(v1, v2)
        optimized_time = timeit(optimized_func, number=10)
        
        # 计算加速比
        speedup = baseline_time / optimized_time if optimized_time > 0 else 0
        
        # 创建结果
        result = TimeitResult(
            operation=f"向量点积 {size}",
            baseline_time=baseline_time,
            optimized_time=optimized_time,
            speedup=speedup,
            data_size=(size,),
            instruction_set=instruction_set
        )
        
        logger.info(str(result))
        results.append(result)
    
    return results

def test_matrix_vector_multiply(sizes: List[Tuple[int, int]] = None) -> List[TimeitResult]:
    """测试矩阵向量乘法性能
    
    Args:
        sizes: 要测试的大小列表，每个元素是(rows, cols)表示矩阵A(rows×cols)乘以向量x(cols)
        
    Returns:
        List[TimeitResult]: 测试结果列表
    """
    if not HAS_PIPELINE_OPT:
        logger.error("无法进行矩阵向量乘法测试：流水线优化模块不可用")
        return []
    
    # 默认测试大小
    if sizes is None:
        sizes = [(100, 100), (500, 500), (1000, 1000)]
    
    results = []
    instruction_set = detect_instruction_set()
    
    for size in sizes:
        rows, cols = size
        
        # 创建随机测试数据
        A = np.random.rand(rows, cols).astype(np.float32)
        x = np.random.rand(cols).astype(np.float32)
        
        # 基准测试（使用NumPy）
        baseline_func = lambda: np.dot(A, x)
        baseline_time = timeit(baseline_func, number=5)
        
        # 优化版本测试
        optimized_func = lambda: matrix_vector_multiply(A, x)
        optimized_time = timeit(optimized_func, number=5)
        
        # 计算加速比
        speedup = baseline_time / optimized_time if optimized_time > 0 else 0
        
        # 创建结果
        result = TimeitResult(
            operation=f"矩阵向量乘法 {rows}×{cols}",
            baseline_time=baseline_time,
            optimized_time=optimized_time,
            speedup=speedup,
            data_size=(rows, cols),
            instruction_set=instruction_set
        )
        
        logger.info(str(result))
        results.append(result)
    
    return results

def test_avx2_acceleration() -> bool:
    """AVX2加速效果验证
    
    验证AVX2指令集优化是否达到预期的加速效果（至少提速40%）
    
    Returns:
        bool: 是否通过验证
    """
    logger.info("=== AVX2加速效果验证 ===")
    
    # 检查系统是否支持AVX2
    instruction_set = detect_instruction_set()
    if instruction_set != 'AVX2' and instruction_set != 'AVX512':
        logger.warning(f"当前系统使用的是{instruction_set}指令集，不支持AVX2验证")
        return False
    
    # 创建测试数据 (500x500矩阵乘法)
    data_size = (500, 500, 500)
    A = np.random.rand(data_size[0], data_size[1]).astype(np.float32)
    B = np.random.rand(data_size[1], data_size[2]).astype(np.float32)
    
    # 基准测试（NumPy）
    baseline_op = lambda: np.matmul(A, B)
    baseline_time = timeit(baseline_op, number=3)
    
    # AVX2优化版本
    avx2_op = lambda: matrix_multiply(A, B)
    optimized_time = timeit(avx2_op, number=3)
    
    # 计算加速比并验证
    speedup = baseline_time / optimized_time if optimized_time > 0 else 0
    
    # AVX2加速至少应该达到3倍 (原始时间的33%)
    # 这里验证是否至少优化40% (optimized_time < baseline_time * 0.6)
    passed = optimized_time < baseline_time * 0.6
    
    logger.info(f"基准时间: {baseline_time:.6f}秒")
    logger.info(f"优化时间: {optimized_time:.6f}秒")
    logger.info(f"加速比: {speedup:.2f}x")
    logger.info(f"验证结果: {'通过' if passed else '未通过'} (要求至少加速40%)")
    
    return passed

def test_instruction_set_performance() -> Dict[str, bool]:
    """测试当前指令集是否达到性能标准
    
    Returns:
        Dict[str, bool]: 每种操作是否通过验证
    """
    # 检测当前指令集
    instruction_set = detect_instruction_set()
    target_speedup = PERFORMANCE_STANDARDS.get(instruction_set, 1.0)
    
    logger.info(f"=== {instruction_set}指令集性能标准验证 ===")
    logger.info(f"期望最低加速比: {target_speedup}x")
    
    results = {}
    
    # 测试矩阵乘法
    matrix_results = test_matrix_multiply([(500, 500, 500)])
    if matrix_results:
        result = matrix_results[0]
        passed = result.speedup >= target_speedup
        results['matrix_multiply'] = passed
        logger.info(f"矩阵乘法验证: {'通过' if passed else '未通过'} "
                    f"(实际加速比: {result.speedup:.2f}x, 要求: {target_speedup}x)")
    
    # 测试向量点积
    vector_results = test_vector_dot_product([100000])
    if vector_results:
        result = vector_results[0]
        passed = result.speedup >= target_speedup
        results['vector_dot_product'] = passed
        logger.info(f"向量点积验证: {'通过' if passed else '未通过'} "
                    f"(实际加速比: {result.speedup:.2f}x, 要求: {target_speedup}x)")
    
    # 测试矩阵向量乘法
    mat_vec_results = test_matrix_vector_multiply([(500, 500)])
    if mat_vec_results:
        result = mat_vec_results[0]
        passed = result.speedup >= target_speedup
        results['matrix_vector_multiply'] = passed
        logger.info(f"矩阵向量乘法验证: {'通过' if passed else '未通过'} "
                    f"(实际加速比: {result.speedup:.2f}x, 要求: {target_speedup}x)")
    
    # 总体验证结果
    all_passed = all(results.values()) if results else False
    logger.info(f"总体验证结果: {'通过' if all_passed else '未通过'}")
    
    return results

def generate_performance_report(output_path: Optional[str] = None) -> Dict[str, Any]:
    """生成性能报告
    
    Args:
        output_path: 报告输出路径，如果为None则不保存文件
        
    Returns:
        Dict[str, Any]: 性能报告数据
    """
    logger.info("=== 生成性能验证报告 ===")
    
    # 收集系统信息
    system_info = {
        'platform': platform.platform(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'numpy_version': np.__version__
    }
    
    # 检测指令集
    instruction_set = detect_instruction_set()
    
    # 收集优化器信息
    optimizer_info = {}
    if HAS_PIPELINE_OPT:
        optimizer = get_pipeline_optimizer()
        optimizer_info = {
            'available': True,
            'level': optimizer.optimization_level,
            'stats': optimizer.get_stats()
        }
    else:
        optimizer_info = {'available': False}
    
    # 运行测试
    matrix_results = test_matrix_multiply()
    vector_results = test_vector_dot_product()
    mat_vec_results = test_matrix_vector_multiply()
    
    # 验证结果
    verification_results = test_instruction_set_performance()
    avx2_test = test_avx2_acceleration() if instruction_set in ['AVX2', 'AVX512'] else False
    
    # 组装报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_info': system_info,
        'instruction_set': instruction_set,
        'optimizer_info': optimizer_info,
        'results': {
            'matrix_multiply': [r.to_dict() for r in matrix_results],
            'vector_dot_product': [r.to_dict() for r in vector_results],
            'matrix_vector_multiply': [r.to_dict() for r in mat_vec_results]
        },
        'verification': {
            'instruction_set_performance': verification_results,
            'avx2_acceleration': avx2_test
        }
    }
    
    # 保存报告
    if output_path:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"性能报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存性能报告时出错: {str(e)}")
    
    return report

def main():
    """主函数"""
    # 配置命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='指令流水线优化性能验证套件')
    parser.add_argument('--report', '-r', type=str, default='performance_report.json',
                        help='性能报告输出路径')
    parser.add_argument('--verify', '-v', action='store_true',
                        help='只运行验证测试')
    parser.add_argument('--avx2', '-a', action='store_true',
                        help='只测试AVX2加速')
    args = parser.parse_args()
    
    # 检查流水线优化可用性
    if not HAS_PIPELINE_OPT:
        logger.error("流水线优化模块不可用，无法进行性能验证")
        return 1
    
    if not is_pipeline_opt_available():
        logger.error("系统不支持流水线优化，无法进行性能验证")
        return 1
    
    logger.info("=== 指令流水线优化性能验证套件 ===")
    
    if args.avx2:
        # 只测试AVX2加速
        passed = test_avx2_acceleration()
        return 0 if passed else 1
    
    if args.verify:
        # 只运行验证测试
        results = test_instruction_set_performance()
        return 0 if all(results.values()) else 1
    
    # 生成完整性能报告
    generate_performance_report(args.report)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 