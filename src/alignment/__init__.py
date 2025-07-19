"""
多模态对齐模块

此模块提供视频-文本多模态内容的对齐和同步功能，包括：
1. 视频与字幕的同步检查
2. 视频关键帧提取与文本的对齐
3. 场景识别与文本关联
4. 视觉-文本内容一致性验证
"""

from src.alignment.multimodal_sync import AudioVisualAligner
from src.alignment.scene_analyzer import SceneAnalyzer
from src.alignment.keyframe_extractor import extract_keyframes

__version__ = "0.1.0"

__all__ = [
    'AudioVisualAligner',
    'SceneAnalyzer',
    'extract_keyframes',
]
