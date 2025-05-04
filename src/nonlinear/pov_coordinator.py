"""
视角切换协调器

负责管理多视角叙事中的视角切换和转场效果
用于协调不同角色视角之间的转换，使剧情流畅连贯
"""

import logging
import random
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.utils.validators import validate_float_range

# 创建日志记录器
logger = logging.getLogger("pov_coordinator")

class TransitionType(Enum):
    """转场类型枚举"""
    CUT = "cut"                   # 直接切换，无过渡效果
    MIRROR_SHOT = "mirror_shot"    # 镜像画面（对话切换）
    EMPTY_SCENE = "empty_scene"    # 空景转场（场景切换）
    ACTION_MATCH = "action_match"  # 动作匹配转场（动作连贯）
    DIALOG_OVERLAP = "dialog_overlap"  # 对话重叠转场
    ABSTRACT = "abstract"          # 抽象转场（表意性）


class POVManager:
    """视角管理器，处理不同角色视角的切换和转场"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化视角管理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 初始化转场类型配置
        self.transition_configs = {
            TransitionType.CUT: {
                "description": "直接切换，无过渡效果",
                "duration": 0.0,  # 无持续时间
                "suitable_contexts": ["快节奏", "动作", "高压力场景"],
                "weight": 1.0
            },
            TransitionType.MIRROR_SHOT: {
                "description": "镜像画面，通常用于对话切换",
                "duration": 0.5,  # 短持续时间
                "suitable_contexts": ["对话", "人物互动", "两人场景"],
                "weight": 0.8
            },
            TransitionType.EMPTY_SCENE: {
                "description": "通过空镜头实现场景转换",
                "duration": 1.0,  # 中等持续时间
                "suitable_contexts": ["场景变换", "时间流逝", "情绪转变"],
                "weight": 0.6
            },
            TransitionType.ACTION_MATCH: {
                "description": "动作匹配转场，保持动作连贯性",
                "duration": 0.3,  # 较短持续时间
                "suitable_contexts": ["连续动作", "动作戏", "追踪镜头"],
                "weight": 0.7
            },
            TransitionType.DIALOG_OVERLAP: {
                "description": "对话重叠转场，声音先于画面切换",
                "duration": 0.7,  # 中等持续时间
                "suitable_contexts": ["情感对话", "角色反应", "心理活动"],
                "weight": 0.5
            },
            TransitionType.ABSTRACT: {
                "description": "抽象表意转场，用于隐喻或情感表达",
                "duration": 1.2,  # 较长持续时间
                "suitable_contexts": ["心理变化", "情感高潮", "梦境/幻觉"],
                "weight": 0.4
            }
        }
        
        # 加载配置（如果提供了配置文件）
        self.config = self._load_config(config_path)
        
        # 上次使用的视角和转场类型
        self.last_pov = None
        self.last_transition_type = None
        
        logger.info("视角切换协调器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        # 默认配置
        config = {
            "min_pov_duration": 2.0,       # 最短视角持续时间（秒）
            "max_consecutive_same_transitions": 2,  # 同类型转场最大连续次数
            "character_pov_weight": 1.2,    # 主要角色视角权重
            "environment_pov_weight": 0.7,  # 环境视角权重
            "transition_variety": 0.7,      # 转场多样性（0-1）
            "allow_adaptive_transitions": True  # 允许根据内容自适应转场
        }
        
        # TODO: 如果指定了配置文件路径，加载自定义配置
        
        return config
        
    def manage_transitions(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        管理多视角切换的视觉线索
        
        Args:
            scenes: 场景列表
            
        Returns:
            更新后的场景列表，添加了转场信息
        """
        if not scenes or len(scenes) < 2:
            return scenes
        
        # 创建场景副本以避免修改原始数据
        updated_scenes = scenes.copy()
        
        # 遍历场景，识别视角变化并添加转场
        for i in range(1, len(updated_scenes)):
            prev_pov = updated_scenes[i-1].get("pov_character", None)
            curr_pov = updated_scenes[i].get("pov_character", None)
            
            # 如果视角发生变化，添加适当的转场效果
            if prev_pov != curr_pov:
                transition_type, transition_info = self._generate_transition_shots(
                    prev_pov, curr_pov, 
                    prev_scene=updated_scenes[i-1], 
                    curr_scene=updated_scenes[i]
                )
                
                # 添加转场信息到当前场景
                updated_scenes[i]["transition"] = transition_info
                updated_scenes[i]["transition_type"] = transition_type.value
        
        # 更新上次处理的视角
        if updated_scenes:
            self.last_pov = updated_scenes[-1].get("pov_character", None)
        
        return updated_scenes
    
    def _generate_transition_shots(self, 
                                  prev_pov: Optional[str], 
                                  curr_pov: Optional[str],
                                  prev_scene: Dict[str, Any] = None,
                                  curr_scene: Dict[str, Any] = None) -> Tuple[TransitionType, Dict[str, Any]]:
        """
        生成适合的转场画面
        
        Args:
            prev_pov: 前一个视角的角色
            curr_pov: 当前视角的角色
            prev_scene: 前一个场景信息
            curr_scene: 当前场景信息
            
        Returns:
            转场类型和转场信息
        """
        # 默认转场信息
        transition_info = {
            "duration": 0.0,
            "description": "",
            "effect": "cut"
        }
        
        # 分析场景上下文
        context = self._analyze_transition_context(prev_scene, curr_scene)
        
        # 根据上下文选择合适的转场类型
        transition_type = self._select_transition_type(prev_pov, curr_pov, context)
        
        # 避免频繁使用相同转场类型
        if transition_type == self.last_transition_type:
            # 每个转场类型的连续使用次数有限
            consecutive_count = context.get("consecutive_same_transition", 0)
            if consecutive_count >= self.config["max_consecutive_same_transitions"]:
                # 强制使用不同类型
                available_types = [t for t in TransitionType if t != transition_type]
                transition_type = random.choice(available_types)
        
        # 获取转场配置
        transition_config = self.transition_configs[transition_type]
        
        # 创建转场信息
        transition_info = {
            "type": transition_type.value,
            "duration": transition_config["duration"],
            "description": transition_config["description"],
            "effect": self._get_visual_effect_for_transition(transition_type)
        }
        
        # 特殊转场处理
        if transition_type == TransitionType.DIALOG_OVERLAP:
            # 对话重叠需要添加音频信息
            transition_info["audio_overlap"] = True
            transition_info["audio_lead_time"] = 0.3  # 声音提前0.3秒
        
        # 记录本次使用的转场类型
        self.last_transition_type = transition_type
        
        return transition_type, transition_info
    
    def _analyze_transition_context(self, 
                                   prev_scene: Optional[Dict[str, Any]], 
                                   curr_scene: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析转场上下文
        
        Args:
            prev_scene: 前一个场景
            curr_scene: 当前场景
            
        Returns:
            上下文信息
        """
        context = {
            "consecutive_same_transition": 0,
            "scene_types": [],
            "emotion_change": 0.0,
            "has_dialog": False,
            "action_continuity": False,
            "location_change": False
        }
        
        # 如果没有场景信息，返回基本上下文
        if not prev_scene or not curr_scene:
            return context
        
        # 检查场景类型
        if "scene_type" in prev_scene:
            context["scene_types"].append(prev_scene["scene_type"])
        if "scene_type" in curr_scene:
            context["scene_types"].append(curr_scene["scene_type"])
        
        # 检查情感变化
        prev_emotion = prev_scene.get("emotion_score", 0.0)
        curr_emotion = curr_scene.get("emotion_score", 0.0)
        if isinstance(prev_emotion, (int, float)) and isinstance(curr_emotion, (int, float)):
            context["emotion_change"] = abs(curr_emotion - prev_emotion)
        
        # 检查是否有对话
        prev_dialog = "dialog" in prev_scene or prev_scene.get("has_dialog", False)
        curr_dialog = "dialog" in curr_scene or curr_scene.get("has_dialog", False)
        context["has_dialog"] = prev_dialog or curr_dialog
        
        # 检查位置变化
        prev_location = prev_scene.get("location", "")
        curr_location = curr_scene.get("location", "")
        context["location_change"] = prev_location != curr_location and prev_location and curr_location
        
        # 检查动作连续性
        if "action" in prev_scene and "action" in curr_scene:
            # 这里可以添加更复杂的动作连续性分析
            # 简单实现：检查动作描述是否包含相似词汇
            prev_action = prev_scene["action"].lower() if isinstance(prev_scene["action"], str) else ""
            curr_action = curr_scene["action"].lower() if isinstance(curr_scene["action"], str) else ""
            
            # 如果有公共词汇，认为有动作连续性
            prev_words = set(prev_action.split())
            curr_words = set(curr_action.split())
            common_words = prev_words.intersection(curr_words)
            
            context["action_continuity"] = len(common_words) > 0
        
        # 检查转场连续性
        if self.last_transition_type:
            context["consecutive_same_transition"] = 1
            
            # 这里可以添加更详细的转场历史跟踪
            # 简单实现：仅跟踪上一次转场
        
        return context
    
    def _select_transition_type(self, 
                               prev_pov: Optional[str], 
                               curr_pov: Optional[str],
                               context: Dict[str, Any]) -> TransitionType:
        """
        选择合适的转场类型
        
        Args:
            prev_pov: 前一个视角角色
            curr_pov: 当前视角角色
            context: 上下文信息
            
        Returns:
            转场类型
        """
        # 分配各种转场类型的权重
        weights = {}
        for t_type in TransitionType:
            # 基础权重
            weights[t_type] = self.transition_configs[t_type]["weight"]
            
            # 根据上下文调整权重
            if t_type == TransitionType.MIRROR_SHOT and context["has_dialog"]:
                weights[t_type] *= 1.5  # 对话场景增加镜像画面权重
                
            if t_type == TransitionType.EMPTY_SCENE and context["location_change"]:
                weights[t_type] *= 1.8  # 位置变化增加空景转场权重
                
            if t_type == TransitionType.ACTION_MATCH and context["action_continuity"]:
                weights[t_type] *= 2.0  # 动作连续时增加动作匹配转场权重
                
            if t_type == TransitionType.DIALOG_OVERLAP and context["has_dialog"]:
                weights[t_type] *= 1.6  # 对话场景增加对话重叠转场权重
                
            if t_type == TransitionType.ABSTRACT and context["emotion_change"] > 0.6:
                weights[t_type] *= 1.7  # 情感变化大时增加抽象转场权重
                
            # 如果是连续转场，降低权重
            if t_type == self.last_transition_type:
                weights[t_type] *= 0.5
        
        # 避免全部权重为0
        if sum(weights.values()) <= 0:
            return TransitionType.CUT  # 默认使用直切
        
        # 权重随机选择
        transition_types = list(weights.keys())
        transition_weights = [weights[t] for t in transition_types]
        
        # 标准化权重
        total_weight = sum(transition_weights)
        if total_weight > 0:
            transition_weights = [w/total_weight for w in transition_weights]
        else:
            # 如果所有权重都是0，使用均等概率
            transition_weights = [1.0/len(transition_types)] * len(transition_types)
        
        # 随机选择
        return random.choices(transition_types, weights=transition_weights, k=1)[0]
    
    def _get_visual_effect_for_transition(self, transition_type: TransitionType) -> str:
        """
        获取转场类型对应的视觉效果
        
        Args:
            transition_type: 转场类型
            
        Returns:
            视觉效果描述
        """
        # 转场效果映射
        effects = {
            TransitionType.CUT: "cut",
            TransitionType.MIRROR_SHOT: "mirror",
            TransitionType.EMPTY_SCENE: "fade",
            TransitionType.ACTION_MATCH: "match_cut",
            TransitionType.DIALOG_OVERLAP: "j_cut",  # J型剪辑（声音先于画面）
            TransitionType.ABSTRACT: "dissolve"
        }
        
        return effects.get(transition_type, "cut")
    
    def analyze_pov_distribution(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析场景中视角分布情况
        
        Args:
            scenes: 场景列表
            
        Returns:
            视角分布分析
        """
        if not scenes:
            return {
                "total_povs": 0,
                "pov_distribution": {},
                "avg_pov_duration": 0,
                "pov_switches": 0
            }
        
        # 统计视角
        pov_distribution = {}
        current_pov = None
        pov_switches = 0
        pov_durations = {}
        
        for scene in scenes:
            pov = scene.get("pov_character", "unknown")
            
            # 统计视角分布
            if pov not in pov_distribution:
                pov_distribution[pov] = 0
                pov_durations[pov] = []
            
            # 增加计数
            pov_distribution[pov] += 1
            
            # 计算持续时间
            if "duration" in scene:
                pov_durations[pov].append(scene["duration"])
            
            # 检测视角切换
            if current_pov is not None and current_pov != pov:
                pov_switches += 1
            
            current_pov = pov
        
        # 计算平均视角持续时间
        avg_durations = {}
        for pov, durations in pov_durations.items():
            if durations:
                avg_durations[pov] = sum(durations) / len(durations)
        
        # 总平均持续时间
        all_durations = [d for duration_list in pov_durations.values() for d in duration_list]
        avg_pov_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        
        return {
            "total_povs": len(pov_distribution),
            "pov_distribution": pov_distribution,
            "avg_pov_duration": avg_pov_duration,
            "pov_switches": pov_switches,
            "pov_avg_durations": avg_durations
        }


# 提供便捷函数
def manage_pov_transitions(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    管理场景中的POV转场的便捷函数
    
    Args:
        scenes: 场景列表
        
    Returns:
        更新后的场景列表，添加了转场信息
    """
    manager = POVManager()
    return manager.manage_transitions(scenes)


def get_transition_types() -> List[str]:
    """
    获取所有可用的转场类型
    
    Returns:
        转场类型列表
    """
    return [t.value for t in TransitionType] 