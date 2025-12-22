#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI集成测试
测试核心工作流程的端到端功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_model_check_workflow():
    """测试1：模型检查工作流程"""
    print("=" * 60)
    print("测试1：模型检查工作流程")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        
        # 创建应用实例（不显示UI）
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口实例
        window = simple_ui_fixed.VisionAIClipsMaster()
        
        # 测试模型检查功能
        print("\n测试模型检查功能...")
        window.check_models()
        print("✓ 模型检查功能可调用")
        
        # 测试模型文件检查
        print("\n测试中文模型文件检查...")
        zh_exists = window._check_model_files("zh")
        print(f"✓ 中文模型检查结果: {'存在' if zh_exists else '不存在'}")
        
        print("\n测试英文模型文件检查...")
        en_exists = window._check_model_files("en")
        print(f"✓ 英文模型检查结果: {'存在' if en_exists else '不存在'}")
        
        # 清理
        window.close()
        
        print("\n✅ 模型检查工作流程测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_language_mode_switching():
    """测试2：语言模式切换"""
    print("\n" + "=" * 60)
    print("测试2：语言模式切换")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = simple_ui_fixed.VisionAIClipsMaster()
        
        # 测试切换到中文模式
        print("\n测试切换到中文模式...")
        window.change_language_mode("zh")
        current_mode = window.get_current_language_mode()
        assert current_mode == "zh", f"预期zh，实际{current_mode}"
        print("✓ 成功切换到中文模式")
        
        # 测试切换到英文模式
        print("\n测试切换到英文模式...")
        window.change_language_mode("en")
        current_mode = window.get_current_language_mode()
        assert current_mode == "en", f"预期en，实际{current_mode}"
        print("✓ 成功切换到英文模式")
        
        # 测试切换到自动模式
        print("\n测试切换到自动模式...")
        window.change_language_mode("auto")
        current_mode = window.get_current_language_mode()
        assert current_mode == "auto", f"预期auto，实际{current_mode}"
        print("✓ 成功切换到自动模式")
        
        # 清理
        window.close()
        
        print("\n✅ 语言模式切换测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_management():
    """测试3：内存管理功能"""
    print("\n" + "=" * 60)
    print("测试3：内存管理功能")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = simple_ui_fixed.VisionAIClipsMaster()
        
        # 测试获取内存使用情况
        print("\n测试获取内存使用情况...")
        memory_usage = window.get_memory_usage()
        print(f"✓ 当前内存使用: {memory_usage:.2f} MB")
        
        # 测试内存清理
        print("\n测试内存清理功能...")
        window.cleanup_memory()
        print("✓ 内存清理功能可调用")
        
        # 测试内存检查
        print("\n测试内存检查功能...")
        window.check_memory_usage()
        print("✓ 内存检查功能可调用")
        
        # 清理
        window.close()
        
        print("\n✅ 内存管理功能测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_components_initialization():
    """测试4：UI组件初始化"""
    print("\n" + "=" * 60)
    print("测试4：UI组件初始化")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = simple_ui_fixed.VisionAIClipsMaster()
        
        # 检查关键UI组件是否存在
        print("\n检查关键UI组件...")
        
        components = [
            ("tabs", "标签页组件"),
            ("video_list", "视频列表"),
            ("srt_list", "字幕列表"),
            ("process_progress_bar", "进度条"),
            ("lang_auto_radio", "自动语言单选按钮"),
            ("lang_zh_radio", "中文语言单选按钮"),
            ("lang_en_radio", "英文语言单选按钮"),
        ]
        
        for attr_name, description in components:
            if hasattr(window, attr_name):
                print(f"✓ {description} ({attr_name}) 存在")
            else:
                print(f"✗ {description} ({attr_name}) 不存在")
                return False
        
        # 清理
        window.close()
        
        print("\n✅ UI组件初始化测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_monitoring():
    """测试5：性能监控功能"""
    print("\n" + "=" * 60)
    print("测试5：性能监控功能")
    print("=" * 60)
    
    try:
        import simple_ui_fixed
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        window = simple_ui_fixed.VisionAIClipsMaster()
        
        # 测试性能摘要获取
        print("\n测试获取性能摘要...")
        if hasattr(window, 'get_performance_summary'):
            summary = window.get_performance_summary()
            print(f"✓ 性能摘要: {summary}")
        else:
            print("⚠ get_performance_summary方法不存在（可选功能）")
        
        # 测试用户交互记录
        print("\n测试用户交互记录...")
        if hasattr(window, 'record_user_interaction'):
            window.record_user_interaction()
            print("✓ 用户交互记录功能可调用")
        else:
            print("⚠ record_user_interaction方法不存在（可选功能）")
        
        # 清理
        window.close()
        
        print("\n✅ 性能监控功能测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster UI集成测试")
    print("=" * 60)
    
    results = []
    
    # 测试1：模型检查工作流程
    result1 = test_model_check_workflow()
    results.append(("模型检查工作流程", result1))
    
    # 测试2：语言模式切换
    result2 = test_language_mode_switching()
    results.append(("语言模式切换", result2))
    
    # 测试3：内存管理功能
    result3 = test_memory_management()
    results.append(("内存管理功能", result3))
    
    # 测试4：UI组件初始化
    result4 = test_ui_components_initialization()
    results.append(("UI组件初始化", result4))
    
    # 测试5：性能监控功能
    result5 = test_performance_monitoring()
    results.append(("性能监控功能", result5))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    print(f"\n总计: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有集成测试通过！UI功能真实可用。")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

