#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计报告生成演示脚本

演示生成GDPR和个人信息保护法合规的审计报告。
提供命令行界面，支持不同报告类型和输出格式。
"""

import os
import sys
import argparse
import datetime
import json
from pathlib import Path
from typing import Union, Dict, Any, List, Optional

# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入审计报告生成器
from src.exporters.log_audit import (
    generate_audit_report, 
    export_audit_report,
    count_operations,
    list_security_events
)
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("audit_report_demo")

def parse_date(date_str: str) -> datetime.date:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串，格式为 YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month'
        
    Returns:
        解析后的日期对象
    """
    today = datetime.date.today()
    
    if date_str.lower() == 'today':
        return today
    elif date_str.lower() == 'yesterday':
        return today - datetime.timedelta(days=1)
    elif date_str.lower() == 'last_week':
        return today - datetime.timedelta(days=7)
    elif date_str.lower() == 'last_month':
        return today - datetime.timedelta(days=30)
    else:
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"无法解析日期: {date_str}，请使用 YYYY-MM-DD 格式或 'today', 'yesterday', 'last_week', 'last_month'")

def show_report_summary(report: Dict[str, Any]) -> None:
    """
    显示报告摘要
    
    Args:
        report: 报告字典
    """
    if isinstance(report, str):
        # 如果是字符串（例如文本格式的报告），直接打印
        print(report)
        return
        
    # 打印报告摘要
    summary = report.get("summary", {})
    
    print("\n" + "=" * 80)
    print(f"审计报告摘要: {report.get('period', '')}")
    print("=" * 80)
    print(f"总操作数: {summary.get('total_operations', 0)}")
    print(f"安全事件数: {summary.get('security_incidents_count', 0)}")
    print(f"数据主体数: {summary.get('data_subjects_count', 0)}")
    print(f"合规状态: {'合规' if summary.get('compliant', False) else '不合规'}")
    print("=" * 80)
    
    # 显示操作统计
    operations = report.get("operations", {})
    if operations:
        print("\n操作统计:")
        for op_type, count in operations.items():
            if op_type != "total":  # 跳过总数，已在摘要中显示
                print(f"  {op_type}: {count}")
    
    # 显示安全事件
    security_incidents = report.get("security_incidents", [])
    if security_incidents:
        print("\n安全事件:")
        for i, incident in enumerate(security_incidents[:5], 1):  # 只显示前5个
            print(f"  {i}. [{incident.get('timestamp', '未知时间')}] "
                  f"{incident.get('type', '未知类型')}: "
                  f"{incident.get('description', '无描述')}")
            
        if len(security_incidents) > 5:
            print(f"  ... 还有 {len(security_incidents) - 5} 个安全事件未显示")
    
    print("\n报告详情已" + (f"保存至: {args.output}" if args.output else "显示在上方"))

def generate_report_interactive() -> None:
    """交互式生成报告"""
    print("\n=== 交互式生成审计报告 ===\n")
    
    # 获取日期范围
    start_date_str = input("请输入开始日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month'): ")
    try:
        start_date = parse_date(start_date_str)
    except ValueError as e:
        print(f"错误: {e}")
        return
        
    end_date_str = input("请输入结束日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month'): ")
    try:
        end_date = parse_date(end_date_str)
    except ValueError as e:
        print(f"错误: {e}")
        return
    
    # 如果开始日期晚于结束日期，交换它们
    if start_date > end_date:
        print("警告: 开始日期晚于结束日期，将交换这两个日期。")
        start_date, end_date = end_date, start_date
    
    # 选择报告类型
    report_type = input("请选择报告类型 (gdpr, pipl, all) [默认: gdpr]: ").lower() or "gdpr"
    if report_type not in ["gdpr", "pipl", "all"]:
        print(f"错误: 不支持的报告类型: {report_type}")
        return
    
    # 选择输出格式
    output_format = input("请选择输出格式 (json, csv, text) [默认: text]: ").lower() or "text"
    if output_format not in ["json", "csv", "text"]:
        print(f"错误: 不支持的输出格式: {output_format}")
        return
    
    # 选择是否包含详细信息
    include_details_str = input("是否包含详细信息 (y/n) [默认: n]: ").lower() or "n"
    include_details = include_details_str.startswith("y")
    
    # 选择是否导出到文件
    export_str = input("是否导出到文件 (y/n) [默认: n]: ").lower() or "n"
    if export_str.startswith("y"):
        output_file = input("请输入输出文件路径: ")
        if not output_file:
            print("错误: 输出文件路径不能为空")
            return
    else:
        output_file = None
    
    # 生成报告
    try:
        report = generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            output_format=output_format,
            include_details=include_details
        )
        
        # 导出或显示报告
        if output_file:
            export_audit_report(
                start_date=start_date,
                end_date=end_date,
                output_file=output_file,
                report_type=report_type,
                output_format=output_format
            )
            print(f"报告已导出到: {output_file}")
        else:
            # 显示报告
            if output_format == "json":
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(report)
    
    except Exception as e:
        print(f"生成报告时出错: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成合规审计报告")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 生成报告命令
    generate_parser = subparsers.add_parser("generate", help="生成审计报告")
    generate_parser.add_argument("--start-date", type=str, required=True, 
                              help="开始日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    generate_parser.add_argument("--end-date", type=str, required=True,
                              help="结束日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    generate_parser.add_argument("--type", type=str, default="gdpr", choices=["gdpr", "pipl", "all"],
                              help="报告类型 (默认: gdpr)")
    generate_parser.add_argument("--format", type=str, default="text", choices=["json", "csv", "text"],
                              help="输出格式 (默认: text)")
    generate_parser.add_argument("--output", type=str, help="输出文件路径")
    generate_parser.add_argument("--details", action="store_true", help="包含详细信息")
    
    # 统计操作命令
    stats_parser = subparsers.add_parser("stats", help="统计操作")
    stats_parser.add_argument("--start-date", type=str, required=True, 
                           help="开始日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    stats_parser.add_argument("--end-date", type=str, required=True,
                           help="结束日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    
    # 安全事件命令
    security_parser = subparsers.add_parser("security", help="列出安全事件")
    security_parser.add_argument("--start-date", type=str, required=True, 
                              help="开始日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    security_parser.add_argument("--end-date", type=str, required=True,
                              help="结束日期 (YYYY-MM-DD 或 'today', 'yesterday', 'last_week', 'last_month')")
    security_parser.add_argument("--output", type=str, help="输出文件路径")
    
    # 交互式命令
    subparsers.add_parser("interactive", help="交互式生成报告")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有命令，显示帮助
    if not args.command:
        parser.print_help()
        return
    
    # 执行对应的命令
    if args.command == "generate":
        try:
            start_date = parse_date(args.start_date)
            end_date = parse_date(args.end_date)
            
            # 如果开始日期晚于结束日期，交换它们
            if start_date > end_date:
                logger.warning("开始日期晚于结束日期，将交换这两个日期。")
                start_date, end_date = end_date, start_date
            
            if args.output:
                # 导出到文件
                success = export_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    output_file=args.output,
                    report_type=args.type,
                    output_format=args.format
                )
                
                if success:
                    print(f"审计报告已导出到: {args.output}")
                    
                    # 生成报告用于显示摘要
                    report = generate_audit_report(
                        start_date=start_date,
                        end_date=end_date,
                        report_type=args.type,
                        output_format="json",  # 用于解析摘要
                        include_details=args.details
                    )
                    
                    # 显示摘要
                    show_report_summary(report)
                else:
                    print("导出审计报告失败")
            else:
                # 直接生成并显示
                report = generate_audit_report(
                    start_date=start_date,
                    end_date=end_date,
                    report_type=args.type,
                    output_format=args.format,
                    include_details=args.details
                )
                
                # 如果是文本格式，直接打印
                if args.format == "text":
                    print(report)
                elif args.format == "json":
                    print(json.dumps(report, ensure_ascii=False, indent=2))
                else:
                    print(report)
        
        except Exception as e:
            print(f"生成审计报告时出错: {str(e)}")
    
    elif args.command == "stats":
        try:
            start_date = parse_date(args.start_date)
            end_date = parse_date(args.end_date)
            
            # 如果开始日期晚于结束日期，交换它们
            if start_date > end_date:
                logger.warning("开始日期晚于结束日期，将交换这两个日期。")
                start_date, end_date = end_date, start_date
            
            # 统计操作
            operations = count_operations(start_date, end_date)
            
            # 显示统计结果
            print("\n操作统计:")
            for op_type, count in operations.items():
                print(f"  {op_type}: {count}")
                
        except Exception as e:
            print(f"统计操作时出错: {str(e)}")
    
    elif args.command == "security":
        try:
            start_date = parse_date(args.start_date)
            end_date = parse_date(args.end_date)
            
            # 如果开始日期晚于结束日期，交换它们
            if start_date > end_date:
                logger.warning("开始日期晚于结束日期，将交换这两个日期。")
                start_date, end_date = end_date, start_date
            
            # 列出安全事件
            security_events = list_security_events(start_date, end_date)
            
            # 如果需要导出到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(security_events, f, ensure_ascii=False, indent=2)
                print(f"安全事件已导出到: {args.output}")
            
            # 显示安全事件
            print(f"\n安全事件 ({len(security_events)} 个):")
            for i, event in enumerate(security_events, 1):
                print(f"  {i}. [{event.get('timestamp', '未知时间')}] "
                      f"{event.get('type', '未知类型')} ({event.get('severity', '未知级别')}): "
                      f"{event.get('description', '无描述')}")
                
        except Exception as e:
            print(f"列出安全事件时出错: {str(e)}")
    
    elif args.command == "interactive":
        generate_report_interactive()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 