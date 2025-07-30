#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSS兼容性清理工具
移除所有不兼容QSS的CSS属性
"""

import os
import re

def clean_css_compatibility():
    """清理CSS兼容性问题"""
    print("🔧 清理CSS兼容性问题...")
    
    # 不兼容的CSS属性模式
    incompatible_patterns = [
        r'transform\s*:[^;]*;',
        r'box-shadow\s*:[^;]*;',
        r'text-shadow\s*:[^;]*;',
        r'/* CSS property removed for QSS compatibility */]*;',
        r'transition\s*:[^;]*;',
        r'animation\s*:[^;]*;',
        r'/* CSS property removed for QSS compatibility */]*}',
        r'filter\s*:[^;]*;',
        r'backdrop-filter\s*:[^;]*;'
    ]
    
    # 查找所有可能包含CSS的文件
    target_files = []
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk('.'):
        # 跳过一些不需要处理的目录
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', '.pytest_cache', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.qss', '.css')):
                file_path = os.path.join(root, file)
                target_files.append(file_path)
    
    cleaned_files = []
    
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 移除不兼容的CSS属性
            for pattern in incompatible_patterns:
                content = re.sub(pattern, '/* CSS property removed for QSS compatibility */', content, flags=re.IGNORECASE)
            
            # 特殊处理：移除CSS字符串中的不兼容属性
            # 查找字符串中的CSS
            css_string_pattern = r'(["\'])(.*?)(transform|box-shadow|text-shadow|transition|animation|filter|backdrop-filter)\s*:[^;]*;(.*?)\1'
            
            def replace_css_in_string(match):
                quote = match.group(1)
                before = match.group(2)
                prop = match.group(3)
                after = match.group(4)
                return f'{quote}{before}/* {prop} removed for QSS compatibility */{after}{quote}'
            
            content = re.sub(css_string_pattern, replace_css_in_string, content, flags=re.IGNORECASE | re.DOTALL)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                cleaned_files.append(file_path)
                print(f"  ✅ 清理: {os.path.relpath(file_path)}")
        
        except Exception as e:
            print(f"  ⚠️  处理文件 {file_path} 时出错: {e}")
    
    print(f"\n清理完成！共处理 {len(cleaned_files)} 个文件")
    return len(cleaned_files)

def verify_css_compatibility():
    """验证CSS兼容性"""
    print("\n🔍 验证CSS兼容性...")
    
    incompatible_properties = [
        'transform:', 'box-shadow:', 'text-shadow:', 
        '-webkit-', 'transition:', 'animation:', 'filter:', 'backdrop-filter:'
    ]
    
    problematic_files = []
    
    for root, dirs, files in os.walk('.'):
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', '.pytest_cache']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.qss', '.css')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for prop in incompatible_properties:
                        if prop in content:
                            # 检查是否在注释中
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if prop in line and not ('/*' in line or '#' in line or '//' in line):
                                    if file_path not in problematic_files:
                                        problematic_files.append(os.path.relpath(file_path))
                                    break
                except:
                    continue
    
    if problematic_files:
        print(f"❌ 发现 {len(problematic_files)} 个文件仍有兼容性问题:")
        for file in problematic_files[:10]:  # 只显示前10个
            print(f"  - {file}")
        if len(problematic_files) > 10:
            print(f"  ... 还有 {len(problematic_files) - 10} 个文件")
    else:
        print("✅ 所有文件CSS兼容性检查通过")
    
    return len(problematic_files) == 0

def main():
    """主函数"""
    cleaned_count = clean_css_compatibility()
    is_compatible = verify_css_compatibility()
    
    if cleaned_count > 0:
        print(f"\n✅ 成功清理 {cleaned_count} 个文件的CSS兼容性问题")
    
    if is_compatible:
        print("🎉 CSS兼容性验证通过！")
        return 0
    else:
        print("⚠️  仍有CSS兼容性问题需要处理")
        return 1

if __name__ == "__main__":
    exit(main())
