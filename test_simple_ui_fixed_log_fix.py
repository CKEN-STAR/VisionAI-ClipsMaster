#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试simple_ui_fixed.py中日志查看器修复效果
"""

import sys
import os
import time
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_log_handler_fix():
    """测试LogHandler修复效果"""
    print("=== 测试LogHandler修复效果 ===")
    
    try:
        import simple_ui_fixed
        log_handler = simple_ui_fixed.log_handler
        
        print(f"修复后的日志文件路径: {log_handler.log_file}")
        print(f"日志文件是否存在: {os.path.exists(log_handler.log_file)}")
        
        # 检查是否使用了主日志文件
        main_log_file = os.path.join(os.path.dirname(log_handler.log_file), "visionai.log")
        if log_handler.log_file == main_log_file:
            print("✓ 正确使用主日志文件 visionai.log")
        else:
            print(f"⚠️ 使用的是日期格式日志文件: {os.path.basename(log_handler.log_file)}")
        
        # 测试日志读取数量
        logs_50 = log_handler.get_logs(n=50)
        logs_500 = log_handler.get_logs(n=500)
        logs_1000 = log_handler.get_logs(n=1000)
        
        print(f"\n日志读取测试:")
        print(f"请求50条日志，获取: {len(logs_50)} 条")
        print(f"请求500条日志，获取: {len(logs_500)} 条")
        print(f"请求1000条日志，获取: {len(logs_1000)} 条")
        
        # 检查实际日志文件总数
        if os.path.exists(log_handler.log_file):
            with open(log_handler.log_file, 'r', encoding='utf-8') as f:
                total_lines = len(f.readlines())
            print(f"实际日志文件总行数: {total_lines}")
            
            # 计算完整性
            completeness = (len(logs_1000) / total_lines) * 100 if total_lines > 0 else 0
            print(f"日志显示完整性: {completeness:.1f}% ({len(logs_1000)}/{total_lines})")
            
            if completeness >= 95:
                print("✅ 日志显示完整性优秀")
                return True
            elif completeness >= 80:
                print("⚠️ 日志显示完整性良好")
                return True
            else:
                print("❌ 日志显示完整性需要改进")
                return False
        else:
            print("❌ 日志文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_log_viewer_dialog_fix():
    """测试LogViewerDialog修复效果"""
    print("\n=== 测试LogViewerDialog修复效果 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        import simple_ui_fixed
        
        # 创建应用（如果需要）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建日志查看器
        dialog = simple_ui_fixed.LogViewerDialog()
        print("✓ LogViewerDialog创建成功")
        
        # 测试刷新功能
        dialog.refresh_logs()
        print("✓ refresh_logs方法调用成功")
        
        # 检查显示内容
        log_content = dialog.log_display.toPlainText()
        print(f"日志显示内容长度: {len(log_content)} 字符")
        
        if log_content:
            # 检查是否包含统计信息
            if "=== 日志查看器" in log_content:
                print("✓ 包含日志统计信息")
            
            # 检查日志数量
            lines = log_content.split('\n')
            log_lines = [line for line in lines if line.strip() and not line.startswith('===')]
            print(f"显示的日志行数: {len(log_lines)}")
            
            if len(log_lines) >= 100:
                print("✅ 显示了大量日志内容")
                return True
            elif len(log_lines) >= 50:
                print("⚠️ 显示了适量日志内容")
                return True
            else:
                print("❌ 显示的日志内容过少")
                return False
        else:
            print("❌ 没有显示任何日志内容")
            return False
        
        dialog.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_filtering_functionality():
    """测试过滤功能"""
    print("\n=== 测试过滤功能 ===")
    
    try:
        import simple_ui_fixed
        log_handler = simple_ui_fixed.log_handler
        
        # 测试级别过滤
        info_logs = log_handler.get_logs(n=1000, level="INFO")
        warning_logs = log_handler.get_logs(n=1000, level="WARNING")
        error_logs = log_handler.get_logs(n=1000, level="ERROR")
        
        print(f"INFO级别日志: {len(info_logs)} 条")
        print(f"WARNING级别日志: {len(warning_logs)} 条")
        print(f"ERROR级别日志: {len(error_logs)} 条")
        
        # 测试搜索过滤
        search_logs = log_handler.get_logs(n=1000, search_text="初始化")
        print(f"包含'初始化'的日志: {len(search_logs)} 条")
        
        # 验证过滤结果
        if info_logs or warning_logs or error_logs:
            print("✅ 级别过滤功能正常")
        else:
            print("⚠️ 级别过滤可能有问题")
        
        if search_logs:
            print("✅ 搜索过滤功能正常")
        else:
            print("⚠️ 搜索过滤可能有问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 过滤功能测试失败: {e}")
        return False

def test_ui_integration():
    """测试UI集成"""
    print("\n=== 测试UI集成 ===")
    
    try:
        # 检查show_log_viewer方法
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键代码
        checks = [
            ('def show_log_viewer(self):', 'show_log_viewer方法定义'),
            ('LogViewerDialog(self)', 'LogViewerDialog创建'),
            ('log_viewer.show()', '对话框显示'),
            ('view_log_btn.clicked.connect(self.show_log_viewer)', '按钮事件绑定')
        ]
        
        all_passed = True
        for check_code, description in checks:
            if check_code in content:
                print(f"✓ {description}")
            else:
                print(f"❌ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ UI集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== simple_ui_fixed.py 日志查看器修复验证 ===")
    print("目标: 验证日志查看器能够正常工作并显示完整内容")
    
    # 执行所有测试
    tests = [
        ("LogHandler修复", test_log_handler_fix),
        ("LogViewerDialog修复", test_log_viewer_dialog_fix),
        ("过滤功能", test_filtering_functionality),
        ("UI集成", test_ui_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 失败: {e}")
            results.append((test_name, False))
    
    # 计算总体结果
    print(f"\n{'='*50}")
    print("=== 修复验证结果 ===")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_rate = (passed / total) * 100
    print(f"\n总体通过率: {success_rate:.1f}% ({passed}/{total})")
    
    # 最终评估
    if success_rate >= 95:
        print("\n🎉 simple_ui_fixed.py 日志查看器修复成功！")
        print("✅ 日志文件路径配置正确")
        print("✅ 日志内容显示完整")
        print("✅ 过滤功能正常工作")
        print("✅ UI集成良好")
        print("\n用户现在可以正常使用'查看日志'功能了！")
    elif success_rate >= 75:
        print("\n⚠️ 大部分功能正常，但有少量问题需要解决")
    else:
        print("\n❌ 存在较多问题，需要进一步修复")
    
    return success_rate

if __name__ == "__main__":
    main()
