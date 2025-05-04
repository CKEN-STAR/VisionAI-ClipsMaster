#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
场景分析器模块 - 分析视频场景并与文本内容关联
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Callable
import logging
from collections import defaultdict
from dataclasses import dataclass, field

# 导入日志模块
from src.utils.log_handler import get_logger

# 导入关键帧提取器
from src.alignment.keyframe_extractor import extract_keyframes

# 配置日志
logger = get_logger("scene_analyzer")

@dataclass
class Scene:
    """场景数据类"""
    start_time: float
    end_time: float
    keyframes: List[Dict[str, Any]] = field(default_factory=list)
    text: Optional[str] = None
    scene_type: Optional[str] = None
    location: Optional[str] = None
    characters: List[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class SceneAnalyzer:
    """视频场景分析器"""
    
    def __init__(self, 
                 min_scene_duration: float = 1.0,
                 scene_threshold: float = 30.0,
                 use_external_models: bool = False):
        """
        初始化场景分析器
        
        参数:
            min_scene_duration: 最小场景持续时间（秒）
            scene_threshold: 场景变化阈值
            use_external_models: 是否使用外部模型进行高级场景分析
        """
        self.min_scene_duration = min_scene_duration
        self.scene_threshold = scene_threshold
        self.use_external_models = use_external_models
        
        # 可选: 如果启用外部模型，尝试导入
        self.scene_classifier = None
        if use_external_models:
            try:
                # 这里可以导入更高级的场景分类模型
                # 例如基于深度学习的场景分类器
                logger.info("外部场景分类模型未配置")
            except ImportError:
                logger.warning("无法导入外部场景分类模型，将使用基本分析方法")
        
        logger.info(f"场景分析器初始化完成，最小场景持续时间: {min_scene_duration}秒")
    
    def analyze_video(self, 
                     video_path: str, 
                     subtitle_data: Optional[List[Dict[str, Any]]] = None) -> List[Scene]:
        """
        分析视频，识别场景并关联字幕数据
        
        参数:
            video_path: 视频文件路径
            subtitle_data: 字幕数据，每项包含start_time, end_time, text等字段
            
        返回:
            场景列表
        """
        logger.info(f"开始分析视频: {video_path}")
        
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return []
        
        # 提取场景变化关键帧
        keyframes = extract_keyframes(
            video_path=video_path,
            method='scene',
            threshold=self.scene_threshold
        )
        
        logger.info(f"找到 {len(keyframes)} 个潜在场景变化点")
        
        # 获取视频基本信息
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps if fps > 0 else 0
        cap.release()
        
        # 识别场景边界
        scenes = self._identify_scenes(keyframes, fps, video_duration)
        logger.info(f"识别出 {len(scenes)} 个场景")
        
        # 关联字幕数据
        if subtitle_data:
            self._align_subtitles_with_scenes(scenes, subtitle_data)
            logger.info("已将字幕数据与场景关联")
        
        # 分析场景内容
        self._analyze_scene_content(scenes, video_path)
        
        return scenes
    
    def _identify_scenes(self, 
                        keyframes: List[Dict[str, Any]], 
                        fps: float, 
                        video_duration: float) -> List[Scene]:
        """从关键帧识别场景"""
        scenes = []
        
        # 视频开始时间
        current_scene_start = 0.0
        
        # 确保关键帧按时间戳排序
        sorted_keyframes = sorted(keyframes, key=lambda x: x.get('timestamp', 0))
        current_scene_keyframes = []
        
        # 处理每个关键帧
        for i, kf in enumerate(sorted_keyframes):
            timestamp = kf.get('timestamp', 0)
            
            # 添加到当前场景的关键帧
            current_scene_keyframes.append(kf)
            
            # 场景长度超过最小长度，且位于场景变化点
            scene_duration = timestamp - current_scene_start
            is_last_keyframe = i == len(sorted_keyframes) - 1
            
            if (scene_duration >= self.min_scene_duration) and (
                kf.get('motion_score', 0) > self.scene_threshold/100 or is_last_keyframe
            ):
                # 创建新场景
                scene = Scene(
                    start_time=current_scene_start,
                    end_time=timestamp,
                    keyframes=current_scene_keyframes.copy()
                )
                scenes.append(scene)
                
                # 开始新场景
                current_scene_start = timestamp
                current_scene_keyframes = []
        
        # 处理最后一个场景（如果未结束）
        if current_scene_start < video_duration:
            scene = Scene(
                start_time=current_scene_start,
                end_time=video_duration,
                keyframes=current_scene_keyframes
            )
            scenes.append(scene)
        
        return scenes
    
    def _align_subtitles_with_scenes(self, 
                                   scenes: List[Scene], 
                                   subtitle_data: List[Dict[str, Any]]) -> None:
        """将字幕数据与场景关联"""
        # 为每个场景找到对应的字幕
        for scene in scenes:
            scene_subtitles = []
            
            # 查找与当前场景时间重叠的字幕
            for subtitle in subtitle_data:
                sub_start = subtitle.get('start_time', 0)
                sub_end = subtitle.get('end_time', 0)
                
                # 字幕与场景有重叠
                if (sub_start < scene.end_time and sub_end > scene.start_time):
                    scene_subtitles.append(subtitle)
            
            # 根据字幕数据设置场景文本
            if scene_subtitles:
                combined_text = " ".join([sub.get('text', '') for sub in scene_subtitles])
                scene.text = combined_text
    
    def _analyze_scene_content(self, 
                             scenes: List[Scene], 
                             video_path: str) -> None:
        """分析场景内容，包括场景类型、位置等"""
        for scene in scenes:
            # 提取代表性帧进行分析
            representative_frame = None
            if scene.keyframes:
                # 使用场景中间的关键帧作为代表
                mid_idx = len(scene.keyframes) // 2
                representative_kf = scene.keyframes[mid_idx]
                
                # 如果关键帧中有保存的文件路径，直接读取图像
                if 'file_path' in representative_kf and os.path.exists(representative_kf['file_path']):
                    representative_frame = cv2.imread(representative_kf['file_path'])
                # 如果关键帧中直接包含图像数据
                elif 'frame' in representative_kf:
                    representative_frame = representative_kf['frame']
                # 否则，从视频中提取
                else:
                    timestamp = representative_kf.get('timestamp', (scene.start_time + scene.end_time) / 2)
                    representative_frame = self._extract_frame_at_time(video_path, timestamp)
            
            # 如果没有有效的关键帧，提取场景中间的帧
            if representative_frame is None:
                mid_time = (scene.start_time + scene.end_time) / 2
                representative_frame = self._extract_frame_at_time(video_path, mid_time)
            
            # 分析场景内容
            if representative_frame is not None:
                # 基本分析: 明暗、颜色分布等
                scene.metadata['brightness'] = np.mean(representative_frame)
                
                # 日夜场景分类
                brightness = np.mean(representative_frame)
                if brightness < 80:
                    scene.scene_type = "night"
                elif brightness < 160:
                    scene.scene_type = "indoor"
                else:
                    scene.scene_type = "day"
                
                # 室内/室外基本分类
                hsv = cv2.cvtColor(representative_frame, cv2.COLOR_BGR2HSV)
                sat_mean = np.mean(hsv[:,:,1])
                if scene.scene_type != "night" and sat_mean > 100:
                    scene.location = "outdoor"
                else:
                    scene.location = "indoor"
                
                # 保存分析数据
                scene.metadata['color_histogram'] = self._calculate_color_histogram(representative_frame)
                scene.confidence = 0.7  # 基本分析的置信度适中
            
            # 使用外部模型进行高级分析
            if self.use_external_models and self.scene_classifier and representative_frame is not None:
                # 这里可以使用更高级的分析方法
                # 例如场景识别模型、OCR识别文字等
                scene.confidence = 0.9  # 高级分析的置信度更高
                pass
    
    def _extract_frame_at_time(self, video_path: str, timestamp: float) -> Optional[np.ndarray]:
        """从视频的指定时间点提取帧"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                logger.warning("无法获取视频FPS")
                cap.release()
                return None
            
            # 计算帧位置
            frame_position = int(timestamp * fps)
            
            # 设置读取位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            
            # 读取帧
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return frame
            else:
                logger.warning(f"无法从时间点 {timestamp}s 读取帧")
                return None
                
        except Exception as e:
            logger.error(f"提取视频帧时出错: {str(e)}")
            if 'cap' in locals():
                cap.release()
            return None
    
    def _calculate_color_histogram(self, frame: np.ndarray) -> List[float]:
        """计算图像的颜色直方图"""
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算色调通道的直方图
        hist = cv2.calcHist([hsv], [0], None, [18], [0, 180])
        
        # 归一化直方图
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        
        return hist.flatten().tolist()
    
    def classify_scenes(self, 
                       scenes: List[Scene], 
                       classifier_fn: Optional[Callable] = None) -> List[Scene]:
        """使用外部分类器对场景进行分类
        
        参数:
            scenes: 要分类的场景列表
            classifier_fn: 自定义分类器函数，接收场景作为输入，返回分类标签
        
        返回:
            更新后的场景列表
        """
        if classifier_fn is None:
            logger.warning("未提供分类器函数，将使用默认分类")
            return scenes
        
        for scene in scenes:
            try:
                scene_type = classifier_fn(scene)
                if scene_type:
                    scene.scene_type = scene_type
            except Exception as e:
                logger.error(f"场景分类失败: {str(e)}")
        
        return scenes
    
    def analyze_scene_transitions(self, scenes: List[Scene]) -> Dict[str, Any]:
        """分析场景之间的过渡关系
        
        返回:
            场景过渡分析结果
        """
        transitions = []
        scene_types = defaultdict(int)
        avg_scene_duration = 0
        
        if not scenes:
            return {
                "transitions": [],
                "scene_types": {},
                "avg_scene_duration": 0,
                "total_scenes": 0
            }
        
        # 计算场景统计信息
        for i, scene in enumerate(scenes):
            # 统计场景类型
            if scene.scene_type:
                scene_types[scene.scene_type] += 1
            
            # 计算场景持续时间
            duration = scene.end_time - scene.start_time
            avg_scene_duration += duration
            
            # 分析相邻场景关系
            if i < len(scenes) - 1:
                next_scene = scenes[i + 1]
                
                # 创建过渡信息
                transition = {
                    "from_scene_idx": i,
                    "to_scene_idx": i + 1,
                    "from_type": scene.scene_type,
                    "to_type": next_scene.scene_type,
                    "transition_time": next_scene.start_time - scene.end_time,
                    "is_cut": (next_scene.start_time - scene.end_time) < 0.1
                }
                transitions.append(transition)
        
        # 计算平均场景持续时间
        if scenes:
            avg_scene_duration /= len(scenes)
        
        return {
            "transitions": transitions,
            "scene_types": dict(scene_types),
            "avg_scene_duration": avg_scene_duration,
            "total_scenes": len(scenes)
        }

# 提供便捷函数
def analyze_video_scenes(video_path: str, subtitle_data: Optional[List[Dict[str, Any]]] = None) -> List[Scene]:
    """
    分析视频场景的便捷函数
    
    参数:
        video_path: 视频文件路径
        subtitle_data: 字幕数据
        
    返回:
        识别的场景列表
    """
    analyzer = SceneAnalyzer()
    return analyzer.analyze_video(video_path, subtitle_data)


# 测试代码
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <视频文件路径> [字幕文件路径]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    subtitle_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 如果有字幕文件，解析字幕
    subtitle_data = None
    if subtitle_path:
        from src.core.srt_parser import parse_subtitle
        try:
            subtitle_data = parse_subtitle(subtitle_path)
            print(f"已加载 {len(subtitle_data)} 条字幕")
        except Exception as e:
            print(f"字幕解析错误: {str(e)}")
    
    # 分析视频场景
    try:
        analyzer = SceneAnalyzer()
        scenes = analyzer.analyze_video(video_path, subtitle_data)
        
        print(f"识别到 {len(scenes)} 个场景:")
        for i, scene in enumerate(scenes):
            print(f"\n场景 {i+1}: {scene.start_time:.2f}s - {scene.end_time:.2f}s (持续: {scene.end_time - scene.start_time:.2f}s)")
            print(f"  类型: {scene.scene_type or '未知'}, 位置: {scene.location or '未知'}")
            if scene.text:
                print(f"  文本: {scene.text[:100]}{'...' if len(scene.text) > 100 else ''}")
            print(f"  关键帧数: {len(scene.keyframes)}")
        
        # 分析场景过渡
        transitions = analyzer.analyze_scene_transitions(scenes)
        print(f"\n场景统计:")
        print(f"  总场景数: {transitions['total_scenes']}")
        print(f"  平均场景持续时间: {transitions['avg_scene_duration']:.2f}秒")
        print(f"  场景类型分布: {transitions['scene_types']}")
        
    except Exception as e:
        print(f"场景分析错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 