#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存压力测试命令行工具

用于测试低配设备上的内存性能和模型加载行为
支持多种测试模式和自动报告生成
"""

import os
import sys
import time
import argparse
import json
import csv
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

# 导入内存组件
from src.utils.memory_integration import get_memory_manager
from src.utils.memory_pressure import MemoryPressurer, run_pressure_test


def get_timestamp():
    """获取格式化的时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_report(report, output_format="json", output_dir="logs/memory_tests"):
    """
    保存测试报告
    
    Args:
        report: 测试报告数据
        output_format: 输出格式 (json, csv)
        output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = get_timestamp()
    test_mode = report.get("test_mode", "unknown")
    
    # 基本文件名
    base_filename = f"{timestamp}_{test_mode}_memory_test"
    
    if output_format == "json" or output_format == "all":
        # 保存为JSON
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已保存为JSON: {json_path}")
        
    if output_format == "csv" or output_format == "all":
        # 保存为CSV (仅保存关键数据)
        csv_path = os.path.join(output_dir, f"{base_filename}.csv")
        
        # 提取关键数据到扁平结构
        flat_data = {
            "timestamp": timestamp,
            "test_mode": test_mode,
            "duration": report.get("duration", 0),
            "model_id": report.get("model_id", "none"),
            "start_memory_percent": report.get("start_memory", {}).get("memory_percent", 0),
            "peak_memory_percent": report.get("peak_memory", 0),
            "end_memory_percent": report.get("end_memory", {}).get("memory_percent", 0),
            "model_load_time": report.get("model_load_time", 0),
            "avg_memory_percent": report.get("memory_statistics", {}).get("avg_memory_percent", 0),
            "min_available_gb": report.get("memory_statistics", {}).get("min_available_gb", 0),
            "volatility": report.get("memory_statistics", {}).get("volatility", 0)
        }
        
        # 写入CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flat_data.keys())
            writer.writeheader()
            writer.writerow(flat_data)
        print(f"报告摘要已保存为CSV: {csv_path}")
        
    return True


def run_simple_test(args):
    """
    运行简单的内存压力测试
    
    Args:
        args: 命令行参数
    """
    print(f"运行{args.mode}模式内存压力测试...")
    
    # 参数准备
    test_kwargs = {}
    if args.mode == "staircase":
        test_kwargs = {
            "step_size_mb": args.step_size,
            "step_interval_sec": args.interval,
            "max_steps": args.steps
        }
    elif args.mode == "burst":
        test_kwargs = {
            "target_percent": args.target / 100.0,  # 转为0-1范围
            "burst_duration_sec": args.duration
        }
    elif args.mode == "sawtooth":
        test_kwargs = {
            "min_percent": args.min / 100.0,  # 转为0-1范围
            "max_percent": args.max / 100.0,  # 转为0-1范围
            "cycle_duration_sec": args.duration,
            "num_cycles": args.cycles
        }
    
    # 运行测试
    run_pressure_test(args.mode, **test_kwargs)


def run_model_test(args):
    """
    运行模型加载测试
    
    Args:
        args: 命令行参数
    """
    print(f"运行模型加载压力测试，模型ID: {args.model_id}...")
    
    # 获取内存管理器
    mm = get_memory_manager()
    
    # 参数准备
    test_kwargs = {}
    if args.mode == "staircase":
        test_kwargs = {
            "step_size_mb": args.step_size,
            "step_interval_sec": args.interval,
            "max_steps": args.steps
        }
    elif args.mode == "burst":
        test_kwargs = {
            "target_percent": args.target / 100.0,
            "burst_duration_sec": args.duration
        }
    elif args.mode == "sawtooth":
        test_kwargs = {
            "min_percent": args.min / 100.0,
            "max_percent": args.max / 100.0,
            "cycle_duration_sec": args.duration, 
            "num_cycles": args.cycles
        }
    
    # 运行测试
    report = mm.run_controlled_pressure_test(
        test_mode=args.mode,
        model_id=args.model_id,
        test_duration=args.test_duration,
        **test_kwargs
    )
    
    # 保存报告
    if args.save_report:
        save_report(report, args.report_format, args.output_dir)
    
    return report


def run_quantization_test(args):
    """
    测试不同量化级别在不同内存压力下的表现
    
    Args:
        args: 命令行参数
    """
    print(f"运行量化级别测试，测试{len(args.quant_levels)}个量化级别...")
    
    # 获取内存管理器
    mm = get_memory_manager()
    
    # 量化级别列表
    quant_levels = args.quant_levels.split(',')
    if not quant_levels:
        quant_levels = ["Q2_K", "Q4_K_M", "Q6_K"]  # 默认测试3个级别
    
    results = []
    
    # 对每个量化级别运行测试
    for quant in quant_levels:
        print(f"\n测试量化级别: {quant}")
        
        # 运行测试
        report = mm.run_controlled_pressure_test(
            test_mode="burst",  # 使用突发模式测试
            model_id=args.model_id,
            test_duration=30,
            target_percent=0.7,
            burst_duration_sec=15
        )
        
        # 记录量化级别
        report["quantization_level"] = quant
        results.append(report)
        
        # 输出结果
        print(f"  峰值内存: {report['peak_memory']:.1f}%")
        print(f"  加载时间: {report['model_load_time']:.2f}秒")
        
        # 等待系统恢复
        time.sleep(5)
    
    # 保存汇总报告
    if args.save_report:
        summary_report = {
            "timestamp": get_timestamp(),
            "test_type": "quantization_comparison",
            "model_id": args.model_id,
            "results": results
        }
        
        save_report(summary_report, args.report_format, args.output_dir)
    
    return results


def run_stability_test(args):
    """
    长时间稳定性测试
    
    Args:
        args: 命令行参数
    """
    print(f"开始长时间稳定性测试: {args.hours}小时...")
    
    # 获取内存管理器
    mm = get_memory_manager()
    
    # 开始监控
    mm.start_monitoring(collect_stats=True)
    
    # 转换为秒
    duration_sec = int(args.hours * 3600)
    interval_min = 5  # 每5分钟运行一次压力测试
    
    start_time = time.time()
    cycle = 1
    
    results = []
    
    try:
        # 循环运行直到达到持续时间
        while time.time() - start_time < duration_sec:
            # 计算剩余时间
            elapsed = time.time() - start_time
            remaining = duration_sec - elapsed
            remaining_hr = remaining / 3600
            
            print(f"\n=== 循环 {cycle} ===")
            print(f"已经运行: {elapsed/3600:.1f}小时, 剩余: {remaining_hr:.1f}小时")
            
            # 每次循环交替运行不同压力模式
            if cycle % 3 == 1:
                test_mode = "staircase"
                test_kwargs = {"step_size_mb": 200, "step_interval_sec": 1.0, "max_steps": 8}
            elif cycle % 3 == 2:
                test_mode = "burst"
                test_kwargs = {"target_percent": 0.75, "burst_duration_sec": 10}
            else:
                test_mode = "sawtooth"
                test_kwargs = {"min_percent": 0.4, "max_percent": 0.7, "cycle_duration_sec": 15, "num_cycles": 2}
            
            # 运行测试
            print(f"运行{test_mode}压力测试...")
            report = mm.run_controlled_pressure_test(
                test_mode=test_mode,
                model_id=args.model_id if args.use_model else None,
                test_duration=60,  # 1分钟测试
                **test_kwargs
            )
            
            # 记录结果
            report["cycle"] = cycle
            report["elapsed_hours"] = elapsed / 3600
            results.append(report)
            
            # 输出当前状态
            print(f"峰值内存: {report['peak_memory']:.1f}%")
            if args.use_model:
                print(f"模型加载时间: {report['model_load_time']:.2f}秒")
            
            # 生成内存报告
            mem_report = mm.generate_memory_report()
            print(f"内存趋势: {mem_report['trend']}")
            print(f"建议: {mem_report['recommendation']}")
            
            cycle += 1
            
            # 休息间隔，除非已经接近结束
            if remaining > interval_min * 60:
                wait_time = interval_min * 60
                print(f"等待{interval_min}分钟后开始下一循环...")
                time.sleep(wait_time)
            else:
                # 剩余时间不足一个间隔，等待剩余时间
                print(f"等待{remaining/60:.1f}分钟后结束测试...")
                time.sleep(remaining)
                break
    
    except KeyboardInterrupt:
        print("\n用户中断测试")
    
    finally:
        # 停止监控
        mm.stop_monitoring()
        
        # 保存汇总报告
        if args.save_report:
            summary_report = {
                "timestamp": get_timestamp(),
                "test_type": "stability_test",
                "duration_hours": args.hours,
                "model_id": args.model_id if args.use_model else None,
                "completed_cycles": cycle - 1,
                "results": results
            }
            
            # 保存报告
            save_report(summary_report, args.report_format, args.output_dir)
        
        print(f"稳定性测试完成，共运行{cycle-1}个循环")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="内存压力测试工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 简单测试子命令
    simple_parser = subparsers.add_parser("simple", help="简单内存压力测试")
    simple_parser.add_argument("--mode", choices=["staircase", "burst", "sawtooth", "allocate_full"],
                             default="staircase", help="测试模式")
    simple_parser.add_argument("--step-size", type=int, default=100, help="阶梯模式下每步增加的内存(MB)")
    simple_parser.add_argument("--interval", type=float, default=1.0, help="阶梯模式下每步间隔时间(秒)")
    simple_parser.add_argument("--steps", type=int, default=20, help="阶梯模式下最大步数")
    simple_parser.add_argument("--target", type=float, default=70, help="突发模式下目标内存占用百分比(0-100)")
    simple_parser.add_argument("--duration", type=float, default=5.0, 
                             help="突发模式下持续时间或锯齿模式下周期时间(秒)")
    simple_parser.add_argument("--min", type=float, default=30, help="锯齿模式下最小内存占用百分比(0-100)")
    simple_parser.add_argument("--max", type=float, default=70, help="锯齿模式下最大内存占用百分比(0-100)")
    simple_parser.add_argument("--cycles", type=int, default=3, help="锯齿模式下周期数")
    
    # 模型测试子命令
    model_parser = subparsers.add_parser("model", help="模型加载内存压力测试")
    model_parser.add_argument("--model-id", type=str, required=True, help="要测试的模型ID")
    model_parser.add_argument("--mode", choices=["staircase", "burst", "sawtooth"],
                            default="burst", help="测试模式")
    model_parser.add_argument("--test-duration", type=int, default=60, help="测试持续时间(秒)")
    model_parser.add_argument("--step-size", type=int, default=100, help="阶梯模式下每步增加的内存(MB)")
    model_parser.add_argument("--interval", type=float, default=1.0, help="阶梯模式下每步间隔时间(秒)")
    model_parser.add_argument("--steps", type=int, default=20, help="阶梯模式下最大步数")
    model_parser.add_argument("--target", type=float, default=70, help="突发模式下目标内存占用百分比(0-100)")
    model_parser.add_argument("--duration", type=float, default=5.0, 
                            help="突发模式下持续时间或锯齿模式下周期时间(秒)")
    model_parser.add_argument("--min", type=float, default=30, help="锯齿模式下最小内存占用百分比(0-100)")
    model_parser.add_argument("--max", type=float, default=70, help="锯齿模式下最大内存占用百分比(0-100)")
    model_parser.add_argument("--cycles", type=int, default=3, help="锯齿模式下周期数")
    model_parser.add_argument("--save-report", action="store_true", help="保存测试报告")
    model_parser.add_argument("--report-format", choices=["json", "csv", "all"], 
                            default="all", help="报告格式")
    model_parser.add_argument("--output-dir", type=str, default="logs/memory_tests", help="报告输出目录")
    
    # 量化测试子命令
    quant_parser = subparsers.add_parser("quantization", help="量化级别测试")
    quant_parser.add_argument("--model-id", type=str, required=True, help="要测试的模型ID")
    quant_parser.add_argument("--quant-levels", type=str, default="Q2_K,Q4_K_M,Q6_K",
                            help="要测试的量化级别,逗号分隔")
    quant_parser.add_argument("--save-report", action="store_true", help="保存测试报告")
    quant_parser.add_argument("--report-format", choices=["json", "csv", "all"], 
                            default="all", help="报告格式")
    quant_parser.add_argument("--output-dir", type=str, default="logs/memory_tests", help="报告输出目录")
    
    # 稳定性测试子命令
    stability_parser = subparsers.add_parser("stability", help="长时间稳定性测试")
    stability_parser.add_argument("--hours", type=float, default=1.0, help="测试持续时间(小时)")
    stability_parser.add_argument("--use-model", action="store_true", help="是否加载模型")
    stability_parser.add_argument("--model-id", type=str, help="要测试的模型ID")
    stability_parser.add_argument("--save-report", action="store_true", help="保存测试报告")
    stability_parser.add_argument("--report-format", choices=["json", "csv", "all"], 
                                default="all", help="报告格式")
    stability_parser.add_argument("--output-dir", type=str, default="logs/memory_tests", help="报告输出目录")
    
    args = parser.parse_args()
    
    # 根据命令执行对应任务
    if args.command == "simple":
        run_simple_test(args)
    elif args.command == "model":
        run_model_test(args)
    elif args.command == "quantization":
        run_quantization_test(args)
    elif args.command == "stability":
        run_stability_test(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 