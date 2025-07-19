#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 监控看板启动器

简单的启动脚本，用于启动监控看板。
支持命令行参数，可以选择Web界面或命令行界面。
"""

import sys
import os
import argparse
from pathlib import Path

# 确保src目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入启动函数
from src.dashboard.monitor_dashboard import get_dashboard
from src.dashboard.web_dashboard import run_web_dashboard
from src.dashboard.cli import run_cli_dashboard, export_dashboard_data

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 监控看板启动器')
    
    # 界面选择
    parser.add_argument('--ui', '-u', choices=['web', 'cli', 'export'], default='web',
                      help='界面类型: web=网页界面, cli=命令行界面, export=导出数据 (默认: web)')
    
    # Web界面参数
    parser.add_argument('--host', default='localhost',
                      help='Web服务器主机地址 (默认: localhost)')
    parser.add_argument('--port', '-p', type=int, default=8080,
                      help='Web服务器端口 (默认: 8080)')
    
    # 命令行界面参数
    parser.add_argument('--interval', '-i', type=int, default=5,
                      help='刷新间隔(秒) (默认: 5)')
    parser.add_argument('--duration', '-d', type=int, default=0,
                      help='运行时间(秒) (默认: 0=不限时间)')
    
    # 导出参数
    parser.add_argument('--output', '-o', 
                      help='导出文件路径')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                      help='导出格式 (默认: json)')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    print("启动 VisionAI-ClipsMaster 监控看板...")
    
    try:
        # 根据参数启动不同界面
        if args.ui == 'web':
            print(f"启动Web界面: http://{args.host}:{args.port}/")
            run_web_dashboard(host=args.host, port=args.port)
            
        elif args.ui == 'cli':
            print(f"启动命令行界面，刷新间隔: {args.interval}秒")
            duration = args.duration if args.duration > 0 else float('inf')
            run_cli_dashboard(refresh_interval=args.interval, duration=duration)
            
        elif args.ui == 'export':
            print(f"导出监控数据，格式: {args.format}")
            export_dashboard_data(output_path=args.output, format=args.format)
            print("数据导出完成")
            
    except KeyboardInterrupt:
        print("\n用户中断，正在关闭...")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        # 确保停止监控看板
        dashboard = get_dashboard()
        if dashboard.running:
            dashboard.stop()
            print("监控看板已停止")

if __name__ == "__main__":
    main() 