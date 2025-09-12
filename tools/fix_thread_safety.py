#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线程安全修复脚本
确保所有UI操作都在主线程中执行
"""

import re
import os

def fix_thread_safety_issues(file_path: str) -> dict:
    """
    修复线程安全问题
    
    Args:
        file_path: 要修复的文件路径
        
    Returns:
        dict: 修复结果统计
    """
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes_applied = {
        'thread_checks_added': 0,
        'qtimer_fixes': 0,
        'signal_connections_fixed': 0,
        'total_fixes': 0
    }
    
    # 1. 在文件开头添加线程安全工具函数
    thread_safety_utils = '''
# 线程安全工具函数
def ensure_main_thread(func):
    """装饰器：确保函数在主线程中执行"""
    def wrapper(*args, **kwargs):
        try:
            from PyQt6.QtCore import QTimer, QThread
            from PyQt6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app and QThread.currentThread() != app.thread():
                # 不在主线程，使用QTimer.singleShot延迟到主线程执行
                QTimer.singleShot(0, lambda: func(*args, **kwargs))
                return
            else:
                # 在主线程，直接执行
                return func(*args, **kwargs)
        except Exception as e:
            print(f"[WARN] 线程安全执行失败: {e}")
            # 回退到直接执行
            return func(*args, **kwargs)
    return wrapper

def safe_signal_emit(signal, *args):
    """线程安全的信号发送"""
    try:
        from PyQt6.QtCore import QTimer, QThread
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app and QThread.currentThread() != app.thread():
            # 不在主线程，延迟发送
            QTimer.singleShot(0, lambda: signal.emit(*args))
        else:
            # 在主线程，直接发送
            signal.emit(*args)
    except Exception as e:
        print(f"[WARN] 线程安全信号发送失败: {e}")
        try:
            signal.emit(*args)  # 回退到直接发送
        except:
            pass

'''
    
    # 找到合适的插入位置（在导入之后）
    import_pattern = r'(from PyQt6\.QtCore import[^\n]*\n)'
    match = re.search(import_pattern, content)
    
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + thread_safety_utils + content[insert_pos:]
        fixes_applied['thread_checks_added'] += 1
    
    # 2. 修复直接的信号发送，使用线程安全版本
    # 查找 signal.emit() 模式并替换
    signal_emit_pattern = r'(\w+)\.emit\(([^)]*)\)'
    def replace_signal_emit(match):
        signal_name = match.group(1)
        args = match.group(2)
        fixes_applied['signal_connections_fixed'] += 1
        return f'safe_signal_emit({signal_name}, {args})'
    
    # 只替换明显的信号发送（避免误替换）
    signal_patterns = [
        r'(progress_updated|item_completed|all_completed|error_occurred|performance_update|response_time_update)\.emit\(([^)]*)\)'
    ]
    
    for pattern in signal_patterns:
        content = re.sub(pattern, replace_signal_emit, content)
    
    # 3. 确保QTimer.singleShot调用的线程安全性
    # 查找现有的QTimer.singleShot调用，确保它们是线程安全的
    qtimer_pattern = r'QTimer\.singleShot\((\d+),\s*([^)]+)\)'
    def fix_qtimer_call(match):
        delay = match.group(1)
        callback = match.group(2)
        fixes_applied['qtimer_fixes'] += 1
        
        # 包装回调以确保线程安全
        return f'QTimer.singleShot({delay}, ensure_main_thread({callback}))'
    
    # 暂时注释掉这个修复，因为可能会导致语法问题
    # content = re.sub(qtimer_pattern, fix_qtimer_call, content)
    
    # 4. 添加线程检查到关键的初始化方法
    init_methods = [
        '_init_stability_monitor',
        '_init_responsiveness_monitor', 
        '_init_alert_manager_in_main_thread',
        '_init_ui_error_handler'
    ]
    
    for method in init_methods:
        method_pattern = f'(def {method}\\(self[^)]*\\):[^\\n]*\\n)(\\s*)(.*?)(?=\\n\\s*def|\\n\\s*class|\\Z)'
        
        def add_thread_check(match):
            method_def = match.group(1)
            indent = match.group(2)
            method_body = match.group(3)
            
            thread_check = f'''{indent}# 确保在主线程中执行
{indent}from PyQt6.QtCore import QThread
{indent}from PyQt6.QtWidgets import QApplication
{indent}app = QApplication.instance()
{indent}if app and QThread.currentThread() != app.thread():
{indent}    print(f"[WARN] {{self.__class__.__name__}}.{method} 不在主线程中执行，延迟到主线程")
{indent}    QTimer.singleShot(0, lambda: self.{method}())
{indent}    return
{indent}
'''
            
            fixes_applied['thread_checks_added'] += 1
            return method_def + thread_check + method_body
        
        content = re.sub(method_pattern, add_thread_check, content, flags=re.DOTALL)
    
    # 计算总修复数
    fixes_applied['total_fixes'] = sum(fixes_applied.values()) - fixes_applied['total_fixes']
    
    # 备份原文件
    backup_path = f"{file_path}.thread_safety_backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ 原文件已备份到: {backup_path}")
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return fixes_applied

def add_thread_safety_imports(file_path: str):
    """添加线程安全相关的导入"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有QMetaObject导入
    if "QMetaObject" not in content:
        # 在PyQt6.QtCore导入中添加QMetaObject
        qtcore_pattern = r'(from PyQt6\.QtCore import[^)]*)(Qt, pyqtSignal, QThread, QObject, QTimer)([^)]*\))'
        
        def add_qmetaobject(match):
            prefix = match.group(1)
            core_imports = match.group(2)
            suffix = match.group(3)
            
            # 添加QMetaObject到导入列表
            new_imports = core_imports + ", QMetaObject"
            return prefix + new_imports + suffix
        
        content = re.sub(qtcore_pattern, add_qmetaobject, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已添加QMetaObject导入")

def main():
    """主函数"""
    print("🔧 开始修复线程安全问题")
    print("=" * 60)
    
    file_path = "simple_ui_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📝 正在修复文件: {file_path}")
    
    # 添加必要的导入
    add_thread_safety_imports(file_path)
    
    # 执行线程安全修复
    fixes = fix_thread_safety_issues(file_path)
    
    print("\n📊 修复统计:")
    print(f"   线程检查添加: {fixes['thread_checks_added']} 处")
    print(f"   QTimer修复: {fixes['qtimer_fixes']} 处") 
    print(f"   信号连接修复: {fixes['signal_connections_fixed']} 处")
    print(f"   总计修复: {fixes['total_fixes']} 处")
    
    print(f"\n✅ 线程安全修复完成!")
    print(f"   原文件备份: {file_path}.thread_safety_backup")
    print(f"   修复后文件: {file_path}")
    
    # 验证修复效果
    print(f"\n🧪 验证修复效果...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否添加了线程安全工具
        if 'ensure_main_thread' in content and 'safe_signal_emit' in content:
            print("✅ 线程安全工具函数已添加")
        else:
            print("⚠️ 线程安全工具函数添加可能不完整")
        
        # 检查是否有QMetaObject导入
        if 'QMetaObject' in content:
            print("✅ QMetaObject导入已添加")
        else:
            print("⚠️ QMetaObject导入可能缺失")
            
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")

if __name__ == "__main__":
    main()
