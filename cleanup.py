#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 清理工具

该脚本提供便捷的命令行接口，用于执行清理操作。
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 设置项目根目录
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cleanup")

# 导入清理模块
from tests.golden_samples.cleanup import (
    auto_purge_temp_files,
    archive_old_reports,
    clean_cache_files,
    run_daily_cleanup,
    emergency_cleanup,
    check_disk_space,
    get_disk_usage
)

# 导入存储验证模块
from src.validation.storage_validator import (
    scan_temp_directories,
    verify_and_cleanup,
    get_storage_report
)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 清理工具")
    parser.add_argument("--temp", action="store_true", help="清理临时文件")
    parser.add_argument("--reports", action="store_true", help="归档旧报告")
    parser.add_argument("--cache", action="store_true", help="清理缓存文件")
    parser.add_argument("--all", action="store_true", help="执行所有清理操作")
    parser.add_argument("--emergency", action="store_true", help="执行紧急清理（释放最大空间）")
    parser.add_argument("--check", action="store_true", help="检查磁盘空间使用情况")
    parser.add_argument("--report", action="store_true", help="显示存储验证报告")
    parser.add_argument("--validate", action="store_true", help="执行存储验证并清理残留文件")
    
    args = parser.parse_args()
    
    # 显示磁盘使用情况
    usage = get_disk_usage()
    print(f"当前磁盘使用率: {usage:.1f}%")
    
    # 执行操作
    if args.temp or args.all:
        deleted = auto_purge_temp_files()
        print(f"已清理 {len(deleted)} 个临时文件")
    
    if args.reports or args.all:
        archived = archive_old_reports()
        print(f"已归档 {len(archived)} 个旧报告")
    
    if args.cache or args.all:
        cleaned = clean_cache_files()
        print(f"已清理 {len(cleaned)} 个缓存文件")
    
    if args.validate or args.all:
        print("执行存储验证...")
        # 扫描所有临时目录
        found = scan_temp_directories()
        print(f"发现 {found} 个潜在的临时文件")
        
        # 验证并清理
        success = verify_and_cleanup()
        if success:
            print("所有临时文件已成功清理")
        else:
            print("警告: 部分临时文件未能清理")
    
    if args.report or args.all:
        # 显示存储验证报告
        report = get_storage_report()
        print("\n=== 存储验证报告 ===")
        print(f"总文件数: {report['total_files']}")
        print(f"已清理文件数: {report['cleaned_files']}")
        print(f"未清理文件数: {report['uncleaned_files']}")
        print(f"总大小: {report['total_size_kb']:.2f} KB")
        print(f"清理率: {report['cleanup_rate']:.2f}%")
    
    if args.all:
        print("已完成所有标准清理操作")
    
    if args.emergency:
        space_freed = emergency_cleanup()
        space_mb = space_freed / (1024 * 1024)
        print(f"紧急清理完成，释放空间: {space_mb:.2f} MB")
    
    if args.check:
        check_disk_space()
    
    # 如果没有提供任何参数，则显示帮助
    if not any([args.temp, args.reports, args.cache, args.all, args.emergency, args.check, args.report, args.validate]):
        parser.print_help()

if __name__ == "__main__":
    main() 