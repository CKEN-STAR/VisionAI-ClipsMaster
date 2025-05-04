"""
英文节拍分析器模块

专门针对英文短剧文本的叙事节拍分析，用于识别英文文本中的
叙事结构和节奏单元。特性：
1. 英文句法分析
2. 情感和意图识别
3. 基于位置和语义的节拍分类
4. 英文叙事特定转折点识别
"""

import os
import re
import json
import yaml
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

# 尝试导入NLP工具 - 当英文模型可用时
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    logger.warning("NLTK未安装，英文节拍分析将使用基础方法")
    NLTK_AVAILABLE = False

from src.nlp.sentiment_analyzer import analyze_text_sentiment
from src.utils.memory_guard import track_memory

# 英文节拍特征词汇和标记
EN_BEAT_FEATURES = {
    "exposition": {
        "keywords": [
            "once", "one day", "there was", "there were", "lived", "used to",
            "first", "began", "started", "introduced", "met", "discovered",
            "noticed", "realized", "knew", "understood", "moved", "went"
        ],
        "patterns": [
            r"^(Once|One day|In the beginning|Long ago|There was)",
            r"\bintroduced\b",
            r"\bset in\b"
        ],
        "sentiment_range": (-0.3, 0.3),
        "intensity_threshold": 0.4
    },
    "rising_action": {
        "keywords": [
            "suddenly", "however", "but", "yet", "although", "despite", 
            "nevertheless", "still", "while", "as", "when", "during",
            "began to", "started to", "tried to", "wanted to", "needed to",
            "had to", "decided to", "planned to", "attempted to"
        ],
        "patterns": [
            r"\b(but|however|yet)\b",
            r"\bsuddenly\b",
            r"\bbegan to\b"
        ],
        "sentiment_range": (-0.7, 0.7),
        "intensity_threshold": 0.5
    },
    "climax": {
        "keywords": [
            "finally", "at last", "ultimately", "in the end", "eventually",
            "suddenly", "instantly", "immediately", "all at once", "abruptly",
            "exploded", "erupted", "shouted", "screamed", "yelled", "burst",
            "shocked", "horrified", "terrified", "amazed", "astonished",
            "never", "ever", "always", "must", "absolutely", "completely"
        ],
        "patterns": [
            r".*[!]{1,}$",
            r".*[?]{2,}$",
            r"\b(screamed|yelled|shouted|exclaimed)\b"
        ],
        "sentiment_range": (-1.0, 1.0),
        "intensity_threshold": 0.7
    },
    "resolution": {
        "keywords": [
            "finally", "at last", "in the end", "eventually", "after that",
            "since then", "from that day", "learned", "understood", "realized",
            "knew", "accepted", "decided", "changed", "became", "returned",
            "left", "ended", "finished", "completed", "concluded", "thereafter"
        ],
        "patterns": [
            r".*\.$",
            r"\b(finally|at last|in the end)\b",
            r"\b(thus|therefore|so|hence)\b"
        ],
        "sentiment_range": (-0.5, 0.8),
        "intensity_threshold": 0.5
    }
}


class EnBeatAnalyzer:
    """英文节拍分析器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化英文节拍分析器
        
        Args:
            config_path: 配置文件路径，为None时使用默认配置
        """
        self.config = self._load_config(config_path)
        self._init_resources()
        logger.info("英文节拍分析器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "beat_features": EN_BEAT_FEATURES,
            "similarity_threshold": 0.6,
            "context_window": 2,
            "position_weight": 0.3,
            "sentiment_weight": 0.3,
            "keyword_weight": 0.4,
            "minimum_beat_length": 5,
            "combine_threshold": 0.7
        }
        
        # 如果提供了配置路径，尝试加载自定义配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = yaml.safe_load(f)
                    # 递归合并配置
                    default_config = self._merge_configs(default_config, custom_config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """递归合并配置字典"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _init_resources(self):
        """初始化资源"""
        # 从配置加载节拍特征
        self.beat_features = self.config.get("beat_features", EN_BEAT_FEATURES)
        
        # 预编译正则表达式模式
        for beat_type, features in self.beat_features.items():
            if "patterns" in features:
                compiled_patterns = []
                for pattern in features["patterns"]:
                    try:
                        compiled_patterns.append(re.compile(pattern))
                    except re.error as e:
                        logger.error(f"正则表达式编译错误: {pattern}, {e}")
                features["compiled_patterns"] = compiled_patterns
        
        # 初始化NLTK资源 (如果可用)
        if NLTK_AVAILABLE:
            try:
                nltk.download('punkt', quiet=True)
            except Exception as e:
                logger.error(f"NLTK资源下载失败: {e}")
        
        # 构建关键词索引
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """构建节拍关键词索引"""
        self.keyword_to_beat = {}
        for beat_type, features in self.beat_features.items():
            if "keywords" in features:
                for keyword in features["keywords"]:
                    if keyword in self.keyword_to_beat:
                        self.keyword_to_beat[keyword].append(beat_type)
                    else:
                        self.keyword_to_beat[keyword] = [beat_type]
    
    @track_memory("en_beat_analysis")
    def predict_beats(self, text: str) -> List[Dict[str, Any]]:
        """
        预测英文文本的叙事节拍
        
        Args:
            text: 待分析的英文文本
            
        Returns:
            节拍列表
        """
        # 基础功能实现 (将在未来英文模型可用时完善)
        logger.info("英文叙事节拍分析触发 - 基础版实现")
        return []  # 当前返回空列表，将来完善实现 