#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理机制测试脚本

该脚本用于测试自动化清理机制的功能。
"""

import os
import time
import datetime
import sys
import shutil
from pathlib import Path

# 添加项目根目录到系统路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# 导入清理模块
from tests.golden_samples.cleanup import (
    auto_purge_temp_files,
    archive_old_reports,
    clean_cache_files,
    run_daily_cleanup,
    TMP_DIR,
    CACHE_DIR,
    REPORTS_DIR,
    ARCHIVES_DIR
)

def create_test_files():
    """创建测试文件"""
    # 确保目录存在
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # 创建临时文件
    current_time = time.time()
    one_day_ago = current_time - (25 * 3600)  # 25小时前（超过清理阈值）
    
    # 创建"旧"文件（模拟25小时前创建的文件）
    old_tmp_file = os.path.join(TMP_DIR, "old_test_file.txt")
    with open(old_tmp_file, 'w') as f:
        f.write("This is an old test file that should be deleted")
    
    # 修改文件的访问和修改时间
    os.utime(old_tmp_file, (one_day_ago, one_day_ago))
    
    # 创建"新"文件（刚刚创建的文件）
    new_tmp_file = os.path.join(TMP_DIR, "new_test_file.txt")
    with open(new_tmp_file, 'w') as f:
        f.write("This is a new test file that should NOT be deleted")
    
    # 创建测试报告文件
    old_report_file = os.path.join(REPORTS_DIR, "old_report.html")
    with open(old_report_file, 'w') as f:
        f.write("<html><body>Old report</body></html>")
    
    # 修改报告文件的时间为7天前
    week_ago = current_time - (8 * 24 * 3600)  # 8天前
    os.utime(old_report_file, (week_ago, week_ago))
    
    # 创建新报告
    new_report_file = os.path.join(REPORTS_DIR, "new_report.html")
    with open(new_report_file, 'w') as f:
        f.write("<html><body>New report</body></html>")
    
    # 创建缓存文件
    old_cache_file = os.path.join(CACHE_DIR, "old_cache.dat")
    with open(old_cache_file, 'w') as f:
        f.write("Old cache data")
    
    # 修改缓存文件的时间为31天前
    month_ago = current_time - (31 * 24 * 3600)  # 31天前
    os.utime(old_cache_file, (month_ago, month_ago))
    
    # 创建新缓存文件
    new_cache_file = os.path.join(CACHE_DIR, "new_cache.dat")
    with open(new_cache_file, 'w') as f:
        f.write("New cache data")
    
    print(f"测试文件已创建:")
    print(f"  临时文件: {old_tmp_file} (旧), {new_tmp_file} (新)")
    print(f"  报告文件: {old_report_file} (旧), {new_report_file} (新)")
    print(f"  缓存文件: {old_cache_file} (旧), {new_cache_file} (新)")

def list_directory_files(directory):
    """列出目录中的文件"""
    print(f"\n{directory} 中的文件:")
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"  {filename} (修改时间: {mod_time})")

def run_test():
    """运行清理测试"""
    print("==== 自动化清理测试开始 ====")
    
    # 1. 创建测试文件
    create_test_files()
    
    # 2. 显示清理前的文件状态
    print("\n清理前状态:")
    list_directory_files(TMP_DIR)
    list_directory_files(REPORTS_DIR)
    list_directory_files(CACHE_DIR)
    
    # 3. 运行清理
    print("\n执行清理...")
    deleted_tmp = auto_purge_temp_files()
    archived_reports = archive_old_reports()
    cleaned_cache = clean_cache_files()
    
    print(f"清理了 {len(deleted_tmp)} 个临时文件")
    print(f"归档了 {len(archived_reports)} 个报告文件")
    print(f"清理了 {len(cleaned_cache)} 个缓存文件")
    
    # 4. 显示清理后的状态
    print("\n清理后状态:")
    list_directory_files(TMP_DIR)
    list_directory_files(REPORTS_DIR)
    list_directory_files(CACHE_DIR)
    list_directory_files(ARCHIVES_DIR)
    
    print("==== 自动化清理测试完成 ====")

if __name__ == "__main__":
    run_test() 