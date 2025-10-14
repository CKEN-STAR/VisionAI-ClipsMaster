#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映导出便捷工具

提供简单的命令行接口来导出剪映草稿
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def export_from_segments(video_path: str, segments: list, project_name: str, 
                        output_dir: str = None, auto_copy: bool = False):
    """
    从片段列表导出剪映草稿
    
    Args:
        video_path: 视频文件路径
        segments: 片段列表，每个片段包含start_time和end_time
        project_name: 项目名称
        output_dir: 输出目录（默认为data/output）
        auto_copy: 是否自动复制到剪映目录
    """
    from src.exporters.jianying_exporter_adapter import JianyingExporterAdapter
    
    # 准备项目数据
    project_data = {
        "project_name": project_name,
        "segments": []
    }
    
    # 转换片段格式
    for seg in segments:
        project_data["segments"].append({
            "source_file": video_path,
            "start_time": seg["start_time"],
            "end_time": seg["end_time"],
            "duration": seg["end_time"] - seg["start_time"],
            "speed": seg.get("speed", 1.0),
            "volume": seg.get("volume", 1.0)
        })
    
    # 创建导出器
    adapter = JianyingExporterAdapter(width=1920, height=1080, fps=30)
    
    # 导出
    if output_dir is None:
        output_dir = "data/output"
    
    os.makedirs(output_dir, exist_ok=True)
    draft_path = adapter.export_project(project_data, output_dir)
    
    if draft_path:
        print(f"✅ 草稿导出成功: {draft_path}")
        
        # 自动复制到剪映
        if auto_copy:
            copy_to_jianying(draft_path)
        
        return draft_path
    else:
        print("❌ 草稿导出失败")
        return None


def export_from_srt(video_path: str, srt_path: str, project_name: str,
                   output_dir: str = None, auto_copy: bool = False):
    """
    从SRT字幕文件导出剪映草稿
    
    Args:
        video_path: 视频文件路径
        srt_path: SRT字幕文件路径
        project_name: 项目名称
        output_dir: 输出目录
        auto_copy: 是否自动复制到剪映目录
    """
    from src.exporters.jianying_exporter_adapter import JianyingExporterAdapter
    
    # 解析SRT文件
    subtitles = parse_srt_file(srt_path)
    
    # 创建导出器
    adapter = JianyingExporterAdapter(width=1920, height=1080, fps=30)
    
    # 导出
    if output_dir is None:
        output_dir = "data/output"
    
    os.makedirs(output_dir, exist_ok=True)
    draft_path = adapter.export_from_subtitles(video_path, subtitles, output_dir, project_name)
    
    if draft_path:
        print(f"✅ 草稿导出成功: {draft_path}")
        
        # 自动复制到剪映
        if auto_copy:
            copy_to_jianying(draft_path)
        
        return draft_path
    else:
        print("❌ 草稿导出失败")
        return None


def parse_srt_file(srt_path: str) -> list:
    """解析SRT字幕文件"""
    import re
    
    subtitles = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割字幕块
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # 解析时间码
        time_line = lines[1]
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
        
        if match:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups()
            
            start_time = int(h1) * 3600 + int(m1) * 60 + int(s1) + int(ms1) / 1000
            end_time = int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2) / 1000
            
            text = '\n'.join(lines[2:])
            
            subtitles.append({
                "start_time": start_time,
                "end_time": end_time,
                "text": text
            })
    
    return subtitles


def copy_to_jianying(draft_path: str):
    """复制草稿到剪映目录"""
    import shutil
    
    # 查找剪映草稿目录
    jianying_dirs = [
        os.path.expanduser("~/AppData/Local/JianyingPro/User Data/Projects/com.lveditor.draft"),
        os.path.expanduser("~/AppData/Roaming/JianyingPro/User Data/Projects/com.lveditor.draft"),
    ]
    
    jianying_dir = None
    for dir_path in jianying_dirs:
        if os.path.exists(dir_path):
            jianying_dir = dir_path
            break
    
    if not jianying_dir:
        print("⚠️ 未找到剪映草稿目录，请手动复制")
        return False
    
    # 复制草稿
    draft_name = os.path.basename(draft_path)
    target_path = os.path.join(jianying_dir, draft_name)
    
    if os.path.exists(target_path):
        print(f"⚠️ 目标位置已存在同名草稿，将覆盖")
        shutil.rmtree(target_path)
    
    shutil.copytree(draft_path, target_path)
    print(f"✅ 草稿已复制到剪映: {target_path}")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='剪映导出便捷工具')
    parser.add_argument('--video', required=True, help='视频文件路径')
    parser.add_argument('--srt', help='SRT字幕文件路径（可选）')
    parser.add_argument('--segments', help='片段JSON文件路径（可选）')
    parser.add_argument('--name', default='VisionAI项目', help='项目名称')
    parser.add_argument('--output', help='输出目录（默认为data/output）')
    parser.add_argument('--auto-copy', action='store_true', help='自动复制到剪映目录')
    
    args = parser.parse_args()
    
    # 检查视频文件
    if not os.path.exists(args.video):
        print(f"❌ 视频文件不存在: {args.video}")
        return 1
    
    # 根据输入类型导出
    if args.srt:
        # 从SRT文件导出
        if not os.path.exists(args.srt):
            print(f"❌ SRT文件不存在: {args.srt}")
            return 1
        
        draft_path = export_from_srt(
            args.video, args.srt, args.name,
            args.output, args.auto_copy
        )
    
    elif args.segments:
        # 从片段JSON文件导出
        if not os.path.exists(args.segments):
            print(f"❌ 片段文件不存在: {args.segments}")
            return 1
        
        with open(args.segments, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        draft_path = export_from_segments(
            args.video, segments, args.name,
            args.output, args.auto_copy
        )
    
    else:
        print("❌ 请提供 --srt 或 --segments 参数")
        return 1
    
    if draft_path:
        print("\n📋 下一步:")
        if not args.auto_copy:
            print("1. 手动复制草稿到剪映目录")
            print(f"   复制: {draft_path}")
        print("2. 打开剪映")
        print("3. 在草稿列表中查找项目")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

