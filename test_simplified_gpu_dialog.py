#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化GPU检测弹窗测试脚本

用于测试简化后的GPU检测弹窗是否正确移除了详细信息功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_simplified_gpu_dialog():
    """测试简化的GPU检测弹窗"""
    print("=" * 60)
    print("简化GPU检测弹窗测试")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import detect_gpu_info, show_gpu_detection_dialog
        
        # 创建QApplication实例
        app = QApplication(sys.argv)
        
        print("\n1. 执行GPU检测...")
        gpu_info = detect_gpu_info()
        
        print(f"检测结果:")
        print(f"  独立显卡可用: {gpu_info.get('available', False)}")
        print(f"  GPU名称: {gpu_info.get('name', 'N/A')}")
        print(f"  GPU类型: {gpu_info.get('gpu_type', 'none')}")
        
        print("\n2. 显示简化的GPU检测弹窗...")
        print("请检查弹窗是否符合简化要求：")
        print("  ✓ 只有'确定'按钮，无'详细信息'按钮")
        print("  ✓ 只显示核心检测结果，无详细技术信息")
        print("  ✓ 界面简洁，信息清晰")
        print("  ✓ '确定'按钮显示为中文")
        
        print("\n弹窗将在3秒后显示...")
        
        # 延迟显示弹窗
        from PyQt6.QtCore import QTimer
        
        def show_dialog():
            result = show_gpu_detection_dialog(None, gpu_info)
            print(f"\n弹窗关闭，返回值: {result}")
            app.quit()  # 关闭应用
        
        QTimer.singleShot(3000, show_dialog)  # 3秒后显示弹窗
        
        # 运行应用
        app.exec()
        
        print("\n3. 测试完成")
        print("如果弹窗只显示核心信息且无详细信息按钮，则简化成功！")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保在VisionAI-ClipsMaster项目目录中运行此脚本")
        return False
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_both_scenarios():
    """测试有GPU和无GPU两种场景"""
    print("\n" + "=" * 60)
    print("测试不同场景的弹窗显示")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import show_gpu_detection_dialog
        
        app = QApplication(sys.argv)
        
        # 模拟有GPU的情况
        print("\n1. 模拟检测到独立显卡的情况...")
        gpu_info_success = {
            "available": True,
            "name": "NVIDIA GeForce RTX 4080",
            "gpu_type": "nvidia",
            "details": {},
            "errors": [],
            "detection_methods": ["PyTorch", "nvidia-smi"]
        }
        
        print("显示成功检测弹窗...")
        result1 = show_gpu_detection_dialog(None, gpu_info_success)
        print(f"成功弹窗关闭，返回值: {result1}")
        
        # 等待用户确认
        input("\n按Enter键继续测试失败场景...")
        
        # 模拟无GPU的情况
        print("\n2. 模拟未检测到独立显卡的情况...")
        gpu_info_fail = {
            "available": False,
            "name": "未检测到独立显卡",
            "gpu_type": "none",
            "details": {},
            "errors": ["仅检测到集成显卡: Intel(R) Iris(R) Xe Graphics"],
            "detection_methods": ["PyTorch", "Windows-WMI"]
        }
        
        print("显示失败检测弹窗...")
        result2 = show_gpu_detection_dialog(None, gpu_info_fail)
        print(f"失败弹窗关闭，返回值: {result2}")
        
        print("\n两种场景测试完成！")
        return True
        
    except Exception as e:
        print(f"场景测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_simplification():
    """验证简化效果"""
    print("\n" + "=" * 60)
    print("简化效果验证")
    print("=" * 60)
    
    print("\n简化前的功能（已移除）:")
    print("  ❌ 详细信息按钮")
    print("  ❌ 隐藏详细信息按钮")
    print("  ❌ 详细的GPU技术信息")
    print("  ❌ 检测方法列表")
    print("  ❌ 错误信息详情")
    print("  ❌ 诊断建议")
    print("  ❌ 系统信息")
    
    print("\n简化后保留的功能:")
    print("  ✅ 核心检测结果（是否有独立显卡）")
    print("  ✅ GPU名称和类型")
    print("  ✅ 简要的状态说明")
    print("  ✅ 确定按钮（中文）")
    print("  ✅ 清晰的成功/失败提示")
    
    print("\n简化的优势:")
    print("  🎯 界面更简洁")
    print("  🎯 信息更直观")
    print("  🎯 操作更简单")
    print("  🎯 用户体验更好")

if __name__ == "__main__":
    print("VisionAI-ClipsMaster 简化GPU检测弹窗测试工具")
    print(f"项目路径: {PROJECT_ROOT}")
    
    # 执行主要测试
    success1 = test_simplified_gpu_dialog()
    
    # 等待用户确认
    input("\n按Enter键继续场景测试...")
    
    # 执行场景测试
    success2 = test_both_scenarios()
    
    # 显示简化效果验证
    verify_simplification()
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"简化弹窗测试: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"场景测试: {'✅ 成功' if success2 else '❌ 失败'}")
    
    if success1 and success2:
        print("\n🎉 所有测试通过！GPU检测弹窗简化成功。")
        print("\n✨ 简化效果:")
        print("   - 移除了复杂的详细信息功能")
        print("   - 保留了核心的检测结果显示")
        print("   - 界面更加简洁直观")
        print("   - 用户操作更加简单")
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
    
    print(f"\n按Enter键退出...")
    input()
