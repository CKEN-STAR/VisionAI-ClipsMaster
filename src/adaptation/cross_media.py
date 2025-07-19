"""
跨媒介模式迁移模块

该模块实现了不同媒介类型之间的叙事模式迁移和适配，
支持将一种媒介类型的叙事模式转换为另一种媒介类型的模式。
"""

import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import numpy as np
from loguru import logger

from src.version_management.pattern_version_manager import PatternVersionManager
from src.algorithms.pattern_mining import PatternMiner
from src.core.pattern_updater import PatternUpdater


class CrossMediaAdapter:
    """跨媒介模式迁移器，实现不同媒介类型间的模式迁移"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化跨媒介模式迁移器
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        self.pattern_miner = PatternMiner()
        self.version_manager = PatternVersionManager()
        
        # 加载配置
        self._load_config(config_path)
        
        # 初始化媒介类型适配规则
        self._init_adaptation_rules()
        
        logger.info("跨媒介模式迁移器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> None:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        # 默认配置
        self.config = {
            "media_types": [
                "短视频", "互动剧", "广播剧", "漫画", "电影", "网剧", "动画"
            ],
            "adaptation_rules": {
                "短视频": {
                    "duration_factor": 0.3,  # 时长缩短到30%
                    "narrative_density": 2.0,  # 叙事密度提高1倍
                    "pattern_priorities": ["climax", "conflict", "surprise"],
                    "focus_areas": ["opening", "ending"]
                },
                "互动剧": {
                    "branching_factor": 2.5,  # 分支因子
                    "decision_points": ["conflict", "climax"],  # 决策点放置位置
                    "minimal_branches": 2,  # 最少分支数
                    "branching_threshold": 0.6  # 分支阈值
                },
                "广播剧": {
                    "audio_hints": True,  # 使用声音提示
                    "voice_emphasis": 1.5,  # 语音强调因子
                    "background_audio": True,  # 使用背景音效
                    "narrative_pacing": 1.2  # 叙事节奏因子
                },
                "漫画": {
                    "visual_emphasis": True,  # 视觉强调
                    "panel_transitions": ["moment", "action", "subject", "scene", "aspect"],
                    "keyword_highlighting": True,  # 关键词突出显示
                    "scene_compression": 1.8  # 场景压缩因子
                },
                "电影": {
                    "cinematic_techniques": ["establishing_shot", "closeup", "pan", "tracking"],
                    "scene_duration_factor": 1.0,  # 场景时长因子
                    "visual_storytelling": True,  # 视觉叙事
                    "audio_visual_sync": True  # 音视频同步
                },
                "网剧": {
                    "episode_hooks": True,  # 使用集末钩子
                    "character_focus": True,  # 角色聚焦
                    "cliffhanger_frequency": 0.8,  # 悬念频率
                    "recurring_elements": True  # 使用重复元素
                },
                "动画": {
                    "visual_exaggeration": 1.5,  # 视觉夸张因子
                    "stylization_level": 0.7,  # 风格化程度
                    "movement_emphasis": True,  # 动作强调
                    "color_psychology": True  # 色彩心理学
                }
            },
            "pattern_adaptation": {
                "opening": {
                    "short_video": "compress",  # 压缩
                    "interactive": "branch_setup",  # 设置分支
                    "radio_drama": "audio_intro",  # 音频介绍
                    "comic": "visual_hook",  # 视觉钩子
                    "movie": "establishing",  # 建立场景
                    "web_series": "character_intro",  # 角色介绍
                    "animation": "stylized_intro"  # 风格化介绍
                },
                "climax": {
                    "short_video": "intensify",  # 强化
                    "interactive": "decision_point",  # 决策点
                    "radio_drama": "audio_peak",  # 音频高潮
                    "comic": "dramatic_panel",  # 戏剧性面板
                    "movie": "visual_climax",  # 视觉高潮
                    "web_series": "episode_peak",  # 剧集高潮
                    "animation": "dynamic_movement"  # 动态运动
                },
                "conflict": {
                    "short_video": "compress",  # 压缩
                    "interactive": "choice_moment",  # 选择时刻
                    "radio_drama": "dialogue_tension",  # 对话紧张
                    "comic": "contrast_panels",  # 对比面板
                    "movie": "conflict_sequence",  # 冲突序列
                    "web_series": "character_clash",  # 角色冲突
                    "animation": "exaggerated_conflict"  # 夸张冲突
                },
                "transition": {
                    "short_video": "minimal",  # 最小化
                    "interactive": "path_connection",  # 路径连接
                    "radio_drama": "audio_bridge",  # 音频桥接
                    "comic": "panel_transition",  # 面板过渡
                    "movie": "visual_transition",  # 视觉过渡
                    "web_series": "scene_shift",  # 场景转换
                    "animation": "fluid_transition"  # 流畅过渡
                },
                "resolution": {
                    "short_video": "simplify",  # 简化
                    "interactive": "outcome_reveal",  # 结果揭示
                    "radio_drama": "tone_resolution",  # 语调解决
                    "comic": "visual_conclusion",  # 视觉结论
                    "movie": "emotional_payoff",  # 情感回报
                    "web_series": "arc_completion",  # 弧线完成
                    "animation": "visual_harmony"  # 视觉和谐
                },
                "ending": {
                    "short_video": "strong_hook",  # 强钩子
                    "interactive": "final_choice",  # 最终选择
                    "radio_drama": "auditory_closure",  # 听觉封闭
                    "comic": "final_panel",  # 最终面板
                    "movie": "emotional_closure",  # 情感闭合
                    "web_series": "next_episode_hook",  # 下一集钩子
                    "animation": "symbolic_ending"  # 象征性结束
                }
            }
        }
        
        # 加载外部配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import yaml
                    external_config = yaml.safe_load(f)
                    # 深度合并配置
                    self._deep_merge_config(self.config, external_config)
                logger.info(f"从 {config_path} 加载跨媒介配置成功")
            except Exception as e:
                logger.warning(f"加载跨媒介配置失败: {e}，使用默认配置")
    
    def _deep_merge_config(self, base_config: Dict, new_config: Dict) -> None:
        """
        深度合并配置
        
        Args:
            base_config: 基础配置
            new_config: 新配置
        """
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _init_adaptation_rules(self) -> None:
        """初始化媒介类型适配规则"""
        # 媒介类型映射（英文到中文）
        self.media_type_mapping = {
            "short_video": "短视频",
            "interactive": "互动剧",
            "radio_drama": "广播剧",
            "comic": "漫画",
            "movie": "电影",
            "web_series": "网剧",
            "animation": "动画"
        }
        
        # 中文到英文的反向映射
        self.reverse_media_mapping = {v: k for k, v in self.media_type_mapping.items()}
        
        # 模式类型映射
        self.pattern_type_mapping = {
            "opening": "开场",
            "climax": "高潮",
            "conflict": "冲突",
            "transition": "过渡",
            "resolution": "解决",
            "ending": "结束"
        }
    
    def adapt_pattern(self, pattern: Dict[str, Any], target_media_type: str) -> Dict[str, Any]:
        """
        将模式适配到目标媒介类型
        
        Args:
            pattern: 原始模式
            target_media_type: 目标媒介类型
            
        Returns:
            适配后的模式
        """
        logger.info(f"将模式 {pattern.get('id', '未知')} 适配到 {target_media_type}")
        
        # 复制一份模式数据进行修改
        adapted_pattern = pattern.copy()
        
        # 获取模式类型
        pattern_type = pattern.get("type", "unknown")
        
        # 添加适配信息
        adapted_pattern["adapted"] = True
        adapted_pattern["source_media"] = pattern.get("media_type", "unknown")
        adapted_pattern["target_media"] = target_media_type
        adapted_pattern["adaptation_method"] = self._get_adaptation_method(pattern_type, target_media_type)
        
        # 根据媒介类型进行具体适配
        if target_media_type == "短视频":
            adapted_pattern = self._shorten_duration(adapted_pattern, 0.3)
        elif target_media_type == "互动剧":
            adapted_pattern = self._add_branching(adapted_pattern)
        elif target_media_type == "广播剧":
            adapted_pattern = self._enhance_audio(adapted_pattern)
        elif target_media_type == "漫画":
            adapted_pattern = self._highlight_keywords(adapted_pattern)
        
        # 记录适配历史
        if "adaptation_history" not in adapted_pattern:
            adapted_pattern["adaptation_history"] = []
        
        adapted_pattern["adaptation_history"].append({
            "timestamp": self._get_current_timestamp(),
            "from": pattern.get("media_type", "unknown"),
            "to": target_media_type,
            "method": adapted_pattern["adaptation_method"]
        })
        
        # 更新媒介类型
        adapted_pattern["media_type"] = target_media_type
        
        return adapted_pattern
    
    def _get_adaptation_method(self, pattern_type: str, target_media_type: str) -> str:
        """获取适配方法"""
        # 获取英文媒介类型
        en_media_type = self.reverse_media_mapping.get(target_media_type, "unknown")
        
        # 从配置中获取适配方法
        pattern_adaptation = self.config.get("pattern_adaptation", {})
        type_adaptations = pattern_adaptation.get(pattern_type, {})
        
        return type_adaptations.get(en_media_type, "default")
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _shorten_duration(self, pattern: Dict[str, Any], factor: float = 0.3) -> Dict[str, Any]:
        """
        缩短模式时长
        
        Args:
            pattern: 原始模式
            factor: 缩短因子
            
        Returns:
            修改后的模式
        """
        if "duration" in pattern:
            pattern["duration"] = pattern["duration"] * factor
        
        # 增加叙事密度以适应短时长
        pattern["narrative_density"] = pattern.get("narrative_density", 1.0) * 2.0
        
        # 添加短视频专属属性
        pattern["quick_hook"] = True
        pattern["attention_grabbing"] = True
        
        # 优先保留高潮和冲突场景
        if pattern["type"] in ["climax", "conflict"]:
            pattern["preservation_priority"] = "high"
        else:
            pattern["preservation_priority"] = "medium"
        
        return pattern
    
    def _add_branching(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加分支结构
        
        Args:
            pattern: 原始模式
            
        Returns:
            修改后的模式
        """
        # 获取分支配置
        branching_config = self.config.get("adaptation_rules", {}).get("互动剧", {})
        branching_factor = branching_config.get("branching_factor", 2.5)
        min_branches = branching_config.get("minimal_branches", 2)
        
        # 添加分支相关属性
        pattern["has_branches"] = True
        pattern["branch_points"] = min_branches
        pattern["branch_factor"] = branching_factor
        
        # 如果是冲突或高潮类型，增加分支选项
        if pattern["type"] in ["conflict", "climax"]:
            pattern["decision_required"] = True
            pattern["choice_options"] = min_branches + 1  # 额外增加一个选项
            pattern["outcome_variance"] = 0.7  # 结果差异度
        
        # 添加互动剧专属属性
        pattern["player_agency"] = True
        pattern["choice_impact"] = 0.8  # 选择影响程度
        
        return pattern
    
    def _enhance_audio(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        增强音频特性
        
        Args:
            pattern: 原始模式
            
        Returns:
            修改后的模式
        """
        # 获取广播剧配置
        audio_config = self.config.get("adaptation_rules", {}).get("广播剧", {})
        voice_emphasis = audio_config.get("voice_emphasis", 1.5)
        
        # 添加音频相关属性
        pattern["audio_enhanced"] = True
        pattern["voice_prominence"] = voice_emphasis
        pattern["background_audio"] = True
        
        # 根据模式类型添加特定音效提示
        if pattern["type"] == "opening":
            pattern["audio_cues"] = ["theme_intro", "character_voice", "setting_ambience"]
        elif pattern["type"] == "climax":
            pattern["audio_cues"] = ["dramatic_music", "emotional_voices", "sound_effects"]
        elif pattern["type"] == "conflict":
            pattern["audio_cues"] = ["tension_music", "voice_confrontation", "impact_sounds"]
        elif pattern["type"] == "ending":
            pattern["audio_cues"] = ["resolution_theme", "emotional_closure", "final_note"]
        else:
            pattern["audio_cues"] = ["transition_sound", "background_ambience"]
        
        # 添加广播剧专属属性
        pattern["audio_narrative"] = True
        pattern["voice_acting_emphasis"] = True
        
        return pattern
    
    def _highlight_keywords(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        突出关键词
        
        Args:
            pattern: 原始模式
            
        Returns:
            修改后的模式
        """
        # 获取漫画配置
        comic_config = self.config.get("adaptation_rules", {}).get("漫画", {})
        panel_transitions = comic_config.get("panel_transitions", [])
        
        # 添加关键词突出属性
        pattern["keywords_highlighted"] = True
        
        # 添加漫画面板相关属性
        if pattern["type"] == "opening":
            pattern["panel_layout"] = "establishing"
            pattern["transition_type"] = "scene"
        elif pattern["type"] == "climax":
            pattern["panel_layout"] = "dynamic"
            pattern["transition_type"] = "action"
        elif pattern["type"] == "conflict":
            pattern["panel_layout"] = "confrontational"
            pattern["transition_type"] = "subject"
        elif pattern["type"] == "ending":
            pattern["panel_layout"] = "closing"
            pattern["transition_type"] = "aspect"
        else:
            pattern["panel_layout"] = "standard"
            pattern["transition_type"] = panel_transitions[0] if panel_transitions else "moment"
        
        # 强化视觉表现
        pattern["visual_emphasis"] = True
        pattern["symbolic_elements"] = True
        
        # 添加漫画专属属性
        pattern["panel_based"] = True
        pattern["visual_narrative"] = True
        
        return pattern
    
    def batch_adapt_patterns(self, patterns: List[Dict[str, Any]], target_media_type: str) -> List[Dict[str, Any]]:
        """
        批量适配模式
        
        Args:
            patterns: 模式列表
            target_media_type: 目标媒介类型
            
        Returns:
            适配后的模式列表
        """
        logger.info(f"批量将 {len(patterns)} 个模式适配到 {target_media_type}")
        adapted_patterns = []
        
        for pattern in patterns:
            try:
                adapted_pattern = self.adapt_pattern(pattern, target_media_type)
                adapted_patterns.append(adapted_pattern)
            except Exception as e:
                logger.error(f"适配模式 {pattern.get('id', '未知')} 失败: {e}")
        
        logger.info(f"成功适配 {len(adapted_patterns)} 个模式")
        return adapted_patterns
    
    def adapt_from_version(self, version_name: Optional[str], target_media_type: str) -> List[Dict[str, Any]]:
        """
        从指定版本中适配模式
        
        Args:
            version_name: 版本名称，如果为None则使用最新版本
            target_media_type: 目标媒介类型
            
        Returns:
            适配后的模式列表
        """
        try:
            # 获取版本配置
            config = self.version_manager.get_pattern_config(version_name)
            
            # 获取顶级模式
            top_patterns = config.get("top_patterns", [])
            
            # 适配模式
            adapted_patterns = self.batch_adapt_patterns(top_patterns, target_media_type)
            
            return adapted_patterns
        except Exception as e:
            logger.error(f"从版本 {version_name} 适配模式失败: {e}")
            return []
    
    def create_adapted_version(self, source_version: Optional[str], target_media_type: str) -> bool:
        """
        创建适配后的新版本
        
        Args:
            source_version: 源版本名称，如果为None则使用最新版本
            target_media_type: 目标媒介类型
            
        Returns:
            是否成功创建
        """
        try:
            # 获取源版本
            if source_version is None:
                source_version = self.version_manager.get_latest_version()
            
            # 适配模式
            adapted_patterns = self.adapt_from_version(source_version, target_media_type)
            
            if not adapted_patterns:
                logger.warning(f"没有从版本 {source_version} 获取到可适配的模式")
                return False
            
            # 创建新版本
            media_type_short = self.reverse_media_mapping.get(target_media_type, "media")
            new_version = f"{source_version.rstrip('0123456789')}_{media_type_short}"
            
            # 创建新版本描述
            description = f"从版本 {source_version} 适配到 {target_media_type} 的模式集合"
            
            # 创建新版本
            result = self.version_manager.create_new_version(
                new_version,
                description=description,
                author="CrossMediaAdapter",
                base_version=source_version
            )
            
            if not result:
                logger.error(f"创建新版本 {new_version} 失败")
                return False
            
            # 获取新版本配置
            new_config = self.version_manager.get_pattern_config(new_version)
            
            # 更新配置
            new_config["top_patterns"] = adapted_patterns
            new_config["target_media_type"] = target_media_type
            new_config["source_version"] = source_version
            
            # 更新配置
            result = self.version_manager.update_pattern_config(new_config, new_version)
            
            return result
        except Exception as e:
            logger.error(f"创建适配版本失败: {e}")
            return False
    
    def get_supported_media_types(self) -> List[str]:
        """
        获取支持的媒介类型
        
        Returns:
            支持的媒介类型列表
        """
        return self.config.get("media_types", []) 