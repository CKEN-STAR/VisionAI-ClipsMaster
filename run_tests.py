#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主测试脚本
运行所有测试模块，包括模型管理测试、数据隔离测试和视频处理测试
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
from datetime import datetime

def run_test_file(file_path, verbose=True):
    """运行指定的测试文件
    
    Args:
        file_path: 测试文件路径
        verbose: 是否显示详细输出
        
    Returns:
        bool: 测试是否成功
    """
    if verbose:
        print(f"运行测试文件: {file_path}")
    result = subprocess.run([sys.executable, file_path], capture_output=True, text=True)
    
    # 输出测试结果
    if verbose:
        print(result.stdout)
        if result.stderr:
            print(f"错误信息: {result.stderr}")
    
    return result.returncode == 0

def run_test_module(test_name, test_files, verbose=True):
    """运行一组测试文件
    
    Args:
        test_name: 测试模块名称
        test_files: 测试文件列表
        verbose: 是否显示详细输出
        
    Returns:
        tuple: (是否全部通过, 通过数量, 总数量)
    """
    if verbose:
        print("=" * 50)
        print(f"开始执行{test_name}测试")
        print("=" * 50)
    
    passed_count = 0
    total_count = len(test_files)
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            if verbose:
                print(f"警告: 测试文件不存在: {test_file}")
            continue
            
        if run_test_file(test_file, verbose):
            passed_count += 1
    
    all_passed = passed_count == total_count
    
    if verbose:
        print("\n" + "=" * 50)
        if all_passed:
            print(f"{test_name}测试全部通过! ({passed_count}/{total_count})")
        else:
            print(f"{test_name}测试部分失败 ({passed_count}/{total_count})")
        print("=" * 50)
    
    return all_passed, passed_count, total_count

def main():
    """主函数，运行所有测试"""
    parser = argparse.ArgumentParser(description="运行VisionAI-ClipsMaster项目测试")
    parser.add_argument("--model", action="store_true", help="只运行模型管理测试")
    parser.add_argument("--data", action="store_true", help="只运行数据隔离测试")
    parser.add_argument("--video", action="store_true", help="只运行视频处理测试")
    parser.add_argument("--no-gpu", action="store_true", help="视频处理测试时不使用GPU")
    parser.add_argument("--quiet", action="store_true", help="静默模式，只显示最终结果")
    args = parser.parse_args()
    
    verbose = not args.quiet
    start_time = datetime.now()
    
    # 测试文件
    model_tests = [
        os.path.join("test_model_manager.py")
    ]
    
    data_tests = [
        os.path.join("tests", "unit_test", "standalone_data_isolation.py"),
        os.path.join("validate_data_isolation.py")
    ]
    
    video_tests = [
        os.path.join("tests", "video_processing", "test_clip_generator.py"),
        os.path.join("tests", "video_processing", "run_pipeline_test.py") + 
            (" --no-gpu" if args.no_gpu else "")
    ]
    
    # 运行测试
    results = {}
    
    # 根据命令行参数，确定要运行的测试模块
    run_all = not (args.model or args.data or args.video)
    
    if args.model or run_all:
        model_passed, model_pass_count, model_total = run_test_module("模型管理", model_tests, verbose)
        results["模型管理"] = {
            "passed": model_passed,
            "pass_count": model_pass_count,
            "total": model_total
        }
    
    if args.data or run_all:
        data_passed, data_pass_count, data_total = run_test_module("数据隔离", data_tests, verbose)
        results["数据隔离"] = {
            "passed": data_passed,
            "pass_count": data_pass_count,
            "total": data_total
        }
    
    if args.video or run_all:
        video_passed, video_pass_count, video_total = run_test_module("视频处理", video_tests, verbose)
        results["视频处理"] = {
            "passed": video_passed,
            "pass_count": video_pass_count,
            "total": video_total
        }
    
    # 输出总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print(f"测试完成! 耗时: {duration:.2f}秒")
    print("=" * 70)
    
    for module_name, result in results.items():
        status = "通过" if result["passed"] else "失败"
        print(f"{module_name}测试: {status} ({result['pass_count']}/{result['total']})")
    
    print("=" * 70)
    
    # 判断总体是否通过
    all_passed = all(result["passed"] for result in results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 