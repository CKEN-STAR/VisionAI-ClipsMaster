#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感记忆触发器模块

根据场景标签和情感类型，为场景添加情感记忆触发点，增强叙事的情感连贯性和观众共鸣。
通过识别场景中的特定情感标签，添加恰当的描述性文本，唤起观众记忆中的情感体验。
"""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    from ..config.constants import EMOTION_TYPES, MEMORY_TRIGGER_TEMPLATES
except ImportError:
    # 备用常量，以防无法导入
    EMOTION_TYPES = {
        "en": ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"],
        "zh": ["喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"]
    }
    MEMORY_TRIGGER_TEMPLATES = {
        "高潮": ["[闪回画面:回忆过去场景片段]"],
        "胜利": ["[重复播放:加强蒙太奇效果]"]
    }

try:
    from ..utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    # 定义备用异常类，以防无法导入
    class ClipMasterError(Exception):
        def __init__(self, message="", code=None, details=None):
            self.code = code
            self.details = details or {}
            super().__init__(message)
    
    class ErrorCode:
        NARRATIVE_ANALYSIS_ERROR = 1405

logger = logging.getLogger(__name__)

class MemoryTriggerError(ClipMasterError):
    """情感记忆触发器异常类"""
    
    def __init__(self, msg: str = "情感记忆触发失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(msg, code=ErrorCode.NARRATIVE_ANALYSIS_ERROR, details=details)

class EmotionMemoryTrigger:
    """情感记忆触发器
    
    分析场景标签和情感类型，为场景添加能引发观众情感记忆的描述性内容。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化情感记忆触发器
        
        Args:
            config: 配置参数，用于自定义触发规则
        """
        try:
            self.config = config or self._default_config()
            self.memory_tag_map = self.config.get("memory_tag_map", {})
            self.emotion_tag_map = self.config.get("emotion_tag_map", {})
            self.trigger_templates = self.config.get("trigger_templates", {})
            self.language = self.config.get("language", "zh")
            
            logger.info("情感记忆触发器初始化完成")
        except Exception as e:
            logger.error(f"情感记忆触发器初始化失败: {str(e)}")
            raise MemoryTriggerError(f"情感记忆触发器初始化失败: {str(e)}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "language": "zh",  # 默认语言
            "memory_tag_map": {
                # 情感记忆标签映射
                "高潮": ["回忆", "闪回", "思绪", "记忆", "往事"],
                "胜利": ["成就", "成功", "欢呼", "成长", "赞许"],
                "悲剧": ["失落", "痛苦", "伤心", "悲伤", "眼泪"],
                "冲突": ["矛盾", "对抗", "争执", "紧张", "敌对"],
                "启示": ["醒悟", "领悟", "明白", "顿悟", "理解"],
                "离别": ["告别", "分离", "离开", "不舍", "道别"],
                "团聚": ["重逢", "相见", "团圆", "拥抱", "温暖"],
                "成长": ["蜕变", "进步", "成熟", "历练", "提升"],
                "牺牲": ["奉献", "舍己", "放弃", "牺牲", "无私"],
                "转折": ["转变", "变化", "新章", "转向", "改变"]
            },
            "emotion_tag_map": {
                # 情感类型标签映射
                "喜悦": ["欢乐", "高兴", "愉悦", "开心", "兴奋"],
                "悲伤": ["忧伤", "难过", "伤心", "痛苦", "眼泪"],
                "愤怒": ["生气", "恼怒", "激愤", "怒火", "暴怒"],
                "恐惧": ["害怕", "惊恐", "畏惧", "胆怯", "惊吓"],
                "厌恶": ["反感", "讨厌", "排斥", "嫌弃", "抵触"],
                "惊讶": ["震惊", "意外", "吃惊", "诧异", "错愕"],
                "中性": ["平静", "沉默", "淡定", "镇定", "从容"]
            },
            "trigger_templates": MEMORY_TRIGGER_TEMPLATES
        }
    
    def process_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理场景列表，添加情感记忆触发点
        
        Args:
            scenes: 场景列表
            
        Returns:
            处理后的场景列表
            
        Raises:
            MemoryTriggerError: 处理过程中发生错误
        """
        try:
            processed_scenes = []
            
            for scene in scenes:
                processed_scene = self.process_scene(scene)
                processed_scenes.append(processed_scene)
            
            return processed_scenes
        except Exception as e:
            logger.error(f"处理场景列表失败: {str(e)}")
            raise MemoryTriggerError(f"处理场景列表失败: {str(e)}")
    
    def process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个场景，添加情感记忆触发点
        
        Args:
            scene: 单个场景数据
            
        Returns:
            处理后的场景
            
        Raises:
            MemoryTriggerError: 处理过程中发生错误
        """
        try:
            # 创建场景副本，避免修改原始数据
            processed_scene = scene.copy()
            
            # 初始化标签列表（如果不存在）
            if "tags" not in processed_scene:
                processed_scene["tags"] = []
            elif isinstance(processed_scene["tags"], str):
                processed_scene["tags"] = [processed_scene["tags"]]
            
            # 初始化文本字段（如果不存在）
            if "text" not in processed_scene:
                processed_scene["text"] = ""
            
            # 处理记忆触发标签
            memory_hooks = self._get_memory_hooks(processed_scene)
            
            # 如果找到了记忆触发器，添加到场景
            if memory_hooks:
                for hook in memory_hooks:
                    if hook.get("text"):
                        # 添加记忆触发器文本
                        processed_scene["text"] += f"\n{hook['text']}"
                        
                        # 标记已添加记忆触发器
                        processed_scene["has_memory_trigger"] = True
                        processed_scene["memory_trigger_type"] = hook.get("type", "未知")
            
            return processed_scene
        except Exception as e:
            logger.error(f"处理单个场景失败: {str(e)}")
            # 记录错误但不中断处理，返回原始场景
            return scene
    
    def _get_memory_hooks(self, scene: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据场景标签获取记忆触发器
        
        Args:
            scene: 场景数据
            
        Returns:
            找到的记忆触发器列表
        """
        hooks = []
        tags = scene.get("tags", [])
        emotion = scene.get("emotion", {})
        emotion_type = emotion.get("type", "中性")
        
        # 检查特定记忆标签
        for tag in tags:
            memory_hook = self._check_memory_tag(tag, emotion_type)
            if memory_hook:
                hooks.append(memory_hook)
        
        # 检查情感类型标签
        emotion_hook = self._check_emotion_type(emotion_type)
        if emotion_hook:
            hooks.append(emotion_hook)
        
        return hooks
    
    def _check_memory_tag(self, tag: str, emotion_type: str) -> Optional[Dict[str, Any]]:
        """检查标签是否匹配记忆触发条件
        
        Args:
            tag: 场景标签
            emotion_type: 情感类型
            
        Returns:
            记忆触发器数据（如果匹配）
        """
        # 检查是否有直接的标签映射
        for memory_key, related_tags in self.memory_tag_map.items():
            if tag in related_tags or tag == memory_key:
                # 获取对应的模板
                templates = self.trigger_templates.get(memory_key, [])
                if templates:
                    # 选择一个随机模板
                    template = random.choice(templates)
                    
                    return {
                        "type": memory_key,
                        "text": template,
                        "source": "memory_tag"
                    }
        
        return None
    
    def _check_emotion_type(self, emotion_type: str) -> Optional[Dict[str, Any]]:
        """检查情感类型是否匹配记忆触发条件
        
        Args:
            emotion_type: 情感类型
            
        Returns:
            记忆触发器数据（如果匹配）
        """
        # 确保使用正确语言的情感类型
        emotion_types = EMOTION_TYPES.get(self.language, [])
        
        # 映射英文情感类型到中文（如果需要）
        if self.language == "zh" and emotion_type in EMOTION_TYPES.get("en", []):
            # 找到对应的中文情感类型
            try:
                index = EMOTION_TYPES.get("en", []).index(emotion_type)
                if index < len(emotion_types):
                    emotion_type = emotion_types[index]
            except (ValueError, IndexError):
                # 如果找不到，使用原始值
                pass
        
        # 检查情感类型是否有对应模板
        templates = self.trigger_templates.get(emotion_type, [])
        if templates:
            # 选择一个随机模板
            template = random.choice(templates)
            
            return {
                "type": emotion_type,
                "text": template,
                "source": "emotion_type"
            }
        
        return None


def implant_memory_hooks(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """插入唤起观众情感记忆的钩子
    
    为场景添加能引发观众情感共鸣的描述内容。
    
    Args:
        scenes: 场景列表
        
    Returns:
        处理后的场景列表
    """
    try:
        # 创建副本，避免修改原始数据
        processed_scenes = [scene.copy() for scene in scenes]
        
        # 处理每个场景中的特殊标签
        for scene in processed_scenes:
            # 初始化标签如果不存在
            if "tags" not in scene:
                scene["tags"] = []
            elif isinstance(scene["tags"], str):
                scene["tags"] = [scene["tags"]]
            
            # 初始化文本字段如果不存在
            if "text" not in scene:
                scene["text"] = ""
            
            # 处理高潮标签
            if "高潮" in scene["tags"]:
                scene["text"] += "\n[闪回画面:回忆过去场景片段]"
            
            # 处理胜利标签
            if "胜利" in scene["tags"]:
                scene["text"] += "\n[重复播放:加强蒙太奇效果]"
        
        return processed_scenes
    except Exception as e:
        logger.error(f"插入情感记忆钩子失败: {str(e)}")
        # 出错时返回原始场景，确保不会中断处理流程
        return scenes 