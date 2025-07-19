#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本控制模块 - 简化版（UI演示用）

提供剧本版本管理功能，支持不同风格和参数设置。
"""

import time
from typing import Dict, List, Any, Optional
from enum import Enum

class SnapshotType(Enum):
    """快照类型枚举"""
    LINEAR = "初始线性版"
    REVERSED = "倒叙重构版"
    EXPERIMENTAL = "多线实验版"
    OPTIMIZED = "最终优化版"

def prepare_screenplay_params(
    original_subtitles: List[Dict[str, Any]],
    preset_name: Optional[str] = None,
    language: Optional[str] = None,
    custom_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    准备剧本参数 - 简化版（UI演示用）
    
    参数:
        original_subtitles: 原始字幕列表
        preset_name: 预设名称
        language: 语言代码
        custom_params: 自定义参数
        
    返回:
        参数字典
    """
    # 基础参数
    params = {
        "language": language or "auto",
        "pace": 1.0,                 # 节奏因子（大于1加快，小于1减慢）
        "context_preservation": 0.5, # 上下文保留度（0-1）
        "emotion_intensity": 0.7,    # 情感强度（0-1）
        "min_segment_duration": 1.5, # 最小片段时长（秒）
    }
    
    # 应用预设参数
    if preset_name:
        preset_params = _get_preset_params(preset_name)
        params.update(preset_params)
    
    # 应用自定义参数
    if custom_params:
        params.update(custom_params)
    
    return params

def _get_preset_params(preset_name: str) -> Dict[str, Any]:
    """获取预设参数"""
    presets = {
        "默认": {
            "pace": 1.0,
            "context_preservation": 0.5,
            "emotion_intensity": 0.7,
        },
        "快节奏": {
            "pace": 1.3,
            "context_preservation": 0.4,
            "emotion_intensity": 0.8,
        },
        "情感化": {
            "pace": 0.9,
            "context_preservation": 0.6,
            "emotion_intensity": 0.9,
        },
        "悬疑": {
            "pace": 0.8,
            "context_preservation": 0.7,
            "emotion_intensity": 0.8,
        },
        "励志": {
            "pace": 1.1,
            "context_preservation": 0.5,
            "emotion_intensity": 0.9,
        },
        "对比式": {
            "pace": 1.0,
            "context_preservation": 0.4,
            "emotion_intensity": 0.8,
        },
        "金字塔": {
            "pace": 1.2,
            "context_preservation": 0.5,
            "emotion_intensity": 0.7,
        },
        "三段式": {
            "pace": 1.0,
            "context_preservation": 0.6,
            "emotion_intensity": 0.7,
        }
    }
    
    return presets.get(preset_name, presets["默认"])

class SceneVersionManager:
    """场景版本管理器 - 简化版（UI演示用）"""
    
    def __init__(self, project_name: str):
        """初始化版本管理器"""
        self.project_name = project_name
        self.versions = {}
        self.version_tree = {}
        
    def save_scene_version(self, 
                           scenes: List[Dict[str, Any]], 
                           name: str,
                           snapshot_type: SnapshotType = SnapshotType.LINEAR,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """保存场景版本"""
        # 生成ID
        version_id = f"{int(time.time())}"
        
        # 收集元数据
        if metadata is None:
            metadata = {}
        
        # 保存版本
        self.versions[version_id] = {
            "id": version_id,
            "name": name,
            "type": snapshot_type.value,
            "timestamp": time.time(),
            "metadata": metadata,
            "scenes_count": len(scenes),
            "scenes": scenes
        }
        
        return version_id
    
    def load_scene_version(self, version_id: str) -> List[Dict[str, Any]]:
        """加载场景版本"""
        if version_id not in self.versions:
            return []
        
        return self.versions[version_id]["scenes"]
    
    def list_versions(self) -> List[Dict[str, Any]]:
        """列出所有版本"""
        return list(self.versions.values()) 