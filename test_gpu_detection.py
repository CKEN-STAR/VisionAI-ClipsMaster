#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU检测功能测试脚本

用于独立测试GPU检测和诊断功能，帮助调试GPU检测问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_gpu_detection():
    """测试独立显卡检测功能"""
    print("=" * 60)
    print("独立显卡检测功能测试")
    print("=" * 60)
    
    try:
        # 导入GPU检测函数
        from simple_ui_fixed import detect_gpu_info, diagnose_gpu_issues
        
        print("\n1. 执行独立显卡检测...")
        gpu_info = detect_gpu_info()

        print(f"\n检测结果:")
        print(f"  独立显卡可用: {gpu_info.get('available', False)}")
        print(f"  GPU名称: {gpu_info.get('name', 'N/A')}")
        print(f"  GPU类型: {gpu_info.get('gpu_type', 'none')}")
        print(f"  检测方法: {', '.join(gpu_info.get('detection_methods', []))}")
        
        # 显示详细信息
        details = gpu_info.get('details', {})
        if details:
            print(f"\n详细信息:")
            for key, value in details.items():
                print(f"  {key}: {value}")
        
        # 显示错误信息
        errors = gpu_info.get('errors', [])
        if errors:
            print(f"\n检测过程中的问题:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        print("\n" + "=" * 60)
        print("独立显卡问题诊断")
        print("=" * 60)

        print("\n2. 执行独立显卡诊断...")
        diagnosis = diagnose_gpu_issues()
        
        # 显示系统信息
        sys_info = diagnosis.get('system_info', {})
        if sys_info:
            print(f"\n系统信息:")
            for key, value in sys_info.items():
                print(f"  {key}: {value}")
        
        # 显示环境检查
        env_check = diagnosis.get('environment_check', {})
        if env_check:
            print(f"\n环境检查:")
            for key, value in env_check.items():
                print(f"  {key}: {value}")
        
        # 显示问题
        issues = diagnosis.get('issues', [])
        if issues:
            print(f"\n发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        
        # 显示建议
        suggestions = diagnosis.get('suggestions', [])
        if suggestions:
            print(f"\n修复建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        return gpu_info.get('available', False)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保在VisionAI-ClipsMaster项目目录中运行此脚本")
        return False
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_methods():
    """测试各个独立显卡检测方法"""
    print("\n" + "=" * 60)
    print("单独测试各独立显卡检测方法")
    print("=" * 60)
    
    # 测试PyTorch
    print("\n1. 测试PyTorch CUDA检测:")
    try:
        import torch
        print(f"  PyTorch版本: {torch.__version__}")
        print(f"  CUDA编译支持: {torch.version.cuda is not None}")
        if torch.version.cuda:
            print(f"  CUDA版本: {torch.version.cuda}")
        print(f"  CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  设备数量: {torch.cuda.device_count()}")
            print(f"  当前设备: {torch.cuda.current_device()}")
            print(f"  设备名称: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("  PyTorch未安装")
    except Exception as e:
        print(f"  PyTorch检测出错: {e}")
    
    # 测试TensorFlow
    print("\n2. 测试TensorFlow GPU检测:")
    try:
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')  # 抑制日志
        print(f"  TensorFlow版本: {tf.__version__}")
        gpus = tf.config.experimental.list_physical_devices('GPU')
        print(f"  GPU设备数量: {len(gpus)}")
        for i, gpu in enumerate(gpus):
            print(f"  设备{i}: {gpu}")
    except ImportError:
        print("  TensorFlow未安装")
    except Exception as e:
        print(f"  TensorFlow检测出错: {e}")
    
    # 测试nvidia-smi
    print("\n3. 测试nvidia-smi:")
    try:
        import subprocess
        result = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  nvidia-smi可用")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                print(f"  {line}")
        else:
            print(f"  nvidia-smi执行失败，返回码: {result.returncode}")
    except FileNotFoundError:
        print("  nvidia-smi命令未找到")
    except Exception as e:
        print(f"  nvidia-smi检测出错: {e}")

if __name__ == "__main__":
    print("VisionAI-ClipsMaster 独立显卡检测测试工具")
    print(f"项目路径: {PROJECT_ROOT}")

    # 执行主要测试
    gpu_available = test_gpu_detection()

    # 执行详细测试
    test_individual_methods()

    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"独立显卡检测结果: {'✅ 成功' if gpu_available else '❌ 失败'}")

    if not gpu_available:
        print("\n如果您确定有独立显卡但检测失败，请检查:")
        print("1. 是否为NVIDIA GeForce/RTX/GTX或AMD Radeon系列独立显卡")
        print("2. 显卡驱动是否正确安装")
        print("3. CUDA Toolkit是否正确安装（NVIDIA显卡）")
        print("4. PyTorch是否支持CUDA")
        print("5. 是否在打包环境中运行（可能缺失动态库）")
        print("\n注意：程序只检测独立显卡，不检测集成显卡（Intel Iris/UHD等）")

    print(f"\n按Enter键退出...")
    input()
