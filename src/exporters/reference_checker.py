#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
引用完整性检查模块

提供XML文件中资源引用的完整性验证功能，确保:
1. 所有clip元素引用的资源ID存在
2. 所有资源ID格式正确且唯一
3. 没有孤立资源（未被引用的资源）
4. 复杂引用关系的完整性（如nested clips, linked assets等）
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union
import logging

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志替代
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)

# 配置日志
logger = get_logger("reference_checker")


class ReferenceError(Exception):
    """引用错误异常"""
    pass


def check_asset_references(xml_root: ET.Element) -> bool:
    """
    验证所有clip引用的asset存在

    Args:
        xml_root: XML根元素

    Returns:
        bool: 验证是否通过

    Raises:
        ReferenceError: 当发现未定义资源引用时抛出
    """
    logger.info("验证所有clip引用的asset存在")
    
    # 收集所有资源ID
    asset_ids = {a.get('id') for a in xml_root.findall(".//asset")}
    
    # 添加视频资源ID
    asset_ids.update({v.get('id') for v in xml_root.findall(".//video") if v.get('id')})
    
    # 添加音频资源ID
    asset_ids.update({a.get('id') for a in xml_root.findall(".//audio") if a.get('id')})
    
    # 添加图像资源ID
    asset_ids.update({i.get('id') for i in xml_root.findall(".//image") if i.get('id')})
    
    # 检查所有clip的引用
    for clip in xml_root.findall(".//clip"):
        # 获取资源引用（不同XML格式可能使用不同属性名）
        ref = clip.get('ref') or clip.get('resourceId') or clip.get('asset_id')
        
        if ref and ref not in asset_ids:
            error_msg = f"未定义素材引用: {ref}"
            logger.error(error_msg)
            raise ReferenceError(error_msg)
    
    logger.info("所有clip引用的asset验证通过")
    return True


def check_id_uniqueness(xml_root: ET.Element) -> bool:
    """
    验证所有ID是否唯一

    Args:
        xml_root: XML根元素

    Returns:
        bool: 验证是否通过

    Raises:
        ReferenceError: 当发现重复ID时抛出
    """
    logger.info("验证所有资源ID唯一性")
    
    # 收集所有带ID的元素
    id_elements = []
    for elem in xml_root.findall(".//*[@id]"):
        id_elements.append((elem.get('id'), elem.tag))
    
    # 检查ID唯一性
    id_counts = {}
    for id_val, tag in id_elements:
        if id_val in id_counts:
            id_counts[id_val].append(tag)
        else:
            id_counts[id_val] = [tag]
    
    # 找出重复的ID
    duplicates = {id_val: tags for id_val, tags in id_counts.items() if len(tags) > 1}
    
    if duplicates:
        error_msg = "发现重复ID: " + ", ".join([f"{id_val} (用于 {', '.join(tags)})" for id_val, tags in duplicates.items()])
        logger.error(error_msg)
        raise ReferenceError(error_msg)
    
    logger.info("所有资源ID唯一性验证通过")
    return True


def check_orphaned_assets(xml_root: ET.Element) -> Dict[str, List[str]]:
    """
    检查未被引用的孤立资源

    Args:
        xml_root: XML根元素

    Returns:
        Dict[str, List[str]]: 孤立资源字典，键为资源类型，值为资源ID列表
    """
    logger.info("检查孤立资源")
    
    # 收集所有资源ID及其类型
    asset_ids = {}
    
    # 视频资源
    for elem in xml_root.findall(".//video[@id]"):
        asset_ids[elem.get('id')] = 'video'
    
    # 音频资源
    for elem in xml_root.findall(".//audio[@id]"):
        asset_ids[elem.get('id')] = 'audio'
    
    # 图像资源
    for elem in xml_root.findall(".//image[@id]"):
        asset_ids[elem.get('id')] = 'image'
    
    # 通用资源
    for elem in xml_root.findall(".//asset[@id]"):
        asset_ids[elem.get('id')] = 'asset'
    
    # 收集所有被引用的资源ID
    referenced_ids = set()
    
    # 从clip元素收集引用
    for clip in xml_root.findall(".//clip"):
        ref = clip.get('ref') or clip.get('resourceId') or clip.get('asset_id')
        if ref:
            referenced_ids.add(ref)
    
    # 从其他可能引用资源的元素收集引用
    for elem in xml_root.findall(".//*[@resource]"):
        referenced_ids.add(elem.get('resource'))
    
    for elem in xml_root.findall(".//*[@source]"):
        referenced_ids.add(elem.get('source'))
    
    # 找出未被引用的资源
    orphaned = {}
    for asset_id, asset_type in asset_ids.items():
        if asset_id not in referenced_ids:
            if asset_type not in orphaned:
                orphaned[asset_type] = []
            orphaned[asset_type].append(asset_id)
    
    # 记录结果
    if orphaned:
        for asset_type, ids in orphaned.items():
            logger.warning(f"发现未被引用的{asset_type}资源: {', '.join(ids)}")
    else:
        logger.info("未发现孤立资源")
    
    return orphaned


def check_reference_integrity(xml_path: str, strict: bool = False) -> Dict[str, Any]:
    """
    全面验证XML文件中的引用完整性

    Args:
        xml_path: XML文件路径
        strict: 是否使用严格模式（严格模式下孤立资源也被视为错误）

    Returns:
        Dict[str, Any]: 验证结果字典，包含以下键:
            - valid (bool): 总体验证是否通过
            - errors (List[str]): 错误信息列表
            - warnings (List[str]): 警告信息列表
            - orphaned_assets (Dict[str, List[str]]): 孤立资源信息
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "orphaned_assets": {}
    }
    
    logger.info(f"开始验证XML文件引用完整性: {xml_path}")
    
    # 检查文件存在性
    if not os.path.exists(xml_path):
        result["errors"].append(f"文件不存在: {xml_path}")
        return result
    
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 验证资源引用
        try:
            check_asset_references(root)
        except ReferenceError as e:
            result["errors"].append(str(e))
        
        # 验证ID唯一性
        try:
            check_id_uniqueness(root)
        except ReferenceError as e:
            result["errors"].append(str(e))
        
        # 检查孤立资源
        orphaned = check_orphaned_assets(root)
        result["orphaned_assets"] = orphaned
        
        # 严格模式下将孤立资源视为错误
        if strict and orphaned:
            orphan_msg = "孤立资源: " + ", ".join([f"{t}:{','.join(ids)}" for t, ids in orphaned.items()])
            result["errors"].append(orphan_msg)
        elif orphaned:
            # 非严格模式下仅视为警告
            for asset_type, ids in orphaned.items():
                result["warnings"].append(f"未被引用的{asset_type}资源: {', '.join(ids)}")
        
        # 设置最终验证结果
        result["valid"] = len(result["errors"]) == 0
        
        # 记录验证结果
        if result["valid"]:
            logger.info("引用完整性验证通过")
        else:
            logger.error(f"引用完整性验证失败: {'; '.join(result['errors'])}")
        
        if result["warnings"]:
            logger.warning(f"引用完整性警告: {'; '.join(result['warnings'])}")
        
    except ET.ParseError as e:
        result["errors"].append(f"XML解析错误: {str(e)}")
    except Exception as e:
        result["errors"].append(f"验证过程异常: {str(e)}")
    
    return result


def fix_missing_references(xml_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    尝试修复缺失的资源引用
    
    通过以下方式修复:
    1. 为引用不存在资源的clip创建适当的asset元素
    2. 移除不合法的引用属性
    
    Args:
        xml_path: 输入XML文件路径
        output_path: 输出XML文件路径，如果为None则覆盖原文件
        
    Returns:
        Tuple[bool, str]: (是否成功修复, 修复后的文件路径)
    """
    if output_path is None:
        output_path = xml_path
    
    logger.info(f"尝试修复XML文件引用完整性问题: {xml_path}")
    
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 收集所有资源ID
        asset_ids = {a.get('id') for a in root.findall(".//*[@id]") if a.tag in ['asset', 'video', 'audio', 'image']}
        
        # 收集问题引用
        missing_refs = []
        for clip in root.findall(".//clip"):
            ref = clip.get('ref') or clip.get('resourceId') or clip.get('asset_id')
            if ref and ref not in asset_ids:
                missing_refs.append((clip, ref))
        
        # 如果没有问题，直接返回
        if not missing_refs:
            logger.info("未发现引用问题，无需修复")
            return (True, xml_path)
        
        # 创建资源节点
        resources = root.find(".//resources")
        if resources is None:
            resources = ET.SubElement(root, "resources")
        
        # 修复问题引用
        for clip, ref in missing_refs:
            # 创建placeholder资源
            asset = ET.SubElement(resources, "asset", {
                "id": ref,
                "type": "placeholder",
                "name": f"自动创建的资源 {ref}"
            })
            
            # 添加placeholder属性
            ET.SubElement(asset, "placeholder").text = "true"
            
            logger.info(f"为引用 {ref} 创建placeholder资源")
        
        # 保存修复后的XML
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"引用完整性问题修复完成，保存到: {output_path}")
        
        return (True, output_path)
        
    except Exception as e:
        logger.error(f"修复引用完整性问题失败: {str(e)}")
        return (False, xml_path)


def remove_orphaned_assets(xml_path: str, output_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    移除未被引用的孤立资源
    
    Args:
        xml_path: 输入XML文件路径
        output_path: 输出XML文件路径，如果为None则覆盖原文件
        
    Returns:
        Tuple[bool, str]: (是否成功修复, 修复后的文件路径)
    """
    if output_path is None:
        output_path = xml_path
    
    logger.info(f"尝试移除XML文件中的孤立资源: {xml_path}")
    
    try:
        # 解析XML文件
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 检查孤立资源
        orphaned_info = check_orphaned_assets(root)
        
        # 如果没有孤立资源，直接返回
        if not orphaned_info:
            logger.info("未发现孤立资源，无需移除")
            return (True, xml_path)
        
        # 收集所有孤立资源ID
        orphaned_ids = []
        for ids in orphaned_info.values():
            orphaned_ids.extend(ids)
        
        # 移除孤立资源
        removed_count = 0
        for asset_type in ['asset', 'video', 'audio', 'image']:
            for elem in root.findall(f".//{asset_type}[@id]"):
                if elem.get('id') in orphaned_ids:
                    parent = root.find(f".//*[./{asset_type}[@id='{elem.get('id')}']]")
                    if parent is not None:
                        parent.remove(elem)
                        removed_count += 1
        
        # 保存修复后的XML
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"成功移除 {removed_count} 个孤立资源，保存到: {output_path}")
        
        return (True, output_path)
        
    except Exception as e:
        logger.error(f"移除孤立资源失败: {str(e)}")
        return (False, xml_path)


def check_reference_cycles(xml_root: ET.Element) -> List[List[str]]:
    """
    检查XML中的引用循环
    
    Args:
        xml_root: XML根元素
        
    Returns:
        List[List[str]]: 发现的循环引用链，每个链是一个ID列表
    """
    logger.info("检查引用循环")
    
    # 构建引用图（ID -> 引用的ID列表）
    reference_graph = {}
    
    # 收集所有带ID的元素
    elements_by_id = {}
    for elem in xml_root.findall(".//*[@id]"):
        elements_by_id[elem.get('id')] = elem
    
    # 构建引用关系
    for elem_id, elem in elements_by_id.items():
        references = []
        
        # 检查不同类型的引用
        for ref_attr in ['ref', 'resourceId', 'asset_id', 'source', 'target']:
            ref_id = elem.get(ref_attr)
            if ref_id and ref_id in elements_by_id:
                references.append(ref_id)
        
        reference_graph[elem_id] = references
    
    # 查找循环
    cycles = []
    
    def dfs(node, path, visited):
        """深度优先搜索查找循环"""
        if node in path:
            # 发现循环
            cycle_start = path.index(node)
            cycles.append(path[cycle_start:] + [node])
            return
        
        if node in visited:
            return
        
        visited.add(node)
        path.append(node)
        
        for neighbor in reference_graph.get(node, []):
            dfs(neighbor, path.copy(), visited)
    
    # 对每个节点开始搜索
    visited = set()
    for node in reference_graph:
        if node not in visited:
            dfs(node, [], visited)
    
    # 记录结果
    if cycles:
        for cycle in cycles:
            logger.error(f"发现引用循环: {' -> '.join(cycle)}")
    else:
        logger.info("未发现引用循环")
    
    return cycles


def validate_references(xml_path: str, auto_fix: bool = False, 
                        strict: bool = False) -> Dict[str, Any]:
    """
    验证并可选修复XML文件的引用完整性问题
    
    Args:
        xml_path: XML文件路径
        auto_fix: 是否自动修复问题
        strict: 是否使用严格模式
        
    Returns:
        Dict[str, Any]: 验证结果，包含验证状态和问题详情
    """
    # 验证引用完整性
    result = check_reference_integrity(xml_path, strict)
    
    # 如果启用自动修复且验证失败
    if auto_fix and not result["valid"]:
        # 修复缺失引用
        fixed_missing, fixed_path = fix_missing_references(xml_path)
        
        # 移除孤立资源
        if strict and result["orphaned_assets"]:
            fixed_orphans, fixed_path = remove_orphaned_assets(fixed_path)
        
        # 重新验证
        new_result = check_reference_integrity(fixed_path, strict)
        
        # 添加修复信息
        new_result["fixed"] = True
        new_result["original_status"] = result["valid"]
        
        return new_result
    
    return result


if __name__ == "__main__":
    # 如果作为脚本运行，接受命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description='验证XML文件引用完整性')
    parser.add_argument('xml_path', help='要验证的XML文件路径')
    parser.add_argument('--fix', action='store_true', help='自动修复引用问题')
    parser.add_argument('--strict', action='store_true', help='使用严格验证模式')
    parser.add_argument('--output', help='修复后的输出文件路径')
    
    args = parser.parse_args()
    
    if args.fix:
        result = validate_references(args.xml_path, auto_fix=True, strict=args.strict)
        if result["fixed"]:
            print(f"已修复引用问题，最终验证状态: {'通过' if result['valid'] else '失败'}")
    else:
        result = check_reference_integrity(args.xml_path, strict=args.strict)
        
        if result["valid"]:
            print("引用完整性验证通过")
        else:
            print("引用完整性验证失败:")
            for error in result["errors"]:
                print(f"  - 错误: {error}")
        
        if result["warnings"]:
            print("警告:")
            for warning in result["warnings"]:
                print(f"  - 警告: {warning}")
    
    sys.exit(0 if result["valid"] else 1) 