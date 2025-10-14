#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI字体修改回退工具

此脚本将撤销所有字体缩放相关的修改，恢复到原始状态
"""

import sys
import os
from pathlib import Path
import re

def revert_font_changes():
    """回退字体修改"""
    
    print("🔄 开始回退VisionAI-ClipsMaster UI字体修改...")
    
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
    
    # 备份当前文件
    backup_file = ui_file.with_suffix('.py.font_backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 已创建备份文件：{backup_file}")
    
    # 回退修改
    reverts_applied = 0
    
    # 1. 移除ResponsiveFontManager类定义
    pattern1 = r'class ResponsiveFontManager:.*?(?=class|\Z)'
    if re.search(pattern1, content, re.DOTALL):
        content = re.sub(pattern1, '', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了ResponsiveFontManager类")
    
    # 2. 移除font_manager初始化
    pattern2 = r'\s*# 初始化响应式字体管理器\s*\n\s*self\.font_manager = ResponsiveFontManager\(\)\s*\n'
    if re.search(pattern2, content):
        content = re.sub(pattern2, '\n', content)
        reverts_applied += 1
        print("✅ 移除了font_manager初始化")
    
    # 3. 移除resizeEvent方法
    pattern3 = r'def resizeEvent\(self, event\):.*?(?=def|\Z)'
    if re.search(pattern3, content, re.DOTALL):
        content = re.sub(pattern3, '', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了resizeEvent方法")
    
    # 4. 移除_update_responsive_fonts方法
    pattern4 = r'def _update_responsive_fonts\(self\):.*?(?=def|\Z)'
    if re.search(pattern4, content, re.DOTALL):
        content = re.sub(pattern4, '', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了_update_responsive_fonts方法")
    
    # 5. 移除_update_component_fonts方法
    pattern5 = r'def _update_component_fonts\(self, font_sizes\):.*?(?=def|\Z)'
    if re.search(pattern5, content, re.DOTALL):
        content = re.sub(pattern5, '', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了_update_component_fonts方法")
    
    # 6. 移除font_manager相关的更新代码
    pattern6 = r'\s*# 更新字体管理器.*?\n.*?self\.font_manager\.dpi_scale = dpi_scale\s*\n'
    if re.search(pattern6, content, re.DOTALL):
        content = re.sub(pattern6, '\n', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了font_manager更新代码")
    
    # 7. 恢复原始字体大小 - 将增大的字体恢复到原始值
    font_revert_mapping = {
        '28px': '24px',   # header++ -> header
        '26px': '22px',   # header+ -> header
        '24px': '20px',   # header -> title
        '20px': '18px',   # title -> xlarge
        '18px': '16px',   # xlarge -> large
        '17px': '15px',   # large+ -> medium+
        '16px': '14px',   # large -> medium
        '15px': '13px',   # medium+ -> normal+
        '14px': '12px',   # medium -> normal
        '13px': '11px',   # normal+ -> small
        '12px': '10px',   # normal -> small
        '10px': '8px',    # small -> tiny
    }
    
    for new_size, old_size in font_revert_mapping.items():
        pattern = rf'font-size:\s*{re.escape(new_size)}'
        replacement = f'font-size: {old_size}'
        
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            reverts_applied += matches
            print(f"✅ 将 {new_size} 恢复为 {old_size} ({matches} 处)")
    
    # 8. 移除font_manager相关的条件判断
    pattern8 = r'self\.font_manager\.base_font_size if hasattr\(self, "font_manager"\) else (\d+)'
    replacement8 = r'\1'
    matches = len(re.findall(pattern8, content))
    if matches > 0:
        content = re.sub(pattern8, replacement8, content)
        reverts_applied += matches
        print(f"✅ 移除了 {matches} 个font_manager条件判断")
    
    # 9. 移除font_sizes初始化代码块
    pattern9 = r'\s*# 初始化响应式字体大小.*?}\s*\n'
    if re.search(pattern9, content, re.DOTALL):
        content = re.sub(pattern9, '\n', content, flags=re.DOTALL)
        reverts_applied += 1
        print("✅ 移除了font_sizes初始化代码")
    
    # 10. 恢复QFont.setPointSize调用
    pattern10 = r'font\.setPointSize\((\d+)\)'
    def restore_point_size(match):
        size = int(match.group(1))
        original_size = max(8, size - 2)  # 减少2pt，恢复原始大小
        return f'font.setPointSize({original_size})'
    
    matches = len(re.findall(pattern10, content))
    if matches > 0:
        content = re.sub(pattern10, restore_point_size, content)
        reverts_applied += matches
        print(f"✅ 恢复了 {matches} 个QFont字体大小设置")
    
    # 写入回退后的内容
    with open(ui_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"🎉 UI字体修改回退完成！")
    print(f"📊 总共回退了 {reverts_applied} 个修改")
    print(f"💾 原文件已备份到：{backup_file}")
    
    return True

def verify_revert():
    """验证回退效果"""
    print("\n🔍 验证回退效果...")
    
    try:
        ui_file = Path("simple_ui_fixed.py")
        with open(ui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("ResponsiveFontManager", "响应式字体管理器", False),
            ("resizeEvent", "窗口大小变化监听", False),
            ("_update_responsive_fonts", "响应式字体更新", False),
            ("font_manager.get_scaled_font_sizes", "字体大小计算", False),
            ("font-size: 20px", "标题字体大小", True),
            ("font-size: 14px", "正常字体大小", True),
        ]
        
        passed = 0
        for check, description, should_exist in checks:
            exists = check in content
            if exists == should_exist:
                status = "✅" if should_exist else "✅"
                print(f"{status} {description} - {'存在' if should_exist else '已移除'}")
                passed += 1
            else:
                status = "❌"
                expected = "应存在" if should_exist else "应移除"
                actual = "存在" if exists else "不存在"
                print(f"{status} {description} - {expected}但{actual}")
        
        print(f"\n📊 验证结果：{passed}/{len(checks)} 项检查通过")
        
        if passed == len(checks):
            print("🎉 所有回退都已正确应用！")
            return True
        else:
            print("⚠️ 部分回退可能未完全应用")
            return False
            
    except Exception as e:
        print(f"❌ 验证过程中出现错误：{e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 VisionAI-ClipsMaster UI字体修改回退工具")
    print("=" * 60)
    
    # 执行回退
    if revert_font_changes():
        # 验证回退效果
        if verify_revert():
            print("\n✅ UI字体修改回退成功完成！")
            print("\n📋 回退内容：")
            print("  • 移除了响应式字体管理器")
            print("  • 移除了窗口大小变化监听")
            print("  • 恢复了原始字体大小设置")
            print("  • 移除了DPI缩放相关代码")
            print("  • 恢复了硬编码字体大小值")
            print("\n🚀 现在可以启动应用程序测试原始字体效果")
        else:
            print("\n⚠️ 回退完成但验证发现问题，请检查日志")
    else:
        print("\n❌ 回退过程中出现错误")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
