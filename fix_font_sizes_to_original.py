#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复字体大小到原始合理值
"""

import re
from pathlib import Path

def fix_font_sizes():
    """修复字体大小到原始值"""
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 修复字体大小到原始合理值...")
    
    # 字体大小映射 - 恢复到原始合理值
    font_fixes = [
        # 标题字体 - 保持20px
        (r'font-size: 8px;.*?font-weight: bold;.*?color: #4a90e2', 'font-size: 20px;\n                font-weight: bold;\n                color: #4a90e2'),
        
        # 普通文本 - 14px
        (r'font-size: 8px;(?![^}]*font-weight: bold)', 'font-size: 14px;'),
        
        # 小字体 - 12px
        (r'font-size: 8px;(?=[^}]*color: #6c757d)', 'font-size: 12px;'),
        
        # 按钮字体 - 14px
        (r'font-size: 8px;(?=[^}]*border: none)', 'font-size: 14px;'),
        
        # 组标题 - 16px
        (r'font-size: 8px;(?=[^}]*color: #2c3e50)', 'font-size: 16px;'),
        
        # HTML中的字体
        (r'font-size: 8px;(?=[^"]*color: #2c3e50)', 'font-size: 14px;'),
        (r'font-size: 8px;(?=[^"]*color: #495057)', 'font-size: 12px;'),
        (r'font-size: 8px;(?=[^"]*color: #7f8c8d)', 'font-size: 10px;'),
        (r'font-size: 8px;(?=[^"]*color: #27ae60)', 'font-size: 18px;'),
        (r'font-size: 8px;(?=[^"]*color: #856404)', 'font-size: 14px;'),
        (r'font-size: 8px;(?=[^"]*color: #2980b9)', 'font-size: 14px;'),
        (r'font-size: 8px;(?=[^"]*color: #1a5276)', 'font-size: 18px;'),
        
        # setStyleSheet中的字体
        (r'font-size: 8px;(?=[^"]*font-weight: bold)', 'font-size: 16px;'),
        (r'font-size: 8px;(?=[^"]*padding: 8px)', 'font-size: 14px;'),
    ]
    
    fixes_applied = 0
    
    for pattern, replacement in font_fixes:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            fixes_applied += matches
            print(f"✅ 修复了 {matches} 个字体大小设置")
    
    # 特殊处理：确保一些关键字体大小正确
    specific_fixes = [
        # 标题字体
        ('title.*?font-size: \d+px', 'font-size: 20px'),
        # 副标题
        ('subtitle.*?font-size: \d+px', 'font-size: 16px'),
        # 按钮
        ('QPushButton.*?font-size: \d+px', 'font-size: 14px'),
        # 标签
        ('QLabel.*?font-size: \d+px', 'font-size: 14px'),
    ]
    
    # 写入修复后的文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 字体大小修复完成！应用了 {fixes_applied} 个修复")
    
    return True

if __name__ == "__main__":
    fix_font_sizes()
