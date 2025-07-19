#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志归档加密演示脚本

演示和测试日志归档加密功能，并提供命令行工具用于加密/解密日志文件。
"""

import os
import sys
import argparse
import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_archived_logs_directory
from src.exporters.log_lifecycle import LogLifecycleManager, get_log_lifecycle_manager
from src.exporters.log_crypto import encrypt_file, decrypt_file, encrypt_archived_logs, check_crypto_available

# 模块日志记录器
logger = get_module_logger("encrypt_archived_logs_demo")

def show_status():
    """显示日志归档加密状态"""
    # 获取日志生命周期管理器
    manager = get_log_lifecycle_manager()
    
    # 获取日志统计信息
    stats = manager.get_log_stats()
    
    # 显示状态信息
    print("\n=== 日志归档加密状态 ===")
    print(f"加密功能状态: {'启用' if manager.encryption_enabled else '禁用'}")
    print(f"加密库可用: {'是' if check_crypto_available() else '否'}")
    print(f"总日志文件数: {stats['file_count']}")
    print(f"已加密日志数: {stats['encrypted_logs']}")
    print(f"日志总大小: {stats['total_size_human']}")
    
    # 显示归档目录信息
    archive_dir = get_archived_logs_directory()
    print(f"\n归档目录: {archive_dir}")
    
    # 计算加密归档文件数量和大小
    enc_files = list(archive_dir.glob("**/*.enc"))
    enc_size = sum(f.stat().st_size for f in enc_files)
    
    print(f"加密归档文件数: {len(enc_files)}")
    print(f"加密归档大小: {_format_size(enc_size)}")
    
    return manager

def archive_and_encrypt_logs(days: int = 30):
    """归档并加密日志"""
    manager = get_log_lifecycle_manager()
    
    print(f"\n=== 归档并加密{days}天前的日志 ===")
    result = manager.archive_logs(days_to_archive=days, encrypt_archives=True)
    
    if result.get("status") == "no_files":
        print("没有找到符合条件的日志文件")
        return
    
    print(f"处理文件总数: {result.get('total_files', 0)}")
    print(f"成功处理文件: {result.get('processed_files', 0)}")
    print(f"成功加密文件: {len(result.get('encrypted_files', []))}")
    
    if result.get('errors'):
        print(f"错误数量: {len(result.get('errors', []))}")
        for error in result.get('errors', [])[:5]:  # 只显示前5个错误
            print(f"  - {error.get('file')}: {error.get('error')}")
        
        if len(result.get('errors', [])) > 5:
            print(f"  ... 还有 {len(result.get('errors', [])) - 5} 个错误未显示")

def encrypt_existing_archives(days: int = 30):
    """加密现有归档日志"""
    manager = get_log_lifecycle_manager()
    
    print(f"\n=== 加密{days}天前的现有归档日志 ===")
    result = manager.encrypt_archived_logs(days)
    
    if result.get("status") == "encryption_disabled":
        print("加密功能已禁用")
        return
    
    if result.get("status") == "encryption_unavailable":
        print("加密库不可用，无法加密")
        return
    
    if result.get("status") == "error":
        print(f"加密过程中出错: {result.get('error')}")
        return
    
    print(f"处理文件总数: {result.get('total', 0)}")
    print(f"成功加密文件: {result.get('success', 0)}")
    print(f"加密失败文件: {result.get('failed', 0)}")
    
    # 显示部分详细结果
    details = result.get("details", {})
    if details:
        print("\n部分加密结果:")
        count = 0
        for src, dest in details.items():
            if count >= 5:  # 只显示前5个结果
                break
            print(f"  - {Path(src).name} -> {dest if 'error' in dest else Path(dest).name}")
            count += 1
        
        if len(details) > 5:
            print(f"  ... 还有 {len(details) - 5} 个结果未显示")

def encrypt_single_file(file_path: Union[str, Path], delete_original: bool = False):
    """加密单个文件"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    print(f"\n=== 加密文件: {file_path} ===")
    
    if not check_crypto_available():
        print("加密库不可用，无法加密文件")
        return
    
    output_path = file_path.with_suffix(file_path.suffix + ".enc")
    
    start_time = datetime.datetime.now()
    result = encrypt_file(file_path, output_path=output_path, delete_original=delete_original)
    end_time = datetime.datetime.now()
    
    if result:
        print(f"加密成功: {result}")
        print(f"加密用时: {(end_time - start_time).total_seconds():.2f} 秒")
        
        # 显示文件大小对比
        orig_size = file_path.stat().st_size if file_path.exists() else None
        enc_size = Path(result).stat().st_size
        
        if orig_size:
            print(f"原始文件大小: {_format_size(orig_size)}")
            print(f"加密后文件大小: {_format_size(enc_size)}")
            print(f"大小比例: {enc_size/orig_size:.2f}")
    else:
        print("加密失败")

def decrypt_single_file(file_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None):
    """解密单个文件"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    print(f"\n=== 解密文件: {file_path} ===")
    
    if not check_crypto_available():
        print("加密库不可用，无法解密文件")
        return
    
    if output_path is None:
        if file_path.suffix == ".enc":
            output_path = file_path.with_suffix("")
        else:
            output_path = file_path.with_name(f"{file_path.stem}_decrypted{file_path.suffix}")
    
    start_time = datetime.datetime.now()
    result = decrypt_file(file_path, output_path=output_path)
    end_time = datetime.datetime.now()
    
    if result:
        print(f"解密成功: {result}")
        print(f"解密用时: {(end_time - start_time).total_seconds():.2f} 秒")
    else:
        print("解密失败")

def _format_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024 or unit == 'TB':
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="日志归档加密工具")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 状态命令
    status_parser = subparsers.add_parser("status", help="显示日志归档加密状态")
    
    # 归档并加密命令
    archive_parser = subparsers.add_parser("archive", help="归档并加密日志")
    archive_parser.add_argument("--days", type=int, default=30, help="处理几天前的日志（默认30天）")
    
    # 加密现有归档命令
    encrypt_archives_parser = subparsers.add_parser("encrypt-archives", help="加密现有归档日志")
    encrypt_archives_parser.add_argument("--days", type=int, default=30, help="处理几天前的日志（默认30天）")
    
    # 加密单个文件命令
    encrypt_parser = subparsers.add_parser("encrypt", help="加密单个文件")
    encrypt_parser.add_argument("file", help="要加密的文件路径")
    encrypt_parser.add_argument("--delete", action="store_true", help="加密后删除原始文件")
    
    # 解密单个文件命令
    decrypt_parser = subparsers.add_parser("decrypt", help="解密单个文件")
    decrypt_parser.add_argument("file", help="要解密的文件路径")
    decrypt_parser.add_argument("--output", help="解密后的输出文件路径")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有指定命令，显示状态
    if args.command is None:
        manager = show_status()
        return
    
    # 执行对应的命令
    if args.command == "status":
        manager = show_status()
    
    elif args.command == "archive":
        archive_and_encrypt_logs(days=args.days)
    
    elif args.command == "encrypt-archives":
        encrypt_existing_archives(days=args.days)
    
    elif args.command == "encrypt":
        encrypt_single_file(args.file, delete_original=args.delete)
    
    elif args.command == "decrypt":
        decrypt_single_file(args.file, output_path=args.output if hasattr(args, 'output') else None)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 