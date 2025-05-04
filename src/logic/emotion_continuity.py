#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
情感演进监测器

此模块提供用于分析和监测视频场景间情感连贯性的工具。主要功能包括：
1. 情感跳跃检测 - 识别场景之间不自然的情感变化
2. 情感曲线分析 - 评估整体视频的情感起伏是否符合预期模式
3. 情感节奏构建 - 确保视频情感变化的节奏感
4. 情感冲突检测 - 分析跨场景的情感冲突
5. 情感连贯性建议 - 提供改善情感连贯性的建议

通过监测和分析视频的情感流动，可以增强视频的叙事连贯性和观众体验。
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import matplotlib.pyplot as plt
from enum import Enum, auto
import json
from pathlib import Path

# 尝试导入项目内部模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    logging.warning("无法导入完整的异常处理模块，将使用基础异常类")
    
    class ErrorCode:
        VALIDATION_ERROR = 1005
        NARRATIVE_ANALYSIS_ERROR = 1405
    
    class ClipMasterError(Exception):
        def __init__(self, message, code=None, details=None):
            self.message = message
            self.code = code
            self.details = details or {}
            super().__init__(message)

# 配置日志
logger = logging.getLogger(__name__)

class EmotionCategory(Enum):
    """情感类别枚举"""
    HAPPINESS = auto()
    SADNESS = auto()
    ANGER = auto()
    FEAR = auto()
    DISGUST = auto()
    SURPRISE = auto()
    NEUTRAL = auto()
    ANTICIPATION = auto()
    TRUST = auto()
    
    @classmethod
    def from_string(cls, emotion_name: str) -> 'EmotionCategory':
        """从字符串获取情感类别"""
        mapping = {
            "happy": cls.HAPPINESS,
            "happiness": cls.HAPPINESS,
            "joy": cls.HAPPINESS,
            
            "sad": cls.SADNESS,
            "sadness": cls.SADNESS,
            "grief": cls.SADNESS,
            
            "angry": cls.ANGER,
            "anger": cls.ANGER,
            "rage": cls.ANGER,
            
            "fear": cls.FEAR,
            "fearful": cls.FEAR,
            "scared": cls.FEAR,
            
            "disgust": cls.DISGUST,
            "disgusted": cls.DISGUST,
            
            "surprise": cls.SURPRISE,
            "surprised": cls.SURPRISE,
            "shocked": cls.SURPRISE,
            
            "neutral": cls.NEUTRAL,
            
            "anticipation": cls.ANTICIPATION,
            "expectation": cls.ANTICIPATION,
            
            "trust": cls.TRUST,
            "trustful": cls.TRUST
        }
        
        lower_name = emotion_name.lower()
        if lower_name in mapping:
            return mapping[lower_name]
        
        # 如果没有精确匹配，尝试部分匹配
        for key, value in mapping.items():
            if key in lower_name:
                return value
        
        return cls.NEUTRAL  # 默认为中性情感

class EmotionDiscontinuityError(ClipMasterError):
    """情感不连贯异常
    
    当场景之间情感变化过大或缺乏合理过渡时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """初始化情感不连贯异常
        
        Args:
            message: 错误信息
            details: 详细信息，包含场景间情感跳跃的具体描述
        """
        super().__init__(
            message,
            code=ErrorCode.NARRATIVE_ANALYSIS_ERROR,
            details=details or {}
        )

class EmotionTransitionMonitor:
    """情感过渡监测器
    
    用于监测和分析视频场景间的情感变化，确保情感过渡自然流畅。
    """
    
    # 相邻场景情感最大允许跳跃度
    MAX_JUMP = 0.5
    
    # 情感冲突矩阵 - 定义哪些情感之间的转变需要额外的过渡
    EMOTION_CONFLICT_MATRIX = {
        EmotionCategory.HAPPINESS: [EmotionCategory.SADNESS, EmotionCategory.ANGER, EmotionCategory.DISGUST],
        EmotionCategory.SADNESS: [EmotionCategory.HAPPINESS, EmotionCategory.ANTICIPATION],
        EmotionCategory.ANGER: [EmotionCategory.HAPPINESS, EmotionCategory.TRUST],
        EmotionCategory.FEAR: [EmotionCategory.TRUST, EmotionCategory.HAPPINESS],
        EmotionCategory.DISGUST: [EmotionCategory.HAPPINESS, EmotionCategory.TRUST],
        EmotionCategory.SURPRISE: [],  # 惊讶可以与任何情感自然过渡
        EmotionCategory.NEUTRAL: [],   # 中性情感可以与任何情感自然过渡
        EmotionCategory.ANTICIPATION: [EmotionCategory.SADNESS, EmotionCategory.DISGUST],
        EmotionCategory.TRUST: [EmotionCategory.FEAR, EmotionCategory.ANGER, EmotionCategory.DISGUST]
    }
    
    def __init__(self, max_jump: float = None, emotion_rhythms_path: str = None):
        """初始化情感过渡监测器
        
        Args:
            max_jump: 相邻场景情感最大允许跳跃度，默认为0.5
            emotion_rhythms_path: 情感节奏模式数据文件路径
        """
        self.max_jump = max_jump if max_jump is not None else self.MAX_JUMP
        self.emotion_rhythms = self._load_emotion_rhythms(emotion_rhythms_path)
        self.emotion_curve = []  # 存储情感曲线
        self.transition_points = []  # 存储关键情感转变点
        
    def _load_emotion_rhythms(self, path: Optional[str]) -> Dict[str, List[float]]:
        """加载预定义的情感节奏模式
        
        Args:
            path: 情感节奏数据文件路径
            
        Returns:
            情感节奏模式字典
        """
        default_rhythms = {
            "mountain": [0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 0.7, 0.5, 0.3, 0.2],  # 山形曲线
            "valley": [0.8, 0.6, 0.4, 0.2, 0.1, 0.1, 0.2, 0.4, 0.6, 0.8],    # 谷形曲线
            "rising": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],    # 上升曲线
            "falling": [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],   # 下降曲线
            "wave": [0.5, 0.7, 0.9, 0.7, 0.5, 0.3, 0.1, 0.3, 0.5, 0.7]       # 波浪曲线
        }
        
        if not path:
            return default_rhythms
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                custom_rhythms = json.load(f)
                # 合并自定义节奏和默认节奏
                default_rhythms.update(custom_rhythms)
                return default_rhythms
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"加载情感节奏文件失败: {e}，将使用默认节奏")
            return default_rhythms
    
    def check_emotion_flow(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """监测情感曲线综合连贯性
        
        分析整个场景序列的情感流动，识别情感跳跃
        
        Args:
            scenes: 场景列表，每个场景包含情感评分
            
        Returns:
            情感问题列表，包含问题类型和位置
            
        Raises:
            EmotionDiscontinuityError: 当情感变化过大时抛出
        """
        if not scenes or len(scenes) < 2:
            return []  # 场景不足，无法分析
        
        problems = []
        prev_score = scenes[0]["emotion_score"]
        self.emotion_curve = [prev_score]  # 记录情感曲线
        
        for i, scene in enumerate(scenes[1:], 1):
            current_score = scene["emotion_score"]
            self.emotion_curve.append(current_score)
            
            # 计算情感变化幅度
            delta = abs(current_score - prev_score)
            
            # 检测情感跳跃
            if delta > self.max_jump:
                problem = {
                    "type": "emotion_jump",
                    "position": i,
                    "prev_scene_id": scenes[i-1]["id"],
                    "current_scene_id": scene["id"],
                    "delta": delta,
                    "prev_score": prev_score,
                    "current_score": current_score,
                    "message": f"场景{scene['id']}情感跳跃过大: {prev_score}->{current_score}"
                }
                problems.append(problem)
                
                # 如果需要立即抛出异常，取消下面的注释
                # raise EmotionDiscontinuityError(
                #     problem["message"],
                #     details={
                #         "prev_scene": scenes[i-1]["id"],
                #         "current_scene": scene["id"],
                #         "delta": delta
                #     }
                # )
                
                # 添加转变点记录
                self.transition_points.append({
                    "position": i,
                    "scenes": [scenes[i-1]["id"], scene["id"]],
                    "delta": delta
                })
            
            prev_score = current_score
        
        return problems
    
    def analyze_emotion_conflicts(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析场景间的情感冲突
        
        检测场景间的情感类型转变是否存在冲突，基于情感冲突矩阵
        
        Args:
            scenes: 场景列表，每个场景包含emotion_type字段
            
        Returns:
            情感冲突列表
        """
        if not scenes or len(scenes) < 2:
            return []
        
        conflicts = []
        
        for i, scene in enumerate(scenes[1:], 1):
            # 获取前一个场景和当前场景的情感类型
            prev_scene = scenes[i-1]
            
            if "emotion_type" not in prev_scene or "emotion_type" not in scene:
                continue
                
            prev_emotion = EmotionCategory.from_string(prev_scene["emotion_type"])
            current_emotion = EmotionCategory.from_string(scene["emotion_type"])
            
            # 检查是否存在情感冲突
            if current_emotion in self.EMOTION_CONFLICT_MATRIX.get(prev_emotion, []):
                conflict = {
                    "type": "emotion_conflict",
                    "position": i,
                    "prev_scene_id": prev_scene["id"],
                    "current_scene_id": scene["id"],
                    "prev_emotion": prev_emotion.name,
                    "current_emotion": current_emotion.name,
                    "message": f"场景{scene['id']}与前一场景情感冲突: {prev_emotion.name}->{current_emotion.name}"
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def evaluate_rhythm_alignment(self, scenes: List[Dict[str, Any]], target_rhythm: str = None) -> Dict[str, Any]:
        """评估情感曲线与目标节奏的匹配度
        
        Args:
            scenes: 场景列表
            target_rhythm: 目标节奏类型，如"mountain", "valley"等
            
        Returns:
            包含匹配度评分和建议的字典
        """
        if not scenes or len(scenes) < 2:
            return {"score": 0, "message": "场景不足，无法分析节奏"}
        
        # 提取情感分数
        emotion_scores = [scene.get("emotion_score", 0.5) for scene in scenes]
        
        # 如果未指定目标节奏，则基于场景内容自动选择最佳节奏
        if not target_rhythm:
            target_rhythm = self._select_best_rhythm(emotion_scores)
        
        # 获取目标节奏模式
        rhythm_pattern = self.emotion_rhythms.get(target_rhythm)
        if not rhythm_pattern:
            return {"score": 0, "message": f"未找到节奏类型: {target_rhythm}"}
        
        # 调整目标节奏的长度匹配场景数量
        adjusted_pattern = self._adjust_rhythm_length(rhythm_pattern, len(emotion_scores))
        
        # 计算情感曲线与目标节奏的相似度
        similarity = self._calculate_similarity(emotion_scores, adjusted_pattern)
        
        # 生成评估结果
        result = {
            "target_rhythm": target_rhythm,
            "similarity_score": similarity,
            "emotion_curve": emotion_scores,
            "target_curve": adjusted_pattern,
            "message": self._generate_rhythm_message(similarity, target_rhythm)
        }
        
        # 添加改进建议
        if similarity < 0.7:
            result["suggestions"] = self._generate_rhythm_suggestions(
                emotion_scores, adjusted_pattern, scenes
            )
        
        return result
    
    def _select_best_rhythm(self, emotion_scores: List[float]) -> str:
        """基于情感分数自动选择最佳匹配的节奏类型
        
        Args:
            emotion_scores: 情感分数列表
            
        Returns:
            最佳匹配的节奏类型名称
        """
        best_rhythm = "wave"  # 默认为波浪型
        best_similarity = -1
        
        for rhythm_name, pattern in self.emotion_rhythms.items():
            adjusted_pattern = self._adjust_rhythm_length(pattern, len(emotion_scores))
            similarity = self._calculate_similarity(emotion_scores, adjusted_pattern)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_rhythm = rhythm_name
        
        return best_rhythm
    
    def _adjust_rhythm_length(self, pattern: List[float], target_length: int) -> List[float]:
        """调整节奏模式的长度以匹配目标长度
        
        Args:
            pattern: 原始节奏模式
            target_length: 目标长度
            
        Returns:
            调整后的节奏模式
        """
        if len(pattern) == target_length:
            return pattern
        
        # 使用线性插值调整长度
        indices = np.linspace(0, len(pattern) - 1, target_length)
        return [pattern[int(i)] if i.is_integer() else 
                pattern[int(i)] * (1 - (i - int(i))) + pattern[min(int(i) + 1, len(pattern) - 1)] * (i - int(i)) 
                for i in indices]
    
    def _calculate_similarity(self, curve1: List[float], curve2: List[float]) -> float:
        """计算两条曲线的相似度
        
        Args:
            curve1: 第一条曲线
            curve2: 第二条曲线
            
        Returns:
            相似度评分 (0-1)
        """
        if len(curve1) != len(curve2):
            raise ValueError("曲线长度必须相同")
        
        # 计算欧几里得距离的归一化倒数
        diffs = [(a - b) ** 2 for a, b in zip(curve1, curve2)]
        distance = np.sqrt(sum(diffs))
        max_distance = np.sqrt(len(curve1) * 1.0)  # 最大可能距离
        
        similarity = 1 - (distance / max_distance)
        return max(0, min(1, similarity))  # 确保在0-1范围内
    
    def _generate_rhythm_message(self, similarity: float, rhythm_type: str) -> str:
        """生成节奏评估消息
        
        Args:
            similarity: 相似度评分
            rhythm_type: 节奏类型
            
        Returns:
            评估消息
        """
        if similarity >= 0.9:
            return f"情感曲线与{rhythm_type}节奏非常匹配，效果出色"
        elif similarity >= 0.7:
            return f"情感曲线与{rhythm_type}节奏较好匹配，整体流畅"
        elif similarity >= 0.5:
            return f"情感曲线与{rhythm_type}节奏部分匹配，有改进空间"
        else:
            return f"情感曲线与{rhythm_type}节奏匹配度低，建议调整"
    
    def _generate_rhythm_suggestions(
        self, 
        actual_curve: List[float], 
        target_curve: List[float],
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成改进情感节奏的建议
        
        Args:
            actual_curve: 实际情感曲线
            target_curve: 目标情感曲线
            scenes: 场景列表
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 寻找最大差异点
        diffs = [(i, abs(a - t)) for i, (a, t) in enumerate(zip(actual_curve, target_curve))]
        diffs.sort(key=lambda x: x[1], reverse=True)
        
        # 为差异最大的3个点提供建议
        for idx, diff in diffs[:3]:
            if diff < 0.2:  # 如果差异不大，跳过
                continue
                
            scene = scenes[idx]
            target = target_curve[idx]
            actual = actual_curve[idx]
            
            suggestion = {
                "scene_id": scene["id"],
                "position": idx,
                "current_emotion": actual,
                "target_emotion": target,
                "diff": diff
            }
            
            if actual < target:
                suggestion["message"] = f"场景{scene['id']}的情感强度需要增强，建议增加情感元素"
                suggestion["action"] = "increase_emotion"
            else:
                suggestion["message"] = f"场景{scene['id']}的情感强度需要降低，建议减弱情感元素"
                suggestion["action"] = "decrease_emotion"
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def visualize_emotion_curve(
        self, 
        scenes: List[Dict[str, Any]], 
        target_rhythm: str = None,
        output_path: str = None
    ) -> Optional[str]:
        """可视化情感曲线
        
        创建情感曲线的图表，可选择与目标节奏进行对比
        
        Args:
            scenes: 场景列表
            target_rhythm: 可选的目标节奏类型
            output_path: 输出文件路径
            
        Returns:
            如果指定了output_path，返回保存的文件路径；否则在交互式环境中显示图表
        """
        try:
            import matplotlib.pyplot as plt
            
            # 提取情感分数和场景ID
            emotion_scores = [scene.get("emotion_score", 0.5) for scene in scenes]
            scene_ids = [scene.get("id", f"Scene {i}") for i, scene in enumerate(scenes)]
            
            # 创建图表
            plt.figure(figsize=(12, 6))
            plt.plot(emotion_scores, 'b-o', label='实际情感曲线')
            
            # 如果指定了目标节奏，添加对比曲线
            if target_rhythm and target_rhythm in self.emotion_rhythms:
                rhythm_pattern = self.emotion_rhythms[target_rhythm]
                adjusted_pattern = self._adjust_rhythm_length(rhythm_pattern, len(emotion_scores))
                plt.plot(adjusted_pattern, 'r--x', label=f'目标节奏: {target_rhythm}')
            
            # 添加转变点标记
            for point in self.transition_points:
                plt.axvline(x=point["position"], color='g', linestyle='--', alpha=0.5)
            
            # 设置图表属性
            plt.title('视频情感曲线分析')
            plt.xlabel('场景序号')
            plt.ylabel('情感强度')
            plt.xticks(range(len(scene_ids)), scene_ids, rotation=45)
            plt.ylim(0, 1)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            
            # 保存或显示图表
            if output_path:
                plt.savefig(output_path)
                plt.close()
                return output_path
            else:
                plt.show()
                return None
                
        except ImportError:
            logger.warning("缺少matplotlib库，无法创建可视化图表")
            return None
        except Exception as e:
            logger.error(f"创建情感曲线可视化图表时出错: {e}")
            return None

    def suggest_transition_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """建议在情感跳跃点之间添加过渡场景
        
        分析情感跳跃点，提供添加过渡场景的建议
        
        Args:
            scenes: 场景列表
            
        Returns:
            过渡场景建议列表
        """
        # 先检查情感流，确保已识别转变点
        if not self.transition_points and len(scenes) >= 2:
            self.check_emotion_flow(scenes)
        
        transition_suggestions = []
        
        for point in self.transition_points:
            pos = point["position"]
            if pos >= len(scenes) or pos < 1:
                continue
                
            prev_scene = scenes[pos-1]
            current_scene = scenes[pos]
            
            prev_score = prev_scene.get("emotion_score", 0.5)
            current_score = current_scene.get("emotion_score", 0.5)
            
            # 计算中间过渡值
            mid_score = (prev_score + current_score) / 2
            
            # 获取情感类型（如果有）
            prev_emotion = prev_scene.get("emotion_type", "neutral")
            current_emotion = current_scene.get("emotion_type", "neutral")
            
            suggestion = {
                "type": "add_transition",
                "position": pos,
                "between_scenes": [prev_scene["id"], current_scene["id"]],
                "target_emotion_score": mid_score,
                "message": f"在场景{prev_scene['id']}和{current_scene['id']}之间添加过渡场景"
            }
            
            # 根据不同类型的情感跳跃提供具体建议
            prev_emotion_cat = EmotionCategory.from_string(prev_emotion)
            current_emotion_cat = EmotionCategory.from_string(current_emotion)
            
            if current_emotion_cat in self.EMOTION_CONFLICT_MATRIX.get(prev_emotion_cat, []):
                # 情感类型有冲突，提供特定过渡建议
                suggestion["conflict_type"] = "emotion_category_conflict"
                suggestion["details"] = f"从{prev_emotion_cat.name}到{current_emotion_cat.name}的转变需要过渡"
                
                # 根据情感类型提供具体过渡建议
                transition_advice = self._get_transition_advice(prev_emotion_cat, current_emotion_cat)
                if transition_advice:
                    suggestion["transition_advice"] = transition_advice
            else:
                # 纯粹的情感强度跳跃
                suggestion["conflict_type"] = "emotion_intensity_jump"
                suggestion["details"] = f"情感强度从{prev_score}到{current_score}的跳跃过大"
            
            transition_suggestions.append(suggestion)
        
        return transition_suggestions
    
    def _get_transition_advice(
        self, 
        from_emotion: EmotionCategory, 
        to_emotion: EmotionCategory
    ) -> Dict[str, Any]:
        """根据情感类型转变提供过渡建议
        
        Args:
            from_emotion: 起始情感类型
            to_emotion: 目标情感类型
            
        Returns:
            过渡建议信息
        """
        # 情感过渡建议映射
        transition_map = {
            (EmotionCategory.HAPPINESS, EmotionCategory.SADNESS): {
                "description": "从快乐到悲伤的转变",
                "suggestion": "添加一个逐渐认识到问题/困难的场景，角色从乐观转向思考",
                "elements": ["回忆", "消息", "意识到问题", "沉思"]
            },
            (EmotionCategory.SADNESS, EmotionCategory.HAPPINESS): {
                "description": "从悲伤到快乐的转变",
                "suggestion": "添加一个希望出现的转折点，角色发现新的可能性",
                "elements": ["希望", "支持", "解决方案", "新视角"]
            },
            (EmotionCategory.ANGER, EmotionCategory.HAPPINESS): {
                "description": "从愤怒到快乐的转变",
                "suggestion": "添加一个释放或解决场景，角色消除愤怒源头",
                "elements": ["倾诉", "理解", "道歉", "和解"]
            },
            (EmotionCategory.FEAR, EmotionCategory.TRUST): {
                "description": "从恐惧到信任的转变",
                "suggestion": "添加一个安全感建立场景，角色获得保护或支持",
                "elements": ["帮助", "保护", "解释", "证明"]
            }
        }
        
        # 尝试获取具体建议
        key = (from_emotion, to_emotion)
        if key in transition_map:
            return transition_map[key]
        
        # 如果没有具体建议，提供通用建议
        return {
            "description": f"从{from_emotion.name}到{to_emotion.name}的转变",
            "suggestion": "添加情感过渡场景，避免情感突变",
            "elements": ["中间状态", "渐变", "情感触发", "反思"]
        }
    
    def check_emotion_balance(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查整体情感平衡性
        
        分析视频情感分布是否平衡，是否缺少某些情感类型
        
        Args:
            scenes: 场景列表
            
        Returns:
            情感平衡分析结果
        """
        if not scenes:
            return {"balanced": True, "message": "没有场景可分析"}
        
        # 统计各类情感出现次数
        emotion_counts = {}
        for scene in scenes:
            emotion_type = scene.get("emotion_type", "neutral").lower()
            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
        
        # 计算情感占比
        total_scenes = len(scenes)
        emotion_percentages = {
            emotion: count / total_scenes
            for emotion, count in emotion_counts.items()
        }
        
        # 分析结果
        result = {
            "emotion_counts": emotion_counts,
            "emotion_percentages": emotion_percentages,
            "total_scenes": total_scenes
        }
        
        # 检查是否某种情感过度主导（超过60%）
        dominant_emotions = [
            emotion for emotion, percentage in emotion_percentages.items()
            if percentage > 0.6
        ]
        
        if dominant_emotions:
            result["balanced"] = False
            result["dominant_emotions"] = dominant_emotions
            result["message"] = f"情感分布不平衡，以下情感过度主导: {', '.join(dominant_emotions)}"
            result["suggestion"] = "建议添加更多元化的情感，丰富视频情感体验"
        else:
            result["balanced"] = True
            result["message"] = "情感分布较为平衡"
        
        # 检查情感多样性
        if len(emotion_counts) <= 2 and total_scenes > 5:
            result["balanced"] = False
            result["issue"] = "情感多样性不足"
            result["message"] = f"仅包含{len(emotion_counts)}种情感类型，建议增加情感变化"
            
            # 建议可以添加的情感
            all_basic_emotions = {"happiness", "sadness", "anger", "fear", "surprise", "disgust"}
            missing_emotions = all_basic_emotions - set(emotion_counts.keys())
            if missing_emotions:
                result["missing_emotions"] = list(missing_emotions)
                result["suggestion"] = f"建议考虑添加以下情感: {', '.join(missing_emotions)}"
        
        return result

    def get_best_emotion_patterns(self, scenes: List[Dict[str, Any]], genre: str = None) -> Dict[str, Any]:
        """根据视频类型推荐最佳情感模式
        
        为不同类型的视频提供推荐的情感曲线模式
        
        Args:
            scenes: 场景列表
            genre: 视频类型（如"喜剧", "恐怖", "剧情"等）
            
        Returns:
            推荐的情感模式
        """
        # 各视频类型的典型情感模式
        genre_patterns = {
            "喜剧": ["wave", "rising"],
            "恐怖": ["rising", "mountain"],
            "动作": ["mountain", "wave"],
            "剧情": ["valley", "mountain"],
            "爱情": ["valley", "rising"],
            "悬疑": ["rising", "mountain"],
            "科幻": ["wave", "mountain"],
            "纪录片": ["rising", "wave"]
        }
        
        result = {"current_rhythm": None, "recommendations": []}
        
        # 分析当前情感曲线最接近哪种模式
        if scenes and len(scenes) >= 2:
            emotion_scores = [scene.get("emotion_score", 0.5) for scene in scenes]
            current_rhythm = self._select_best_rhythm(emotion_scores)
            result["current_rhythm"] = current_rhythm
            
            # 为当前模式计算匹配度
            rhythm_pattern = self.emotion_rhythms.get(current_rhythm)
            if rhythm_pattern:
                adjusted_pattern = self._adjust_rhythm_length(rhythm_pattern, len(emotion_scores))
                similarity = self._calculate_similarity(emotion_scores, adjusted_pattern)
                result["current_similarity"] = similarity
        
        # 根据视频类型提供推荐
        if genre and genre in genre_patterns:
            result["recommendations"] = genre_patterns[genre]
            result["genre"] = genre
            result["message"] = f"{genre}类型视频通常适合以下情感节奏: {', '.join(genre_patterns[genre])}"
        else:
            # 如果未指定类型，推荐通用的情感模式
            result["recommendations"] = ["wave", "mountain", "rising"]
            result["message"] = "通用推荐的情感节奏模式"
        
        return result


def validate_emotion_continuity(
    scenes: List[Dict[str, Any]], 
    max_jump: float = None,
    target_rhythm: str = None,
    visualize: bool = False,
    output_path: str = None
) -> Dict[str, Any]:
    """
    便捷函数：验证情感连贯性
    
    Args:
        scenes: 场景列表，每个场景需包含emotion_score字段
        max_jump: 最大允许情感跳跃度，默认为系统预设值
        target_rhythm: 目标情感节奏模式，如"mountain", "valley"等
        visualize: 是否生成可视化图表
        output_path: 可视化图表输出路径
        
    Returns:
        验证结果和建议
    """
    monitor = EmotionTransitionMonitor(max_jump=max_jump)
    
    # 检查情感流
    emotion_jumps = monitor.check_emotion_flow(scenes)
    
    # 分析情感冲突
    emotion_conflicts = monitor.analyze_emotion_conflicts(scenes)
    
    # 评估情感节奏
    rhythm_analysis = monitor.evaluate_rhythm_alignment(scenes, target_rhythm)
    
    # 生成过渡场景建议
    transition_suggestions = monitor.suggest_transition_scenes(scenes)
    
    # 检查情感平衡性
    balance_analysis = monitor.check_emotion_balance(scenes)
    
    # 可视化（如果需要）
    visualization_path = None
    if visualize:
        visualization_path = monitor.visualize_emotion_curve(
            scenes, target_rhythm, output_path
        )
    
    # 生成综合结果
    result = {
        "issues_detected": len(emotion_jumps) + len(emotion_conflicts) > 0,
        "emotion_jumps": emotion_jumps,
        "emotion_conflicts": emotion_conflicts,
        "rhythm_analysis": rhythm_analysis,
        "transition_suggestions": transition_suggestions,
        "emotion_balance": balance_analysis
    }
    
    if visualization_path:
        result["visualization_path"] = visualization_path
    
    return result 