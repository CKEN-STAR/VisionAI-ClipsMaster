#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置验证器演示脚本

展示如何使用配置验证器验证不同类型的配置和配置文件。
"""

import os
import sys
import json
import yaml
from pathlib import Path
import argparse
import colorama
from colorama import Fore, Style

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# 导入配置验证器
from src.config import (
    validate_config,
    validate_export_config,
    validate_storage_config,
    validate_model_config,
    validate_system_config,
    validate_config_file,
    ConfigValidationError
)


def print_separator(title=None):
    """打印分隔线"""
    width = 80
    if title:
        text = f" {title} "
        padding = (width - len(text)) // 2
        print("=" * padding + text + "=" * padding)
    else:
        print("=" * width)


def print_result(is_valid, errors=None):
    """打印验证结果"""
    if is_valid:
        print(f"{Fore.GREEN}✓ 配置有效{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ 配置无效{Style.RESET_ALL}")
        if errors:
            for i, error in enumerate(errors, 1):
                print(f"{Fore.YELLOW}  {i}. {error}{Style.RESET_ALL}")


def demo_export_config():
    """演示导出配置验证"""
    print_separator("导出配置验证")
    
    # 有效配置
    valid_config = {
        "frame_rate": 30,
        "resolution": "1080p",
        "codec": "h264",
        "format": "mp4",
        "output_path": "~/videos/output"
    }
    print(f"有效配置:\n{json.dumps(valid_config, indent=2, ensure_ascii=False)}")
    errors = validate_export_config(valid_config)
    print_result(len(errors) == 0, errors)
    
    print()
    
    # 无效配置
    invalid_config = {
        "frame_rate": 70,  # 超过最大允许帧率60
        "resolution": "8K",  # 不支持的分辨率
        "codec": "h264",
        "format": "mp4",
        "output_path": "~/videos/output"
    }
    print(f"无效配置:\n{json.dumps(invalid_config, indent=2, ensure_ascii=False)}")
    errors = validate_export_config(invalid_config)
    print_result(len(errors) == 0, errors)


def demo_storage_config():
    """演示存储配置验证"""
    print_separator("存储配置验证")
    
    # 有效配置
    valid_config = {
        "output_path": "~/videos/output",
        "cache_path": "~/videos/cache",
        "cache_size_limit": 10000
    }
    print(f"有效配置:\n{json.dumps(valid_config, indent=2, ensure_ascii=False)}")
    errors = validate_storage_config(valid_config)
    print_result(len(errors) == 0, errors)
    
    print()
    
    # 无效配置
    invalid_config = {
        "output_path": "~/videos/output",
        "cache_path": "~/videos/cache",
        "cache_size_limit": 60000,  # 超过最大缓存限制
        "cloud_storage": {
            "enabled": True,
            "type": "s3",
            "bucket": "my-bucket"
            # 缺少必填字段 access_key 和 secret_key
        }
    }
    print(f"无效配置:\n{json.dumps(invalid_config, indent=2, ensure_ascii=False)}")
    errors = validate_storage_config(invalid_config)
    print_result(len(errors) == 0, errors)


def demo_model_config():
    """演示模型配置验证"""
    print_separator("模型配置验证")
    
    # 有效配置
    valid_config = {
        "language_mode": "auto",
        "quantization": "Q4_K_M",
        "context_length": 2048,
        "generation_params": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    print(f"有效配置:\n{json.dumps(valid_config, indent=2, ensure_ascii=False)}")
    errors = validate_model_config(valid_config)
    print_result(len(errors) == 0, errors)
    
    print()
    
    # 无效配置
    invalid_config = {
        "language_mode": "jp",  # 不支持的语言模式
        "quantization": "Q3",   # 不支持的量化等级
        "context_length": 10000,  # 超过最大上下文长度
        "generation_params": {
            "temperature": 2.5,  # 超过最大温度值
            "top_p": 1.5   # 超过最大top_p值
        }
    }
    print(f"无效配置:\n{json.dumps(invalid_config, indent=2, ensure_ascii=False)}")
    errors = validate_model_config(invalid_config)
    print_result(len(errors) == 0, errors)


def demo_system_config():
    """演示系统配置验证"""
    print_separator("系统配置验证")
    
    # 有效配置
    valid_config = {
        "num_threads": 4,
        "memory_limit": 4096,
        "log_level": "info",
        "gpu": {
            "enabled": True,
            "memory_limit": 2048
        }
    }
    print(f"有效配置:\n{json.dumps(valid_config, indent=2, ensure_ascii=False)}")
    errors = validate_system_config(valid_config)
    print_result(len(errors) == 0, errors)
    
    print()
    
    # 无效配置
    invalid_config = {
        "num_threads": 0,  # 低于最小线程数
        "memory_limit": 256,  # 低于最小内存限制
        "log_level": "trace",  # 不支持的日志级别
        "gpu": {
            "enabled": "yes",  # 应该是布尔值
            "memory_limit": 512  # 低于最小GPU内存限制
        }
    }
    print(f"无效配置:\n{json.dumps(invalid_config, indent=2, ensure_ascii=False)}")
    errors = validate_system_config(invalid_config)
    print_result(len(errors) == 0, errors)


def demo_complete_config():
    """演示完整配置验证"""
    print_separator("完整配置验证")
    
    # 完整有效配置
    valid_config = {
        "export": {
            "frame_rate": 30,
            "resolution": "1080p",
            "codec": "h264",
            "format": "mp4",
            "output_path": "~/videos/output"
        },
        "storage": {
            "output_path": "~/videos/output",
            "cache_path": "~/videos/cache",
            "cache_size_limit": 10000
        },
        "model": {
            "language_mode": "auto",
            "quantization": "Q4_K_M",
            "context_length": 2048,
            "generation_params": {
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        "system": {
            "num_threads": 4,
            "memory_limit": 4096,
            "log_level": "info"
        }
    }
    
    print("完整有效配置验证...")
    errors = validate_config(valid_config)
    print_result(len(errors) == 0, errors)
    
    print()
    
    # 完整无效配置（多处错误）
    invalid_config = valid_config.copy()
    invalid_config["export"]["frame_rate"] = 70  # 超过最大允许帧率
    invalid_config["model"]["language_mode"] = "jp"  # 不支持的语言模式
    invalid_config["system"]["log_level"] = "trace"  # 不支持的日志级别
    
    print("完整无效配置验证（多处错误）...")
    errors = validate_config(invalid_config)
    print_result(len(errors) == 0, errors)


def demo_config_file():
    """演示配置文件验证"""
    print_separator("配置文件验证")
    
    # 创建临时目录
    temp_dir = root_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # 有效配置
    valid_config = {
        "export": {
            "frame_rate": 30,
            "resolution": "1080p",
            "codec": "h264",
            "format": "mp4"
        },
        "storage": {
            "output_path": "~/videos/output",
            "cache_path": "~/videos/cache"
        },
        "model": {
            "language_mode": "auto",
            "quantization": "Q4_K_M",
            "context_length": 2048
        },
        "system": {
            "num_threads": 4,
            "memory_limit": 4096
        }
    }
    
    # 无效配置
    invalid_config = {
        "export": {
            "frame_rate": 70,
            "resolution": "8K"
        },
        "model": {
            "language_mode": "jp"
        }
    }
    
    # 写入配置文件
    valid_json_file = temp_dir / "valid_config.json"
    valid_yaml_file = temp_dir / "valid_config.yaml"
    invalid_json_file = temp_dir / "invalid_config.json"
    
    with open(valid_json_file, 'w', encoding='utf-8') as f:
        json.dump(valid_config, f, indent=2, ensure_ascii=False)
    
    with open(valid_yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(valid_config, f, allow_unicode=True)
    
    with open(invalid_json_file, 'w', encoding='utf-8') as f:
        json.dump(invalid_config, f, indent=2, ensure_ascii=False)
    
    # 验证JSON配置文件
    print(f"验证JSON配置文件: {valid_json_file.name}")
    is_valid, errors = validate_config_file(str(valid_json_file))
    print_result(is_valid, errors)
    
    print()
    
    # 验证YAML配置文件
    print(f"验证YAML配置文件: {valid_yaml_file.name}")
    is_valid, errors = validate_config_file(str(valid_yaml_file))
    print_result(is_valid, errors)
    
    print()
    
    # 验证无效配置文件
    print(f"验证无效配置文件: {invalid_json_file.name}")
    is_valid, errors = validate_config_file(str(invalid_json_file))
    print_result(is_valid, errors)
    
    print()
    
    # 验证不存在的配置文件
    print("验证不存在的配置文件: non_existent_config.json")
    is_valid, errors = validate_config_file("non_existent_config.json")
    print_result(is_valid, errors)
    
    # 清理临时文件
    valid_json_file.unlink()
    valid_yaml_file.unlink()
    invalid_json_file.unlink()
    
    try:
        temp_dir.rmdir()
    except OSError:
        pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="配置验证器演示")
    parser.add_argument("--demo", choices=["export", "storage", "model", "system", "complete", "file", "all"], 
                        default="all", help="要运行的演示类型")
    args = parser.parse_args()
    
    # 初始化colorama
    colorama.init()
    
    print("配置验证器演示\n")
    print("此演示展示了如何使用配置验证器验证不同类型的配置和配置文件。")
    print("验证器可以检测出配置中的各种错误，如数值超出范围、类型错误、缺少必填字段等。")
    print()
    
    if args.demo == "export" or args.demo == "all":
        demo_export_config()
        print()
    
    if args.demo == "storage" or args.demo == "all":
        demo_storage_config()
        print()
    
    if args.demo == "model" or args.demo == "all":
        demo_model_config()
        print()
    
    if args.demo == "system" or args.demo == "all":
        demo_system_config()
        print()
    
    if args.demo == "complete" or args.demo == "all":
        demo_complete_config()
        print()
    
    if args.demo == "file" or args.demo == "all":
        demo_config_file()
    
    # 重置colorama设置
    colorama.deinit()


if __name__ == "__main__":
    main() 