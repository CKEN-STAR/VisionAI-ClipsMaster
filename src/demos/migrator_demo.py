#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置迁移器演示脚本

展示如何使用配置迁移器在不同版本的配置文件间进行迁移，
包括字段映射、值转换、结构重组等。
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
import pprint
import datetime

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# 导入配置迁移器
from src.config.migrator import (
    migrate_legacy_config,
    get_config_migrator,
    ConfigMigrationRule
)

# 导入日志工具
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("migrator_demo")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("migrator_demo")

# 配置文件路径
CONFIG_DIR = os.path.join(root_dir, "configs")
SAMPLE_DIR = os.path.join(CONFIG_DIR, "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def create_sample_configs():
    """创建示例配置文件"""
    # 创建1.0版本示例配置
    v1_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "1.0",
        "video_height": 720,
        "video.quality": "high",
        "save_folder": "D:/Videos/Output",
        "audio_volume": 1.0,
        "audio_normalize": True,
        "processing": {
            "threads": 2
        },
        "project": {
            "name": "演示项目",
            "description": "这是一个演示迁移功能的项目",
            "tags": "视频,演示,迁移",
            "created": "2023-01-01T10:00:00"
        },
        "effects": {
            "enabled": False,
            "blur": 0.2,
            "contrast": 1.1
        },
        "sequence": {
            "duration": 120,
            "frame_rate": 30
        }
    }
    
    # 创建2.0版本示例配置（手动迁移）
    v2_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "2.0",
        "export": {
            "resolution": "720p"
        },
        "storage": {
            "output_path": "D:/Videos/Output"
        },
        "audio": {
            "volume": 1.0,
            "normalize": True
        },
        "performance": {
            "cpu_threads": 4
        },
        "project": {
            "name": "演示项目",
            "description": "这是一个演示迁移功能的项目",
            "tags": "视频,演示,迁移",
            "created": "2023-01-01T10:00:00"
        },
        "effects": {
            "enabled": True,
            "blur": 0.2,
            "contrast": 1.1
        },
        "sequence": {
            "duration": 120,
            "frame_rate": 30
        },
        "_meta": {
            "version": "2.0",
            "updated_at": "2023-06-01T15:30:00"
        }
    }
    
    # 创建2.5版本示例配置（手动迁移）
    v2_5_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "2.5",
        "export": {
            "resolution": "1080p",
            "frame_rate": 30
        },
        "storage": {
            "output_path": "D:/Videos/Output"
        },
        "audio": {
            "volume": 1.0,
            "normalize": True
        },
        "performance": {
            "cpu_threads": 4
        },
        "metadata": {
            "project_name": "演示项目",
            "description": "这是一个演示迁移功能的项目",
            "tags": ["视频", "演示", "迁移"],
            "created_at": "2023-01-01T10:00:00"
        },
        "effects": {
            "enabled": True,
            "blur": 0.2,
            "contrast": 1.1
        },
        "sequence": {
            "duration": 120,
            "frame_rate": 30
        },
        "_meta": {
            "version": "2.5",
            "updated_at": "2023-08-15T09:45:00"
        }
    }
    
    # 写入示例配置文件
    config_files = {
        "v1_config.json": v1_config,
        "v2_config.json": v2_config,
        "v2_5_config.json": v2_5_config
    }
    
    for filename, config in config_files.items():
        file_path = os.path.join(SAMPLE_DIR, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"创建示例配置文件: {file_path}")
    
    return v1_config, v2_config, v2_5_config


def demonstrate_automatic_migration(v1_config):
    """演示自动迁移功能"""
    print("\n自动迁移演示")
    print("=" * 60)
    
    migrator = get_config_migrator()
    
    try:
        # 1.0版本配置迁移到2.0版本
        print("\n1. 从1.0版本迁移到2.0版本:")
        v2_config = migrator.migrate_legacy_config(v1_config, "1.0", "2.0")
        print_config_diff(v1_config, v2_config)
        
        # 2.0版本配置迁移到2.5版本
        print("\n2. 从2.0版本迁移到2.5版本:")
        v2_5_config = migrator.migrate_legacy_config(v2_config, "2.0", "2.5")
        print_config_diff(v2_config, v2_5_config)
        
        # 2.5版本配置迁移到3.0版本
        print("\n3. 从2.5版本迁移到3.0版本:")
        v3_config = migrator.migrate_legacy_config(v2_5_config, "2.5", "3.0")
        print_config_diff(v2_5_config, v3_config)
        
        # 直接从1.0版本迁移到3.0版本
        print("\n4. 直接从1.0版本迁移到3.0版本:")
        v3_direct_config = migrator.migrate_legacy_config(v1_config, "1.0", "3.0")
        print_config_diff(v1_config, v3_direct_config)
        
    except Exception as e:
        print(f"迁移过程出错: {str(e)}")


def demonstrate_custom_rule():
    """演示创建自定义迁移规则"""
    print("\n自定义迁移规则演示")
    print("=" * 60)
    
    # 创建一个自定义配置
    custom_config = {
        "app_version": "custom-1.0",
        "canvas": {
            "width": 1920,
            "height": 1080,
            "background": "#000000"
        },
        "render_settings": {
            "quality": "best",
            "format": "mp4",
            "codec": "h264",
            "bitrate": 5000
        },
        "project_info": {
            "title": "自定义项目",
            "author": "测试用户",
            "creation_date": "2023-11-15"
        }
    }
    
    print("\n原始自定义配置:")
    print(json.dumps(custom_config, indent=2, ensure_ascii=False))
    
    # 创建自定义迁移规则
    custom_rule = ConfigMigrationRule("custom-1.0", "standard-3.0")
    
    # 添加字段映射
    custom_rule.add_field_mapping("canvas.width", "export.width")
    custom_rule.add_field_mapping("canvas.height", "export.height")
    custom_rule.add_field_mapping("render_settings.quality", "export.quality")
    custom_rule.add_field_mapping("render_settings.format", "export.format")
    custom_rule.add_field_mapping("render_settings.codec", "export.codec")
    custom_rule.add_field_mapping("render_settings.bitrate", "export.bitrate")
    
    # 添加项目信息映射
    custom_rule.add_field_mapping("project_info.title", "metadata.project_name")
    custom_rule.add_field_mapping("project_info.author", "metadata.author")
    
    # 添加日期格式转换
    def convert_date(date_str):
        try:
            # 假设输入格式为YYYY-MM-DD
            if isinstance(date_str, str) and len(date_str) == 10:
                year, month, day = date_str.split("-")
                return f"{year}-{month}-{day}T00:00:00"
            return date_str
        except Exception:
            return datetime.datetime.now().isoformat()
    
    custom_rule.add_field_mapping(
        "project_info.creation_date", 
        "metadata.created_at",
        transform_func=convert_date
    )
    
    # 添加分辨率检测和标准化
    def detect_resolution(config):
        result = {}
        
        # 如果有宽高信息，添加标准分辨率名称
        if "export" in config and "width" in config["export"] and "height" in config["export"]:
            width = config["export"]["width"]
            height = config["export"]["height"]
            
            # 检测标准分辨率
            if width == 1920 and height == 1080:
                result["resolution"] = "1080p"
            elif width == 3840 and height == 2160:
                result["resolution"] = "4K"
            elif width == 1280 and height == 720:
                result["resolution"] = "720p"
            else:
                # 非标准分辨率，使用高度值
                result["resolution"] = f"{height}p"
            
            # 添加到export节点
            if "export" not in result:
                result["export"] = {}
            result["export"]["resolution"] = result["resolution"]
        
        return result
    
    # 添加后处理器
    custom_rule.add_postprocessor(lambda config: {**config, **detect_resolution(config)})
    
    # 应用自定义规则
    try:
        migrated_config = custom_rule.apply(custom_config)
        
        print("\n迁移后的标准配置:")
        print(json.dumps(migrated_config, indent=2, ensure_ascii=False))
        
        # 注册规则到全局迁移器
        migrator = get_config_migrator()
        migrator.add_rule(custom_rule)
        
        print("\n自定义规则已注册到全局迁移器")
        
    except Exception as e:
        print(f"应用自定义规则失败: {str(e)}")


def demonstrate_config_file_migration():
    """演示配置文件迁移"""
    print("\n配置文件迁移演示")
    print("=" * 60)
    
    # 使用示例配置文件
    v1_file = os.path.join(SAMPLE_DIR, "v1_config.json")
    
    if not os.path.exists(v1_file):
        print(f"示例文件不存在: {v1_file}")
        return
    
    # 加载配置
    with open(v1_file, 'r', encoding='utf-8') as f:
        v1_config = json.load(f)
    
    # 迁移到最新版本
    try:
        migrator = get_config_migrator()
        latest_config = migrator.migrate_legacy_config(v1_config, "1.0")
        
        # 保存迁移后的文件
        output_file = os.path.join(SAMPLE_DIR, "migrated_latest.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(latest_config, f, indent=2, ensure_ascii=False)
        
        print(f"已将 {v1_file} 迁移到最新版本")
        print(f"迁移结果保存至: {output_file}")
        print("\n迁移后的配置:")
        print(json.dumps(latest_config, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"文件迁移失败: {str(e)}")


def print_config_diff(before, after):
    """打印配置差异"""
    # 这里使用一个简单的方法来显示差异
    # 在实际项目中，可以使用更复杂的差异显示库
    
    print("\n变更前:")
    print(json.dumps(before, indent=2, ensure_ascii=False))
    
    print("\n变更后:")
    print(json.dumps(after, indent=2, ensure_ascii=False))
    
    # 打印元数据
    if "_meta" in after:
        print("\n迁移元数据:")
        for key, value in after["_meta"].items():
            print(f"  {key}: {value}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="配置迁移器演示")
    parser.add_argument("--create-samples", action="store_true", help="只创建示例配置文件")
    parser.add_argument("--auto-migration", action="store_true", help="演示自动迁移")
    parser.add_argument("--custom-rule", action="store_true", help="演示自定义规则")
    parser.add_argument("--file-migration", action="store_true", help="演示文件迁移")
    args = parser.parse_args()
    
    print("VisionAI-ClipsMaster 配置迁移器演示")
    print("=" * 60)
    
    # 创建示例配置
    v1_config, v2_config, v2_5_config = create_sample_configs()
    
    if args.create_samples:
        print("已创建示例配置文件")
        return
    
    # 如果没有指定参数，运行所有演示
    if not any([args.auto_migration, args.custom_rule, args.file_migration]):
        args.auto_migration = True
        args.custom_rule = True
        args.file_migration = True
    
    # 演示自动迁移
    if args.auto_migration:
        demonstrate_automatic_migration(v1_config)
    
    # 演示自定义规则
    if args.custom_rule:
        demonstrate_custom_rule()
    
    # 演示文件迁移
    if args.file_migration:
        demonstrate_config_file_migration()
    
    print("\n配置迁移器演示完成")


if __name__ == "__main__":
    main() 