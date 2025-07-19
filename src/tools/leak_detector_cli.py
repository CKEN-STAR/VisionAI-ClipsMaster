#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存泄漏追踪系统命令行工具

此模块提供命令行界面，用于监控和检测应用程序中的内存泄漏。
特别适用于4GB RAM无GPU的低端设备。
"""

import os
import sys
import time
import gc
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 确保可以导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入泄漏追踪器
try:
    from src.memory.leak_detector import (

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        LeakTracker,
        get_leak_tracker,
        start_leak_tracking,
        stop_leak_tracking,
        check_for_leaks,
        save_leak_report
    )
except ImportError:
    print("错误: 无法导入内存泄漏追踪器模块。请确保您位于项目根目录或正确设置了PYTHONPATH。")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("leak_detector_cli")


def setup_parser() -> argparse.ArgumentParser:
    """
    创建命令行参数解析器
    
    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(description="内存泄漏追踪工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # monitor命令 - 持续监控内存泄漏
    monitor_parser = subparsers.add_parser("monitor", help="监控内存泄漏")
    monitor_parser.add_argument("--interval", type=float, default=60.0, help="监控间隔（秒）")
    monitor_parser.add_argument("--threshold", type=float, default=2.0, help="泄漏阈值（百分比）")
    monitor_parser.add_argument("--consecutive", type=int, default=3, help="连续检测阈值")
    monitor_parser.add_argument("--duration", type=int, default=0, help="监控持续时间（秒），0表示无限")
    monitor_parser.add_argument("--log-dir", help="日志目录")
    
    # check命令 - 执行单次检查
    check_parser = subparsers.add_parser("check", help="检查内存泄漏")
    check_parser.add_argument("--threshold", type=float, default=2.0, help="泄漏阈值（百分比）")
    check_parser.add_argument("--consecutive", type=int, default=3, help="连续检测阈值")
    check_parser.add_argument("--repeat", type=int, default=1, help="重复检查次数")
    check_parser.add_argument("--interval", type=float, default=5.0, help="重复检查间隔（秒）")
    check_parser.add_argument("--log-dir", help="日志目录")
    
    # simulate命令 - 模拟泄漏场景（用于测试）
    simulate_parser = subparsers.add_parser("simulate", help="模拟内存泄漏场景")
    simulate_parser.add_argument("--size", type=int, default=10, help="每次泄漏大小（MB）")
    simulate_parser.add_argument("--count", type=int, default=10, help="泄漏对象数量")
    simulate_parser.add_argument("--interval", type=float, default=2.0, help="泄漏间隔（秒）")
    simulate_parser.add_argument("--cleanup", action="store_true", help="测试结束后清理泄漏")
    
    # reset命令 - 重置跟踪器状态
    reset_parser = subparsers.add_parser("reset", help="重置内存泄漏跟踪器")
    
    return parser


def monitor_memory(args) -> None:
    """
    持续监控内存泄漏
    
    Args:
        args: 命令行参数
    """
    # 创建跟踪器
    tracker = LeakTracker(
        leak_threshold_percent=args.threshold,
        consecutive_leaks_threshold=args.consecutive,
        log_dir=args.log_dir
    )
    
    # 开始跟踪
    logger.info(f"开始内存泄漏监控，间隔: {args.interval}秒，阈值: {args.threshold}%")
    tracker.start_tracking(interval_seconds=args.interval)
    
    try:
        if args.duration > 0:
            # 运行指定时间
            logger.info(f"监控将运行 {args.duration} 秒")
            time.sleep(args.duration)
        else:
            # 无限运行，直到用户中断
            logger.info("监控已启动，按Ctrl+C停止")
            while True:
                # 每60秒输出一次状态摘要
                time.sleep(60)
                summary = tracker.get_leak_summary()
                logger.info(f"状态: 已检测到 {summary['detected_leaks_count']} 个泄漏，"
                          f"{summary['consecutive_leaks']} 个连续泄漏")
    except KeyboardInterrupt:
        logger.info("监控被用户中断")
    finally:
        # 停止跟踪
        tracker.stop_tracking()
        
        # 如果检测到泄漏，保存最终报告
        if tracker.detected_leaks:
            report_file = tracker.save_leak_report()
            logger.info(f"泄漏报告已保存到: {report_file}")
        
        logger.info("内存泄漏监控已停止")


def check_memory(args) -> None:
    """
    执行内存泄漏检查
    
    Args:
        args: 命令行参数
    """
    # 创建跟踪器
    tracker = LeakTracker(
        leak_threshold_percent=args.threshold,
        consecutive_leaks_threshold=args.consecutive,
        log_dir=args.log_dir
    )
    
    logger.info(f"执行内存泄漏检查，重复 {args.repeat} 次，间隔 {args.interval} 秒")
    
    # 执行多次检查
    for i in range(args.repeat):
        logger.info(f"检查 {i+1}/{args.repeat}")
        
        # 强制垃圾回收
        gc.collect()
        
        # 执行检查
        leaks = tracker.check_for_leaks()
        
        if leaks:
            logger.warning(f"检测到 {len(leaks)} 个潜在泄漏")
            
            # 如果这是最后一次检查或检测到连续泄漏，保存报告
            if i == args.repeat - 1 or tracker.consecutive_leaks >= args.consecutive:
                report_file = tracker.save_leak_report()
                logger.info(f"泄漏报告已保存到: {report_file}")
        else:
            logger.info("未检测到泄漏")
        
        # 如果不是最后一次检查，等待指定间隔
        if i < args.repeat - 1:
            time.sleep(args.interval)
    
    # 打印摘要
    summary = tracker.get_leak_summary()
    if summary["detected_leaks_count"] > 0:
        logger.warning(f"检测到 {summary['detected_leaks_count']} 个潜在泄漏，"
                     f"{summary['unique_locations']} 个唯一位置")
        
        # 打印最大的几个泄漏
        if summary["top_leaks"]:
            logger.info("最大泄漏:")
            for i, leak in enumerate(summary["top_leaks"]):
                logger.info(f"  {i+1}. 位置: {leak['location']}, "
                          f"大小: {leak['size_diff']/1024/1024:.2f}MB, "
                          f"增长率: {leak['growth_rate']*100:.1f}%")
    else:
        logger.info("未检测到任何泄漏")


def simulate_leak(args) -> None:
    """
    模拟内存泄漏场景
    
    Args:
        args: 命令行参数
    """
    logger.info(f"模拟内存泄漏: {args.count} 个对象，每个 {args.size}MB，间隔 {args.interval} 秒")
    
    # 创建跟踪器并开始监控
    tracker = get_leak_tracker()
    tracker.start_tracking(interval_seconds=args.interval)
    
    try:
        # 存储泄漏对象
        leaked_objects = []
        
        # 创建指定数量的泄漏对象
        for i in range(args.count):
            logger.info(f"创建泄漏对象 {i+1}/{args.count}")
            
            # 创建指定大小的对象
            obj = bytearray(args.size * 1024 * 1024)
            leaked_objects.append(obj)
            
            # 等待指定间隔
            if i < args.count - 1:
                time.sleep(args.interval)
        
        # 检查是否检测到泄漏
        summary = tracker.get_leak_summary()
        if summary["detected_leaks_count"] > 0:
            logger.info(f"已检测到 {summary['detected_leaks_count']} 个泄漏")
            
            # 保存报告
            report_file = tracker.save_leak_report()
            logger.info(f"泄漏报告已保存到: {report_file}")
        else:
            logger.warning("未检测到泄漏，可能需要增加对象数量或调整参数")
        
        # 如果需要清理
        if args.cleanup:
            logger.info("清理泄漏对象...")
            leaked_objects.clear()
            gc.collect()
    finally:
        # 停止跟踪
        tracker.stop_tracking()


def reset_tracker(args) -> None:
    """
    重置内存泄漏跟踪器
    
    Args:
        args: 命令行参数
    """
    logger.info("重置内存泄漏跟踪器")
    
    # 获取跟踪器并重置
    tracker = get_leak_tracker()
    tracker.reset()
    
    logger.info("内存泄漏跟踪器已重置")


def main() -> None:
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # 执行相应命令
        if args.command == "monitor":
            monitor_memory(args)
        elif args.command == "check":
            check_memory(args)
        elif args.command == "simulate":
            simulate_leak(args)
        elif args.command == "reset":
            reset_tracker(args)
    except Exception as e:
        logger.error(f"执行命令时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 