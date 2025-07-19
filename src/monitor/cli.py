#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据分析命令行工具

为VisionAI-ClipsMaster提供历史数据分析的命令行界面。
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import tabulate

# 确保能够导入src包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 导入历史分析模块
try:
    from src.monitor.history_analyzer import (
        get_history_analyzer, 
        analyze_memory_trends,
        analyze_cache_performance,
        analyze_oom_risks,
        generate_daily_report,
        generate_weekly_report,
        get_latest_reports,
        start_collection,
        stop_collection,
        start_auto_reports,
        stop_auto_reports
    )
except ImportError:
    # 直接从当前目录导入
    from history_analyzer import (
        get_history_analyzer, 
        analyze_memory_trends,
        analyze_cache_performance,
        analyze_oom_risks,
        generate_daily_report,
        generate_weekly_report,
        get_latest_reports,
        start_collection,
        stop_collection,
        start_auto_reports,
        stop_auto_reports
    )

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("history_cli")


def format_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
    """格式化表格数据
    
    Args:
        data: 表格数据
        columns: 需要显示的列
        
    Returns:
        格式化后的表格字符串
    """
    if not data:
        return "无数据"
    
    if columns:
        # 只保留指定列
        filtered_data = []
        for item in data:
            filtered_item = {col: item.get(col, "") for col in columns}
            filtered_data.append(filtered_item)
        data = filtered_data
    
    # 表头
    headers = data[0].keys()
    
    # 表格数据
    rows = [list(item.values()) for item in data]
    
    # 格式化为表格
    return tabulate.tabulate(rows, headers=headers, tablefmt="grid")


def print_json(data: Dict[str, Any]):
    """打印JSON数据
    
    Args:
        data: JSON数据
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))


def command_collect(args):
    """处理数据采集命令
    
    Args:
        args: 命令行参数
    """
    if args.stop:
        print("停止数据采集...")
        stop_collection()
        return
    
    print(f"启动数据采集，间隔: {args.interval}秒")
    start_collection(args.interval)
    
    if args.daemon:
        print("在后台运行，按Ctrl+C停止")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n接收到中断信号，停止数据采集...")
            stop_collection()


def command_report(args):
    """处理报告命令
    
    Args:
        args: 命令行参数
    """
    if args.list:
        # 列出最新报告
        reports = get_latest_reports(args.type, args.limit)
        
        if not reports:
            print("没有找到报告")
            return
        
        print(f"找到 {len(reports)} 份报告:")
        
        # 格式化报告列表
        table_data = []
        for i, report in enumerate(reports, 1):
            report_type = "日报" if "daily" in report.get('file_name', '') else "周报"
            date = report.get('datetime', '未知时间').split('T')[0]
            
            table_data.append({
                "序号": i,
                "类型": report_type,
                "日期": date,
                "文件路径": report.get('file_path', '')
            })
        
        print(format_table(table_data))
        return
    
    if args.daily:
        # 生成每日报告
        print("生成每日报告...")
        report = generate_daily_report()
        analyzer = get_history_analyzer()
        print(f"报告已保存至: {analyzer.reports_dir}")
        
        if args.show:
            print("\n报告内容:")
            print_json(report)
        
        return
    
    if args.weekly:
        # 生成每周报告
        print("生成每周报告...")
        report = generate_weekly_report()
        analyzer = get_history_analyzer()
        print(f"报告已保存至: {analyzer.reports_dir}")
        
        if args.show:
            print("\n报告内容:")
            print_json(report)
        
        return
    
    if args.auto:
        if args.stop_auto:
            # 停止自动报告
            print("停止自动报告生成...")
            stop_auto_reports()
        else:
            # 启动自动报告
            print(f"启动自动报告生成，日报间隔: {args.daily_interval}秒，周报间隔: {args.weekly_interval}秒")
            start_auto_reports(args.daily_interval, args.weekly_interval)
            
            if args.daemon:
                print("在后台运行，按Ctrl+C停止")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n接收到中断信号，停止自动报告生成...")
                    stop_auto_reports()
        
        return
    
    # 没有指定具体命令，显示帮助
    print("请指定具体的报告命令")
    print("使用 --daily 生成每日报告")
    print("使用 --weekly 生成每周报告")
    print("使用 --list 列出已有报告")
    print("使用 --auto 启动自动报告生成")


def command_analyze(args):
    """处理分析命令
    
    Args:
        args: 命令行参数
    """
    results = {}
    
    if args.memory or args.all:
        # 分析内存趋势
        print(f"分析最近{args.days}天的内存趋势...")
        memory_results = analyze_memory_trends(args.days)
        results["memory"] = memory_results
        
        if not args.all:
            print_json(memory_results)
    
    if args.cache or args.all:
        # 分析缓存性能
        print(f"分析最近{args.days}天的缓存性能...")
        cache_results = analyze_cache_performance(args.days)
        results["cache"] = cache_results
        
        if not args.all:
            print_json(cache_results)
    
    if args.oom or args.all:
        # 分析OOM风险
        print(f"分析最近{args.days}天的OOM风险...")
        oom_results = analyze_oom_risks(args.days)
        results["oom"] = oom_results
        
        if not args.all:
            print_json(oom_results)
    
    if args.all:
        # 输出所有分析结果
        print_json(results)
    
    if args.output:
        # 保存到文件
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"分析结果已保存至: {args.output}")


def command_dashboard(args):
    """启动可视化仪表盘
    
    Args:
        args: 命令行参数
    """
    try:
        from src.ui.history_dashboard import run_dashboard
        print("启动历史数据可视化仪表盘...")
        run_dashboard()
    except ImportError:
        print("错误: 缺少PyQt6或pyqtgraph，无法启动仪表盘")
        print("请安装所需依赖: pip install PyQt6 pyqtgraph")
    except Exception as e:
        print(f"启动仪表盘失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 历史数据分析工具")
    subparsers = parser.add_subparsers(title="命令", dest="command")
    
    # 收集命令
    collect_parser = subparsers.add_parser("collect", help="数据采集")
    collect_parser.add_argument("--interval", type=int, default=300, help="采集间隔（秒），默认300秒")
    collect_parser.add_argument("--stop", action="store_true", help="停止数据采集")
    collect_parser.add_argument("--daemon", action="store_true", help="作为守护进程运行")
    collect_parser.set_defaults(func=command_collect)
    
    # 报告命令
    report_parser = subparsers.add_parser("report", help="报告管理")
    report_parser.add_argument("--daily", action="store_true", help="生成每日报告")
    report_parser.add_argument("--weekly", action="store_true", help="生成每周报告")
    report_parser.add_argument("--list", action="store_true", help="列出最新报告")
    report_parser.add_argument("--type", choices=["daily", "weekly"], help="报告类型")
    report_parser.add_argument("--limit", type=int, default=10, help="最大返回数量")
    report_parser.add_argument("--show", action="store_true", help="显示报告内容")
    report_parser.add_argument("--auto", action="store_true", help="启动自动报告生成")
    report_parser.add_argument("--stop-auto", action="store_true", help="停止自动报告生成")
    report_parser.add_argument("--daily-interval", type=int, default=86400, help="日报生成间隔（秒），默认86400秒")
    report_parser.add_argument("--weekly-interval", type=int, default=604800, help="周报生成间隔（秒），默认604800秒")
    report_parser.add_argument("--daemon", action="store_true", help="作为守护进程运行")
    report_parser.set_defaults(func=command_report)
    
    # 分析命令
    analyze_parser = subparsers.add_parser("analyze", help="数据分析")
    analyze_parser.add_argument("--memory", action="store_true", help="分析内存趋势")
    analyze_parser.add_argument("--cache", action="store_true", help="分析缓存性能")
    analyze_parser.add_argument("--oom", action="store_true", help="分析OOM风险")
    analyze_parser.add_argument("--all", action="store_true", help="执行所有分析")
    analyze_parser.add_argument("--days", type=int, default=7, help="分析天数，默认7天")
    analyze_parser.add_argument("--output", help="保存分析结果到文件")
    analyze_parser.set_defaults(func=command_analyze)
    
    # 仪表盘命令
    dashboard_parser = subparsers.add_parser("dashboard", help="启动可视化仪表盘")
    dashboard_parser.set_defaults(func=command_dashboard)
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行命令
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 