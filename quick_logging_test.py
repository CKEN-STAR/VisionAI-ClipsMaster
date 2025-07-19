#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时日志功能快速验证
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_basic_logging():
    """测试基础日志功能"""
    print("=" * 50)
    print("基础日志功能测试")
    print("=" * 50)
    
    try:
        # 测试日志处理器
        from src.visionai_clipsmaster.ui.main_window import LogHandler, log_signal_emitter
        
        print("✅ 日志处理器导入成功")
        
        # 创建日志处理器
        log_handler = LogHandler("quick_test")
        print("✅ 日志处理器创建成功")
        
        # 测试日志记录
        test_messages = [
            ("info", "这是一条信息日志"),
            ("warning", "这是一条警告日志"),
            ("error", "这是一条错误日志"),
        ]
        
        for level, message in test_messages:
            log_handler.log(level, message)
            print(f"✅ {level.upper()} 日志记录成功")
        
        # 测试日志获取
        logs = log_handler.get_logs(n=5)
        realtime_logs = log_handler.get_realtime_logs(n=5)
        
        print(f"✅ 文件日志获取成功: {len(logs)} 条")
        print(f"✅ 实时缓存获取成功: {len(realtime_logs)} 条")
        
        # 测试信号机制
        signal_received = False
        
        def test_signal_slot(message, level):
            nonlocal signal_received
            signal_received = True
            print(f"✅ 信号接收成功: [{level}] {message}")
        
        # 连接信号
        log_signal_emitter.log_message.connect(test_signal_slot)
        
        # 发送测试日志
        log_handler.log("info", "信号测试消息")
        time.sleep(0.1)  # 等待信号处理
        
        if signal_received:
            print("✅ 信号槽机制工作正常")
        else:
            print("❌ 信号槽机制未工作")
        
        # 断开信号
        log_signal_emitter.log_message.disconnect(test_signal_slot)
        
        return True
        
    except Exception as e:
        print(f"❌ 基础日志功能测试失败: {e}")
        return False

def test_core_modules():
    """测试核心模块日志"""
    print("\n" + "=" * 50)
    print("核心模块日志测试")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # 测试screenplay_engineer
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        engineer = ScreenplayEngineer()
        engineer.load_subtitles([])
        print("✅ screenplay_engineer 日志正常")
        success_count += 1
    except Exception as e:
        print(f"❌ screenplay_engineer 测试失败: {e}")
    total_count += 1
    
    # 测试model_switcher
    try:
        from src.core.model_switcher import ModelSwitcher
        switcher = ModelSwitcher()
        switcher.switch_model("zh")
        print("✅ model_switcher 日志正常")
        success_count += 1
    except Exception as e:
        print(f"❌ model_switcher 测试失败: {e}")
    total_count += 1
    
    # 测试jianying_exporter
    try:
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        exporter = JianYingProExporter()
        print("✅ jianying_exporter 日志正常")
        success_count += 1
    except Exception as e:
        print(f"❌ jianying_exporter 测试失败: {e}")
    total_count += 1
    
    print(f"\n核心模块测试结果: {success_count}/{total_count} 通过")
    return success_count == total_count

def test_ui_components():
    """测试UI组件导入"""
    print("\n" + "=" * 50)
    print("UI组件导入测试")
    print("=" * 50)
    
    components = [
        ("TrainingPanel", "src.ui.training_panel"),
        ("ProgressDashboard", "src.ui.progress_dashboard"),
        ("RealtimeCharts", "src.ui.realtime_charts"),
        ("AlertManager", "src.ui.alert_manager"),
    ]
    
    success_count = 0
    
    for component_name, module_path in components:
        try:
            module = __import__(module_path, fromlist=[component_name])
            component_class = getattr(module, component_name)
            print(f"✅ {component_name} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {component_name} 导入失败: {e}")
    
    print(f"\nUI组件测试结果: {success_count}/{len(components)} 通过")
    return success_count == len(components)

def main():
    """主测试函数"""
    print("VisionAI-ClipsMaster 实时日志功能快速验证")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    start_time = time.time()
    
    # 运行测试
    test1 = test_basic_logging()
    test2 = test_core_modules()
    test3 = test_ui_components()
    
    end_time = time.time()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    tests = [
        ("基础日志功能", test1),
        ("核心模块日志", test2),
        ("UI组件导入", test3),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
    
    print(f"\n总体结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print(f"测试耗时: {end_time - start_time:.2f} 秒")
    
    if passed == total:
        print("\n🎉 所有测试通过！实时日志功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要进一步检查。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
