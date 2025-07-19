#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练功能测试启动器 - 一键运行所有训练功能测试
这个脚本是VisionAI-ClipsMaster训练功能测试的入口点
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 添加项目根目录到Python路径
sys.path.append(str(PROJECT_ROOT))


def print_header(text):
    """打印带有格式的标题"""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def run_test(script_name, args=None):
    """运行指定的测试脚本
    
    Args:
        script_name: 脚本文件名
        args: 可选的命令行参数列表
    
    Returns:
        bool: 测试是否成功
    """
    script_path = PROJECT_ROOT / script_name
    
    if not script_path.exists():
        print(f"错误: 找不到脚本 {script_path}")
        return False
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"运行: {' '.join(cmd)}")
    
    try:
        # 使用subprocess.run但不立即检查返回码，以便我们可以处理非零返回码
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 打印输出，无论成功与否
        if result.stdout:
            print(result.stdout)
        
        # 如果有错误输出，也打印出来
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        # 返回是否成功
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"测试运行失败: {e}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout.decode('utf-8', errors='replace'))
        if e.stderr:
            print("错误输出:")
            print(e.stderr.decode('utf-8', errors='replace'))
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False


def run_all_tests(args):
    """运行所有训练功能测试
    
    Args:
        args: 命令行参数
    
    Returns:
        bool: 所有测试是否成功
    """
    start_time = time.time()
    all_success = True
    test_results = {
        "functional": {"run": False, "success": False},
        "ui": {"run": False, "success": False},
        "validation": {"run": False, "success": False}
    }
    
    # 运行功能测试
    print_header("1. 运行训练功能测试")
    if args.skip_functional:
        print("根据参数设置跳过功能测试")
    else:
        test_results["functional"]["run"] = True
        test_results["functional"]["success"] = run_test("train_functionality_test.py")
        if not test_results["functional"]["success"]:
            print("功能测试失败，但将继续运行其他测试")
    
    # 运行UI测试
    print_header("2. 运行训练UI测试")
    if args.skip_ui:
        print("根据参数设置跳过UI测试")
    else:
        test_results["ui"]["run"] = True
        test_results["ui"]["success"] = run_test("ui_training_test.py")
        if not test_results["ui"]["success"]:
            print("UI测试失败，但将继续运行其他测试")
    
    # 运行验证测试
    print_header("3. 运行训练验证测试")
    if args.skip_validation:
        print("根据参数设置跳过验证测试")
    else:
        validation_args = []
        if args.clean_validation:
            validation_args.append("--clean")
        if args.gen_only:
            validation_args.append("--generate-only")
        if args.validate_only:
            validation_args.append("--validate-only")
        
        test_results["validation"]["run"] = True
        test_results["validation"]["success"] = run_test("train_validation_test.py", validation_args)
        if not test_results["validation"]["success"]:
            print("验证测试失败，但将继续生成报告")
    
    # 计算总体成功状态
    # 只考虑实际运行的测试
    run_tests = [k for k, v in test_results.items() if v["run"]]
    if run_tests:
        success_tests = [k for k in run_tests if test_results[k]["success"]]
        all_success = len(success_tests) > 0  # 只要有一个测试成功就算部分成功
        
        # 如果验证测试成功运行，那么整体结果主要取决于验证测试
        if test_results["validation"]["run"]:
            all_success = test_results["validation"]["success"]
    
    # 生成最终报告
    print_header("测试完成")
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"总运行时间: {elapsed_time:.2f} 秒")
    print(f"测试结果: {'测试通过' if all_success else '部分测试失败'}")
    
    return all_success, test_results


def create_test_report(success, test_results=None):
    """创建测试报告
    
    Args:
        success: 是否全部成功
        test_results: 各个测试的详细结果
    """
    report_path = PROJECT_ROOT / "test_reports"
    os.makedirs(report_path, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = report_path / f"training_test_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("VisionAI-ClipsMaster 训练功能测试报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 整体结果
        if success:
            f.write("整体结果: 测试通过\n\n")
        else:
            f.write("整体结果: 部分测试失败\n\n")
        
        # 详细测试结果
        f.write("详细测试结果:\n")
        if test_results:
            # 功能测试
            if test_results["functional"]["run"]:
                status = "通过" if test_results["functional"]["success"] else "失败"
                f.write(f"- 功能测试: {status}\n")
            else:
                f.write("- 功能测试: 已跳过\n")
                
            # UI测试
            if test_results["ui"]["run"]:
                status = "通过" if test_results["ui"]["success"] else "失败"
                f.write(f"- UI测试: {status}\n")
            else:
                f.write("- UI测试: 已跳过\n")
                
            # 验证测试
            if test_results["validation"]["run"]:
                status = "通过" if test_results["validation"]["success"] else "失败"
                f.write(f"- 验证测试: {status}\n")
            else:
                f.write("- 验证测试: 已跳过\n")
        else:
            f.write("- 功能测试: 检查ModelTrainer类的基本功能\n")
            f.write("- UI测试: 验证训练界面的交互功能\n")
            f.write("- 验证测试: 评估训练后模型的有效性\n")
        
        f.write("\n")
        
        # 测试说明
        f.write("测试说明:\n")
        f.write("- 功能测试: 检查ModelTrainer类的基本功能，包括初始化、训练和生成\n")
        f.write("- UI测试: 验证训练界面的交互功能，包括语言切换、文件导入和训练过程\n")
        f.write("- 验证测试: 评估训练后模型的有效性，通过比较生成结果与目标结果的相似度\n\n")
        
        # 建议
        f.write("建议:\n")
        if success:
            f.write("- 测试通过，可以进行下一步开发\n")
            f.write("- 考虑增加更多边缘情况测试\n")
            f.write("- 添加性能基准测试\n")
        else:
            # 根据具体失败的测试给出建议
            if test_results:
                if test_results["functional"]["run"] and not test_results["functional"]["success"]:
                    f.write("- 修复功能测试失败的问题，检查ModelTrainer类的实现\n")
                
                if test_results["ui"]["run"] and not test_results["ui"]["success"]:
                    f.write("- UI测试失败，可能是由于PyQt依赖问题，考虑检查环境配置\n")
                    f.write("- 可以使用--skip-ui参数跳过UI测试\n")
                
                if test_results["validation"]["run"] and not test_results["validation"]["success"]:
                    f.write("- 验证测试失败，检查模型训练和生成的实现\n")
            else:
                f.write("- 修复测试失败的问题\n")
                f.write("- 检查日志以获取详细错误信息\n")
                f.write("- 运行单个测试以进行调试\n")
    
    print(f"\n测试报告已保存到: {report_file}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="训练功能测试启动器")
    parser.add_argument("--skip-functional", action="store_true", help="跳过功能测试")
    parser.add_argument("--skip-ui", action="store_true", help="跳过UI测试")
    parser.add_argument("--skip-validation", action="store_true", help="跳过验证测试")
    parser.add_argument("--clean-validation", action="store_true", help="清理验证测试数据")
    parser.add_argument("--gen-only", action="store_true", help="只生成验证测试数据")
    parser.add_argument("--validate-only", action="store_true", help="只运行验证测试")
    return parser.parse_args()


def main():
    """主函数"""
    print_header("VisionAI-ClipsMaster 训练功能测试启动器")
    
    args = parse_args()
    success, test_results = run_all_tests(args)
    create_test_report(success, test_results)
    
    # 返回退出码
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 