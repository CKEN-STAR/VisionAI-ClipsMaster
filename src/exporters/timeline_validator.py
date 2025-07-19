#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间轴连续性验证模块

提供对VisionAI-ClipsMaster项目中时间轴轨道的连续性验证功能，确保：
1. 时间轴上的片段没有不合理的重叠
2. 片段按时间顺序排列
3. 片段之间的转场和时间跳跃合理
4. 特殊轨道（如字幕、音效）的时间对齐正确
"""

import os
import sys
import logging
from typing import Dict, List, Tuple, Any, Optional, Union, Set
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from collections import defaultdict

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
logger = get_logger("timeline_validator")


class TimelineError(Exception):
    """时间轴错误异常基类"""
    pass


class TimelineConsistencyError(TimelineError):
    """时间轴连续性错误"""
    pass


class TimelineOverlapError(TimelineConsistencyError):
    """片段重叠错误"""
    pass


def validate_timeline_continuity(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    检测视频频轨道连续性错误
    
    验证时间轴上的片段是否按正确顺序排列，没有不合理的重叠或跳跃。
    
    Args:
        tracks: 轨道列表，每个轨道包含clips/items列表
        
    Returns:
        问题列表，每个问题是一个字典，包含错误类型、位置和描述
    """
    logger.info("验证时间轴连续性")
    
    errors = []
    
    # 检查每个轨道
    for track_index, track in enumerate(tracks):
        # 获取轨道类型
        track_type = track.get('type', 'video')
        track_name = track.get('name', f'轨道 {track_index+1}')
        
        # 获取片段列表（兼容不同格式）
        clips = track.get('clips', track.get('items', []))
        
        if not clips:
            logger.debug(f"轨道 '{track_name}' 没有片段")
            continue
            
        # 按开始时间排序
        sorted_clips = sorted(clips, key=lambda x: x.get('start', x.get('start_frame', 0)))
        
        # 检查排序后的片段连续性
        prev_end = 0
        
        for clip_index, clip in enumerate(sorted_clips):
            # 获取片段ID或名称（用于错误报告）
            clip_id = clip.get('id', f"片段{clip_index+1}")
            
            # 获取开始和结束时间（兼容不同格式）
            start = clip.get('start', clip.get('start_frame', 0))
            end = clip.get('end', clip.get('end_frame', 0))
            
            # 1. 检查开始时间是否小于结束时间
            if start >= end:
                errors.append({
                    'type': 'invalid_clip',
                    'track': track_index,
                    'clip': clip_id,
                    'description': f"无效的片段时间范围: {start} - {end}（开始时间应小于结束时间）"
                })
                continue
                
            # 2. 检查与前一个片段的时间关系
            if start < prev_end:
                # 重叠检测
                errors.append({
                    'type': 'overlap',
                    'track': track_index,
                    'clip': clip_id,
                    'description': f"轨道 '{track_name}' 上的片段 '{clip_id}' 与前一个片段重叠（{start} < {prev_end}）"
                })
                
            # 更新前一个片段的结束时间
            prev_end = end
            
    return errors


def validate_timeline_continuity_simple(tracks: List[Dict]) -> None:
    """
    检测视频频轨道连续性错误
    
    Args:
        tracks: 时间轴轨道列表
    
    Raises:
        TimelineError: 当发现时间轴连续性错误时抛出
    """
    prev_end = 0
    for clip in sorted(tracks, key=lambda x: x['start']):
        if clip['start'] < prev_end:
            raise TimelineConsistencyError(f"时间轴重叠: {clip['id']}")
        prev_end = clip['end']


def multi_track_validate_timeline_continuity(tracks: List[Dict[str, Any]]) -> None:
    """
    验证多轨道时间轴连续性
    
    更严格的版本，用于图示样例函数实现
    
    Args:
        tracks: 轨道数据列表
    
    Raises:
        TimelineError: 当发现时间轴连续性错误时抛出
    """
    logger.info("检测视频频轨道连续性错误")
    
    # 这是对应图片中的简化实现
    prev_end = 0
    for clip in sorted(tracks, key=lambda x: x['start']):
        if clip['start'] < prev_end:
            raise TimelineConsistencyError(f"时间轴重叠: {clip['id']}")
        prev_end = clip['end']


def validate_multi_track_timeline(timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    验证多轨道时间轴的复杂连续性
    
    处理多轨道之间的关系，主轨道和辅助轨道（字幕、音效等）的时间对齐。
    
    Args:
        timeline_data: 完整的时间轴数据
        
    Returns:
        问题列表
    """
    errors = []
    
    # 获取轨道
    tracks = timeline_data.get('tracks', [])
    
    # 验证每个轨道的内部连续性
    track_errors = validate_timeline_continuity(tracks)
    errors.extend(track_errors)
    
    # 检查主视频轨道
    video_tracks = [t for t in tracks if t.get('type', 'video') == 'video']
    
    # 如果有视频轨道，检查其他轨道的时间对齐
    if video_tracks:
        main_track = video_tracks[0]  # 假设第一个视频轨道是主轨道
        main_clips = main_track.get('clips', main_track.get('items', []))
        
        if main_clips:
            # 确定主轨道的时间范围
            main_start = min(clip.get('start', clip.get('start_frame', 0)) for clip in main_clips)
            main_end = max(clip.get('end', clip.get('end_frame', 0)) for clip in main_clips)
            
            # 检查其他轨道是否超出主轨道范围
            for track_index, track in enumerate(tracks):
                if track.get('type', 'video') == 'video':
                    continue  # 跳过视频轨道
                    
                track_name = track.get('name', f'轨道 {track_index+1}')
                clips = track.get('clips', track.get('items', []))
                
                for clip_index, clip in enumerate(clips):
                    clip_id = clip.get('id', f"片段{clip_index+1}")
                    start = clip.get('start', clip.get('start_frame', 0))
                    end = clip.get('end', clip.get('end_frame', 0))
                    
                    # 检查是否超出主轨道范围
                    if start < main_start:
                        errors.append({
                            'type': 'alignment',
                            'track': track_index,
                            'clip': clip_id,
                            'description': f"轨道 '{track_name}' 上的 '{clip_id}' 开始时间早于主视频轨道"
                        })
                    
                    if end > main_end:
                        errors.append({
                            'type': 'alignment',
                            'track': track_index,
                            'clip': clip_id,
                            'description': f"轨道 '{track_name}' 上的 '{clip_id}' 结束时间晚于主视频轨道"
                        })
    
    return errors


def check_timeline_gaps(tracks: List[Dict[str, Any]], gap_threshold: int = 0) -> List[Dict[str, Any]]:
    """
    检查时间轴上的时间间隙
    
    在视频编辑中，轨道上的片段之间通常不应该有未覆盖的间隙。
    
    Args:
        tracks: 轨道列表
        gap_threshold: 可接受的最大间隙（单位：帧或时间单位），大于此阈值的间隙会被报告
        
    Returns:
        间隙问题列表
    """
    gaps = []
    
    # 检查每个轨道
    for track_index, track in enumerate(tracks):
        # 跳过非视频轨道
        if track.get('type', 'video') != 'video':
            continue
            
        track_name = track.get('name', f'轨道 {track_index+1}')
        clips = track.get('clips', track.get('items', []))
        
        if len(clips) <= 1:
            continue  # 需要至少两个片段才能检测间隙
            
        # 按开始时间排序
        sorted_clips = sorted(clips, key=lambda x: x.get('start', x.get('start_frame', 0)))
        
        # 检查相邻片段之间的间隙
        for i in range(1, len(sorted_clips)):
            prev_clip = sorted_clips[i-1]
            curr_clip = sorted_clips[i]
            
            prev_end = prev_clip.get('end', prev_clip.get('end_frame', 0))
            curr_start = curr_clip.get('start', curr_clip.get('start_frame', 0))
            
            gap_size = curr_start - prev_end
            
            # 只报告大于阈值的间隙
            if gap_size > gap_threshold:
                prev_id = prev_clip.get('id', f"片段{i}")
                curr_id = curr_clip.get('id', f"片段{i+1}")
                
                gaps.append({
                    'type': 'gap',
                    'track': track_index,
                    'start': prev_end,
                    'end': curr_start,
                    'size': gap_size,
                    'description': f"轨道 '{track_name}' 上在 '{prev_id}' 和 '{curr_id}' 之间存在 {gap_size} 单位的间隙"
                })
    
    return gaps


def check_scene_transition_consistency(timeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    检查场景转场的连续性
    
    分析场景之间的转场是否合理，避免突兀的场景切换。
    
    Args:
        timeline_data: 时间轴数据
        
    Returns:
        场景转场问题列表
    """
    issues = []
    
    # 获取所有转场效果
    transitions = timeline_data.get('transitions', [])
    
    # 获取视频轨道
    tracks = timeline_data.get('tracks', [])
    video_tracks = [t for t in tracks if t.get('type', 'video') == 'video']
    
    if not video_tracks:
        return []  # 没有视频轨道，不检查场景转场
    
    # 遍历视频轨道
    for track_index, track in enumerate(video_tracks):
        track_name = track.get('name', f'视频轨道 {track_index+1}')
        clips = track.get('clips', track.get('items', []))
        
        # 检查相邻片段的场景一致性
        for i in range(1, len(clips)):
            prev_clip = clips[i-1]
            curr_clip = clips[i]
            
            # 检查是否有场景信息
            prev_scene = prev_clip.get('scene', prev_clip.get('scene_id', None))
            curr_scene = curr_clip.get('scene', curr_clip.get('scene_id', None))
            
            # 如果两个片段的场景不同，检查是否有适当的转场
            if prev_scene is not None and curr_scene is not None and prev_scene != curr_scene:
                # 获取片段时间点
                prev_end = prev_clip.get('end', prev_clip.get('end_frame', 0))
                curr_start = curr_clip.get('start', curr_clip.get('start_frame', 0))
                
                # 检查是否有转场覆盖这个切换点
                has_transition = False
                
                for trans in transitions:
                    trans_start = trans.get('start', trans.get('start_frame', 0))
                    trans_end = trans.get('end', trans.get('end_frame', 0))
                    
                    # 如果转场覆盖了场景切换点
                    if trans_start <= prev_end and trans_end >= curr_start:
                        has_transition = True
                        break
                
                if not has_transition:
                    issues.append({
                        'type': 'scene_transition',
                        'track': track_index,
                        'location': prev_end,
                        'description': f"场景从 '{prev_scene}' 到 '{curr_scene}' 的切换缺少过渡效果"
                    })
    
    return issues


def validate_clip_duration(timeline_data: Dict[str, Any], min_duration: int = 15) -> List[Dict[str, Any]]:
    """
    验证片段持续时间是否合理
    
    检查时间轴上的片段是否过短，可能导致观看体验不佳。
    
    Args:
        timeline_data: 时间轴数据
        min_duration: 最小允许的片段持续时间（单位：帧或时间单位）
        
    Returns:
        持续时间问题列表
    """
    issues = []
    
    # 获取轨道
    tracks = timeline_data.get('tracks', [])
    
    # 检查每个轨道
    for track_index, track in enumerate(tracks):
        track_name = track.get('name', f'轨道 {track_index+1}')
        clips = track.get('clips', track.get('items', []))
        
        # 检查每个片段的持续时间
        for clip_index, clip in enumerate(clips):
            clip_id = clip.get('id', f"片段{clip_index+1}")
            start = clip.get('start', clip.get('start_frame', 0))
            end = clip.get('end', clip.get('end_frame', 0))
            
            duration = end - start
            
            # 检查是否过短
            if duration < min_duration:
                issues.append({
                    'type': 'short_duration',
                    'track': track_index,
                    'clip': clip_id,
                    'duration': duration,
                    'description': f"轨道 '{track_name}' 上的 '{clip_id}' 持续时间仅 {duration} 单位，可能过短"
                })
    
    return issues


def validate_timeline_from_file(file_path: str) -> Dict[str, Any]:
    """
    从文件加载并验证时间轴
    
    Args:
        file_path: 时间轴文件路径（JSON或XML）
        
    Returns:
        验证结果字典
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "gaps": [],
        "file": file_path
    }
    
    try:
        # 根据文件扩展名判断文件类型
        ext = os.path.splitext(file_path)[1].lower()
        
        # 加载时间轴数据
        timeline_data = None
        
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
        elif ext in ('.xml', '.fcpxml', '.prproj'):
            # 简单解析XML格式的时间轴
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 提取时间轴数据 - 这里需要根据具体XML格式做适配
            # 这是一个简化的示例，实际应用可能需要针对具体编辑软件格式做专门解析
            timeline_data = {"tracks": []}
            
            # 尝试提取轨道和片段信息
            for track_elem in root.findall(".//track") or root.findall(".//sequence/track"):
                track = {
                    "name": track_elem.get("name", "未命名轨道"),
                    "type": track_elem.get("type", "video"),
                    "clips": []
                }
                
                # 提取片段
                for clip_elem in track_elem.findall("./clip") or track_elem.findall("./item"):
                    clip = {
                        "id": clip_elem.get("id", None),
                        "start": int(clip_elem.get("start", "0")),
                        "end": int(clip_elem.get("end", "0"))
                    }
                    track["clips"].append(clip)
                
                timeline_data["tracks"].append(track)
        else:
            result["valid"] = False
            result["errors"].append(f"不支持的文件格式: {ext}")
            return result
            
        # 验证时间轴连续性
        continuity_errors = validate_timeline_continuity(timeline_data.get('tracks', []))
        result["errors"].extend(continuity_errors)
        
        # 验证多轨道关系
        multi_track_errors = validate_multi_track_timeline(timeline_data)
        result["errors"].extend(multi_track_errors)
        
        # 检查间隙
        gaps = check_timeline_gaps(timeline_data.get('tracks', []))
        result["gaps"] = gaps
        
        # 如果有间隙，添加为警告
        if gaps:
            for gap in gaps:
                result["warnings"].append(gap["description"])
        
        # 检查场景转场
        scene_issues = check_scene_transition_consistency(timeline_data)
        for issue in scene_issues:
            result["warnings"].append(issue["description"])
        
        # 检查短片段
        duration_issues = validate_clip_duration(timeline_data)
        for issue in duration_issues:
            result["warnings"].append(issue["description"])
        
        # 更新最终验证状态
        result["valid"] = len(result["errors"]) == 0
        
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"验证过程发生错误: {str(e)}")
        logger.error(f"验证时间轴文件时发生错误: {str(e)}", exc_info=True)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='验证时间轴连续性')
    parser.add_argument('timeline_file', help='时间轴文件路径（JSON或XML）')
    
    args = parser.parse_args()
    
    result = validate_timeline_from_file(args.timeline_file)
    
    if result["valid"]:
        print("时间轴验证通过!")
    else:
        print("时间轴验证失败!")
        
    if result["errors"]:
        print("\n错误:")
        for error in result["errors"]:
            if isinstance(error, dict):
                print(f"  - {error['description']}")
            else:
                print(f"  - {error}")
    
    if result["warnings"]:
        print("\n警告:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    
    if result["gaps"]:
        print("\n检测到时间间隙:")
        for gap in result["gaps"]:
            print(f"  - {gap['description']}") 