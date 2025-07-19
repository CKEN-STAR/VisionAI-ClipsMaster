#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查simple_ui_fixed.py的语法错误
"""

import ast
import sys
from pathlib import Path

def check_syntax(file_path):
    """检查文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析AST
        tree = ast.parse(content, filename=file_path)
        print(f"✓ {file_path} 语法正确")
        
        # 查找类定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'SimpleScreenplayApp':
                print(f"✓ 找到类 {node.name} 在行 {node.lineno}")
                
                # 查找方法定义
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                print(f"✓ 类中有 {len(methods)} 个方法")
                
                # 查找特定方法
                target_methods = [
                    'record_user_interaction',
                    'on_performance_update', 
                    'on_response_time_update',
                    'on_ui_error_occurred',
                    'on_memory_warning',
                    'get_performance_summary'
                ]
                
                found_methods = []
                for method in methods:
                    if method.name in target_methods:
                        found_methods.append(method.name)
                        print(f"  ✓ 找到方法 {method.name} 在行 {method.lineno}")
                
                missing_methods = set(target_methods) - set(found_methods)
                if missing_methods:
                    print(f"  ❌ 缺失方法: {missing_methods}")
                else:
                    print(f"  ✓ 所有目标方法都存在")
                
                break
        else:
            print("❌ 未找到 SimpleScreenplayApp 类")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ 语法错误在 {file_path}:")
        print(f"   行 {e.lineno}: {e.text}")
        print(f"   错误: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    file_path = "simple_ui_fixed.py"
    print(f"检查文件: {file_path}")
    print("=" * 50)
    
    success = check_syntax(file_path)
    
    if success:
        print("=" * 50)
        print("✓ 语法检查通过")
    else:
        print("=" * 50)
        print("❌ 语法检查失败")
