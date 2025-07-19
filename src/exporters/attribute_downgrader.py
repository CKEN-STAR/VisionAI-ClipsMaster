#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
属性降级处理器

将高版本XML元素的属性转换为低版本兼容的格式，
支持多种版本转换路径和自定义规则。
"""

import os
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

def downgrade_attributes(xml_element, target_version):
    """将高版本本特性转换为低版本兼容格式

    处理XML元素的属性，根据目标版本进行适当的降级转换
    
    Args:
        xml_element: XML元素对象
        target_version: 目标版本号
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 版本比较
        if compare_versions(target_version, "3.0") < 0:
            # 目标版本低于3.0，需要降级处理
            
            # 将4K标签降级为HD标签
            if xml_element.tag == "4K":
                xml_element.tag = "HD"
                # 添加super_sample属性表示这是从高分辨率降采样的内容
                xml_element.set("super_sample", "true")
            
            # 处理fourk_tag元素
            if xml_element.tag == "fourk_tag" and xml_element.get("type") == "4K":
                xml_element.set("type", "HD")
                # 添加super_sample属性表示这是从高分辨率降采样的内容
                xml_element.set("super_sample", "true")
                
            # 处理高分辨率属性
            if "resolution" in xml_element.attrib:
                resolution = xml_element.get("resolution")
                # 检查是否为高分辨率（超过1080p）
                match = re.match(r"(\d+)x(\d+)", resolution)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    if height > 1080 or width > 1920:
                        if target_version < "2.5":
                            # 2.0版本只支持最高720p
                            new_resolution = "1280x720"
                        else:
                            # 2.5和2.9版本支持最高1080p
                            new_resolution = "1920x1080"
                        xml_element.set("resolution", new_resolution)
                        xml_element.set("downsampled", "true")
            
            # 处理HDR属性
            if "hdr" in xml_element.attrib and xml_element.get("hdr").lower() == "true":
                # 低版本不支持HDR，移除该属性
                del xml_element.attrib["hdr"]
                # 添加标记表示这是从HDR内容转换而来
                xml_element.set("colorspace", "srgb")
                xml_element.set("converted_from_hdr", "true")
                
            # 处理嵌套序列
            if xml_element.tag == "nested_sequence":
                if target_version < "3.0":
                    # 3.0以下版本不支持嵌套序列，转换为普通剪辑
                    xml_element.tag = "clip"
                    xml_element.set("flattened", "true")
                    xml_element.set("original_type", "nested_sequence")
            
            # 处理高级效果
            if xml_element.tag == "effect":
                effect_type = xml_element.get("type", "")
                # 检查是否为高级效果
                if effect_type in ["blur", "color", "transform", "audio", "3d"]:
                    if target_version < "3.0":
                        # 版本2.9.5只支持transition效果
                        if target_version >= "2.9" and effect_type == "transition":
                            # 保留transition效果
                            pass
                        else:
                            # 将不支持的效果转换为备注
                            xml_element.tag = "comment"
                            xml_element.set("original_effect", effect_type)
                            xml_element.set("conversion_note", "效果在目标版本中不支持")
            
            # 处理关键帧动画
            for child in xml_element.findall(".//keyframe"):
                if target_version < "2.9":
                    # 2.9以下版本不支持关键帧动画
                    parent = child.find("..")
                    if parent is not None:
                        # 移除关键帧，保留首帧值
                        first_keyframe = parent.find("keyframe")
                        if first_keyframe is not None:
                            value = first_keyframe.get("value")
                            parent.set("static_value", value)
                        # 移除所有关键帧
                        for kf in parent.findall("keyframe"):
                            parent.remove(kf)
            
            # 处理效果层
            if xml_element.tag == "effects_track":
                if target_version < "2.9":
                    # 2.9以下版本不支持效果层
                    parent = xml_element.find("..")
                    if parent is not None:
                        parent.remove(xml_element)
            
            # 处理音频特效
            if xml_element.tag == "audio_effect":
                if target_version < "3.0":
                    # 3.0以下版本不支持音频特效
                    parent = xml_element.find("..")
                    if parent is not None:
                        parent.remove(xml_element)
            
            # 递归处理所有子元素
            for child in list(xml_element):
                downgrade_attributes(child, target_version)
                
        return True
    except Exception as e:
        logger.error(f"降级属性时出错: {str(e)}")
        return False

def process_xml_file(input_file: str, output_file: str, target_version: str) -> bool:
    """
    处理XML文件，降级其中的属性
    
    Args:
        input_file: 输入XML文件路径
        output_file: 输出XML文件路径
        target_version: 目标版本号
        
    Returns:
        bool: 处理是否成功
    """
    try:
        # 解析XML文件
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        # 获取原始版本
        original_version = root.get("version", "unknown")
        
        # 如果原始版本已经低于或等于目标版本，无需降级
        if compare_versions(original_version, target_version) <= 0:
            logger.info(f"原始版本 {original_version} 已经低于或等于目标版本 {target_version}，无需降级")
            # 直接复制文件
            if input_file != output_file:
                with open(input_file, 'rb') as src, open(output_file, 'wb') as dst:
                    dst.write(src.read())
            return True
        
        # 更新根元素的版本属性
        root.set("version", target_version)
        
        # 降级属性
        success = downgrade_attributes(root, target_version)
        if not success:
            return False
        
        # 保存修改后的XML
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        
        logger.info(f"成功将XML从版本 {original_version} 降级到 {target_version}")
        return True
    except Exception as e:
        logger.error(f"处理XML文件时出错: {str(e)}")
        return False

def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    
    Args:
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        int: 
            如果version1 > version2，返回1
            如果version1 < version2，返回-1
            如果version1 == version2，返回0
    """
    # 规范化版本号
    v1_parts = normalize_version(version1)
    v2_parts = normalize_version(version2)
    
    # 比较版本号
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1 = v1_parts[i] if i < len(v1_parts) else 0
        v2 = v2_parts[i] if i < len(v2_parts) else 0
        
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    
    # 所有部分都相等
    return 0

def normalize_version(version: str) -> List[int]:
    """
    标准化版本号为整数列表
    
    Args:
        version: 版本号字符串
        
    Returns:
        List[int]: 版本号的整数列表表示
    """
    # 移除版本号前缀（如v, V等）
    if version.lower().startswith('v'):
        version = version[1:]
        
    # 分割版本号
    parts = version.split('.')
    
    # 尝试将每部分转换为整数
    result = []
    for part in parts:
        try:
            result.append(int(part))
        except ValueError:
            # 如果无法转换，尝试提取数字部分
            digits = re.findall(r'\d+', part)
            if digits:
                result.append(int(digits[0]))
            else:
                result.append(0)
    
    return result

def batch_downgrade_directory(input_dir: str, output_dir: str, target_version: str, 
                              file_pattern: str = "*.xml") -> Tuple[int, int]:
    """
    批量降级目录中的XML文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        target_version: 目标版本号
        file_pattern: 文件匹配模式
        
    Returns:
        Tuple[int, int]: 成功处理的文件数量和总文件数量
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取所有匹配的文件
    input_path = Path(input_dir)
    matched_files = list(input_path.glob(file_pattern))
    
    # 统计
    total_files = len(matched_files)
    success_count = 0
    
    # 处理每个文件
    for file_path in matched_files:
        # 构建输出文件路径
        rel_path = file_path.relative_to(input_path)
        output_path = Path(output_dir) / rel_path
        
        # 确保输出文件的目录存在
        os.makedirs(output_path.parent, exist_ok=True)
        
        # 处理文件
        if process_xml_file(str(file_path), str(output_path), target_version):
            success_count += 1
            logger.info(f"成功处理文件: {rel_path}")
        else:
            logger.error(f"处理文件失败: {rel_path}")
    
    return success_count, total_files

def get_supported_versions() -> List[str]:
    """
    获取支持的目标版本列表
    
    Returns:
        List[str]: 支持的版本列表
    """
    # 这里可以集成版本特征库中的版本信息
    try:
        from src.versioning.version_features import get_version_features
        
        # 获取版本特征库
        version_features = get_version_features()
        
        # 获取所有版本信息
        all_versions = version_features.get_all_versions()
        
        # 提取版本号
        return [v.get('version') for v in all_versions if 'version' in v]
    except ImportError:
        # 如果无法导入版本特征库，返回默认支持的版本
        return ["2.0.0", "2.5.0", "2.9.5", "3.0.0"]
    except Exception as e:
        logger.error(f"获取支持的版本列表时出错: {str(e)}")
        return ["2.0.0", "2.5.0", "2.9.5", "3.0.0"]


if __name__ == "__main__":
    import sys
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) < 4:
        print("用法: python attribute_downgrader.py <input_file> <output_file> <target_version>")
        print("或者: python attribute_downgrader.py --batch <input_dir> <output_dir> <target_version>")
        sys.exit(1)
    
    # 检查是否为批处理模式
    if sys.argv[1] == "--batch":
        if len(sys.argv) < 5:
            print("批处理模式用法: python attribute_downgrader.py --batch <input_dir> <output_dir> <target_version>")
            sys.exit(1)
            
        input_dir = sys.argv[2]
        output_dir = sys.argv[3]
        target_version = sys.argv[4]
        
        print(f"正在批量降级目录 {input_dir} 中的XML文件到版本 {target_version}...")
        success, total = batch_downgrade_directory(input_dir, output_dir, target_version)
        print(f"处理完成. 成功: {success}/{total}")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        target_version = sys.argv[3]
        
        print(f"正在将 {input_file} 降级到版本 {target_version}...")
        if process_xml_file(input_file, output_file, target_version):
            print("降级成功!")
        else:
            print("降级失败!")
            sys.exit(1) 