#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自动化清理机制

该模块负责定期清理临时文件、过期报告和不再需要的缓存数据。
支持以下功能：
1. 临时文件清理（超过指定时间的文件将被删除）
2. 过期报告归档（旧报告移动到归档目录）
3. 定期运行的清理任务
4. 事件触发的清理（如空间不足时）
"""

import os
import sys
import time
import shutil
import logging
import datetime
import threading
import schedule
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Union

# 获取项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# 配置目录
TMP_DIR = PROJECT_ROOT / "tests" / "golden_samples" / "temp"
REPORTS_DIR = PROJECT_ROOT / "tests" / "golden_samples" / "reports"
ARCHIVES_DIR = PROJECT_ROOT / "tests" / "golden_samples" / "archives"
CACHE_DIR = PROJECT_ROOT / "tests" / "golden_samples" / "cache"

# 确保目录存在
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(ARCHIVES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# 配置日志
logger = logging.getLogger("cleanup")

# 清理配置
TEMP_FILE_MAX_AGE = 24 * 3600  # 临时文件最大保留时间（秒）
REPORT_ARCHIVE_AGE = 7 * 24 * 3600  # 报告归档时间（秒）
CACHE_MAX_AGE = 30 * 24 * 3600  # 缓存最大保留时间（秒）
MAX_DISK_USAGE_PERCENT = 80  # 磁盘使用率超过此值时触发强制清理

def auto_purge_temp_files():
    """定期清理临时文件"""
    deleted = []
    
    # 遍历临时目录
    for f in os.listdir(TMP_DIR):
        file_path = os.path.join(TMP_DIR, f)
        try:
            # 检查文件修改时间
            if time.time() - os.path.getctime(file_path) > TEMP_FILE_MAX_AGE:  # 超过24小时
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted.append(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    deleted.append(file_path)
        except Exception as e:
            logger.warning(f"清理文件 {file_path} 失败: {str(e)}")
    
    if deleted:
        logger.info(f"清理临时文件: {len(deleted)}个")
    
    return deleted

def archive_old_reports():
    """归档旧报告文件"""
    archived = []
    
    # 获取当前时间
    current_time = time.time()
    
    # 遍历报告目录
    for f in os.listdir(REPORTS_DIR):
        if not f.endswith('.html'):
            continue
            
        file_path = os.path.join(REPORTS_DIR, f)
        try:
            # 检查文件修改时间
            if current_time - os.path.getmtime(file_path) > REPORT_ARCHIVE_AGE:
                # 生成归档文件名（添加日期前缀）
                creation_date = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                date_prefix = creation_date.strftime("%Y%m%d")
                archive_name = f"{date_prefix}_{f}"
                archive_path = os.path.join(ARCHIVES_DIR, archive_name)
                
                # 移动到归档目录
                shutil.move(file_path, archive_path)
                archived.append((file_path, archive_path))
        except Exception as e:
            logger.warning(f"归档报告 {file_path} 失败: {str(e)}")
    
    if archived:
        logger.info(f"归档报告文件: {len(archived)}个")
    
    return archived

def clean_cache_files():
    """清理缓存文件"""
    cleaned = []
    
    # 遍历缓存目录
    for f in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, f)
        try:
            # 检查文件修改时间
            if time.time() - os.path.getmtime(file_path) > CACHE_MAX_AGE:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    cleaned.append(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    cleaned.append(file_path)
        except Exception as e:
            logger.warning(f"清理缓存 {file_path} 失败: {str(e)}")
    
    if cleaned:
        logger.info(f"清理缓存文件: {len(cleaned)}个")
    
    return cleaned

def get_disk_usage(path: str = None) -> float:
    """
    获取指定路径的磁盘使用率
    
    Args:
        path: 目录路径，如果为None则使用项目根目录
    
    Returns:
        float: 磁盘使用率（百分比）
    """
    if path is None:
        path = PROJECT_ROOT
    
    try:
        total, used, free = shutil.disk_usage(path)
        return (used / total) * 100
    except Exception as e:
        logger.error(f"获取磁盘使用率失败: {str(e)}")
        return 0

def emergency_cleanup():
    """
    紧急清理，当磁盘空间不足时调用
    
    Returns:
        int: 释放的空间大小（字节）
    """
    space_freed = 0
    
    # 1. 清理所有临时文件
    for f in os.listdir(TMP_DIR):
        file_path = os.path.join(TMP_DIR, f)
        try:
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                space_freed += file_size
            elif os.path.isdir(file_path):
                dir_size = get_dir_size(file_path)
                shutil.rmtree(file_path)
                space_freed += dir_size
        except Exception as e:
            logger.warning(f"紧急清理文件 {file_path} 失败: {str(e)}")
    
    # 2. 清理旧缓存文件
    for f in os.listdir(CACHE_DIR):
        file_path = os.path.join(CACHE_DIR, f)
        try:
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                space_freed += file_size
            elif os.path.isdir(file_path):
                dir_size = get_dir_size(file_path)
                shutil.rmtree(file_path)
                space_freed += dir_size
        except Exception as e:
            logger.warning(f"紧急清理缓存 {file_path} 失败: {str(e)}")
    
    # 记录清理结果
    if space_freed > 0:
        space_mb = space_freed / (1024 * 1024)
        logger.info(f"紧急清理完成，释放空间: {space_mb:.2f} MB")
    
    return space_freed

def get_dir_size(path: str) -> int:
    """
    计算目录大小
    
    Args:
        path: 目录路径
    
    Returns:
        int: 目录大小（字节）
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def check_disk_space():
    """检查磁盘空间，必要时执行紧急清理"""
    usage = get_disk_usage()
    if usage > MAX_DISK_USAGE_PERCENT:
        logger.warning(f"磁盘使用率过高 ({usage:.1f}%)，执行紧急清理")
        emergency_cleanup()

def run_daily_cleanup():
    """执行每日清理任务"""
    logger.info("开始每日清理任务")
    auto_purge_temp_files()
    archive_old_reports()
    clean_cache_files()
    check_disk_space()
    logger.info("每日清理任务完成")

def start_cleanup_scheduler():
    """启动定时清理调度器"""
    # 创建定时任务
    schedule.every().day.at("03:00").do(run_daily_cleanup)  # 每天凌晨3点执行
    
    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次定时任务
    
    # 在后台线程中运行调度器
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()
    logger.info("清理调度器已启动")
    
    return scheduler_thread

def init_cleanup_system(enable_scheduler=True):
    """
    初始化清理系统
    
    Args:
        enable_scheduler: 是否启用定时清理调度器
    """
    # 配置日志
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # 创建必要的目录
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(ARCHIVES_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 启动入口检查，清理过期临时文件
    auto_purge_temp_files()
    
    # 启动定时清理
    if enable_scheduler:
        start_cleanup_scheduler()
    
    logger.info("清理系统初始化完成")

if __name__ == "__main__":
    # 直接运行脚本时，执行一次完整清理
    init_cleanup_system(enable_scheduler=False)
    run_daily_cleanup() 