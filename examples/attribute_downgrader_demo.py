#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
属性降级处理器演示程序

演示如何使用属性降级处理器将高版本XML文件转换为低版本兼容格式。
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入属性降级处理器
try:
    from src.exporters.attribute_downgrader import (
        process_xml_file, 
        batch_downgrade_directory,
        get_supported_versions
    )
except ImportError as e:
    print(f"导入属性降级处理器出错: {e}")
    sys.exit(1)

def create_sample_xml(output_file: str, version: str = "3.0.0") -> bool:
    """
    创建示例XML文件用于测试
    
    Args:
        output_file: 输出文件路径
        version: XML文件版本
        
    Returns:
        bool: 是否创建成功
    """
    try:
        # 创建XML文档
        doc = minidom.getDOMImplementation().createDocument(None, "jianying_project", None)
        root = doc.documentElement
        
        # 设置版本属性
        root.setAttribute("version", version)
        
        # 添加基本结构
        info = doc.createElement("info")
        metadata = doc.createElement("metadata")
        project_settings = doc.createElement("project_settings")
        
        # 填充元数据
        jy_type = doc.createElement("jy_type")
        jy_type.appendChild(doc.createTextNode("project"))
        
        project_id = doc.createElement("project_id")
        project_id.appendChild(doc.createTextNode("sample_001"))
        
        title = doc.createElement("title")
        title.appendChild(doc.createTextNode("示例项目"))
        
        metadata.appendChild(jy_type)
        metadata.appendChild(project_id)
        metadata.appendChild(title)
        info.appendChild(metadata)
        
        # 添加项目设置 - 高分辨率
        resolution = doc.createElement("resolution")
        resolution.setAttribute("width", "3840")
        resolution.setAttribute("height", "2160")
        
        frame_rate = doc.createElement("frame_rate")
        frame_rate.appendChild(doc.createTextNode("30.0"))
        
        # HDR支持
        color_space = doc.createElement("color_space")
        color_space.setAttribute("hdr", "true")
        color_space.setAttribute("type", "rec2020")
        
        project_settings.appendChild(resolution)
        project_settings.appendChild(frame_rate)
        project_settings.appendChild(color_space)
        info.appendChild(project_settings)
        
        # 添加资源和时间线
        resources = doc.createElement("resources")
        timeline = doc.createElement("timeline")
        timeline.setAttribute("id", "timeline_001")
        timeline.setAttribute("duration", "00:01:00.000")
        
        # 添加多个轨道
        for i in range(3):
            track = doc.createElement("track")
            track.setAttribute("id", f"video_track_{i+1}")
            track.setAttribute("type", "video")
            timeline.appendChild(track)
            
        for i in range(2):
            track = doc.createElement("track")
            track.setAttribute("id", f"audio_track_{i+1}")
            track.setAttribute("type", "audio")
            timeline.appendChild(track)
            
        # 添加字幕轨
        subtitle_track = doc.createElement("subtitle_track")
        subtitle_track.setAttribute("id", "subtitle_track_1")
        subtitle_track.setAttribute("language", "zh-CN")
        timeline.appendChild(subtitle_track)
            
        # 添加效果层
        effects_track = doc.createElement("effects_track")
        effects_track.setAttribute("id", "effects_track_1")
        timeline.appendChild(effects_track)
        
        # 添加各种效果
        effects = [
            {"type": "blur", "name": "模糊效果"},
            {"type": "color", "name": "颜色调整"},
            {"type": "transform", "name": "变换效果"},
            {"type": "transition", "name": "转场效果"},
            {"type": "audio", "name": "音频效果"},
            {"type": "3d", "name": "3D效果"}
        ]
        
        for i, effect_info in enumerate(effects):
            effect = doc.createElement("effect")
            effect.setAttribute("id", f"effect_{i+1}")
            effect.setAttribute("type", effect_info["type"])
            effect.setAttribute("name", effect_info["name"])
            
            # 添加关键帧
            parameter = doc.createElement("parameter")
            parameter.setAttribute("name", "intensity")
            
            for j in range(3):
                keyframe = doc.createElement("keyframe")
                keyframe.setAttribute("time", f"00:00:{j*10}.000")
                keyframe.setAttribute("value", str(j * 0.3))
                keyframe.setAttribute("interpolation", "linear")
                parameter.appendChild(keyframe)
                
            effect.appendChild(parameter)
            effects_track.appendChild(effect)
        
        # 添加嵌套序列
        nested = doc.createElement("nested_sequence")
        nested.setAttribute("id", "nested_001")
        nested.setAttribute("name", "嵌套场景")
        nested.setAttribute("duration", "00:00:30.000")
        
        nested_track = doc.createElement("track")
        nested_track.setAttribute("id", "nested_track_1")
        nested_track.setAttribute("type", "video")
        
        # 添加嵌套剪辑
        clip = doc.createElement("clip")
        clip.setAttribute("id", "clip_001")
        clip.setAttribute("start", "00:00:00.000")
        clip.setAttribute("duration", "00:00:05.000")
        nested_track.appendChild(clip)
        
        nested.appendChild(nested_track)
        
        # 添加4K标签元素
        fourk_elem = doc.createElement("fourk_tag")
        fourk_elem.setAttribute("enabled", "true")
        fourk_elem.setAttribute("upscale", "false")
        fourk_elem.setAttribute("type", "4K")
        
        # 添加主要部分到根元素
        root.appendChild(info)
        root.appendChild(resources)
        root.appendChild(timeline)
        root.appendChild(nested)
        root.appendChild(fourk_elem)
        
        # 输出格式化的XML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8"))
            
        print(f"创建示例XML文件成功: {output_file}")
        return True
    except Exception as e:
        print(f"创建示例XML文件失败: {str(e)}")
        return False

def compare_xml_files(original_file: str, downgraded_file: str) -> None:
    """
    比较原始XML文件和降级后的XML文件
    
    Args:
        original_file: 原始XML文件路径
        downgraded_file: 降级后的XML文件路径
    """
    try:
        # 解析XML文件
        original_tree = ET.parse(original_file)
        original_root = original_tree.getroot()
        
        downgraded_tree = ET.parse(downgraded_file)
        downgraded_root = downgraded_tree.getroot()
        
        # 获取版本
        original_version = original_root.get("version", "unknown")
        downgraded_version = downgraded_root.get("version", "unknown")
        
        print(f"\n比较 XML 文件:")
        print(f"原始版本: {original_version}")
        print(f"降级版本: {downgraded_version}")
        
        # 分析变化
        print("\n主要变化:")
        
        # 检查分辨率
        original_res = original_root.find(".//resolution")
        downgraded_res = downgraded_root.find(".//resolution")
        
        if original_res is not None and downgraded_res is not None:
            original_width = original_res.get("width", "0")
            original_height = original_res.get("height", "0")
            downgraded_width = downgraded_res.get("width", "0")
            downgraded_height = downgraded_res.get("height", "0")
            
            if original_width != downgraded_width or original_height != downgraded_height:
                print(f"- 分辨率: {original_width}x{original_height} -> {downgraded_width}x{downgraded_height}")
        
        # 检查4K标签
        original_4k = original_root.find(".//fourk_tag[@type='4K']")
        downgraded_4k = downgraded_root.find(".//fourk_tag[@type='4K']")
        downgraded_hd = downgraded_root.find(".//fourk_tag[@type='HD']")
        
        if original_4k is not None and downgraded_4k is None and downgraded_hd is not None:
            print(f"- 标签: 4K -> HD")
            if downgraded_hd.get("super_sample") == "true":
                print(f"  添加了 super_sample 属性: true")
        
        # 检查HDR属性
        original_hdr = original_root.find(".//*[@hdr='true']")
        downgraded_hdr = downgraded_root.find(".//*[@hdr='true']")
        
        if original_hdr is not None and downgraded_hdr is None:
            print(f"- HDR: 已移除")
            colorspace_elem = downgraded_root.find(".//*[@converted_from_hdr='true']")
            if colorspace_elem is not None:
                print(f"  添加了 converted_from_hdr 属性: true")
        
        # 检查嵌套序列
        original_nested = original_root.find(".//nested_sequence")
        downgraded_nested = downgraded_root.find(".//nested_sequence")
        
        if original_nested is not None:
            if downgraded_nested is None:
                flattened = downgraded_root.find(".//*[@original_type='nested_sequence']")
                if flattened is not None:
                    print(f"- 嵌套序列: 转换为普通剪辑")
                    print(f"  添加了 flattened 属性: {flattened.get('flattened')}")
                else:
                    print(f"- 嵌套序列: 已移除")
            else:
                print(f"- 嵌套序列: 保留")
        
        # 检查效果
        original_effects = original_root.findall(".//effect")
        downgraded_effects = downgraded_root.findall(".//effect")
        
        if len(original_effects) != len(downgraded_effects):
            print(f"- 效果: {len(original_effects)} -> {len(downgraded_effects)}")
            
            # 查找转换为备注的效果
            comments = downgraded_root.findall(".//*[@original_effect]")
            if comments:
                print(f"  {len(comments)} 个效果转换为备注")
        
        # 检查关键帧
        original_keyframes = original_root.findall(".//keyframe")
        downgraded_keyframes = downgraded_root.findall(".//keyframe")
        
        if len(original_keyframes) != len(downgraded_keyframes):
            print(f"- 关键帧: {len(original_keyframes)} -> {len(downgraded_keyframes)}")
            
            # 检查是否添加了静态值
            static_values = downgraded_root.findall(".//*[@static_value]")
            if static_values:
                print(f"  {len(static_values)} 个参数转换为静态值")
        
        # 检查轨道数量
        original_tracks = original_root.findall(".//track")
        downgraded_tracks = downgraded_root.findall(".//track")
        
        if len(original_tracks) != len(downgraded_tracks):
            print(f"- 轨道数量: {len(original_tracks)} -> {len(downgraded_tracks)}")
            
        # 检查效果层
        original_effects_track = original_root.find(".//effects_track")
        downgraded_effects_track = downgraded_root.find(".//effects_track")
        
        if original_effects_track is not None and downgraded_effects_track is None:
            print(f"- 效果层: 已移除")
        
        print("\n降级处理完成。")
        
    except Exception as e:
        print(f"比较XML文件时出错: {str(e)}")

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="属性降级处理器演示程序")
    
    # 获取支持的版本
    supported_versions = get_supported_versions()
    version_choices = supported_versions if supported_versions else ["2.0.0", "2.5.0", "2.9.5", "3.0.0"]
    
    # 创建子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 创建示例文件命令
    create_parser = subparsers.add_parser("create", help="创建示例XML文件")
    create_parser.add_argument("--output", "-o", default="sample.xml", help="输出文件路径")
    create_parser.add_argument("--version", "-v", default="3.0.0", help="XML文件版本")
    
    # 降级文件命令
    downgrade_parser = subparsers.add_parser("downgrade", help="降级XML文件")
    downgrade_parser.add_argument("input_file", help="输入XML文件路径")
    downgrade_parser.add_argument("--output", "-o", help="输出文件路径")
    downgrade_parser.add_argument("--target-version", "-t", choices=version_choices, required=True, help="目标版本")
    downgrade_parser.add_argument("--compare", "-c", action="store_true", help="比较原始和降级后的文件")
    
    # 批量降级命令
    batch_parser = subparsers.add_parser("batch", help="批量降级XML文件")
    batch_parser.add_argument("input_dir", help="输入目录")
    batch_parser.add_argument("output_dir", help="输出目录")
    batch_parser.add_argument("--target-version", "-t", choices=version_choices, required=True, help="目标版本")
    batch_parser.add_argument("--pattern", "-p", default="*.xml", help="文件匹配模式")
    
    # 创建并降级命令
    demo_parser = subparsers.add_parser("demo", help="创建示例文件并降级")
    demo_parser.add_argument("--output-dir", "-o", default=".", help="输出目录")
    demo_parser.add_argument("--target-version", "-t", choices=version_choices, default="2.0.0", help="目标版本")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "create":
        create_sample_xml(args.output, args.version)
    elif args.command == "downgrade":
        output_file = args.output if args.output else f"{os.path.splitext(args.input_file)[0]}_v{args.target_version}.xml"
        
        if process_xml_file(args.input_file, output_file, args.target_version):
            print(f"文件已成功降级到版本 {args.target_version}")
            print(f"降级后的文件: {output_file}")
            
            if args.compare:
                compare_xml_files(args.input_file, output_file)
        else:
            print("降级失败!")
    elif args.command == "batch":
        success, total = batch_downgrade_directory(args.input_dir, args.output_dir, args.target_version, args.pattern)
        print(f"处理完成. 成功: {success}/{total}")
    elif args.command == "demo":
        # 确保输出目录存在
        os.makedirs(args.output_dir, exist_ok=True)
        
        # 创建示例文件
        sample_file = os.path.join(args.output_dir, "sample_v3.0.0.xml")
        if create_sample_xml(sample_file, "3.0.0"):
            # 降级文件
            output_file = os.path.join(args.output_dir, f"sample_v{args.target_version}.xml")
            
            if process_xml_file(sample_file, output_file, args.target_version):
                print(f"文件已成功降级到版本 {args.target_version}")
                print(f"降级后的文件: {output_file}")
                
                compare_xml_files(sample_file, output_file)
            else:
                print("降级失败!")
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