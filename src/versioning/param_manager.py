#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数管理器模块 - 简化版

该模块负责管理和应用参数矩阵到剧本重构过程，提供动态参数调整和语言特定优化。
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import random

# 设置日志记录器
logger = logging.getLogger(__name__)

# 默认参数集
DEFAULT_PARAMS = {
    # 基本处理参数
    "language": "auto",             # 语言: "auto", "zh", "en"
    "model": "auto",                # 模型: "auto", "mistral", "qwen"
    "style": "viral",               # 风格: "viral", "formal", "casual", "dramatic"
    
    # 匹配检查参数
    "match": {
        "enabled": True,           # 是否启用匹配检查
        "threshold": 0.75,         # 匹配阈值，高于此值认为匹配成功
        "min_semantic_score": 0.6, # 最小语义相似度分数
        "max_content_drift": 0.3,  # 最大内容偏移度
        "check_style_match": True, # 是否检查风格匹配
        "check_emotion_match": True # 是否检查情感匹配
    },
    
    # 情感参数
    "emotion": {
        "amplify": 0.3,             # 情感放大系数
        "prefer_positive": True,    # 是否偏好积极情感
        "dramatize": 0.5,           # 戏剧化程度
        "surprise_factor": 0.2,     # 惊奇因子
        "maintain_arc": True,       # 保持情感弧
        "dimensions": {             # 各情感维度权重
            "drama": 0.7,           # 戏剧性
            "humor": 0.5,           # 幽默感
            "tension": 0.4,         # 紧张感
            "warmth": 0.3,          # 温暖感
            "urgency": 0.6,         # 紧迫感
            "surprise": 0.5         # 惊奇感
        }
    },
    
    # 重构参数
    "reconstruction": {
        "viral_prefix_rate": 0.3,    # 爆款前缀添加率
        "viral_suffix_rate": 0.2,    # 爆款后缀添加率
        "max_length_multiplier": 1.5, # 最大长度倍数
        "min_length_ratio": 0.8,     # 最小长度比例
        "preserve_key_information": 0.85, # 保留关键信息比例
        "creative_freedom": 0.4      # 创意自由度
    },
    
    # SRT格式处理参数
    "srt_format": {
        "preserve_timing": True,      # 保留原始时间码
        "adjust_duration": False,     # 调整持续时间
        "min_display_time": 1.0,      # 最小显示时间(秒)
        "max_chars_per_line": 40,     # 每行最大字符数
        "max_lines": 2,               # 最大行数
        "support_complex_format": True # 支持复杂SRT格式
    },
    
    # 高级参数
    "advanced": {
        "use_gpu": True,               # 使用GPU
        "batch_processing": True,      # 批处理
        "cache_results": True,         # 缓存结果
        "debug_mode": False            # 调试模式
    }
}

# 语言特定参数调整
LANGUAGE_ADJUSTMENTS = {
    "zh": {
        "reconstruction": {
            "viral_prefix_rate": 0.35,  # 中文前缀率略高
            "max_chars_per_line": 30    # 中文每行字符数更少
        },
        "emotion": {
            "amplify": 0.35             # 中文情感放大系数略高
        }
    },
    "en": {
        "reconstruction": {
            "viral_prefix_rate": 0.25,  # 英文前缀率略低
            "max_chars_per_line": 50    # 英文每行字符数更多
        },
        "emotion": {
            "dramatize": 0.4            # 英文戏剧化程度略低
        }
    }
}

# 不同风格的参数调整
STYLE_ADJUSTMENTS = {
    "viral": {
        "emotion": {
            "amplify": 0.4,          # 高情感放大
            "dramatize": 0.6         # 高戏剧化
        },
        "reconstruction": {
            "viral_prefix_rate": 0.4, # 高前缀率
            "viral_suffix_rate": 0.3  # 高后缀率
        }
    },
    "formal": {
        "emotion": {
            "amplify": 0.1,          # 低情感放大
            "dramatize": 0.2         # 低戏剧化
        },
        "reconstruction": {
            "viral_prefix_rate": 0.1, # 低前缀率
            "viral_suffix_rate": 0.05 # 低后缀率
        }
    },
    "casual": {
        "emotion": {
            "amplify": 0.2,          # 中等情感放大
            "prefer_positive": True   # 偏好积极情感
        },
        "reconstruction": {
            "creative_freedom": 0.6   # 高创意自由度
        }
    },
    "dramatic": {
        "emotion": {
            "dramatize": 0.8,         # 非常高的戏剧化
            "tension": 0.7            # 高紧张感
        },
        "reconstruction": {
            "viral_prefix_rate": 0.5   # 非常高的前缀率
        }
    }
}

# 根据内容特征调整参数
def adjust_by_content(content_analysis: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据内容分析结果调整参数
    
    Args:
        content_analysis: 内容分析结果
        params: 当前参数
        
    Returns:
        调整后的参数
    """
    adjusted_params = params.copy()
    
    # 提取内容特征
    avg_emotion = content_analysis.get("avg_emotion", 0.5)
    complexity = content_analysis.get("complexity", 0.5)
    has_dialogue = content_analysis.get("has_dialogue", False)
    
    # 根据平均情感调整
    if avg_emotion > 0.7:  # 高情感内容
        adjusted_params["emotion"]["amplify"] *= 0.8  # 减少放大，已经很情感化
    elif avg_emotion < 0.3:  # 低情感内容
        adjusted_params["emotion"]["amplify"] *= 1.5  # 增加放大，使其更情感化
    
    # 根据复杂性调整
    if complexity > 0.7:  # 高复杂度内容
        adjusted_params["reconstruction"]["max_length_multiplier"] *= 0.9  # 减少长度增长
        adjusted_params["reconstruction"]["preserve_key_information"] = 0.9  # 更多保留关键信息
    
    # 根据是否有对话调整
    if has_dialogue:
        adjusted_params["reconstruction"]["creative_freedom"] *= 0.8  # 减少创意自由度，对话要保持连贯
    
    return adjusted_params

def get_params(language: str = "auto", style: str = "viral", content_analysis: Optional[Dict[str, Any]] = None, custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    获取剧本重构参数，结合预设、语言特性和内容分析
    
    Args:
        language: 语言代码或"auto"自动检测
        style: 风格预设名称
        content_analysis: 内容分析结果
        custom_params: 自定义参数
        
    Returns:
        合并后的参数字典
    """
    # 从默认参数开始
    params = DEFAULT_PARAMS.copy()
    
    # 应用风格调整
    if style in STYLE_ADJUSTMENTS:
        style_adjustments = STYLE_ADJUSTMENTS[style]
        # 递归合并风格参数
        _deep_merge(params, style_adjustments)
    
    # 应用语言特定调整
    if language in LANGUAGE_ADJUSTMENTS:
        lang_adjustments = LANGUAGE_ADJUSTMENTS[language]
        # 递归合并语言参数
        _deep_merge(params, lang_adjustments)
    
    # 根据内容分析调整
    if content_analysis:
        params = adjust_by_content(content_analysis, params)
    
    # 应用自定义参数（如果有）
    if custom_params:
        _deep_merge(params, custom_params)
    
    # 更新记录语言和风格
    params["language"] = language
    params["style"] = style
    
    return params

def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    递归合并两个字典
    
    Args:
        target: 目标字典
        source: 源字典（其值将合并到目标字典）
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value

def save_params_to_file(params: Dict[str, Any], filepath: str) -> bool:
    """
    将参数保存到文件
    
    Args:
        params: 参数字典
        filepath: 文件路径
        
    Returns:
        bool: 是否成功保存
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存参数到文件失败: {e}")
        return False

def load_params_from_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    从文件加载参数
    
    Args:
        filepath: 文件路径
        
    Returns:
        Dict或None: 加载的参数字典，失败则返回None
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"从文件加载参数失败: {e}")
        return None

# 快捷函数
def prepare_params(language: str = "auto", style: str = "viral", custom_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    快捷函数：准备剧本重构参数
    
    Args:
        language: 语言代码或"auto"自动检测
        style: 风格预设名称
        custom_params: 自定义参数
        
    Returns:
        准备好的参数字典
    """
    # 简单内容分析
    mock_content_analysis = {
        "avg_emotion": random.uniform(0.3, 0.7),
        "complexity": random.uniform(0.3, 0.7),
        "has_dialogue": random.choice([True, False])
    }
    
    return get_params(language, style, mock_content_analysis, custom_params)

# 测试代码
if __name__ == "__main__":
    # 输出示例参数，用于说明
    import pprint
    
    # 中文病毒式风格
    zh_viral_params = prepare_params("zh", "viral")
    print("中文病毒式风格参数:")
    pprint.pprint(zh_viral_params)
    
    print("\n" + "-" * 50 + "\n")
    
    # 英文正式风格
    en_formal_params = prepare_params("en", "formal")
    print("英文正式风格参数:")
    pprint.pprint(en_formal_params)
    
    print("\n" + "-" * 50 + "\n")
    
    # 带自定义参数
    custom = {
        "emotion": {
            "amplify": 0.8  # 高情感放大
        },
        "reconstruction": {
            "creative_freedom": 0.8  # 高创意自由度
        }
    }
    custom_params = prepare_params("zh", "dramatic", custom)
    print("自定义戏剧化参数:")
    pprint.pprint(custom_params) 