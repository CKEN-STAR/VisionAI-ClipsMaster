#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试ClipGenerator类结构
"""

import ast
import sys

def analyze_class_structure(filename):
    """分析Python文件中的类结构"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == 'ClipGenerator':
                    print(f"找到类: {node.name}")
                    print(f"类定义开始行: {node.lineno}")
                    
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append({
                                'name': item.name,
                                'line': item.lineno,
                                'args': [arg.arg for arg in item.args.args]
                            })
                    
                    print(f"找到 {len(methods)} 个方法:")
                    for method in methods:
                        print(f"  {method['name']} (行 {method['line']}) - 参数: {method['args']}")
                    
                    return methods
        
        print("未找到ClipGenerator类")
        return []
        
    except SyntaxError as e:
        print(f"语法错误: {e}")
        print(f"错误位置: 行 {e.lineno}, 列 {e.offset}")
        return []
    except Exception as e:
        print(f"分析失败: {e}")
        return []

if __name__ == "__main__":
    methods = analyze_class_structure("src/core/clip_generator.py")
    
    # 检查期望的方法是否存在
    expected_methods = ['generate_clips', 'generate_from_srt', 'extract_segments', 'concatenate_segments']
    
    found_methods = [m['name'] for m in methods]
    
    print(f"\n期望的方法检查:")
    for method in expected_methods:
        status = "✓" if method in found_methods else "✗"
        print(f"  {method}: {status}")
