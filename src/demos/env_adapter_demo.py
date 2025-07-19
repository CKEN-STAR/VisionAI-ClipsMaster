#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境适配器演示脚本

展示如何使用环境适配器自动调整配置以适应不同的操作系统和硬件环境。
"""

import os
import sys
import json
import yaml
import platform
import argparse
import logging
from pathlib import Path
import pprint

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# 导入环境适配器
from src.config import (
    adapt_for_environment,
    get_adapted_config,
    detect_system_info,
    get_optimal_cpu_threads,
    get_optimal_memory_limit,
    get_optimal_temp_dir
)

# 导入日志工具
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("env_adapter_demo")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("env_adapter_demo")

# 配置文件路径
CONFIG_DIR = os.path.join(root_dir, "configs")
TEST_CONFIG_PATH = os.path.join(CONFIG_DIR, "env_test_config.json")


def create_test_config():
    """创建测试配置文件"""
    # 创建测试配置
    test_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "1.0.0",
        "storage": {
            "temp_dir": "./temp",
            "cache_enabled": True
        },
        "performance": {
            "cpu_threads": 4,
            "memory_limit_mb": 2048
        },
        "gpu": {
            "enabled": True,
            "device": "auto",
            "memory_limit_mb": 1024
        },
        "ui": {
            "language": "auto",
            "theme": "dark"
        },
        "logging": {
            "level": "auto",
            "file_rotation": 7
        }
    }
    
    # 写入JSON配置文件
    os.makedirs(os.path.dirname(TEST_CONFIG_PATH), exist_ok=True)
    with open(TEST_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"创建了测试配置文件: {TEST_CONFIG_PATH}")
    return test_config


def print_system_info(system_info):
    """打印系统信息"""
    print("\n系统信息:")
    print("-" * 60)
    
    # 操作系统信息
    print(f"操作系统:      {system_info['os']['system']} {system_info['os']['release']} ({system_info['os']['platform']})")
    print(f"架构:          {system_info['os']['architecture']} {system_info['os']['machine']}")
    print(f"处理器:        {system_info['os']['processor']}")
    
    # Python信息
    print(f"Python版本:    {system_info['python']['version']} ({system_info['python']['implementation']})")
    
    # 硬件信息
    cpu_count = system_info['hardware']['cpu_count']
    logical_cpu_count = system_info['hardware']['logical_cpu_count']
    print(f"CPU:           {cpu_count}核心 ({logical_cpu_count}逻辑处理器)")
    
    # 内存信息
    total_memory_gb = system_info['hardware']['memory_total'] / (1024**3)
    available_memory_gb = system_info['hardware']['memory_available'] / (1024**3)
    print(f"内存:          总计 {total_memory_gb:.2f} GB, 可用 {available_memory_gb:.2f} GB")
    
    # 磁盘信息
    total_disk_gb = system_info['hardware']['disk_total'] / (1024**3)
    free_disk_gb = system_info['hardware']['disk_free'] / (1024**3)
    print(f"磁盘:          总计 {total_disk_gb:.2f} GB, 可用 {free_disk_gb:.2f} GB")
    
    # GPU信息
    if "gpu" in system_info['hardware']:
        gpu_info = system_info['hardware']['gpu']
        print(f"GPU:           类型: {gpu_info.get('type', 'Unknown')}, 数量: {gpu_info.get('count', '?')}")
        if 'name' in gpu_info:
            print(f"                型号: {gpu_info['name']}")
        if 'memory_total' in gpu_info:
            gpu_mem_gb = gpu_info['memory_total'] / (1024**3)
            print(f"                显存: {gpu_mem_gb:.2f} GB")
    else:
        print(f"GPU:           未检测到")
    
    # 网络信息
    print(f"主机名:        {system_info['network']['hostname']}")
    print(f"网络连接:      {'已连接' if system_info['network']['has_internet'] else '未连接'}")
    
    # 用户信息
    print(f"用户:          {system_info['user']['username']}")
    
    # 路径信息
    print(f"临时目录:      {system_info['paths']['temp_dir']}")
    print(f"应用数据目录:  {system_info['paths']['app_data_dir']}")


def print_config_comparison(original_config, adapted_config):
    """打印原始配置和适配后配置的对比"""
    print("\n配置对比:")
    print("-" * 60)
    
    def print_diff(orig, adapted, path=""):
        """递归打印配置差异"""
        if isinstance(adapted, dict):
            for key in sorted(set(list(orig.keys()) + list(adapted.keys()))):
                new_path = f"{path}.{key}" if path else key
                
                if key not in orig:
                    print(f"+ {new_path}: {adapted[key]}")
                elif key not in adapted:
                    print(f"- {new_path}: {orig[key]}")
                elif orig[key] != adapted[key]:
                    if isinstance(orig[key], dict) and isinstance(adapted[key], dict):
                        print_diff(orig[key], adapted[key], new_path)
                    else:
                        print(f"  {new_path}: {orig[key]} -> {adapted[key]}")
    
    print_diff(original_config, adapted_config)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="环境适配器演示")
    parser.add_argument("--show-system-info", action="store_true", help="显示系统信息")
    parser.add_argument("--show-optimal-values", action="store_true", help="显示最佳配置值")
    parser.add_argument("--test-config", action="store_true", help="创建和测试配置文件")
    parser.add_argument("--config-file", help="指定要适配的配置文件路径")
    args = parser.parse_args()
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    print("VisionAI-ClipsMaster 环境适配器演示")
    print("=" * 60)
    
    # 如果没有指定任何参数，默认显示所有内容
    if not any([args.show_system_info, args.show_optimal_values, args.test_config, args.config_file]):
        args.show_system_info = True
        args.show_optimal_values = True
        args.test_config = True
    
    # 显示系统信息
    if args.show_system_info:
        system_info = detect_system_info()
        print_system_info(system_info)
    
    # 显示最佳配置值
    if args.show_optimal_values:
        print("\n最佳配置值:")
        print("-" * 60)
        print(f"CPU线程数:     {get_optimal_cpu_threads()}")
        print(f"内存限制(MB):  {get_optimal_memory_limit()}")
        print(f"临时目录:      {get_optimal_temp_dir()}")
    
    # 测试配置文件
    if args.test_config:
        original_config = create_test_config()
        adapted_config = get_adapted_config(TEST_CONFIG_PATH)
        print_config_comparison(original_config, adapted_config)
    
    # 适配指定配置文件
    if args.config_file:
        try:
            config_path = args.config_file
            print(f"\n适配配置文件: {config_path}")
            print("-" * 60)
            
            # 加载原始配置
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    original_config = json.load(f)
                elif config_path.endswith(('.yaml', '.yml')):
                    original_config = yaml.safe_load(f)
                else:
                    print(f"不支持的文件格式: {config_path}")
                    return
            
            # 获取适配后的配置
            adapted_config = get_adapted_config(config_path)
            
            # 打印对比
            print_config_comparison(original_config, adapted_config)
        except Exception as e:
            print(f"处理配置文件时出错: {e}")
    
    print("\n环境适配器演示完成")


if __name__ == "__main__":
    main() 