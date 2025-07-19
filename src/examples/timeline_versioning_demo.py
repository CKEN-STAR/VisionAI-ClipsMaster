#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时间轴版本控制演示脚本

展示如何在短剧混剪项目中使用TimelineArchiver进行时间轴版本管理，
包括保存、加载、比较不同版本的场景时间轴数据。
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.timecode import TimelineArchiver

# 模拟场景数据
def create_initial_scenes():
    """创建初始场景数据，模拟从原片字幕分析得到的场景列表"""
    return [
        {
            "id": "scene_001",
            "source_file": "episode1.mp4",
            "start_time": 120.5,
            "end_time": 135.2,
            "duration": 14.7,
            "text": "你知道吗？我已经等这一天很久了。",
            "character": "男主角",
            "emotion": "期待",
            "importance": 0.75
        },
        {
            "id": "scene_002",
            "source_file": "episode1.mp4",
            "start_time": 210.3,
            "end_time": 218.5,
            "duration": 8.2,
            "text": "我从未想过会以这种方式相遇。",
            "character": "女主角",
            "emotion": "惊讶",
            "importance": 0.85
        },
        {
            "id": "scene_003",
            "source_file": "episode2.mp4",
            "start_time": 45.8,
            "end_time": 58.2,
            "duration": 12.4,
            "text": "命运有时就是如此奇妙，不是吗？",
            "character": "男主角",
            "emotion": "思考",
            "importance": 0.65
        }
    ]

def modify_scenes_version1(scenes):
    """对场景进行第一次修改，模拟剧本重构后的结果"""
    new_scenes = scenes.copy()
    
    # 修改现有场景的文本和情感
    new_scenes[0]["text"] = "等待这一刻，我已经期盼了很久。"
    new_scenes[0]["emotion"] = "激动"
    
    # 添加新场景
    new_scenes.append({
        "id": "scene_004",
        "source_file": "episode3.mp4",
        "start_time": 78.3,
        "end_time": 85.7,
        "duration": 7.4,
        "text": "有些相遇，注定改变一生。",
        "character": "旁白",
        "emotion": "深沉",
        "importance": 0.9
    })
    
    return new_scenes

def modify_scenes_version2(scenes):
    """对场景进行第二次修改，模拟爆款风格调整后的结果"""
    new_scenes = scenes.copy()
    
    # 删除不重要的场景
    new_scenes = [scene for scene in new_scenes if scene["id"] != "scene_003"]
    
    # 调整场景顺序（将最后一个场景移到开头）
    last_scene = new_scenes.pop()
    new_scenes.insert(0, last_scene)
    
    # 修改文本，使其更有冲击力
    new_scenes[0]["text"] = "有些相遇，注定改变一生！命运的转折就此开始..."
    new_scenes[0]["emotion"] = "震撼"
    
    # 添加高潮场景
    new_scenes.append({
        "id": "scene_005",
        "source_file": "episode4.mp4",
        "start_time": 143.9,
        "end_time": 151.2,
        "duration": 7.3,
        "text": "这一切，究竟是巧合，还是命中注定？",
        "character": "男主角",
        "emotion": "困惑",
        "importance": 0.95
    })
    
    return new_scenes

def display_version_info(version_info):
    """格式化显示版本信息"""
    print(f"\n版本ID: {version_info['version_id']}")
    print(f"创建时间: {version_info['formatted_time']}")
    print(f"场景数量: {version_info['scene_count']}")
    print(f"描述: {version_info['note']}")
    print(f"当前激活: {'是' if version_info['is_current'] else '否'}")

def display_scene_summary(scenes):
    """显示场景摘要信息"""
    print("\n场景摘要:")
    print("-" * 80)
    print(f"{'ID':<10} {'角色':<8} {'情感':<6} {'时长':>6} {'文本'}")
    print("-" * 80)
    
    for scene in scenes:
        print(f"{scene['id']:<10} {scene['character']:<8} {scene['emotion']:<6} {scene['duration']:>6.1f}s {scene['text'][:40]}")
    
    total_duration = sum(scene['duration'] for scene in scenes)
    print("-" * 80)
    print(f"总时长: {total_duration:.1f}秒 ({total_duration/60:.1f}分钟)")

def display_comparison(comparison):
    """显示版本比较结果"""
    print("\n版本比较:")
    print("-" * 80)
    print(f"版本 {comparison['version1']['id']} ({comparison['version1']['time']})")
    print(f"vs")
    print(f"版本 {comparison['version2']['id']} ({comparison['version2']['time']})")
    print("-" * 80)
    print(f"场景数量变化: {comparison['scene_diff']:+d} 个场景")
    print(f"总时长变化: {comparison['total_duration_diff']:+.1f} 秒")
    print("-" * 80)

def main():
    """主函数"""
    print("=" * 80)
    print("短剧混剪时间轴版本管理演示")
    print("=" * 80)
    
    # 设置测试目录
    output_dir = os.path.join(root_dir, "data", "output", "demo_versions")
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 初始化时间轴存档器
    project_name = f"short_drama_mix_{int(time.time())}"
    archiver = TimelineArchiver(project_name, output_dir)
    print(f"项目名称: {project_name}")
    
    # 创建初始场景数据
    initial_scenes = create_initial_scenes()
    
    # 保存初始版本
    initial_version_id = archiver.save_version(
        initial_scenes, 
        "初始分析结果 - 从原片字幕提取的关键场景"
    )
    print(f"\n✓ 保存初始版本: {initial_version_id}")
    
    # 显示场景摘要
    display_scene_summary(initial_scenes)
    
    # 创建并保存修改版本1
    modified_scenes1 = modify_scenes_version1(initial_scenes)
    modified_version1_id = archiver.save_version(
        modified_scenes1,
        "剧本重构 - 调整台词和情感，添加旁白"
    )
    print(f"\n✓ 保存修改版本1: {modified_version1_id}")
    
    # 创建并保存修改版本2
    modified_scenes2 = modify_scenes_version2(modified_scenes1)
    modified_version2_id = archiver.save_version(
        modified_scenes2,
        "爆款风格优化 - 重排序场景，增强情感冲击力"
    )
    print(f"\n✓ 保存修改版本2: {modified_version2_id}")
    
    # 获取所有版本列表
    version_list = archiver.get_version_list()
    print(f"\n共有 {len(version_list)} 个版本:")
    for version in version_list:
        display_version_info(version)
    
    # 加载并显示最终版本
    final_scenes = archiver.load_version(modified_version2_id)
    print("\n最终版本场景:")
    display_scene_summary(final_scenes)
    
    # 比较初始版本和最终版本的差异
    comparison = archiver.compare_versions(initial_version_id, modified_version2_id)
    display_comparison(comparison)
    
    # 导出最终版本
    export_path = os.path.join(output_dir, f"{project_name}_final.json")
    archiver.export_version(modified_version2_id, export_path)
    print(f"\n✓ 最终版本已导出至: {export_path}")
    
    print("\n版本化时间轴存档演示完成!")
    print(f"所有版本数据存储在: {os.path.join(output_dir, project_name)}")

if __name__ == "__main__":
    main() 