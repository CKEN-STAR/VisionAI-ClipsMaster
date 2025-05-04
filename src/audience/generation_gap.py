#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器模块

帮助弥合不同代际群体之间的文化差异，优化内容在不同年龄层受众中的理解和接受度。
通过识别和转换代际文化参考，使内容能够跨代际有效传播。
支持Z世代、80后、90后、00后等不同世代群体之间的文化表达桥接。
"""

import os
import copy
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from pathlib import Path

from loguru import logger
from src.utils.log_handler import get_logger
from src.adaptation.culture_adapter import CultureAdapter
from src.nlp.text_processor import TextProcessor

# 配置日志
generation_logger = get_logger("generation_bridge")

class GenerationBridge:
    """
    代际差异桥接器
    
    帮助优化内容在不同世代受众之间的有效传播，通过转换代际特定的文化参考、
    流行语、表达方式和梗，使内容更容易被目标世代理解和接受。
    """
    
    # 默认代际参考点映射
    REFERENCE_POINTS = {
        "Z世代": ["二次元", "整片化", "玩梗", "原神", "鬼畜", "嘎嘎猛", "绝绝子", "笑死", "yyds", "破防", "真香"],
        "90后": ["QQ空间", "非主流", "贴吧", "神曲", "LOL", "微博", "秒懂", "蓝瘦香菇", "小鲜肉", "接地气"],
        "80后": ["怀旧", "经典款", "长叙事", "童年", "港台文化", "流行歌", "青春", "小时候", "成长", "老歌"],
        "70后": ["岁月", "老故事", "传统", "经典", "价值观", "文化底蕴", "电视剧", "集体记忆", "怀旧金曲", "年代感"],
        "60后": ["传统文化", "历史", "国产", "老电影", "相声", "戏曲", "年代剧", "红色经典", "革命故事", "集体主义"]
    }
    
    # 世代之间的共同参考点映射（辅助跨代翻译）
    COMMON_REFERENCES = {
        ("Z世代", "90后"): ["网络文化", "电子游戏", "手机APP", "短视频"],
        ("90后", "80后"): ["校园生活", "青春回忆", "成长烦恼", "偶像文化"],
        ("80后", "70后"): ["家庭观念", "工作态度", "社会变迁", "传统价值"]
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化代际差异桥接器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化文化适配器
        self.culture_adapter = CultureAdapter()
        
        # 初始化文本处理器
        self.text_processor = TextProcessor()
        
        # 加载代际表达映射
        self._load_generation_mappings()
        
        generation_logger.info("代际差异桥接器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            "adaptation_level": 0.7,  # 代际适配强度，0-1之间
            "preserve_core_meaning": True,  # 保留核心含义
            "translate_slang": True,  # 转换俚语/流行语
            "translate_references": True,  # 转换文化参考
            "translate_memes": True,  # 转换梗
            "add_explanations": False,  # 为目标代际添加解释
            "explanation_style": "parentheses",  # 解释样式：parentheses, footnote
            "generation_definitions": {
                "Z世代": {"birth_years": [2000, 2015], "also_known_as": ["00后", "10后", "Z时代"]},
                "90后": {"birth_years": [1990, 1999], "also_known_as": ["90后"]},
                "80后": {"birth_years": [1980, 1989], "also_known_as": ["80后"]},
                "70后": {"birth_years": [1970, 1979], "also_known_as": ["70后"]},
                "60后": {"birth_years": [1960, 1969], "also_known_as": ["60后"]}
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                default_config.update(config)
                generation_logger.info(f"从{config_path}加载配置文件成功")
            except Exception as e:
                generation_logger.error(f"加载配置文件失败: {str(e)}")
                
        return default_config
    
    def _load_generation_mappings(self):
        """
        加载代际表达映射数据
        """
        self.generation_maps = {}
        
        # 预定义的基础映射
        base_mappings = {
            ("Z世代", "80后"): {
                "二次元": "动漫",
                "yyds": "最棒的",
                "绝绝子": "太厉害了",
                "破防": "受打击",
                "真香": "真的很不错",
                "鬼畜": "搞笑视频",
                "整片化": "完整观看",
                "原神": "热门游戏",
                "嘎嘎猛": "非常厉害",
                "笑死": "很好笑"
            },
            ("80后", "Z世代"): {
                "非主流": "独特风格",
                "贴吧": "网络论坛",
                "QQ空间": "社交平台",
                "小时候": "童年",
                "怀旧": "复古",
                "90年代": "老旧时期",
                "老歌": "经典歌曲",
                "港台": "香港台湾",
                "长篇故事": "长内容"
            }
        }
        
        # 扩展到所有代际组合
        generations = list(self.REFERENCE_POINTS.keys())
        for i, gen1 in enumerate(generations):
            for j, gen2 in enumerate(generations):
                if i != j:
                    key = (gen1, gen2)
                    
                    # 查找是否有预定义映射
                    if key in base_mappings:
                        self.generation_maps[key] = base_mappings[key]
                    elif (gen2, gen1) in base_mappings:
                        # 创建反向映射
                        self.generation_maps[key] = {v: k for k, v in base_mappings[(gen2, gen1)].items()}
                    else:
                        # 创建空映射
                        self.generation_maps[key] = {}
        
        # 尝试从文件加载更多映射
        try:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'generation'
            if not data_dir.exists():
                data_dir.mkdir(parents=True, exist_ok=True)
                
            # 检查是否有映射文件存在
            for gen1 in generations:
                for gen2 in generations:
                    if gen1 != gen2:
                        file_path = data_dir / f"{gen1}_to_{gen2}.json"
                        
                        if file_path.exists():
                            with open(file_path, 'r', encoding='utf-8') as f:
                                additional_map = json.load(f)
                                
                            key = (gen1, gen2)
                            if key in self.generation_maps:
                                self.generation_maps[key].update(additional_map)
                            else:
                                self.generation_maps[key] = additional_map
                                
                            generation_logger.info(f"从{file_path}加载了{len(additional_map)}个代际表达映射")
        except Exception as e:
            generation_logger.warning(f"加载代际映射文件失败: {str(e)}")
    
    def bridge_gap(self, content: Dict[str, Any], target_gen: str) -> Dict[str, Any]:
        """
        弥合不同世代之间的代际差异
        
        将内容中的代际特定表达转换为目标世代更容易理解的形式，
        优化跨代际内容传播效果。
        
        Args:
            content: 需要转换的内容
            target_gen: 目标世代，例如 "Z世代", "80后" 等
            
        Returns:
            转换后的内容
        """
        generation_logger.info(f"开始将内容转换为{target_gen}风格")
        
        # 检查目标世代是否有效
        if target_gen not in self.REFERENCE_POINTS:
            generation_logger.warning(f"未知的目标世代: {target_gen}，使用默认世代")
            target_gen = list(self.REFERENCE_POINTS.keys())[0]
        
        # 创建内容副本
        result = copy.deepcopy(content)
        
        # 检测源内容的世代倾向
        source_gen = self._detect_generation(content)
        generation_logger.debug(f"检测到源内容世代倾向: {source_gen}")
        
        # 如果源世代和目标世代相同，无需转换
        if source_gen == target_gen:
            generation_logger.info("源世代与目标世代相同，无需转换")
            return result
        
        # 获取目标世代的参考点
        target_references = self.REFERENCE_POINTS[target_gen]
        
        # 应用代际转换
        result = self._transform_to_generation(result, source_gen, target_gen)
        
        generation_logger.info(f"内容成功转换为{target_gen}风格")
        return result
    
    def _detect_generation(self, content: Dict[str, Any]) -> str:
        """
        检测内容的世代倾向
        
        根据内容中的关键词和表达方式，判断内容更接近哪个世代
        
        Args:
            content: 内容数据
            
        Returns:
            检测到的世代标识
        """
        # 提取所有文本
        text_content = self._extract_text_content(content)
        
        # 计算每个世代的匹配分数
        scores = {}
        for generation, references in self.REFERENCE_POINTS.items():
            score = 0
            for ref in references:
                if ref in text_content:
                    score += 1
            
            # 归一化分数
            if references:
                scores[generation] = score / len(references)
            else:
                scores[generation] = 0
        
        # 找出得分最高的世代
        if scores:
            max_gen = max(scores.items(), key=lambda x: x[1])
            if max_gen[1] > 0:
                return max_gen[0]
        
        # 默认返回中间代际
        return list(self.REFERENCE_POINTS.keys())[len(self.REFERENCE_POINTS) // 2]
    
    def _extract_text_content(self, content: Dict[str, Any]) -> str:
        """
        从内容中提取所有文本
        
        Args:
            content: 内容数据
            
        Returns:
            合并后的文本
        """
        text_parts = []
        
        # 提取标题
        if "title" in content and isinstance(content["title"], str):
            text_parts.append(content["title"])
        
        # 提取描述
        if "description" in content and isinstance(content["description"], str):
            text_parts.append(content["description"])
        
        # 提取对话
        if "dialogues" in content and isinstance(content["dialogues"], list):
            for dialogue in content["dialogues"]:
                if isinstance(dialogue, dict) and "text" in dialogue:
                    text_parts.append(dialogue["text"])
        
        # 提取场景描述
        if "scenes" in content and isinstance(content["scenes"], list):
            for scene in content["scenes"]:
                if isinstance(scene, dict):
                    if "description" in scene:
                        text_parts.append(scene["description"])
                    
                    # 提取场景元素内容
                    if "elements" in scene and isinstance(scene["elements"], list):
                        for element in scene["elements"]:
                            if isinstance(element, dict) and "content" in element:
                                text_parts.append(element["content"])
        
        # 合并所有文本
        return ' '.join(text_parts)
    
    def _transform_to_generation(self, content: Dict[str, Any], source_gen: str, target_gen: str) -> Dict[str, Any]:
        """
        将内容转换为目标世代风格
        
        Args:
            content: 内容数据
            source_gen: 源世代
            target_gen: 目标世代
            
        Returns:
            转换后的内容
        """
        result = copy.deepcopy(content)
        
        # 获取世代间映射
        generation_map = self.generation_maps.get((source_gen, target_gen), {})
        
        # 处理标题和描述
        if "title" in result and isinstance(result["title"], str):
            result["title"] = self._transform_text(result["title"], generation_map, source_gen, target_gen)
        
        if "description" in result and isinstance(result["description"], str):
            result["description"] = self._transform_text(result["description"], generation_map, source_gen, target_gen)
        
        # 处理对话
        if "dialogues" in result and isinstance(result["dialogues"], list):
            for dialogue in result["dialogues"]:
                if isinstance(dialogue, dict) and "text" in dialogue:
                    dialogue["text"] = self._transform_text(dialogue["text"], generation_map, source_gen, target_gen)
        
        # 处理场景
        if "scenes" in result and isinstance(result["scenes"], list):
            for scene in result["scenes"]:
                if isinstance(scene, dict):
                    # 处理场景描述
                    if "description" in scene:
                        scene["description"] = self._transform_text(scene["description"], generation_map, source_gen, target_gen)
                    
                    # 处理场景元素
                    if "elements" in scene and isinstance(scene["elements"], list):
                        for element in scene["elements"]:
                            if isinstance(element, dict) and "content" in element:
                                element["content"] = self._transform_text(element["content"], generation_map, source_gen, target_gen)
        
        # 添加代际转换标记
        result["generation_adaptation"] = {
            "source_generation": source_gen,
            "target_generation": target_gen,
            "adaptation_level": self.config["adaptation_level"]
        }
        
        return result
    
    def _transform_text(self, text: str, generation_map: Dict[str, str], source_gen: str, target_gen: str) -> str:
        """
        转换单个文本
        
        Args:
            text: 原始文本
            generation_map: 世代映射字典
            source_gen: 源世代
            target_gen: 目标世代
            
        Returns:
            转换后的文本
        """
        if not text:
            return text
        
        result = text
        
        # 1. 应用直接词汇映射
        for source_term, target_term in generation_map.items():
            # 使用正则表达式确保匹配完整词汇
            pattern = r'\b' + re.escape(source_term) + r'\b'
            result = re.sub(pattern, target_term, result)
        
        # 2. 添加解释（如果配置启用）
        if self.config["add_explanations"]:
            # 识别源世代特有的词汇和表达
            source_unique_terms = set(self.REFERENCE_POINTS[source_gen]) - set(self.REFERENCE_POINTS[target_gen])
            
            for term in source_unique_terms:
                if term in result and term in generation_map:
                    explanation = generation_map[term]
                    
                    # 根据配置选择解释样式
                    if self.config["explanation_style"] == "parentheses":
                        pattern = r'\b' + re.escape(term) + r'\b'
                        replacement = f"{term}（{explanation}）"
                        result = re.sub(pattern, replacement, result, count=1)  # 只替换第一次出现
                
        # 3. 调整表达风格
        # 为不同世代应用不同的表达风格转换
        if target_gen == "Z世代":
            result = self._apply_z_generation_style(result)
        elif target_gen == "80后":
            result = self._apply_80s_style(result)
        elif target_gen == "90后":
            result = self._apply_90s_style(result)
        
        return result
    
    def _apply_z_generation_style(self, text: str) -> str:
        """
        应用Z世代表达风格
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        # Z世代风格特点：简短、直接、使用流行词
        result = text
        
        # 1. 增加一些Z世代常用语气词（如果原文较长）
        if len(text) > 50 and not any(term in text for term in ["绝绝子", "yyds", "笑死", "破防"]):
            z_expressions = ["绝绝子", "yyds", "笑死", "破防", "真香", "太可了", "无语子"]
            import random
            
            # 在句末随机添加Z世代表达
            sentences = re.split(r'([.!?。！？])', result)
            if len(sentences) >= 3:  # 至少有一个完整句子
                insert_idx = random.randrange(0, len(sentences) - 2, 2)  # 只在句子内容位置插入
                z_expr = random.choice(z_expressions)
                
                if sentences[insert_idx].strip():
                    sentences[insert_idx] = sentences[insert_idx] + "，" + z_expr
                
                result = ''.join(sentences)
        
        # 2. 缩短冗长表达
        result = re.sub(r'非常非常', '超级', result)
        result = re.sub(r'我认为这个是', '这个是', result)
        
        # 3. 增加表情符号（如果原文没有）
        if "！" in result and not any(emoji in result for emoji in ["😂", "🤣", "👍", "🔥"]):
            result = result.replace("！", "！🔥", 1)
        
        return result
    
    def _apply_80s_style(self, text: str) -> str:
        """
        应用80后表达风格
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        # 80后风格特点：略显怀旧，叙事性强，正式一些
        result = text
        
        # 1. 增加叙事性和过渡词
        result = re.sub(r'^这个', '其实这个', result)
        result = re.sub(r'^我', '说实话，我', result)
        
        # 2. 降低过度夸张表达
        result = re.sub(r'绝绝子', '非常好', result)
        result = re.sub(r'yyds', '经典', result)
        result = re.sub(r'太可了', '很棒', result)
        
        # 3. 移除过多表情符号
        for emoji in ["😂", "🤣", "👍", "🔥", "💯", "🤦‍♀️", "🤷‍♂️"]:
            if emoji in result:
                result = result.replace(emoji, "", result.count(emoji) - 1)  # 保留一个
        
        return result
    
    def _apply_90s_style(self, text: str) -> str:
        """
        应用90后表达风格
        
        Args:
            text: 原始文本
            
        Returns:
            转换后的文本
        """
        # 90后风格：介于80后和Z世代之间，使用部分网络用语但保持一定叙事性
        result = text
        
        # 1. 调整语气
        result = re.sub(r'^', '嗯，', result, count=1)
        result = re.sub(r'绝绝子', '很赞', result)
        result = re.sub(r'yyds', '永远的神', result)
        
        # 2. 适度添加表情符号
        if "！" in result and not any(emoji in result for emoji in ["😊", "👍"]):
            result = result.replace("！", "！👍", 1)
        
        return result


def insert_cultural_elements(content: Dict[str, Any], cultural_references: List[str]) -> Dict[str, Any]:
    """
    在内容中插入文化元素
    
    向内容中添加特定世代的文化参考和表达，增强世代特色
    
    Args:
        content: 原始内容
        cultural_references: 文化参考列表
        
    Returns:
        添加文化元素后的内容
    """
    result = copy.deepcopy(content)
    
    # 提取关键位置用于插入文化元素
    insertion_points = []
    
    # 检查对话
    if "dialogues" in result and isinstance(result["dialogues"], list):
        for i, dialogue in enumerate(result["dialogues"]):
            if isinstance(dialogue, dict) and "text" in dialogue and len(dialogue["text"]) > 10:
                insertion_points.append(("dialogues", i))
    
    # 检查场景
    if "scenes" in result and isinstance(result["scenes"], list):
        for i, scene in enumerate(result["scenes"]):
            if isinstance(scene, dict):
                # 场景描述
                if "description" in scene and len(scene["description"]) > 10:
                    insertion_points.append(("scenes_desc", i))
                
                # 场景元素
                if "elements" in scene and isinstance(scene["elements"], list):
                    for j, element in enumerate(scene["elements"]):
                        if isinstance(element, dict) and "content" in element and len(element["content"]) > 10:
                            insertion_points.append(("elements", (i, j)))
    
    # 如果没有找到合适的插入点，返回原内容
    if not insertion_points:
        return result
    
    # 随机选择一些插入点
    import random
    num_insertions = min(len(cultural_references), len(insertion_points) // 2 + 1)
    selected_points = random.sample(insertion_points, num_insertions)
    
    # 执行插入
    for i, (point_type, indices) in enumerate(selected_points):
        if i < len(cultural_references):
            reference = cultural_references[i]
            
            if point_type == "dialogues":
                idx = indices
                dialogue = result["dialogues"][idx]
                dialogue["text"] = _insert_reference_into_text(dialogue["text"], reference)
            
            elif point_type == "scenes_desc":
                idx = indices
                scene = result["scenes"][idx]
                scene["description"] = _insert_reference_into_text(scene["description"], reference)
            
            elif point_type == "elements":
                scene_idx, elem_idx = indices
                element = result["scenes"][scene_idx]["elements"][elem_idx]
                element["content"] = _insert_reference_into_text(element["content"], reference)
    
    return result


def _insert_reference_into_text(text: str, reference: str) -> str:
    """
    在文本中插入文化参考
    
    Args:
        text: 原始文本
        reference: 要插入的文化参考
        
    Returns:
        插入后的文本
    """
    # 如果文本已包含该参考，则不再插入
    if reference in text:
        return text
    
    # 将文本分割成句子
    sentences = re.split(r'([.!?。！？])', text)
    
    # 如果文本很短，直接附加
    if len(sentences) <= 2:
        return f"{text} {reference}"
    
    # 创建插入模板
    templates = [
        f"就像{reference}一样，",
        f"这让我想起了{reference}，",
        f"有点{reference}的感觉，",
        f"跟{reference}很像，"
    ]
    
    import random
    template = random.choice(templates)
    
    # 找到合适的位置插入（句子开头）
    for i in range(2, len(sentences), 2):
        if sentences[i].strip():
            sentences[i] = template + sentences[i]
            break
    else:
        # 如果没有找到合适位置，附加到最后
        sentences[-1] = sentences[-1] + f" {reference}"
    
    return ''.join(sentences)


# 创建单例对象
_generation_bridge = None

def get_generation_bridge() -> GenerationBridge:
    """
    获取代际差异桥接器实例
    
    Returns:
        GenerationBridge: 代际差异桥接器实例
    """
    global _generation_bridge
    if _generation_bridge is None:
        _generation_bridge = GenerationBridge()
    return _generation_bridge


def bridge_gap(content: Dict[str, Any], target_gen: str) -> Dict[str, Any]:
    """
    弥合不同世代之间的代际差异的便捷函数
    
    Args:
        content: 需要转换的内容
        target_gen: 目标世代，例如 "Z世代", "80后" 等
        
    Returns:
        转换后的内容
    """
    bridge = get_generation_bridge()
    return bridge.bridge_gap(content, target_gen)


def detect_content_generation(content: Dict[str, Any]) -> str:
    """
    检测内容的世代风格
    
    Args:
        content: 内容数据
        
    Returns:
        检测到的世代标识
    """
    bridge = get_generation_bridge()
    return bridge._detect_generation(content) 