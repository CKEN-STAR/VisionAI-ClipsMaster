#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨平台路径解析演示脚本

展示如何使用跨平台路径解析模块处理不同系统下的路径特殊标记。
"""

import os
import sys
import platform
from pathlib import Path
import argparse

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.config.path_resolver import (
    resolve_special_path,
    ensure_dir_exists,
    get_app_data_dir,
    get_temp_dir,
    get_project_root,
    normalize_path,
    get_relative_path,
    is_subpath,
    join_paths,
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


def demo_resolve_special_path():
    """演示特殊路径解析功能"""
    print_separator("特殊路径解析")
    
    test_paths = [
        # 通用路径
        ".",
        "..",
        "~/Documents",
        
        # Windows特定路径
        "%USERPROFILE%\\Documents",
        "%APPDATA%\\Local",
        "%TEMP%\\test",
        
        # Unix特定路径
        "$HOME/Downloads",
        "${HOME}/Projects",
        "/usr/local/bin",
        
        # 变量组合路径
        "${TEMP}/test_${USERNAME}",
        "~/projects/%COMPUTERNAME%",
    ]
    
    print(f"当前操作系统: {platform.system()} ({platform.release()})\n")
    
    for path in test_paths:
        try:
            resolved = resolve_special_path(path)
            print(f"原始路径: {path}")
            print(f"解析结果: {resolved}")
            print(f"存在: {'是' if os.path.exists(resolved) else '否'}")
            print()
        except Exception as e:
            print(f"解析 {path} 失败: {str(e)}")
            print()


def demo_platform_path():
    """演示跨平台路径转换"""
    print_separator("跨平台路径转换")
    
    test_paths = [
        "C:/Windows/System32",
        "/usr/local/bin",
        "path/to/file.txt",
        "path\\to\\another\\file.txt",
    ]
    
    print(f"当前操作系统: {platform.system()}\n")
    
    for path in test_paths:
        normalized = normalize_path(path)
        print(f"原始路径: {path}")
        print(f"标准化后: {normalized}")
        print()


def demo_app_paths():
    """演示应用路径功能"""
    print_separator("应用程序路径")
    
    # 获取应用数据目录
    app_data = get_app_data_dir("VisionAI-ClipsMaster")
    print(f"应用数据目录: {app_data}")
    
    # 获取临时目录
    temp_dir = get_temp_dir("visionai_demo_")
    print(f"临时目录: {temp_dir}")
    
    # 获取项目根目录
    project_root = get_project_root()
    print(f"项目根目录: {project_root}")
    
    # 测试数据目录
    data_dir = join_paths(project_root, "data", "samples")
    print(f"样本数据目录: {data_dir}")
    
    # 配置文件路径
    config_file = join_paths(project_root, "configs", "app_settings.yaml")
    print(f"配置文件路径: {config_file}")


def demo_relative_paths():
    """演示相对路径功能"""
    print_separator("相对路径操作")
    
    # 获取项目根目录
    project_root = get_project_root()
    print(f"项目根目录: {project_root}")
    
    # 测试文件
    test_file = join_paths(project_root, "src", "demos", "path_resolver_demo.py")
    print(f"测试文件: {test_file}")
    
    # 计算相对路径
    rel_path = get_relative_path(test_file)
    print(f"相对项目根目录: {rel_path}")
    
    # 测试是否是子路径
    subpath_result = is_subpath(test_file, project_root)
    print(f"测试文件是项目根目录的子路径: {'是' if subpath_result else '否'}")
    
    # 反向测试
    reverse_result = is_subpath(project_root, test_file)
    print(f"项目根目录是测试文件的子路径: {'是' if reverse_result else '否'}")


def demo_create_dirs():
    """演示目录创建功能"""
    print_separator("目录创建")
    
    # 获取临时目录
    temp_base = get_temp_dir("visionai_demo_")
    
    # 创建多级目录
    nested_dir = join_paths(temp_base, "level1", "level2", "level3")
    created_path = ensure_dir_exists(nested_dir)
    
    print(f"创建的多级目录: {created_path}")
    print(f"目录是否存在: {'是' if os.path.isdir(created_path) else '否'}")
    
    # 计算相对路径
    rel_path = get_relative_path(created_path, temp_base)
    print(f"相对于临时目录的路径: {rel_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="跨平台路径解析演示")
    parser.add_argument('--all', action='store_true', help="运行所有演示")
    parser.add_argument('--special', action='store_true', help="演示特殊路径解析")
    parser.add_argument('--platform', action='store_true', help="演示跨平台路径转换")
    parser.add_argument('--app-paths', action='store_true', help="演示应用路径")
    parser.add_argument('--relative', action='store_true', help="演示相对路径操作")
    parser.add_argument('--create-dirs', action='store_true', help="演示目录创建")
    
    args = parser.parse_args()
    
    # 默认运行所有演示
    run_all = args.all or not any([
        args.special, args.platform, args.app_paths, 
        args.relative, args.create_dirs
    ])
    
    print_separator("VisionAI-ClipsMaster 跨平台路径解析演示")
    print("此演示展示了如何使用跨平台路径解析模块在不同操作系统间处理路径。")
    print(f"当前运行环境: {platform.system()} {platform.release()}")
    print()
    
    if run_all or args.special:
        demo_resolve_special_path()
    
    if run_all or args.platform:
        demo_platform_path()
    
    if run_all or args.app_paths:
        demo_app_paths()
    
    if run_all or args.relative:
        demo_relative_paths()
    
    if run_all or args.create_dirs:
        demo_create_dirs()
    
    print_separator("演示结束")
    print("您可以在自己的代码中导入并使用这些功能，确保在不同操作系统上都能正确处理路径。")


if __name__ == "__main__":
    main() 