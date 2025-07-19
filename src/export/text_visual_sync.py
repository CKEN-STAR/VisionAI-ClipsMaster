#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 字幕-镜头映射器

此模块提供将SRT字幕与视频镜头进行精确映射的功能。
它能够找到最佳匹配的视频片段，确保字幕与视觉内容同步，
从而在混剪过程中保持视听一致性。

主要功能：
1. 单条字幕到视频镜头的精确映射
2. 多条字幕的批量映射处理
3. 处理特殊情况（如找不到完美匹配）的回退策略
4. 视听一致性评分计算
5. 时间码校准与补偿
"""

import os
import re
import json
import logging
import bisect
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# 相对导入变更为适应模块化运行
try:
    from src.utils.log_handler import get_logger
    from src.utils.exceptions import ClipMasterError, MappingError
    from src.export.timeline_checker import detect_overlap
except ImportError:
    # 当作为独立模块运行时的后备导入路径
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    try:
        from src.utils.log_handler import get_logger
        from src.utils.exceptions import ClipMasterError, MappingError
        from src.export.timeline_checker import detect_overlap
    except ImportError:
        # 如果还是无法导入，使用基本日志
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        def get_logger(name):
            return logging.getLogger(name)
        
        # 定义基本异常类
        class ClipMasterError(Exception):
            pass
        
        class MappingError(ClipMasterError):
            pass
        
        # 简单的重叠检测函数
        def detect_overlap(a_start, a_end, b_start, b_end):
            return max(0, min(a_end, b_end) - max(a_start, b_start))

# 配置日志
logger = get_logger("text_visual_sync")


def map_subtitle_to_shot(srt_text: Dict[str, Any], video_shots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将单条字幕映射到最佳匹配的视频镜头
    
    寻找时间码重叠的视频镜头，如果找不到则回退到最近的镜头
    
    Args:
        srt_text: 包含start和end键的字幕字典
        video_shots: 视频镜头列表
        
    Returns:
        最佳匹配的视频镜头
    """
    best_shot = None
    best_overlap = 0
    
    # 检查参数有效性
    if not srt_text or 'start' not in srt_text or 'end' not in srt_text:
        logger.warning("无效的字幕数据")
        return video_shots[-1] if video_shots else None
    
    if not video_shots:
        logger.warning("视频镜头列表为空")
        return None
    
    # 遍历所有镜头寻找最佳匹配
    for shot in video_shots:
        if 'start' not in shot or 'end' not in shot:
            continue
        
        # 计算重叠程度
        overlap_start = max(shot['start'], srt_text['start'])
        overlap_end = min(shot['end'], srt_text['end'])
        overlap = max(0, overlap_end - overlap_start)
        
        # 更新最佳匹配
        if overlap > best_overlap:
            best_overlap = overlap
            best_shot = shot
            
            # 如果找到完全包含的镜头，直接返回（最优解）
            if shot['start'] <= srt_text['start'] and shot['end'] >= srt_text['end']:
                return shot
    
    # 如果找到部分重叠的镜头，返回它
    if best_shot:
        return best_shot
    
    # 如果没有重叠，找最接近的镜头
    sorted_shots = sorted(video_shots, key=lambda x: x.get('start', 0))
    shot_starts = [shot.get('start', 0) for shot in sorted_shots]
    
    # 查找最接近的镜头索引
    idx = bisect.bisect_left(shot_starts, srt_text['start'])
    
    # 如果索引有效，返回最接近的镜头
    if 0 <= idx < len(sorted_shots):
        return sorted_shots[idx]
    # 如果字幕在所有镜头之前，返回第一个镜头
    elif idx == 0 and sorted_shots:
        return sorted_shots[0]
    # 如果字幕在所有镜头之后，返回最后一个镜头
    elif sorted_shots:
        return sorted_shots[-1]
    
    # 最终回退策略
    return None


def batch_map_subtitles(subtitles: List[Dict[str, Any]], video_shots: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """批量处理多条字幕的镜头映射
    
    Args:
        subtitles: 字幕列表
        video_shots: 视频镜头列表
        
    Returns:
        字幕和对应镜头的映射列表
    """
    mappings = []
    
    for subtitle in subtitles:
        best_shot = map_subtitle_to_shot(subtitle, video_shots)
        if best_shot:
            mappings.append((subtitle, best_shot))
        else:
            logger.warning(f"无法为字幕找到匹配镜头: {subtitle.get('content', '')[:30]}...")
    
    return mappings


def calculate_sync_score(subtitle: Dict[str, Any], shot: Dict[str, Any]) -> float:
    """计算字幕与镜头的同步评分
    
    分数范围: 0.0-1.0，越高表示匹配度越好
    
    Args:
        subtitle: 字幕字典
        shot: 视频镜头字典
        
    Returns:
        同步评分
    """
    if not subtitle or not shot:
        return 0.0
        
    if 'start' not in subtitle or 'end' not in subtitle or 'start' not in shot or 'end' not in shot:
        return 0.0
    
    # 计算重叠部分
    overlap_start = max(shot['start'], subtitle['start'])
    overlap_end = min(shot['end'], subtitle['end'])
    overlap = max(0, overlap_end - overlap_start)
    
    # 计算字幕和镜头的持续时间
    subtitle_duration = subtitle['end'] - subtitle['start']
    shot_duration = shot['end'] - shot['start']
    
    # 计算重叠比例（相对于字幕持续时间）
    if subtitle_duration > 0:
        subtitle_overlap_ratio = overlap / subtitle_duration
    else:
        subtitle_overlap_ratio = 0
        
    # 计算总评分
    score = subtitle_overlap_ratio
    
    return min(1.0, score)  # 确保评分不超过1.0


def generate_mapping_report(mappings: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> Dict[str, Any]:
    """生成映射质量报告
    
    Args:
        mappings: 字幕和镜头的映射列表
        
    Returns:
        映射质量统计报告
    """
    report = {
        "total_mappings": len(mappings),
        "perfect_match_count": 0,
        "partial_match_count": 0,
        "low_quality_match_count": 0,
        "average_score": 0.0,
        "score_distribution": {
            "excellent": 0,  # 0.9-1.0
            "good": 0,       # 0.7-0.9
            "fair": 0,       # 0.4-0.7
            "poor": 0        # 0.0-0.4
        }
    }
    
    total_score = 0.0
    
    for subtitle, shot in mappings:
        score = calculate_sync_score(subtitle, shot)
        total_score += score
        
        # 分类评分
        if score >= 0.9:
            report["perfect_match_count"] += 1
            report["score_distribution"]["excellent"] += 1
        elif score >= 0.7:
            report["partial_match_count"] += 1
            report["score_distribution"]["good"] += 1
        elif score >= 0.4:
            report["partial_match_count"] += 1
            report["score_distribution"]["fair"] += 1
        else:
            report["low_quality_match_count"] += 1
            report["score_distribution"]["poor"] += 1
    
    # 计算平均评分
    if mappings:
        report["average_score"] = total_score / len(mappings)
    
    return report


def adjust_mapping_times(mappings: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """调整映射时间以创建连贯的时间线
    
    修剪或扩展镜头以匹配字幕时间，并处理可能的间隙
    
    Args:
        mappings: 字幕和镜头的映射列表
        
    Returns:
        调整后的片段列表
    """
    adjusted_clips = []
    
    for subtitle, shot in mappings:
        # 创建基于镜头但时间与字幕匹配的新片段
        clip = shot.copy()
        
        # 使用字幕的时间范围
        clip['start'] = subtitle['start']
        clip['end'] = subtitle['end']
        clip['duration'] = subtitle['end'] - subtitle['start']
        
        # 添加字幕内容
        clip['subtitle'] = subtitle.get('content', '')
        
        adjusted_clips.append(clip)
    
    return adjusted_clips


class TextVisualSyncer:
    """字幕-镜头同步处理器类"""
    
    def __init__(self):
        """初始化同步处理器"""
        self.logger = logger
    
    def process(self, subtitles: List[Dict[str, Any]], video_shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理字幕和视频镜头同步
        
        Args:
            subtitles: 字幕列表
            video_shots: 视频镜头列表
            
        Returns:
            包含映射和质量报告的结果
        """
        try:
            # 批量处理映射
            mappings = batch_map_subtitles(subtitles, video_shots)
            
            # 调整映射时间
            adjusted_clips = adjust_mapping_times(mappings)
            
            # 生成质量报告
            report = generate_mapping_report(mappings)
            
            return {
                "mappings": mappings,
                "adjusted_clips": adjusted_clips,
                "report": report
            }
        
        except Exception as e:
            self.logger.error(f"处理字幕-镜头同步时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise MappingError(f"字幕-镜头同步失败: {str(e)}")


# 创建全局实例
_syncer = None

def get_text_visual_syncer() -> TextVisualSyncer:
    """获取字幕-镜头同步处理器实例
    
    Returns:
        TextVisualSyncer: 同步处理器实例
    """
    global _syncer
    if _syncer is None:
        _syncer = TextVisualSyncer()
    return _syncer


def sync_text_with_visuals(subtitles: List[Dict[str, Any]], video_shots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """将字幕与视频画面同步（便捷函数）
    
    Args:
        subtitles: 字幕列表
        video_shots: 视频镜头列表
        
    Returns:
        同步处理结果
    """
    syncer = get_text_visual_syncer()
    return syncer.process(subtitles, video_shots)


if __name__ == "__main__":
    # 简单测试
    test_subtitles = [
        {"id": "sub1", "start": 1.0, "end": 3.0, "content": "这是第一条字幕"},
        {"id": "sub2", "start": 3.5, "end": 5.0, "content": "这是第二条字幕"},
        {"id": "sub3", "start": 6.0, "end": 9.0, "content": "这是第三条字幕"}
    ]
    
    test_shots = [
        {"id": "shot1", "start": 0.0, "end": 2.5, "source": "video1.mp4"},
        {"id": "shot2", "start": 2.5, "end": 4.0, "source": "video1.mp4"},
        {"id": "shot3", "start": 4.0, "end": 7.0, "source": "video1.mp4"},
        {"id": "shot4", "start": 7.0, "end": 10.0, "source": "video1.mp4"}
    ]
    
    # 执行同步
    result = sync_text_with_visuals(test_subtitles, test_shots)
    
    # 打印结果
    print("同步结果:")
    for i, clip in enumerate(result["adjusted_clips"]):
        print(f"字幕 {i+1}: {clip['subtitle']}")
        print(f"时间范围: {clip['start']} - {clip['end']}")
        print(f"来源镜头: {clip.get('id', 'unknown')}")
        print()
    
    print("质量报告:")
    print(json.dumps(result["report"], indent=2)) 