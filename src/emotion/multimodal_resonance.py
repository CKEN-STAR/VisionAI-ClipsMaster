#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多模态情感共振模块

此模块根据内容情感类型，自动增强视频和音频效果，实现跨模态的情感协同增强。
主要功能包括：
1. 根据情感类型选择合适的视觉和听觉效果
2. 应用视觉滤镜和转场效果
3. 添加情感匹配的配乐和音效
4. 情感和节奏的动态同步
5. 多模态综合协调
"""

import os
import yaml
import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path

# 导入本地模块
from src.emotion.intensity_mapper import EmotionMapper
from src.emotion.focus_locator import EmotionFocusLocator
from src.utils.config_utils import load_config

logger = logging.getLogger(__name__)

class EmotionalResonance:
    """多模态情感共振类，用于根据情感类型增强视频和音频效果"""
    
    def __init__(self, config_path: str = "configs/emotion_resonance.yaml"):
        """
        初始化多模态情感共振器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置文件
        self.config = load_config(config_path)
        
        # 初始化依赖模块
        self.emotion_mapper = EmotionMapper()
        self.focus_locator = EmotionFocusLocator()
        
        # 加载情感效果配置
        self.EMOTION_EFFECTS = self.config.get("emotion_effects", {})
        
        # 加载音频资源配置
        self.audio_resources = self.config.get("audio_resources", {})
        
        # 加载节奏同步配置
        self.rhythm_sync_config = self.config.get("rhythm_sync", {})
        
        # 加载情感转场配置
        self.transition_config = self.config.get("emotion_transitions", {})
        
        # 加载BGM文件路径基础目录
        self.audio_base_path = self.config.get("content_enhancement", {}).get(
            "audio_resources_path", "resources/audio"
        )
        
        logger.info("多模态情感共振器初始化完成")
    
    def detect_scene_emotion(self, scene: Dict[str, Any]) -> Tuple[str, float]:
        """
        检测场景的主要情感类型和强度
        
        Args:
            scene: 场景数据字典
        
        Returns:
            情感类型和强度元组
        """
        # 如果场景已包含情感标签，直接使用
        if "emotion" in scene and "type" in scene["emotion"] and "intensity" in scene["emotion"]:
            return scene["emotion"]["type"], scene["emotion"]["intensity"]
        
        # 否则从场景文本中提取情感
        text_content = scene.get("text", "")
        if not text_content:
            logger.warning("场景缺少文本内容，无法准确判断情感")
            return "中性", 0.5
        
        # 简单情感关键词匹配
        emotion_keywords = {
            "喜悦": ["喜悦", "欢喜", "高兴", "兴奋", "开心", "欢乐", "快乐", "欣喜", "愉快", "欢呼", "庆祝", "笑"],
            "悲伤": ["悲伤", "伤心", "难过", "痛苦", "哀伤", "哭泣", "忧郁", "沮丧", "失落", "泪水", "痛心", "哭"],
            "愤怒": ["愤怒", "生气", "恼火", "发怒", "暴怒", "气愤", "恼怒", "怒火", "怒气", "火冒三丈", "大怒"],
            "恐惧": ["恐惧", "害怕", "惊恐", "惧怕", "畏惧", "胆怯", "惊吓", "恐慌", "战栗", "害怕"],
            "惊讶": ["惊讶", "吃惊", "震惊", "惊讶", "惊愕", "惊诧", "意外", "惊奇", "诧异", "困惑"],
            "紧张": ["紧张", "焦虑", "忐忑", "不安", "担忧", "慌张", "急迫", "焦急", "心跳", "出汗"]
        }
        
        # 统计各种情感关键词出现次数
        emotion_counts = {}
        for emotion, keywords in emotion_keywords.items():
            count = 0
            for keyword in keywords:
                count += text_content.count(keyword)
            emotion_counts[emotion] = count
        
        # 获取情感焦点并计算强度
        emotion_ranges = self.focus_locator.find_emotion_focus_ranges(text_content)
        
        # 如果没有找到情感关键词和情感焦点，返回中性
        if sum(emotion_counts.values()) == 0 and not emotion_ranges:
            return "中性", 0.5
        
        # 通过情感关键词确定主要情感
        if sum(emotion_counts.values()) > 0:
            # 获取出现最多的情感类型
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
            emotion_type = dominant_emotion[0]
            
            # 计算情感强度
            if emotion_ranges:
                # 如果有情感焦点，计算平均强度
                avg_intensity = sum(r["emotion_score"] for r in emotion_ranges) / len(emotion_ranges)
                # 根据情感关键词数量增加强度
                keyword_intensity = min(0.9, 0.5 + (dominant_emotion[1] * 0.1))
                # 取两者的加权平均
                intensity = (avg_intensity * 0.7) + (keyword_intensity * 0.3)
            else:
                # 如果没有情感焦点，根据关键词数量估算强度
                intensity = min(0.8, 0.5 + (dominant_emotion[1] * 0.05))
        else:
            # 如果只有情感焦点但没有关键词，使用情感焦点的主要情感
            emotion_type = "未知情感"
            
            # 可以根据不同情感分数特征进行简单分类
            highest_score = max(r["emotion_score"] for r in emotion_ranges)
            intensity = highest_score
        
        return emotion_type, min(1.0, intensity)
    
    def add_audiovisual_cues(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        为场景添加情感匹配的视觉和听觉效果
        
        Args:
            scene: 场景数据字典
        
        Returns:
            增强后的场景数据字典
        """
        # 检测场景情感
        emotion_type, emotion_intensity = self.detect_scene_emotion(scene)
        
        # 如果不在预定义情感类型中，使用最接近的情感类型
        if emotion_type not in self.EMOTION_EFFECTS:
            logger.info(f"情感类型 '{emotion_type}' 不在预定义效果中，使用中性效果")
            emotion_type = "中性"
            # 对于中性情感使用轻微增强
            scene["video_effects"] = scene.get("video_effects", []) + [{
                "type": "color_grading",
                "params": {"temperature": 0, "saturation": 0}
            }]
            return scene
        
        # 获取情感对应的效果
        effects = self.EMOTION_EFFECTS.get(emotion_type, {})
        
        # 应用视频效果
        if "video" in effects and scene.get("video_path"):
            video_effects = effects["video"]
            
            # 根据情感强度调整效果参数
            intensity_factor = emotion_intensity / 0.5  # 标准化强度因子
            
            # 添加色彩调整
            if "color_grading" in video_effects:
                color_params = {
                    k: v * intensity_factor 
                    for k, v in video_effects["color_grading"].items()
                }
                
                scene["video_effects"] = scene.get("video_effects", []) + [{
                    "type": "color_grading",
                    "params": color_params
                }]
            
            # 添加转场效果
            if "transition" in video_effects:
                scene["transitions"] = scene.get("transitions", []) + [{
                    "type": video_effects["transition"],
                    "duration": 0.5 + (0.5 * emotion_intensity)  # 根据情感强度调整转场时长
                }]
            
            # 添加速度调整
            if "speed" in video_effects:
                # 根据情感强度调整速度变化
                speed_adj = ((video_effects["speed"] - 1.0) * intensity_factor) + 1.0
                scene["video_effects"] = scene.get("video_effects", []) + [{
                    "type": "speed_adjustment",
                    "params": {"speed_factor": speed_adj}
                }]
            
            # 添加特殊效果（如模糊、锐化等）
            if "special" in video_effects:
                for effect_name, effect_intensity in video_effects["special"].items():
                    # 根据情感强度调整特效强度
                    adjusted_intensity = effect_intensity * intensity_factor
                    
                    scene["video_effects"] = scene.get("video_effects", []) + [{
                        "type": effect_name,
                        "params": {"intensity": adjusted_intensity}
                    }]
        
        # 应用音频效果
        if "audio" in effects:
            audio_effects = effects["audio"]
            
            # 添加背景音乐
            if "bgm_type" in audio_effects and self.audio_resources.get(audio_effects["bgm_type"]):
                # 从该情感类型的BGM中随机选择一个
                bgm_options = self.audio_resources[audio_effects["bgm_type"]]
                selected_bgm = np.random.choice(bgm_options)
                
                scene["audio_effects"] = scene.get("audio_effects", []) + [{
                    "type": "bgm",
                    "file": selected_bgm,
                    "volume": 0.7 + (audio_effects.get("volume_adjust", 0) / 20)  # 音量调整
                }]
            
            # 添加混响效果
            if audio_effects.get("reverb", False):
                scene["audio_effects"] = scene.get("audio_effects", []) + [{
                    "type": "reverb",
                    "params": {
                        "room_size": 0.6 + (0.3 * emotion_intensity),
                        "damping": 0.5,
                        "wet_level": 0.3 + (0.4 * emotion_intensity),
                        "dry_level": 0.7
                    }
                }]
            
            # 添加均衡器效果
            if "eq" in audio_effects:
                scene["audio_effects"] = scene.get("audio_effects", []) + [{
                    "type": "equalizer",
                    "params": {
                        # 根据情感强度调整EQ参数
                        "low": audio_effects["eq"]["low"] * intensity_factor,
                        "mid": audio_effects["eq"]["mid"] * intensity_factor,
                        "high": audio_effects["eq"]["high"] * intensity_factor
                    }
                }]
        
        # 记录应用的情感增强效果
        scene["applied_emotion_resonance"] = {
            "type": emotion_type,
            "intensity": emotion_intensity,
            "video_effects_applied": bool("video" in effects and scene.get("video_path")),
            "audio_effects_applied": bool("audio" in effects)
        }
        
        # 记录日志（如果启用）
        if self.config.get("debug", {}).get("log_applied_effects", True):
            logger.info(f"为场景添加了'{emotion_type}'情感的视听效果增强")
        
        return scene
    
    def synchronize_emotion_with_rhythm(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        将情感效果与视频节奏同步
        
        Args:
            scene: 场景数据字典
        
        Returns:
            节奏同步后的场景数据字典
        """
        # 如果场景缺少节奏数据，跳过同步
        if "rhythm" not in scene or not scene["rhythm"]:
            logger.warning("场景缺少节奏数据，无法进行情感-节奏同步")
            return scene
        
        rhythm_data = scene["rhythm"]
        emotion_type, emotion_intensity = self.detect_scene_emotion(scene)
        
        # 根据情感类型调整节奏同步策略
        if emotion_type in ["紧张", "愤怒", "惊讶"]:
            # 高能量情感：强调高峰点，增加对比度
            high_energy_config = self.rhythm_sync_config.get("high_energy", {})
            video_emphasis = high_energy_config.get("video_emphasis", {})
            audio_emphasis = high_energy_config.get("audio_emphasis", {})
            
            for peak in rhythm_data.get("peaks", []):
                peak_time = peak["time"]
                peak_intensity = peak["intensity"]
                
                # 确定要应用的效果类型
                effect_type = "flash" if emotion_type == "惊讶" else "zoom" if emotion_type == "紧张" else "shake"
                effect_intensity = (
                    video_emphasis.get("flash_intensity", 0.7) if effect_type == "flash" else
                    video_emphasis.get("zoom_intensity", 0.5) if effect_type == "zoom" else
                    video_emphasis.get("shake_intensity", 0.4)
                )
                
                # 在节奏高峰处添加强调效果
                scene["rhythm_effects"] = scene.get("rhythm_effects", []) + [{
                    "type": "emphasis",
                    "time": peak_time,
                    "duration": 0.3,
                    "intensity": peak_intensity * emotion_intensity * effect_intensity,
                    "effect": effect_type
                }]
                
                # 添加音频强调
                scene["rhythm_audio"] = scene.get("rhythm_audio", []) + [{
                    "type": "accent",
                    "time": peak_time,
                    "duration": 0.2,
                    "intensity": peak_intensity * emotion_intensity * audio_emphasis.get("accent_volume", 1.5),
                    "bass_boost": audio_emphasis.get("bass_boost", 4) * (emotion_type == "愤怒" or emotion_type == "紧张")
                }]
        
        elif emotion_type in ["悲伤", "喜悦"]:
            # 情绪性情感：平滑过渡，强调持续性
            emotional_config = self.rhythm_sync_config.get("emotional", {})
            transition_smoothness = emotional_config.get("transition_smoothness", {})
            effect_persistence = emotional_config.get("effect_persistence", {})
            flow_settings = emotional_config.get("flow_settings", {})
            
            # 确定参数值
            smoothness = transition_smoothness.get("sad" if emotion_type == "悲伤" else "happy", 0.7)
            persistence = effect_persistence.get("sad" if emotion_type == "悲伤" else "happy", 0.6)
            
            scene["rhythm_style"] = {
                "transition_smoothness": smoothness,
                "effect_persistence": persistence,
                "beat_alignment": flow_settings.get("beat_alignment", True),
                "emotional_flow": emotion_type,
                "use_crossfade": flow_settings.get("use_crossfade", True)
            }
        
        # 记录节奏同步信息
        scene["emotion_rhythm_sync"] = {
            "applied": True,
            "emotion_type": emotion_type,
            "sync_strategy": "peak_emphasis" if emotion_type in ["紧张", "愤怒", "惊讶"] else "smooth_flow"
        }
        
        return scene
    
    def enhance_scene_group(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        增强一组相关场景，确保情感连贯性
        
        Args:
            scenes: 场景列表
        
        Returns:
            增强后的场景列表
        """
        if not scenes:
            return []
        
        # 分析整体情感走向
        emotion_sequence = []
        for scene in scenes:
            emotion_type, intensity = self.detect_scene_emotion(scene)
            emotion_sequence.append((emotion_type, intensity))
        
        # 构建情感过渡矩阵
        enhanced_scenes = []
        prev_emotion = None
        
        for i, scene in enumerate(scenes):
            # 增强当前场景
            enhanced_scene = self.add_audiovisual_cues(scene)
            
            # 与上一个场景的情感同步
            current_emotion, current_intensity = emotion_sequence[i]
            
            if prev_emotion and prev_emotion != current_emotion:
                # 确定过渡类型
                transition_style = "contrast" if abs(emotion_sequence[i-1][1] - current_intensity) > 0.4 else "gradual"
                
                # 获取过渡配置
                transition_config = self.transition_config.get(transition_style, {})
                
                # 不同情感之间添加过渡效果
                enhanced_scene["emotion_transition"] = {
                    "from": prev_emotion,
                    "to": current_emotion,
                    "transition_style": transition_style,
                    "video_effect": transition_config.get("video_effect"),
                    "audio_effect": transition_config.get("audio_effect"),
                    "duration_factor": transition_config.get("duration_factor", 1.0)
                }
            
            # 更新前一个情感
            prev_emotion = current_emotion
            
            # 应用节奏同步
            enhanced_scene = self.synchronize_emotion_with_rhythm(enhanced_scene)
            enhanced_scenes.append(enhanced_scene)
        
        return enhanced_scenes
    
    def process_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理整个脚本，应用多模态情感共振
        
        Args:
            script: 脚本数据
        
        Returns:
            处理后的脚本数据
        """
        if "scenes" not in script or not script["scenes"]:
            logger.error("脚本缺少场景数据")
            return script
        
        # 分析整个脚本的情感结构
        scenes = script["scenes"]
        scene_groups = []
        current_group = []
        
        # 按情感相似性分组场景
        for scene in scenes:
            if not current_group:
                current_group.append(scene)
                continue
            
            current_emotion, _ = self.detect_scene_emotion(current_group[-1])
            scene_emotion, _ = self.detect_scene_emotion(scene)
            
            # 如果情感类型相同，添加到当前组
            if scene_emotion == current_emotion:
                current_group.append(scene)
            else:
                # 否则处理当前组并开始新组
                scene_groups.append(current_group)
                current_group = [scene]
        
        # 处理最后一组
        if current_group:
            scene_groups.append(current_group)
        
        # 增强每组场景
        enhanced_scenes = []
        for group in scene_groups:
            enhanced_group = self.enhance_scene_group(group)
            enhanced_scenes.extend(enhanced_group)
        
        # 更新脚本
        script["scenes"] = enhanced_scenes
        
        # 添加整体情感走向分析
        script["emotion_flow"] = self.analyze_emotion_flow(enhanced_scenes)
        
        return script
    
    def analyze_emotion_flow(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析场景序列的情感走向
        
        Args:
            scenes: 场景列表
        
        Returns:
            情感走向分析结果
        """
        if not scenes:
            return {"status": "empty", "analysis": None}
        
        # 提取情感序列
        emotion_types = []
        intensities = []
        
        for scene in scenes:
            emotion_type, intensity = (
                scene["applied_emotion_resonance"]["type"],
                scene["applied_emotion_resonance"]["intensity"]
            ) if "applied_emotion_resonance" in scene else self.detect_scene_emotion(scene)
            
            emotion_types.append(emotion_type)
            intensities.append(intensity)
        
        # 计算情感变化率
        intensity_changes = [intensities[i+1] - intensities[i] for i in range(len(intensities)-1)]
        avg_change_rate = np.mean(np.abs(intensity_changes)) if intensity_changes else 0
        
        # 获取情感流程分析配置
        flow_analysis_config = self.config.get("emotion_flow_analysis", {})
        peak_detection = flow_analysis_config.get("peak_detection", {})
        pattern_recognition = flow_analysis_config.get("pattern_recognition", {})
        
        # 检测情感高峰
        peaks = []
        min_intensity = peak_detection.get("min_intensity", 0.6)
        min_prominence = peak_detection.get("min_prominence", 0.2)
        
        for i in range(1, len(intensities)-1):
            if (intensities[i] > intensities[i-1] and 
                intensities[i] > intensities[i+1] and 
                intensities[i] > min_intensity and
                min(intensities[i] - intensities[i-1], intensities[i] - intensities[i+1]) > min_prominence):
                
                peaks.append({
                    "position": i,
                    "emotion_type": emotion_types[i],
                    "intensity": intensities[i]
                })
        
        # 检测主要情感类型
        emotion_counts = {}
        for emotion in emotion_types:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1]) if emotion_counts else (None, 0)
        
        # 确定情感模式
        ascending_threshold = pattern_recognition.get("ascending_threshold", 0.1)
        descending_threshold = pattern_recognition.get("descending_threshold", -0.1)
        overall_change = intensities[-1] - intensities[0] if intensities else 0
        
        emotional_pattern = (
            "ascending" if overall_change > ascending_threshold else 
            "descending" if overall_change < descending_threshold else 
            "stable"
        )
        
        return {
            "status": "analyzed",
            "dominant_emotion": dominant_emotion[0],
            "emotion_variety": len(emotion_counts),
            "avg_intensity": np.mean(intensities),
            "intensity_change_rate": avg_change_rate,
            "emotional_peaks": peaks,
            "emotional_pattern": emotional_pattern,
            "significant_changes": [
                {"position": i+1, "change": change} 
                for i, change in enumerate(intensity_changes) 
                if abs(change) > flow_analysis_config.get("change_rate", {}).get("significant_threshold", 0.15)
            ]
        }

# 实用函数
def apply_multimodal_resonance(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    为单个场景应用多模态情感共振效果
    
    Args:
        scene: 场景数据字典
    
    Returns:
        增强后的场景
    """
    resonator = EmotionalResonance()
    return resonator.add_audiovisual_cues(scene)

def process_script_with_resonance(script: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理整个脚本并应用多模态情感共振
    
    Args:
        script: 脚本数据
    
    Returns:
        处理后的脚本
    """
    resonator = EmotionalResonance()
    return resonator.process_script(script) 