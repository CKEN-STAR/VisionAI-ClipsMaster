#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试增强版日志查看器功能
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

def test_enhanced_log_handler():
    """测试增强版LogHandler"""
    print("=== 测试增强版LogHandler ===")
    
    # 导入增强版LogHandler
    import simple_ui_latest
    log_handler = simple_ui_latest.LogHandler()
    
    print(f"使用的日志文件: {log_handler.log_file}")
    
    # 测试新的get_logs方法
    print("\n1. 测试新的get_logs方法...")
    
    # 获取所有日志
    all_logs_result = log_handler.get_logs(n=None)
    print(f"总日志数: {all_logs_result['total_count']}")
    print(f"过滤后日志数: {all_logs_result['filtered_count']}")
    print(f"实际获取日志数: {len(all_logs_result['logs'])}")
    print(f"是否有更多: {all_logs_result['has_more']}")
    
    # 测试分页
    print("\n2. 测试分页功能...")
    page_size = 100
    page1 = log_handler.get_logs(n=page_size, offset=0)
    page2 = log_handler.get_logs(n=page_size, offset=page_size)
    
    print(f"第1页: {len(page1['logs'])} 条日志，有更多: {page1['has_more']}")
    print(f"第2页: {len(page2['logs'])} 条日志，有更多: {page2['has_more']}")
    
    # 测试级别过滤
    print("\n3. 测试级别过滤...")
    error_logs = log_handler.get_logs(n=None, level="ERROR")
    warning_logs = log_handler.get_logs(n=None, level="WARNING")
    info_logs = log_handler.get_logs(n=None, level="INFO")
    
    print(f"ERROR级别日志: {len(error_logs['logs'])} 条")
    print(f"WARNING级别日志: {len(warning_logs['logs'])} 条")
    print(f"INFO级别日志: {len(info_logs['logs'])} 条")
    
    # 测试搜索过滤
    print("\n4. 测试搜索过滤...")
    search_result = log_handler.get_logs(n=None, search_text="初始化")
    print(f"包含'初始化'的日志: {len(search_result['logs'])} 条")
    
    # 测试向后兼容性
    print("\n5. 测试向后兼容性...")
    simple_logs = log_handler.get_logs_simple(n=50)
    print(f"简化方法获取日志: {len(simple_logs)} 条")
    
    # 测试统计功能
    print("\n6. 测试日志统计...")
    stats = log_handler.get_log_stats()
    print(f"统计信息: {stats}")
    
    return all_logs_result['total_count'], len(all_logs_result['logs'])

def test_enhanced_log_viewer_ui():
    """测试增强版日志查看器UI"""
    print("\n=== 测试增强版日志查看器UI ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        import simple_ui_latest
        
        # 创建应用（如果需要）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建增强版日志查看器
        dialog = simple_ui_latest.LogViewerDialog()
        print("✓ 增强版LogViewerDialog创建成功")
        
        # 检查新增的UI组件
        ui_components = [
            ('pagesize_combo', '每页显示数量选择'),
            ('prev_btn', '上一页按钮'),
            ('next_btn', '下一页按钮'),
            ('page_info_label', '页码信息标签'),
            ('range_label', '显示范围标签'),
            ('show_all_btn', '显示全部按钮'),
            ('top_btn', '顶部按钮'),
            ('bottom_btn', '底部按钮')
        ]
        
        for attr_name, description in ui_components:
            if hasattr(dialog, attr_name):
                print(f"✓ {description} 存在")
            else:
                print(f"✗ {description} 缺失")
        
        # 测试分页功能
        print(f"\n当前页面大小: {dialog.page_size}")
        print(f"当前偏移量: {dialog.current_offset}")
        print(f"总日志数: {dialog.total_logs}")
        print(f"过滤后日志数: {dialog.filtered_logs}")
        
        # 测试状态显示
        status_text = dialog.status_label.text()
        range_text = dialog.range_label.text()
        page_text = dialog.page_info_label.text()
        
        print(f"状态显示: {status_text}")
        print(f"范围显示: {range_text}")
        print(f"页码显示: {page_text}")
        
        # 测试按钮状态
        print(f"上一页按钮启用: {dialog.prev_btn.isEnabled()}")
        print(f"下一页按钮启用: {dialog.next_btn.isEnabled()}")
        print(f"显示全部按钮启用: {dialog.show_all_btn.isEnabled()}")
        
        dialog.close()
        return True
        
    except Exception as e:
        print(f"UI测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print("\n=== 测试性能 ===")
    
    import simple_ui_latest
    import psutil
    import gc
    
    log_handler = simple_ui_latest.LogHandler()
    process = psutil.Process()
    
    # 测试大量日志读取性能
    print("1. 测试大量日志读取性能...")
    
    gc.collect()
    start_memory = process.memory_info().rss / 1024 / 1024
    start_time = time.time()
    
    # 读取所有日志
    all_logs = log_handler.get_logs(n=None)
    
    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024
    
    read_time = end_time - start_time
    memory_increase = end_memory - start_memory
    
    print(f"读取 {len(all_logs['logs'])} 条日志:")
    print(f"  耗时: {read_time:.2f} 秒")
    print(f"  内存增加: {memory_increase:.1f} MB")
    print(f"  当前内存: {end_memory:.1f} MB")
    
    # 检查性能标准
    performance_ok = True
    if read_time > 2.0:
        print(f"  ⚠️ 读取时间超过2秒限制")
        performance_ok = False
    else:
        print(f"  ✓ 读取性能良好")
    
    if end_memory > 400:
        print(f"  ⚠️ 内存使用超过400MB限制")
        performance_ok = False
    else:
        print(f"  ✓ 内存使用正常")
    
    return performance_ok

def main():
    """主测试函数"""
    print("=== VisionAI-ClipsMaster 增强版日志查看器测试 ===")
    
    # 测试1: 增强版LogHandler
    total_logs, displayed_logs = test_enhanced_log_handler()
    
    # 测试2: 增强版UI
    ui_ok = test_enhanced_log_viewer_ui()
    
    # 测试3: 性能测试
    performance_ok = test_performance()
    
    # 总结测试结果
    print("\n=== 测试结果总结 ===")
    
    if total_logs > 0:
        completeness_rate = (displayed_logs / total_logs) * 100
        print(f"日志完整性: {completeness_rate:.1f}% ({displayed_logs}/{total_logs})")
        
        if completeness_rate >= 99:
            print("✅ 日志显示完整性: 优秀")
        elif completeness_rate >= 90:
            print("✅ 日志显示完整性: 良好")
        else:
            print("❌ 日志显示完整性: 需要改进")
    
    print(f"UI功能: {'✅ 正常' if ui_ok else '❌ 异常'}")
    print(f"性能表现: {'✅ 良好' if performance_ok else '❌ 需要优化'}")
    
    # 计算总体评分
    scores = []
    if total_logs > 0:
        scores.append(min(100, (displayed_logs / total_logs) * 100))
    scores.append(100 if ui_ok else 0)
    scores.append(100 if performance_ok else 70)
    
    overall_score = sum(scores) / len(scores)
    print(f"\n总体评分: {overall_score:.1f}/100")
    
    if overall_score >= 95:
        print("🎉 增强版日志查看器修复成功！")
        print("✅ 所有功能正常工作")
        print("✅ 性能符合要求")
        print("✅ 日志显示完整")
    elif overall_score >= 80:
        print("⚠️ 大部分功能正常，但有改进空间")
    else:
        print("❌ 存在问题，需要进一步修复")
    
    return overall_score

if __name__ == "__main__":
    main()
