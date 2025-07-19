#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控看板CLI工具

提供命令行工具，用于启动和管理VisionAI-ClipsMaster的监控看板。
支持以CLI、Web或导出模式运行。
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# 导入监控组件
from src.dashboard.monitor_dashboard import get_dashboard
from src.dashboard.web_dashboard import run_web_dashboard

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard_cli")

def print_metrics(metrics: Dict[str, Any], prefix: str = ""):
    """打印指标信息到控制台
    
    Args:
        metrics: 指标字典
        prefix: 输出前缀
    """
    for key, value in sorted(metrics.items()):
        # 处理嵌套字典
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_metrics(value, prefix + "  ")
        # 处理列表
        elif isinstance(value, list):
            print(f"{prefix}{key}: [{len(value)} 项]")
        # 处理数值，格式化输出
        elif isinstance(value, (int, float)):
            # 对百分比和内存值进行格式化
            if "percent" in key or "率" in key:
                print(f"{prefix}{key}: {value:.1f}%")
            elif "memory" in key or "内存" in key:
                print(f"{prefix}{key}: {value:.1f} MB")
            elif "size" in key or "capacity" in key or "容量" in key:
                print(f"{prefix}{key}: {value:.1f} MB")
            elif "time" in key or "duration" in key or "时间" in key:
                print(f"{prefix}{key}: {value:.2f} 秒")
            else:
                print(f"{prefix}{key}: {value}")
        # 其他类型直接输出
        else:
            print(f"{prefix}{key}: {value}")

def run_cli_dashboard(refresh_interval: int = 5, duration: int = 300):
    """运行命令行界面的监控看板
    
    Args:
        refresh_interval: 刷新间隔（秒）
        duration: 运行时间（秒）
    """
    # 获取看板实例
    dashboard = get_dashboard()
    if not dashboard.running:
        dashboard.start()
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 获取最新数据
            data = dashboard.get_dashboard_data()
            
            # 打印标题
            print("\n===== VisionAI-ClipsMaster 监控看板 =====")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"运行时间: {time.time() - start_time:.1f} 秒")
            print("=" * 40)
            
            # 打印系统状态
            print("\n系统状态:")
            print(f"  运行状态: {'运行中' if data['status']['running'] else '已停止'}")
            print(f"  上次更新: {data['status']['last_update']:.1f} 秒前")
            print(f"  运行时间: {data['status']['uptime']:.1f} 秒")
            
            # 打印关键指标
            print("\n系统资源:")
            if "system.memory_percent" in data["metrics"]:
                print(f"  内存使用率: {data['metrics']['system.memory_percent']:.1f}%")
            if "system.cpu_percent" in data["metrics"]:
                print(f"  CPU使用率: {data['metrics']['system.cpu_percent']:.1f}%")
            if "system.disk_percent" in data["metrics"]:
                print(f"  磁盘使用率: {data['metrics']['system.disk_percent']:.1f}%")
            if "system.process_memory" in data["metrics"]:
                print(f"  进程内存: {data['metrics']['system.process_memory']:.1f} MB")
            
            print("\n模型信息:")
            if "model.model_memory" in data["metrics"]:
                print(f"  模型内存: {data['metrics']['model.model_memory']:.1f} MB")
            if "model.model_type" in data["metrics"]:
                print(f"  模型类型: {data['metrics']['model.model_type']}")
            if "model.model_loaded" in data["metrics"]:
                print(f"  模型状态: {'已加载' if data['metrics']['model.model_loaded'] else '未加载'}")
            
            print("\n处理指标:")
            if "processing.cache_hit_rate" in data["metrics"]:
                print(f"  缓存命中率: {data['metrics']['processing.cache_hit_rate']:.1f}%")
            
            # 图表信息
            chart_files = data.get("charts", {})
            if chart_files:
                print("\n已生成图表:")
                for chart_id, chart_path in chart_files.items():
                    print(f"  - {chart_id}: {chart_path}")
            
            # 等待刷新
            print("\n" + "=" * 40)
            print(f"按 Ctrl+C 退出。{refresh_interval}秒后刷新...")
            time.sleep(refresh_interval)
    
    except KeyboardInterrupt:
        print("\n用户中断，停止监控...")
    finally:
        if duration > 0:  # 如果设置了时间限制，则停止看板
            dashboard.stop()
            print("监控看板已停止")

def export_dashboard_data(output_path: Optional[str] = None, format: str = "json"):
    """导出监控看板数据
    
    Args:
        output_path: 输出路径
        format: 导出格式，支持json和csv
    """
    # 获取看板实例
    dashboard = get_dashboard()
    if not dashboard.running:
        dashboard.start()
        # 等待收集一些数据
        time.sleep(5)
    
    # 获取数据
    data = dashboard.get_dashboard_data()
    metrics_history = dashboard.get_metrics_history()
    
    # 设置默认输出路径
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format == "json":
            output_path = f"dashboard_export_{timestamp}.json"
        else:
            output_path = f"dashboard_export_{timestamp}.csv"
    
    try:
        if format == "json":
            # 导出为JSON
            export_data = {
                "timestamp": time.time(),
                "current_metrics": data["metrics"],
                "metrics_history": metrics_history,
                "status": data["status"]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"监控数据已导出到: {output_path}")
            
        elif format == "csv":
            # 导出为CSV (只导出历史数据)
            import csv
            
            # 获取所有指标键
            all_keys = []
            for category in ["system", "model", "processing"]:
                for key in metrics_history["metrics"].keys():
                    if key.startswith(category):
                        all_keys.append(key)
            
            # 写入CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                header = ["timestamp"] + all_keys
                writer.writerow(header)
                
                # 写入数据行
                for i in range(len(metrics_history["timestamps"])):
                    row = [datetime.fromtimestamp(metrics_history["timestamps"][i]).strftime("%Y-%m-%d %H:%M:%S")]
                    
                    # 添加每个指标的值
                    for key in all_keys:
                        if key in metrics_history["metrics"] and i < len(metrics_history["metrics"][key]):
                            row.append(metrics_history["metrics"][key][i])
                        else:
                            row.append("")
                    
                    writer.writerow(row)
            
            logger.info(f"监控数据已导出到: {output_path}")
            
        else:
            logger.error(f"不支持的导出格式: {format}")
            
    except Exception as e:
        logger.error(f"导出数据时出错: {e}")
    finally:
        # 如果刚才启动了看板，现在停止它
        if not dashboard.running:
            dashboard.stop()

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 监控看板')
    
    # 模式选择
    parser.add_argument('--mode', '-m', choices=['web', 'cli', 'export'], default='web',
                      help='运行模式: web=网页界面, cli=命令行界面, export=导出数据')
    
    # Web模式参数
    parser.add_argument('--host', default='127.0.0.1',
                      help='Web服务器主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=8080,
                      help='Web服务器端口 (默认: 8080)')
    parser.add_argument('--debug', action='store_true',
                      help='启用Flask调试模式')
    
    # CLI模式参数
    parser.add_argument('--interval', '-i', type=int, default=5,
                      help='刷新间隔(秒) (默认: 5)')
    parser.add_argument('--duration', '-d', type=int, default=0,
                      help='运行时间(秒) (默认: 0=不限时间)')
    
    # 导出模式参数
    parser.add_argument('--output', '-o', 
                      help='导出文件路径')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                      help='导出格式 (默认: json)')
    
    # 通用参数
    parser.add_argument('--config', '-c',
                      help='配置文件路径')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 根据配置初始化看板
    if args.config and os.path.exists(args.config):
        logger.info(f"使用配置文件: {args.config}")
        dashboard = get_dashboard()
        # 在这里可以应用自定义配置
    
    # 根据模式运行
    if args.mode == 'web':
        logger.info(f"启动Web监控看板: http://{args.host}:{args.port}/")
        run_web_dashboard(host=args.host, port=args.port, debug=args.debug)
    
    elif args.mode == 'cli':
        logger.info(f"启动命令行监控看板，刷新间隔: {args.interval}秒")
        run_cli_dashboard(refresh_interval=args.interval, duration=args.duration)
    
    elif args.mode == 'export':
        logger.info(f"导出监控数据，格式: {args.format}")
        export_dashboard_data(output_path=args.output, format=args.format)

if __name__ == "__main__":
    main() 