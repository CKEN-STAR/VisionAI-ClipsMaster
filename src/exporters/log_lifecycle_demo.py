#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志生命周期管理演示程序

展示日志生命周期管理的主要功能，包括轮换、归档和清理。
"""

import os
import sys
import time
import random
import threading
from pathlib import Path

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_log_file_path
from src.exporters.log_lifecycle import LogLifecycleManager, get_log_lifecycle_manager
from src.exporters.log_writer import get_realtime_logger
from src.exporters.structured_logger import get_structured_logger

# 演示日志记录器
logger = get_module_logger("lifecycle_demo")

def generate_log_content(lines=100):
    """生成随机日志内容"""
    words = [
        "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL",
        "用户操作", "系统事件", "网络连接", "文件处理", "数据库操作",
        "登录", "登出", "权限验证", "数据加载", "数据保存",
        "视频处理", "音频处理", "图像处理", "文本处理", "模型推理",
        "VisionAI", "ClipsMaster", "日志", "轮换", "生命周期"
    ]
    
    content = []
    for i in range(lines):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        level = random.choice(["INFO", "DEBUG", "WARNING", "ERROR"])
        msg_words = random.randint(3, 10)
        message = " ".join(random.choice(words) for _ in range(msg_words))
        content.append(f"{timestamp} | {level.ljust(8)} | demo:{i:04d} - {message}")
    
    return "\n".join(content)

def demonstrate_log_rotation():
    """演示日志轮换功能"""
    logger.info("=== 演示日志轮换功能 ===")
    
    # 获取生命周期管理器
    manager = get_log_lifecycle_manager()
    
    # 创建演示日志文件
    demo_log = get_log_file_path("demo_lifecycle.log")
    logger.info(f"创建演示日志文件: {demo_log}")
    
    # 配置日志文件的轮换（小大小方便演示）
    from src.exporters.log_rotator import get_log_rotation_manager
    rotation_manager = get_log_rotation_manager()
    rotator = rotation_manager.add_log(
        demo_log,
        {
            "size": "10KB",         # 10KB演示用
            "backup_count": 5,      # 保留5个备份
            "check_interval": 1,    # 每秒检查一次
            "compress": True        # 启用压缩
        }
    )
    
    # 写入测试数据并观察轮换
    for i in range(1, 6):
        logger.info(f"写入批次 {i}...")
        
        # 生成并写入随机内容
        content = generate_log_content(lines=100)
        with open(demo_log, "a", encoding="utf-8") as f:
            f.write(content + "\n")
            
        # 检查文件大小
        if demo_log.exists():
            size = os.path.getsize(demo_log) / 1024
            logger.info(f"文件大小: {size:.1f}KB")
        else:
            logger.info("文件已轮换")
            
        # 统计备份文件
        backups = list(rotator.backup_dir.glob("*"))
        logger.info(f"备份文件数量: {len(backups)}")
        
        # 暂停一下，让轮换器有时间检查
        time.sleep(1.5)
    
    # 手动触发轮换
    logger.info("手动触发轮换...")
    rotator.rotate()
    
    # 检查轮换后的状态
    logger.info("轮换状态:")
    status = rotation_manager.get_status()
    for path, info in status.items():
        logger.info(f"文件: {Path(path).name}")
        logger.info(f"  大小: {info['size'] / 1024:.1f}KB")
        logger.info(f"  限制: {info['size_limit'] / 1024:.1f}KB")
        logger.info(f"  需要轮换: {info['rotation_needed']}")
        logger.info(f"  备份数量: {info['backup_count']}")

def demonstrate_log_stats():
    """演示日志统计功能"""
    logger.info("=== 演示日志统计功能 ===")
    
    # 获取生命周期管理器
    manager = get_log_lifecycle_manager()
    
    # 获取日志统计信息
    stats = manager.get_log_stats()
    
    # 显示统计信息
    logger.info("日志系统统计:")
    logger.info(f"日志目录: {stats['log_directory']}")
    logger.info(f"临时目录: {stats['temp_directory']}")
    logger.info(f"文件总数: {stats['file_count']}")
    logger.info(f"总大小: {stats['total_size_human']}")
    
    # 显示文件类型统计
    logger.info("按文件类型统计:")
    for suffix, info in stats['by_type'].items():
        logger.info(f"  {suffix}: {info['count']}个文件, {manager._format_size(info['total_size'])}")
    
    # 显示最旧和最新文件
    if stats['oldest_file']:
        logger.info(f"最旧文件: {stats['oldest_file']['path']}")
        logger.info(f"  时间: {stats['oldest_file']['time']}")
        logger.info(f"  年龄: {stats['oldest_file']['age_days']:.1f}天")
    
    if stats['newest_file']:
        logger.info(f"最新文件: {stats['newest_file']['path']}")
        logger.info(f"  时间: {stats['newest_file']['time']}")

def demonstrate_log_archiving():
    """演示日志归档功能"""
    logger.info("=== 演示日志归档功能 ===")
    
    # 获取生命周期管理器
    manager = get_log_lifecycle_manager()
    
    # 创建一些测试日志文件用于归档
    archive_dir = Path(get_log_directory()) / "archive_demo"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"创建测试文件用于归档: {archive_dir}")
    
    # 创建几个带有旧时间戳的文件
    for i in range(5):
        test_file = archive_dir / f"old_log_{i}.log"
        
        # 写入内容
        with open(test_file, "w") as f:
            f.write(generate_log_content(lines=50))
            
        # 设置为31天前的时间戳
        old_time = time.time() - (31 * 86400)
        os.utime(test_file, (old_time, old_time))
        
        logger.info(f"创建测试文件: {test_file.name} (模拟31天前)")
    
    # 执行归档（30天前的文件）
    logger.info("执行日志归档...")
    archive_file = manager.archive_logs(days_to_archive=30)
    
    if archive_file:
        logger.info(f"归档文件: {archive_file}")
        logger.info(f"大小: {archive_file.stat().st_size / 1024:.1f}KB")
    else:
        logger.warning("归档失败或无文件可归档")

def demonstrate_log_cleanup():
    """演示日志清理功能"""
    logger.info("=== 演示日志清理功能 ===")
    
    # 获取生命周期管理器
    manager = get_log_lifecycle_manager()
    
    # 创建一些测试日志文件用于清理
    cleanup_dir = Path(get_log_directory()) / "cleanup_demo"
    cleanup_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"创建测试文件用于清理: {cleanup_dir}")
    
    # 创建几个带有旧时间戳的文件
    for i in range(3):
        test_file = cleanup_dir / f"old_log_{i}.log"
        
        # 写入内容
        with open(test_file, "w") as f:
            f.write(generate_log_content(lines=20))
            
        # 设置为31天前的时间戳
        old_time = time.time() - (31 * 86400)
        os.utime(test_file, (old_time, old_time))
        
        logger.info(f"创建测试文件: {test_file.name} (模拟31天前)")
    
    # 执行清理（30天前的文件）
    logger.info("执行日志清理...")
    deleted = manager.cleanup_old_logs(30)
    logger.info(f"清理了 {deleted} 个过期日志文件")
    
    # 检查目录内容
    remaining = list(cleanup_dir.glob("*"))
    logger.info(f"剩余文件数量: {len(remaining)}")
    for file in remaining:
        logger.info(f"  {file.name}")

def main():
    """主函数"""
    logger.info("开始日志生命周期管理演示")
    
    # 初始化日志生命周期管理
    from src.exporters.log_lifecycle import init_log_lifecycle
    init_log_lifecycle()
    
    try:
        # 演示日志轮换
        demonstrate_log_rotation()
        
        # 演示日志统计功能
        demonstrate_log_stats()
        
        # 演示日志归档功能
        demonstrate_log_archiving()
        
        # 演示日志清理功能
        demonstrate_log_cleanup()
        
    finally:
        # 关闭日志生命周期管理
        from src.exporters.log_lifecycle import shutdown_log_lifecycle
        shutdown_log_lifecycle()
    
    logger.info("演示完成")

if __name__ == "__main__":
    main() 