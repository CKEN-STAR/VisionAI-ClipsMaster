#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器独立演示脚本

这是一个完全独立的脚本，直接加载GenerationBridge类而不依赖其他模块。
"""

import os
import sys
import json
import copy
import re
import random
from typing import Dict, List, Any, Optional, Tuple, Union

# 直接定义必要的类，跳过导入
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
    
    def __init__(self):
        """初始化代际差异桥接器"""
        # 简化版配置
        self.config = {
            "adaptation_level": 0.7,
            "add_explanations": False,
            "explanation_style": "parentheses"
        }
        
        # 加载代际表达映射
        self.generation_maps = self._load_generation_mappings()
        
        print("[INFO] 代际差异桥接器初始化完成")
    
    def _load_generation_mappings(self):
        """加载代际表达映射数据"""
        generation_maps = {}
        
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
                        generation_maps[key] = base_mappings[key]
                    elif (gen2, gen1) in base_mappings:
                        # 创建反向映射
                        generation_maps[key] = {v: k for k, v in base_mappings[(gen2, gen1)].items()}
                    else:
                        # 创建空映射
                        generation_maps[key] = {}
        
        return generation_maps
    
    def bridge_gap(self, content: Dict[str, Any], target_gen: str) -> Dict[str, Any]:
        """弥合不同世代之间的代际差异"""
        print(f"[INFO] 开始将内容转换为{target_gen}风格")
        
        # 检查目标世代是否有效
        if target_gen not in self.REFERENCE_POINTS:
            print(f"[WARNING] 未知的目标世代: {target_gen}，使用默认世代")
            target_gen = list(self.REFERENCE_POINTS.keys())[0]
        
        # 创建内容副本
        result = copy.deepcopy(content)
        
        # 检测源内容的世代倾向
        source_gen = self._detect_generation(content)
        print(f"[DEBUG] 检测到源内容世代倾向: {source_gen}")
        
        # 如果源世代和目标世代相同，无需转换
        if source_gen == target_gen:
            print("[INFO] 源世代与目标世代相同，无需转换")
            return result
        
        # 应用代际转换
        result = self._transform_to_generation(result, source_gen, target_gen)
        
        print(f"[INFO] 内容成功转换为{target_gen}风格")
        return result
    
    def _detect_generation(self, content: Dict[str, Any]) -> str:
        """检测内容的世代倾向"""
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
        """从内容中提取所有文本"""
        text_parts = []
        
        # 提取标题和描述
        if "title" in content and isinstance(content["title"], str):
            text_parts.append(content["title"])
        
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
        """将内容转换为目标世代风格"""
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
        """转换单个文本"""
        if not text:
            return text
        
        result = text
        
        # 1. 应用直接词汇映射
        for source_term, target_term in generation_map.items():
            # 使用正则表达式确保匹配完整词汇
            pattern = r'\b' + re.escape(source_term) + r'\b'
            result = re.sub(pattern, target_term, result)
        
        # 2. 调整表达风格
        if target_gen == "Z世代":
            result = self._apply_z_generation_style(result)
        elif target_gen == "80后":
            result = self._apply_80s_style(result)
        elif target_gen == "90后":
            result = self._apply_90s_style(result)
        
        return result
    
    def _apply_z_generation_style(self, text: str) -> str:
        """应用Z世代表达风格"""
        # Z世代风格特点：简短、直接、使用流行词
        result = text
        
        # 1. 增加一些Z世代常用语气词（如果原文较长）
        if len(text) > 50 and not any(term in text for term in ["绝绝子", "yyds", "笑死", "破防"]):
            z_expressions = ["绝绝子", "yyds", "笑死", "破防", "真香", "太可了", "无语子"]
            
            # 在句末随机添加Z世代表达
            sentences = re.split(r'([.!?。！？])', result)
            if len(sentences) >= 3:  # 至少有一个完整句子
                try:
                    insert_idx = random.randrange(0, len(sentences) - 2, 2)  # 只在句子内容位置插入
                    z_expr = random.choice(z_expressions)
                    
                    if sentences[insert_idx].strip():
                        sentences[insert_idx] = sentences[insert_idx] + "，" + z_expr
                    
                    result = ''.join(sentences)
                except ValueError:
                    # 如果随机索引生成出错，直接在文本末尾添加
                    result = result + "，" + random.choice(z_expressions)
        
        # 2. 缩短冗长表达
        result = re.sub(r'非常非常', '超级', result)
        
        # 3. 增加表情符号（如果原文没有）
        if "！" in result and not any(emoji in result for emoji in ["😂", "🤣", "👍", "🔥"]):
            result = result.replace("！", "！🔥", 1)
        
        return result
    
    def _apply_80s_style(self, text: str) -> str:
        """应用80后表达风格"""
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
        for emoji in ["😂", "🤣", "👍", "🔥"]:
            if emoji in result:
                result = result.replace(emoji, "", result.count(emoji) - 1)  # 保留一个
        
        return result
    
    def _apply_90s_style(self, text: str) -> str:
        """应用90后表达风格"""
        # 90后风格：介于80后和Z世代之间
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
    """在内容中插入文化元素"""
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
    """在文本中插入文化参考"""
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


# 主函数
def main():
    """主函数，执行演示"""
    print("=" * 50)
    print("代际差异桥接器独立演示")
    print("=" * 50)
    
    # 创建桥接器实例
    bridge = GenerationBridge()
    
    # 示例内容
    z_gen_content = {
        "title": "二次元动漫角色大盘点",
        "description": "这些角色简直绝绝子，太可了，我直接笑死！",
        "dialogues": [
            {"speaker": "narrator", "text": "这些梗真是太香了，yyds！"},
            {"speaker": "presenter", "text": "直接一整个无语子，破防了家人们！"}
        ],
        "scenes": [
            {
                "id": "scene_1",
                "description": "玩梗时刻，满屏yyds",
                "elements": [
                    {"type": "text", "content": "这个角色也太A了，破防了"}
                ]
            }
        ]
    }
    
    gen80_content = {
        "title": "怀旧经典动画角色回顾",
        "description": "这些角色陪伴了我们的童年，满满的回忆",
        "dialogues": [
            {"speaker": "narrator", "text": "这些经典角色真是满满的回忆啊"},
            {"speaker": "presenter", "text": "那个年代的动画真是越看越有味道"}
        ],
        "scenes": [
            {
                "id": "scene_1",
                "description": "经典港台动画，长篇叙事",
                "elements": [
                    {"type": "text", "content": "小时候最喜欢看的卡通形象"}
                ]
            }
        ]
    }
    
    # 1. 检测世代
    print("\n1. 测试代际检测:")
    
    z_detected = bridge._detect_generation(z_gen_content)
    print(f"Z世代内容检测结果: {z_detected}")
    
    gen80_detected = bridge._detect_generation(gen80_content)
    print(f"80后内容检测结果: {gen80_detected}")
    
    # 2. 代际转换
    print("\n2. 测试代际转换:")
    
    # Z世代 -> 80后
    z_to_80 = bridge.bridge_gap(z_gen_content, "80后")
    print(f"\nZ世代 -> 80后转换结果:")
    print(f"原始标题: {z_gen_content['title']}")
    print(f"转换标题: {z_to_80['title']}")
    print(f"原始描述: {z_gen_content['description']}")
    print(f"转换描述: {z_to_80['description']}")
    print(f"原始对话: {z_gen_content['dialogues'][0]['text']}")
    print(f"转换对话: {z_to_80['dialogues'][0]['text']}")
    
    # 80后 -> Z世代
    gen80_to_z = bridge.bridge_gap(gen80_content, "Z世代")
    print(f"\n80后 -> Z世代转换结果:")
    print(f"原始标题: {gen80_content['title']}")
    print(f"转换标题: {gen80_to_z['title']}")
    print(f"原始描述: {gen80_content['description']}")
    print(f"转换描述: {gen80_to_z['description']}")
    print(f"原始对话: {gen80_content['dialogues'][0]['text']}")
    print(f"转换对话: {gen80_to_z['dialogues'][0]['text']}")
    
    # 3. 文化元素插入
    print("\n3. 测试文化元素插入:")
    
    # 创建通用内容
    generic_content = {
        "title": "动画角色分析",
        "description": "探讨几个经典动画角色的特点",
        "dialogues": [
            {"speaker": "narrator", "text": "动画角色的设计反映了时代特征。这些角色各有风格，表达方式也不同。有的朝气蓬勃，有的成熟稳重。"}
        ]
    }
    
    # 插入Z世代文化元素
    z_elements = ["二次元", "yyds", "整片化"]
    z_enhanced = insert_cultural_elements(generic_content, z_elements)
    
    print(f"原始文本: {generic_content['dialogues'][0]['text']}")
    print(f"添加Z世代元素后: {z_enhanced['dialogues'][0]['text']}")
    
    # 4. 代际风格应用
    print("\n4. 测试代际风格应用:")
    
    test_text = "这些动画角色设计很好，讲述了生动的故事，值得大家一看"
    
    z_styled = bridge._apply_z_generation_style(test_text)
    gen80_styled = bridge._apply_80s_style(test_text)
    gen90_styled = bridge._apply_90s_style(test_text)
    
    print(f"原始文本: {test_text}")
    print(f"Z世代风格: {z_styled}")
    print(f"80后风格: {gen80_styled}")
    print(f"90后风格: {gen90_styled}")
    
    print("\n演示完成!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"演示出错: {str(e)}")
        traceback.print_exc() 