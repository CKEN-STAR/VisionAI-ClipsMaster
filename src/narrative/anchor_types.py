#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
锚点类型定义

定义剧本中的各种锚点类型和锚点信息数据结构。
锚点是指剧情中的重要转折点或关键点，它们在叙事结构中起着承上启下的作用。
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

class AnchorType(Enum):
    """锚点类型枚举"""
    
    EMOTION = "情感锚点"      # 情感高潮或低谷
    CHARACTER = "角色锚点"    # 角色相关转折点
    SUSPENSE = "悬念锚点"     # 设置或解决悬念
    CONFLICT = "冲突锚点"     # 冲突出现或升级
    REVELATION = "揭示锚点"   # 揭示重要信息
    TRANSITION = "转折锚点"   # 剧情转折点
    CLIMAX = "高潮锚点"       # 故事高潮点
    RESOLUTION = "解决锚点"   # 问题解决点

@dataclass
class AnchorInfo:
    """锚点信息数据类"""
    
    # 锚点类型
    anchor_type: AnchorType
    
    # 锚点在剧本中的位置
    start_idx: int  # 开始场景索引
    position: float  # 相对位置（0-1）
    
    # 锚点描述
    description: str
    
    # 置信度（0-1之间）
    confidence: float = 0.5
    
    # 重要性（0-1之间，由检测器计算）
    importance: float = 0.0
    
    # 相关场景索引
    related_scenes: List[int] = field(default_factory=list)
    
    # 对于悬念锚点，是否已解决
    is_resolved: bool = False
    
    # 对于悬念锚点，解决的场景索引
    resolution_idx: Optional[int] = None
    
    # 额外的自定义属性
    properties: Dict[str, Any] = field(default_factory=dict)

# 锚点类型参数配置
ANCHOR_PARAMS = {
    AnchorType.EMOTION: {
        "color": "#FF5733",  # 橙红色
        "min_confidence": 0.4,
        "priority": 3
    },
    AnchorType.CHARACTER: {
        "color": "#33FF57",  # 绿色
        "min_confidence": 0.5,
        "priority": 2
    },
    AnchorType.SUSPENSE: {
        "color": "#3357FF",  # 蓝色
        "min_confidence": 0.6,
        "priority": 5
    },
    AnchorType.CONFLICT: {
        "color": "#FF3333",  # 红色
        "min_confidence": 0.5,
        "priority": 4
    },
    AnchorType.REVELATION: {
        "color": "#FFFF33",  # 黄色
        "min_confidence": 0.6,
        "priority": 5
    },
    AnchorType.TRANSITION: {
        "color": "#33FFFF",  # 青色
        "min_confidence": 0.5,
        "priority": 3
    },
    AnchorType.CLIMAX: {
        "color": "#FF33FF",  # 紫色
        "min_confidence": 0.7,
        "priority": 5
    },
    AnchorType.RESOLUTION: {
        "color": "#AAAAAA",  # 灰色
        "min_confidence": 0.5,
        "priority": 4
    }
} 