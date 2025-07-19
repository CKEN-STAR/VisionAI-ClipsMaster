#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试simple_ui_fixed.py中的日志查看器功能
"""

import sys
import os
import time
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def test_log_handler_in_fixed_ui():
    """测试simple_ui_fixed.py中的LogHandler"""
    print("=== 测试simple_ui_fixed.py中的LogHandler ===")
    
    try:
        # 导入simple_ui_fixed模块
        import simple_ui_fixed
        
        # 检查log_handler是否存在
        if hasattr(simple_ui_fixed, 'log_handler'):
            log_handler = simple_ui_fixed.log_handler
            print("✓ log_handler 存在")
            
            # 检查日志文件路径
            print(f"日志文件路径: {log_handler.log_file}")
            print(f"日志文件是否存在: {os.path.exists(log_handler.log_file)}")
            
            # 测试写入日志
            log_handler.log("info", "测试日志记录 - simple_ui_fixed")
            print("✓ 日志写入测试完成")
            
            # 测试读取日志
            logs = log_handler.get_logs(n=10)
            print(f"读取到的日志数量: {len(logs)}")
            
            if logs:
                print("最新的几条日志:")
                for i, log in enumerate(logs[:3]):
                    print(f"  {i+1}: {log.strip()}")
            else:
                print("❌ 没有读取到日志内容")
                
                # 检查可能的日志文件
                log_dir = os.path.dirname(log_handler.log_file)
                if os.path.exists(log_dir):
                    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
                    print(f"日志目录中的文件: {log_files}")
                    
                    # 尝试读取主日志文件
                    main_log = os.path.join(log_dir, "visionai.log")
                    if os.path.exists(main_log):
                        print(f"发现主日志文件: {main_log}")
                        with open(main_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        print(f"主日志文件行数: {len(lines)}")
                        
                        # 更新log_handler的日志文件路径
                        log_handler.log_file = main_log
                        logs = log_handler.get_logs(n=10)
                        print(f"使用主日志文件读取到的日志数量: {len(logs)}")
            
            return log_handler
            
        else:
            print("❌ log_handler 不存在")
            return None
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

def test_log_viewer_dialog():
    """测试LogViewerDialog"""
    print("\n=== 测试LogViewerDialog ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        import simple_ui_fixed
        
        # 创建应用（如果需要）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 测试LogViewerDialog创建
        dialog = simple_ui_fixed.LogViewerDialog()
        print("✓ LogViewerDialog创建成功")
        
        # 检查UI组件
        components = [
            ('level_combo', '日志级别选择框'),
            ('search_edit', '搜索输入框'),
            ('log_display', '日志显示区域')
        ]
        
        for attr_name, description in components:
            if hasattr(dialog, attr_name):
                print(f"✓ {description} 存在")
            else:
                print(f"❌ {description} 缺失")
        
        # 测试刷新日志功能
        try:
            dialog.refresh_logs()
            print("✓ refresh_logs方法调用成功")
            
            # 检查日志显示内容
            log_content = dialog.log_display.toPlainText()
            if log_content:
                print(f"✓ 日志内容已显示，长度: {len(log_content)} 字符")
            else:
                print("❌ 日志显示区域为空")
                
        except Exception as e:
            print(f"❌ refresh_logs方法调用失败: {e}")
        
        dialog.close()
        return True
        
    except Exception as e:
        print(f"❌ LogViewerDialog测试失败: {e}")
        return False

def test_show_log_viewer_method():
    """测试show_log_viewer方法"""
    print("\n=== 测试show_log_viewer方法 ===")
    
    try:
        import simple_ui_fixed
        
        # 检查SimpleScreenplayApp类是否有show_log_viewer方法
        if hasattr(simple_ui_fixed, 'SimpleScreenplayApp'):
            app_class = simple_ui_fixed.SimpleScreenplayApp
            if hasattr(app_class, 'show_log_viewer'):
                print("✓ show_log_viewer方法存在")
                return True
            else:
                print("❌ show_log_viewer方法不存在")
                return False
        else:
            print("❌ SimpleScreenplayApp类不存在")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_button_binding():
    """测试按钮绑定"""
    print("\n=== 测试按钮绑定 ===")
    
    try:
        # 读取文件内容检查按钮绑定
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键代码
        checks = [
            ('view_log_btn.clicked.connect(self.show_log_viewer)', '查看日志按钮事件绑定'),
            ('view_log_action.triggered.connect(self.show_log_viewer)', '菜单项事件绑定'),
            ('def show_log_viewer(self):', 'show_log_viewer方法定义'),
            ('LogViewerDialog(self)', 'LogViewerDialog创建')
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
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== simple_ui_fixed.py 日志查看器功能诊断 ===")
    
    # 测试1: LogHandler
    log_handler = test_log_handler_in_fixed_ui()
    
    # 测试2: LogViewerDialog
    dialog_ok = test_log_viewer_dialog()
    
    # 测试3: show_log_viewer方法
    method_ok = test_show_log_viewer_method()
    
    # 测试4: 按钮绑定
    binding_ok = test_button_binding()
    
    # 总结问题
    print("\n=== 问题诊断总结 ===")
    
    issues = []
    if not log_handler:
        issues.append("LogHandler创建或功能异常")
    elif not hasattr(log_handler, 'log_file') or not os.path.exists(log_handler.log_file):
        issues.append("日志文件路径配置错误")
    
    if not dialog_ok:
        issues.append("LogViewerDialog实现有问题")
    
    if not method_ok:
        issues.append("show_log_viewer方法缺失")
    
    if not binding_ok:
        issues.append("按钮事件绑定有问题")
    
    if issues:
        print("发现的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✓ 所有基本组件都正常")
    
    # 修复建议
    print("\n=== 修复建议 ===")
    if log_handler and hasattr(log_handler, 'log_file'):
        log_dir = os.path.dirname(log_handler.log_file)
        main_log = os.path.join(log_dir, "visionai.log")
        if os.path.exists(main_log):
            print("1. 修复日志文件路径，使用主日志文件 visionai.log")
        else:
            print("1. 检查日志文件创建和路径配置")
    
    if not dialog_ok:
        print("2. 修复LogViewerDialog的实现")
    
    print("3. 参考simple_ui_latest.py中的成功实现")
    print("4. 确保导入和依赖关系正确")

if __name__ == "__main__":
    main()
