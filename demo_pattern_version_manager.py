#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
模式版本管理系统演示脚本

演示如何使用模式版本管理系统来管理和切换不同版本的叙事模式库，
包括创建新版本、比较版本差异、查看版本元数据等功能。
"""

import os
import json
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger
import yaml

# 导入版本管理模块
from src.version_management.pattern_version_manager import (
    PatternVersionManager,
    get_latest_version,
    get_available_versions,
    set_current_version,
    get_version_metadata,
    create_new_version,
    compare_versions,
    get_pattern_config
)

# 设置日志
logger.add("logs/pattern_version_demo.log", rotation="10 MB")


def print_header(title: str) -> None:
    """打印标题"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_section(title: str) -> None:
    """打印小节标题"""
    print("\n" + "-" * 80)
    print(f" {title} ".center(80, "-"))
    print("-" * 80)


def list_versions(manager: PatternVersionManager, verbose: bool = False) -> None:
    """列出所有可用版本"""
    print_section("可用模式版本")
    
    versions = manager.get_available_versions()
    
    if not versions:
        print("暂无可用版本")
        return
    
    for i, version in enumerate(versions):
        current_marker = " [当前]" if version.get("is_current") else ""
        print(f"{i+1}. {version['version']}{current_marker} - {version['description']}")
        print(f"   创建日期: {version['created_at']}")
        
        if verbose:
            # 获取详细信息
            metadata = manager.get_version_metadata(version["version"])
            print(f"   数据大小: {metadata.get('data_size', '未知')}")
            print(f"   支持语言覆盖率:")
            for lang, coverage in metadata.get("coverage", {}).items():
                print(f"      - {lang}: {coverage*100:.1f}%")
            
            # 打印模型信息
            print(f"   包含模型:")
            for model_name, model_info in metadata.get("models", {}).items():
                print(f"      - {model_name}: {model_info['description']}")
                
            # 打印更新日志
            if "changelog" in metadata:
                print(f"   更新日志:")
                for change in metadata.get("changelog", []):
                    print(f"      - {change['date']}: {', '.join(change['changes'])}")
        
        print()


def show_version_details(manager: PatternVersionManager, version_name: str) -> None:
    """显示版本详情"""
    print_section(f"版本详情: {version_name}")
    
    metadata = manager.get_version_metadata(version_name)
    
    if not metadata:
        print(f"未找到版本 {version_name} 的元数据")
        return
    
    # 打印基本信息
    print(f"版本: {metadata['version']}")
    print(f"创建日期: {metadata['created_at']}")
    print(f"描述: {metadata['description']}")
    print(f"作者: {metadata['author']}")
    print(f"数据大小: {metadata.get('data_size', '未知')}")
    
    # 兼容的应用版本
    print(f"兼容的应用版本: {', '.join(metadata.get('compatible_app_versions', ['未知']))}")
    
    # 语言覆盖率
    print(f"\n语言覆盖率:")
    for lang, coverage in metadata.get("coverage", {}).items():
        print(f"  - {lang}: {coverage*100:.1f}%")
    
    # 模型信息
    print(f"\n包含模型:")
    for model_name, model_info in metadata.get("models", {}).items():
        print(f"  - {model_name}:")
        print(f"    描述: {model_info['description']}")
        print(f"    算法: {model_info['algorithm']}")
        print(f"    训练数据: {model_info['trained_on']}")
        print(f"    参数:")
        for param_name, param_value in model_info.get("parameters", {}).items():
            print(f"      - {param_name}: {param_value}")
    
    # 性能指标
    if "performance_metrics" in metadata:
        print(f"\n性能指标:")
        for metric, value in metadata["performance_metrics"].items():
            print(f"  - {metric}: {value}")
    
    # 更新日志
    if "changelog" in metadata:
        print(f"\n更新日志:")
        for change in metadata.get("changelog", []):
            print(f"  - {change['date']}:")
            for item in change["changes"]:
                print(f"    * {item}")


def show_pattern_config(manager: PatternVersionManager, version_name: str) -> None:
    """显示模式配置信息"""
    print_section(f"模式配置: {version_name}")
    
    config = manager.get_pattern_config(version_name)
    
    if not config:
        print(f"未找到版本 {version_name} 的配置")
        return
    
    # 打印模式类型
    print(f"模式类型:")
    for pattern_type in config.get("pattern_types", []):
        print(f"  - {pattern_type}")
    
    # 打印评估权重
    print(f"\n评估权重:")
    for metric, weight in config.get("evaluation_weights", {}).items():
        print(f"  - {metric}: {weight}")
    
    # 打印阈值
    print(f"\n评估阈值:")
    for threshold_name, value in config.get("thresholds", {}).items():
        print(f"  - {threshold_name}: {value}")
    
    # 打印特征重要性
    print(f"\n特征重要性:")
    for feature, importance in config.get("feature_importance", {}).items():
        print(f"  - {feature}: {importance}")
    
    # 打印模式参数
    if "pattern_parameters" in config:
        print(f"\n模式类型参数:")
        for pattern_type, params in config["pattern_parameters"].items():
            print(f"  - {pattern_type}:")
            for param_name, param_value in params.items():
                print(f"    * {param_name}: {param_value}")
    
    # 打印推荐组合
    if "recommended_combinations" in config:
        print(f"\n推荐模式组合:")
        for combo in config["recommended_combinations"]:
            print(f"  - {combo['name']}: {', '.join(combo['patterns'])}")
            print(f"    描述: {combo['description']}")
    
    # 打印平台优化参数
    if "platform_optimization" in config:
        print(f"\n平台优化参数:")
        for platform, params in config["platform_optimization"].items():
            print(f"  - {platform}:")
            for param_name, param_value in params.items():
                if isinstance(param_value, dict):
                    print(f"    * {param_name}:")
                    for sub_name, sub_value in param_value.items():
                        print(f"      - {sub_name}: {sub_value}")
                else:
                    print(f"    * {param_name}: {param_value}")


def create_version_demo(manager: PatternVersionManager) -> None:
    """演示创建新版本"""
    print_section("创建新版本")
    
    # 获取当前最新版本作为基础
    base_version = manager._find_latest_version()
    
    if not base_version:
        print("未找到基础版本，无法创建新版本")
        return
    
    print(f"基于版本 {base_version} 创建新版本 v1.1")
    
    # 创建新版本
    success = manager.create_new_version(
        version_name="v1.1",
        description="改进的模式库，增强了对短视频平台的优化",
        author="演示用户",
        base_version=base_version
    )
    
    if not success:
        print("创建新版本失败")
        return
    
    print("新版本创建成功")
    
    # 修改新版本的配置
    new_config = manager.get_pattern_config("v1.1")
    
    # 添加新的模式类型
    if "pattern_types" in new_config:
        if "surprise" not in new_config["pattern_types"]:
            new_config["pattern_types"].append("surprise")
    
    # 修改评估权重
    if "evaluation_weights" in new_config:
        new_config["evaluation_weights"]["viral_coefficient"] = 0.25
        new_config["evaluation_weights"]["recommendation_weight"] = 0.20
        new_config["evaluation_weights"]["emotional_intensity"] = 0.30
    
    # 添加新的平台
    if "platform_optimization" in new_config:
        new_config["platform_optimization"]["bilibili"] = {
            "recommended_duration": [30, 300],
            "key_positions": [0.0, 0.3, 0.6, 0.9],
            "engagement_metrics": {
                "watch_time": 0.4,
                "likes": 0.2,
                "coins": 0.2,
                "favorites": 0.1,
                "comments": 0.1
            }
        }
    
    # 保存修改后的配置
    manager.update_pattern_config(new_config, "v1.1")
    
    # 更新元数据
    metadata = manager.get_version_metadata("v1.1")
    if metadata:
        # 更新数据覆盖率
        if "coverage" in metadata:
            metadata["coverage"]["zh"] = 0.92
            metadata["coverage"]["en"] = 0.80
        
        # 添加更新日志
        if "changelog" in metadata:
            metadata["changelog"].append({
                "date": "2024-05-15",
                "changes": [
                    "增加了新的'surprise'模式类型",
                    "调整了评估权重",
                    "增加了对哔哩哔哩平台的支持"
                ]
            })
        
        # 更新性能指标
        if "performance_metrics" in metadata:
            metadata["performance_metrics"]["accuracy"] = 0.88
            metadata["performance_metrics"]["precision"] = 0.86
        
        # 保存修改后的元数据
        metadata_path = Path(f"models/narrative_patterns/v1.1/metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print("已更新v1.1版本的配置和元数据")


def compare_versions_demo(manager: PatternVersionManager) -> None:
    """演示比较版本差异"""
    print_section("比较版本差异")
    
    # 比较v1.0和v1.1的差异
    diff = manager.compare_versions("v1.0", "v1.1")
    
    if "error" in diff:
        print(f"比较版本失败: {diff['error']}")
        return
    
    print(f"比较版本 v1.0 和 v1.1")
    print(f"较新版本: {diff['version_info']['newer']}")
    print(f"v1.0 创建日期: {diff['version_info']['version1_date']}")
    print(f"v1.1 创建日期: {diff['version_info']['version2_date']}")
    
    # 打印元数据差异
    print("\n元数据差异:")
    for key, change in diff["metadata_diff"].items():
        status = change["status"]
        
        if status == "changed":
            if "old_value" in change:
                print(f"  - {key}: 从 '{change['old_value']}' 变更为 '{change['new_value']}'")
            elif "diff" in change:
                print(f"  - {key}: 内部属性变更")
                for sub_key, sub_change in change["diff"].items():
                    if sub_change["status"] == "changed" and "old_value" in sub_change:
                        print(f"    * {sub_key}: 从 '{sub_change['old_value']}' 变更为 '{sub_change['new_value']}'")
            elif "added" in change or "removed" in change:
                added = change.get("added", [])
                removed = change.get("removed", [])
                if added:
                    print(f"    * 添加项: {added}")
                if removed:
                    print(f"    * 移除项: {removed}")
        elif status == "added":
            print(f"  - 添加了 {key}: {change['value']}")
        elif status == "removed":
            print(f"  - 移除了 {key}: {change['value']}")
    
    # 打印配置差异
    print("\n配置差异:")
    for key, change in diff["config_diff"].items():
        status = change["status"]
        
        if status == "changed":
            if "old_value" in change:
                print(f"  - {key}: 从 '{change['old_value']}' 变更为 '{change['new_value']}'")
            elif "diff" in change:
                print(f"  - {key}: 内部属性变更")
                for sub_key, sub_change in change["diff"].items():
                    if "status" in sub_change:
                        if sub_change["status"] == "added":
                            print(f"    * 添加了 {sub_key}: {sub_change['value']}")
                        elif sub_change["status"] == "changed" and "old_value" in sub_change:
                            print(f"    * {sub_key}: 从 '{sub_change['old_value']}' 变更为 '{sub_change['new_value']}'")
            elif "added" in change or "removed" in change:
                added = change.get("added", [])
                removed = change.get("removed", [])
                if added:
                    print(f"    * 添加项: {added}")
                if removed:
                    print(f"    * 移除项: {removed}")
        elif status == "added":
            print(f"  - 添加了 {key}: {change['value']}")
        elif status == "removed":
            print(f"  - 移除了 {key}: {change['value']}")


def switch_version_demo(manager: PatternVersionManager) -> None:
    """演示切换版本"""
    print_section("切换当前版本")
    
    # 获取当前版本
    current = manager.current_version
    print(f"当前版本: {current}")
    
    # 切换到v1.1
    print("切换到版本 v1.1")
    success = manager.set_current_version("v1.1")
    
    if not success:
        print("切换版本失败")
        return
    
    print(f"版本已切换到: {manager.current_version}")
    
    # 切换回v1.0
    print("切换回版本 v1.0")
    success = manager.set_current_version("v1.0")
    
    if not success:
        print("切换版本失败")
        return
    
    print(f"版本已切换回: {manager.current_version}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='模式版本管理系统演示')
    parser.add_argument('--list', action='store_true',
                        help='列出所有可用版本')
    parser.add_argument('--detail', type=str, default=None,
                        help='显示指定版本的详情')
    parser.add_argument('--config', type=str, default=None,
                        help='显示指定版本的配置')
    parser.add_argument('--compare', action='store_true',
                        help='比较版本差异')
    parser.add_argument('--create', action='store_true',
                        help='创建新版本')
    parser.add_argument('--switch', action='store_true',
                        help='切换版本')
    parser.add_argument('--all', action='store_true',
                        help='运行所有演示')
    args = parser.parse_args()
    
    print_header("模式版本管理系统演示")
    
    # 创建版本管理器
    manager = PatternVersionManager()
    
    # 判断演示内容
    if args.list or args.all:
        list_versions(manager, verbose=True)
    
    if args.detail or args.all:
        version = args.detail or "v1.0"
        show_version_details(manager, version)
    
    if args.config or args.all:
        version = args.config or "v1.0"
        show_pattern_config(manager, version)
    
    if args.create or args.all:
        create_version_demo(manager)
    
    if (args.compare or args.all) and Path("models/narrative_patterns/v1.1").exists():
        compare_versions_demo(manager)
    
    if (args.switch or args.all) and Path("models/narrative_patterns/v1.1").exists():
        switch_version_demo(manager)
    
    # 如果没有指定任何选项，显示帮助信息
    if not any([args.list, args.detail, args.config, args.compare, args.create, args.switch, args.all]):
        list_versions(manager)
        print("\n使用 --help 查看更多选项")
    
    print("\n演示完成!")


if __name__ == "__main__":
    main() 