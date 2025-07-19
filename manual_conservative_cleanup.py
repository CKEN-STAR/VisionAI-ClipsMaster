#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
手动执行保守优化清理
避免权限问题，安全地清理项目文件
"""

import os
import sys
import shutil
import time
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def safe_remove_file(file_path):
    """安全删除文件"""
    try:
        if file_path.exists():
            size = file_path.stat().st_size
            file_path.unlink()
            logger.info(f"删除文件: {file_path} ({format_size(size)})")
            return size
    except (PermissionError, OSError) as e:
        logger.warning(f"无法删除文件 {file_path}: {e}")
    return 0

def safe_remove_dir(dir_path):
    """安全删除目录"""
    try:
        if dir_path.exists() and dir_path.is_dir():
            # 先尝试删除目录内容
            total_size = 0
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except:
                        pass
            
            shutil.rmtree(dir_path, ignore_errors=True)
            if not dir_path.exists():
                logger.info(f"删除目录: {dir_path} ({format_size(total_size)})")
                return total_size
            else:
                logger.warning(f"目录删除不完整: {dir_path}")
                return 0
    except Exception as e:
        logger.warning(f"无法删除目录 {dir_path}: {e}")
    return 0

def clean_cache_files():
    """清理缓存文件"""
    logger.info("🧹 清理Python缓存文件...")
    total_removed = 0
    
    # 清理 __pycache__ 目录
    for cache_dir in Path(".").rglob("__pycache__"):
        if cache_dir.is_dir():
            total_removed += safe_remove_dir(cache_dir)
    
    # 清理 .pyc 文件
    for pyc_file in Path(".").rglob("*.pyc"):
        total_removed += safe_remove_file(pyc_file)
    
    # 清理 .pyo 文件
    for pyo_file in Path(".").rglob("*.pyo"):
        total_removed += safe_remove_file(pyo_file)
    
    logger.info(f"缓存清理完成: {format_size(total_removed)}")
    return total_removed

def clean_log_files():
    """清理日志文件"""
    logger.info("📝 清理旧日志文件...")
    total_removed = 0
    
    # 清理30天前的日志
    cutoff_time = time.time() - (30 * 24 * 3600)
    
    log_patterns = ["*.log", "*.log.*"]
    for pattern in log_patterns:
        for log_file in Path(".").rglob(pattern):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    total_removed += safe_remove_file(log_file)
            except:
                continue
    
    logger.info(f"日志清理完成: {format_size(total_removed)}")
    return total_removed

def clean_backup_files():
    """清理备份文件"""
    logger.info("🗂️ 清理备份文件...")
    total_removed = 0
    
    backup_patterns = ["*.bak", "*.backup", "*~", "*.tmp", "*.temp"]
    for pattern in backup_patterns:
        for backup_file in Path(".").rglob(pattern):
            total_removed += safe_remove_file(backup_file)
    
    logger.info(f"备份文件清理完成: {format_size(total_removed)}")
    return total_removed

def clean_build_artifacts():
    """清理构建产物"""
    logger.info("🔨 清理构建产物...")
    total_removed = 0
    
    build_dirs = ["build", "dist", ".pytest_cache", ".coverage", "htmlcov"]
    for build_dir in build_dirs:
        dir_path = Path(build_dir)
        total_removed += safe_remove_dir(dir_path)
    
    # 清理egg-info目录
    for egg_info in Path(".").rglob("*.egg-info"):
        if egg_info.is_dir():
            total_removed += safe_remove_dir(egg_info)
    
    logger.info(f"构建产物清理完成: {format_size(total_removed)}")
    return total_removed

def clean_temp_files():
    """清理临时文件"""
    logger.info("🗑️ 清理临时文件...")
    total_removed = 0
    
    # 清理系统临时文件
    temp_patterns = ["*.tmp", "*.temp", "Thumbs.db", ".DS_Store"]
    for pattern in temp_patterns:
        for temp_file in Path(".").rglob(pattern):
            total_removed += safe_remove_file(temp_file)
    
    logger.info(f"临时文件清理完成: {format_size(total_removed)}")
    return total_removed

def clean_editor_files():
    """清理编辑器临时文件"""
    logger.info("✏️ 清理编辑器文件...")
    total_removed = 0
    
    editor_patterns = [
        "*.swp", "*.swo", "*~",  # Vim
        ".vscode/settings.json.bak",  # VSCode
        "*.orig",  # Git merge
    ]
    
    for pattern in editor_patterns:
        for editor_file in Path(".").rglob(pattern):
            total_removed += safe_remove_file(editor_file)
    
    logger.info(f"编辑器文件清理完成: {format_size(total_removed)}")
    return total_removed

def main():
    """主清理函数"""
    logger.info("🚀 开始保守优化清理...")
    
    start_time = time.time()
    total_saved = 0
    
    # 执行各项清理
    cleaners = [
        ("缓存文件", clean_cache_files),
        ("日志文件", clean_log_files),
        ("备份文件", clean_backup_files),
        ("构建产物", clean_build_artifacts),
        ("临时文件", clean_temp_files),
        ("编辑器文件", clean_editor_files),
    ]
    
    for name, cleaner_func in cleaners:
        try:
            saved = cleaner_func()
            total_saved += saved
            logger.info(f"✅ {name}清理完成")
        except Exception as e:
            logger.error(f"❌ {name}清理失败: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("=" * 50)
    logger.info(f"🎉 保守优化清理完成!")
    logger.info(f"📊 总节省空间: {format_size(total_saved)}")
    logger.info(f"⏱️ 耗时: {duration:.1f}秒")
    logger.info("=" * 50)
    
    return total_saved

if __name__ == "__main__":
    main()
