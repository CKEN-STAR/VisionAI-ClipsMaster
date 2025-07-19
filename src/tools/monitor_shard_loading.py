#!/usr/bin/env python
"""分片加载监控工具

此工具用于监控模型分片的加载情况，识别热点分片，
分析加载模式，并提供优化建议。
"""

import os
import sys
import time
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

# 获取项目根目录并添加到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.sharding.metadata_manager import MetadataManager
from src.sharding.cache_manager import ShardManager
from src.sharding.monitor import ShardMonitor, create_shard_monitor


def format_time(seconds: float) -> str:
    """格式化时间
    
    将秒数转换为人类可读的时间格式
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 0.001:
        return f"{seconds*1000000:.2f}μs"
    elif seconds < 1:
        return f"{seconds*1000:.2f}ms"
    else:
        return f"{seconds:.4f}s"


def format_bytes(size: int) -> str:
    """格式化字节数
    
    将字节数转换为人类可读的形式
    
    Args:
        size: 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    power = 2**10
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}"


def monitor_model_loading(
    model_name: str,
    output_dir: str = "monitor_reports",
    shard_dir: Optional[str] = None,
    hot_threshold: int = 5,
    watch_mode: bool = False,
    watch_interval: float = 5.0
) -> None:
    """监控模型加载
    
    Args:
        model_name: 模型名称
        output_dir: 输出目录
        shard_dir: 分片目录
        hot_threshold: 热点分片阈值
        watch_mode: 是否启用观察模式
        watch_interval: 观察模式的更新间隔（秒）
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 确定分片目录
    if shard_dir is None:
        shard_dir = f"models/{model_name}/shards"
    
    # 生成输出文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = Path(output_dir) / f"{model_name}_monitor_{timestamp}.json"
    chart_path = Path(output_dir) / f"{model_name}_monitor_{timestamp}.png"
    
    # 创建元数据管理器和分片管理器
    metadata_manager = MetadataManager()
    
    if not metadata_manager.has_metadata(model_name):
        logger.error(f"找不到模型 {model_name} 的元数据")
        sys.exit(1)
    
    # 创建分片管理器
    shard_manager = ShardManager(
        model_name=model_name,
        metadata_manager=metadata_manager,
        shard_dir=shard_dir
    )
    
    # 创建监控器
    monitor = create_shard_monitor(
        shard_manager=shard_manager,
        save_path=str(json_path),
        hot_threshold=hot_threshold
    )
    
    logger.info(f"分片加载监控器已启动，监控模型: {model_name}")
    logger.info(f"监控数据将保存到: {json_path}")
    
    try:
        if watch_mode:
            # 观察模式：定期生成报告
            logger.info(f"已启动观察模式，更新间隔: {watch_interval}秒，按Ctrl+C停止")
            
            iteration = 0
            while True:
                iteration += 1
                
                # 生成报告
                generate_report(monitor, chart_path, iteration)
                
                # 等待下一次更新
                time.sleep(watch_interval)
        else:
            # 生成一次性报告（当用户完成操作后）
            logger.info("监控器已就绪，请使用模型...")
            logger.info("按Enter键生成报告...")
            input()
            
            generate_report(monitor, chart_path)
    
    except KeyboardInterrupt:
        logger.info("\n监控已停止")
    
    finally:
        # 保存最终监控数据
        monitor._save_monitoring_data()
        
        # 清理资源
        shard_manager.clear_cache()
        logger.info("已清理资源")


def generate_report(
    monitor: ShardMonitor, 
    chart_path: Path, 
    iteration: int = 0
) -> None:
    """生成监控报告
    
    Args:
        monitor: 分片监控器
        chart_path: 图表保存路径
        iteration: 当前迭代次数，用于观察模式
    """
    # 获取监控统计信息
    stats = monitor.get_monitor_stats()
    total_loads = stats.get("total_loads", 0)
    
    if total_loads == 0:
        logger.warning("没有监测到分片加载活动")
        return
    
    # 打印标题
    iteration_str = f"[更新 #{iteration}] " if iteration > 0 else ""
    print(f"\n===== {iteration_str}分片加载监控报告 =====")
    
    # 打印基本统计信息
    total_load_time = stats.get("total_load_time", 0)
    avg_load_time = total_load_time / total_loads if total_loads > 0 else 0
    
    print(f"总分片数: {stats.get('unique_shards', 0)}")
    print(f"总加载次数: {total_loads}")
    print(f"总加载时间: {format_time(total_load_time)}")
    print(f"平均加载时间: {format_time(avg_load_time)}")
    print(f"失败次数: {stats.get('failed_loads', 0)}")
    print(f"最大并发加载: {stats.get('max_concurrent_loads', 0)}")
    
    # 打印热点分片
    hot_shards = monitor.get_hot_shards(limit=5)
    if hot_shards:
        print("\n热点分片:")
        for shard_id, count in hot_shards:
            times = monitor.load_times.get(shard_id, [])
            avg_time = sum(times) / len(times) if times else 0
            print(f"  {shard_id}: 加载 {count} 次, 平均 {format_time(avg_time)}")
    
    # 打印加载缓慢的分片
    slow_shards = monitor.get_slow_loading_shards(limit=5)
    if slow_shards:
        print("\n加载缓慢的分片:")
        for shard_id, time_value in slow_shards:
            load_count = len(monitor.load_times.get(shard_id, []))
            print(f"  {shard_id}: 平均 {format_time(time_value)}, 加载 {load_count} 次")
    
    # 打印优化建议
    suggestions = monitor.generate_optimization_suggestions()
    if suggestions:
        print("\n优化建议:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
    
    # 生成可视化图表
    try:
        # 如果是观察模式，每次都更新图表路径
        if iteration > 0:
            path_obj = Path(str(chart_path))
            stem = path_obj.stem.split('_monitor_')[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path = path_obj.parent / f"{stem}_monitor_{timestamp}.png"
            chart_path = new_path
        
        monitor.visualize_load_pattern(str(chart_path))
        logger.info(f"图表已保存到: {chart_path}")
    
    except Exception as e:
        logger.error(f"生成图表失败: {str(e)}")


def analyze_report(report_path: str) -> None:
    """分析已保存的监控报告
    
    Args:
        report_path: 报告文件路径
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 提取统计信息
        stats = data.get("stats", {})
        hot_shards = data.get("hot_shards", [])
        slow_shards = data.get("slow_shards", [])
        suggestions = data.get("suggestions", [])
        
        # 打印报告
        print("\n===== 分片加载分析报告 =====")
        
        # 基本统计
        total_loads = stats.get("total_loads", 0)
        total_load_time = stats.get("total_load_time", 0)
        avg_load_time = total_load_time / total_loads if total_loads > 0 else 0
        
        print(f"总分片数: {stats.get('unique_shards', 0)}")
        print(f"总加载次数: {total_loads}")
        print(f"总加载时间: {format_time(total_load_time)}")
        print(f"平均加载时间: {format_time(avg_load_time)}")
        print(f"失败次数: {stats.get('failed_loads', 0)}")
        print(f"最大并发加载: {stats.get('max_concurrent_loads', 0)}")
        
        # 热点分片
        if hot_shards:
            print("\n热点分片:")
            for shard_id, count in hot_shards[:5]:
                print(f"  {shard_id}: 加载 {count} 次")
        
        # 慢加载分片
        if slow_shards:
            print("\n加载缓慢的分片:")
            for item in slow_shards[:5]:
                shard_id = item.get("shard_id", "未知")
                avg_time = item.get("avg_time", 0)
                print(f"  {shard_id}: 平均 {format_time(avg_time)}")
        
        # 优化建议
        if suggestions:
            print("\n优化建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        
        # 加载时间分析
        load_times = data.get("load_times", {})
        if load_times:
            all_times = []
            for shard_id, times in load_times.items():
                all_times.extend(times)
            
            if all_times:
                all_times.sort()
                percentile_50 = all_times[len(all_times) // 2]
                percentile_90 = all_times[int(len(all_times) * 0.9)]
                percentile_99 = all_times[int(len(all_times) * 0.99)]
                
                print("\n加载时间分析:")
                print(f"  最小值: {format_time(min(all_times))}")
                print(f"  50th 百分位: {format_time(percentile_50)}")
                print(f"  90th 百分位: {format_time(percentile_90)}")
                print(f"  99th 百分位: {format_time(percentile_99)}")
                print(f"  最大值: {format_time(max(all_times))}")
    
    except Exception as e:
        logger.error(f"分析报告失败: {str(e)}")


def list_reports(output_dir: str = "monitor_reports") -> None:
    """列出所有监控报告
    
    Args:
        output_dir: 报告目录
    """
    report_dir = Path(output_dir)
    
    if not report_dir.exists() or not report_dir.is_dir():
        logger.error(f"报告目录不存在: {output_dir}")
        return
    
    # 查找所有JSON报告文件
    reports = list(report_dir.glob("*_monitor_*.json"))
    
    if not reports:
        logger.info(f"在 {output_dir} 中没有找到报告")
        return
    
    # 按修改时间排序
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    print(f"\n在 {output_dir} 中找到 {len(reports)} 个报告:")
    for i, report in enumerate(reports):
        # 获取文件基本信息
        size = report.stat().st_size
        mtime = datetime.fromtimestamp(report.stat().st_mtime)
        
        # 提取模型名称
        model_name = report.stem.split('_monitor_')[0]
        
        # 尝试获取报告中的基本统计
        try:
            with open(report, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats = data.get("stats", {})
                total_loads = stats.get("total_loads", 0)
                unique_shards = stats.get("unique_shards", 0)
                stats_str = f"{total_loads}次加载, {unique_shards}个分片"
        except:
            stats_str = "无法读取统计"
        
        print(f"  {i+1}. {report.name}")
        print(f"     模型: {model_name}")
        print(f"     日期: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     大小: {format_bytes(size)}")
        print(f"     内容: {stats_str}")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="分片加载监控工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 监控子命令
    monitor_parser = subparsers.add_parser("monitor", help="启动分片加载监控")
    monitor_parser.add_argument("model_name", help="模型名称")
    monitor_parser.add_argument("--shard-dir", help="分片目录")
    monitor_parser.add_argument("--output-dir", default="monitor_reports", help="输出目录")
    monitor_parser.add_argument("--hot-threshold", type=int, default=5, help="热点分片阈值")
    monitor_parser.add_argument("--watch", action="store_true", help="启用观察模式")
    monitor_parser.add_argument("--interval", type=float, default=5.0, help="观察模式的更新间隔（秒）")
    
    # 分析子命令
    analyze_parser = subparsers.add_parser("analyze", help="分析已保存的监控报告")
    analyze_parser.add_argument("report_path", help="报告文件路径")
    
    # 列出子命令
    list_parser = subparsers.add_parser("list", help="列出所有监控报告")
    list_parser.add_argument("--output-dir", default="monitor_reports", help="报告目录")
    
    # 设置日志格式
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""), 
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <level>{message}</level>"
    )
    
    args = parser.parse_args()
    
    if args.command == "monitor":
        monitor_model_loading(
            model_name=args.model_name,
            output_dir=args.output_dir,
            shard_dir=args.shard_dir,
            hot_threshold=args.hot_threshold,
            watch_mode=args.watch,
            watch_interval=args.interval
        )
    elif args.command == "analyze":
        analyze_report(args.report_path)
    elif args.command == "list":
        list_reports(args.output_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 