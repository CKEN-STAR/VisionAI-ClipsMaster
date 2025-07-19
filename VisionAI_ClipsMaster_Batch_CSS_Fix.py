#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 批量CSS修复脚本

批量移除PyQt6不支持的CSS属性

作者: CKEN
版本: v1.0
日期: 2025-07-12
"""

import re
from pathlib import Path

def batch_fix_css():
    """批量修复CSS"""
    ui_file = Path("VisionAI-ClipsMaster-Core/simple_ui_fixed.py")
    
    if not ui_file.exists():
        print("❌ UI文件不存在")
        return
    
    print("🧹 开始批量清理CSS警告...")
    
    # 读取文件
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 定义需要移除的CSS属性模式
    css_patterns_to_remove = [
        r'\s*transform:\s*[^;]+;?\s*\n?',
        r'\s*box-shadow:\s*[^;]+;?\s*\n?',
        r'\s*text-shadow:\s*[^;]+;?\s*\n?',
        r'\s*transition:\s*[^;]+;?\s*\n?',
        r'\s*-webkit-[^:]*:\s*[^;]+;?\s*\n?',
        r'\s*-moz-[^:]*:\s*[^;]+;?\s*\n?',
        r'\s*-ms-[^:]*:\s*[^;]+;?\s*\n?'
    ]
    
    removed_count = 0
    
    # 逐个移除不支持的CSS属性
    for pattern in css_patterns_to_remove:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            removed_count += len(matches)
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            print(f"  移除 {len(matches)} 个匹配: {pattern[:30]}...")
    
    # 清理多余的空行
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # 保存修复后的文件
    if content != original_content:
        with open(ui_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ CSS清理完成！")
        print(f"  移除CSS属性: {removed_count} 个")
        print(f"  文件大小变化: {len(original_content)} → {len(content)} 字节")
    else:
        print("ℹ️ 未发现需要清理的CSS属性")

if __name__ == "__main__":
    batch_fix_css()
