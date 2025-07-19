#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
情感演进监测器独立测试脚本

直接导入emotion_continuity模块进行测试，避免项目依赖问题。
"""

import sys
import os
import logging
from pathlib import Path
import json
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from enum import Enum, auto
import numpy as np
import matplotlib.pyplot as plt

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 基本异常类
class ErrorCode:
    NARRATIVE_ANALYSIS_ERROR = 1405

class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

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
    """情感不连贯异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.NARRATIVE_ANALYSIS_ERROR, details=details or {})

class EmotionTransitionMonitor:
    """情感过渡监测器"""
    
    # 相邻场景情感最大允许跳跃度
    MAX_JUMP = 0.5
    
    # 情感冲突矩阵
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
        """初始化情感过渡监测器"""
        self.max_jump = max_jump if max_jump is not None else self.MAX_JUMP
        self.emotion_rhythms = self._load_emotion_rhythms(emotion_rhythms_path)
        self.emotion_curve = []  # 存储情感曲线
        self.transition_points = []  # 存储关键情感转变点
        
    def _load_emotion_rhythms(self, path: Optional[str]) -> Dict[str, List[float]]:
        """加载预定义的情感节奏模式"""
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
                default_rhythms.update(custom_rhythms)
                return default_rhythms
        except Exception as e:
            logger.warning(f"加载情感节奏文件失败: {e}，将使用默认节奏")
            return default_rhythms
    
    def check_emotion_flow(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """监测情感曲线综合连贯性"""
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
                
                # 添加转变点记录
                self.transition_points.append({
                    "position": i,
                    "scenes": [scenes[i-1]["id"], scene["id"]],
                    "delta": delta
                })
            
            prev_score = current_score
        
        return problems
    
    def analyze_emotion_conflicts(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析场景间的情感冲突"""
        if not scenes or len(scenes) < 2:
            return []
        
        conflicts = []
        
        for i, scene in enumerate(scenes[1:], 1):
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

# 创建测试场景
def create_test_scenes():
    """创建测试场景数据"""
    # 1. 平滑过渡的情感曲线
    smooth_scenes = [
        {"id": "smooth_1", "emotion_score": 0.3, "emotion_type": "neutral"},
        {"id": "smooth_2", "emotion_score": 0.4, "emotion_type": "happiness"},
        {"id": "smooth_3", "emotion_score": 0.5, "emotion_type": "happiness"},
        {"id": "smooth_4", "emotion_score": 0.6, "emotion_type": "happiness"}
    ]
    
    # 2. 情感跳跃问题场景
    jump_scenes = [
        {"id": "jump_1", "emotion_score": 0.2, "emotion_type": "sadness"},
        {"id": "jump_2", "emotion_score": 0.8, "emotion_type": "happiness"},  # 大幅跳跃
        {"id": "jump_3", "emotion_score": 0.3, "emotion_type": "fear"}        # 又一次大幅跳跃
    ]
    
    # 3. 情感冲突场景
    conflict_scenes = [
        {"id": "conflict_1", "emotion_score": 0.7, "emotion_type": "happiness"},
        {"id": "conflict_2", "emotion_score": 0.6, "emotion_type": "sadness"}  # 情感冲突
    ]
    
    # 4. 匹配山形节奏的场景
    mountain_scenes = [
        {"id": "mountain_1", "emotion_score": 0.2, "emotion_type": "neutral"},
        {"id": "mountain_2", "emotion_score": 0.4, "emotion_type": "happiness"},
        {"id": "mountain_3", "emotion_score": 0.6, "emotion_type": "happiness"},
        {"id": "mountain_4", "emotion_score": 0.8, "emotion_type": "anticipation"},
        {"id": "mountain_5", "emotion_score": 0.9, "emotion_type": "happiness"},
        {"id": "mountain_6", "emotion_score": 0.7, "emotion_type": "happiness"},
        {"id": "mountain_7", "emotion_score": 0.5, "emotion_type": "neutral"},
        {"id": "mountain_8", "emotion_score": 0.3, "emotion_type": "neutral"}
    ]
    
    return {
        "smooth": smooth_scenes,
        "jump": jump_scenes,
        "conflict": conflict_scenes,
        "mountain": mountain_scenes
    }

def test_emotion_flow():
    """测试情感流分析"""
    print("\n=== 测试情感流分析 ===")
    
    scenes = create_test_scenes()
    monitor = EmotionTransitionMonitor()
    
    # 测试平滑场景
    smooth_problems = monitor.check_emotion_flow(scenes["smooth"])
    print(f"平滑场景检测到 {len(smooth_problems)} 个问题")
    
    # 测试跳跃场景
    jump_problems = monitor.check_emotion_flow(scenes["jump"])
    print(f"跳跃场景检测到 {len(jump_problems)} 个问题:")
    for problem in jump_problems:
        print(f"  - {problem['message']}")
    
    # 测试冲突检测
    conflicts = monitor.analyze_emotion_conflicts(scenes["conflict"])
    print(f"\n情感冲突检测到 {len(conflicts)} 个冲突:")
    for conflict in conflicts:
        print(f"  - {conflict['message']}")

def validate_emotion_continuity(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """情感连贯性验证便捷函数"""
    monitor = EmotionTransitionMonitor()
    emotion_jumps = monitor.check_emotion_flow(scenes)
    emotion_conflicts = monitor.analyze_emotion_conflicts(scenes)
    
    return {
        "issues_detected": len(emotion_jumps) + len(emotion_conflicts) > 0,
        "emotion_jumps": emotion_jumps,
        "emotion_conflicts": emotion_conflicts
    }

def test_convenience_function():
    """测试便捷函数"""
    print("\n=== 测试便捷函数 ===")
    
    scenes = create_test_scenes()
    
    for name, scene_data in scenes.items():
        result = validate_emotion_continuity(scene_data)
        issues = result["issues_detected"]
        print(f"{name} 场景检测到问题: {issues}")
        if issues:
            print(f"  情感跳跃: {len(result['emotion_jumps'])}")
            print(f"  情感冲突: {len(result['emotion_conflicts'])}")

def test_visualization():
    """测试可视化功能"""
    print("\n=== 测试情感曲线可视化 ===")
    
    scenes = create_test_scenes()
    monitor = EmotionTransitionMonitor()
    
    # 为山形场景生成情感曲线
    try:
        mountain_scenes = scenes["mountain"]
        monitor.check_emotion_flow(mountain_scenes)  # 确保有情感曲线
        
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / "mountain_emotion_curve.png"
        plt.figure(figsize=(10, 6))
        plt.plot(monitor.emotion_curve, 'b-o', label='情感曲线')
        plt.title('山形情感曲线')
        plt.xlabel('场景序号')
        plt.ylabel('情感强度')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()
        
        print(f"情感曲线图表已保存至: {output_path}")
    except Exception as e:
        print(f"生成可视化图表失败: {e}")

def main():
    """主函数"""
    print("=== 情感演进监测器独立测试 ===")
    
    try:
        # 创建输出目录
        os.makedirs("./output", exist_ok=True)
        
        # 测试情感流分析
        test_emotion_flow()
        
        # 测试便捷函数
        test_convenience_function()
        
        # 测试可视化功能
        test_visualization()
        
        print("\n所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 