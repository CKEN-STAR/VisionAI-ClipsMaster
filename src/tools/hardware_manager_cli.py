#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""硬件降级策略管理命令行工具

该工具提供命令行界面，用于管理系统的硬件降级策略、内存使用和模型配置。
"""

import os
import sys
import argparse
import json
from typing import Dict, Any

# 确保可以导入项目模块
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from src.core.hardware_manager import (
    initialize_hardware_strategy,
    get_hardware_strategy,
    set_adaptive_mode,
    get_hardware_status,
    optimize_for_language,
    shutdown
)
from src.core.hardware_degradation_strategy import AdaptiveMode, HardwareProfile


def print_status(status: Dict[str, Any]) -> None:
    """打印状态信息
    
    Args:
        status: 状态信息字典
    """
    print("\n--- 硬件状态 ---")
    print(f"硬件配置: {status.get('hardware_profile', '未知')}")
    print(f"自适应模式: {status.get('adaptive_mode', '未知')}")
    print(f"监控状态: {'运行中' if status.get('monitoring_active', False) else '已停止'}")
    print(f"降级级别: {status.get('degradation_level', '未知')}")
    
    print("\n--- 组件配置 ---")
    components = status.get('components_state', {})
    for key, value in components.items():
        print(f"{key}: {value}")
    
    print("\n--- 资源状态 ---")
    resources = status.get('resource_state', {})
    memory = resources.get('memory', {})
    if memory:
        print(f"内存总量: {memory.get('total_gb', 0):.2f} GB")
        print(f"可用内存: {memory.get('available_gb', 0):.2f} GB")
        print(f"内存使用率: {memory.get('percent', 0) * 100:.1f}%")
    
    print(f"CPU使用率: {resources.get('cpu_percent', 0):.1f}%")

def print_json(data: Dict[str, Any]) -> None:
    """以JSON格式打印数据
    
    Args:
        data: 要打印的数据
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="VisionAI-ClipsMaster 硬件降级策略管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # status命令
    status_parser = subparsers.add_parser("status", help="显示当前硬件状态")
    status_parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    
    # mode命令
    mode_parser = subparsers.add_parser("mode", help="设置自适应模式")
    mode_parser.add_argument(
        "mode_name",
        choices=[mode.value for mode in AdaptiveMode],
        help="要设置的模式"
    )
    
    # optimize命令
    optimize_parser = subparsers.add_parser("optimize", help="为特定语言优化设置")
    optimize_parser.add_argument(
        "language",
        choices=["zh", "en"],
        help="目标语言 (zh: 中文, en: 英文)"
    )
    optimize_parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    
    # reset命令
    reset_parser = subparsers.add_parser("reset", help="重置硬件策略到默认设置")
    
    # memory命令
    memory_parser = subparsers.add_parser("memory", help="显示内存使用详情")
    memory_parser.add_argument("--json", action="store_true", help="以JSON格式输出")
    
    # 解析参数
    args = parser.parse_args()
    
    # 初始化硬件策略
    try:
        strategy = initialize_hardware_strategy()
    except Exception as e:
        logger.error(f"初始化硬件降级策略失败: {e}")
        sys.exit(1)
    
    try:
        # 根据命令执行相应操作
        if args.command == "status" or args.command is None:
            status = get_hardware_status()
            if args.json if hasattr(args, 'json') else False:
                print_json(status)
            else:
                print_status(status)
        
        elif args.command == "mode":
            mode = AdaptiveMode(args.mode_name)
            success = set_adaptive_mode(mode)
            if success:
                print(f"已成功切换到{mode.value}模式")
                status = get_hardware_status()
                print_status(status)
            else:
                print(f"切换模式失败")
                sys.exit(1)
        
        elif args.command == "optimize":
            result = optimize_for_language(args.language)
            if result.get("success", False):
                print(f"已为{args.language}语言优化硬件设置")
                if args.json:
                    print_json(result)
                else:
                    print_status(get_hardware_status())
                    print("\n优化设置:")
                    for key, value in result.get("optimized_settings", {}).items():
                        print(f"{key}: {value}")
            else:
                print(f"优化失败: {result.get('error', '未知错误')}")
                sys.exit(1)
        
        elif args.command == "reset":
            strategy.reset()
            print("已重置硬件策略到默认设置")
            print_status(get_hardware_status())
        
        elif args.command == "memory":
            memory_info = strategy._get_memory_info()
            if args.json:
                print_json(memory_info)
            else:
                print("\n--- 内存使用详情 ---")
                print(f"总内存: {memory_info['total_gb']:.2f} GB")
                print(f"可用内存: {memory_info['available_gb']:.2f} GB")
                print(f"已用内存: {memory_info['used'] / (1024**3):.2f} GB")
                print(f"内存使用率: {memory_info['percent'] * 100:.1f}%")
    
    except Exception as e:
        logger.error(f"操作失败: {e}")
        sys.exit(1)
    finally:
        # 关闭硬件策略
        shutdown()


if __name__ == "__main__":
    main() 