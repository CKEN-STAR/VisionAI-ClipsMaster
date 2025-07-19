#!/usr/bin/env python3
"""
运行指令流水线优化测试 - VisionAI-ClipsMaster
提供简单方式运行流水线优化测试并生成报告
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('pipeline-tests')

def check_prerequisites():
    """检查测试先决条件"""
    root_dir = Path(__file__).resolve().parent
    src_dir = root_dir / 'src' / 'hardware'
    
    # 检查核心文件是否存在
    required_files = [
        src_dir / 'pipeline_wrapper.py',
        src_dir / 'test_pipeline_opt.py',
        src_dir / 'pipeline_opt.h'
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        logger.error("缺少必要的文件:")
        for f in missing_files:
            logger.error(f"  - {f}")
        return False
    
    # 检查库文件
    if sys.platform == 'win32':
        lib_path = src_dir / 'pipeline_opt.dll'
    elif sys.platform == 'darwin':
        lib_path = src_dir / 'libpipeline_opt.dylib'
    else:
        lib_path = src_dir / 'libpipeline_opt.so'
    
    if not lib_path.exists():
        logger.warning(f"未找到库文件: {lib_path}")
        logger.warning("需要先构建库文件才能进行完整的测试")
        return False
    
    return True

def build_library(force=False):
    """构建优化库"""
    root_dir = Path(__file__).resolve().parent
    build_script = root_dir / 'build_pipeline_opt.py'
    
    if not build_script.exists():
        logger.error("未找到构建脚本: build_pipeline_opt.py")
        return False
    
    logger.info("构建流水线优化库...")
    result = subprocess.run([sys.executable, str(build_script)], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error("构建失败:")
        logger.error(result.stderr)
        return False
    
    logger.info("构建成功")
    return True

def run_tests(verbose=False):
    """运行测试套件"""
    root_dir = Path(__file__).resolve().parent
    test_script = root_dir / 'src' / 'hardware' / 'test_pipeline_opt.py'
    
    if not test_script.exists():
        logger.error(f"未找到测试脚本: {test_script}")
        return False
    
    logger.info("运行流水线优化测试...")
    
    cmd = [sys.executable, str(test_script)]
    if verbose:
        cmd.append('-v')
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=not verbose)
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        logger.error("测试失败")
        if not verbose:
            logger.error(result.stderr.decode('utf-8', errors='ignore') 
                        if hasattr(result.stderr, 'decode') else result.stderr)
        return False
    
    logger.info(f"测试成功完成 ({elapsed:.2f}秒)")
    return True

def run_benchmark():
    """运行性能基准测试"""
    logger.info("运行流水线优化性能基准测试...")
    
    try:
        # 导入必要的模块
        import numpy as np
        from src.hardware.pipeline_wrapper import (
            get_pipeline_optimizer, matrix_multiply, 
            vector_dot_product, matrix_vector_multiply
        )
        
        optimizer = get_pipeline_optimizer()
        logger.info(f"流水线优化支持级别: {optimizer.optimization_level}")
        
        # 准备测试数据
        sizes = [100, 500, 1000]
        
        logger.info("\n矩阵乘法性能基准:")
        logger.info(f"{'大小':>8} | {'优化版本 (秒)':>15} | {'NumPy (秒)':>15} | {'加速比':>8}")
        logger.info("-" * 55)
        
        for size in sizes:
            # 创建测试矩阵
            A = np.random.rand(size, size).astype(np.float32)
            B = np.random.rand(size, size).astype(np.float32)
            
            # 测试优化版本
            start = time.time()
            C1 = matrix_multiply(A, B)
            opt_time = time.time() - start
            
            # 测试NumPy版本
            start = time.time()
            C2 = np.matmul(A, B)
            numpy_time = time.time() - start
            
            # 计算加速比
            speedup = numpy_time / opt_time if opt_time > 0 else 0
            
            # 检查结果正确性
            max_error = np.max(np.abs(C1 - C2))
            if max_error > 1e-2:
                logger.warning(f"结果误差较大: {max_error:.2e}")
            
            logger.info(f"{size:>8} | {opt_time:>15.6f} | {numpy_time:>15.6f} | {speedup:>8.2f}x")
        
        # 向量点积测试
        logger.info("\n向量点积性能基准:")
        logger.info(f"{'大小':>8} | {'优化版本 (秒)':>15} | {'NumPy (秒)':>15} | {'加速比':>8}")
        logger.info("-" * 55)
        
        for size in [1000, 10000, 100000]:
            # 创建测试向量
            v1 = np.random.rand(size).astype(np.float32)
            v2 = np.random.rand(size).astype(np.float32)
            
            # 测试优化版本
            start = time.time()
            for _ in range(100):  # 运行多次以获得更准确的计时
                r1 = vector_dot_product(v1, v2)
            opt_time = (time.time() - start) / 100
            
            # 测试NumPy版本
            start = time.time()
            for _ in range(100):
                r2 = np.dot(v1, v2)
            numpy_time = (time.time() - start) / 100
            
            # 计算加速比
            speedup = numpy_time / opt_time if opt_time > 0 else 0
            
            logger.info(f"{size:>8} | {opt_time:>15.6f} | {numpy_time:>15.6f} | {speedup:>8.2f}x")
        
        # 输出统计信息
        stats = optimizer.get_stats()
        logger.info("\n优化器统计信息:")
        for k, v in stats.items():
            logger.info(f"  {k}: {v}")
        
        return True
    except ImportError as e:
        logger.error(f"基准测试失败，缺少必要的模块: {e}")
        return False
    except Exception as e:
        logger.error(f"基准测试失败: {e}")
        return False

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='运行指令流水线优化测试')
    parser.add_argument('--build', action='store_true', help='构建库文件')
    parser.add_argument('--benchmark', action='store_true', help='运行性能基准测试')
    parser.add_argument('--verbose', '-v', action='store_true', help='输出详细信息')
    args = parser.parse_args()
    
    logger.info("=== 指令流水线优化测试 ===")
    
    if args.build:
        if not build_library(force=True):
            return 1
    
    # 检查先决条件
    if not check_prerequisites():
        logger.warning("未满足先决条件，可能无法完成全部测试")
        
        # 询问是否构建
        if not args.build:
            answer = input("是否要构建流水线优化库? (y/n): ").strip().lower()
            if answer.startswith('y'):
                if not build_library():
                    return 1
    
    # 运行测试
    if not run_tests(verbose=args.verbose):
        logger.error("测试失败")
        return 1
    
    # 运行基准测试
    if args.benchmark:
        if not run_benchmark():
            logger.error("基准测试失败")
            return 1
    
    logger.info("=== 测试完成 ===")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 