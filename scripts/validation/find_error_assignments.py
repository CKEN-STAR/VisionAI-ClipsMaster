#!/usr/bin/env python3
"""
查找PowerShell文件中的$error变量赋值问题
"""

import os
import re
from pathlib import Path

def find_error_assignments():
    """查找所有包含$error变量赋值的PowerShell文件"""
    project_root = Path(".")
    ps_files = list(project_root.glob("*.ps1"))
    
    print(f"🔍 检查 {len(ps_files)} 个PowerShell文件...")
    
    error_files = []
    
    for ps_file in ps_files:
        try:
            with open(ps_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(ps_file, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(ps_file, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        # 查找$error变量的赋值
        patterns = [
            r'\$error\s*=',  # $error = something
            r'\$error\s*\+=',  # $error += something
            r'\$error\s*\[.*\]\s*=',  # $error[index] = something
            r'\$error\..*\s*=',  # $error.property = something
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 排除注释行
                    if not line.strip().startswith('#'):
                        error_files.append({
                            'file': ps_file.name,
                            'line': i,
                            'content': line.strip(),
                            'pattern': pattern
                        })
    
    return error_files

def main():
    """主函数"""
    print("🚀 查找PowerShell $error变量赋值问题")
    print("=" * 50)
    
    error_assignments = find_error_assignments()
    
    if not error_assignments:
        print("✅ 未发现$error变量赋值问题")
        return
    
    print(f"❌ 发现 {len(error_assignments)} 个$error变量赋值问题:")
    print()
    
    current_file = None
    for error in error_assignments:
        if error['file'] != current_file:
            current_file = error['file']
            print(f"📁 文件: {current_file}")
        
        print(f"  第{error['line']}行: {error['content']}")
        print(f"  匹配模式: {error['pattern']}")
        print()

if __name__ == "__main__":
    main()
