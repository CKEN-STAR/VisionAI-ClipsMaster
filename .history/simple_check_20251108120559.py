#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path

def check_dir(path_str, skip_venv=True):
    path = Path(path_str)
    if not path.exists():
        print(f"{path_str}: 不存在")
        return

    print(f"\n{path_str}: 扫描中...")

    files = []
    for item in path.rglob('*'):
        # 跳过.venv目录
        if skip_venv and '.venv' in item.parts:
            continue
        if item.is_file():
            try:
                files.append((item, item.stat().st_size))
            except:
                pass

    total_size = sum(size for _, size in files)
    file_count = len(files)

    print(f"\n{path_str}:")
    print(f"  文件数: {file_count}")
    print(f"  总大小: {total_size/(1024**3):.2f} GB ({total_size/(1024**2):.2f} MB)")

    # 列出大文件
    large_files = [(f, size) for f, size in files if size > 100*1024*1024]
    if large_files:
        print(f"  大文件 (>100MB):")
        for f, size in sorted(large_files, key=lambda x: x[1], reverse=True)[:20]:
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

