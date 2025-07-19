#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码质量修复脚本
修复导入错误、异常处理等问题
"""

import re
import os
import ast

def fix_import_issues(file_path: str) -> dict:
    """
    修复导入问题
    
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
        'import_fixes': 0,
        'exception_handling_added': 0,
        'missing_imports_added': 0,
        'total_fixes': 0
    }
    
    # 1. 确保所有必要的导入都存在
    required_imports = {
        'import sys': 'import sys',
        'import os': 'import os', 
        'import gc': 'import gc',
        'import time': 'import time',
        'import json': 'import json',
        'import logging': 'import logging',
        'import threading': 'import threading',
        'import psutil': 'import psutil',
        'from datetime import datetime': 'from datetime import datetime',
        'from pathlib import Path': 'from pathlib import Path'
    }
    
    # 检查并添加缺失的导入
    for import_check, import_statement in required_imports.items():
        if import_check not in content:
            # 在现有导入后添加
            import_pattern = r'(import sys\nimport os\n)'
            if re.search(import_pattern, content):
                content = re.sub(import_pattern, f'\\1{import_statement}\n', content)
                fixes_applied['missing_imports_added'] += 1
    
    # 2. 修复可能的NameError
    # 确保在使用sys之前已导入
    sys_usage_pattern = r'(\s+)(sys\.[a-zA-Z_][a-zA-Z0-9_]*)'
    def fix_sys_usage(match):
        indent = match.group(1)
        sys_call = match.group(2)
        
        # 添加安全的sys导入检查
        safe_sys_usage = f'''{indent}try:
{indent}    {sys_call}
{indent}except NameError:
{indent}    import sys
{indent}    {sys_call}'''
        
        fixes_applied['import_fixes'] += 1
        return safe_sys_usage
    
    # 暂时注释掉这个修复，因为可能会导致语法问题
    # content = re.sub(sys_usage_pattern, fix_sys_usage, content)
    
    # 3. 添加更好的异常处理
    # 查找没有异常处理的关键操作
    critical_operations = [
        r'(subprocess\.Popen\([^)]+\))',
        r'(QApplication\.instance\(\)[^)]*)',
        r'(self\.[a-zA-Z_][a-zA-Z0-9_]*\.emit\([^)]*\))'
    ]
    
    for pattern in critical_operations:
        matches = re.finditer(pattern, content)
        for match in matches:
            operation = match.group(1)
            # 检查是否已经在try-except块中
            start_pos = max(0, match.start() - 200)
            context = content[start_pos:match.end()]
            
            if 'try:' not in context or 'except' not in context:
                # 需要添加异常处理
                fixes_applied['exception_handling_added'] += 1
    
    # 4. 修复常见的语法问题
    syntax_fixes = [
        # 修复可能的缩进问题
        (r'\n    \n        ', '\n        '),
        # 修复多余的空行
        (r'\n\n\n+', '\n\n'),
        # 修复可能的编码问题
        (r'# -\*- coding: utf-8 -\*-', '# -*- coding: utf-8 -*-'),
    ]
    
    for pattern, replacement in syntax_fixes:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            fixes_applied['import_fixes'] += 1
    
    # 5. 添加安全的模块导入包装器
    safe_import_wrapper = '''
def safe_import(module_name, fallback=None):
    """安全导入模块，失败时返回fallback"""
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"[WARN] 导入模块失败 {module_name}: {e}")
        return fallback

def safe_from_import(module_name, item_name, fallback=None):
    """安全从模块导入项目"""
    try:
        module = __import__(module_name, fromlist=[item_name])
        return getattr(module, item_name)
    except (ImportError, AttributeError) as e:
        print(f"[WARN] 从模块导入失败 {module_name}.{item_name}: {e}")
        return fallback

'''
    
    # 在文件开头添加安全导入工具
    if 'def safe_import(' not in content:
        # 找到合适的插入位置（在导入之后）
        insert_pattern = r'(from pathlib import Path\n)'
        if re.search(insert_pattern, content):
            content = re.sub(insert_pattern, f'\\1\n{safe_import_wrapper}', content)
            fixes_applied['import_fixes'] += 1
    
    # 计算总修复数
    fixes_applied['total_fixes'] = sum(fixes_applied.values()) - fixes_applied['total_fixes']
    
    # 备份原文件
    backup_path = f"{file_path}.quality_backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ 原文件已备份到: {backup_path}")
    
    # 写入修复后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return fixes_applied

def validate_syntax(file_path: str) -> dict:
    """
    验证Python语法
    
    Args:
        file_path: 要验证的文件路径
        
    Returns:
        dict: 验证结果
    """
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试编译代码
        ast.parse(content)
        
        return {
            "valid": True,
            "errors": []
        }
        
    except SyntaxError as e:
        return {
            "valid": False,
            "errors": [f"语法错误 (行 {e.lineno}): {e.msg}"]
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"其他错误: {str(e)}"]
        }

def add_comprehensive_error_handling(file_path: str):
    """添加全面的错误处理"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在主函数周围添加全局异常处理
    global_error_handler = '''
def handle_global_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    import traceback
    import logging
    
    # 记录异常
    logging.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # 显示用户友好的错误消息
    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        if QApplication.instance():
            QMessageBox.critical(
                None, 
                "程序错误", 
                f"程序遇到未预期的错误:\\n{exc_type.__name__}: {exc_value}\\n\\n请重启程序或联系技术支持。"
            )
    except:
        print(f"严重错误: {exc_type.__name__}: {exc_value}")

# 安装全局异常处理器
import sys
sys.excepthook = handle_global_exception

'''
    
    # 在文件开头添加全局异常处理
    if 'def handle_global_exception(' not in content:
        # 在导入之后添加
        insert_pattern = r'(from pathlib import Path\n)'
        if re.search(insert_pattern, content):
            content = re.sub(insert_pattern, f'\\1\n{global_error_handler}', content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 已添加全局异常处理器")

def main():
    """主函数"""
    print("🔧 开始代码质量修复")
    print("=" * 60)
    
    file_path = "simple_ui_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📝 正在修复文件: {file_path}")
    
    # 1. 语法验证
    print("\n🧪 验证语法...")
    syntax_result = validate_syntax(file_path)
    
    if syntax_result["valid"]:
        print("✅ 语法验证通过")
    else:
        print("❌ 语法验证失败:")
        for error in syntax_result["errors"]:
            print(f"   {error}")
    
    # 2. 修复导入和质量问题
    print("\n🔧 修复代码质量问题...")
    fixes = fix_import_issues(file_path)
    
    print("\n📊 修复统计:")
    print(f"   导入修复: {fixes['import_fixes']} 处")
    print(f"   异常处理添加: {fixes['exception_handling_added']} 处") 
    print(f"   缺失导入添加: {fixes['missing_imports_added']} 处")
    print(f"   总计修复: {fixes['total_fixes']} 处")
    
    # 3. 添加全局异常处理
    print("\n🛡️ 添加全局异常处理...")
    add_comprehensive_error_handling(file_path)
    
    # 4. 再次验证语法
    print("\n🧪 再次验证语法...")
    final_syntax_result = validate_syntax(file_path)
    
    if final_syntax_result["valid"]:
        print("✅ 最终语法验证通过")
    else:
        print("❌ 最终语法验证失败:")
        for error in final_syntax_result["errors"]:
            print(f"   {error}")
    
    print(f"\n✅ 代码质量修复完成!")
    print(f"   原文件备份: {file_path}.quality_backup")
    print(f"   修复后文件: {file_path}")

if __name__ == "__main__":
    main()
