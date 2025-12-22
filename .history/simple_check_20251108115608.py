#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path

def check_dir(path_str):
    path = Path(path_str)
    if not path.exists():
        print(f"{path_str}: 不存在")
        return
    
    files = list(path.rglob('*'))
    total_size = sum(f.stat().st_size for f in files if f.is_file())
    file_count = sum(1 for f in files if f.is_file())
    
    print(f"\n{path_str}:")
    print(f"  文件数: {file_count}")
    print(f"  总大小: {total_size/(1024**3):.2f} GB ({total_size/(1024**2):.2f} MB)")
    
    # 列出大文件
    large_files = [(f, f.stat().st_size) for f in files if f.is_file() and f.stat().st_size > 100*1024*1024]
    if large_files:
        print(f"  大文件 (>100MB):")
        for f, size in sorted(large_files, key=lambda x: x[1], reverse=True):
            print(f"    {size/(1024**3):.2f} GB - {f.relative_to(path)}")

print("="*80)
print("VisionAI-ClipsMaster 磁盘空间快速检查")
print("="*80)

# 检查关键目录
dirs = [
    'models/qwen3-1.7b',
    'models/qwen',
    'models/mistral',
    'models',
    '.venv',
    'output',
    'logs'
]

for d in dirs:
    check_dir(d)

print("\n" + "="*80)
print("完成!")
print("="*80)

