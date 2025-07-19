"""
悬念植入器

负责在叙事中策略性地植入悬念线索，增强观众观看体验
通过提前揭示关键信息，创造期待感和叙事张力
"""

import logging
import random
import re
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union, Set

from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.utils.validators import validate_float_range

# 创建日志记录器
logger = logging.getLogger("suspense_planter")

class ClueType(Enum):
    """悬念线索类型枚举"""
    VISUAL_DETAIL = "visual_detail"     # 视觉线索（道具特写）
    DIALOG_HINT = "dialog_hint"         # 台词暗示（双关语）
    AUDIO_CUE = "audio_cue"             # 声效铺垫（环境音效）
    CHARACTER_SECRET = "character_secret" # 角色秘密（隐藏动机）
    FORESHADOWING = "foreshadowing"     # 剧情伏笔（未来事件暗示）
    RED_HERRING = "red_herring"         # 误导线索（转移注意力）


class SuspensePlanter:
    """悬念植入器，在剧本中植入悬念和伏笔"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化悬念植入器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 初始化线索模板库
        self.clue_templates = {
            ClueType.VISUAL_DETAIL: [
                "镜头短暂停留在{prop}上",
                "{character}的视线扫过{prop}",
                "特写：{prop}被{character}注意到",
                "背景中若隐若现的{prop}",
                "{prop}在光线下若隐若现"
            ],
            ClueType.DIALOG_HINT: [
                "「{character}：{hint_dialog}」",
                "「{character}看似随意地提到：{hint_dialog}」",
                "「{character}突然说道：{hint_dialog}」",
                "「{character}：（意味深长地）{hint_dialog}」",
                "「{character}低声说：{hint_dialog}」"
            ],
            ClueType.AUDIO_CUE: [
                "背景传来{sound}声",
                "远处隐约听到{sound}",
                "{sound}声若有若无",
                "当{character}说话时，{sound}声突然响起",
                "场景转换，{sound}声从远到近"
            ],
            ClueType.CHARACTER_SECRET: [
                "{character}偷偷{secret_action}",
                "当没人注意时，{character}{secret_action}",
                "{character}表情变化，似乎在隐瞒什么",
                "{character}避开其他人的视线，{secret_action}",
                "特写：{character}的眼神透露出秘密"
            ],
            ClueType.FORESHADOWING: [
                "{character}无意中提到{future_event}",
                "画面闪回：预示{future_event}的片段",
                "{character}做了个预示{future_event}的梦",
                "背景中的电视/广播提到类似{future_event}的事",
                "镜头扫过暗示{future_event}的报纸/书籍"
            ],
            ClueType.RED_HERRING: [
                "{character}表现出可疑的举动，但实际上...",
                "明显的线索指向{character}，转移观众注意力",
                "看似关键的{prop}被强调，实际是误导",
                "{character}过分关注{prop}，引起误会",
                "伪造的证据指向错误方向"
            ]
        }
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化各类线索库
        self.clue_bank = {
            "props": ["钥匙", "手机", "信件", "照片", "药瓶", "刀具", "笔记本", "戒指", "口红", "手表", "文件夹", "枪"],
            "sounds": ["电话铃", "门铃", "脚步声", "窃窃私语", "玻璃碎裂", "雷声", "警笛", "钟声", "风声", "哭声", "笑声"],
            "hint_dialogs": [
                "一切并不像表面看起来那样",
                "总有一天真相会大白",
                "有些秘密最好永远不要揭开",
                "我们都有自己的秘密",
                "小心你信任的人",
                "事情很快就会改变",
                "过去总是会回来找我们",
                "有时候最明显的答案是错的",
                "别相信你看到的一切"
            ],
            "secret_actions": [
                "藏起一样东西",
                "检查手机消息",
                "擦掉什么痕迹",
                "记下什么信息",
                "观察某个人",
                "撒了谎",
                "销毁证据",
                "打了个神秘电话",
                "翻看机密文件"
            ],
            "future_events": [
                "人物身份揭露",
                "背叛事件",
                "重要角色死亡",
                "关键地点出现",
                "意外灾难",
                "阴谋揭露",
                "情感冲突爆发",
                "重要决定时刻",
                "历史真相揭示"
            ]
        }
        
        # 已使用的线索，避免重复
        self.used_clues = set()
        
        logger.info("悬念植入器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        # 默认配置
        config = {
            "early_clue_ratio": 0.35,    # 前期埋设线索的比例（占剧本长度）
            "mid_clue_ratio": 0.25,      # 中期埋设线索的比例
            "max_clues": 5,              # 最大线索数量
            "clue_type_weights": {       # 各类线索的权重
                "visual_detail": 1.0,
                "dialog_hint": 1.2,
                "audio_cue": 0.8,
                "character_secret": 1.1,
                "foreshadowing": 1.3,
                "red_herring": 0.9
            },
            "subtlety_level": 0.7,       # 线索隐蔽度（0-1，值越高越隐蔽）
            "randomization": 0.3         # 随机性（0-1，值越高变化越大）
        }
        
        # TODO: 如果指定了配置文件路径，加载自定义配置
        
        return config
        
    def plant_early_clues(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        在剧本前半部分植入伏笔和线索
        
        Args:
            script: 场景列表
            
        Returns:
            植入线索后的场景列表
        """
        if not script:
            return script
        
        # 创建场景副本以避免修改原始数据
        script_copy = script.copy()
        
        # 确定前半部分范围
        for i, scene in enumerate(script_copy):
            if i < len(script) // 2:  # 前半部分
                # 遍历后面的场景，寻找可以提前暗示的关键信息
                for future_scene in script[i+1:]:
                    # 检查是否有关键标签可以提前暗示
                    tags = future_scene.get("tags", [])
                    if isinstance(tags, str):
                        tags = [tags]
                    
                    # 寻找关键标签
                    if "关键道具" in tags or "重要信息" in tags or "转折点" in tags:
                        # 提取关键信息并植入伏笔
                        prop = future_scene.get("prop", "")
                        if prop:
                            # 为当前场景添加伏笔文本
                            scene["text"] += f"\n[镜头短暂停留在{prop}上特写]"
        
        return script_copy
    
    def plant_suspense(self, 
                      script: List[Dict[str, Any]], 
                      anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
        """
        在整个剧本中策略性地植入悬念元素
        
        Args:
            script: 场景列表
            anchors: 剧情锚点列表，用于确定关键位置，可选
            
        Returns:
            植入悬念后的场景列表
        """
        if not script:
            return script
        
        # 创建场景副本以避免修改原始数据
        script_copy = [scene.copy() for scene in script]
        
        # 重置已使用线索集合
        self.used_clues = set()
        
        # 确定高潮和关键转折点
        climax_indices = []
        if anchors:
            # 根据锚点确定关键位置
            for i, anchor in enumerate(anchors):
                if anchor.type == AnchorType.CLIMAX:
                    # 找到锚点对应的场景索引
                    scene_idx = min(int(anchor.position * len(script)), len(script) - 1)
                    climax_indices.append(scene_idx)
        
        # 如果没有锚点或未找到高潮点，使用默认策略
        if not climax_indices:
            # 假设剧本的2/3处为高潮
            climax_indices = [int(len(script) * 0.66)]
        
        # 计算前期、中期、结尾部分的边界
        early_end = int(len(script) * self.config["early_clue_ratio"])
        mid_end = early_end + int(len(script) * self.config["mid_clue_ratio"])
        
        # 在前期植入伏笔，准备后期的高潮和转折
        early_indices = self._select_clue_positions(0, early_end, 2)
        
        # 在前期场景植入伏笔
        for idx in early_indices:
            # 找到这个场景需要暗示的未来内容
            future_index = self._find_revelant_future_scene(script, idx, climax_indices)
            if future_index > idx:
                # 植入指向未来的线索
                self._add_foreshadowing_clue(script_copy[idx], script[future_index])
        
        # 在中期植入更多细节，加深悬念
        mid_indices = self._select_clue_positions(early_end, mid_end, 2)
        
        # 在中期场景加深悬念
        for idx in mid_indices:
            # 植入角色秘密或误导线索
            if random.random() < 0.5:
                self._add_character_secret_clue(script_copy[idx])
            else:
                self._add_red_herring_clue(script_copy[idx])
        
        # 确保悬念线索不会超过配置的最大数量
        total_clues = len(early_indices) + len(mid_indices)
        if total_clues > self.config["max_clues"]:
            logger.warning(f"悬念线索数量({total_clues})超过最大限制({self.config['max_clues']})")
        
        return script_copy
    
    def _select_clue_positions(self, start_idx: int, end_idx: int, count: int) -> List[int]:
        """
        在指定范围内选择放置线索的位置
        
        Args:
            start_idx: 起始索引（含）
            end_idx: 结束索引（不含）
            count: 目标线索数量
            
        Returns:
            选定的场景索引列表
        """
        if start_idx >= end_idx:
            return []
        
        # 可选范围长度
        range_len = end_idx - start_idx
        
        # 根据范围长度调整实际线索数量
        actual_count = min(count, max(1, range_len // 2))
        
        # 在范围内均匀分布线索位置
        if actual_count == 1:
            # 只有一个线索，放在中间稍前的位置
            return [start_idx + range_len // 3]
        else:
            # 多个线索，均匀分布
            step = range_len // actual_count
            # 添加一些随机性
            randomization = self.config["randomization"]
            positions = []
            for i in range(actual_count):
                base_pos = start_idx + i * step
                # 添加随机偏移，但确保不超出范围
                offset = int(step * randomization * (random.random() * 2 - 1))
                pos = max(start_idx, min(end_idx - 1, base_pos + offset))
                positions.append(pos)
            return positions
    
    def _find_revelant_future_scene(self, 
                                  script: List[Dict[str, Any]], 
                                  current_idx: int, 
                                  climax_indices: List[int]) -> int:
        """
        找到与当前场景相关的未来场景，用于植入伏笔
        
        Args:
            script: 场景列表
            current_idx: 当前场景索引
            climax_indices: 高潮场景索引列表
            
        Returns:
            相关未来场景的索引
        """
        # 默认指向最近的高潮点
        target_idx = min([idx for idx in climax_indices if idx > current_idx], 
                         default=len(script) - 1)
        
        # 在当前场景和目标高潮间寻找包含重要信息的场景
        for idx in range(current_idx + 1, target_idx):
            scene = script[idx]
            
            # 检查是否有关键标签
            tags = scene.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
                
            if any(tag in ["关键道具", "重要信息", "转折点", "关键信息"] for tag in tags):
                return idx
        
        # 如果没找到更合适的，返回目标高潮点
        return target_idx
    
    def _add_foreshadowing_clue(self, current_scene: Dict[str, Any], future_scene: Dict[str, Any]) -> None:
        """
        在当前场景中添加指向未来场景的伏笔
        
        Args:
            current_scene: 当前场景
            future_scene: 未来场景
        """
        # 检查未来场景的关键元素
        prop = future_scene.get("prop", "")
        character = self._get_scene_character(future_scene)
        
        # 如果有关键道具，添加视觉线索
        if prop and random.random() < 0.6:
            template = random.choice(self.clue_templates[ClueType.VISUAL_DETAIL])
            clue_text = template.format(
                prop=prop,
                character=self._get_scene_character(current_scene)
            )
            self._add_clue_to_scene(current_scene, clue_text)
        
        # 或者添加对话暗示
        elif character:
            template = random.choice(self.clue_templates[ClueType.DIALOG_HINT])
            hint = random.choice(self.clue_bank["hint_dialogs"])
            # 确保不重复使用相同的对话暗示
            clue_key = f"dialog_{hint}"
            if clue_key not in self.used_clues:
                self.used_clues.add(clue_key)
                clue_text = template.format(
                    character=self._get_scene_character(current_scene),
                    hint_dialog=hint
                )
                self._add_clue_to_scene(current_scene, clue_text)
        
        # 否则添加更模糊的伏笔
        else:
            template = random.choice(self.clue_templates[ClueType.FORESHADOWING])
            future_event = random.choice(self.clue_bank["future_events"])
            # 确保不重复使用相同的未来事件
            clue_key = f"future_{future_event}"
            if clue_key not in self.used_clues:
                self.used_clues.add(clue_key)
                clue_text = template.format(
                    character=self._get_scene_character(current_scene),
                    future_event=future_event
                )
                self._add_clue_to_scene(current_scene, clue_text)
    
    def _add_character_secret_clue(self, scene: Dict[str, Any]) -> None:
        """
        在场景中添加角色秘密线索
        
        Args:
            scene: 目标场景
        """
        character = self._get_scene_character(scene)
        if not character:
            return
            
        template = random.choice(self.clue_templates[ClueType.CHARACTER_SECRET])
        secret_action = random.choice(self.clue_bank["secret_actions"])
        
        # 确保不重复使用相同的秘密动作
        clue_key = f"secret_{character}_{secret_action}"
        if clue_key not in self.used_clues:
            self.used_clues.add(clue_key)
            clue_text = template.format(
                character=character,
                secret_action=secret_action
            )
            self._add_clue_to_scene(scene, clue_text)
    
    def _add_red_herring_clue(self, scene: Dict[str, Any]) -> None:
        """
        在场景中添加误导线索
        
        Args:
            scene: 目标场景
        """
        character = self._get_scene_character(scene)
        if not character:
            return
            
        template = random.choice(self.clue_templates[ClueType.RED_HERRING])
        prop = random.choice(self.clue_bank["props"])
        
        # 确保不重复使用相同的误导组合
        clue_key = f"herring_{character}_{prop}"
        if clue_key not in self.used_clues:
            self.used_clues.add(clue_key)
            clue_text = template.format(
                character=character,
                prop=prop
            )
            self._add_clue_to_scene(scene, clue_text)
    
    def _add_audio_clue(self, scene: Dict[str, Any]) -> None:
        """
        在场景中添加音效线索
        
        Args:
            scene: 目标场景
        """
        template = random.choice(self.clue_templates[ClueType.AUDIO_CUE])
        sound = random.choice(self.clue_bank["sounds"])
        
        # 确保不重复使用相同的音效
        clue_key = f"audio_{sound}"
        if clue_key not in self.used_clues:
            self.used_clues.add(clue_key)
            clue_text = template.format(
                sound=sound,
                character=self._get_scene_character(scene)
            )
            self._add_clue_to_scene(scene, clue_text)
    
    def _add_clue_to_scene(self, scene: Dict[str, Any], clue_text: str) -> None:
        """
        将线索文本添加到场景中
        
        Args:
            scene: 目标场景
            clue_text: 线索文本
        """
        # 如果场景没有文本字段，添加一个
        if "text" not in scene:
            scene["text"] = ""
        
        # 添加悬念线索
        scene["text"] += f"\n{clue_text}"
        
        # 向场景标签中添加线索标记
        if "tags" not in scene:
            scene["tags"] = []
        elif isinstance(scene["tags"], str):
            scene["tags"] = [scene["tags"]]
            
        scene["tags"].append("悬念线索")
    
    def _get_scene_character(self, scene: Dict[str, Any]) -> str:
        """
        从场景中获取角色名称
        
        Args:
            scene: 场景字典
            
        Returns:
            角色名称，如果没有角色则返回空字符串
        """
        # 尝试不同的可能字段
        for field in ["character", "characters", "pov_character", "speaker"]:
            if field in scene:
                chars = scene[field]
                if isinstance(chars, list) and chars:
                    return chars[0]
                elif isinstance(chars, str) and chars:
                    return chars
        
        # 从文本中尝试提取角色
        text = scene.get("text", "")
        if text:
            # 尝试从对话中提取说话者
            dialog_match = re.search(r"「([^：]+)：", text)
            if dialog_match:
                return dialog_match.group(1)
        
        # 默认角色
        return "某人"


# 提供便捷函数
def plant_early_clues(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    在剧本前半部分植入伏笔和线索的便捷函数
    
    Args:
        script: 场景列表
        
    Returns:
        植入线索后的场景列表
    """
    planter = SuspensePlanter()
    return planter.plant_early_clues(script)


def plant_suspense(script: List[Dict[str, Any]], 
                 anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
    """
    在整个剧本中策略性地植入悬念元素的便捷函数
    
    Args:
        script: 场景列表
        anchors: 剧情锚点列表，可选
        
    Returns:
        植入悬念后的场景列表
    """
    planter = SuspensePlanter()
    return planter.plant_suspense(script, anchors)


def get_clue_types() -> List[str]:
    """
    获取所有可用的线索类型
    
    Returns:
        线索类型列表
    """
    return [t.value for t in ClueType] 