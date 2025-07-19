#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模式版本管理系统简易演示脚本

演示如何使用模式加载工具简单地获取不同版本的模式配置，
以及切换版本、查看版本信息等功能。
"""

import os
import json
import argparse
from typing import Dict, Any
from loguru import logger

# 导入模式加载工具
from src.utils.pattern_loader import (
    get_current_pattern_config,
    get_recommended_combinations,
    get_pattern_parameters,
    get_evaluation_weights,
    get_platform_optimization,
    get_version_info,
    switch_pattern_version
)

# 设置日志
logger.add("logs/pattern_version_simple_demo.log", rotation="10 MB")


def print_header(text: str) -> None:
    """打印标题"""
    print("\n" + "=" * 80)
    print(" " + text.center(78) + " ")
    print("=" * 80)


def print_section(text: str) -> None:
    """打印分节"""
    print("\n" + "-" * 80)
    print(" " + text.center(78) + " ")
    print("-" * 80)


def show_version_info() -> None:
    """显示当前版本信息"""
    print_section("当前版本信息")
    
    info = get_version_info()
    
    if not info.get("has_version_manager", False):
        print("版本管理系统不可用")
        return
    
    print(f"版本: {info.get('version', '未知')}")
    print(f"创建日期: {info.get('created_at', '未知')}")
    print(f"描述: {info.get('description', '')}")
    print(f"作者: {info.get('author', '未知')}")
    print(f"数据大小: {info.get('data_size', '未知')}")
    
    print("\n语言覆盖率:")
    for lang, coverage in info.get("coverage", {}).items():
        print(f"  - {lang}: {coverage*100:.1f}%")


def show_current_config() -> None:
    """显示当前配置信息"""
    print_section("当前配置信息")
    
    config = get_current_pattern_config()
    
    # 打印模式类型
    print("模式类型:")
    for pattern_type in config.get("pattern_types", []):
        print(f"  - {pattern_type}")
    
    # 打印评估权重
    print("\n评估权重:")
    weights = get_evaluation_weights()
    for metric, weight in weights.items():
        print(f"  - {metric}: {weight}")
    
    # 打印推荐组合
    print("\n推荐模式组合:")
    combinations = get_recommended_combinations()
    for combo in combinations:
        print(f"  - {combo['name']}: {', '.join(combo['patterns'])}")
        print(f"    描述: {combo['description']}")
    
    # 打印平台优化参数
    print("\n平台优化参数:")
    platforms = get_platform_optimization()
    for platform, params in platforms.items():
        print(f"  - {platform}:")
        print(f"    推荐时长: {params.get('recommended_duration', [])}")
        print(f"    关键节点: {params.get('key_positions', [])}")


def show_pattern_details() -> None:
    """显示模式详情"""
    print_section("模式类型详情")
    
    config = get_current_pattern_config()
    pattern_types = config.get("pattern_types", [])
    
    for pattern_type in pattern_types:
        print(f"\n{pattern_type}模式:")
        
        params = get_pattern_parameters(pattern_type)
        if not params:
            print("  无详细参数")
            continue
        
        for param_name, param_value in params.items():
            print(f"  - {param_name}: {param_value}")


def demo_switch_version() -> None:
    """演示切换版本"""
    print_section("切换版本演示")
    
    # 获取当前版本信息
    current_info = get_version_info()
    current_version = current_info.get("version", "未知")
    
    print(f"当前版本: {current_version}")
    
    # 尝试切换到v1.1
    target_version = "v1.1"
    print(f"\n尝试切换到 {target_version}")
    
    success = switch_pattern_version(target_version)
    if success:
        print(f"成功切换到版本 {target_version}")
        
        # 显示切换后的版本信息
        new_info = get_version_info()
        print(f"新版本: {new_info.get('version', '未知')}")
        print(f"创建日期: {new_info.get('created_at', '未知')}")
        print(f"描述: {new_info.get('description', '')}")
    else:
        print(f"切换版本失败")
    
    # 切换回原版本
    print(f"\n切换回版本 {current_version}")
    switch_pattern_version(current_version)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="模式版本管理简易演示")
    parser.add_argument("--info", action="store_true", help="显示当前版本信息")
    parser.add_argument("--config", action="store_true", help="显示当前配置")
    parser.add_argument("--details", action="store_true", help="显示模式详情")
    parser.add_argument("--switch", action="store_true", help="演示切换版本")
    parser.add_argument("--all", action="store_true", help="显示所有信息")
    args = parser.parse_args()
    
    print_header("模式版本管理系统简易演示")
    
    # 根据参数显示相应信息
    if args.info or args.all:
        show_version_info()
    
    if args.config or args.all:
        show_current_config()
        
    if args.details or args.all:
        show_pattern_details()
        
    if args.switch or args.all:
        demo_switch_version()
    
    # 如果没有指定参数，显示基本信息
    if not any([args.info, args.config, args.details, args.switch, args.all]):
        show_version_info()
        print("\n使用 --help 查看更多选项")
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 