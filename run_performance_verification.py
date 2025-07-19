#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能验证套件运行器 - VisionAI-ClipsMaster
提供简单方式运行指令流水线性能验证测试并生成报告
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
logger = logging.getLogger('perf-verify-runner')

def check_environment():
    """检查运行环境"""
    # 检查必要的Python包
    try:
        import numpy
        logger.info(f"NumPy版本: {numpy.__version__}")
    except ImportError:
        logger.error("未安装NumPy，这是性能测试所必需的")
        return False
    
    # 检查系统信息
    import platform
    logger.info(f"操作系统: {platform.platform()}")
    logger.info(f"处理器: {platform.processor()}")
    logger.info(f"Python版本: {platform.python_version()}")
    
    # 检查项目结构
    root_dir = Path(__file__).resolve().parent
    
    required_files = [
        root_dir / "src" / "hardware" / "performance_verification.py",
        root_dir / "tests" / "hardware_test" / "instruction_test.py",
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        logger.error("缺少必要的文件:")
        for f in missing_files:
            logger.error(f"  - {f}")
        return False
    
    return True

def run_verification_test(avx2_only=False, generate_report=True, output_path=None):
    """运行性能验证测试"""
    root_dir = Path(__file__).resolve().parent
    verification_script = root_dir / "src" / "hardware" / "performance_verification.py"
    
    if not verification_script.exists():
        logger.error(f"找不到验证脚本: {verification_script}")
        return False
    
    logger.info("运行指令流水线性能验证...")
    
    cmd = [sys.executable, str(verification_script)]
    
    if avx2_only:
        cmd.append("--avx2")
    elif not generate_report:
        cmd.append("--verify")
    elif output_path:
        cmd.extend(["--report", output_path])
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True)
        elapsed = time.time() - start_time
        
        logger.info(f"验证完成，耗时 {elapsed:.2f} 秒")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"验证测试失败，退出代码: {e.returncode}")
        return False

def run_instruction_tests():
    """运行指令集优化测试"""
    root_dir = Path(__file__).resolve().parent
    test_script = root_dir / "tests" / "hardware_test" / "instruction_test.py"
    
    if not test_script.exists():
        logger.error(f"找不到指令测试脚本: {test_script}")
        return False
    
    logger.info("运行指令集优化测试...")
    
    try:
        result = subprocess.run([sys.executable, str(test_script)], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"指令测试失败，退出代码: {e.returncode}")
        return False

def run_comprehensive_benchmark():
    """运行全面基准测试"""
    logger.info("=== 开始全面性能基准测试 ===")
    
    # 导入性能验证模块
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from src.hardware.performance_verification import (
            test_matrix_multiply,
            test_vector_dot_product,
            test_matrix_vector_multiply,
            detect_instruction_set,
            generate_performance_report
        )
    except ImportError as e:
        logger.error(f"导入性能验证模块失败: {e}")
        return False
    
    # 检测指令集
    instruction_set = detect_instruction_set()
    logger.info(f"检测到指令集: {instruction_set}")
    
    # 运行各项测试
    logger.info("1. 矩阵乘法测试")
    matrix_results = test_matrix_multiply()
    
    logger.info("\n2. 向量点积测试")
    vector_results = test_vector_dot_product()
    
    logger.info("\n3. 矩阵向量乘法测试")
    mat_vec_results = test_matrix_vector_multiply()
    
    # 生成并保存报告
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    report_path = f"benchmark_report_{timestamp}.json"
    
    logger.info(f"\n生成基准测试报告: {report_path}")
    report = generate_performance_report(report_path)
    
    # 输出摘要
    logger.info("\n=== 性能测试摘要 ===")
    logger.info(f"指令集: {instruction_set}")
    
    # 矩阵乘法摘要
    if matrix_results:
        avg_speedup = sum(r.speedup for r in matrix_results) / len(matrix_results)
        logger.info(f"矩阵乘法平均加速比: {avg_speedup:.2f}x")
    
    # 向量点积摘要
    if vector_results:
        avg_speedup = sum(r.speedup for r in vector_results) / len(vector_results)
        logger.info(f"向量点积平均加速比: {avg_speedup:.2f}x")
    
    # 矩阵向量乘法摘要
    if mat_vec_results:
        avg_speedup = sum(r.speedup for r in mat_vec_results) / len(mat_vec_results)
        logger.info(f"矩阵向量乘法平均加速比: {avg_speedup:.2f}x")
    
    logger.info(f"详细报告已保存至: {report_path}")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='指令流水线优化性能验证套件运行器')
    parser.add_argument('--avx2', '-a', action='store_true', help='只测试AVX2加速效果')
    parser.add_argument('--verify', '-v', action='store_true', help='只运行验证测试')
    parser.add_argument('--benchmark', '-b', action='store_true', help='运行全面基准测试')
    parser.add_argument('--report', '-r', type=str, help='性能报告输出路径')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    args = parser.parse_args()
    
    logger.info("=== 指令流水线优化性能验证套件 ===")
    
    # 检查环境
    if not check_environment():
        logger.error("环境检查失败，无法继续测试")
        return 1
    
    # 根据参数选择要运行的测试
    if args.avx2:
        # 只测试AVX2加速
        success = run_verification_test(avx2_only=True)
    elif args.verify:
        # 只运行验证测试
        success = run_verification_test(generate_report=False)
    elif args.benchmark:
        # 运行全面基准测试
        success = run_comprehensive_benchmark()
    elif args.all:
        # 运行所有测试
        logger.info("运行所有性能验证测试...")
        success1 = run_verification_test(output_path=args.report)
        success2 = run_instruction_tests()
        success3 = run_comprehensive_benchmark()
        success = success1 and success2 and success3
    else:
        # 默认运行验证测试并生成报告
        success = run_verification_test(output_path=args.report)
    
    if success:
        logger.info("性能验证测试完成")
        return 0
    else:
        logger.error("性能验证测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 