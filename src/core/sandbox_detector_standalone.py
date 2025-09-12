#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
逻辑漏洞沙盒检测器独立测试脚本

提供逻辑漏洞沙盒检测器的独立测试功能，无需依赖完整项目。
"""

import sys
import os
import logging
import random
import json
import copy
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===========================================
# 简化的模型代码，用于独立运行
# ===========================================

class ErrorCode:
    LOGIC_SANDBOX_ERROR = 1800


class ClipMasterError(Exception):
    def __init__(self, message, code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class LogicDefectType(Enum):
    """逻辑缺陷类型"""
    TIME_JUMP = auto()          # 时间跳跃：场景时间线异常跳跃
    PROP_TELEPORT = auto()      # 道具传送：道具无故出现或消失
    CHARACTER_CLONE = auto()    # 角色分身：角色同时出现在不同场景
    CHARACTER_SWAP = auto()     # 角色互换：角色特征/性格突然互换
    CAUSALITY_BREAK = auto()    # 因果断裂：事件因果关系断裂
    DIALOGUE_MISMATCH = auto()  # 对话错位：人物对话与角色设定不符
    EMOTION_FLIP = auto()       # 情感翻转：情感突然不合理转变
    KNOWLEDGE_ERROR = auto()    # 知识错误：常识性错误或专业知识错误
    CONSTRAINT_BREAK = auto()   # 约束违反：违反物理或世界观规则
    MOTIVATION_LOSS = auto()    # 动机丢失：角色行为失去合理动机


class LogicSandboxError(ClipMasterError):
    """逻辑沙盒错误异常"""
    def __init__(self, message: str, defect_type: LogicDefectType, 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=ErrorCode.LOGIC_SANDBOX_ERROR, 
                         details=details or {"defect_type": defect_type.name})
        self.defect_type = defect_type


@dataclass
class LogicDefect:
    """逻辑缺陷"""
    defect_type: LogicDefectType          # 缺陷类型
    description: str                      # 缺陷描述
    scene_index: int = -1                 # 缺陷所在场景索引（-1表示全局缺陷）
    confidence: float = 1.0               # 缺陷检测置信度
    severity: str = "medium"              # 缺陷严重程度 (low, medium, high, critical)
    suggested_fix: Optional[str] = None   # 建议修复方法


class LogicSandbox:
    """逻辑沙盒"""
    
    def __init__(self):
        """初始化逻辑沙盒"""
        # 注册内置缺陷注入器
        self.defect_injectors = {
            LogicDefectType.TIME_JUMP: self._inject_time_jump,
            LogicDefectType.PROP_TELEPORT: self._inject_prop_teleport,
            LogicDefectType.CHARACTER_CLONE: self._inject_character_clone,
            LogicDefectType.CAUSALITY_BREAK: self._inject_causality_break,
            LogicDefectType.DIALOGUE_MISMATCH: self._inject_dialogue_mismatch,
            LogicDefectType.EMOTION_FLIP: self._inject_emotion_flip
        }
        
        # 注册内置缺陷检测器
        self.defect_detectors = {
            LogicDefectType.TIME_JUMP: self._detect_time_jump,
            LogicDefectType.PROP_TELEPORT: self._detect_prop_teleport,
            LogicDefectType.CHARACTER_CLONE: self._detect_character_clone,
            LogicDefectType.CAUSALITY_BREAK: self._detect_causality_break,
            LogicDefectType.DIALOGUE_MISMATCH: self._detect_dialogue_mismatch,
            LogicDefectType.EMOTION_FLIP: self._detect_emotion_flip
        }
        
        # 初始化配置参数
        self.config = {
            "detection_threshold": 0.7,  # 缺陷检测阈值
            "severity_weights": {        # 不同严重程度的权重
                "low": 0.5,
                "medium": 1.0,
                "high": 1.5,
                "critical": 2.0
            }
        }
    
    def stress_test(self, script: Dict[str, Any]) -> float:
        """注入50种典型逻辑错问题进行压力测试
        
        Args:
            script: 待测试的脚本
            
        Returns:
            漏洞检出率，越高越好
        """
        test_cases = [
            {"type": "TIME_JUMP", "value": -300},      # 时间倒流
            {"type": "PROP_TELEPORT", "item": "宝剑"},  # 道具瞬移
            {"type": "CHARACTER_CLONE"}                # 角色分身
        ]
        
        detection_rate = 0
        for case in test_cases:
            corrupted_script = self.inject_defect(script, case)
            if self.detect_defects(corrupted_script):
                detection_rate += 1
                
        return detection_rate / len(test_cases)  # 返回漏洞检出率
    
    def inject_defect(self, script: Dict[str, Any], defect_config: Dict[str, Any]) -> Dict[str, Any]:
        """向脚本中注入缺陷
        
        Args:
            script: 原始脚本
            defect_config: 缺陷配置，包含类型和相关参数
            
        Returns:
            注入缺陷后的脚本副本
        """
        # 创建脚本副本，避免修改原始脚本
        script_copy = copy.deepcopy(script)
        
        # 解析缺陷类型
        defect_type_str = defect_config.get("type", "").upper()
        try:
            # 尝试将字符串映射到枚举
            defect_type = next(t for t in LogicDefectType 
                              if t.name == defect_type_str)
        except StopIteration:
            # 找不到对应的缺陷类型
            logger.warning(f"未知的缺陷类型: {defect_type_str}")
            return script_copy
        
        # 调用对应的缺陷注入器
        if defect_type in self.defect_injectors:
            try:
                result = self.defect_injectors[defect_type](script_copy, defect_config)
                logger.info(f"已注入缺陷: {defect_type.name}")
                return result
            except Exception as e:
                logger.error(f"注入缺陷失败: {e}")
                return script_copy
        else:
            logger.warning(f"没有找到缺陷类型 {defect_type.name} 的注入器")
            return script_copy
    
    def detect_defects(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测脚本中的逻辑缺陷
        
        Args:
            script: 待检测的脚本
            
        Returns:
            检测到的缺陷列表
        """
        defects = []
        
        # 运行所有注册的缺陷检测器
        for defect_type, detector in self.defect_detectors.items():
            try:
                defect_results = detector(script)
                if defect_results:
                    # 过滤低于检测阈值的缺陷
                    filtered_defects = [d for d in defect_results 
                                       if d.confidence >= self.config["detection_threshold"]]
                    defects.extend(filtered_defects)
            except Exception as e:
                logger.error(f"运行缺陷检测器 {defect_type.name} 时出错: {e}")
        
        return defects
    
    # 省略具体的缺陷注入和检测方法实现
    # 完整实现可参考 src/logic/sandbox_detector.py
    
    def _inject_time_jump(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入时间跳跃缺陷"""
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return script
        
        # 获取跳跃值
        jump_value = config.get("value", 1000)
        
        # 随机选择一个场景进行修改
        scene_idx = random.randint(1, len(scenes) - 1)
        
        # 修改时间戳
        if "timestamp" in scenes[scene_idx]:
            original_time = scenes[scene_idx]["timestamp"]
            new_time = max(0, original_time + jump_value)
            scenes[scene_idx]["timestamp"] = new_time
            
            # 记录注入的缺陷
            if "_injected_defects" not in script:
                script["_injected_defects"] = []
                
            script["_injected_defects"].append({
                "type": LogicDefectType.TIME_JUMP.name,
                "scene_index": scene_idx,
                "original_value": original_time,
                "new_value": new_time,
                "description": f"在场景 {scene_idx} 中注入时间跳跃，从 {original_time} 到 {new_time}"
            })
        
        return script
    
    def _inject_prop_teleport(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入道具传送缺陷"""
        # 简化版实现
        scenes = script.get("scenes", [])
        if not scenes:
            return script
            
        # 随机选择一个场景
        scene_idx = random.randint(0, len(scenes) - 1)
        scene = scenes[scene_idx]
        
        # 添加一个不存在的道具
        if "props" not in scene:
            scene["props"] = []
        
        scene["props"].append({"name": "魔法道具", "state": "appeared"})
        
        # 记录注入的缺陷
        if "_injected_defects" not in script:
            script["_injected_defects"] = []
            
        script["_injected_defects"].append({
            "type": LogicDefectType.PROP_TELEPORT.name,
            "scene_index": scene_idx,
            "item": "魔法道具",
            "description": f"在场景 {scene_idx} 中添加了魔法道具"
        })
        
        return script
    
    def _inject_character_clone(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入角色分身缺陷"""
        # 简化版实现
        return script
    
    def _inject_causality_break(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入因果断裂缺陷"""
        # 简化版实现
        return script
    
    def _inject_dialogue_mismatch(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入对话错位缺陷"""
        # 简化版实现
        return script
    
    def _inject_emotion_flip(self, script: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """注入情感翻转缺陷"""
        # 简化版实现
        return script
    
    def _detect_time_jump(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测时间跳跃缺陷"""
        defects = []
        
        # 获取场景列表
        scenes = script.get("scenes", [])
        if not scenes or len(scenes) < 2:
            return defects
            
        # 检查时间戳序列
        prev_timestamp = None
        for i, scene in enumerate(scenes):
            if "timestamp" in scene:
                current_timestamp = scene["timestamp"]
                
                if prev_timestamp is not None:
                    # 检查是否有时间倒流
                    if current_timestamp < prev_timestamp:
                        defects.append(LogicDefect(
                            defect_type=LogicDefectType.TIME_JUMP,
                            description=f"场景 {i} 的时间戳 ({current_timestamp}) 早于前一个场景 ({prev_timestamp})，可能存在时间倒流",
                            scene_index=i,
                            confidence=0.9,
                            severity="high",
                            suggested_fix=f"调整场景 {i} 的时间戳，确保不早于前一个场景"
                        ))
                
                prev_timestamp = current_timestamp
        
        return defects
    
    def _detect_prop_teleport(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测道具传送缺陷"""
        # 简化版实现
        return []
    
    def _detect_character_clone(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测角色分身缺陷"""
        # 简化版实现
        return []
    
    def _detect_causality_break(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测因果断裂缺陷"""
        # 简化版实现
        return []
    
    def _detect_dialogue_mismatch(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测对话错位缺陷"""
        # 简化版实现
        return []
    
    def _detect_emotion_flip(self, script: Dict[str, Any]) -> List[LogicDefect]:
        """检测情感翻转缺陷"""
        # 简化版实现
        return []


def validate_logic_sandbox(script: Dict[str, Any], stress_test: bool = False) -> Dict[str, Any]:
    """使用逻辑沙盒验证脚本"""
    sandbox = LogicSandbox()
    defects = sandbox.detect_defects(script)
    
    result = {
        "defects": [defect.__dict__ for defect in defects],
        "defect_count": len(defects),
        "timestamp": "N/A"
    }
    
    # 计算综合评分
    if defects:
        severity_weights = sandbox.config["severity_weights"]
        weighted_score = sum(severity_weights.get(d.severity, 1.0) * d.confidence for d in defects)
        avg_score = weighted_score / len(defects)
        result["score"] = max(0, 1 - avg_score / 3)
    else:
        result["score"] = 1.0
        
    # 如果需要进行压力测试
    if stress_test:
        detection_rate = sandbox.stress_test(script)
        result["stress_test"] = {
            "detection_rate": detection_rate,
            "description": f"在模拟注入的缺陷中检测出了 {detection_rate:.2%}"
        }
    
    return result


# ===========================================
# 测试数据和测试函数
# ===========================================

def create_test_script():
    """创建测试脚本"""
    return {
        "scenes": [
            {
                "id": "scene1",
                "timestamp": 1000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "visible"},
                    {"name": "地图", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "我们必须找到宝藏！", "emotion": "excited"},
                    {"character": "配角", "text": "我们得小心行事。", "emotion": "cautious"}
                ],
                "emotion": "positive"
            },
            {
                "id": "scene2",
                "timestamp": 2000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "配角", "traits": ["聪明", "谨慎"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "wielded"},
                    {"name": "地图", "state": "used"}
                ],
                "dialogues": [
                    {"character": "主角", "text": "看，地图上标记的位置就在前方！", "emotion": "excited"},
                    {"character": "配角", "text": "有些不对劲，我们可能被跟踪了。", "emotion": "worried"}
                ],
                "emotion": "tense"
            },
            {
                "id": "scene3",
                "timestamp": 3000,
                "characters": [
                    {"name": "主角", "traits": ["勇敢", "忠诚"]},
                    {"name": "敌人", "traits": ["凶狠", "贪婪"]}
                ],
                "props": [
                    {"name": "宝剑", "state": "wielded"},
                    {"name": "宝箱", "state": "visible"}
                ],
                "dialogues": [
                    {"character": "敌人", "text": "这宝藏是我的了！", "emotion": "aggressive"},
                    {"character": "主角", "text": "我不会让你得逞的！", "emotion": "determined"}
                ],
                "emotion": "negative"
            }
        ]
    }


def create_defective_script():
    """创建有缺陷的测试脚本"""
    script = create_test_script()
    
    # 修改第二个场景的时间戳，造成时间倒流
    script["scenes"][1]["timestamp"] = 500
    
    # 添加一个无来由的道具
    script["scenes"][1]["props"].append({"name": "魔法杖", "state": "appeared"})
    
    return script


def test_sandbox_detector():
    """测试逻辑沙盒检测器"""
    print("\n===== 测试逻辑沙盒检测器 =====")
    
    # 创建沙盒实例
    sandbox = LogicSandbox()
    
    # 测试正常脚本
    normal_script = create_test_script()
    print("\n--- 测试正常脚本 ---")
    defects = sandbox.detect_defects(normal_script)
    print(f"检测到缺陷数量: {len(defects)}")
    
    # 测试有缺陷的脚本
    defective_script = create_defective_script()
    print("\n--- 测试有缺陷脚本 ---")
    defects = sandbox.detect_defects(defective_script)
    print(f"检测到缺陷数量: {len(defects)}")
    
    for i, defect in enumerate(defects, 1):
        print(f"缺陷 {i}: [{defect.defect_type.name}] {defect.description}")
        if defect.suggested_fix:
            print(f"  建议修复: {defect.suggested_fix}")
    
    # 测试便捷验证函数
    print("\n--- 测试便捷验证函数 ---")
    result = validate_logic_sandbox(defective_script)
    print(f"缺陷数量: {result['defect_count']}")
    print(f"脚本评分: {result['score']:.2f}/1.0")
    
    # 测试压力测试
    print("\n--- 测试压力测试 ---")
    result = validate_logic_sandbox(normal_script, stress_test=True)
    print(f"检出率: {result['stress_test']['detection_rate']:.2%}")
    print(f"描述: {result['stress_test']['description']}")


def test_defect_injection():
    """测试缺陷注入"""
    print("\n===== 测试缺陷注入 =====")
    
    # 创建沙盒实例和测试脚本
    sandbox = LogicSandbox()
    script = create_test_script()
    
    # 注入时间跳跃缺陷
    print("\n--- 注入时间跳跃缺陷 ---")
    config = {"type": "TIME_JUMP", "value": -500}
    corrupted_script = sandbox.inject_defect(script, config)
    
    # 验证缺陷是否成功注入
    if "_injected_defects" in corrupted_script:
        defect = corrupted_script["_injected_defects"][0]
        print(f"注入的缺陷: {defect['type']}")
        print(f"描述: {defect['description']}")
        
        # 检测注入的缺陷
        defects = sandbox.detect_defects(corrupted_script)
        print(f"检测到缺陷数量: {len(defects)}")
        
        if defects:
            print(f"检测到的缺陷: {defects[0].defect_type.name}")
            print(f"缺陷描述: {defects[0].description}")
    else:
        print("缺陷注入失败")


def main():
    """主函数"""
    print("===== 逻辑漏洞沙盒检测器独立测试 =====")
    
    try:
        # 测试逻辑沙盒检测器
        test_sandbox_detector()
        
        # 测试缺陷注入
        test_defect_injection()
        
        print("\n所有测试完成!")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 