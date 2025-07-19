#!/usr/bin/env python
"""内存泄露检测命令行工具

此脚本提供命令行接口，用于检测应用程序内存泄露情况。

用法:
    python memory_cli.py monitor --process <PID> --interval 1 --duration 60
    python memory_cli.py test --scenario basic
    python memory_cli.py analyze --log <LOG_FILE>
"""

import os
import sys
import time
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入内存泄露检测器
from test.memory_test.memory_leak_detector import MemoryLeakDetector, MemorySnapshotType
from test.memory_test.test_leak import (
    test_memory_leak,
    test_model_switcher_memory,
    test_long_running_memory,
    test_error_recovery_memory,
    test_qos_memory_management
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_cli")


def parse_arguments():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析的命令行参数
    """
    parser = argparse.ArgumentParser(description="内存泄露检测命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # monitor命令 - 监控内存使用
    monitor_parser = subparsers.add_parser("monitor", help="监控内存使用")
    monitor_parser.add_argument("--process", type=int, help="进程ID（不指定则监控当前进程）")
    monitor_parser.add_argument("--interval", type=float, default=1.0, help="监控间隔（秒）")
    monitor_parser.add_argument("--duration", type=int, default=60, help="监控持续时间（秒），0表示持续监控直到手动停止")
    monitor_parser.add_argument("--threshold", type=float, default=0.05, help="内存泄露阈值（占比）")
    monitor_parser.add_argument("--log-dir", default="logs/memory", help="日志目录")
    
    # test命令 - 运行测试场景
    test_parser = subparsers.add_parser("test", help="运行内存泄露测试场景")
    test_parser.add_argument("--scenario", choices=[
        "basic", "model", "long", "error", "qos", "all"
    ], default="all", help="测试场景")
    test_parser.add_argument("--log-dir", default="logs/memory", help="日志目录")
    
    # analyze命令 - 分析内存日志
    analyze_parser = subparsers.add_parser("analyze", help="分析内存日志")
    analyze_parser.add_argument("--log", required=True, help="内存日志文件路径")
    analyze_parser.add_argument("--output", help="分析结果输出路径")
    
    return parser.parse_args()


def monitor_memory(args):
    """监控内存使用
    
    Args:
        args: 命令行参数
    """
    # 确保日志目录存在
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 创建内存泄露检测器
    detector = MemoryLeakDetector(
        leak_threshold=args.threshold,
        window_size=10,
        log_dir=args.log_dir
    )
    
    print(f"开始监控内存使用...")
    print(f"间隔: {args.interval}秒")
    if args.duration > 0:
        print(f"持续时间: {args.duration}秒")
    else:
        print("持续时间: 无限制（按Ctrl+C停止）")
    print(f"日志目录: {args.log_dir}")
    
    try:
        # 启动内存监控
        detector.start_monitoring(interval=args.interval)
        
        # 运行指定时间
        if args.duration > 0:
            time.sleep(args.duration)
        else:
            # 持续运行，直到用户中断
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n监控被用户中断")
    finally:
        # 停止监控
        detector.stop_monitoring()
        
        # 保存最终快照
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_snapshots_file = os.path.join(args.log_dir, f"final_snapshots_{timestamp}.json")
        detector.leak_analyzer.save_snapshots(final_snapshots_file)
        
        # 分析泄露趋势
        leak_detected = detector.leak_analyzer.analyze_leak_trend()
        leak_info = detector.leak_analyzer.get_leak_info()
        
        # 打印分析结果
        print("\n===== 内存监控结果 =====")
        print(f"初始内存: {leak_info['initial_memory_mb']:.2f}MB")
        print(f"最终内存: {leak_info['final_memory_mb']:.2f}MB")
        print(f"内存增长: {leak_info['absolute_growth_mb']:.2f}MB ({leak_info['growth_rate']*100:.2f}%)")
        
        if leak_detected:
            print(f"\n[警告] 检测到内存泄露趋势!")
            print(f"内存增长率: {leak_info['growth_rate']*100:.2f}% (阈值: {args.threshold*100:.2f}%)")
        else:
            print(f"\n未检测到明显的内存泄露")
        
        print(f"\n快照已保存到: {final_snapshots_file}")


def run_test_scenario(args):
    """运行测试场景
    
    Args:
        args: 命令行参数
    """
    # 确保日志目录存在
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 设置环境变量
    os.environ["MEMORY_LOG_DIR"] = args.log_dir
    
    # 根据场景选择运行的测试
    scenario = args.scenario.lower()
    
    print(f"===== 运行内存泄露测试: {scenario} =====")
    
    if scenario == "basic" or scenario == "all":
        print("\n> 运行基础内存泄露测试...")
        try:
            test_memory_leak()
            print("√ 基础内存泄露测试通过")
        except AssertionError as e:
            print(f"× 基础内存泄露测试失败: {str(e)}")
    
    if scenario == "model" or scenario == "all":
        print("\n> 运行模型切换内存测试...")
        try:
            test_model_switcher_memory()
            print("√ 模型切换内存测试通过")
        except AssertionError as e:
            print(f"× 模型切换内存测试失败: {str(e)}")
    
    if scenario == "long" or scenario == "all":
        print("\n> 运行长时间运行内存测试...")
        try:
            test_long_running_memory()
            print("√ 长时间运行内存测试通过")
        except AssertionError as e:
            print(f"× 长时间运行内存测试失败: {str(e)}")
    
    if scenario == "error" or scenario == "all":
        print("\n> 运行错误恢复内存测试...")
        try:
            test_error_recovery_memory()
            print("√ 错误恢复内存测试通过")
        except AssertionError as e:
            print(f"× 错误恢复内存测试失败: {str(e)}")
    
    if scenario == "qos" or scenario == "all":
        print("\n> 运行QoS内存管理测试...")
        try:
            test_qos_memory_management()
            print("√ QoS内存管理测试通过")
        except AssertionError as e:
            print(f"× QoS内存管理测试失败: {str(e)}")
    
    print("\n===== 内存泄露测试完成 =====")


def analyze_memory_log(args):
    """分析内存日志
    
    Args:
        args: 命令行参数
    """
    log_file = args.log
    
    if not os.path.exists(log_file):
        print(f"错误: 日志文件 {log_file} 不存在")
        return
    
    print(f"分析内存日志: {log_file}")
    
    try:
        # 读取日志文件
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            print("错误: 无效的日志文件格式")
            return
        
        # 提取内存使用数据
        timestamps = []
        memory_values = []
        
        for snapshot in data:
            if 'datetime' in snapshot and 'process' in snapshot and 'rss_mb' in snapshot['process']:
                timestamps.append(snapshot['datetime'])
                memory_values.append(snapshot['process']['rss_mb'])
        
        if len(memory_values) < 2:
            print("错误: 日志中的有效数据点不足")
            return
        
        # 计算基本统计信息
        initial_memory = memory_values[0]
        final_memory = memory_values[-1]
        min_memory = min(memory_values)
        max_memory = max(memory_values)
        avg_memory = sum(memory_values) / len(memory_values)
        
        # 计算内存增长
        absolute_growth = final_memory - initial_memory
        relative_growth = (absolute_growth / initial_memory) if initial_memory > 0 else 0
        
        # 计算增长趋势
        import numpy as np
        x = np.arange(len(memory_values))
        slope, intercept = np.polyfit(x, memory_values, 1)
        r_squared = np.corrcoef(x, memory_values)[0, 1] ** 2
        
        # 打印分析结果
        print("\n===== 内存日志分析 =====")
        print(f"数据点数量: {len(memory_values)}")
        print(f"开始时间: {timestamps[0]}")
        print(f"结束时间: {timestamps[-1]}")
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"最小内存: {min_memory:.2f}MB")
        print(f"最大内存: {max_memory:.2f}MB")
        print(f"平均内存: {avg_memory:.2f}MB")
        print(f"内存增长: {absolute_growth:.2f}MB ({relative_growth*100:.2f}%)")
        print(f"增长趋势: {slope:.4f}MB/snapshot (R²: {r_squared:.4f})")
        
        # 判断是否存在泄露
        if slope > 0 and r_squared > 0.7 and relative_growth > 0.05:
            print("\n[警告] 检测到可能的内存泄露趋势!")
        else:
            print("\n未检测到明显的内存泄露趋势")
        
        # 生成并保存分析报告
        if args.output:
            report = {
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log_file": log_file,
                "data_points": len(memory_values),
                "start_time": timestamps[0],
                "end_time": timestamps[-1],
                "memory": {
                    "initial_mb": initial_memory,
                    "final_mb": final_memory,
                    "min_mb": min_memory,
                    "max_mb": max_memory,
                    "avg_mb": avg_memory,
                    "absolute_growth_mb": absolute_growth,
                    "relative_growth": relative_growth
                },
                "trend": {
                    "slope": slope,
                    "intercept": intercept,
                    "r_squared": float(r_squared),
                    "has_leak_trend": slope > 0 and r_squared > 0.7 and relative_growth > 0.05
                }
            }
            
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n分析报告已保存到: {args.output}")
        
    except Exception as e:
        print(f"分析日志时出错: {str(e)}")


def main():
    """主函数"""
    args = parse_arguments()
    
    if args.command == "monitor":
        monitor_memory(args)
    elif args.command == "test":
        run_test_scenario(args)
    elif args.command == "analyze":
        analyze_memory_log(args)
    else:
        print("错误: 未指定有效的命令")
        print("有效命令: monitor, test, analyze")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 