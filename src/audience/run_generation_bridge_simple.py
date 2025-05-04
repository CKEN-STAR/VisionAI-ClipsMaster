#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代际差异桥接器简易运行脚本

完全自包含的脚本，不依赖于任何外部模块，可以直接运行。
包含代际差异桥接器的核心实现和简单演示。
"""

import re
import copy
import random
import sys
from typing import Dict, List, Any, Optional, Tuple, Union

print("代际差异桥接器简易演示")
print("=" * 50)

class GenerationBridge:
    """
    代际差异桥接器
    """
    
    # 默认代际参考点映射
    REFERENCE_POINTS = {
        "Z世代": ["二次元", "整片化", "玩梗", "原神", "鬼畜", "嘎嘎猛", "绝绝子", "笑死", "yyds", "破防", "真香"],
        "90后": ["QQ空间", "非主流", "贴吧", "神曲", "LOL", "微博", "秒懂", "蓝瘦香菇", "小鲜肉", "接地气"],
        "80后": ["怀旧", "经典款", "长叙事", "童年", "港台文化", "流行歌", "青春", "小时候", "成长", "老歌"],
        "70后": ["岁月", "老故事", "传统", "经典", "价值观", "文化底蕴", "电视剧", "集体记忆", "怀旧金曲", "年代感"]
    }
    
    def __init__(self):
        """初始化代际差异桥接器"""
        # 配置
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


def insert_cultural_elements(content: Dict[str, Any], cultural_references: List[str], bridge: GenerationBridge) -> Dict[str, Any]:
    """在内容中插入文化元素"""
    print(f"[INFO] 正在插入文化元素: {cultural_references}")
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
        print("[WARNING] 未找到合适的文化元素插入点")
        return result
    
    print(f"[INFO] 找到 {len(insertion_points)} 个可能的插入点")
    
    # 随机选择一些插入点
    num_insertions = min(len(cultural_references), len(insertion_points) // 2 + 1)
    selected_points = random.sample(insertion_points, num_insertions)
    
    print(f"[INFO] 将在 {num_insertions} 个位置插入文化元素")
    
    # 执行插入
    for i, (point_type, indices) in enumerate(selected_points):
        if i < len(cultural_references):
            reference = cultural_references[i]
            
            try:
                if point_type == "dialogues":
                    idx = indices
                    dialogue = result["dialogues"][idx]
                    original = dialogue["text"]
                    dialogue["text"] = _insert_reference_into_text(dialogue["text"], reference)
                    print(f"[INFO] 对话插入: '{original}' -> '{dialogue['text']}'")
                
                elif point_type == "scenes_desc":
                    idx = indices
                    scene = result["scenes"][idx]
                    original = scene["description"]
                    scene["description"] = _insert_reference_into_text(scene["description"], reference)
                    print(f"[INFO] 场景描述插入: '{original}' -> '{scene['description']}'")
                
                elif point_type == "elements":
                    scene_idx, elem_idx = indices
                    element = result["scenes"][scene_idx]["elements"][elem_idx]
                    original = element["content"]
                    element["content"] = _insert_reference_into_text(element["content"], reference)
                    print(f"[INFO] 元素内容插入: '{original}' -> '{element['content']}'")
            except Exception as e:
                print(f"[ERROR] 插入文化元素时出错: {str(e)}")
    
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
    try:
        inserted = False
        for i in range(2, min(len(sentences), 10), 2):
            if i < len(sentences) and sentences[i].strip():
                sentences[i] = template + sentences[i]
                inserted = True
                break
        
        # 如果没有找到合适位置，附加到最后
        if not inserted:
            sentences[-1] = sentences[-1] + f" {reference}"
        
        return ''.join(sentences)
    except Exception as e:
        print(f"[ERROR] 文本插入失败: {str(e)}, 直接附加")
        return f"{text} {reference}"


# 创建测试内容
def create_test_contents():
    # Z世代内容
    z_gen_content = {
        "title": "二次元动漫角色大盘点",
        "description": "这些角色简直绝绝子，太可了，我直接笑死！",
        "scenes": [
            {
                "id": "scene_1", 
                "description": "玩梗时刻，满屏yyds",
                "elements": [
                    {"type": "text", "content": "这个角色也太A了，破防了"},
                    {"type": "image", "source": "meme.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "整片化的原神场景",
                "elements": [
                    {"type": "video", "content": "原神游戏中最嘎嘎猛的时刻"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "这些梗真是太香了，yyds！"},
            {"speaker": "presenter", "text": "直接一整个无语子，破防了家人们！"}
        ]
    }
    
    # 80后内容
    gen80_content = {
        "title": "怀旧经典动画角色回顾",
        "description": "这些角色陪伴了我们的童年，满满的回忆",
        "scenes": [
            {
                "id": "scene_1",
                "description": "经典港台动画，长篇叙事",
                "elements": [
                    {"type": "text", "content": "小时候最喜欢看的卡通形象"},
                    {"type": "image", "source": "classic.png"}
                ]
            },
            {
                "id": "scene_2",
                "description": "青春记忆，经典款角色",
                "elements": [
                    {"type": "video", "content": "80年代最流行的动画角色"}
                ]
            }
        ],
        "dialogues": [
            {"speaker": "narrator", "text": "这些经典角色真是满满的回忆啊"},
            {"speaker": "presenter", "text": "那个年代的动画真是越看越有味道"}
        ]
    }
    
    return {"Z世代": z_gen_content, "80后": gen80_content}


def print_content_summary(content, label="内容"):
    """打印内容摘要"""
    print(f"\n{label}摘要:")
    print(f"标题: {content.get('title', '无标题')}")
    print(f"描述: {content.get('description', '无描述')}")
    
    if "dialogues" in content and content["dialogues"]:
        print(f"对话示例: {content['dialogues'][0].get('text', '无内容')}")
    
    if "scenes" in content and content["scenes"]:
        print(f"场景描述: {content['scenes'][0].get('description', '无描述')}")
        if "elements" in content["scenes"][0] and content["scenes"][0]["elements"]:
            print(f"元素内容: {content['scenes'][0]['elements'][0].get('content', '无内容')}")


def main():
    """主函数"""
    try:
        print("\n===== 开始代际差异桥接器演示 =====")
        
        # 创建桥接器实例
        bridge = GenerationBridge()
        
        # 创建测试内容
        print("\n创建测试内容...")
        contents = create_test_contents()
        print(f"成功创建 {len(contents)} 个测试内容")
        
        # 1. 检测内容的代际倾向
        print("\n1. 检测内容代际倾向:")
        for gen_name, content in contents.items():
            detected = bridge._detect_generation(content)
            print(f"- {gen_name}内容的检测结果: {detected}")
        
        # 2. 代际转换示例
        print("\n2. 代际转换示例:")
        
        # Z世代 -> 80后
        z_to_80 = bridge.bridge_gap(contents["Z世代"], "80后")
        print("\nZ世代 -> 80后 转换:")
        print_content_summary(contents["Z世代"], "原始Z世代内容")
        print_content_summary(z_to_80, "转换为80后风格后")
        
        # 80后 -> Z世代
        gen80_to_z = bridge.bridge_gap(contents["80后"], "Z世代")
        print("\n80后 -> Z世代 转换:")
        print_content_summary(contents["80后"], "原始80后内容") 
        print_content_summary(gen80_to_z, "转换为Z世代风格后")
        
        # 3. 插入文化元素
        print("\n3. 文化元素插入示例:")
        
        # 创建通用内容
        generic_content = {
            "title": "动画角色分析",
            "description": "探讨几个经典动画角色的特点",
            "scenes": [
                {
                    "id": "scene_1",
                    "description": "展示不同角色类型",
                    "elements": [
                        {"type": "text", "content": "这些角色各有不同的设计理念"}
                    ]
                }
            ],
            "dialogues": [
                {"speaker": "narrator", "text": "动画角色的设计反映了时代特征"}
            ]
        }
        
        # 向通用内容中插入Z世代文化元素
        z_elements = ["二次元", "yyds", "破防"]
        z_enhanced = insert_cultural_elements(generic_content, z_elements, bridge)
        print_content_summary(generic_content, "原始通用内容")
        print_content_summary(z_enhanced, "添加Z世代元素后")
        
        # 4. 世代风格应用
        print("\n4. 世代风格应用示例:")
        
        # 测试文本样本
        test_text = "这些动画角色设计很好，值得一看"
        
        # 应用不同世代风格
        z_styled = bridge._apply_z_generation_style(test_text)
        gen80_styled = bridge._apply_80s_style(test_text)
        gen90_styled = bridge._apply_90s_style(test_text)
        
        print(f"原始文本: {test_text}")
        print(f"Z世代风格: {z_styled}")
        print(f"80后风格: {gen80_styled}")
        print(f"90后风格: {gen90_styled}")
        
        print("\n===== 代际差异桥接器演示完成 =====")
        
    except Exception as e:
        import traceback
        print(f"演示过程中发生错误: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    main() 