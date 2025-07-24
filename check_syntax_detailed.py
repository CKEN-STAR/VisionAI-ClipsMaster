#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的语法检查
"""

import ast
import sys

def check_syntax_line_by_line(filename):
    """逐行检查语法"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"检查文件: {filename}")
        print(f"总行数: {len(lines)}")
        
        # 尝试解析整个文件
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            print("✓ 整个文件语法正确")
            
            # 分析类结构
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == 'ClipGenerator':
                    print(f"\n找到ClipGenerator类:")
                    print(f"  开始行: {node.lineno}")
                    
                    # 找到类的结束行
                    class_end_line = node.lineno
                    for item in node.body:
                        if hasattr(item, 'lineno'):
                            class_end_line = max(class_end_line, item.lineno)
                            if hasattr(item, 'end_lineno') and item.end_lineno:
                                class_end_line = max(class_end_line, item.end_lineno)
                    
                    print(f"  结束行: {class_end_line}")
                    
                    # 列出所有方法
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append({
                                'name': item.name,
                                'start': item.lineno,
                                'end': item.end_lineno if hasattr(item, 'end_lineno') else 'unknown'
                            })
                    
                    print(f"  方法列表 ({len(methods)} 个):")
                    for method in methods:
                        print(f"    {method['name']}: 行 {method['start']}-{method['end']}")
                    
                    return methods
            
        except SyntaxError as e:
            print(f"✗ 语法错误: {e}")
            print(f"  错误位置: 行 {e.lineno}, 列 {e.offset}")
            print(f"  错误行内容: {lines[e.lineno-1].strip() if e.lineno <= len(lines) else 'N/A'}")
            
            # 尝试找到问题的具体位置
            print(f"\n尝试逐段检查...")
            
            # 检查到错误行之前的代码
            for check_line in range(min(e.lineno + 10, len(lines)), 0, -10):
                try:
                    partial_content = ''.join(lines[:check_line])
                    ast.parse(partial_content)
                    print(f"  行 1-{check_line}: ✓")
                except SyntaxError:
                    print(f"  行 1-{check_line}: ✗")
                    continue
                break
            
            return []
            
    except Exception as e:
        print(f"检查失败: {e}")
        return []

if __name__ == "__main__":
    methods = check_syntax_line_by_line("src/core/clip_generator.py")
    
    if methods:
        expected_methods = ['generate_clips', 'generate_from_srt', 'extract_segments', 'concatenate_segments']
        found_methods = [m['name'] for m in methods]
        
        print(f"\n期望方法检查:")
        for method in expected_methods:
            status = "✓" if method in found_methods else "✗"
            print(f"  {method}: {status}")
