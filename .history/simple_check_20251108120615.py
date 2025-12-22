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
    ('models/qwen3-1.7b', True),
    ('models/qwen', True),
    ('models/mistral', True),
    ('models', True),
    ('output', True),
    ('logs', True)
]

for d, skip_venv in dirs:
    check_dir(d, skip_venv)

# 单独检查.venv (使用快速方法)
print("\n.venv: 扫描中...")
venv_path = Path('.venv')
if venv_path.exists():
    # 只统计大小,不列出文件
    total = 0
    count = 0
    for item in venv_path.rglob('*'):
        if item.is_file():
            try:
                total += item.stat().st_size
                count += 1
            except:
                pass
    print(f"\n.venv:")
    print(f"  文件数: {count}")
    print(f"  总大小: {total/(1024**3):.2f} GB ({total/(1024**2):.2f} MB)")
else:
    print("\n.venv: 不存在")

print("\n" + "="*80)
print("完成!")
print("="*80)

