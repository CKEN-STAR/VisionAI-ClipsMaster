#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SRT时间码解析器演示脚本

展示SRT时间码解析器的基本用法和功能
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.parsers.srt_parser import (
    parse_srt_time,
    format_srt_time,
    parse_srt_timerange,
    calculate_duration,
    adjust_srt_time,
    adjust_srt_timerange,
    is_valid_srt_time
)


def demo_parse_time():
    """演示解析SRT时间码"""
    print("\n==== 演示解析SRT时间码 ====")
    
    test_times = [
        "01:02:03,456",  # 标准格式（逗号分隔）
        "01:02:03.456",  # 标准格式（点分隔）
        "00:00:00,000",  # 零值
        "10:20:30,789",  # 大数值
        "01:02:03,4",    # 毫秒不足3位
        "25:02:03,456"   # 小时>24
    ]
    
    for time_str in test_times:
        try:
            seconds = parse_srt_time(time_str)
            print(f"时间码: {time_str} → {seconds:.3f}秒")
        except ValueError as e:
            print(f"错误: {time_str} - {str(e)}")
    
    # 测试无效格式
    try:
        parse_srt_time("invalid")
    except ValueError as e:
        print(f"预期的错误处理: {str(e)}")


def demo_format_time():
    """演示格式化为SRT时间码"""
    print("\n==== 演示格式化为SRT时间码 ====")
    
    test_seconds = [
        3723.456,  # 标准值
        0,         # 零值
        37230.789, # 大数值
        3723,      # 整数
        3723.4567  # 四舍五入
    ]
    
    for seconds in test_seconds:
        try:
            time_str = format_srt_time(seconds)
            print(f"{seconds:.3f}秒 → {time_str}")
        except ValueError as e:
            print(f"错误: {seconds} - {str(e)}")
    
    # 测试无效值
    try:
        format_srt_time(-1)
    except ValueError as e:
        print(f"预期的错误处理: {str(e)}")


def demo_parse_timerange():
    """演示解析SRT时间范围"""
    print("\n==== 演示解析SRT时间范围 ====")
    
    test_ranges = [
        "01:02:03,456 --> 01:02:10,789",             # 标准格式
        "  01:02:03,456  -->  01:02:10,789  ",       # 额外空格
        "01:02:03.456 --> 01:02:10.789"              # 点分隔
    ]
    
    for range_str in test_ranges:
        try:
            start, end = parse_srt_timerange(range_str)
            print(f"时间范围: {range_str}")
            print(f"  开始: {start:.3f}秒")
            print(f"  结束: {end:.3f}秒")
            print(f"  持续: {end - start:.3f}秒")
        except ValueError as e:
            print(f"错误: {range_str} - {str(e)}")
    
    # 测试无效格式
    try:
        parse_srt_timerange("01:02:03,456")
    except ValueError as e:
        print(f"预期的错误处理: {str(e)}")


def demo_calculate_duration():
    """演示计算持续时间"""
    print("\n==== 演示计算持续时间 ====")
    
    test_pairs = [
        ("01:02:03,456", "01:02:10,789"),  # 字符串输入
        (3723.456, 3730.789),              # 数字输入
        ("01:02:03,456", 3730.789),        # 混合输入
        (3723.456, "01:02:10,789"),        # 混合输入
        ("01:02:03,456", "01:02:03,456")   # 零持续时间
    ]
    
    for start, end in test_pairs:
        try:
            duration = calculate_duration(start, end)
            print(f"开始: {start}, 结束: {end} → 持续: {duration:.3f}秒")
        except ValueError as e:
            print(f"错误: {start} to {end} - {str(e)}")
    
    # 测试无效输入
    try:
        calculate_duration("01:02:10,789", "01:02:03,456")
    except ValueError as e:
        print(f"预期的错误处理: {str(e)}")


def demo_adjust_time():
    """演示调整SRT时间码"""
    print("\n==== 演示调整SRT时间码 ====")
    
    test_adjustments = [
        ("01:02:03,456", 10),    # 增加时间
        ("01:02:03,456", -3),    # 减少时间
        ("01:02:03,456", 60),    # 跨分钟
        ("01:59:03,456", 60),    # 跨小时
        ("01:02:03,456", 0.5),   # 毫秒处理
        ("01:02:03,456", -0.2),  # 毫秒处理
        ("01:02:03,456", 0)      # 无变化
    ]
    
    for time_str, offset in test_adjustments:
        try:
            adjusted = adjust_srt_time(time_str, offset)
            print(f"原始: {time_str}, 偏移: {offset:.1f}秒 → 调整后: {adjusted}")
        except ValueError as e:
            print(f"错误: {time_str} + {offset} - {str(e)}")
    
    # 测试无效调整
    try:
        adjust_srt_time("01:02:03,456", -4000)
    except ValueError as e:
        print(f"预期的错误处理: {str(e)}")


def demo_adjust_timerange():
    """演示调整SRT时间范围"""
    print("\n==== 演示调整SRT时间范围 ====")
    
    test_adjustments = [
        ("01:02:03,456 --> 01:02:10,789", 10),  # 增加时间
        ("01:02:03,456 --> 01:02:10,789", -3)   # 减少时间
    ]
    
    for range_str, offset in test_adjustments:
        try:
            adjusted = adjust_srt_timerange(range_str, offset)
            print(f"原始: {range_str}")
            print(f"偏移: {offset:.1f}秒")
            print(f"调整后: {adjusted}")
        except ValueError as e:
            print(f"错误: {range_str} + {offset} - {str(e)}")


def demo_validate_time():
    """演示验证SRT时间码格式"""
    print("\n==== 演示验证SRT时间码格式 ====")
    
    test_formats = [
        "01:02:03,456",  # 有效（逗号分隔）
        "01:02:03.456",  # 有效（点分隔）
        "00:00:00,000",  # 有效（零值）
        "invalid",       # 无效
        "01:02:03",      # 无效（无毫秒）
        "01:02:03,abc"   # 无效（非数字毫秒）
    ]
    
    for time_str in test_formats:
        valid = is_valid_srt_time(time_str)
        status = "有效" if valid else "无效"
        print(f"时间码: {time_str} → {status}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SRT时间码解析器演示")
    parser.add_argument("--all", action="store_true", help="运行所有演示")
    parser.add_argument("--parse", action="store_true", help="演示解析SRT时间码")
    parser.add_argument("--format", action="store_true", help="演示格式化为SRT时间码")
    parser.add_argument("--range", action="store_true", help="演示解析SRT时间范围")
    parser.add_argument("--duration", action="store_true", help="演示计算持续时间")
    parser.add_argument("--adjust", action="store_true", help="演示调整SRT时间码")
    parser.add_argument("--adjust-range", action="store_true", help="演示调整SRT时间范围")
    parser.add_argument("--validate", action="store_true", help="演示验证SRT时间码格式")
    
    args = parser.parse_args()
    
    # 如果没有指定参数，默认运行所有演示
    if not any(vars(args).values()):
        args.all = True
    
    # 运行所有演示
    if args.all:
        print("=== SRT时间码解析器演示 ===")
        demo_parse_time()
        demo_format_time()
        demo_parse_timerange()
        demo_calculate_duration()
        demo_adjust_time()
        demo_adjust_timerange()
        demo_validate_time()
        return
    
    # 运行指定的演示
    if args.parse:
        demo_parse_time()
    
    if args.format:
        demo_format_time()
    
    if args.range:
        demo_parse_timerange()
    
    if args.duration:
        demo_calculate_duration()
    
    if args.adjust:
        demo_adjust_time()
    
    if args.adjust_range:
        demo_adjust_timerange()
    
    if args.validate:
        demo_validate_time()


if __name__ == "__main__":
    main() 