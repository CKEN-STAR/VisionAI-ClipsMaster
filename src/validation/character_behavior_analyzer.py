#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色行为一致性分析器

此模块提供用于分析角色行为一致性的工具，主要功能包括：
1. 角色特性分析 - 基于角色的行为和对话建立角色性格档案
2. 行为一致性验证 - 验证角色行为与其已建立的性格特征是否一致
3. 角色发展弧线 - 分析角色特性随时间的演变是否合理
4. 关系一致性 - 监测角色间的关系是否保持一致

使用这些工具可以确保视频内容中角色的行为符合其设定的个性，提高内容的连贯性和可信度。
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import re
from collections import defaultdict, Counter

# 配置日志
logger = logging.getLogger(__name__)

# 定义常量
PERSONALITY_TRAITS = {
    "勇敢": ["brave", "courageous", "bold", "fearless", "勇敢", "勇气", "无畏"],
    "谨慎": ["cautious", "careful", "prudent", "wary", "谨慎", "小心", "警惕"],
    "乐观": ["optimistic", "hopeful", "positive", "cheerful", "乐观", "积极", "开朗"],
    "悲观": ["pessimistic", "negative", "gloomy", "downbeat", "悲观", "消极", "阴郁"],
    "诚实": ["honest", "truthful", "straightforward", "sincere", "诚实", "真诚", "坦率"],
    "欺骗": ["deceptive", "dishonest", "lying", "manipulative", "欺骗", "说谎", "操纵"],
    "慷慨": ["generous", "giving", "charitable", "benevolent", "慷慨", "大方", "善良"],
    "吝啬": ["stingy", "greedy", "selfish", "miserly", "吝啬", "自私", "贪婪"],
    "忠诚": ["loyal", "faithful", "devoted", "dedicated", "忠诚", "忠心", "信守"],
    "背叛": ["betraying", "disloyal", "treacherous", "unfaithful", "背叛", "不忠", "出卖"],
}

# 设定对立特性
OPPOSING_TRAITS = {
    "勇敢": "谨慎",
    "乐观": "悲观",
    "诚实": "欺骗",
    "慷慨": "吝啬",
    "忠诚": "背叛",
}
# 完成反向映射
OPPOSING_TRAITS.update({v: k for k, v in OPPOSING_TRAITS.items()})

# 行为关键词到特性的映射
BEHAVIOR_TO_TRAIT = {
    "冲上前": "勇敢",
    "挺身而出": "勇敢",
    "拯救": "勇敢",
    "保护": "勇敢",
    "犹豫不决": "谨慎",
    "三思而后行": "谨慎",
    "谨慎考虑": "谨慎",
    "衡量风险": "谨慎",
    "期待": "乐观",
    "相信": "乐观",
    "看好": "乐观",
    "充满希望": "乐观",
    "担忧": "悲观",
    "不相信": "悲观",
    "怀疑": "悲观",
    "失去希望": "悲观",
    "坦白": "诚实",
    "告知真相": "诚实",
    "坦诚相待": "诚实",
    "撒谎": "欺骗",
    "隐瞒": "欺骗",
    "欺骗": "欺骗",
    "分享": "慷慨",
    "帮助": "慷慨",
    "捐赠": "慷慨",
    "拒绝分享": "吝啬",
    "只顾自己": "吝啬",
    "据为己有": "吝啬",
    "忠于": "忠诚",
    "坚守承诺": "忠诚",
    "支持": "忠诚",
    "背叛": "背叛",
    "出卖": "背叛",
    "食言": "背叛"
}

class CharacterPersonaDatabase:
    """
    角色特性数据库
    
    存储和管理角色的性格特性数据，用于跟踪角色的性格发展和一致性。
    """
    
    def __init__(self):
        """初始化角色特性数据库"""
        self.character_personas: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.character_scenes: Dict[str, List[int]] = defaultdict(list)
        self.character_relationships: Dict[Tuple[str, str], Dict[str, float]] = {}
        
    def reset(self):
        """重置数据库"""
        self.character_personas.clear()
        self.character_scenes.clear()
        self.character_relationships.clear()
    
    def add_trait_observation(self, character: str, trait: str, strength: float = 1.0, scene_index: Optional[int] = None):
        """
        添加一个角色特性观察
        
        Args:
            character: 角色名称
            trait: 特性名称
            strength: 特性强度 (0.0-1.0)
            scene_index: 观察到的场景索引，如果提供将用于跟踪角色出现的场景
        """
        self.character_personas[character][trait] += strength
        
        # 记录角色出现的场景
        if scene_index is not None and scene_index not in self.character_scenes[character]:
            self.character_scenes[character].append(scene_index)
    
    def get_character_trait(self, character: str, trait: str) -> float:
        """
        获取角色的特定特性强度
        
        Args:
            character: 角色名称
            trait: 特性名称
            
        Returns:
            特性强度值
        """
        return self.character_personas[character].get(trait, 0.0)
    
    def get_character_profile(self, character: str) -> Dict[str, float]:
        """
        获取角色的完整性格档案
        
        Args:
            character: 角色名称
            
        Returns:
            角色的所有特性和相应强度
        """
        return dict(self.character_personas[character])
    
    def get_dominant_traits(self, character: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        获取角色的主要特性
        
        Args:
            character: 角色名称
            top_n: 返回的主要特性数量
            
        Returns:
            主要特性及其强度的列表，按强度降序排列
        """
        traits = self.get_character_profile(character)
        # 按特性强度降序排序
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        return sorted_traits[:top_n]
    
    def record_relationship(self, character1: str, character2: str, relationship_type: str, strength: float = 1.0):
        """
        记录两个角色之间的关系
        
        Args:
            character1: 第一个角色
            character2: 第二个角色
            relationship_type: 关系类型（如"友好"、"敌对"等）
            strength: 关系强度 (0.0-1.0)
        """
        # 确保角色对的顺序一致
        char_key = tuple(sorted([character1, character2]))
        
        if char_key not in self.character_relationships:
            self.character_relationships[char_key] = {}
        
        # 累加关系强度
        self.character_relationships[char_key][relationship_type] = \
            self.character_relationships[char_key].get(relationship_type, 0.0) + strength
    
    def get_relationship(self, character1: str, character2: str) -> Dict[str, float]:
        """
        获取两个角色之间的关系
        
        Args:
            character1: 第一个角色
            character2: 第二个角色
            
        Returns:
            角色间的关系类型及其强度
        """
        char_key = tuple(sorted([character1, character2]))
        return dict(self.character_relationships.get(char_key, {}))
    
    def has_contradicting_traits(self, character: str) -> List[Tuple[str, str, float, float]]:
        """
        检查角色是否有矛盾的特性
        
        Args:
            character: 角色名称
            
        Returns:
            矛盾特性对列表，每项包含特性名称和强度
        """
        contradictions = []
        traits = self.get_character_profile(character)
        
        for trait1, strength1 in traits.items():
            if trait1 in OPPOSING_TRAITS and strength1 > 0:
                opposing_trait = OPPOSING_TRAITS[trait1]
                strength2 = traits.get(opposing_trait, 0.0)
                if strength2 > 0:
                    contradictions.append((trait1, opposing_trait, strength1, strength2))
        
        return contradictions
    
    def extract_traits_from_text(self, text: str) -> Dict[str, float]:
        """
        从文本中提取性格特性
        
        Args:
            text: 角色对话或描述文本
            
        Returns:
            提取的特性及其强度
        """
        traits = {}
        
        # 检查行为关键词
        for behavior, trait in BEHAVIOR_TO_TRAIT.items():
            if behavior in text:
                traits[trait] = traits.get(trait, 0) + 1.0
        
        # 检查特性关键词
        for trait, keywords in PERSONALITY_TRAITS.items():
            for keyword in keywords:
                if keyword in text.lower():
                    traits[trait] = traits.get(trait, 0) + 0.8
        
        return traits


class CharacterBehaviorValidator:
    """
    角色行为一致性验证器
    
    分析角色的行为与其已建立的性格特征是否一致。
    """
    
    def __init__(self):
        """初始化角色行为一致性验证器"""
        self.persona_db = CharacterPersonaDatabase()
        
    def reset(self):
        """重置验证器状态"""
        self.persona_db.reset()
    
    def analyze_scene(self, scene: Dict[str, Any], scene_index: int = None) -> List[Dict[str, Any]]:
        """
        分析单个场景中的角色行为
        
        Args:
            scene: 场景数据
            scene_index: 场景索引
            
        Returns:
            可能的角色行为不一致问题
        """
        inconsistencies = []
        
        # 提取场景中的角色
        characters = self._extract_characters(scene)
        
        for character in characters:
            # 提取文本内容
            text = self._get_character_text(scene, character)
            if not text:
                continue
                
            # 提取特性
            traits = self.persona_db.extract_traits_from_text(text)
            
            # 更新角色特性数据库
            for trait, strength in traits.items():
                self.persona_db.add_trait_observation(character, trait, strength, scene_index)
            
            # 检查行为与已记录特性的一致性
            profile = self.persona_db.get_character_profile(character)
            if profile:  # 只有当我们已经有角色档案时才进行一致性检查
                for trait, strength in traits.items():
                    # 检查是否与已知主要特性相矛盾
                    if trait in OPPOSING_TRAITS:
                        opposing = OPPOSING_TRAITS[trait]
                        if opposing in profile and profile[opposing] > 1.5 and strength > 0.5:
                            inconsistencies.append({
                                'character': character,
                                'problem': f"行为与角色特性不一致",
                                'details': f"展现了'{trait}'，但该角色主要特性为'{opposing}'",
                                'scene_index': scene_index
                            })
        
        # 提取角色关系
        self._extract_relationships(scene, scene_index)
        
        return inconsistencies
    
    def validate_character_development(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证角色发展弧线的合理性
        
        Args:
            scenes: 场景列表
            
        Returns:
            角色发展分析结果
        """
        # 重置验证器状态
        self.reset()
        
        # 按顺序分析所有场景
        all_inconsistencies = []
        for i, scene in enumerate(scenes):
            inconsistencies = self.analyze_scene(scene, i)
            all_inconsistencies.extend(inconsistencies)
        
        # 分析角色弧线
        character_arcs = {}
        arc_problems = []
        
        for character in self.persona_db.character_personas:
            # 获取角色出现的场景
            char_scenes = self.persona_db.character_scenes[character]
            
            if len(char_scenes) >= 3:  # 只分析有足够场景的角色
                # 获取主要特性在不同场景中的变化
                dominant_traits = self.persona_db.get_dominant_traits(character, top_n=2)
                
                if dominant_traits:
                    main_trait = dominant_traits[0][0]
                    trait_development = {}
                    
                    # 对每个场景计算特性强度
                    for scene_idx in char_scenes:
                        if scene_idx < len(scenes):
                            scene = scenes[scene_idx]
                            text = self._get_character_text(scene, character)
                            if text:
                                traits = self.persona_db.extract_traits_from_text(text)
                                trait_development[scene_idx] = traits.get(main_trait, 0.0)
                    
                    # 检查特性发展是否平滑
                    character_arcs[character] = {
                        'main_trait': main_trait,
                        'development': trait_development
                    }
                    
                    # 检测不合理的特性变化
                    if trait_development:
                        indices = sorted(trait_development.keys())
                        for i in range(1, len(indices)):
                            curr_idx = indices[i]
                            prev_idx = indices[i-1]
                            
                            curr_val = trait_development[curr_idx]
                            prev_val = trait_development[prev_idx]
                            
                            # 检测突然的极端变化
                            if abs(curr_val - prev_val) > 1.5 and curr_idx - prev_idx <= 2:
                                arc_problems.append({
                                    'character': character,
                                    'problem': '角色特性变化过于突然',
                                    'trait': main_trait,
                                    'scene_indices': [prev_idx, curr_idx]
                                })
        
        # 检查矛盾的性格特性
        trait_contradictions = []
        for character in self.persona_db.character_personas:
            contradictions = self.persona_db.has_contradicting_traits(character)
            if contradictions:
                for contra in contradictions:
                    trait_contradictions.append({
                        'character': character,
                        'problem': '角色具有矛盾的特性',
                        'traits': f"{contra[0]}({contra[2]:.1f}) 和 {contra[1]}({contra[3]:.1f})"
                    })
        
        # 检查关系一致性
        relationship_issues = self._validate_relationships()
        
        return {
            'character_profiles': {char: dict(profile) for char, profile in self.persona_db.character_personas.items()},
            'behavior_inconsistencies': all_inconsistencies,
            'character_arcs': character_arcs,
            'arc_problems': arc_problems,
            'trait_contradictions': trait_contradictions,
            'relationship_issues': relationship_issues
        }
    
    def suggest_personality_adjustments(self, character: str) -> Dict[str, Any]:
        """
        基于观察到的行为建议调整角色性格档案
        
        Args:
            character: 角色名称
            
        Returns:
            性格调整建议
        """
        profile = self.persona_db.get_character_profile(character)
        if not profile:
            return {"character": character, "suggestions": []}
        
        suggestions = []
        contradictions = self.persona_db.has_contradicting_traits(character)
        
        for contra in contradictions:
            trait1, trait2, strength1, strength2 = contra
            if strength1 > strength2:
                suggestions.append({
                    "remove_trait": trait2,
                    "reason": f"与主要特性'{trait1}'相矛盾",
                    "confidence": (strength1 - strength2) / (strength1 + strength2)
                })
            else:
                suggestions.append({
                    "remove_trait": trait1,
                    "reason": f"与主要特性'{trait2}'相矛盾",
                    "confidence": (strength2 - strength1) / (strength1 + strength2)
                })
        
        dominant_traits = self.persona_db.get_dominant_traits(character)
        weak_traits = [(t, s) for t, s in profile.items() if s < 0.5]
        
        for trait, strength in weak_traits:
            # 检查弱特性是否与主要特性冲突
            is_conflicting = False
            for dom_trait, _ in dominant_traits:
                if dom_trait in OPPOSING_TRAITS and OPPOSING_TRAITS[dom_trait] == trait:
                    is_conflicting = True
                    break
            
            if is_conflicting:
                suggestions.append({
                    "remove_trait": trait,
                    "reason": f"证据不足且与主要特性冲突",
                    "confidence": 0.8
                })
        
        return {
            "character": character,
            "current_profile": profile,
            "suggestions": suggestions
        }
    
    def _extract_characters(self, scene: Dict[str, Any]) -> Set[str]:
        """提取场景中的角色"""
        characters = set()
        
        # 检查character字段
        if "character" in scene and isinstance(scene["character"], str):
            characters.add(scene["character"])
        
        # 检查characters列表
        if "characters" in scene and isinstance(scene["characters"], (list, set)):
            characters.update(scene["characters"])
        
        # 从对话中提取角色
        if "dialog" in scene and isinstance(scene["dialog"], list):
            for entry in scene["dialog"]:
                if isinstance(entry, dict) and "speaker" in entry:
                    characters.add(entry["speaker"])
        
        # 从文本中识别角色（这是一个简化的方法，可能需要更复杂的NLP处理）
        if "text" in scene and isinstance(scene["text"], str):
            # 简单的角色检测模式：假设中文姓名是2-3个字，英文名首字母大写
            char_pattern = r'([A-Z][a-z]+|[\u4e00-\u9fa5]{2,3})[：:]'
            found_chars = re.findall(char_pattern, scene["text"])
            characters.update(found_chars)
        
        return characters
    
    def _get_character_text(self, scene: Dict[str, Any], character: str) -> str:
        """获取特定角色在场景中的所有文本"""
        texts = []
        
        # 收集角色的对话
        if "dialog" in scene and isinstance(scene["dialog"], list):
            for entry in scene["dialog"]:
                if isinstance(entry, dict) and entry.get("speaker") == character and "text" in entry:
                    texts.append(entry["text"])
        
        # 如果场景主角色是当前角色，则包含场景文本
        if scene.get("character") == character and "text" in scene:
            texts.append(scene["text"])
        
        # 从完整文本中提取角色相关内容（简化方法）
        if "text" in scene and character in scene["text"]:
            # 尝试找到角色说的话
            pattern = rf'{re.escape(character)}[：:](.*?)(?=\n|$|[A-Z\u4e00-\u9fa5]{{2,3}}[：:])'
            char_texts = re.findall(pattern, scene["text"], re.DOTALL)
            texts.extend(char_texts)
            
            # 查找描述角色行为的句子
            sentences = re.split(r'[。！？.!?]+', scene["text"])
            for sentence in sentences:
                if character in sentence:
                    texts.append(sentence)
        
        return " ".join(texts)
    
    def _extract_relationships(self, scene: Dict[str, Any], scene_index: int = None) -> None:
        """提取场景中的角色关系"""
        characters = self._extract_characters(scene)
        if len(characters) < 2:
            return
        
        # 识别潜在的关系类型
        relationship_indicators = {
            "友好": ["朋友", "帮助", "感谢", "友好", "信任", "支持", "friend", "help", "thanks", "trust", "support"],
            "敌对": ["敌人", "反对", "战斗", "对抗", "憎恨", "enemy", "against", "fight", "hate", "oppose"],
            "亲密": ["爱", "喜欢", "关心", "思念", "love", "like", "care", "miss"],
            "尊敬": ["尊敬", "佩服", "崇拜", "admire", "respect", "look up to"],
            "恐惧": ["怕", "恐惧", "害怕", "惧怕", "afraid", "fear", "scared"]
        }
        
        for char1 in characters:
            for char2 in characters:
                if char1 != char2:
                    text = scene.get("text", "")
                    
                    # 查找文本中可能指示两个角色关系的部分
                    snippets = []
                    pattern = rf'({re.escape(char1)}.*{re.escape(char2)}|{re.escape(char2)}.*{re.escape(char1)})'
                    relation_snippets = re.findall(pattern, text)
                    snippets.extend(relation_snippets)
                    
                    # 从对话中提取关系
                    if "dialog" in scene and isinstance(scene["dialog"], list):
                        for entry in scene["dialog"]:
                            if entry.get("speaker") == char1 and char2 in entry.get("text", ""):
                                snippets.append(entry["text"])
                    
                    # 分析关系
                    for rel_type, indicators in relationship_indicators.items():
                        for snippet in snippets:
                            for indicator in indicators:
                                if indicator in snippet:
                                    self.persona_db.record_relationship(char1, char2, rel_type, 1.0)
    
    def _validate_relationships(self) -> List[Dict[str, Any]]:
        """验证角色关系的一致性"""
        issues = []
        
        for char_pair, relationships in self.persona_db.character_relationships.items():
            char1, char2 = char_pair
            
            # 检查矛盾关系：如同时存在友好和敌对
            opposing_relations = [
                ("友好", "敌对"),
                ("亲密", "恐惧"),
                ("尊敬", "敌对")
            ]
            
            for rel1, rel2 in opposing_relations:
                if rel1 in relationships and rel2 in relationships:
                    strength1 = relationships[rel1]
                    strength2 = relationships[rel2]
                    
                    # 如果两种关系都很强，那么可能存在矛盾
                    if strength1 > 1.0 and strength2 > 1.0:
                        issues.append({
                            'characters': [char1, char2],
                            'problem': '角色关系矛盾',
                            'details': f"同时存在'{rel1}'({strength1:.1f})和'{rel2}'({strength2:.1f})关系"
                        })
        
        return issues


def validate_character_behavior(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：验证角色行为一致性
    
    Args:
        scenes: 场景列表
        
    Returns:
        验证结果
    """
    validator = CharacterBehaviorValidator()
    return validator.validate_character_development(scenes) 