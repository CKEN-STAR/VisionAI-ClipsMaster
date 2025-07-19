#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本安全回退机制演示程序

演示如何使用版本回退机制处理不兼容的项目文件
"""

import os
import sys
import xml.etree.ElementTree as ET

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ''))
sys.path.insert(0, root_dir)

# 仅用于演示：临时禁用验证版本兼容性功能，以确保示例正常工作
import unittest.mock

# 导入所需的模块
from src.exporters.version_fallback import safe_export, version_specific_export, VersionCompatibilityError

# 临时修改validate_version_compatibility函数作演示用途
import src.exporters.version_fallback
original_validate = src.exporters.version_fallback.validate_version_compatibility

def mock_validate(root, target_version):
    """演示用模拟验证函数"""
    # 2.0.0版本不兼容4K和HDR和嵌套序列
    if target_version == "2.0.0":
        resolution = root.find(".//resolution")
        if resolution is not None:
            width = resolution.get("width", "1920")
            height = resolution.get("height", "1080")
            if int(width) > 1280 or int(height) > 720:
                return False, ["分辨率超过版本2.0.0支持的最大值 (1280x720)"]
        
        # 检查HDR
        if root.find(".//color_space[@hdr='true']") is not None:
            return False, ["HDR功能在版本2.0.0中不支持"]
        
        # 检查嵌套序列
        if root.find(".//nested_sequence") is not None:
            return False, ["嵌套序列功能在版本2.0.0中不支持"]
    
    # 3.0.0版本兼容所有功能
    return True, []

# 设置模拟验证函数
src.exporters.version_fallback.validate_version_compatibility = mock_validate

def demonstrate_safe_export():
    """演示安全导出功能"""
    print("="*50)
    print("版本安全回退机制演示")
    print("="*50)
    
    # 加载示例XML文件
    sample_xml_path = os.path.join(root_dir, 'sample_v3.xml')
    if not os.path.exists(sample_xml_path):
        # 如果示例文件不存在，创建一个4K HDR项目的XML
        complex_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <info>
    <metadata>
      <title>4K示例项目</title>
      <creator>VisionAI-ClipsMaster</creator>
      <description>具有高级功能的项目</description>
    </metadata>
    <project_settings>
      <resolution width="3840" height="2160"/>
      <frame_rate>30</frame_rate>
      <color_space hdr="true"/>
    </project_settings>
  </info>
  <resources>
    <video id="video1" path="videos/sample_4k.mp4"/>
    <audio id="audio1" path="audio/background.mp3"/>
  </resources>
  <timeline id="main_timeline" duration="00:05:30.000">
    <video_track>
      <clip start="00:00:00.000" end="00:01:30.000" resource_id="video1">
        <effects>
          <color_correction brightness="1.2" contrast="1.1"/>
          <blur amount="0.3"/>
        </effects>
        <keyframes>
          <keyframe time="00:00:00.000" zoom="1.0"/>
          <keyframe time="00:00:05.000" zoom="1.2"/>
          <keyframe time="00:00:10.000" zoom="1.0"/>
        </keyframes>
      </clip>
      <nested_sequence id="nested1" start="00:01:30.000" end="00:03:00.000">
        <timeline id="nested_timeline" duration="00:01:30.000">
          <video_track>
            <clip start="00:00:00.000" end="00:01:30.000" resource_id="video1"/>
          </video_track>
        </timeline>
      </nested_sequence>
    </video_track>
    <audio_track>
      <clip start="00:00:00.000" end="00:05:30.000" resource_id="audio1">
        <audio_effect type="fade_in" duration="2.0"/>
        <audio_effect type="fade_out" duration="3.0"/>
      </clip>
    </audio_track>
    <effects_track>
      <effect start="00:00:00.000" end="00:01:00.000" type="3d_rotation" angle="45"/>
    </effects_track>
  </timeline>
</project>
"""
        with open(sample_xml_path, 'w', encoding='utf-8') as f:
            f.write(complex_xml)
        
        print(f"创建了示例XML文件: {sample_xml_path}")
    
    try:
        # 加载XML
        with open(sample_xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print("加载的XML包含以下高级功能:")
        root = ET.fromstring(xml_content)
        
        # 检查分辨率
        resolution = root.find(".//resolution")
        if resolution is not None:
            width = resolution.get("width", "1920")
            height = resolution.get("height", "1080")
            print(f"- 分辨率: {width}x{height}")
        
        # 检查HDR
        color_space = root.find(".//color_space")
        has_hdr = color_space is not None and color_space.get("hdr") == "true"
        print(f"- HDR支持: {'是' if has_hdr else '否'}")
        
        # 检查嵌套序列
        nested_sequences = root.findall(".//nested_sequence")
        print(f"- 嵌套序列: {'是' if nested_sequences else '否'}")
        
        # 检查关键帧
        keyframes = root.findall(".//keyframe")
        print(f"- 关键帧: {'是' if keyframes else '否'}")
        
        # 检查3D效果
        effects_3d = root.findall(".//effect[@type='3d_rotation']")
        print(f"- 3D效果: {'是' if effects_3d else '否'}")
        
        # 检查音频效果
        audio_effects = root.findall(".//audio_effect")
        print(f"- 音频效果: {'是' if audio_effects else '否'}")
        
        print("\n1. 导出到兼容版本 (3.0.0):")
        try:
            result = version_specific_export(xml_content, "3.0.0")
            print("✓ 成功导出到3.0.0版本")
        except VersionCompatibilityError as e:
            print(f"✗ 导出失败: {e}")
            print(f"  问题: {', '.join(e.issues)}")
        
        print("\n2. 导出到不兼容版本 (2.0.0):")
        try:
            result = version_specific_export(xml_content, "2.0.0")
            print("✓ 成功导出到2.0.0版本")
        except VersionCompatibilityError as e:
            print(f"✗ 导出失败: {e}")
            print(f"  问题: {', '.join(e.issues)}")
        
        print("\n3. 使用安全导出到不兼容版本 (2.0.0):")
        result = safe_export(xml_content, "2.0.0")
        print("✓ 安全导出成功 (使用基础模板)")
        
        # 保存基础模板结果
        fallback_path = os.path.join(root_dir, 'examples', 'fallback_result.xml')
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"已保存回退模板结果到: {fallback_path}")
        
        # 解析结果并验证基本结构
        fallback_root = ET.fromstring(result)
        print("\n安全回退结果验证:")
        
        # 检查分辨率
        resolution = fallback_root.find(".//resolution")
        if resolution is not None:
            width = resolution.get("width", "1920")
            height = resolution.get("height", "1080")
            print(f"- 分辨率: {width}x{height}")
        
        # 检查基本结构
        info = fallback_root.find("info")
        metadata = fallback_root.find("info/metadata")
        project_settings = fallback_root.find("info/project_settings")
        resources = fallback_root.find("resources")
        timeline = fallback_root.find("timeline")
        
        print(f"- 基本信息节点: {'存在' if info else '缺失'}")
        print(f"- 元数据节点: {'存在' if metadata else '缺失'}")
        print(f"- 项目设置节点: {'存在' if project_settings else '缺失'}")
        print(f"- 资源节点: {'存在' if resources else '缺失'}")
        print(f"- 时间线节点: {'存在' if timeline else '缺失'}")
        
        print("\n演示完成！")
        
    except Exception as e:
        print(f"演示过程中出错: {e}")
    
    finally:
        # 恢复原始验证函数
        src.exporters.version_fallback.validate_version_compatibility = original_validate

if __name__ == "__main__":
    demonstrate_safe_export() 