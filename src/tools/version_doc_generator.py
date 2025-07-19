#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多版本文档生成器

该脚本自动生成有关版本兼容性的详细文档，包括各版本的特性对比、
兼容性表格和迁移指南等，方便用户理解和使用不同版本的功能。
"""

import os
import sys
import json
import yaml
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.exporters.node_compat import get_version_specification
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("version_doc_generator")

def load_version_specs() -> Dict[str, Any]:
    """
    加载版本规格文件
    
    Returns:
        Dict[str, Any]: 版本规格字典
    """
    spec_path = os.path.join(root_dir, 'configs', 'version_specifications.json')
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            specs = json.load(f)
        return specs
    except Exception as e:
        logger.error(f"加载版本规格文件失败: {e}")
        return {}

def generate_version_compat_doc() -> str:
    """
    生成版本兼容性说明文档
    
    Returns:
        str: 生成的Markdown格式文档
    """
    version_specs = load_version_specs()
    if not version_specs:
        return "# 版本兼容性文档\n\n无法加载版本规格信息，请检查配置文件。"
    
    # 排序版本号，从高到低
    versions = sorted(version_specs.keys(), key=lambda v: [int(x) for x in v.split('.')], reverse=True)
    
    # 文档标题和简介
    doc = [
        "# VisionAI-ClipsMaster 版本兼容性文档",
        "",
        "本文档自动生成于 " + datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
        "## 简介",
        "",
        "VisionAI-ClipsMaster支持多个版本的项目格式，每个版本具有不同的功能和限制。本文档详细介绍各版本之间的差异和兼容性，帮助用户选择合适的版本并实现跨版本协作。",
        "",
        "版本兼容性模块提供以下功能：",
        "",
        "- **版本检测**: 自动识别项目文件的版本",
        "- **兼容性验证**: 检查项目是否与目标版本兼容",
        "- **安全回退**: 当版本不兼容时，提供安全回退机制",
        "- **节点补偿**: 自动添加必要的节点，确保版本兼容",
        "- **版本建议**: 根据项目需求，推荐适合的版本",
        "",
    ]
    
    # 版本概览表格
    doc.extend([
        "## 版本概览",
        "",
        "| 版本 | 分辨率上限 | 支持HDR | 嵌套序列 | 效果层 | 关键帧 | 3D效果 | 色彩分级 | 音频效果 | 多轨道 |",
        "|------|-----------|---------|----------|--------|--------|--------|----------|----------|--------|",
    ])
    
    for version in versions:
        spec = version_specs[version]
        features = spec.get("supported_features", [])
        
        has_4k = "4k_resolution" in features
        has_hdr = "hdr" in features
        has_nested = "nested_sequences" in features
        has_effects_layers = "effects_layers" in features
        has_keyframes = "keyframes" in features
        has_3d = "3d_effects" in features
        has_color = "color_grading" in features
        has_audio = "audio_effects" in features
        has_multi = "multi_track" in features
        
        resolution = "4K (3840x2160)" if has_4k else "HD (1920x1080)" if "hd_resolution" in features else "SD (1280x720)"
        
        row = f"| {version} | {resolution} | {'✓' if has_hdr else '✗'} | {'✓' if has_nested else '✗'} | {'✓' if has_effects_layers else '✗'} | {'✓' if has_keyframes else '✗'} | {'✓' if has_3d else '✗'} | {'✓' if has_color else '✗'} | {'✓' if has_audio else '✗'} | {'✓' if has_multi else '✗'} |"
        doc.append(row)
    
    # 各版本详情
    doc.extend([
        "",
        "## 版本详情",
        "",
    ])
    
    for version in versions:
        spec = version_specs[version]
        doc.extend([
            f"### 版本 {version}",
            "",
            "#### 必需节点",
            "",
            "```",
        ])
        
        # 添加必需节点列表
        for node in spec.get("required_nodes", []):
            doc.append(node)
        
        doc.extend([
            "```",
            "",
            "#### 支持功能",
            "",
        ])
        
        # 添加支持的功能
        features = spec.get("supported_features", [])
        for feature in features:
            doc.append(f"- {feature}")
        
        # 添加不支持的节点
        if "unsupported_nodes" in spec:
            doc.extend([
                "",
                "#### 不支持的节点",
                "",
                "```",
            ])
            
            for node in spec.get("unsupported_nodes", []):
                doc.append(node)
            
            doc.extend([
                "```",
                "",
            ])
        else:
            doc.append("")
    
    # 版本兼容性矩阵
    doc.extend([
        "## 版本兼容性矩阵",
        "",
        "下表展示了不同版本之间的兼容性情况：",
        "",
        "| 源版本\\目标版本 | " + " | ".join(versions) + " |",
        "|" + "-" * 15 + "|" + "-" * 9 * len(versions) + "|",
    ])
    
    # 生成兼容性矩阵
    for src_version in versions:
        row = [f"| {src_version} "]
        
        for target_version in versions:
            if src_version == target_version:
                row.append("✓")  # 相同版本完全兼容
            elif all(v in src_version.split(".") for v in target_version.split(".")):
                row.append("✓")  # 目标版本是源版本的子版本
            elif int(src_version.split(".")[0]) > int(target_version.split(".")[0]):
                row.append("✗")  # 主版本降级通常不兼容
            elif int(src_version.split(".")[0]) == int(target_version.split(".")[0]) and int(src_version.split(".")[1]) > int(target_version.split(".")[1]):
                row.append("△")  # 次版本降级部分兼容
            else:
                row.append("✓")  # 升级通常兼容
        
        doc.append(" | ".join(row) + " |")
    
    doc.extend([
        "",
        "兼容性说明：",
        "- ✓: 完全兼容，可以直接使用",
        "- △: 部分兼容，可能需要移除部分功能",
        "- ✗: 不兼容，需要重新创建项目",
        "",
    ])
    
    # 迁移指南
    doc.extend([
        "## 版本迁移指南",
        "",
        "在不同版本之间迁移项目时，需要注意以下事项：",
        "",
    ])
    
    # 降级迁移
    doc.extend([
        "### 降级迁移（高版本到低版本）",
        "",
        "降级迁移通常需要移除不兼容的功能：",
        "",
    ])
    
    # 为每个版本生成降级指南
    for i, version in enumerate(versions[:-1]):
        target_version = versions[i+1]
        current_features = set(version_specs[version].get("supported_features", []))
        target_features = set(version_specs[target_version].get("supported_features", []))
        removed_features = current_features - target_features
        
        if removed_features:
            doc.extend([
                f"#### 从 {version} 降级到 {target_version}",
                "",
                "需要移除的功能：",
                "",
            ])
            
            for feature in removed_features:
                doc.append(f"- {feature}")
            
            doc.append("")
    
    # 升级迁移
    doc.extend([
        "### 升级迁移（低版本到高版本）",
        "",
        "升级迁移通常比较简单，可以直接使用，但需要注意以下事项：",
        "",
        "- 升级后可能会自动使用新版本的特性，例如更高的分辨率",
        "- 升级后可能会启用默认的新功能，需要检查项目设置",
        "- 升级后文件可能无法被旧版本软件打开",
        "",
    ])
    
    # 实用工具
    doc.extend([
        "## 实用工具",
        "",
        "VisionAI-ClipsMaster提供以下工具，帮助用户处理版本兼容性问题：",
        "",
        "### 版本检测",
        "",
        "```python",
        "from src.exporters.version_detector import detect_version",
        "",
        "# 检测文件版本",
        "version_info = detect_version('path/to/project.xml')",
        "print(f'项目版本: {version_info}')",
        "```",
        "",
        "### 兼容性验证",
        "",
        "```python",
        "from src.exporters.node_compat import validate_version_compatibility",
        "import xml.etree.ElementTree as ET",
        "",
        "# 验证项目与特定版本的兼容性",
        "xml_root = ET.parse('path/to/project.xml').getroot()",
        "is_compatible, issues = validate_version_compatibility(xml_root, '2.9.5')",
        "",
        "if is_compatible:",
        "    print('项目与版本兼容')",
        "else:",
        "    print(f'项目与版本不兼容，原因: {issues}')",
        "```",
        "",
        "### 安全导出",
        "",
        "```python",
        "from src.exporters.version_fallback import safe_export",
        "",
        "# 安全导出到特定版本",
        "result = safe_export(xml_content, '2.0.0')",
        "```",
        "",
        "### 版本建议",
        "",
        "```python",
        "from src.ui.version_advisor import suggest_version_with_reason",
        "",
        "# 获取项目建议版本",
        "video_spec = {",
        "    'resolution': [3840, 2160],",
        "    'hdr': True,",
        "    'effects': True",
        "}",
        "version, reasons = suggest_version_with_reason(video_spec)",
        "print(f'建议版本: {version}')",
        "print(f'原因: {reasons}')",
        "```",
        "",
    ])
    
    # 添加说明和最后更新时间
    doc.extend([
        "## 说明",
        "",
        "本文档自动从配置文件生成，反映了当前支持的版本和功能。如有变更，请参考最新文档。",
        "",
        f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ])
    
    return "\n".join(doc)

def generate_version_compat_summary() -> str:
    """
    生成版本兼容性概要文档
    
    Returns:
        str: 生成的Markdown格式文档
    """
    version_specs = load_version_specs()
    if not version_specs:
        return "# 版本兼容性概要\n\n无法加载版本规格信息，请检查配置文件。"
    
    # 排序版本号，从高到低
    versions = sorted(version_specs.keys(), key=lambda v: [int(x) for x in v.split('.')], reverse=True)
    
    # 文档标题和简介
    doc = [
        "# 版本兼容性概要",
        "",
        "本概要列出了VisionAI-ClipsMaster支持的各个版本及其主要特性。",
        "",
    ]
    
    # 版本列表
    for version in versions:
        spec = version_specs[version]
        features = spec.get("supported_features", [])
        
        if "4k_resolution" in features:
            resolution = "4K (3840x2160)"
        elif "hd_resolution" in features:
            resolution = "HD (1920x1080)"
        else:
            resolution = "SD (1280x720)"
        
        key_features = []
        if "hdr" in features:
            key_features.append("HDR")
        if "nested_sequences" in features:
            key_features.append("嵌套序列")
        if "effects_layers" in features:
            key_features.append("效果层")
        if "3d_effects" in features:
            key_features.append("3D效果")
        
        feature_str = ", ".join(key_features) if key_features else "基本功能"
        
        doc.extend([
            f"## 版本 {version}",
            "",
            f"- **分辨率上限**: {resolution}",
            f"- **主要特性**: {feature_str}",
            f"- **必需节点数**: {len(spec.get('required_nodes', []))}",
            "",
        ])
    
    # 兼容性提示
    doc.extend([
        "## 兼容性提示",
        "",
        "- 高版本通常包含低版本的所有功能",
        "- 从高版本降级到低版本时，可能需要移除部分功能",
        "- 使用安全回退机制可以确保版本转换的可靠性",
        "",
        f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ])
    
    return "\n".join(doc)

def auto_generate_compat_doc():
    """自动生成版本兼容性文档"""
    try:
        # 生成完整文档
        full_doc = generate_version_compat_doc()
        doc_path = os.path.join(root_dir, 'docs', 'VERSION_COMPAT.md')
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(full_doc)
        
        logger.info(f"版本兼容性文档已生成: {doc_path}")
        
        # 生成概要文档
        summary_doc = generate_version_compat_summary()
        summary_path = os.path.join(root_dir, 'docs', 'VERSION_COMPAT_SUMMARY.md')
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_doc)
        
        logger.info(f"版本兼容性概要已生成: {summary_path}")
        
        # 为中文和英文文档目录也生成文档
        zh_doc_path = os.path.join(root_dir, 'docs', 'zh_CN', 'VERSION_COMPAT.md')
        en_doc_path = os.path.join(root_dir, 'docs', 'en_US', 'VERSION_COMPAT.md')
        
        # 确保目录存在
        os.makedirs(os.path.dirname(zh_doc_path), exist_ok=True)
        os.makedirs(os.path.dirname(en_doc_path), exist_ok=True)
        
        # 复制文档（注意：这里应该有适当的翻译，但为简化起见，直接复制）
        with open(zh_doc_path, 'w', encoding='utf-8') as f:
            f.write(full_doc)
        
        # 英文文档需要翻译（简化处理，仅替换标题）
        en_doc = full_doc.replace("VisionAI-ClipsMaster 版本兼容性文档", 
                                  "VisionAI-ClipsMaster Version Compatibility Documentation")
        en_doc = en_doc.replace("简介", "Introduction")
        en_doc = en_doc.replace("版本概览", "Version Overview")
        en_doc = en_doc.replace("版本详情", "Version Details")
        en_doc = en_doc.replace("版本兼容性矩阵", "Version Compatibility Matrix")
        en_doc = en_doc.replace("版本迁移指南", "Version Migration Guide")
        en_doc = en_doc.replace("实用工具", "Utility Tools")
        en_doc = en_doc.replace("说明", "Notes")
        en_doc = en_doc.replace("最后更新", "Last Updated")
        
        with open(en_doc_path, 'w', encoding='utf-8') as f:
            f.write(en_doc)
        
        logger.info(f"版本兼容性文档已生成(中文): {zh_doc_path}")
        logger.info(f"版本兼容性文档已生成(英文): {en_doc_path}")
        
        return True
    except Exception as e:
        logger.error(f"生成版本兼容性文档失败: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='生成版本兼容性文档')
    parser.add_argument('--update', action='store_true', help='更新现有文档')
    args = parser.parse_args()
    
    success = auto_generate_compat_doc()
    
    if success:
        print("版本兼容性文档生成成功!")
    else:
        print("版本兼容性文档生成失败，请查看日志。") 