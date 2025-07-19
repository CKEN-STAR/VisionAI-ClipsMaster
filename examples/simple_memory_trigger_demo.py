#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感记忆触发器简单演示脚本

这是一个独立的演示脚本，不依赖于项目的其他模块，
用于展示情感记忆触发器的基本功能和使用方法。
"""

import random
from typing import Dict, List, Any, Optional


# 内置的情感类型常量
EMOTION_TYPES = {
    "en": ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"],
    "zh": ["喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"]
}

# 内置的触发器模板
MEMORY_TRIGGER_TEMPLATES = {
    # 情感类型触发模板
    "喜悦": [
        "[画面增亮，伴随轻柔音乐，唤起观众对欢乐时刻的共鸣]",
        "[特写镜头捕捉微笑细节，引发观众回忆类似的幸福瞬间]"
    ],
    "悲伤": [
        "[画面色调转冷，慢镜头展现细节，唤起观众共情]",
        "[背景音乐转为钢琴旋律，触发观众对失落感的记忆]"
    ],
    # 情感记忆标签触发模板
    "高潮": [
        "[闪回画面：插入模糊回忆片段，唤起情感连接]",
        "[多角度蒙太奇：快速切换视角，增强情感冲击]"
    ],
    "胜利": [
        "[重复播放：关键动作慢动作重放，强化成就感]",
        "[色彩饱和度提升：画面鲜亮，唤起观众成功记忆]"
    ]
}


class SimpleMemoryTrigger:
    """简单情感记忆触发器
    
    一个简化版的情感记忆触发器，演示基本功能。
    """
    
    def __init__(self):
        """初始化简单情感记忆触发器"""
        # 情感记忆标签映射
        self.memory_tag_map = {
            "高潮": ["回忆", "闪回", "思绪", "记忆", "往事"],
            "胜利": ["成就", "成功", "欢呼", "成长", "赞许"]
        }
        # 情感类型标签映射
        self.emotion_tag_map = {
            "喜悦": ["欢乐", "高兴", "愉悦", "开心", "兴奋"],
            "悲伤": ["忧伤", "难过", "伤心", "痛苦", "眼泪"]
        }
        self.trigger_templates = MEMORY_TRIGGER_TEMPLATES
        self.language = "zh"
        
        print("情感记忆触发器初始化完成")
    
    def process_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理场景列表，添加情感记忆触发点
        
        Args:
            scenes: 场景列表
            
        Returns:
            处理后的场景列表
        """
        processed_scenes = []
        
        for scene in scenes:
            processed_scene = self.process_scene(scene)
            processed_scenes.append(processed_scene)
        
        return processed_scenes
    
    def process_scene(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个场景，添加情感记忆触发点
        
        Args:
            scene: 单个场景数据
            
        Returns:
            处理后的场景
        """
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
            memory_hook = self._check_memory_tag(tag)
            if memory_hook:
                hooks.append(memory_hook)
        
        # 检查情感类型标签
        emotion_hook = self._check_emotion_type(emotion_type)
        if emotion_hook:
            hooks.append(emotion_hook)
        
        return hooks
    
    def _check_memory_tag(self, tag: str) -> Optional[Dict[str, Any]]:
        """检查标签是否匹配记忆触发条件
        
        Args:
            tag: 场景标签
            
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
        # 映射英文情感类型到中文（如果需要）
        if emotion_type in EMOTION_TYPES.get("en", []):
            try:
                index = EMOTION_TYPES.get("en", []).index(emotion_type)
                if index < len(EMOTION_TYPES.get("zh", [])):
                    emotion_type = EMOTION_TYPES.get("zh", [])[index]
            except (ValueError, IndexError):
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


def create_sample_scenes() -> List[Dict[str, Any]]:
    """创建样本场景列表"""
    return [
        {
            "id": "scene_1",
            "emotion": {
                "type": "neutral",
                "score": 0.5
            },
            "tags": ["开场"],
            "text": "主角走在街道上，神情平静，观察周围的环境。"
        },
        {
            "id": "scene_2",
            "emotion": {
                "type": "joy",
                "score": 0.7
            },
            "tags": ["胜利"],
            "text": "主角获得比赛冠军，举起奖杯，面带笑容。"
        },
        {
            "id": "scene_3",
            "emotion": {
                "type": "sadness",
                "score": 0.6
            },
            "tags": ["高潮"],
            "text": "主角沉默地站在雨中，回忆过去的美好时光。"
        },
        {
            "id": "scene_4",
            "emotion": {
                "type": "joy",
                "score": 0.8
            },
            "tags": ["成功"],
            "text": "经过努力，主角终于解决了困扰已久的问题。"
        }
    ]


def print_scene_info(scene: Dict[str, Any], index: int) -> None:
    """打印场景信息"""
    emotion = scene.get("emotion", {})
    emotion_type = emotion.get("type", "未知")
    tags = scene.get("tags", [])
    text = scene.get("text", "")
    
    print(f"场景 {index}:")
    print(f"  情感类型: {emotion_type}")
    print(f"  标签: {', '.join(tags) if tags else '无'}")
    print(f"  描述文本: {text}")
    
    # 如果有记忆触发器，打印额外信息
    if scene.get("has_memory_trigger"):
        trigger_type = scene.get("memory_trigger_type", "未知")
        print(f"  [已添加记忆触发点: {trigger_type}]")
    
    print()


def main():
    """主函数"""
    print("=" * 60)
    print(" 情感记忆触发器简单演示 ".center(60, "="))
    print("=" * 60)
    
    # 创建样本场景
    scenes = create_sample_scenes()
    
    print("原始场景信息:")
    for i, scene in enumerate(scenes, 1):
        print_scene_info(scene, i)
    
    # 创建情感记忆触发器
    trigger = SimpleMemoryTrigger()
    
    # 处理场景
    processed_scenes = trigger.process_scenes(scenes)
    
    print("=" * 60)
    print(" 添加记忆触发点后 ".center(60, "="))
    print("=" * 60)
    
    print("处理后场景信息:")
    for i, scene in enumerate(processed_scenes, 1):
        print_scene_info(scene, i)


if __name__ == "__main__":
    main() 