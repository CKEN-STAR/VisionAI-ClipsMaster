#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
沉浸感增强模块

提供各种沉浸感增强功能，包括环境暗示、情感强化、氛围营造和互动元素。
在视频内容中添加适当的视觉和音频线索，增强观众的沉浸体验。
"""

import os
import re
import yaml
import logging
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

# 设置日志
logger = logging.getLogger("immersion_enhancer")

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "configs")
IMMERSION_CONFIG_PATH = os.path.join(CONFIG_DIR, "immersion_config.yaml")

class ImmersionEnhancer:
    """沉浸感增强器"""
    
    def __init__(self):
        """初始化沉浸感增强器"""
        # 加载配置
        self.config = self._load_config()
        
        # 视觉效果配置
        self.visual_effects = self.config.get('visual_effects', {})
        self.visual_enabled = self.visual_effects.get('enabled', True)
        
        # 音频效果配置
        self.audio_effects = self.config.get('audio_effects', {})
        self.audio_enabled = self.audio_effects.get('enabled', True)
        
        # 转场效果配置
        self.transition_effects = self.config.get('transition_effects', {})
        self.transition_enabled = self.transition_effects.get('enabled', True)
        
        # 模板配置
        self.templates = self.config.get('immersion_templates', {})
        
        # 高级设置
        self.advanced = self.config.get('advanced', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """加载沉浸感增强相关配置"""
        try:
            # 加载沉浸感配置
            if os.path.exists(IMMERSION_CONFIG_PATH):
                with open(IMMERSION_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    logger.info("成功加载沉浸感增强配置")
                    return config
            else:
                logger.warning(f"找不到沉浸感配置文件: {IMMERSION_CONFIG_PATH}, 使用默认配置")
        except Exception as e:
            logger.error(f"加载沉浸感配置失败: {str(e)}")
        
        # 返回默认配置
        return {
            'visual_effects': {'enabled': True},
            'audio_effects': {'enabled': True},
            'transition_effects': {'enabled': True},
            'immersion_templates': {},
            'advanced': {}
        }
    
    def enhance(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        增强脚本的沉浸感
        
        参数:
            script: 场景脚本列表
            
        返回:
            增强后的脚本列表
        """
        logger.info("开始进行沉浸感增强处理")
        enhanced_script = script.copy()
        
        # 添加环境线索
        if self.visual_enabled:
            enhanced_script = self.add_environment_cues(enhanced_script)
            
        # 统一音频线索
        if self.audio_enabled:
            enhanced_script = self.unify_audio_cues(enhanced_script)
            
        # 应用视觉效果
        if self.visual_enabled:
            enhanced_script = self.apply_visual_effects(enhanced_script)
            
        # 增强转场效果
        if self.transition_enabled:
            enhanced_script = self.enhance_transitions(enhanced_script)
            
        # 增强角色互动
        if self.advanced.get('track_character_emotions', True):
            enhanced_script = self.enhance_character_interactions(enhanced_script)
            
        logger.info(f"沉浸感增强处理完成，共处理{len(enhanced_script)}个场景")
        return enhanced_script
    
    def add_environment_cues(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        添加环境线索，提升场景的真实感和代入感
        
        参数:
            script: 原始脚本列表
            
        返回:
            增强后的脚本列表
        """
        if not script:
            return []
            
        enhanced_script = script.copy()
        
        for scene in enhanced_script:
            # 获取场景标签和类型
            tags = scene.get("tags", [])
            scene_type = self._detect_scene_type(scene)
            
            # 应用特定场景类型的视觉增强
            if scene_type and scene_type in self.visual_effects.get('scene_types', {}):
                scene_effects = self.visual_effects['scene_types'][scene_type]
                
                # 添加视觉效果提示
                if "flashback" in tags or scene_type == "flashback":
                    scene["text"] = scene.get("text", "") + "\n[画面淡黄, 添加胶片噪点效果]"
                    
                elif "dream" in tags or scene_type == "dream":
                    scene["text"] = scene.get("text", "") + "\n[画面柔化, 添加轻微模糊和白光边缘]"
                    
                elif scene_type == "emotional" and scene_effects:
                    effect = random.choice(scene_effects)
                    scene["text"] = scene.get("text", "") + f"\n[应用{effect}视觉效果]"
                    
        return enhanced_script
    
    def unify_audio_cues(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        统一音频线索，确保音频连贯性
        
        参数:
            script: 脚本列表
            
        返回:
            增强后的脚本列表
        """
        if not script:
            return []
            
        enhanced_script = script.copy()
        prev_bgm = None
        
        for scene in enhanced_script:
            # 检查背景音乐变化
            if scene.get("bgm") != prev_bgm:
                scene["text"] = scene.get("text", "") + f"\n[背景音乐请变为: {scene['bgm']}]"
                prev_bgm = scene.get("bgm")
                
        return enhanced_script
    
    def apply_visual_effects(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用视觉效果，增强视觉冲击力
        
        参数:
            script: 脚本列表
            
        返回:
            增强后的脚本列表
        """
        if not script:
            return []
            
        enhanced_script = script.copy()
        
        for scene in enhanced_script:
            # 获取情感标签
            sentiment = scene.get("sentiment", {}).get("label", "NEUTRAL")
            intensity = scene.get("sentiment", {}).get("intensity", 0.5)
            scene_type = self._detect_scene_type(scene)
            
            # 根据情感和场景类型添加视觉效果
            if self.advanced.get('adjust_by_emotion_intensity', True):
                # 根据情感强度选择效果
                if sentiment == "POSITIVE" and intensity > 0.7:
                    scene["visual_effects"] = ["bright", "warm_filter", "smooth_motion"]
                elif sentiment == "NEGATIVE" and intensity > 0.7:
                    scene["visual_effects"] = ["dark", "cold_filter", "contrast_increase"]
                elif sentiment == "SURPRISE" and intensity > 0.6:
                    scene["visual_effects"] = ["zoom_focus", "saturated_colors"]
                elif sentiment == "NEUTRAL":
                    scene["visual_effects"] = ["natural", "balanced_lighting"]
            else:
                # 根据场景类型选择默认效果
                if scene_type in self.visual_effects.get('scene_types', {}):
                    scene["visual_effects"] = self.visual_effects['scene_types'][scene_type][:2]
                else:
                    scene["visual_effects"] = self.visual_effects.get('default_enhancements', 
                                                                   ["natural"])
                    
        return enhanced_script
    
    def enhance_transitions(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        增强场景转场效果
        
        参数:
            script: 脚本列表
            
        返回:
            增强后的脚本列表
        """
        if not script or len(script) <= 1:
            return script
            
        enhanced_script = script.copy()
        transition_types = self.transition_effects.get('types', [])
        emotion_transitions = self.transition_effects.get('emotion_transitions', {})
        
        prev_sentiment = None
        for i, scene in enumerate(enhanced_script):
            if i == 0:
                prev_sentiment = scene.get("sentiment", {}).get("label", "NEUTRAL")
                continue
                
            # 获取当前情感
            current_sentiment = scene.get("sentiment", {}).get("label", "NEUTRAL")
            
            # 确定转场类型
            transition = None
            transition_key = f"{prev_sentiment.lower()}_to_{current_sentiment.lower()}"
            
            # 根据情感转换选择转场
            if transition_key in emotion_transitions:
                transition_options = emotion_transitions[transition_key]
                transition = random.choice(transition_options) if transition_options else None
            
            # 没有找到特定情感转场时，使用默认转场
            if not transition and transition_types:
                transition = random.choice(transition_types)
                
            # 添加转场效果
            if transition:
                scene["transition"] = {
                    "type": transition,
                    "from_emotion": prev_sentiment,
                    "to_emotion": current_sentiment
                }
                scene["text"] = scene.get("text", "") + f"\n[使用{transition}转场效果]"
                
            prev_sentiment = current_sentiment
            
        return enhanced_script
    
    def enhance_character_interactions(self, script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        增强角色互动，提升情感共鸣
        
        参数:
            script: 脚本列表
            
        返回:
            增强后的脚本列表
        """
        if not script:
            return []
            
        enhanced_script = script.copy()
        
        # 角色跟踪
        characters = set()
        for scene in enhanced_script:
            # 提取场景中的角色
            text = scene.get("text", "")
            scene_characters = re.findall(r'([A-Z一-龥]{2,})[:：]', text)
            characters.update(scene_characters)
        
        # 为情感强烈的场景添加反应镜头
        for i, scene in enumerate(enhanced_script):
            sentiment = scene.get("sentiment", {}).get("label", "NEUTRAL")
            intensity = scene.get("sentiment", {}).get("intensity", 0.5)
            
            # 为高情感场景添加角色反应
            if intensity > 0.8 and i < len(enhanced_script) - 1:
                if characters:
                    character = random.choice(list(characters))
                    enhanced_script[i+1]["reaction_shot"] = {
                        "character": character,
                        "emotion": sentiment.lower()
                    }
                    
                    # 添加反应镜头建议
                    enhanced_script[i+1]["text"] = enhanced_script[i+1].get("text", "") + \
                        f"\n[插入{character}的情感反应特写]"
        
        return enhanced_script
    
    def _detect_scene_type(self, scene: Dict[str, Any]) -> Optional[str]:
        """
        检测场景类型
        
        参数:
            scene: 场景数据
            
        返回:
            场景类型
        """
        # 首先检查标签
        tags = scene.get("tags", [])
        for tag in tags:
            if tag.lower() in ["emotional", "action", "suspense", "revelation", 
                             "comedy", "romance", "flashback", "dream"]:
                return tag.lower()
        
        # 检查文本内容
        text = scene.get("text", "")
        sentiment = scene.get("sentiment", {}).get("label", "NEUTRAL")
        intensity = scene.get("sentiment", {}).get("intensity", 0.5)
        
        # 基于内容判断场景类型
        if "梦" in text or "梦境" in text or "梦到" in text:
            return "dream"
        elif "回忆" in text or "过去" in text or "闪回" in text:
            return "flashback"
        elif sentiment == "POSITIVE" and intensity > 0.7 and ("爱" in text or "喜欢" in text):
            return "romance"
        elif "战斗" in text or "追逐" in text or "跑" in text:
            return "action"
        elif sentiment == "NEGATIVE" and intensity > 0.6:
            return "suspense"
        elif "笑" in text or "搞笑" in text:
            return "comedy"
        elif intensity > 0.7:
            return "emotional"
            
        # 默认类型
        return "standard"
    
    def apply_template(self, script: List[Dict[str, Any]], template_name: str) -> List[Dict[str, Any]]:
        """
        应用预定义的沉浸感模板
        
        参数:
            script: 脚本列表
            template_name: 模板名称
            
        返回:
            应用模板后的脚本
        """
        if template_name not in self.templates:
            logger.warning(f"找不到模板: {template_name}, 使用标准模板")
            template_name = "standard"
            
        template = self.templates.get(template_name, {})
        
        # 应用模板
        enhanced_script = script.copy()
        for scene in enhanced_script:
            scene["immersion_template"] = template_name
            
            # 应用视觉效果
            if "visual" in template and self.visual_enabled:
                scene["visual_effects"] = template["visual"]
                
            # 应用音频效果
            if "audio" in template and self.audio_enabled:
                scene["audio_effects"] = template["audio"]
        
        return enhanced_script

# 创建全局增强器实例
_enhancer = None

def get_enhancer() -> ImmersionEnhancer:
    """获取沉浸感增强器实例"""
    global _enhancer
    if _enhancer is None:
        _enhancer = ImmersionEnhancer()
    return _enhancer

def enhance_immersion(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    提升脚本的沉浸感体验
    
    为脚本添加视觉和音频提示，增强观众的沉浸感体验。
    
    参数:
        script: 场景脚本列表
        
    返回:
        增强后的脚本列表
    """
    enhancer = get_enhancer()
    return enhancer.enhance(script)

def add_environment_cues(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """添加环境线索，提升场景的真实感和代入感"""
    enhancer = get_enhancer()
    return enhancer.add_environment_cues(script)

def unify_audio_cues(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """统一音频线索，确保音频连贯性"""
    enhancer = get_enhancer()
    return enhancer.unify_audio_cues(script)

def apply_visual_effects(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """应用视觉效果，增强视觉冲击力"""
    enhancer = get_enhancer()
    return enhancer.apply_visual_effects(script)

def enhance_character_interactions(script: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """增强角色互动，提升情感共鸣"""
    enhancer = get_enhancer()
    return enhancer.enhance_character_interactions(script)

def suggest_immersion_enhancements(scene_type: str) -> Dict[str, List[str]]:
    """根据场景类型建议合适的沉浸感增强方法"""
    enhancer = get_enhancer()
    
    # 获取场景类型配置
    visual_effects = []
    if scene_type in enhancer.visual_effects.get('scene_types', {}):
        visual_effects = enhancer.visual_effects['scene_types'][scene_type]
    else:
        visual_effects = enhancer.visual_effects.get('default_enhancements', [])
        
    audio_effects = []
    if scene_type in enhancer.audio_effects.get('scene_types', {}):
        audio_effects = enhancer.audio_effects['scene_types'][scene_type]
    else:
        audio_effects = enhancer.audio_effects.get('default_enhancements', [])
        
    transition_types = enhancer.transition_effects.get('types', [])
    
    # 构建建议
    suggestions = {
        "visual_cues": visual_effects,
        "audio_cues": audio_effects,
        "transitions": [random.choice(transition_types)] if transition_types else []
    }
    
    return suggestions

def apply_immersion_template(script: List[Dict[str, Any]], template_name: str) -> List[Dict[str, Any]]:
    """应用预定义的沉浸感模板"""
    enhancer = get_enhancer()
    return enhancer.apply_template(script, template_name) 