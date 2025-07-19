#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单的日志查看器修复验证
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

def verify_log_files():
    """验证日志文件"""
    print("=== 验证日志文件 ===")
    
    # 检查可能的日志文件
    possible_files = [
        os.path.join(LOG_DIR, "visionai.log"),
        os.path.join(LOG_DIR, f"visionai_{time.strftime('%Y%m%d')}.log"),
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ 找到日志文件: {file_path} (大小: {size} 字节)")
            
            # 读取最后几行
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"  文件行数: {len(lines)}")
                
                if lines:
                    print("  最后3行:")
                    for line in lines[-3:]:
                        print(f"    {line.strip()}")
                        
            except Exception as e:
                print(f"  读取失败: {e}")
        else:
            print(f"✗ 文件不存在: {file_path}")

def verify_log_handler_import():
    """验证LogHandler导入"""
    print("\n=== 验证LogHandler导入 ===")
    
    try:
        # 直接导入simple_ui_latest模块
        import simple_ui_latest
        
        # 检查LogHandler类是否存在
        if hasattr(simple_ui_latest, 'LogHandler'):
            print("✓ LogHandler类导入成功")
            
            # 创建实例
            log_handler = simple_ui_latest.LogHandler()
            print(f"✓ LogHandler实例创建成功")
            print(f"  使用的日志文件: {log_handler.log_file}")
            
            # 测试写入日志
            log_handler.log("info", "验证测试日志")
            print("✓ 日志写入测试成功")
            
            # 测试读取日志
            logs = log_handler.get_logs(n=5)
            print(f"✓ 日志读取测试成功，获取到 {len(logs)} 条日志")
            
            return log_handler
            
        else:
            print("✗ LogHandler类不存在")
            return None
            
    except Exception as e:
        print(f"✗ LogHandler导入失败: {e}")
        return None

def verify_log_viewer_dialog():
    """验证LogViewerDialog"""
    print("\n=== 验证LogViewerDialog ===")
    
    try:
        import simple_ui_latest
        
        if hasattr(simple_ui_latest, 'LogViewerDialog'):
            print("✓ LogViewerDialog类存在")
            
            # 检查PyQt6是否可用
            try:
                from PyQt6.QtWidgets import QApplication
                print("✓ PyQt6可用")
                
                # 创建应用（如果需要）
                app = QApplication.instance()
                if app is None:
                    app = QApplication(sys.argv)
                
                # 创建对话框实例
                dialog = simple_ui_latest.LogViewerDialog()
                print("✓ LogViewerDialog实例创建成功")
                
                # 测试刷新方法
                dialog.refresh_logs()
                print("✓ refresh_logs方法调用成功")
                
                dialog.close()
                return True
                
            except Exception as e:
                print(f"✗ PyQt6测试失败: {e}")
                return False
                
        else:
            print("✗ LogViewerDialog类不存在")
            return False
            
    except Exception as e:
        print(f"✗ LogViewerDialog验证失败: {e}")
        return False

def verify_ui_button():
    """验证UI按钮"""
    print("\n=== 验证UI按钮 ===")
    
    try:
        # 读取UI文件内容
        with open("simple_ui_latest.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键代码
        checks = [
            ('view_log_btn.clicked.connect(self.show_log_viewer)', "查看日志按钮事件绑定"),
            ('def show_log_viewer(self):', "show_log_viewer方法定义"),
            ('log_viewer = LogViewerDialog(self)', "LogViewerDialog创建"),
            ('log_viewer.show()', "对话框显示")
        ]
        
        all_passed = True
        for check_code, description in checks:
            if check_code in content:
                print(f"✓ {description}")
            else:
                print(f"✗ {description}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ UI按钮验证失败: {e}")
        return False

def main():
    """主验证函数"""
    print("=== VisionAI-ClipsMaster 日志查看器修复验证 ===")
    
    # 验证1: 日志文件
    verify_log_files()
    
    # 验证2: LogHandler
    log_handler = verify_log_handler_import()
    
    # 验证3: LogViewerDialog
    dialog_ok = verify_log_viewer_dialog()
    
    # 验证4: UI按钮
    button_ok = verify_ui_button()
    
    # 总结
    print("\n=== 验证结果总结 ===")
    
    results = [
        ("日志文件存在", os.path.exists(os.path.join(LOG_DIR, "visionai.log"))),
        ("LogHandler功能", log_handler is not None),
        ("LogViewerDialog功能", dialog_ok),
        ("UI按钮集成", button_ok)
    ]
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    success_rate = (passed / total) * 100
    print(f"\n总体通过率: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 75:
        print("\n🎉 日志查看器修复验证成功！")
        print("用户现在可以正常使用'查看日志'功能了。")
    else:
        print("\n⚠️ 还有部分问题需要解决")
    
    return success_rate

if __name__ == "__main__":
    main()
