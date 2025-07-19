#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML构建器演示脚本

演示XML构建器的主要功能
"""

from xml_builder import (
    create_base_xml,
    create_project_xml,
    build_scene_timeline,
    xml_to_string,
    convert_seconds_to_timecode
)

def run_demo():
    """运行XML构建器演示"""
    print("=== XML构建器演示开始 ===\n")
    
    # 1. 基础XML结构
    base_xml = create_base_xml()
    print("1. 基础XML结构:")
    print(base_xml)
    
    # 2. 项目XML结构
    project = create_project_xml("演示项目")
    project_xml = xml_to_string(project)
    print("\n\n2. 项目XML结构:")
    print(project_xml)
    
    # 3. 时间码转换
    print("\n\n3. 时间码转换:")
    seconds_samples = [0, 10.5, 60, 3600, 3661.5]
    for seconds in seconds_samples:
        timecode = convert_seconds_to_timecode(seconds)
        print(f"   {seconds}秒 -> {timecode}")
    
    # 4. 场景时间轴构建
    scenes = [
        {"scene_id": "开场", "start_time": 10.5, "duration": 5.0},
        {"scene_id": "转场", "start_time": 25.0, "duration": 3.0},
        {"scene_id": "高潮", "start_time": 45.0, "duration": 8.0, "has_audio": False},
        {"scene_id": "结尾", "start_time": 60.0, "duration": 4.0}
    ]
    
    timeline_xml = build_scene_timeline(
        scenes, 
        "demo_video.mp4",
        "演示时间轴项目"
    )
    
    print("\n\n4. 场景时间轴构建:")
    print(timeline_xml)
    
    # 保存到文件
    with open("demo_timeline.xml", "w", encoding="utf-8") as f:
        f.write(timeline_xml)
    
    print("\n已保存演示时间轴到: demo_timeline.xml")
    print("\n=== XML构建器演示完成 ===")

if __name__ == "__main__":
    run_demo() 