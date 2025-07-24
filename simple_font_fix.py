#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的字体大小修复脚本
"""

import re
from pathlib import Path

def simple_font_fix():
    """简单修复字体大小问题"""
    
    ui_file = Path("simple_ui_fixed.py")
    
    # 读取文件
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 开始简单字体修复...")
    
    # 创建字体大小映射（基于14px基础字体）
    font_mapping = {
        '8px': '10px',    # tiny -> small
        '10px': '12px',   # small -> normal  
        '11px': '13px',   # small -> normal+
        '12px': '14px',   # normal -> medium
        '13px': '15px',   # normal+ -> medium+
        '14px': '16px',   # medium -> large
        '15px': '17px',   # medium+ -> large+
        '16px': '18px',   # large -> xlarge
        '18px': '20px',   # xlarge -> title
        '20px': '24px',   # title -> header
        '22px': '26px',   # header -> header+
        '24px': '28px',   # header -> header++
        '36px': '40px',   # huge -> huge+
    }
    
    fixes_applied = 0
    
    # 替换CSS中的字体大小
    for old_size, new_size in font_mapping.items():
        pattern = rf'font-size:\s*{re.escape(old_size)}'
        replacement = f'font-size: {new_size}'
        
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            fixes_applied += matches
            print(f"✅ 将 {old_size} 替换为 {new_size} ({matches} 处)")
    
    # 替换QFont.setPointSize调用
    pattern = r'font\.setPointSize\((\d+)\)'
    def replace_point_size(match):
        old_size = int(match.group(1))
        new_size = min(24, max(10, old_size + 2))  # 增加2pt，限制在10-24范围内
        return f'font.setPointSize({new_size})'
    
    matches = len(re.findall(pattern, content))
    if matches > 0:
        content = re.sub(pattern, replace_point_size, content)
        fixes_applied += matches
        print(f"✅ 修复了 {matches} 个QFont字体大小设置")
    
    # 修复f-string格式问题 - 将所有{font_sizes.get(...)}替换为固定值
    fstring_pattern = r'\{font_sizes\.get\("(\w+)",\s*(\d+)\)\}'
    def replace_fstring(match):
        font_type = match.group(1)
        default_size = int(match.group(2))
        
        # 根据字体类型返回合适的大小
        size_map = {
            'tiny': 10,
            'small': 12, 
            'normal': 16,
            'medium': 18,
            'large': 20,
            'xlarge': 22,
            'title': 24,
            'header': 28
        }
        
        new_size = size_map.get(font_type, default_size + 2)
        return str(new_size)
    
    matches = len(re.findall(fstring_pattern, content))
    if matches > 0:
        content = re.sub(fstring_pattern, replace_fstring, content)
        fixes_applied += matches
        print(f"✅ 修复了 {matches} 个f-string字体大小")
    
    # 写入修复后的文件
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 简单字体修复完成！总共应用了 {fixes_applied} 个修复")
    
    return True

if __name__ == "__main__":
    simple_font_fix()
