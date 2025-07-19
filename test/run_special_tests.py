#!/usr/bin/env python
"""特殊测试运行脚本

此脚本用于运行VisionAI-ClipsMaster的特殊测试系统，包括：
1. 异常注入测试
2. 性能基准测试

使用方法:
    python run_special_tests.py --all              # 运行所有测试
    python run_special_tests.py --failure          # 仅运行异常注入测试
    python run_special_tests.py --performance      # 仅运行性能基准测试
    python run_special_tests.py --quant            # 仅运行量化性能测试
"""

import os
import sys
import argparse
import time
import unittest
import pytest
from pathlib import Path

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def run_failure_injection_tests(verbose=True):
    """运行异常注入测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        bool: 测试是否全部通过
    """
    print("\n===== 运行异常注入测试 =====")
    
    # 使用unittest运行测试
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern="test_failure_injection.py")
    
    # 创建测试运行器
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # 使用pytest运行参数化测试
    pytest_args = ["-xvs", "test/test_failure_injection.py"] if verbose else ["-q", "test/test_failure_injection.py"]
    pytest_result = pytest.main(pytest_args)
    
    # 判断测试是否成功
    is_success = (len(result.errors) == 0 and len(result.failures) == 0 and pytest_result == 0)
    
    print(f"\n异常注入测试结果: {'成功' if is_success else '失败'}")
    print(f"运行测试数: {result.testsRun}")
    print(f"错误数: {len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    
    return is_success


def run_performance_benchmark_tests(verbose=True):
    """运行性能基准测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        bool: 测试是否全部通过
    """
    print("\n===== 运行性能基准测试 =====")
    
    # 使用unittest运行测试
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern="test_performance_benchmark.py")
    
    # 创建测试运行器
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # 判断测试是否成功
    is_success = (len(result.errors) == 0 and len(result.failures) == 0)
    
    print(f"\n性能基准测试结果: {'成功' if is_success else '失败'}")
    print(f"运行测试数: {result.testsRun}")
    print(f"错误数: {len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    
    return is_success


def run_quant_performance_tests(verbose=True):
    """运行量化性能测试
    
    Args:
        verbose: 是否显示详细输出
    
    Returns:
        bool: 测试是否全部通过
    """
    print("\n===== 运行量化性能参数化测试 =====")
    
    # 使用pytest运行参数化测试
    pytest_args = ["-xvs", "test/test_performance_benchmark.py::test_quant_performance"] if verbose else ["-q", "test/test_performance_benchmark.py::test_quant_performance"]
    pytest_result = pytest.main(pytest_args)
    
    # 判断测试是否成功
    is_success = (pytest_result == 0)
    
    print(f"\n量化性能测试结果: {'成功' if is_success else '失败'}")
    
    return is_success


def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 特殊测试运行器")
    
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--failure", action="store_true", help="运行异常注入测试")
    parser.add_argument("--performance", action="store_true", help="运行性能基准测试")
    parser.add_argument("--quant", action="store_true", help="运行量化性能测试")
    parser.add_argument("--quiet", action="store_true", help="静默模式，减少输出")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 默认运行所有测试
    run_all = args.all or (not args.failure and not args.performance and not args.quant)
    verbose = not args.quiet
    
    start_time = time.time()
    
    # 运行选定的测试
    failure_result = True
    performance_result = True
    quant_result = True
    
    if run_all or args.failure:
        failure_result = run_failure_injection_tests(verbose)
    
    if run_all or args.performance:
        performance_result = run_performance_benchmark_tests(verbose)
    
    if run_all or args.quant:
        quant_result = run_quant_performance_tests(verbose)
    
    # 汇总结果
    total_time = time.time() - start_time
    all_passed = failure_result and performance_result and quant_result
    
    print("\n===== 测试汇总 =====")
    print(f"总运行时间: {total_time:.2f} 秒")
    print(f"异常注入测试: {'通过' if failure_result else '失败'}")
    print(f"性能基准测试: {'通过' if performance_result else '失败'}")
    print(f"量化性能测试: {'通过' if quant_result else '失败'}")
    print(f"\n总体结果: {'全部通过' if all_passed else '存在失败'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main()) 