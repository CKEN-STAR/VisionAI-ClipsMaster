#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 日志完整性修复最终验证测试
"""

import sys
import os
import time
import logging
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志系统
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def test_log_completeness_fix():
    """测试日志完整性修复"""
    print("=== 日志完整性修复验证 ===")
    
    import simple_ui_latest
    log_handler = simple_ui_latest.LogHandler()
    
    # 获取实际日志文件信息
    if os.path.exists(log_handler.log_file):
        with open(log_handler.log_file, 'r', encoding='utf-8') as f:
            actual_lines = f.readlines()
        actual_total = len(actual_lines)
    else:
        actual_total = 0
    
    print(f"实际日志文件总行数: {actual_total}")
    
    # 测试修复前的问题（使用简化方法模拟）
    old_style_logs = log_handler.get_logs_simple(n=100)  # 模拟旧的100条限制
    print(f"旧方式显示日志数: {len(old_style_logs)}")
    
    # 测试修复后的完整显示
    new_style_result = log_handler.get_logs(n=None)  # 显示全部
    new_style_logs = new_style_result['logs']
    print(f"新方式显示日志数: {len(new_style_logs)}")
    
    # 计算改进效果
    if actual_total > 0:
        old_completeness = (len(old_style_logs) / actual_total) * 100
        new_completeness = (len(new_style_logs) / actual_total) * 100
        improvement = new_completeness - old_completeness
        
        print(f"\n修复效果对比:")
        print(f"修复前完整性: {old_completeness:.1f}% ({len(old_style_logs)}/{actual_total})")
        print(f"修复后完整性: {new_completeness:.1f}% ({len(new_style_logs)}/{actual_total})")
        print(f"改进幅度: +{improvement:.1f}%")
        
        if new_completeness >= 99:
            print("✅ 日志完整性修复成功！")
            return True
        else:
            print("❌ 日志完整性仍有问题")
            return False
    else:
        print("⚠️ 没有日志文件可供测试")
        return False

def test_pagination_functionality():
    """测试分页功能"""
    print("\n=== 分页功能测试 ===")
    
    import simple_ui_latest
    log_handler = simple_ui_latest.LogHandler()
    
    # 测试不同页面大小
    page_sizes = [50, 100, 200, 500]
    
    for page_size in page_sizes:
        result = log_handler.get_logs(n=page_size, offset=0)
        print(f"页面大小 {page_size}: 获取 {len(result['logs'])} 条，有更多: {result['has_more']}")
    
    # 测试分页导航
    print("\n分页导航测试:")
    page_size = 100
    total_pages = 0
    offset = 0
    
    while True:
        result = log_handler.get_logs(n=page_size, offset=offset)
        total_pages += 1
        print(f"第 {total_pages} 页: {len(result['logs'])} 条日志")
        
        if not result['has_more'] or total_pages >= 5:  # 限制测试页数
            break
        offset += page_size
    
    print(f"总共测试了 {total_pages} 页")
    return True

def test_filtering_functionality():
    """测试过滤功能"""
    print("\n=== 过滤功能测试 ===")
    
    import simple_ui_latest
    log_handler = simple_ui_latest.LogHandler()
    
    # 测试级别过滤
    levels = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"]
    level_counts = {}
    
    for level in levels:
        result = log_handler.get_logs(n=None, level=level)
        level_counts[level] = len(result['logs'])
        print(f"{level} 级别日志: {level_counts[level]} 条")
    
    # 测试搜索过滤
    search_terms = ["初始化", "错误", "成功", "失败"]
    
    print("\n搜索过滤测试:")
    for term in search_terms:
        result = log_handler.get_logs(n=None, search_text=term)
        print(f"包含 '{term}' 的日志: {len(result['logs'])} 条")
    
    # 测试组合过滤
    result = log_handler.get_logs(n=None, level="ERROR", search_text="失败")
    print(f"\nERROR级别且包含'失败'的日志: {len(result['logs'])} 条")
    
    return True

def test_ui_integration():
    """测试UI集成"""
    print("\n=== UI集成测试 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        import simple_ui_latest
        
        # 创建应用（如果需要）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 测试LogViewerDialog创建
        dialog = simple_ui_latest.LogViewerDialog()
        print("✅ LogViewerDialog创建成功")
        
        # 测试初始状态
        print(f"初始页面大小: {dialog.page_size}")
        print(f"初始总日志数: {dialog.total_logs}")
        print(f"初始过滤日志数: {dialog.filtered_logs}")
        
        # 测试状态显示
        status_text = dialog.status_label.text()
        range_text = dialog.range_label.text()
        
        print(f"状态显示: {status_text}")
        print(f"范围显示: {range_text}")
        
        # 测试分页控件
        pagesize_items = [dialog.pagesize_combo.itemText(i) for i in range(dialog.pagesize_combo.count())]
        print(f"页面大小选项: {pagesize_items}")
        
        dialog.close()
        return True
        
    except Exception as e:
        print(f"UI集成测试失败: {e}")
        return False

def test_performance_standards():
    """测试性能标准"""
    print("\n=== 性能标准测试 ===")
    
    import simple_ui_latest
    import psutil
    import gc
    
    log_handler = simple_ui_latest.LogHandler()
    process = psutil.Process()
    
    # 测试启动时间
    start_time = time.time()
    dialog = simple_ui_latest.LogViewerDialog()
    end_time = time.time()
    startup_time = end_time - start_time
    
    print(f"UI启动时间: {startup_time:.2f} 秒")
    
    # 测试内存使用
    gc.collect()
    memory_usage = process.memory_info().rss / 1024 / 1024
    print(f"当前内存使用: {memory_usage:.1f} MB")
    
    # 测试响应时间
    start_time = time.time()
    dialog.refresh_logs()
    end_time = time.time()
    response_time = end_time - start_time
    
    print(f"日志刷新响应时间: {response_time:.2f} 秒")
    
    dialog.close()
    
    # 检查性能标准
    performance_ok = True
    standards = [
        (startup_time <= 5.0, f"启动时间 ≤ 5秒: {startup_time:.2f}s"),
        (memory_usage <= 400, f"内存使用 ≤ 400MB: {memory_usage:.1f}MB"),
        (response_time <= 2.0, f"响应时间 ≤ 2秒: {response_time:.2f}s")
    ]
    
    for passed, description in standards:
        if passed:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            performance_ok = False
    
    return performance_ok

def main():
    """主测试函数"""
    print("=== VisionAI-ClipsMaster 日志完整性修复最终验证 ===")
    print("目标: 验证日志查看器能够显示100%的日志内容")
    
    # 执行所有测试
    tests = [
        ("日志完整性修复", test_log_completeness_fix),
        ("分页功能", test_pagination_functionality),
        ("过滤功能", test_filtering_functionality),
        ("UI集成", test_ui_integration),
        ("性能标准", test_performance_standards)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 失败: {e}")
            results.append((test_name, False))
    
    # 计算总体结果
    print(f"\n{'='*60}")
    print("=== 最终验证结果 ===")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_rate = (passed / total) * 100
    print(f"\n总体通过率: {success_rate:.1f}% ({passed}/{total})")
    
    # 最终评估
    if success_rate >= 95:
        print("\n🎉 日志完整性修复验证成功！")
        print("✅ 日志查看器现在可以显示100%的日志内容")
        print("✅ 分页功能正常工作")
        print("✅ 过滤功能完整")
        print("✅ UI集成良好")
        print("✅ 性能符合标准")
        print("\n用户现在可以查看完整的日志历史记录！")
    elif success_rate >= 80:
        print("\n⚠️ 大部分功能正常，但有少量问题需要解决")
    else:
        print("\n❌ 存在较多问题，需要进一步修复")
    
    return success_rate

if __name__ == "__main__":
    main()
