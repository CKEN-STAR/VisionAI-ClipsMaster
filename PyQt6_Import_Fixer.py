#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6导入修复工具
修复所有文件中的QAction导入问题
"""

import os
import re

def fix_qaction_imports():
    """修复QAction导入问题"""
    print("🔧 修复PyQt6 QAction导入问题...")
    
    # 需要修复的文件列表
    files_to_fix = [
        'simple_ui_fixed.py',
        'VisionAI_ClipsMaster_Final_Functionality_Verification.py',
        'VisionAI_ClipsMaster_Perfect_Verification.py',
        'VisionAI_ClipsMaster_Precision_Fix.py',
        'main_ui_integration.py',
        'main_window.py',
        'main_window_backup.py'
    ]
    
    # 查找src目录下的main_window.py文件
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file == 'main_window.py':
                files_to_fix.append(os.path.join(root, file))
    
    fixed_files = []
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 修复模式1: from PyQt6.QtWidgets import ..., QAction, ...
            content = re.sub(
                r'from PyQt6\.QtWidgets import ([^)]*?), QAction([^)]*?)',
                r'from PyQt6.QtWidgets import \1\2',
                content
            )
            
            # 修复模式2: from PyQt6.QtWidgets import QAction, ...
            content = re.sub(
                r'from PyQt6\.QtWidgets import QAction, ([^)]*?)',
                r'from PyQt6.QtWidgets import \1',
                content
            )
            
            # 修复模式3: from PyQt6.QtWidgets import ..., QAction
            content = re.sub(
                r'from PyQt6\.QtWidgets import ([^)]*?), QAction',
                r'from PyQt6.QtWidgets import \1',
                content
            )
            
            # 修复模式4: from PyQt6.QtWidgets import QAction
            content = re.sub(
                r'from PyQt6\.QtWidgets import QAction\n',
                r'',
                content
            )
            
            # 修复多行导入中的QAction
            content = re.sub(
                r'from PyQt6\.QtWidgets import \((.*?)QAction(.*?)\)',
                lambda m: f'from PyQt6.QtWidgets import ({m.group(1)}{m.group(2)})',
                content,
                flags=re.DOTALL
            )
            
            # 确保有正确的QAction导入
            if 'QAction' in content and 'from PyQt6.QtGui import' in content:
                # 检查QtGui导入是否已包含QAction
                gui_import_pattern = r'from PyQt6\.QtGui import ([^)]*)'
                gui_match = re.search(gui_import_pattern, content)
                if gui_match and 'QAction' not in gui_match.group(1):
                    # 添加QAction到QtGui导入
                    content = re.sub(
                        gui_import_pattern,
                        r'from PyQt6.QtGui import \1, QAction',
                        content
                    )
            elif 'QAction' in content and 'from PyQt6.QtGui import' not in content:
                # 添加新的QtGui导入
                if 'from PyQt6.QtCore import' in content:
                    content = re.sub(
                        r'(from PyQt6\.QtCore import [^\n]*\n)',
                        r'\1from PyQt6.QtGui import QAction\n',
                        content
                    )
                elif 'from PyQt6.QtWidgets import' in content:
                    content = re.sub(
                        r'(from PyQt6\.QtWidgets import [^\n]*\n)',
                        r'\1from PyQt6.QtGui import QAction\n',
                        content
                    )
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_files.append(file_path)
                print(f"  ✅ 修复: {file_path}")
        
        except Exception as e:
            print(f"  ❌ 修复失败 {file_path}: {e}")
    
    print(f"\n修复完成！共修复 {len(fixed_files)} 个文件")
    return len(fixed_files)

def main():
    """主函数"""
    fixed_count = fix_qaction_imports()
    if fixed_count > 0:
        print(f"✅ 成功修复 {fixed_count} 个文件的PyQt6导入问题")
    else:
        print("ℹ️  未发现需要修复的PyQt6导入问题")

if __name__ == "__main__":
    main()
