#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时空连续性验证器

此模块提供用于验证短剧混剪场景之间时空连续性的工具。主要功能包括：
1. 时间连续性检查 - 确保场景在时间上的先后顺序合理
2. 空间连续性检查 - 验证场景之间的位置变化是否合理
3. 角色一致性检查 - 确保同一角色在不同场景之间的状态转换合理

使用这些验证工具可以避免混剪过程中产生明显的时空逻辑错误，提高视频的专业性和沉浸感。
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import logging
import math

# 配置日志
logger = logging.getLogger(__name__)

# 定义常量
DEFAULT_TIME_THRESHOLD = 30000  # 默认空间跳转时间阈值，单位为毫秒
TIME_INCONSISTENCY_THRESHOLD = 0  # 时间重叠或倒退阈值
SIGNIFICANT_LOCATION_CHANGE_THRESHOLD = 5000  # 显著位置变化的时间阈值（毫秒）
TRANSPORT_METHODS = {"car", "bus", "train", "plane", "taxi", "subway", "bike", "walk", "teleport", "transport"}

class SpatiotemporalValidator:
    """
    时空连续性验证器
    
    提供场景之间时间和空间连续性的验证功能，识别可能存在的逻辑问题。
    """
    
    def __init__(self, 
                 time_threshold: int = DEFAULT_TIME_THRESHOLD,
                 validate_time: bool = True,
                 validate_space: bool = True,
                 validate_characters: bool = True):
        """
        初始化时空连续性验证器
        
        Args:
            time_threshold: 时间阈值（毫秒），超过此阈值的位置变化需要有合理解释
            validate_time: 是否验证时间连续性
            validate_space: 是否验证空间连续性
            validate_characters: 是否验证角色一致性
        """
        self.time_threshold = time_threshold
        self.validate_time = validate_time
        self.validate_space = validate_space
        self.validate_characters = validate_characters
        self.last_checked_scene = None
        self.character_states: Dict[str, Dict[str, Any]] = {}
        
    def reset(self):
        """重置验证器状态"""
        self.last_checked_scene = None
        self.character_states = {}
    
    def validate_scene_transition(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """
        验证场景切换的时空合理性
        
        检查两个连续场景之间的时间和空间连续性，返回发现的问题列表。
        
        Args:
            prev_scene: 前一个场景的数据
            curr_scene: 当前场景的数据
            
        Returns:
            错误消息列表，如果没有错误则为空列表
        """
        errors = []
        
        # 验证时间连续性
        if self.validate_time:
            time_errors = self._validate_time_continuity(prev_scene, curr_scene)
            errors.extend(time_errors)
        
        # 验证空间连续性
        if self.validate_space:
            space_errors = self._validate_spatial_continuity(prev_scene, curr_scene)
            errors.extend(space_errors)
            
        # 验证角色一致性
        if self.validate_characters and "character" in curr_scene:
            character_errors = self._validate_character_continuity(prev_scene, curr_scene)
            errors.extend(character_errors)
            
        # 更新状态
        self.last_checked_scene = curr_scene
        
        return errors
    
    def _validate_time_continuity(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """
        验证时间连续性
        
        检查场景时间的先后顺序是否合理，识别时间重叠或倒退的问题。
        
        Args:
            prev_scene: 前一个场景
            curr_scene: 当前场景
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查时间戳字段存在性
        required_fields = ["start", "end"]
        for field in required_fields:
            if field not in prev_scene or field not in curr_scene:
                errors.append(f"缺少必要的时间字段: {field}")
                return errors
        
        # 检查当前场景的开始时间是否早于前一个场景的结束时间
        # 注意：这里假设时间是以毫秒为单位的数值
        if curr_scene["start"] < prev_scene["end"] - TIME_INCONSISTENCY_THRESHOLD:
            errors.append(f"时间重叠: 场景 {prev_scene.get('id', '?')} 与 {curr_scene.get('id', '?')}")
        
        return errors
    
    def _validate_spatial_continuity(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """
        验证空间连续性
        
        检查场景位置变化是否合理，对于显著的位置变化需要有合理的解释（如交通工具）。
        
        Args:
            prev_scene: 前一个场景
            curr_scene: 当前场景
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查位置字段
        if "location" not in prev_scene or "location" not in curr_scene:
            return errors  # 如果没有位置信息，则跳过此检查
        
        # 位置发生变化
        if prev_scene["location"] != curr_scene["location"]:
            # 检查场景之间的时间间隔
            time_gap = curr_scene["start"] - prev_scene["end"]
            
            # 检查是否有交通方式的说明
            has_transport = False
            
            # 检查props字段中是否包含交通方式
            if "props" in prev_scene and isinstance(prev_scene["props"], (list, set, dict)):
                if isinstance(prev_scene["props"], (list, set)):
                    has_transport = any(prop in TRANSPORT_METHODS for prop in prev_scene["props"])
                elif isinstance(prev_scene["props"], dict):
                    has_transport = any(prop in TRANSPORT_METHODS for prop in prev_scene["props"].keys())
                    has_transport = has_transport or any(prop in TRANSPORT_METHODS for prop in prev_scene["props"].values() if isinstance(prop, str))
            
            # 检查文本中是否包含交通方式的描述
            if "text" in prev_scene and isinstance(prev_scene["text"], str):
                has_transport = has_transport or any(method.lower() in prev_scene["text"].lower() for method in TRANSPORT_METHODS)
            
            # 如果时间间隔短且没有交通方式的说明，则可能存在空间连续性问题
            if time_gap < self.time_threshold and not has_transport:
                errors.append(f"空间跳转: {prev_scene['location']}→{curr_scene['location']} 时间间隔仅 {time_gap/1000:.1f}秒")
        
        return errors
    
    def _validate_character_continuity(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any]) -> List[str]:
        """
        验证角色一致性
        
        检查同一角色在不同场景之间的状态变化是否合理。
        
        Args:
            prev_scene: 前一个场景
            curr_scene: 当前场景
            
        Returns:
            错误消息列表
        """
        errors = []
        
        # 检查角色字段
        if "character" not in prev_scene or "character" not in curr_scene:
            return errors
        
        # 获取当前场景的角色
        curr_character = curr_scene["character"]
        prev_character = prev_scene["character"]
        
        # 若是相同角色，检查状态变化
        if curr_character == prev_character:
            # 检查情感变化是否合理
            if "emotion" in prev_scene and "emotion" in curr_scene:
                prev_emotion = prev_scene["emotion"]
                curr_emotion = curr_scene["emotion"]
                
                # 检测极端情感突变（如从"悲伤"直接到"狂喜"）
                if self._is_emotion_jump_extreme(prev_emotion, curr_emotion):
                    time_gap = curr_scene["start"] - prev_scene["end"]
                    if time_gap < 10000:  # 10秒内的极端情感变化
                        errors.append(f"角色 {curr_character} 情感突变: {prev_emotion}→{curr_emotion}")
        
        # 更新角色状态
        if curr_character not in self.character_states:
            self.character_states[curr_character] = {}
        
        # 记录当前角色状态
        for key in ["emotion", "location", "props"]:
            if key in curr_scene:
                self.character_states[curr_character][key] = curr_scene[key]
        
        return errors
    
    def _is_emotion_jump_extreme(self, prev_emotion: str, curr_emotion: str) -> bool:
        """
        判断情感变化是否极端
        
        Args:
            prev_emotion: 前一个情感状态
            curr_emotion: 当前情感状态
            
        Returns:
            情感变化是否极端
        """
        # 定义对立情感对
        opposing_emotions = [
            {"悲伤", "伤心", "痛苦", "哀伤", "绝望"} | {"喜悦", "开心", "狂喜", "兴奋", "欣喜"}
        ]
        
        # 检查两个情感是否属于对立情感对
        for emotion_set in opposing_emotions:
            if (prev_emotion.lower() in {e.lower() for e in emotion_set} and 
                curr_emotion.lower() in {e.lower() for e in emotion_set} and
                prev_emotion.lower() != curr_emotion.lower()):
                return True
        
        return False
    
    def validate_scene_sequence(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证整个场景序列的时空连续性
        
        Args:
            scenes: 场景列表
            
        Returns:
            验证结果，包含错误消息和统计信息
        """
        results = {
            "errors": [],
            "scene_count": len(scenes),
            "error_count": 0,
            "time_errors": 0,
            "space_errors": 0,
            "character_errors": 0
        }
        
        if len(scenes) < 2:
            return results
        
        # 重置验证器状态
        self.reset()
        
        # 逐一验证相邻场景的过渡
        for i in range(1, len(scenes)):
            prev_scene = scenes[i-1]
            curr_scene = scenes[i]
            
            errors = self.validate_scene_transition(prev_scene, curr_scene)
            
            # 记录错误及其类型
            for error in errors:
                error_info = {
                    "message": error,
                    "prev_scene_id": prev_scene.get("id", f"scene_{i-1}"),
                    "curr_scene_id": curr_scene.get("id", f"scene_{i}"),
                    "type": self._categorize_error(error)
                }
                results["errors"].append(error_info)
                
                # 统计不同类型的错误
                error_type = error_info["type"]
                results["error_count"] += 1
                results[f"{error_type}_errors"] = results.get(f"{error_type}_errors", 0) + 1
        
        return results
    
    def _categorize_error(self, error_message: str) -> str:
        """
        对错误消息进行分类
        
        Args:
            error_message: 错误消息
            
        Returns:
            错误类型（time, space, character）
        """
        if "时间" in error_message:
            return "time"
        if "空间" in error_message:
            return "space"
        if "角色" in error_message:
            return "character"
        return "other"
    
    def generate_fix_suggestions(self, prev_scene: Dict[str, Any], curr_scene: Dict[str, Any], 
                                 errors: List[str]) -> List[str]:
        """
        为检测到的问题生成修复建议
        
        Args:
            prev_scene: 前一个场景
            curr_scene: 当前场景
            errors: 错误消息列表
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        for error in errors:
            # 时间重叠问题的建议
            if "时间重叠" in error:
                suggestions.append(f"建议: 调整 {curr_scene.get('id', '当前场景')} 的开始时间至 {prev_scene.get('end', 0)} 之后")
            
            # 空间跳转问题的建议
            elif "空间跳转" in error:
                time_gap = curr_scene["start"] - prev_scene["end"]
                if time_gap < 5000:  # 5秒内
                    suggestions.append(f"建议: 添加过渡场景说明 {prev_scene.get('location', '?')} 至 {curr_scene.get('location', '?')} 的移动")
                else:
                    suggestions.append(f"建议: 在 {prev_scene.get('id', '前一场景')} 的描述中添加移动方式信息")
            
            # 角色情感突变问题的建议
            elif "情感突变" in error:
                suggestions.append(f"建议: 增加过渡场景或延长时间间隔，使情感变化更加自然")
        
        return suggestions
    
    def analyze_narrative_coherence(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析场景序列的叙事连贯性
        
        检查场景序列的叙事结构是否合理，是否符合基本的故事框架。
        
        Args:
            scenes: 场景列表
            
        Returns:
            分析结果，包含叙事结构评估和改进建议
        """
        if not scenes or len(scenes) < 3:
            return {"status": "too_few_scenes", "message": "场景数量过少，无法进行完整叙事分析"}
        
        result = {
            "narrative_score": 0.0,
            "structure_issues": [],
            "strengths": [],
            "suggestions": []
        }
        
        # 检查是否有明确的开始和结束
        has_opening = self._has_opening_scene(scenes)
        has_closing = self._has_closing_scene(scenes)
        
        if not has_opening:
            result["structure_issues"].append("缺少明确的开场/建立场景")
            result["suggestions"].append("考虑添加一个建立场景背景的开场镜头")
        else:
            result["strengths"].append("具有清晰的开场场景，有助于观众理解情境")
            
        if not has_closing:
            result["structure_issues"].append("缺少明确的结尾/收尾场景")
            result["suggestions"].append("考虑添加一个总结或呼应开场的结尾场景")
        else:
            result["strengths"].append("具有完整的结尾场景，使故事感觉完整")
        
        # 检查情节峰值
        emotional_peaks = self._find_emotional_peaks(scenes)
        if not emotional_peaks:
            result["structure_issues"].append("缺少情感高潮点")
            result["suggestions"].append("考虑添加情感强度较高的场景作为故事高潮")
        elif len(emotional_peaks) > 1:
            positions = [f"场景{peak+1}" for peak in emotional_peaks]
            result["strengths"].append(f"在{', '.join(positions)}处有多个情感强度高点，使叙事更有层次")
        
        # 计算叙事评分 (0.0-10.0)
        base_score = 5.0
        
        # 加分项
        if has_opening: base_score += 1.0
        if has_closing: base_score += 1.0
        if emotional_peaks: base_score += len(emotional_peaks) * 0.5
        
        # 减分项
        base_score -= len(result["structure_issues"]) * 0.5
        
        # 确保分数在合理范围内
        result["narrative_score"] = max(0.0, min(10.0, base_score))
        
        return result
    
    def _has_opening_scene(self, scenes: List[Dict[str, Any]]) -> bool:
        """检查是否有适合的开场场景"""
        if not scenes:
            return False
            
        # 检查第一个场景是否包含位置建立、角色介绍等关键元素
        opening_scene = scenes[0]
        
        # 检查是否有位置描述
        has_location = "location" in opening_scene and opening_scene["location"]
        
        # 检查是否有角色介绍
        has_character = "character" in opening_scene and opening_scene["character"]
        
        # 检查文本是否包含介绍性内容
        has_intro_text = False
        if "text" in opening_scene and opening_scene["text"]:
            intro_keywords = ["我是", "这是", "今天", "开始", "第一次"]
            has_intro_text = any(keyword in opening_scene["text"] for keyword in intro_keywords)
        
        return (has_location and has_character) or has_intro_text
    
    def _has_closing_scene(self, scenes: List[Dict[str, Any]]) -> bool:
        """检查是否有适合的结尾场景"""
        if not scenes:
            return False
            
        # 检查最后一个场景是否包含结尾特征
        closing_scene = scenes[-1]
        
        # 检查文本是否包含结束性内容
        has_closing_text = False
        if "text" in closing_scene and closing_scene["text"]:
            closing_keywords = ["结束", "完成", "最后", "再见", "明白了", "终于", "谢谢"]
            has_closing_text = any(keyword in closing_scene["text"] for keyword in closing_keywords)
        
        # 检查情感是否为结束性情感
        has_closing_emotion = False
        if "emotion" in closing_scene:
            closing_emotions = ["满足", "解脱", "理解", "平静", "释然", "成功", "希望"]
            has_closing_emotion = any(emotion in closing_scene["emotion"] for emotion in closing_emotions)
        
        return has_closing_text or has_closing_emotion
    
    def _find_emotional_peaks(self, scenes: List[Dict[str, Any]]) -> List[int]:
        """
        找出情感高潮点
        
        返回情感强度较高的场景索引列表
        """
        peaks = []
        
        # 情感强度词典
        emotion_intensity = {
            "惊讶": 0.8, "震惊": 0.9, "惊喜": 0.8, "惊恐": 0.9,
            "绝望": 0.9, "崩溃": 0.9, "愤怒": 0.8, "狂喜": 0.9,
            "痛苦": 0.8, "悲伤": 0.7, "兴奋": 0.7, "恐惧": 0.8,
            "愤怒": 0.8, "激动": 0.7, "慌张": 0.7, "惊慌": 0.8,
            "平静": 0.3, "满足": 0.5, "开心": 0.6, "期待": 0.5
        }
        
        # 文本强度关键词
        intensity_keywords = {
            "不敢相信": 0.8, "太棒了": 0.7, "真是太": 0.7, "绝不": 0.7,
            "永远": 0.6, "绝对": 0.7, "从来没有": 0.7, "一定": 0.6,
            "怎么可能": 0.7, "不可能": 0.7, "必须": 0.6, "非常": 0.6,
            "极其": 0.8, "太": 0.6, "最": 0.6, "完全": 0.6
        }
        
        # 计算每个场景的情感强度
        scene_intensities = []
        for scene in scenes:
            intensity = 0.4  # 基础值
            
            # 从情感标签计算强度
            if "emotion" in scene and scene["emotion"]:
                emotion_value = emotion_intensity.get(scene["emotion"], 0.5)
                intensity = max(intensity, emotion_value)
            
            # 从文本计算强度
            if "text" in scene and scene["text"]:
                for keyword, value in intensity_keywords.items():
                    if keyword in scene["text"]:
                        intensity = max(intensity, value)
            
            # 考虑场景重要性（如果有标记）
            if "importance" in scene:
                importance = float(scene["importance"])
                intensity = (intensity + importance) / 2
                
            scene_intensities.append(intensity)
        
        # 找出局部峰值（比前后场景都强的点）
        for i in range(1, len(scene_intensities) - 1):
            if (scene_intensities[i] > scene_intensities[i-1] and 
                scene_intensities[i] > scene_intensities[i+1] and
                scene_intensities[i] >= 0.7):  # 只考虑较高强度的场景
                peaks.append(i)
        
        # 如果没有找到峰值，但有高强度场景，也将其视为峰值
        if not peaks:
            for i, intensity in enumerate(scene_intensities):
                if intensity >= 0.8:
                    peaks.append(i)
        
        return peaks
    
    def analyze_visual_continuity(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析视觉连续性
        
        检查场景之间的视觉元素是否连贯，如光线、颜色、服装等。
        
        Args:
            scenes: 场景列表
            
        Returns:
            分析结果，包含视觉连续性评估和改进建议
        """
        result = {
            "visual_continuity_issues": [],
            "suggestions": []
        }
        
        # 跳过只有一个场景的情况
        if not scenes or len(scenes) < 2:
            return result
        
        # 记录各场景的视觉特征
        for i in range(1, len(scenes)):
            prev_scene = scenes[i-1]
            curr_scene = scenes[i]
            
            # 检查场景来源是否不同
            if "source_file" in prev_scene and "source_file" in curr_scene:
                if prev_scene["source_file"] != curr_scene["source_file"]:
                    # 检查时间是否连续
                    if "end" in prev_scene and "start" in curr_scene:
                        time_gap = curr_scene["start"] - prev_scene["end"]
                        if time_gap < 1000:  # 1秒内的剪辑
                            result["visual_continuity_issues"].append(
                                f"场景{i}和场景{i+1}来自不同源文件且时间间隔小，可能导致视觉跳跃"
                            )
                            result["suggestions"].append(
                                f"考虑在场景{i}和{i+1}之间添加过渡效果或增加时间间隔"
                            )
            
            # 检查白天/黑夜的突变
            if "time_of_day" in prev_scene and "time_of_day" in curr_scene:
                if prev_scene["time_of_day"] != curr_scene["time_of_day"]:
                    if "end" in prev_scene and "start" in curr_scene:
                        time_gap = curr_scene["start"] - prev_scene["end"]
                        if time_gap < 5000:  # 5秒内的白天/黑夜变化
                            result["visual_continuity_issues"].append(
                                f"场景{i}和场景{i+1}之间有白天/黑夜的突变"
                            )
                            result["suggestions"].append(
                                f"在场景{i}和{i+1}之间添加时间过渡提示或使用渐变效果"
                            )
            
            # 检查服装连续性
            if ("character" in prev_scene and "character" in curr_scene and 
                prev_scene["character"] == curr_scene["character"]):
                if "costume" in prev_scene and "costume" in curr_scene:
                    if prev_scene["costume"] != curr_scene["costume"]:
                        result["visual_continuity_issues"].append(
                            f"角色{prev_scene['character']}在连续场景中服装发生变化"
                        )
                        result["suggestions"].append(
                            f"确保同一角色在连续场景中服装一致，或添加更衣/时间跳跃的说明"
                        )
        
        return result
    
    def analyze_editing_patterns(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析剪辑模式
        
        识别视频中使用的剪辑模式，并提供改进建议。
        
        Args:
            scenes: 场景列表
            
        Returns:
            分析结果，包含剪辑模式评估和改进建议
        """
        result = {
            "identified_patterns": [],
            "suggestions": []
        }
        
        # 至少需要3个场景才能分析模式
        if not scenes or len(scenes) < 3:
            return result
        
        # 分析场景持续时间
        durations = []
        for scene in scenes:
            if "start" in scene and "end" in scene:
                duration = scene["end"] - scene["start"]
                durations.append(duration)
        
        # 检查场景时长是否均匀
        if durations:
            avg_duration = sum(durations) / len(durations)
            duration_variation = [abs(d - avg_duration) / avg_duration for d in durations]
            avg_variation = sum(duration_variation) / len(duration_variation)
            
            if avg_variation < 0.2:
                result["identified_patterns"].append("均匀场景长度")
                result["suggestions"].append(
                    "场景长度过于均匀，考虑根据内容重要性调整场景长度，增加节奏变化"
                )
            elif avg_variation > 0.7:
                result["identified_patterns"].append("场景长度差异较大")
            
        # 检查对话模式
        dialogue_alternations = 0
        last_speaker = None
        
        for scene in scenes:
            if "character" in scene:
                current_speaker = scene["character"]
                if last_speaker and current_speaker != last_speaker:
                    dialogue_alternations += 1
                last_speaker = current_speaker
        
        if dialogue_alternations > len(scenes) * 0.4:
            result["identified_patterns"].append("频繁的对话切换")
            
            # 检查对话场景的时长
            short_dialogues = 0
            for duration in durations:
                if duration < 3000:  # 3秒以下的场景
                    short_dialogues += 1
            
            if short_dialogues > len(scenes) * 0.3:
                result["suggestions"].append(
                    "对话场景过短，考虑合并相关对话或使用过肩镜头减少切换频率"
                )
        
        # 检查情感变化模式
        emotions = []
        for scene in scenes:
            if "emotion" in scene:
                emotions.append(scene["emotion"])
        
        if len(emotions) >= 3:
            emotion_changes = 0
            for i in range(1, len(emotions)):
                if emotions[i] != emotions[i-1]:
                    emotion_changes += 1
            
            if emotion_changes == 0:
                result["identified_patterns"].append("情感单一")
                result["suggestions"].append(
                    "场景情感变化不足，考虑增加情感变化以增强观众兴趣"
                )
            elif emotion_changes / len(emotions) > 0.7:
                result["identified_patterns"].append("情感变化频繁")
                result["suggestions"].append(
                    "情感变化过于频繁，考虑让情感变化更加渐进，增加情感发展的层次感"
                )
        
        # 检查是否有交叉剪辑模式
        locations = []
        for scene in scenes:
            if "location" in scene:
                locations.append(scene["location"])
        
        if len(set(locations)) >= 2:
            alternating_locations = 0
            for i in range(1, len(locations) - 1):
                if locations[i] != locations[i-1] and locations[i] != locations[i+1]:
                    alternating_locations += 1
            
            if alternating_locations >= len(locations) * 0.2:
                result["identified_patterns"].append("交叉剪辑")
                result["suggestions"].append(
                    "检测到交叉剪辑模式，确保不同地点的事件有明确的时间关系"
                )
        
        return result

# 辅助函数
def parse_time_ms(time_str: str) -> int:
    """
    解析时间字符串为毫秒数
    
    支持格式: 
    - HH:MM:SS,mmm
    - MM:SS,mmm
    - SS,mmm
    - 纯数字（直接作为毫秒返回）
    
    Args:
        time_str: 时间字符串
        
    Returns:
        毫秒数
    """
    if isinstance(time_str, (int, float)):
        return int(time_str)
        
    if not isinstance(time_str, str):
        raise ValueError(f"不支持的时间格式: {time_str}")
    
    # 尝试直接解析为数字
    try:
        return int(float(time_str))
    except ValueError:
        pass
    
    # 解析时:分:秒,毫秒格式
    parts = time_str.replace('.', ',').split(',')
    time_parts = parts[0].split(':')
    milliseconds = int(parts[1]) if len(parts) > 1 else 0
    
    if len(time_parts) == 3:  # HH:MM:SS
        hours, minutes, seconds = time_parts
        return (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + milliseconds
    elif len(time_parts) == 2:  # MM:SS
        minutes, seconds = time_parts
        return (int(minutes) * 60 + int(seconds)) * 1000 + milliseconds
    else:  # SS
        return int(time_parts[0]) * 1000 + milliseconds

def format_time_ms(ms: int) -> str:
    """
    将毫秒数格式化为时:分:秒,毫秒格式
    
    Args:
        ms: 毫秒数
        
    Returns:
        格式化的时间字符串
    """
    seconds, milliseconds = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def preprocess_scene_data(scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    预处理场景数据，确保所有必要的字段都存在且格式正确
    
    Args:
        scene: 原始场景数据
        
    Returns:
        处理后的场景数据
    """
    processed = scene.copy()
    
    # 确保时间字段是毫秒整数
    for field in ["start", "end"]:
        if field in processed and not isinstance(processed[field], (int, float)):
            processed[field] = parse_time_ms(processed[field])
    
    # 计算持续时间（如果没有提供）
    if "start" in processed and "end" in processed and "duration" not in processed:
        processed["duration"] = processed["end"] - processed["start"]
    
    return processed

def validate_spatiotemporal_logic(scenes: List[Dict[str, Any]], 
                                  time_threshold: int = DEFAULT_TIME_THRESHOLD,
                                  preprocess: bool = True) -> Dict[str, Any]:
    """
    便捷函数：验证场景序列的时空逻辑
    
    Args:
        scenes: 场景序列
        time_threshold: 时间阈值（毫秒）
        preprocess: 是否预处理场景数据
        
    Returns:
        验证结果
    """
    # 预处理场景数据
    if preprocess:
        processed_scenes = [preprocess_scene_data(scene) for scene in scenes]
    else:
        processed_scenes = scenes
    
    # 创建验证器并执行验证
    validator = SpatiotemporalValidator(time_threshold=time_threshold)
    return validator.validate_scene_sequence(processed_scenes)

# 提供给其他模块使用的API
__all__ = [
    'SpatiotemporalValidator',
    'validate_spatiotemporal_logic',
    'parse_time_ms',
    'format_time_ms',
    'preprocess_scene_data'
] 