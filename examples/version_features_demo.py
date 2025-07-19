#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本特征库演示程序

演示如何使用版本特征库进行版本检测、特性查询和兼容性检查。
"""

import os
import sys
import argparse
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入版本管理模块
try:
    from src.versioning.version_features import get_version_features
    from src.versioning.version_detector import detect_version, is_compatible, get_conversion_path
    from src.versioning.schema_validator import validate_xml_file, list_schemas
except ImportError as e:
    print(f"导入模块出错: {e}")
    sys.exit(1)

def print_version_info(version: str) -> None:
    """打印版本信息"""
    features = get_version_features()
    version_info = features.get_version_info(version)
    
    if not version_info:
        print(f"未找到版本 {version} 的信息")
        return
        
    print(f"版本: {version} ({version_info.get('display_name', '未知')})")
    print(f"模式文件: {version_info.get('schema', '未知')}")
    print(f"最大分辨率: {version_info.get('max_resolution', '未知')}")
    
    print("\n支持的功能:")
    for feature in version_info.get('supported_features', []):
        if isinstance(feature, dict):
            required = '(必需)' if feature.get('required') else '(可选)'
            print(f"- {feature.get('name')}: {feature.get('description', '无描述')} {required}")
        elif isinstance(feature, str):
            print(f"- {feature}")
    
    print("\n支持的效果:")
    for effect in version_info.get('supported_effects', []):
        print(f"- {effect}")
    
    print("\n兼容的版本:")
    for compat_ver in version_info.get('compatibility', []):
        print(f"- {compat_ver}")

def analyze_file(file_path: str) -> None:
    """分析文件版本信息"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
        
    print(f"分析文件: {file_path}")
    
    # 检测版本
    version_info = detect_version(file_path)
    
    if not version_info.get('success', False):
        print(f"版本检测失败: {version_info.get('error', '未知错误')}")
        return
        
    print(f"格式类型: {version_info.get('format_type', '未知')}")
    print(f"显示名称: {version_info.get('display_name', '未知')}")
    print(f"版本: {version_info.get('version', '未知')}")
    print(f"文件大小: {version_info.get('file_size', 0)} 字节")
    print(f"最后修改时间: {version_info.get('last_modified', '未知')}")
    
    # 打印支持的功能
    if 'supported_features' in version_info:
        print("\n支持的功能:")
        for feature in version_info['supported_features']:
            print(f"- {feature}")
    
    # 打印支持的效果
    if 'supported_effects' in version_info:
        print("\n支持的效果:")
        for effect in version_info['supported_effects']:
            print(f"- {effect}")
    
    # 打印兼容版本
    if 'compatible_versions' in version_info:
        print("\n兼容的版本:")
        for compat_ver in version_info['compatible_versions']:
            print(f"- {compat_ver}")
    
    # 如果是剪映格式的XML文件，尝试进行验证
    if version_info.get('format_type') == 'jianying' and file_path.lower().endswith('.xml'):
        print("\n验证XML文件:")
        validation = validate_xml_file(file_path)
        
        if validation.get('valid', False):
            print(f"验证通过，使用模式文件: {validation.get('schema_file', '未知')}")
        else:
            print(f"验证失败: {validation.get('message', '未知错误')}")
            if 'errors' in validation:
                print("错误详情:")
                for err in validation['errors']:
                    print(f"- 行 {err['line']}, 列 {err['column']}: {err['message']}")

def check_compatibility(source_version: str, target_version: str) -> None:
    """检查版本兼容性"""
    print(f"检查从版本 {source_version} 到版本 {target_version} 的兼容性")
    
    # 检查是否兼容
    compatible = is_compatible(source_version, target_version)
    
    if compatible:
        print("结果: 兼容")
    else:
        print("结果: 不兼容")
    
    # 获取转换路径
    path = get_conversion_path(source_version, target_version)
    
    if path:
        print("\n转换路径:")
        for i, step in enumerate(path):
            if i < len(path) - 1:
                print(f"{step} -> ", end="")
            else:
                print(step)
        
        # 获取转换操作
        features = get_version_features()
        
        if len(path) >= 2:
            print("\n转换操作:")
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i+1]
                
                operations = features.get_conversion_operations(source, target)
                
                print(f"\n从 {source} 到 {target}:")
                if operations:
                    for op in operations:
                        print(f"- 类型: {op.get('type')}")
                        print(f"  描述: {op.get('description')}")
                        if 'target' in op:
                            print(f"  目标: {op.get('target')}")
                        if 'from' in op and 'to' in op:
                            print(f"  从 {op.get('from')} 到 {op.get('to')}")
                        if 'keep' in op:
                            print(f"  保留: {', '.join(op.get('keep'))}")
                        if 'max' in op:
                            print(f"  最大值: {op.get('max')}")
                else:
                    print("  无需特殊操作")
    else:
        print("\n无法找到转换路径")

def list_all_versions() -> None:
    """列出所有可用版本"""
    features = get_version_features()
    versions = features.get_all_versions()
    
    print("所有支持的版本:")
    for version_info in sorted(versions, key=lambda v: v.get('version', '0.0.0')):
        version = version_info.get('version', '未知')
        display_name = version_info.get('display_name', '未知')
        max_resolution = version_info.get('max_resolution', '未知')
        
        print(f"- {version} ({display_name})")
        print(f"  最大分辨率: {max_resolution}")
        print(f"  模式文件: {version_info.get('schema', '未知')}")
        
        # 显示特性计数
        feature_count = len(version_info.get('supported_features', []))
        effect_count = len(version_info.get('supported_effects', []))
        
        print(f"  功能数量: {feature_count}")
        print(f"  效果数量: {effect_count}")
        print()

def list_all_schemas() -> None:
    """列出所有可用模式文件"""
    schemas = list_schemas()
    
    print("所有可用模式文件:")
    for schema in schemas:
        file_name = schema.get('file_name', '未知')
        version = schema.get('version', '未知')
        
        print(f"- {file_name}")
        print(f"  版本: {version}")
        
        if 'documentation' in schema and schema['documentation']:
            print(f"  描述: {schema['documentation']}")
            
        if 'supports_version' in schema and schema['supports_version']:
            print(f"  支持版本: {', '.join(schema['supports_version'])}")
            
        if 'root_element' in schema:
            print(f"  根元素: {schema['root_element']}")
            
        print()

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="版本特征库演示程序")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 查看版本信息命令
    version_parser = subparsers.add_parser("version", help="查看版本信息")
    version_parser.add_argument("version", help="版本号")
    
    # 分析文件命令
    file_parser = subparsers.add_parser("file", help="分析文件版本信息")
    file_parser.add_argument("file_path", help="文件路径")
    
    # 兼容性检查命令
    compat_parser = subparsers.add_parser("compat", help="检查版本兼容性")
    compat_parser.add_argument("source", help="源版本号")
    compat_parser.add_argument("target", help="目标版本号")
    
    # 列出所有版本命令
    subparsers.add_parser("list", help="列出所有可用版本")
    
    # 列出所有模式文件命令
    subparsers.add_parser("schemas", help="列出所有可用模式文件")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "version":
        print_version_info(args.version)
    elif args.command == "file":
        analyze_file(args.file_path)
    elif args.command == "compat":
        check_compatibility(args.source, args.target)
    elif args.command == "list":
        list_all_versions()
    elif args.command == "schemas":
        list_all_schemas()
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"出错: {str(e)}")
        sys.exit(1) 