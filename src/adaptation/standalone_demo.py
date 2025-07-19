"""
跨媒介模式迁移独立演示

无需依赖完整系统的演示脚本，用于测试CrossMediaAdapter的基本功能
"""

import os
import json
import time
from typing import Dict, List, Any
import random
from pathlib import Path
import logging

# 设置基本日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cross_media_demo")


class MockVersionManager:
    """模拟版本管理器"""
    
    def __init__(self):
        self.versions = {}
        self.current_version = None
    
    def get_pattern_config(self, version_name=None):
        """获取模式配置"""
        if not version_name:
            version_name = self.get_latest_version()
        
        if version_name not in self.versions:
            self.versions[version_name] = {
                "pattern_types": ["opening", "climax", "conflict", "transition", "resolution", "ending"],
                "top_patterns": [],
                "description": f"版本 {version_name}"
            }
        
        return self.versions[version_name]
    
    def get_latest_version(self):
        """获取最新版本"""
        if not self.versions:
            return "v1.0"
        return sorted(self.versions.keys())[-1]
    
    def create_new_version(self, version_name, description=None, author=None, base_version=None):
        """创建新版本"""
        if version_name in self.versions:
            return False
        
        self.versions[version_name] = {
            "pattern_types": ["opening", "climax", "conflict", "transition", "resolution", "ending"],
            "top_patterns": [],
            "description": description or f"版本 {version_name}",
            "author": author or "system",
            "base_version": base_version,
            "created_at": time.time()
        }
        
        # 如果有基础版本，复制配置
        if base_version and base_version in self.versions:
            base_config = self.versions[base_version]
            for k, v in base_config.items():
                if k != "description" and k != "author" and k != "created_at":
                    self.versions[version_name][k] = v
        
        return True
    
    def update_pattern_config(self, config, version_name):
        """更新模式配置"""
        if version_name not in self.versions:
            return False
        
        self.versions[version_name].update(config)
        return True
    
    def get_version_metadata(self, version_name):
        """获取版本元数据"""
        if version_name not in self.versions:
            return None
        
        return {
            "version": version_name,
            "description": self.versions[version_name].get("description"),
            "author": self.versions[version_name].get("author"),
            "created_at": self.versions[version_name].get("created_at")
        }


class MockPatternMiner:
    """模拟模式挖掘器"""
    
    def __init__(self):
        pass
    
    def mine_patterns(self, data, **kwargs):
        """模拟挖掘模式"""
        return []


class SimpleCrossMediaAdapter:
    """简化版跨媒介适配器"""
    
    def __init__(self, config=None):
        self.version_manager = MockVersionManager()
        self.pattern_miner = MockPatternMiner()
        
        # 加载配置
        self._load_config(config)
        
        # 初始化媒介类型适配规则
        self._init_adaptation_rules()
        
        logger.info("跨媒介模式迁移器初始化完成")
    
    def _load_config(self, config=None):
        """加载配置"""
        # 默认配置
        self.config = {
            "media_types": [
                "短视频", "互动剧", "广播剧", "漫画", "电影", "网剧", "动画"
            ],
            "adaptation_rules": {
                "短视频": {
                    "duration_factor": 0.3,  # 时长缩短到30%
                    "narrative_density": 2.0,  # 叙事密度提高1倍
                },
                "互动剧": {
                    "branching_factor": 2.5,  # 分支因子
                    "minimal_branches": 2,  # 最少分支数
                },
                "广播剧": {
                    "audio_hints": True,  # 使用声音提示
                    "voice_emphasis": 1.5,  # 语音强调因子
                },
                "漫画": {
                    "visual_emphasis": True,  # 视觉强调
                    "keyword_highlighting": True,  # 关键词突出显示
                }
            },
            "pattern_adaptation": {
                "opening": {
                    "short_video": "compress",  # 压缩
                    "interactive": "branch_setup",  # 设置分支
                    "radio_drama": "audio_intro",  # 音频介绍
                    "comic": "visual_hook",  # 视觉钩子
                },
                "climax": {
                    "short_video": "intensify",  # 强化
                    "interactive": "decision_point",  # 决策点
                    "radio_drama": "audio_peak",  # 音频高潮
                    "comic": "dramatic_panel",  # 戏剧性面板
                }
            }
        }
        
        # 合并外部配置
        if config:
            self._deep_merge_config(self.config, config)
    
    def _deep_merge_config(self, base_config, new_config):
        """深度合并配置"""
        if not isinstance(new_config, dict):
            return
            
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._deep_merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _init_adaptation_rules(self):
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
    
    def adapt_pattern(self, pattern, target_media_type):
        """将模式适配到目标媒介类型"""
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
    
    def _get_adaptation_method(self, pattern_type, target_media_type):
        """获取适配方法"""
        # 获取英文媒介类型
        en_media_type = self.reverse_media_mapping.get(target_media_type, "unknown")
        
        # 从配置中获取适配方法
        pattern_adaptation = self.config.get("pattern_adaptation", {})
        type_adaptations = pattern_adaptation.get(pattern_type, {})
        
        return type_adaptations.get(en_media_type, "default")
    
    def _get_current_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _shorten_duration(self, pattern, factor=0.3):
        """缩短模式时长"""
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
    
    def _add_branching(self, pattern):
        """添加分支结构"""
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
    
    def _enhance_audio(self, pattern):
        """增强音频特性"""
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
        else:
            pattern["audio_cues"] = ["transition_sound", "background_ambience"]
        
        # 添加广播剧专属属性
        pattern["audio_narrative"] = True
        pattern["voice_acting_emphasis"] = True
        
        return pattern
    
    def _highlight_keywords(self, pattern):
        """突出关键词"""
        # 获取漫画配置
        comic_config = self.config.get("adaptation_rules", {}).get("漫画", {})
        
        # 添加关键词突出属性
        pattern["keywords_highlighted"] = True
        
        # 添加漫画面板相关属性
        if pattern["type"] == "opening":
            pattern["panel_layout"] = "establishing"
            pattern["transition_type"] = "scene"
        elif pattern["type"] == "climax":
            pattern["panel_layout"] = "dynamic"
            pattern["transition_type"] = "action"
        else:
            pattern["panel_layout"] = "standard"
            pattern["transition_type"] = "moment"
        
        # 强化视觉表现
        pattern["visual_emphasis"] = True
        pattern["symbolic_elements"] = True
        
        # 添加漫画专属属性
        pattern["panel_based"] = True
        pattern["visual_narrative"] = True
        
        return pattern
    
    def batch_adapt_patterns(self, patterns, target_media_type):
        """批量适配模式"""
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
    
    def get_supported_media_types(self):
        """获取支持的媒介类型"""
        return self.config.get("media_types", [])


def create_sample_pattern(pattern_id, pattern_type):
    """创建样本模式"""
    pattern = {
        "id": pattern_id,
        "type": pattern_type,
        "media_type": "电影",  # 默认为电影类型
        "description": f"{pattern_type.capitalize()}类型叙事模式",
        "frequency": random.uniform(0.6, 0.9),
        "position": {
            "opening": 0.1,
            "climax": 0.7,
            "conflict": 0.4,
            "transition": random.uniform(0.2, 0.8),
            "resolution": 0.8,
            "ending": 0.9
        }.get(pattern_type, random.uniform(0.2, 0.8)),
        "duration": {
            "opening": random.uniform(60, 120),
            "climax": random.uniform(120, 240),
            "conflict": random.uniform(90, 180),
            "transition": random.uniform(30, 60),
            "resolution": random.uniform(60, 120),
            "ending": random.uniform(60, 120)
        }.get(pattern_type, random.uniform(60, 180)),
        "sentiment": {
            "opening": random.uniform(0.2, 0.5),
            "climax": random.uniform(-0.8, 0.8),
            "conflict": random.uniform(-0.8, -0.3),
            "transition": random.uniform(-0.2, 0.2),
            "resolution": random.uniform(0.3, 0.7),
            "ending": random.uniform(0.2, 0.8)
        }.get(pattern_type, random.uniform(-0.3, 0.3)),
        "keywords": get_sample_keywords(pattern_type),
        "narrative_density": random.uniform(0.7, 1.0),
        "visual_complexity": random.uniform(0.6, 0.9),
        "audio_elements": ["dialogue", "music", "sound_effects"],
        "pacing": random.uniform(0.5, 0.8),
        "impact_score": random.uniform(0.65, 0.9)
    }
    
    return pattern


def get_sample_keywords(pattern_type):
    """获取样本关键词"""
    keywords_map = {
        "opening": ["开场", "介绍", "背景", "设定", "人物", "环境"],
        "climax": ["高潮", "转折", "惊喜", "震撼", "失败", "成功", "情感"],
        "conflict": ["冲突", "对抗", "矛盾", "挑战", "障碍", "危机"],
        "transition": ["过渡", "转换", "变化", "调整", "变动"],
        "resolution": ["解决", "结局", "和解", "理解", "成长"],
        "ending": ["结束", "落幕", "告别", "离开", "新起点"]
    }
    
    all_keywords = keywords_map.get(pattern_type, ["关键", "重要", "核心"])
    return random.sample(all_keywords, min(3, len(all_keywords)))


def generate_sample_patterns(count=6):
    """生成样本模式"""
    pattern_types = ["opening", "climax", "conflict", "transition", "resolution", "ending"]
    patterns = []
    
    for i in range(count):
        pattern_type = pattern_types[i % len(pattern_types)]
        pattern_id = f"pattern_{i+1}"
        pattern = create_sample_pattern(pattern_id, pattern_type)
        patterns.append(pattern)
    
    return patterns


def print_pattern_summary(pattern, prefix=""):
    """打印模式摘要"""
    logger.info(f"{prefix}模式ID: {pattern['id']}")
    logger.info(f"{prefix}模式类型: {pattern['type']}")
    logger.info(f"{prefix}媒介类型: {pattern['media_type']}")
    logger.info(f"{prefix}描述: {pattern['description']}")
    logger.info(f"{prefix}位置: {pattern['position']:.2f}")
    logger.info(f"{prefix}时长: {pattern['duration']:.2f}秒")
    
    if "adaptation_method" in pattern:
        logger.info(f"{prefix}适配方法: {pattern['adaptation_method']}")
    
    if "keywords_highlighted" in pattern:
        logger.info(f"{prefix}关键词突出: {pattern['keywords_highlighted']}")
    
    if "audio_enhanced" in pattern:
        logger.info(f"{prefix}音频增强: {pattern['audio_enhanced']}")
    
    if "has_branches" in pattern:
        logger.info(f"{prefix}分支数量: {pattern['branch_points']}")
    
    logger.info(f"{prefix}{'='*40}")


def main():
    """主函数"""
    logger.info("开始跨媒介模式迁移独立演示")
    
    # 初始化跨媒介适配器
    adapter = SimpleCrossMediaAdapter()
    logger.info("跨媒介适配器初始化完成")
    
    # 获取支持的媒介类型
    media_types = adapter.get_supported_media_types()
    logger.info(f"支持的媒介类型: {', '.join(media_types)}")
    
    # 生成样本模式
    patterns = generate_sample_patterns(6)
    logger.info(f"生成了 {len(patterns)} 个样本模式")
    
    # 打印原始模式
    logger.info("\n原始模式示例:")
    print_pattern_summary(patterns[0])
    
    # 演示适配到不同媒介类型
    target_media_types = ["短视频", "互动剧", "广播剧", "漫画"]
    
    for i, target_media_type in enumerate(target_media_types):
        # 选择一个模式进行适配
        source_pattern = patterns[i % len(patterns)]
        
        logger.info(f"\n将模式 {source_pattern['id']} 适配到 {target_media_type}")
        
        # 适配模式
        adapted_pattern = adapter.adapt_pattern(source_pattern, target_media_type)
        
        # 打印适配后的模式
        logger.info(f"适配后的 {target_media_type} 模式:")
        print_pattern_summary(adapted_pattern, "  ")
        
        # 添加间隔
        logger.info("\n" + "-" * 60 + "\n")
    
    # 演示批量适配
    target_media = "短视频"
    logger.info(f"\n批量将模式适配到 {target_media}")
    
    # 批量适配
    start_time = time.time()
    adapted_patterns = adapter.batch_adapt_patterns(patterns, target_media)
    elapsed_time = time.time() - start_time
    
    logger.info(f"成功适配 {len(adapted_patterns)} 个模式到 {target_media}，耗时 {elapsed_time:.2f} 秒")
    
    logger.info("\n跨媒介模式迁移独立演示完成")


if __name__ == "__main__":
    main() 