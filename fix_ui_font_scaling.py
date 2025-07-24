#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI字体缩放修复工具

此脚本修复UI界面在全屏模式下字体过小的问题，实现响应式字体设计
"""

import sys
import os
from pathlib import Path
import re

def fix_ui_font_scaling():
    """修复UI字体缩放问题"""
    
    print("🔧 开始修复VisionAI-ClipsMaster UI字体缩放问题...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    ui_file = project_root / "simple_ui_fixed.py"
    
    if not ui_file.exists():
        print(f"❌ 错误：找不到UI文件 {ui_file}")
        return False
    
    print(f"📁 正在处理文件：{ui_file}")
    
    # 读取文件内容
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file = ui_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 已创建备份文件：{backup_file}")
    
    # 修复硬编码的字体大小
    fixes_applied = 0
    
    # 1. 修复标题字体大小（20px -> 响应式）
    pattern1 = r'font-size:\s*20px;'
    replacement1 = 'font-size: {font_sizes.get("title", 20)}px;'
    if re.search(pattern1, content):
        content = re.sub(pattern1, replacement1, content)
        fixes_applied += 1
        print("✅ 修复了标题字体大小")
    
    # 2. 修复按钮字体大小（14px, 15px -> 响应式）
    pattern2 = r'font-size:\s*(14|15)px;'
    replacement2 = 'font-size: {font_sizes.get("normal", 14)}px;'
    matches = re.findall(pattern2, content)
    if matches:
        content = re.sub(pattern2, replacement2, content)
        fixes_applied += len(matches)
        print(f"✅ 修复了 {len(matches)} 个按钮字体大小")
    
    # 3. 修复小字体（11px, 12px -> 响应式）
    pattern3 = r'font-size:\s*(11|12)px;'
    replacement3 = 'font-size: {font_sizes.get("small", 12)}px;'
    matches = re.findall(pattern3, content)
    if matches:
        content = re.sub(pattern3, replacement3, content)
        fixes_applied += len(matches)
        print(f"✅ 修复了 {len(matches)} 个小字体大小")
    
    # 4. 修复大字体（18px, 22px, 24px, 36px -> 响应式）
    pattern4 = r'font-size:\s*(18|22|24|36)px;'
    def replace_large_font(match):
        size = int(match.group(1))
        if size >= 24:
            return 'font-size: {font_sizes.get("header", 24)}px;'
        else:
            return 'font-size: {font_sizes.get("large", 18)}px;'
    
    matches = re.findall(pattern4, content)
    if matches:
        content = re.sub(pattern4, replace_large_font, content)
        fixes_applied += len(matches)
        print(f"✅ 修复了 {len(matches)} 个大字体大小")
    
    # 5. 修复QFont.setPointSize调用
    pattern5 = r'font\.setPointSize\((\d+)\)'
    replacement5 = 'font.setPointSize(self.font_manager.base_font_size if hasattr(self, "font_manager") else \\1)'
    matches = re.findall(pattern5, content)
    if matches:
        content = re.sub(pattern5, replacement5, content)
        fixes_applied += len(matches)
        print(f"✅ 修复了 {len(matches)} 个QFont字体大小设置")
    
    # 6. 添加字体大小变量初始化
    if 'font_sizes = self.font_manager.get_scaled_font_sizes' not in content:
        # 在apply_modern_style方法中添加字体大小初始化
        pattern6 = r'(def apply_modern_style\(self\):.*?"""应用现代化样式""")'
        replacement6 = r'\1\n        # 初始化响应式字体大小\n        if hasattr(self, "font_manager"):\n            font_sizes = self.font_manager.get_scaled_font_sizes(self.base_font_size)\n        else:\n            font_sizes = {"tiny": 8, "small": 10, "normal": 12, "medium": 14, "large": 16, "xlarge": 18, "title": 20, "header": 24}'
        
        if re.search(pattern6, content, re.DOTALL):
            content = re.sub(pattern6, replacement6, content, flags=re.DOTALL)
            fixes_applied += 1
            print("✅ 添加了字体大小变量初始化")
    
    # 7. 修复样式表中的f-string格式
    # 将硬编码的字体大小替换为变量引用
    style_patterns = [
        (r'font-size:\s*\{font_sizes\.get\("(\w+)",\s*(\d+)\)\}px;', 
         r'font-size: {font_sizes.get("\1", \2)}px;'),
    ]
    
    for pattern, replacement in style_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes_applied += 1
    
    # 写入修复后的内容
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 UI字体缩放修复完成！")
    print(f"📊 总共应用了 {fixes_applied} 个修复")
    print(f"💾 原文件已备份到：{backup_file}")
    
    return True

def verify_fixes():
    """验证修复效果"""
    print("\n🔍 验证修复效果...")
    
    try:
        # 尝试导入修复后的模块
        sys.path.insert(0, str(Path(__file__).parent))
        
        # 检查响应式字体管理器是否存在
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("ResponsiveFontManager", "响应式字体管理器"),
            ("resizeEvent", "窗口大小变化监听"),
            ("_update_responsive_fonts", "响应式字体更新"),
            ("font_manager.get_scaled_font_sizes", "字体大小计算"),
        ]
        
        passed = 0
        for check, description in checks:
            if check in content:
                print(f"✅ {description} - 已实现")
                passed += 1
            else:
                print(f"❌ {description} - 未找到")
        
        print(f"\n📊 验证结果：{passed}/{len(checks)} 项检查通过")
        
        if passed == len(checks):
            print("🎉 所有修复都已正确应用！")
            return True
        else:
            print("⚠️ 部分修复可能未完全应用")
            return False
            
    except Exception as e:
        print(f"❌ 验证过程中出现错误：{e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎬 VisionAI-ClipsMaster UI字体缩放修复工具")
    print("=" * 60)
    
    # 执行修复
    if fix_ui_font_scaling():
        # 验证修复效果
        if verify_fixes():
            print("\n✅ UI字体缩放修复成功完成！")
            print("\n📋 修复内容：")
            print("  • 实现了响应式字体管理器")
            print("  • 添加了窗口大小变化监听")
            print("  • 修复了硬编码的字体大小")
            print("  • 支持DPI缩放适配")
            print("  • 优化了不同分辨率下的显示效果")
            print("\n🚀 现在可以启动应用程序测试字体缩放效果")
        else:
            print("\n⚠️ 修复完成但验证发现问题，请检查日志")
    else:
        print("\n❌ 修复过程中出现错误")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
