#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多模态同步模块 - 实现视频、音频与文本的对齐
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import copy
from dataclasses import dataclass, field
from datetime import timedelta

# 导入日志模块
from src.utils.log_handler import get_logger

# 导入关键帧提取和场景分析模块
from src.alignment.keyframe_extractor import extract_keyframes
from src.alignment.scene_analyzer import Scene, SceneAnalyzer, analyze_video_scenes

# 导入字幕解析模块
from src.core.srt_parser import parse_subtitle

# 配置日志
logger = get_logger("multimodal_sync")


@dataclass
class ContentAlignment:
    """内容对齐结果数据类"""
    text: str
    start_time: float
    end_time: float
    keyframe: Optional[Dict[str, Any]] = None
    scene: Optional[Scene] = None
    confidence: float = 0.0
    visual_context: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AudioVisualAligner:
    """音视频文本对齐器"""
    
    def __init__(self, 
                time_tolerance: float = 0.5,
                use_ocr: bool = False,
                use_speech_recognition: bool = False,
                visual_context_extraction: bool = True):
        """
        初始化音视频对齐器
        
        参数:
            time_tolerance: 时间容差（秒）
            use_ocr: 是否使用OCR识别视频中的文字
            use_speech_recognition: 是否使用语音识别
            visual_context_extraction: 是否提取视觉上下文
        """
        self.time_tolerance = time_tolerance
        self.use_ocr = use_ocr
        self.use_speech_recognition = use_speech_recognition
        self.visual_context_extraction = visual_context_extraction
        
        # OCR识别器（可选）
        self.ocr_engine = None
        if use_ocr:
            try:
                # 可以导入OCR引擎，例如pytesseract或PaddleOCR
                # 这里先不实现
                logger.info("OCR引擎未配置")
            except ImportError:
                logger.warning("无法导入OCR引擎，将禁用OCR识别")
                self.use_ocr = False
        
        # 语音识别引擎（可选）
        self.speech_recognition_engine = None
        if use_speech_recognition:
            try:
                # 可以导入语音识别引擎，例如whisper或vosk
                # 这里先不实现
                logger.info("语音识别引擎未配置")
            except ImportError:
                logger.warning("无法导入语音识别引擎，将禁用语音识别")
                self.use_speech_recognition = False
        
        logger.info(f"多模态对齐器初始化完成，时间容差: {time_tolerance}秒")
    
    def align_with_video(self, 
                       srt_data: List[Dict[str, Any]], 
                       video_path: str) -> List[ContentAlignment]:
        """
        将字幕与视频内容对齐
        
        参数:
            srt_data: 字幕数据，每项包含id, start_time, end_time, text等字段
            video_path: 视频文件路径
            
        返回:
            对齐的内容列表
        """
        logger.info(f"开始对齐字幕与视频: {video_path}")
        
        # 检查文件是否存在
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return []
        
        # 提取视频关键帧
        keyframes = extract_keyframes(
            video_path=video_path,
            method='uniform',
            num_frames=min(len(srt_data) * 2, 100)  # 提取足够的关键帧
        )
        
        logger.info(f"已提取 {len(keyframes)} 个关键帧")
        
        # 分析视频场景
        scenes = analyze_video_scenes(video_path, srt_data)
        logger.info(f"已识别 {len(scenes)} 个场景")
        
        # 对齐结果列表
        alignments = []
        
        # 遍历每个字幕，查找对应的关键帧和场景
        for subtitle in srt_data:
            sub_start = subtitle.get('start_time', 0)
            sub_end = subtitle.get('end_time', 0)
            sub_text = subtitle.get('text', '')
            
            # 初始化对齐结果
            alignment = ContentAlignment(
                text=sub_text,
                start_time=sub_start,
                end_time=sub_end
            )
            
            # 查找最近的关键帧
            nearest_frame = self._find_nearest_frame(keyframes, sub_start)
            if nearest_frame:
                alignment.keyframe = nearest_frame
                
                # 检查时间偏差
                time_diff = abs(nearest_frame.get('timestamp', 0) - sub_start)
                if time_diff > self.time_tolerance:
                    alignment.warnings.append(f"字幕与画面可能不同步，时间差: {time_diff:.2f}秒")
                
                # 提取视觉上下文（如果启用）
                if self.visual_context_extraction and nearest_frame:
                    alignment.visual_context = self._analyze_frame_content(nearest_frame)
            
            # 关联场景
            matching_scene = self._find_matching_scene(scenes, sub_start, sub_end)
            if matching_scene:
                alignment.scene = matching_scene
            
            # 设置置信度
            if alignment.keyframe and alignment.scene:
                alignment.confidence = 0.9
            elif alignment.keyframe or alignment.scene:
                alignment.confidence = 0.7
            else:
                alignment.confidence = 0.3
                alignment.warnings.append("未找到匹配的视频内容")
            
            alignments.append(alignment)
        
        return alignments
    
    def _find_nearest_frame(self, 
                          keyframes: List[Dict[str, Any]], 
                          target_time: float) -> Optional[Dict[str, Any]]:
        """查找最接近目标时间的关键帧"""
        if not keyframes:
            return None
        
        nearest_frame = None
        min_diff = float('inf')
        
        for kf in keyframes:
            timestamp = kf.get('timestamp', 0)
            diff = abs(timestamp - target_time)
            
            if diff < min_diff:
                min_diff = diff
                nearest_frame = kf
        
        return copy.deepcopy(nearest_frame)
    
    def _find_matching_scene(self, 
                           scenes: List[Scene], 
                           start_time: float, 
                           end_time: float) -> Optional[Scene]:
        """查找与给定时间段匹配的场景"""
        for scene in scenes:
            # 检查时间重叠
            if start_time < scene.end_time and end_time > scene.start_time:
                return copy.deepcopy(scene)
        
        return None
    
    def _analyze_frame_content(self, 
                             keyframe: Dict[str, Any]) -> Optional[str]:
        """分析帧内容，提取视觉上下文"""
        visual_context = None
        
        # 如果帧图像可用
        if 'frame' in keyframe:
            frame = keyframe['frame']
            
            # 基本亮度分析
            brightness = np.mean(frame)
            if brightness < 80:
                visual_context = "暗场景"
            elif brightness > 200:
                visual_context = "亮场景"
            else:
                visual_context = "正常亮度场景"
            
            # 如果启用OCR，识别画面中的文字
            if self.use_ocr and self.ocr_engine:
                # 未实现OCR功能
                pass
        
        # 如果帧图像不可用但有文件路径
        elif 'file_path' in keyframe and os.path.exists(keyframe['file_path']):
            frame = cv2.imread(keyframe['file_path'])
            if frame is not None:
                brightness = np.mean(frame)
                if brightness < 80:
                    visual_context = "暗场景"
                elif brightness > 200:
                    visual_context = "亮场景"
                else:
                    visual_context = "正常亮度场景"
        
        return visual_context
    
    def get_alignment_report(self, 
                           alignments: List[ContentAlignment]) -> Dict[str, Any]:
        """生成对齐质量报告
        
        参数:
            alignments: 对齐结果列表
            
        返回:
            包含对齐质量统计信息的字典
        """
        if not alignments:
            return {
                "total_alignments": 0,
                "average_confidence": 0,
                "warnings_count": 0,
                "warnings_percentage": 0,
                "scene_coverage": 0
            }
        
        # 统计信息
        total = len(alignments)
        confidence_sum = sum(a.confidence for a in alignments)
        warnings_count = sum(1 for a in alignments if a.warnings)
        scene_coverage = sum(1 for a in alignments if a.scene) / total if total > 0 else 0
        
        return {
            "total_alignments": total,
            "average_confidence": confidence_sum / total if total > 0 else 0,
            "warnings_count": warnings_count,
            "warnings_percentage": (warnings_count / total) * 100 if total > 0 else 0,
            "scene_coverage": scene_coverage * 100
        }
    
    def enhance_subtitle_data(self, 
                            srt_data: List[Dict[str, Any]], 
                            alignments: List[ContentAlignment]) -> List[Dict[str, Any]]:
        """用对齐信息增强字幕数据
        
        参数:
            srt_data: 原始字幕数据
            alignments: 对齐结果
            
        返回:
            增强后的字幕数据
        """
        if len(srt_data) != len(alignments):
            logger.warning(f"字幕数据与对齐结果数量不匹配: {len(srt_data)} vs {len(alignments)}")
            return srt_data
        
        enhanced_data = copy.deepcopy(srt_data)
        
        for i, (subtitle, alignment) in enumerate(zip(enhanced_data, alignments)):
            # 添加视觉上下文
            if alignment.visual_context:
                subtitle['visual_context'] = alignment.visual_context
            
            # 添加场景信息
            if alignment.scene:
                subtitle['scene_type'] = alignment.scene.scene_type
                subtitle['location'] = alignment.scene.location
            
            # 添加警告信息
            if alignment.warnings:
                if 'warnings' not in subtitle:
                    subtitle['warnings'] = []
                subtitle['warnings'].extend(alignment.warnings)
            
            # 添加置信度
            subtitle['alignment_confidence'] = alignment.confidence
        
        return enhanced_data


# 提供便捷函数
def align_subtitles_with_video(srt_path: str, 
                              video_path: str) -> List[Dict[str, Any]]:
    """
    将字幕与视频对齐的便捷函数
    
    参数:
        srt_path: 字幕文件路径
        video_path: 视频文件路径
        
    返回:
        增强后的字幕数据
    """
    try:
        # 解析字幕
        srt_data = parse_subtitle(srt_path)
        
        # 创建对齐器
        aligner = AudioVisualAligner()
        
        # 执行对齐
        alignments = aligner.align_with_video(srt_data, video_path)
        
        # 增强字幕数据
        enhanced_data = aligner.enhance_subtitle_data(srt_data, alignments)
        
        return enhanced_data
    except Exception as e:
        logger.error(f"字幕对齐失败: {str(e)}")
        return []


# 测试代码
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <字幕文件路径> <视频文件路径>")
        sys.exit(1)
    
    srt_path = sys.argv[1]
    video_path = sys.argv[2]
    
    try:
        # 解析字幕
        srt_data = parse_subtitle(srt_path)
        print(f"已加载 {len(srt_data)} 条字幕")
        
        # 创建对齐器
        aligner = AudioVisualAligner(
            time_tolerance=1.0,
            visual_context_extraction=True
        )
        
        # 执行对齐
        print("正在进行对齐...")
        alignments = aligner.align_with_video(srt_data, video_path)
        
        # 生成报告
        report = aligner.get_alignment_report(alignments)
        
        print(f"\n对齐报告:")
        print(f"  总对齐数: {report['total_alignments']}")
        print(f"  平均置信度: {report['average_confidence']:.2f}")
        print(f"  警告数量: {report['warnings_count']} ({report['warnings_percentage']:.1f}%)")
        print(f"  场景覆盖率: {report['scene_coverage']:.1f}%")
        
        # 打印有警告的对齐
        print("\n存在警告的对齐:")
        for i, alignment in enumerate(alignments):
            if alignment.warnings:
                print(f"\n  对齐项 {i+1}: 时间 {alignment.start_time:.2f}s - {alignment.end_time:.2f}s")
                print(f"    文本: {alignment.text}")
                print(f"    警告: {', '.join(alignment.warnings)}")
        
        # 增强字幕数据
        enhanced_data = aligner.enhance_subtitle_data(srt_data, alignments)
        
        # 保存结果（可选）
        output_path = os.path.splitext(srt_path)[0] + "_enhanced.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n增强后的字幕数据已保存到: {output_path}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 