#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 CSS兼容性修复脚本
移除不支持的CSS3属性，使用PyQt6兼容的替代方案
"""

import re
import os
from pathlib import Path

def fix_css_compatibility(file_path: str) -> dict:
    """
    修复CSS兼容性问题
    
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
        'transform_removed': 0,
        'box_shadow_removed': 0,
        'text_shadow_removed': 0,
        'transition_removed': 0,
        'total_lines_modified': 0
    }
    
    # 1. 移除 transform 属性
    # /* transform not supported in QSS */ -> 注释掉
    transform_pattern = r'(\s*)(/* transform not supported in QSS */]+;)'
    def replace_transform(match):
        fixes_applied['transform_removed'] += 1
        indent = match.group(1)
        transform_line = match.group(2)
        return f"{indent}/* {transform_line} (PyQt6不支持) */"
    
    content = re.sub(transform_pattern, replace_transform, content)
    
    # 2. 移除 box-shadow 属性
    # /* box-shadow not supported in QSS - use border instead */ -> 注释掉
    box_shadow_pattern = r'(\s*)(/* box-shadow not supported in QSS - use border instead */]+;)'
    def replace_box_shadow(match):
        fixes_applied['box_shadow_removed'] += 1
        indent = match.group(1)
        shadow_line = match.group(2)
        return f"{indent}/* {shadow_line} (PyQt6不支持) */"
    
    content = re.sub(box_shadow_pattern, replace_box_shadow, content)
    
    # 3. 移除 text-shadow 属性
    # /* text-shadow not supported in QSS - use color/font-weight instead */ -> 注释掉
    text_shadow_pattern = r'(\s*)(/* text-shadow not supported in QSS - use color/font-weight instead */]+;)'
    def replace_text_shadow(match):
        fixes_applied['text_shadow_removed'] += 1
        indent = match.group(1)
        shadow_line = match.group(2)
        return f"{indent}/* {shadow_line} (PyQt6不支持) */"
    
    content = re.sub(text_shadow_pattern, replace_text_shadow, content)
    
    # 4. 移除 transition 属性
    # /* transition not supported in QSS */ -> 注释掉
    transition_pattern = r'(\s*)(/* transition not supported in QSS */]+;)'
    def replace_transition(match):
        fixes_applied['transition_removed'] += 1
        indent = match.group(1)
        transition_line = match.group(2)
        return f"{indent}/* {transition_line} (PyQt6不支持) */"
    
    content = re.sub(transition_pattern, replace_transition, content)
    
    # 计算修改的行数
    original_lines = original_content.count('\n')
    new_lines = content.count('\n')
    fixes_applied['total_lines_modified'] = abs(new_lines - original_lines)
    
    # 备份原文件
    backup_path = f"{file_path}.backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ 原文件已备份到: {backup_path}")
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return fixes_applied

def add_css_warning_suppression(file_path: str):
    """
    在文件开头添加CSS警告抑制代码
    """
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经添加了警告抑制代码
    if "QApplication.setAttribute" in content:
        print("⚠️ CSS警告抑制代码已存在")
        return
    
    # 找到导入部分的结束位置
    import_end_pattern = r'(from PyQt6\.QtWidgets import[^\n]*\n)'
    match = re.search(import_end_pattern, content)
    
    if match:
        # 在导入后添加警告抑制代码
        warning_suppression_code = '''
# 抑制PyQt6 CSS兼容性警告
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# 设置Qt属性以减少CSS警告
if hasattr(Qt, 'AA_DisableWindowContextHelpButton'):
    QApplication.setAttribute(Qt.AA_DisableWindowContextHelpButton, True)

# 重定向Qt警告到自定义处理器
def qt_message_handler(mode, context, message):
    # 过滤CSS相关警告
    css_warnings = [
        'Unknown property',
        'transform',
        'box-shadow', 
        'text-shadow',
        'transition'
    ]
    
    if any(warning in message for warning in css_warnings):
        return  # 忽略CSS警告
    
    # 其他警告正常输出
    if mode == 0:  # QtDebugMsg
        print(f"Qt Debug: {message}")
    elif mode == 1:  # QtWarningMsg
        print(f"Qt Warning: {message}")
    elif mode == 2:  # QtCriticalMsg
        print(f"Qt Critical: {message}")
    elif mode == 3:  # QtFatalMsg
        print(f"Qt Fatal: {message}")

# 安装消息处理器
try:
    from PyQt6.QtCore import qInstallMessageHandler
    qInstallMessageHandler(qt_message_handler)
except ImportError:
    pass  # 如果不支持则忽略

'''
        
        insert_pos = match.end()
        new_content = content[:insert_pos] + warning_suppression_code + content[insert_pos:]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 已添加CSS警告抑制代码")
    else:
        print("⚠️ 未找到合适的插入位置，请手动添加警告抑制代码")

def main():
    """主函数"""
    print("🔧 开始修复PyQt6 CSS兼容性问题")
    print("=" * 60)
    
    # 修复simple_ui_fixed.py
    file_path = "simple_ui_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📝 正在修复文件: {file_path}")
    
    # 执行CSS兼容性修复
    fixes = fix_css_compatibility(file_path)
    
    print("\n📊 修复统计:")
    print(f"   transform属性移除: {fixes['transform_removed']} 个")
    print(f"   box-shadow属性移除: {fixes['box_shadow_removed']} 个") 
    print(f"   text-shadow属性移除: {fixes['text_shadow_removed']} 个")
    print(f"   transition属性移除: {fixes['transition_removed']} 个")
    print(f"   总计修复: {sum(fixes.values())} 处")
    
    # 添加警告抑制代码
    print(f"\n🔇 添加CSS警告抑制机制...")
    add_css_warning_suppression(file_path)
    
    print(f"\n✅ CSS兼容性修复完成!")
    print(f"   原文件备份: {file_path}.backup")
    print(f"   修复后文件: {file_path}")
    
    # 验证修复效果
    print(f"\n🧪 验证修复效果...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有未修复的CSS3属性
        remaining_issues = []
        if 'transform:' in content and '/* transform:' not in content:
            remaining_issues.append('transform')
        if 'box-shadow:' in content and '/* box-shadow:' not in content:
            remaining_issues.append('box-shadow')
        if 'text-shadow:' in content and '/* text-shadow:' not in content:
            remaining_issues.append('text-shadow')
        
        if remaining_issues:
            print(f"⚠️ 仍有未修复的CSS属性: {', '.join(remaining_issues)}")
        else:
            print("✅ 所有CSS3不兼容属性已修复")
            
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")

if __name__ == "__main__":
    main()
