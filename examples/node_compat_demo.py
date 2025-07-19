#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
必需节点补偿演示程序

展示如何使用节点兼容性模块为XML文件添加必需节点，以及验证节点兼容性。
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入节点兼容性模块
try:
    from src.exporters.node_compat import (
        add_required_nodes,
        remove_unsupported_nodes,
        verify_required_nodes,
        validate_version_compatibility,
        get_version_specification,
        process_xml_file,
        batch_process_directory
    )
except ImportError as e:
    print(f"导入节点兼容性模块出错: {e}")
    sys.exit(1)

def create_sample_xml(output_file: str, version: str = "3.0.0", minimal: bool = False) -> bool:
    """
    创建示例XML文件用于测试
    
    Args:
        output_file: 输出文件路径
        version: XML文件版本
        minimal: 是否创建最小化结构的XML
        
    Returns:
        bool: 是否创建成功
    """
    try:
        # 创建XML文档
        doc = minidom.getDOMImplementation().createDocument(None, "jianying_project", None)
        root = doc.documentElement
        
        # 设置版本属性
        root.setAttribute("version", version)
        
        if not minimal:
            # 添加完整的结构
            # 添加基本结构
            info = doc.createElement("info")
            metadata = doc.createElement("metadata")
            project_settings = doc.createElement("project_settings")
            
            # 添加元数据
            title = doc.createElement("title")
            title.appendChild(doc.createTextNode("示例项目"))
            creator = doc.createElement("creator")
            creator.appendChild(doc.createTextNode("VisionAI-ClipsMaster"))
            
            metadata.appendChild(title)
            metadata.appendChild(creator)
            
            # 添加项目设置
            resolution = doc.createElement("resolution")
            if version >= "3.0.0":
                resolution.setAttribute("width", "3840")
                resolution.setAttribute("height", "2160")
            elif version >= "2.5.0":
                resolution.setAttribute("width", "1920")
                resolution.setAttribute("height", "1080")
            else:
                resolution.setAttribute("width", "1280")
                resolution.setAttribute("height", "720")
            
            frame_rate = doc.createElement("frame_rate")
            frame_rate.appendChild(doc.createTextNode("30"))
            
            project_settings.appendChild(resolution)
            project_settings.appendChild(frame_rate)
            
            # 组装info部分
            info.appendChild(metadata)
            info.appendChild(project_settings)
            
            # 添加资源和时间线
            resources = doc.createElement("resources")
            timeline = doc.createElement("timeline")
            timeline.setAttribute("id", "main_timeline")
            timeline.setAttribute("duration", "00:01:00.000")
            
            # 将所有部分添加到根元素
            root.appendChild(info)
            root.appendChild(resources)
            root.appendChild(timeline)
        else:
            # 创建最小化结构的XML
            # 只添加资源部分
            resources = doc.createElement("resources")
            root.appendChild(resources)
        
        # 输出格式化的XML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
            
        print(f"创建{'最小化' if minimal else '完整'}示例XML文件成功: {output_file}")
        return True
    except Exception as e:
        print(f"创建示例XML文件失败: {str(e)}")
        return False

def show_version_specifications(version: Optional[str] = None) -> None:
    """
    显示版本规格信息
    
    Args:
        version: 特定版本号，如果为None则显示所有支持的版本
    """
    if version:
        # 显示特定版本的规格
        spec = get_version_specification(version)
        if spec:
            print(f"\n版本 {version} 规格:")
            print("-" * 40)
            print("必需节点:")
            for node in spec.get("required_nodes", []):
                print(f"  - {node}")
            
            print("\n默认值:")
            for node, value in spec.get("default_values", {}).items():
                print(f"  - {node}: {value}")
            
            print("\n必需属性:")
            for node, attrs in spec.get("required_attributes", {}).items():
                print(f"  - {node}:")
                for attr_name, attr_value in attrs.items():
                    print(f"    {attr_name}: {attr_value}")
            
            if "unsupported_nodes" in spec:
                print("\n不支持的节点:")
                for node in spec.get("unsupported_nodes", []):
                    print(f"  - {node}")
            
            if "supported_features" in spec:
                print("\n支持的功能:")
                for feature in spec.get("supported_features", []):
                    print(f"  - {feature}")
        else:
            print(f"未找到版本 {version} 的规格")
    else:
        # 显示所有支持的版本
        print("\n支持的版本:")
        print("-" * 40)
        
        # 尝试加载配置文件中的所有版本
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'configs', 'version_specifications.json')
        
        if os.path.exists(config_path):
            import json
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    specs = json.load(f)
                    
                    for version, spec in specs.items():
                        features = spec.get("supported_features", [])
                        feature_str = ", ".join(features)
                        print(f"版本 {version}: {len(features)} 个功能 - {feature_str}")
            except Exception as e:
                print(f"加载版本规格时出错: {str(e)}")
        else:
            # 使用默认版本列表
            for version in ["3.0.0", "2.9.5", "2.5.0", "2.0.0"]:
                spec = get_version_specification(version)
                if spec:
                    features = spec.get("supported_features", [])
                    feature_str = ", ".join(features)
                    print(f"版本 {version}: {len(features)} 个功能 - {feature_str}")

def check_compatibility(xml_file: str, target_version: str) -> None:
    """
    检查XML文件与目标版本的兼容性
    
    Args:
        xml_file: XML文件路径
        target_version: 目标版本
    """
    try:
        # 解析XML文件
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 检查兼容性
        compatible, reasons = validate_version_compatibility(root, target_version)
        
        current_version = root.get("version", "未知")
        
        print(f"\n兼容性检查结果:")
        print(f"文件: {xml_file}")
        print(f"当前版本: {current_version}")
        print(f"目标版本: {target_version}")
        print(f"兼容性: {'兼容' if compatible else '不兼容'}")
        
        if not compatible:
            print("\n不兼容原因:")
            for reason in reasons:
                print(f"  - {reason}")
        
            # 获取版本规格
            spec = get_version_specification(target_version)
            if spec:
                # 验证必需节点
                missing_nodes = verify_required_nodes(root, spec)
                
                if missing_nodes:
                    print("\n缺失的必需节点:")
                    for node in missing_nodes:
                        print(f"  - {node}")
    except Exception as e:
        print(f"检查兼容性时出错: {str(e)}")

def compare_before_after(original_file: str, processed_file: str) -> None:
    """
    比较处理前后的XML文件
    
    Args:
        original_file: 原始XML文件路径
        processed_file: 处理后的XML文件路径
    """
    try:
        # 解析XML文件
        original_tree = ET.parse(original_file)
        original_root = original_tree.getroot()
        
        processed_tree = ET.parse(processed_file)
        processed_root = processed_tree.getroot()
        
        # 获取版本信息
        original_version = original_root.get("version", "未知")
        processed_version = processed_root.get("version", "未知")
        
        print(f"\n比较处理前后的XML文件:")
        print(f"原始文件: {original_file} (版本 {original_version})")
        print(f"处理后文件: {processed_file} (版本 {processed_version})")
        
        # 统计节点数量
        original_count = count_nodes(original_root)
        processed_count = count_nodes(processed_root)
        
        print(f"\n节点数量变化:")
        print(f"  原始: {original_count} 个节点")
        print(f"  处理后: {processed_count} 个节点")
        print(f"  差异: {processed_count - original_count} 个节点")
        
        # 找出添加和移除的节点
        added_nodes = find_added_nodes(original_root, processed_root)
        removed_nodes = find_removed_nodes(original_root, processed_root)
        
        if added_nodes:
            print(f"\n添加的节点:")
            for node_path in added_nodes:
                print(f"  + {node_path}")
        
        if removed_nodes:
            print(f"\n移除的节点:")
            for node_path in removed_nodes:
                print(f"  - {node_path}")
    except Exception as e:
        print(f"比较文件时出错: {str(e)}")

def count_nodes(element: ET.Element) -> int:
    """
    计算XML元素及其子元素的总数
    
    Args:
        element: XML元素
        
    Returns:
        int: 节点总数
    """
    count = 1  # 当前元素
    
    for child in element:
        count += count_nodes(child)
    
    return count

def find_added_nodes(original: ET.Element, processed: ET.Element, path: str = "") -> List[str]:
    """
    找出在处理后的XML中添加的节点
    
    Args:
        original: 原始XML元素
        processed: 处理后的XML元素
        path: 当前路径
        
    Returns:
        List[str]: 添加的节点路径列表
    """
    added = []
    
    # 创建路径
    current_path = path + "/" + processed.tag if path else processed.tag
    
    # 检查此节点是否在原始XML中存在
    if original is None or original.tag != processed.tag:
        added.append(current_path)
        return added
    
    # 检查子节点
    original_children = {child.tag: child for child in original}
    
    for child in processed:
        # 递归处理子节点
        if child.tag in original_children:
            added.extend(find_added_nodes(original_children[child.tag], child, current_path))
            # 从字典中移除已处理的节点
            del original_children[child.tag]
        else:
            added.append(f"{current_path}/{child.tag}")
    
    return added

def find_removed_nodes(original: ET.Element, processed: ET.Element, path: str = "") -> List[str]:
    """
    找出在处理后的XML中移除的节点
    
    Args:
        original: 原始XML元素
        processed: 处理后的XML元素
        path: 当前路径
        
    Returns:
        List[str]: 移除的节点路径列表
    """
    removed = []
    
    # 创建路径
    current_path = path + "/" + original.tag if path else original.tag
    
    # 检查此节点是否在处理后的XML中存在
    if processed is None or original.tag != processed.tag:
        removed.append(current_path)
        return removed
    
    # 检查子节点
    processed_children = {child.tag: child for child in processed}
    
    for child in original:
        # 递归处理子节点
        if child.tag in processed_children:
            removed.extend(find_removed_nodes(child, processed_children[child.tag], current_path))
            # 从字典中移除已处理的节点
            del processed_children[child.tag]
        else:
            removed.append(f"{current_path}/{child.tag}")
    
    return removed

def main() -> None:
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="XML必需节点补偿演示程序")
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 创建示例文件命令
    create_parser = subparsers.add_parser("create", help="创建示例XML文件")
    create_parser.add_argument("--output", "-o", default="sample.xml", help="输出文件路径")
    create_parser.add_argument("--version", "-v", default="3.0.0", help="XML文件版本")
    create_parser.add_argument("--minimal", "-m", action="store_true", help="创建最小化的XML结构")
    
    # 处理文件命令
    process_parser = subparsers.add_parser("process", help="处理XML文件")
    process_parser.add_argument("input_file", help="输入XML文件路径")
    process_parser.add_argument("--output", "-o", help="输出文件路径")
    process_parser.add_argument("--target-version", "-t", required=True, help="目标版本")
    process_parser.add_argument("--compare", "-c", action="store_true", help="比较处理前后的文件")
    
    # 批量处理命令
    batch_parser = subparsers.add_parser("batch", help="批量处理XML文件")
    batch_parser.add_argument("input_dir", help="输入目录")
    batch_parser.add_argument("output_dir", help="输出目录")
    batch_parser.add_argument("--target-version", "-t", required=True, help="目标版本")
    
    # 检查兼容性命令
    check_parser = subparsers.add_parser("check", help="检查XML文件与目标版本的兼容性")
    check_parser.add_argument("input_file", help="输入XML文件路径")
    check_parser.add_argument("--target-version", "-t", required=True, help="目标版本")
    
    # 显示版本规格命令
    specs_parser = subparsers.add_parser("specs", help="显示版本规格信息")
    specs_parser.add_argument("--version", "-v", help="特定版本号")
    
    # 演示命令
    demo_parser = subparsers.add_parser("demo", help="完整演示：创建、检查、处理和比较")
    demo_parser.add_argument("--output-dir", "-o", default=".", help="输出目录")
    demo_parser.add_argument("--source-version", "-s", default="3.0.0", help="源版本")
    demo_parser.add_argument("--target-version", "-t", default="2.0.0", help="目标版本")
    demo_parser.add_argument("--minimal", "-m", action="store_true", help="使用最小化的XML结构")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 处理命令
    if args.command == "create":
        create_sample_xml(args.output, args.version, args.minimal)
    elif args.command == "process":
        output_file = args.output if args.output else f"{os.path.splitext(args.input_file)[0]}_v{args.target_version}.xml"
        
        if process_xml_file(args.input_file, args.target_version, output_file):
            print(f"成功处理XML文件: {args.input_file} -> {output_file}")
            
            if args.compare:
                compare_before_after(args.input_file, output_file)
        else:
            print(f"处理XML文件失败: {args.input_file}")
    elif args.command == "batch":
        results = batch_process_directory(args.input_dir, args.target_version, args.output_dir)
        
        # 输出统计信息
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"批量处理完成: 成功 {success_count}/{total_count}")
    elif args.command == "check":
        check_compatibility(args.input_file, args.target_version)
    elif args.command == "specs":
        show_version_specifications(args.version)
    elif args.command == "demo":
        # 完整演示流程
        print("\n=== 第1步：显示版本规格信息 ===")
        show_version_specifications(args.target_version)
        
        # 创建示例文件
        print(f"\n=== 第2步：创建{'最小化' if args.minimal else '完整'}示例XML文件 ===")
        original_file = os.path.join(args.output_dir, f"sample_v{args.source_version}_original.xml")
        create_sample_xml(original_file, args.source_version, args.minimal)
        
        # 检查兼容性
        print(f"\n=== 第3步：检查XML文件与目标版本的兼容性 ===")
        check_compatibility(original_file, args.target_version)
        
        # 处理文件
        print(f"\n=== 第4步：处理XML文件，添加必需节点 ===")
        processed_file = os.path.join(args.output_dir, f"sample_v{args.target_version}_processed.xml")
        if process_xml_file(original_file, args.target_version, processed_file):
            print(f"成功处理XML文件: {original_file} -> {processed_file}")
        else:
            print(f"处理XML文件失败: {original_file}")
            sys.exit(1)
        
        # 比较处理前后的文件
        print(f"\n=== 第5步：比较处理前后的XML文件 ===")
        compare_before_after(original_file, processed_file)
        
        # 再次检查兼容性
        print(f"\n=== 第6步：再次检查处理后的XML文件与目标版本的兼容性 ===")
        check_compatibility(processed_file, args.target_version)
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