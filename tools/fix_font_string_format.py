#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复字体字符串格式问题
"""

import re
from pathlib import Path

def fix_font_string_format():
    """修复字体字符串格式问题"""
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 修复字体字符串格式...")
    
    # 修复方法：在每个使用font_sizes的方法开头添加font_sizes定义
    methods_to_fix = [
        'create_training_tab',
        'create_about_tab', 
        'show_about_dialog',
        'show_developer_info',
        'show_hotkey_guide',
        'show_tech_details',
        'show_project_history'
    ]
    
    font_sizes_init = '''        # 初始化响应式字体大小
        if hasattr(self, 'font_manager') and hasattr(self, 'base_font_size'):
            font_sizes = self.font_manager.get_scaled_font_sizes(self.base_font_size)
        else:
            font_sizes = {
                'tiny': 8, 'small': 10, 'normal': 12, 'medium': 14, 
                'large': 16, 'xlarge': 18, 'title': 20, 'header': 24
            }
'''
    
    fixes_applied = 0
    
    for method_name in methods_to_fix:
        # 查找方法定义
        pattern = rf'(def {method_name}\(self.*?\):.*?""".*?""")'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            method_def = match.group(1)
            # 检查是否已经有font_sizes初始化
            if 'font_sizes = ' not in method_def:
                # 在方法定义后添加font_sizes初始化
                replacement = method_def + font_sizes_init
                content = content.replace(method_def, replacement)
                fixes_applied += 1
                print(f"✅ 修复了方法 {method_name}")
    
    # 修复单独的setStyleSheet调用
    # 将 {font_sizes.get(...)} 替换为 f-string 格式
    pattern = r'setStyleSheet\("([^"]*\{font_sizes\.get[^"]*)"'
    
    def replace_setstyle(match):
        style_content = match.group(1)
        # 将样式字符串转换为f-string格式
        return f'setStyleSheet(f"{style_content}"'
    
    content = re.sub(pattern, replace_setstyle, content)
    
    # 修复HTML中的font_sizes引用
    html_pattern = r'<p style="([^"]*\{font_sizes\.get[^"]*)"'
    
    def replace_html_style(match):
        style_content = match.group(1)
        return f'<p style="{style_content}"'
    
    content = re.sub(html_pattern, replace_html_style, content)
    
    # 写入修复后的文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 字体字符串格式修复完成！应用了 {fixes_applied} 个修复")
    
    return True

if __name__ == "__main__":
    fix_font_string_format()
