#!/usr/bin/env python
"""内存泄露检测命令行工具

此脚本提供命令行接口，用于监控和检测应用程序内存泄露。
"""

import os
import sys
import time
import gc
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from test.memory_test.memory_leak_detector import MemoryLeakDetector, MemorySnapshotType
except ImportError:
    print("错误: 无法导入内存泄露检测器模块。请确保您位于项目根目录或正确设置了PYTHONPATH。")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_leak_detector_cli")


def setup_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器
    
    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(description="内存泄露检测工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 监控命令
    monitor_parser = subparsers.add_parser("monitor", help="监控内存使用")
    monitor_parser.add_argument("--interval", type=float, default=1.0, help="监控间隔（秒）")
    monitor_parser.add_argument("--threshold", type=float, default=0.05, help="泄露阈值（比例）")
    monitor_parser.add_argument("--window", type=int, default=10, help="分析窗口大小")
    monitor_parser.add_argument("--duration", type=int, default=60, help="监控持续时间（秒），0表示无限")
    monitor_parser.add_argument("--log-dir", default="./logs/memory", help="日志目录")
    monitor_parser.add_argument("--snapshot-type", choices=["process", "python", "tracemalloc"], 
                               default="process", help="快照类型")
    monitor_parser.add_argument("--track-types", nargs="+", help="要跟踪的类型名称列表")
    
    # 分析命令
    analyze_parser = subparsers.add_parser("analyze", help="分析内存快照")
    analyze_parser.add_argument("snapshot_file", help="快照文件路径")
    analyze_parser.add_argument("--output", help="输出报告文件路径")
    
    # 比较命令
    compare_parser = subparsers.add_parser("compare", help="比较两个内存快照")
    compare_parser.add_argument("snapshot1", help="第一个快照文件路径")
    compare_parser.add_argument("snapshot2", help="第二个快照文件路径")
    compare_parser.add_argument("--output", help="输出比较报告文件路径")
    
    return parser


def get_snapshot_type(type_name: str) -> MemorySnapshotType:
    """根据名称获取快照类型
    
    Args:
        type_name: 类型名称
    
    Returns:
        MemorySnapshotType: 快照类型枚举值
    """
    if type_name == "process":
        return MemorySnapshotType.PROCESS
    elif type_name == "python":
        return MemorySnapshotType.PYTHON
    elif type_name == "tracemalloc":
        return MemorySnapshotType.TRACEMALLOC
    else:
        logger.warning(f"未知的快照类型: {type_name}，使用默认类型PROCESS")
        return MemorySnapshotType.PROCESS


def monitor_memory(args) -> None:
    """监控内存使用
    
    Args:
        args: 命令行参数
    """
    # 创建日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 获取快照类型
    snapshot_type = get_snapshot_type(args.snapshot_type)
    
    # 初始化检测器
    detector = MemoryLeakDetector(
        leak_threshold=args.threshold,
        window_size=args.window,
        snapshot_type=snapshot_type,
        log_dir=args.log_dir
    )
    
    # 跟踪指定类型
    if args.track_types:
        for type_name in args.track_types:
            try:
                # 尝试查找类型
                import importlib
                module_name, class_name = type_name.rsplit(".", 1)
                module = importlib.import_module(module_name)
                cls = getattr(module, class_name)
                detector.track_objects_of_type(cls)
            except (ValueError, ImportError, AttributeError) as e:
                logger.error(f"无法跟踪类型 {type_name}: {e}")
    
    try:
        # 启动监控
        detector.start_monitoring(args.interval)
        
        # 运行指定时间
        if args.duration > 0:
            logger.info(f"内存泄露检测已启动，将运行 {args.duration} 秒")
            time.sleep(args.duration)
        else:
            logger.info("内存泄露检测已启动，按Ctrl+C停止")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("检测被用户中断")
    finally:
        # 停止监控
        detector.stop_monitoring()
        
        # 保存最终快照
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshots_file = os.path.join(args.log_dir, f"final_snapshots_{timestamp}.json")
        detector.leak_analyzer.save_snapshots(snapshots_file)
        
        # 获取tracemalloc快照
        if args.snapshot_type == "tracemalloc":
            detector.take_tracemalloc_snapshot()
        
        logger.info("内存泄露检测已完成")


def analyze_snapshot(args) -> None:
    """分析内存快照
    
    Args:
        args: 命令行参数
    """
    if not os.path.exists(args.snapshot_file):
        logger.error(f"快照文件不存在: {args.snapshot_file}")
        return
    
    try:
        # 加载快照数据
        with open(args.snapshot_file, 'r', encoding='utf-8') as f:
            snapshots = json.load(f)
        
        # 验证数据格式
        if not isinstance(snapshots, list) or len(snapshots) == 0:
            logger.error("无效的快照文件格式")
            return
        
        # 计算统计信息
        num_snapshots = len(snapshots)
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        
        # 提取内存使用数据
        memory_values = [s.get('process', {}).get('rss_mb', 0) for s in snapshots]
        if not memory_values or all(v == 0 for v in memory_values):
            logger.error("快照中无有效内存数据")
            return
        
        # 计算增长趋势
        import numpy as np
        x = np.arange(len(memory_values))
        slope, intercept = np.polyfit(x, memory_values, 1)
        
        growth_rate = slope * len(memory_values) / memory_values[0] if memory_values[0] > 0 else 0
        
        # 生成报告
        report = {
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_file": args.snapshot_file,
            "num_snapshots": num_snapshots,
            "start_time": first_snapshot.get('datetime', ''),
            "end_time": last_snapshot.get('datetime', ''),
            "duration_seconds": (
                last_snapshot.get('timestamp', 0) - first_snapshot.get('timestamp', 0)
            ),
            "memory": {
                "initial_mb": memory_values[0],
                "final_mb": memory_values[-1],
                "min_mb": min(memory_values),
                "max_mb": max(memory_values),
                "avg_mb": sum(memory_values) / len(memory_values),
                "absolute_growth_mb": memory_values[-1] - memory_values[0],
                "growth_percent": (memory_values[-1] - memory_values[0]) / memory_values[0] * 100 if memory_values[0] > 0 else 0,
            },
            "trend": {
                "slope_mb_per_snapshot": slope,
                "intercept_mb": intercept,
                "r_squared": np.corrcoef(x, memory_values)[0, 1] ** 2,
                "growth_rate": growth_rate,
                "has_leak_trend": growth_rate > 0.05  # 默认阈值
            }
        }
        
        # 打印报告
        print("\n===== 内存快照分析报告 =====")
        print(f"快照文件: {args.snapshot_file}")
        print(f"快照数量: {num_snapshots}")
        print(f"起始时间: {report['start_time']}")
        print(f"结束时间: {report['end_time']}")
        print(f"监控时长: {report['duration_seconds']:.1f} 秒")
        print("\n--- 内存使用 ---")
        print(f"初始内存: {report['memory']['initial_mb']:.2f} MB")
        print(f"最终内存: {report['memory']['final_mb']:.2f} MB")
        print(f"最小内存: {report['memory']['min_mb']:.2f} MB")
        print(f"最大内存: {report['memory']['max_mb']:.2f} MB")
        print(f"平均内存: {report['memory']['avg_mb']:.2f} MB")
        print(f"内存增长: {report['memory']['absolute_growth_mb']:.2f} MB ({report['memory']['growth_percent']:.2f}%)")
        print("\n--- 趋势分析 ---")
        print(f"斜率: {report['trend']['slope_mb_per_snapshot']:.4f} MB/快照")
        print(f"R平方: {report['trend']['r_squared']:.4f}")
        print(f"增长率: {report['trend']['growth_rate']:.2%}")
        print(f"泄露趋势: {'是' if report['trend']['has_leak_trend'] else '否'}")
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"\n报告已保存到: {args.output}")
        
    except Exception as e:
        logger.error(f"分析快照时出错: {e}")


def compare_snapshots(args) -> None:
    """比较两个内存快照
    
    Args:
        args: 命令行参数
    """
    if not os.path.exists(args.snapshot1):
        logger.error(f"第一个快照文件不存在: {args.snapshot1}")
        return
    
    if not os.path.exists(args.snapshot2):
        logger.error(f"第二个快照文件不存在: {args.snapshot2}")
        return
    
    try:
        # 加载快照数据
        with open(args.snapshot1, 'r', encoding='utf-8') as f:
            snapshots1 = json.load(f)
        
        with open(args.snapshot2, 'r', encoding='utf-8') as f:
            snapshots2 = json.load(f)
        
        # 验证数据格式
        if not isinstance(snapshots1, list) or len(snapshots1) == 0:
            logger.error(f"无效的快照文件格式: {args.snapshot1}")
            return
        
        if not isinstance(snapshots2, list) or len(snapshots2) == 0:
            logger.error(f"无效的快照文件格式: {args.snapshot2}")
            return
        
        # 计算各快照集的统计信息
        def compute_stats(snapshots) -> Dict[str, Any]:
            memory_values = [s.get('process', {}).get('rss_mb', 0) for s in snapshots]
            if not memory_values or all(v == 0 for v in memory_values):
                return {"error": "无有效内存数据"}
            
            import numpy as np
            x = np.arange(len(memory_values))
            slope, intercept = np.polyfit(x, memory_values, 1)
            
            return {
                "num_snapshots": len(snapshots),
                "start_time": snapshots[0].get('datetime', ''),
                "end_time": snapshots[-1].get('datetime', ''),
                "duration_seconds": (
                    snapshots[-1].get('timestamp', 0) - snapshots[0].get('timestamp', 0)
                ),
                "memory": {
                    "initial_mb": memory_values[0],
                    "final_mb": memory_values[-1],
                    "min_mb": min(memory_values),
                    "max_mb": max(memory_values),
                    "avg_mb": sum(memory_values) / len(memory_values),
                    "absolute_growth_mb": memory_values[-1] - memory_values[0],
                    "growth_percent": (memory_values[-1] - memory_values[0]) / memory_values[0] * 100 if memory_values[0] > 0 else 0,
                },
                "trend": {
                    "slope_mb_per_snapshot": slope,
                    "r_squared": np.corrcoef(x, memory_values)[0, 1] ** 2,
                }
            }
        
        stats1 = compute_stats(snapshots1)
        stats2 = compute_stats(snapshots2)
        
        # 如果有错误，提前退出
        if "error" in stats1:
            logger.error(f"第一个快照文件错误: {stats1['error']}")
            return
        
        if "error" in stats2:
            logger.error(f"第二个快照文件错误: {stats2['error']}")
            return
        
        # 比较结果
        comparison = {
            "comparison_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot1": {
                "file": args.snapshot1,
                "stats": stats1
            },
            "snapshot2": {
                "file": args.snapshot2,
                "stats": stats2
            },
            "differences": {
                "avg_memory_mb": stats2["memory"]["avg_mb"] - stats1["memory"]["avg_mb"],
                "avg_memory_percent": (
                    (stats2["memory"]["avg_mb"] / stats1["memory"]["avg_mb"] - 1) * 100
                    if stats1["memory"]["avg_mb"] > 0 else 0
                ),
                "slope_diff": stats2["trend"]["slope_mb_per_snapshot"] - stats1["trend"]["slope_mb_per_snapshot"],
                "slope_diff_percent": (
                    (stats2["trend"]["slope_mb_per_snapshot"] / stats1["trend"]["slope_mb_per_snapshot"] - 1) * 100
                    if stats1["trend"]["slope_mb_per_snapshot"] != 0 else 0
                ),
                "growth_diff": (
                    stats2["memory"]["growth_percent"] - stats1["memory"]["growth_percent"]
                )
            },
            "conclusion": {
                "has_significant_diff": False,
                "is_worse": False,
                "details": []
            }
        }
        
        # 分析结论
        details = []
        
        # 检查平均内存差异
        if abs(comparison["differences"]["avg_memory_percent"]) > 10:
            if comparison["differences"]["avg_memory_mb"] > 0:
                details.append(f"第二个快照的平均内存使用比第一个高 {comparison['differences']['avg_memory_percent']:.1f}%")
                comparison["conclusion"]["is_worse"] = True
            else:
                details.append(f"第二个快照的平均内存使用比第一个低 {abs(comparison['differences']['avg_memory_percent']):.1f}%")
            comparison["conclusion"]["has_significant_diff"] = True
        
        # 检查增长率差异
        if abs(comparison["differences"]["growth_diff"]) > 5:
            if comparison["differences"]["growth_diff"] > 0:
                details.append(f"第二个快照的内存增长率比第一个高 {comparison['differences']['growth_diff']:.1f}%")
                comparison["conclusion"]["is_worse"] = True
            else:
                details.append(f"第二个快照的内存增长率比第一个低 {abs(comparison['differences']['growth_diff']):.1f}%")
            comparison["conclusion"]["has_significant_diff"] = True
        
        # 检查趋势差异
        if abs(comparison["differences"]["slope_diff"]) > 0.1:
            if comparison["differences"]["slope_diff"] > 0:
                details.append(f"第二个快照的内存增长趋势比第一个更陡峭")
                comparison["conclusion"]["is_worse"] = True
            else:
                details.append(f"第二个快照的内存增长趋势比第一个更平缓")
            comparison["conclusion"]["has_significant_diff"] = True
        
        comparison["conclusion"]["details"] = details
        
        # 打印比较报告
        print("\n===== 内存快照比较报告 =====")
        print(f"快照文件1: {args.snapshot1}")
        print(f"快照文件2: {args.snapshot2}")
        
        print("\n--- 快照1统计 ---")
        print(f"快照数量: {stats1['num_snapshots']}")
        print(f"平均内存: {stats1['memory']['avg_mb']:.2f} MB")
        print(f"内存增长: {stats1['memory']['growth_percent']:.2f}%")
        print(f"内存趋势: {stats1['trend']['slope_mb_per_snapshot']:.4f} MB/快照")
        
        print("\n--- 快照2统计 ---")
        print(f"快照数量: {stats2['num_snapshots']}")
        print(f"平均内存: {stats2['memory']['avg_mb']:.2f} MB")
        print(f"内存增长: {stats2['memory']['growth_percent']:.2f}%")
        print(f"内存趋势: {stats2['trend']['slope_mb_per_snapshot']:.4f} MB/快照")
        
        print("\n--- 差异分析 ---")
        print(f"平均内存差异: {comparison['differences']['avg_memory_mb']:.2f} MB ({comparison['differences']['avg_memory_percent']:.1f}%)")
        print(f"内存增长差异: {comparison['differences']['growth_diff']:.2f}%")
        print(f"趋势斜率差异: {comparison['differences']['slope_diff']:.4f} MB/快照")
        
        print("\n--- 结论 ---")
        if comparison["conclusion"]["has_significant_diff"]:
            if comparison["conclusion"]["is_worse"]:
                print("总体评估: 第二个快照表现更差")
            else:
                print("总体评估: 第二个快照表现更好")
                
            for detail in comparison["conclusion"]["details"]:
                print(f"- {detail}")
        else:
            print("总体评估: 两个快照没有显著差异")
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2)
            print(f"\n报告已保存到: {args.output}")
        
    except Exception as e:
        logger.error(f"比较快照时出错: {e}")


def main() -> None:
    """主函数"""
    # 解析命令行参数
    parser = setup_parser()
    args = parser.parse_args()
    
    # 调用相应的功能
    if args.command == "monitor":
        monitor_memory(args)
    elif args.command == "analyze":
        analyze_snapshot(args)
    elif args.command == "compare":
        compare_snapshots(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 