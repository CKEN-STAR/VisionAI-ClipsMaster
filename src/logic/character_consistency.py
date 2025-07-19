#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色行为一致性分析器

此模块提供用于分析和验证角色在不同场景中的行为是否一致的工具。主要功能包括：
1. 角色性格特征数据库 - 存储角色的基本性格特征和行为倾向
2. 行为一致性检查 - 验证角色的行为是否符合其性格特征
3. 性格冲突检测 - 发现角色行为与其性格设定的冲突
4. 行为演变分析 - 追踪角色性格的自然演变过程

使用这些工具可以避免混剪过程中出现角色行为不一致的情况，提升角色形象的可信度。
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import re
import json
import os
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 默认数据路径
DEFAULT_PERSONA_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    "..", "..", "data", "character_profiles"
)

# 性格特征类型定义
TRAIT_TYPES = {
    "bravery": "勇敢度",      # 勇敢 vs 谨慎
    "optimism": "乐观度",     # 乐观 vs 悲观
    "outgoing": "外向度",     # 外向 vs 内向
    "kindness": "善良度",     # 善良 vs 刻薄
    "honesty": "诚实度",      # 诚实 vs 狡猾
    "intelligence": "智慧度",  # 聪明 vs 愚钝
    "patience": "耐心度",      # 耐心 vs 急躁
    "loyalty": "忠诚度",       # 忠诚 vs 背叛
}

# 行为关键词映射到性格特征
BEHAVIOR_TRAIT_MAPPINGS = {
    "勇敢": {"bravery": 0.8},
    "冒险": {"bravery": 0.7},
    "挑战": {"bravery": 0.6},
    "谨慎": {"bravery": -0.6},
    "害怕": {"bravery": -0.8},
    "退缩": {"bravery": -0.9},
    
    "积极": {"optimism": 0.7},
    "乐观": {"optimism": 0.9},
    "期待": {"optimism": 0.6},
    "悲观": {"optimism": -0.8},
    "消极": {"optimism": -0.7},
    "绝望": {"optimism": -0.9},
    
    "交际": {"outgoing": 0.8},
    "社交": {"outgoing": 0.7},
    "热情": {"outgoing": 0.6},
    "孤僻": {"outgoing": -0.8},
    "安静": {"outgoing": -0.6},
    "独处": {"outgoing": -0.7},
    
    "善良": {"kindness": 0.9},
    "帮助": {"kindness": 0.8},
    "关心": {"kindness": 0.7},
    "冷漠": {"kindness": -0.7},
    "刻薄": {"kindness": -0.8},
    "伤害": {"kindness": -0.9},
    
    "诚实": {"honesty": 0.9},
    "坦白": {"honesty": 0.8},
    "真诚": {"honesty": 0.7},
    "欺骗": {"honesty": -0.9},
    "谎言": {"honesty": -0.8},
    "隐瞒": {"honesty": -0.6},
    
    "聪明": {"intelligence": 0.8},
    "智慧": {"intelligence": 0.9},
    "学习": {"intelligence": 0.7},
    "愚蠢": {"intelligence": -0.8},
    "粗心": {"intelligence": -0.7},
    "糊涂": {"intelligence": -0.6},
    
    "耐心": {"patience": 0.9},
    "等待": {"patience": 0.8},
    "冷静": {"patience": 0.7},
    "急躁": {"patience": -0.8},
    "冲动": {"patience": -0.9},
    "暴躁": {"patience": -0.7},
    
    "忠诚": {"loyalty": 0.9},
    "信任": {"loyalty": 0.8},
    "承诺": {"loyalty": 0.7},
    "背叛": {"loyalty": -0.9},
    "欺骗": {"loyalty": -0.8},
    "背弃": {"loyalty": -0.7},
}

class CharacterPersonaDatabase:
    """
    角色性格特征数据库
    
    管理和存储角色的性格特征数据，支持导入导出和查询功能。
    """
    
    def __init__(self, db_path: str = DEFAULT_PERSONA_DB_PATH):
        """
        初始化角色性格特征数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.personas = {}
        self._load_database()
    
    def _load_database(self) -> None:
        """加载数据库"""
        # 创建数据目录（如果不存在）
        os.makedirs(self.db_path, exist_ok=True)
        
        # 查找所有角色配置文件
        profile_files = Path(self.db_path).glob("*.json")
        
        for file_path in profile_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    character_data = json.load(f)
                    character_id = character_data.get("id", file_path.stem)
                    self.personas[character_id] = character_data
            except Exception as e:
                logger.error(f"加载角色配置文件失败 {file_path}: {e}")
    
    def save_persona(self, character_id: str, persona_data: Dict[str, Any]) -> bool:
        """
        保存角色性格数据
        
        Args:
            character_id: 角色ID
            persona_data: 角色性格数据
            
        Returns:
            保存是否成功
        """
        try:
            # 确保数据包含必要字段
            if "traits" not in persona_data:
                persona_data["traits"] = {}
            
            # 更新内存数据
            self.personas[character_id] = persona_data
            
            # 保存到文件
            file_path = os.path.join(self.db_path, f"{character_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(persona_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"保存角色数据失败 {character_id}: {e}")
            return False
    
    def get_persona(self, character_id: str) -> Dict[str, Any]:
        """
        获取角色性格数据
        
        Args:
            character_id: 角色ID
            
        Returns:
            角色性格数据，如果不存在则返回默认值
        """
        if character_id in self.personas:
            return self.personas[character_id]
        
        # 返回默认性格
        return {
            "id": character_id,
            "name": character_id,
            "traits": {
                "bravery": 0.5,
                "optimism": 0.5,
                "outgoing": 0.5,
                "kindness": 0.5,
                "honesty": 0.5,
                "intelligence": 0.5,
                "patience": 0.5,
                "loyalty": 0.5
            },
            "behaviors": [],
            "relationships": {}
        }
    
    def list_characters(self) -> List[str]:
        """
        列出所有角色ID
        
        Returns:
            角色ID列表
        """
        return list(self.personas.keys())
    
    def update_trait(self, character_id: str, trait: str, value: float) -> bool:
        """
        更新角色特定性格特征值
        
        Args:
            character_id: 角色ID
            trait: 特征名称
            value: 特征值(-1.0到1.0之间)
            
        Returns:
            更新是否成功
        """
        if character_id not in self.personas:
            self.personas[character_id] = self.get_persona(character_id)
        
        # 确保值在有效范围内
        value = max(-1.0, min(1.0, value))
        
        # 更新特征
        if "traits" not in self.personas[character_id]:
            self.personas[character_id]["traits"] = {}
        
        self.personas[character_id]["traits"][trait] = value
        
        # 保存更新
        return self.save_persona(character_id, self.personas[character_id])
    
    def add_behavior(self, character_id: str, behavior: str, context: Optional[str] = None) -> bool:
        """
        添加角色行为记录
        
        Args:
            character_id: 角色ID
            behavior: 行为描述
            context: 行为发生的上下文
            
        Returns:
            添加是否成功
        """
        if character_id not in self.personas:
            self.personas[character_id] = self.get_persona(character_id)
        
        if "behaviors" not in self.personas[character_id]:
            self.personas[character_id]["behaviors"] = []
        
        behavior_entry = {
            "behavior": behavior,
            "context": context
        }
        
        self.personas[character_id]["behaviors"].append(behavior_entry)
        
        # 保存更新
        return self.save_persona(character_id, self.personas[character_id])


class CharacterBehaviorValidator:
    """
    角色行为一致性验证器
    
    检验角色在不同场景中的行为是否符合其人物设定和性格特征。
    """
    
    def __init__(self, persona_db_path: str = DEFAULT_PERSONA_DB_PATH):
        """
        初始化角色行为一致性验证器
        
        Args:
            persona_db_path: 角色数据库路径
        """
        self.persona_db = CharacterPersonaDatabase(persona_db_path)
        self.conflict_threshold = 0.4  # 行为和性格冲突的阈值
    
    def validate_actions(self, character_id: str, current_action: str) -> Optional[str]:
        """
        验证角色行为是否符合其性格特征
        
        Args:
            character_id: 角色ID
            current_action: 当前行为描述
            
        Returns:
            如果行为与性格不符，返回描述冲突的字符串；否则返回None
        """
        # 获取角色性格
        persona = self.persona_db.get_persona(character_id)
        
        # 基于行为分析性格特征
        action_traits = self._analyze_action_traits(current_action)
        
        # 检查冲突
        conflicts = []
        for trait, action_value in action_traits.items():
            # 只有当性格特征已定义时才进行对比
            if trait in persona["traits"]:
                persona_value = persona["traits"][trait]
                # 如果行为特征值和角色特征值差异较大，则视为冲突
                if abs(persona_value - action_value) > self.conflict_threshold:
                    trait_name = TRAIT_TYPES.get(trait, trait)
                    conflicts.append({
                        "trait": trait,
                        "trait_name": trait_name,
                        "expected": persona_value,
                        "actual": action_value,
                        "difference": abs(persona_value - action_value)
                    })
        
        # 如果有冲突，返回描述
        if conflicts:
            # 按冲突程度排序
            conflicts.sort(key=lambda x: x["difference"], reverse=True)
            
            # 构建冲突描述
            conflict_desc = f"角色[{persona.get('name', character_id)}]的行为与其性格不符: "
            for conflict in conflicts[:2]:  # 只显示最严重的两个冲突
                trait_desc = "过于" if conflict["actual"] > conflict["expected"] else "过于不"
                trait_name = conflict["trait_name"]
                conflict_desc += f"{trait_desc}{trait_name}; "
            
            return conflict_desc
        
        # 记录行为
        self.persona_db.add_behavior(character_id, current_action)
        
        return None
    
    def _analyze_action_traits(self, action: str) -> Dict[str, float]:
        """
        分析行为中蕴含的性格特征
        
        Args:
            action: 行为描述
            
        Returns:
            性格特征及其值的字典
        """
        action_traits = {}
        
        # 对于每个行为关键词，检查是否出现在行为描述中
        for keyword, traits in BEHAVIOR_TRAIT_MAPPINGS.items():
            if keyword in action:
                for trait, value in traits.items():
                    # 如果已经有该特征，取平均值
                    if trait in action_traits:
                        action_traits[trait] = (action_traits[trait] + value) / 2
                    else:
                        action_traits[trait] = value
        
        return action_traits
    
    def analyze_character_arc(self, character_id: str, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析角色在场景序列中的性格演变
        
        Args:
            character_id: 角色ID
            scenes: 场景列表
            
        Returns:
            角色性格演变分析结果
        """
        persona = self.persona_db.get_persona(character_id)
        
        # 提取角色在各场景中的行为
        character_actions = []
        for scene in scenes:
            if scene.get("character") == character_id and "text" in scene:
                character_actions.append({
                    "scene_id": scene.get("id", ""),
                    "action": scene["text"],
                    "emotion": scene.get("emotion", ""),
                    "location": scene.get("location", ""),
                    "time": scene.get("start", 0)
                })
        
        if not character_actions:
            return {
                "character_id": character_id,
                "name": persona.get("name", character_id),
                "arc_detected": False,
                "message": "未找到足够的角色行为数据"
            }
        
        # 对行为按时间排序
        character_actions.sort(key=lambda x: x["time"])
        
        # 分析初始和最终性格特征
        initial_traits = {} if not character_actions else self._analyze_action_traits(character_actions[0]["action"])
        final_traits = {} if not character_actions else self._analyze_action_traits(character_actions[-1]["action"])
        
        # 确定性格变化
        trait_changes = {}
        all_traits = set(list(initial_traits.keys()) + list(final_traits.keys()))
        
        for trait in all_traits:
            initial_value = initial_traits.get(trait, 0.0)
            final_value = final_traits.get(trait, 0.0)
            if abs(final_value - initial_value) > 0.2:  # 只关注显著变化
                trait_changes[trait] = {
                    "initial": initial_value,
                    "final": final_value,
                    "change": final_value - initial_value
                }
        
        # 分析结果
        has_arc = bool(trait_changes)
        
        result = {
            "character_id": character_id,
            "name": persona.get("name", character_id),
            "arc_detected": has_arc,
            "scene_count": len(character_actions),
            "trait_changes": trait_changes,
        }
        
        if has_arc:
            # 描述最显著的变化
            significant_changes = sorted(
                trait_changes.items(), 
                key=lambda x: abs(x[1]["change"]), 
                reverse=True
            )
            
            most_significant = significant_changes[0]
            trait_name = TRAIT_TYPES.get(most_significant[0], most_significant[0])
            change_value = most_significant[1]["change"]
            
            if change_value > 0:
                direction = "更加"
            else:
                direction = "变得不那么"
            
            result["arc_description"] = f"角色[{persona.get('name', character_id)}]在故事中{direction}{trait_name}"
        
        return result
    
    def check_relationship_consistency(self, character1_id: str, character2_id: str, 
                                      scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检查两个角色之间关系的一致性
        
        Args:
            character1_id: 第一个角色ID
            character2_id: 第二个角色ID
            scenes: 场景列表
            
        Returns:
            关系一致性分析结果
        """
        # 获取角色信息
        persona1 = self.persona_db.get_persona(character1_id)
        persona2 = self.persona_db.get_persona(character2_id)
        
        # 提取两个角色之间的互动场景
        interaction_scenes = []
        for scene in scenes:
            if (scene.get("character") == character1_id and character2_id in scene.get("text", "")) or \
               (scene.get("character") == character2_id and character1_id in scene.get("text", "")):
                interaction_scenes.append(scene)
        
        if not interaction_scenes:
            return {
                "relationship_detected": False,
                "message": f"未找到角色[{persona1.get('name', character1_id)}]和[{persona2.get('name', character2_id)}]之间的互动"
            }
        
        # 当前角色关系（从数据库中获取）
        relationship1to2 = persona1.get("relationships", {}).get(character2_id, {}).get("type", "未知")
        relationship2to1 = persona2.get("relationships", {}).get(character1_id, {}).get("type", "未知")
        
        # 分析场景中表现出的关系
        positive_interactions = 0
        negative_interactions = 0
        
        positive_keywords = ["喜欢", "爱", "欣赏", "感谢", "尊重", "信任", "友好", "帮助"]
        negative_keywords = ["讨厌", "恨", "厌恶", "不满", "愤怒", "不信任", "敌对", "伤害"]
        
        for scene in interaction_scenes:
            text = scene.get("text", "")
            
            if any(keyword in text for keyword in positive_keywords):
                positive_interactions += 1
            
            if any(keyword in text for keyword in negative_keywords):
                negative_interactions += 1
        
        # 确定场景中的关系类型
        if positive_interactions > negative_interactions:
            scene_relationship = "友好"
        elif negative_interactions > positive_interactions:
            scene_relationship = "敌对"
        else:
            scene_relationship = "中性"
        
        # 检查一致性
        is_consistent1 = (relationship1to2 == "未知") or (relationship1to2 == scene_relationship) or \
                        (relationship1to2 == "中性" and scene_relationship != "敌对") or \
                        (relationship1to2 == "友好" and scene_relationship != "敌对")
        
        is_consistent2 = (relationship2to1 == "未知") or (relationship2to1 == scene_relationship) or \
                        (relationship2to1 == "中性" and scene_relationship != "敌对") or \
                        (relationship2to1 == "友好" and scene_relationship != "敌对")
        
        # 构建结果
        result = {
            "character1": {
                "id": character1_id,
                "name": persona1.get("name", character1_id)
            },
            "character2": {
                "id": character2_id,
                "name": persona2.get("name", character2_id)
            },
            "relationship_detected": True,
            "scene_relationship": scene_relationship,
            "stored_relationship": {
                f"{character1_id}_to_{character2_id}": relationship1to2,
                f"{character2_id}_to_{character1_id}": relationship2to1
            },
            "is_consistent": is_consistent1 and is_consistent2,
            "interaction_count": len(interaction_scenes)
        }
        
        if not result["is_consistent"]:
            if not is_consistent1:
                result["inconsistency_description"] = f"角色[{persona1.get('name', character1_id)}]对[{persona2.get('name', character2_id)}]的关系设定为'{relationship1to2}'，但在场景中表现为'{scene_relationship}'"
            else:
                result["inconsistency_description"] = f"角色[{persona2.get('name', character2_id)}]对[{persona1.get('name', character1_id)}]的关系设定为'{relationship2to1}'，但在场景中表现为'{scene_relationship}'"
        
        return result
    
    def suggest_personality_adjustments(self, character_id: str, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根据场景中的行为，建议调整角色性格特征
        
        Args:
            character_id: 角色ID
            scenes: 场景列表
            
        Returns:
            性格调整建议
        """
        persona = self.persona_db.get_persona(character_id)
        
        # 提取角色行为
        actions = []
        for scene in scenes:
            if scene.get("character") == character_id and "text" in scene:
                actions.append(scene["text"])
        
        if not actions:
            return {
                "character_id": character_id,
                "name": persona.get("name", character_id),
                "adjustments_needed": False,
                "message": "未找到足够的角色行为数据"
            }
        
        # 分析所有行为的性格特征
        all_action_traits = {}
        for action in actions:
            action_traits = self._analyze_action_traits(action)
            for trait, value in action_traits.items():
                if trait in all_action_traits:
                    all_action_traits[trait].append(value)
                else:
                    all_action_traits[trait] = [value]
        
        # 计算平均性格特征
        avg_action_traits = {}
        for trait, values in all_action_traits.items():
            avg_action_traits[trait] = sum(values) / len(values)
        
        # 检查性格不一致
        adjustments = {}
        for trait, avg_value in avg_action_traits.items():
            current_value = persona["traits"].get(trait, 0.5)
            if abs(current_value - avg_value) > self.conflict_threshold:
                adjustments[trait] = {
                    "current": current_value,
                    "suggested": avg_value,
                    "difference": avg_value - current_value
                }
        
        # 构建结果
        result = {
            "character_id": character_id,
            "name": persona.get("name", character_id),
            "adjustments_needed": bool(adjustments),
            "analyzed_actions": len(actions),
            "suggested_adjustments": adjustments
        }
        
        if adjustments:
            suggestions = []
            for trait, adj in adjustments.items():
                trait_name = TRAIT_TYPES.get(trait, trait)
                direction = "增加" if adj["difference"] > 0 else "减少"
                magnitude = abs(adj["difference"])
                
                if magnitude > 0.6:
                    level = "显著"
                elif magnitude > 0.3:
                    level = "适度"
                else:
                    level = "略微"
                
                suggestions.append(f"{level}{direction}'{trait_name}'特征")
            
            result["adjustment_description"] = f"角色[{persona.get('name', character_id)}]建议: " + ", ".join(suggestions)
        
        return result

# 提供给其他模块使用的API
def validate_character_behavior(character_id: str, action: str, 
                               persona_db_path: str = DEFAULT_PERSONA_DB_PATH) -> Optional[str]:
    """
    便捷函数：验证角色行为是否符合其性格特征
    
    Args:
        character_id: 角色ID
        action: 行为描述
        persona_db_path: 角色数据库路径
        
    Returns:
        如果行为不符合性格，返回冲突描述；否则返回None
    """
    validator = CharacterBehaviorValidator(persona_db_path)
    return validator.validate_actions(character_id, action)

def analyze_character_development(character_id: str, scenes: List[Dict[str, Any]],
                                 persona_db_path: str = DEFAULT_PERSONA_DB_PATH) -> Dict[str, Any]:
    """
    便捷函数：分析角色在场景序列中的性格演变
    
    Args:
        character_id: 角色ID
        scenes: 场景列表
        persona_db_path: 角色数据库路径
        
    Returns:
        角色性格演变分析结果
    """
    validator = CharacterBehaviorValidator(persona_db_path)
    return validator.analyze_character_arc(character_id, scenes)

def check_relationship(character1_id: str, character2_id: str, scenes: List[Dict[str, Any]],
                      persona_db_path: str = DEFAULT_PERSONA_DB_PATH) -> Dict[str, Any]:
    """
    便捷函数：检查两个角色之间关系的一致性
    
    Args:
        character1_id: 第一个角色ID
        character2_id: 第二个角色ID
        scenes: 场景列表
        persona_db_path: 角色数据库路径
        
    Returns:
        关系一致性分析结果
    """
    validator = CharacterBehaviorValidator(persona_db_path)
    return validator.check_relationship_consistency(character1_id, character2_id, scenes)

# 导出模块内容
__all__ = [
    'CharacterPersonaDatabase',
    'CharacterBehaviorValidator',
    'validate_character_behavior',
    'analyze_character_development',
    'check_relationship',
    'TRAIT_TYPES',
    'DEFAULT_PERSONA_DB_PATH'
] 