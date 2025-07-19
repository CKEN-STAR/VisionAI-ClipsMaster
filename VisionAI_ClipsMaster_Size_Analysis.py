#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 项目体积分析工具
分析项目中各个目录和文件的大小，识别优化机会
"""

import os
import json
from pathlib import Path
from collections import defaultdict
import time

def get_size(path):
    """获取文件或目录的大小（字节）"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, PermissionError):
            pass
        return total
    return 0

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"

def analyze_directory_sizes(root_path):
    """分析目录大小"""
    print(f"🔍 分析项目目录: {root_path}")
    print("=" * 80)
    
    directory_sizes = []
    file_sizes = []
    
    # 分析顶级目录
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        size = get_size(item_path)
        
        if os.path.isdir(item_path):
            directory_sizes.append((item, size, item_path))
        else:
            file_sizes.append((item, size, item_path))
    
    # 按大小排序
    directory_sizes.sort(key=lambda x: x[1], reverse=True)
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print("📁 顶级目录大小排序:")
    print("-" * 60)
    total_dir_size = 0
    for name, size, path in directory_sizes:
        print(f"{format_size(size):>10} | {name}")
        total_dir_size += size
    
    print("\n📄 顶级文件大小排序:")
    print("-" * 60)
    total_file_size = 0
    for name, size, path in file_sizes[:20]:  # 只显示前20个最大文件
        print(f"{format_size(size):>10} | {name}")
        total_file_size += size
    
    total_size = total_dir_size + total_file_size
    print(f"\n📊 总体积: {format_size(total_size)}")
    print(f"📁 目录总计: {format_size(total_dir_size)}")
    print(f"📄 文件总计: {format_size(total_file_size)}")
    
    return directory_sizes, file_sizes, total_size

def analyze_large_directories(directory_sizes, root_path, threshold_mb=50):
    """详细分析大型目录"""
    print(f"\n🔍 详细分析大于{threshold_mb}MB的目录:")
    print("=" * 80)
    
    large_dirs = []
    threshold_bytes = threshold_mb * 1024 * 1024
    
    for name, size, path in directory_sizes:
        if size > threshold_bytes:
            large_dirs.append((name, size, path))
            print(f"\n📁 {name} ({format_size(size)}):")
            print("-" * 40)
            
            # 分析子目录和文件
            subdirs = []
            subfiles = []
            
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    item_size = get_size(item_path)
                    
                    if os.path.isdir(item_path):
                        subdirs.append((item, item_size))
                    else:
                        subfiles.append((item, item_size))
                
                # 显示最大的子项目
                subdirs.sort(key=lambda x: x[1], reverse=True)
                subfiles.sort(key=lambda x: x[1], reverse=True)
                
                print("  子目录:")
                for subname, subsize in subdirs[:10]:
                    print(f"    {format_size(subsize):>10} | {subname}")
                
                print("  大文件:")
                for subname, subsize in subfiles[:10]:
                    if subsize > 1024 * 1024:  # 大于1MB的文件
                        print(f"    {format_size(subsize):>10} | {subname}")
                        
            except (OSError, PermissionError):
                print("    [无法访问]")
    
    return large_dirs

def identify_optimization_targets(root_path):
    """识别优化目标"""
    print(f"\n🎯 识别优化目标:")
    print("=" * 80)
    
    optimization_targets = []
    
    # 检查常见的可优化目录和文件
    targets = {
        "__pycache__": "Python缓存文件",
        "*.pyc": "编译的Python文件",
        "cache": "缓存目录",
        "*.log": "日志文件",
        "test_outputs": "测试输出目录",
        "snapshots": "快照目录",
        "backup*": "备份目录",
        "recovery": "恢复文件目录",
        "*.json": "大型JSON文件（可能是测试报告）",
        "docs/build": "文档构建目录",
        "examples": "示例文件目录",
        "reports": "报告目录",
        "outputs": "输出目录",
        "results": "结果目录",
        "downloads": "下载目录",
        "spacy_wheels": "SpaCy轮子文件",
        "*.whl": "Python轮子文件",
        "*.png": "图片文件",
        "*.mp4": "视频文件",
        "*.bin": "二进制文件"
    }
    
    for root, dirs, files in os.walk(root_path):
        rel_root = os.path.relpath(root, root_path)
        
        # 检查目录
        for dirname in dirs:
            dir_path = os.path.join(root, dirname)
            dir_size = get_size(dir_path)
            
            for pattern, description in targets.items():
                if "*" in pattern:
                    pattern_clean = pattern.replace("*", "")
                    if pattern_clean in dirname:
                        optimization_targets.append({
                            "type": "directory",
                            "path": dir_path,
                            "rel_path": os.path.join(rel_root, dirname),
                            "size": dir_size,
                            "description": description,
                            "pattern": pattern
                        })
                        break
                elif dirname == pattern:
                    optimization_targets.append({
                        "type": "directory",
                        "path": dir_path,
                        "rel_path": os.path.join(rel_root, dirname),
                        "size": dir_size,
                        "description": description,
                        "pattern": pattern
                    })
                    break
        
        # 检查文件
        for filename in files:
            file_path = os.path.join(root, filename)
            file_size = get_size(file_path)
            
            for pattern, description in targets.items():
                if pattern.startswith("*."):
                    ext = pattern[1:]
                    if filename.endswith(ext):
                        optimization_targets.append({
                            "type": "file",
                            "path": file_path,
                            "rel_path": os.path.join(rel_root, filename),
                            "size": file_size,
                            "description": description,
                            "pattern": pattern
                        })
                        break
    
    # 按大小排序
    optimization_targets.sort(key=lambda x: x["size"], reverse=True)
    
    # 按类型分组显示
    by_type = defaultdict(list)
    for target in optimization_targets:
        by_type[target["description"]].append(target)
    
    total_optimizable = 0
    for desc, targets_list in by_type.items():
        if targets_list:
            type_size = sum(t["size"] for t in targets_list)
            total_optimizable += type_size
            print(f"\n📂 {desc} ({len(targets_list)}个项目, {format_size(type_size)}):")
            
            # 显示最大的几个
            for target in sorted(targets_list, key=lambda x: x["size"], reverse=True)[:5]:
                print(f"  {format_size(target['size']):>10} | {target['rel_path']}")
            
            if len(targets_list) > 5:
                print(f"  ... 还有{len(targets_list) - 5}个项目")
    
    print(f"\n💾 总可优化体积: {format_size(total_optimizable)}")
    
    return optimization_targets, total_optimizable

def main():
    """主函数"""
    root_path = r"d:\zancun\VisionAI-ClipsMaster-backup"
    
    print("🎯 VisionAI-ClipsMaster 项目体积分析")
    print("=" * 80)
    print(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目路径: {root_path}")
    
    # 1. 分析目录大小
    directory_sizes, file_sizes, total_size = analyze_directory_sizes(root_path)
    
    # 2. 详细分析大型目录
    large_dirs = analyze_large_directories(directory_sizes, root_path)
    
    # 3. 识别优化目标
    optimization_targets, total_optimizable = identify_optimization_targets(root_path)
    
    # 4. 生成报告
    report = {
        "analysis_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "project_path": root_path,
        "total_size": total_size,
        "total_size_formatted": format_size(total_size),
        "directory_sizes": [(name, size, format_size(size)) for name, size, path in directory_sizes],
        "large_files": [(name, size, format_size(size)) for name, size, path in file_sizes[:20]],
        "optimization_targets": optimization_targets,
        "total_optimizable": total_optimizable,
        "total_optimizable_formatted": format_size(total_optimizable),
        "optimization_percentage": (total_optimizable / total_size * 100) if total_size > 0 else 0
    }
    
    # 保存报告
    report_file = "VisionAI_ClipsMaster_Size_Analysis_Report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细报告已保存: {report_file}")
    print(f"🎯 优化潜力: {format_size(total_optimizable)} ({report['optimization_percentage']:.1f}%)")

if __name__ == "__main__":
    main()
