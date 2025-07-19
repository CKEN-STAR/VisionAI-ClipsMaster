#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本元数据提取示例

演示如何使用版本检测器获取项目文件的版本信息，
支持多种格式：剪映、Premiere、Final Cut、DaVinci Resolve等
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.exporters.version_detector import (
    detect_version,
    detect_jianying_version,
    detect_jianying_version_from_string
)


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳为可读时间
    
    Args:
        timestamp: UNIX时间戳
        
    Returns:
        str: 格式化的日期时间
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def print_version_info(info: Dict[str, Any]) -> None:
    """
    打印版本信息
    
    Args:
        info: 版本信息字典
    """
    print("\n" + "=" * 50)
    print(f"文件路径: {info['file_path']}")
    print(f"格式类型: {info['display_name']} ({info['format_type']})")
    print(f"版本号: {info['version']}")
    print(f"文件大小: {info['file_size']} 字节")
    print(f"最后修改: {format_timestamp(info['last_modified'])}")
    print("=" * 50 + "\n")


def process_directory(directory: str) -> List[Dict[str, Any]]:
    """
    处理目录中的所有文件
    
    Args:
        directory: 目录路径
        
    Returns:
        List[Dict[str, Any]]: 版本信息列表
    """
    results = []
    
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"错误: {directory} 不是有效的目录")
        return results
    
    print(f"扫描目录: {directory}")
    
    # 支持的文件扩展名
    supported_extensions = ['.xml', '.fcpxml', '.json', '.txt']
    
    for file_path in dir_path.glob('**/*'):
        if file_path.is_file() and (file_path.suffix.lower() in supported_extensions or 'jianying' in file_path.name.lower()):
            print(f"处理文件: {file_path.name}")
            info = detect_version(str(file_path))
            
            if info['version'] != 'unknown':
                results.append(info)
                print_version_info(info)
    
    return results


def process_file(file_path: str) -> Dict[str, Any]:
    """
    处理单个文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict[str, Any]: 版本信息
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return {}
    
    info = detect_version(file_path)
    print_version_info(info)
    return info


def process_content(content: str) -> str:
    """
    从内容字符串中提取版本
    
    Args:
        content: 内容字符串
        
    Returns:
        str: 版本号
    """
    version = detect_jianying_version_from_string(content)
    print(f"\n从内容中提取的版本: {version}\n")
    return version


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本元数据提取工具")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--file', '-f', help='要分析的文件路径')
    group.add_argument('--dir', '-d', help='要扫描的目录路径')
    group.add_argument('--content', '-c', help='要分析的内容字符串')
    
    args = parser.parse_args()
    
    if args.file:
        process_file(args.file)
    elif args.dir:
        results = process_directory(args.dir)
        print(f"\n共发现 {len(results)} 个文件包含有效版本信息")
    elif args.content:
        process_content(args.content)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 