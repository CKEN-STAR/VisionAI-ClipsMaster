"""
多模态对齐模块

此模块提供视频-文本多模态内容的对齐和同步功能，包括：
1. 视频与字幕的同步检查
2. 视频关键帧提取与文本的对齐
3. 场景识别与文本关联
4. 视觉-文本内容一致性验证
"""

__version__ = "0.1.0"

# 延迟导入,避免cv2循环导入问题
def __getattr__(name):
    """延迟导入模块属性"""
    if name == 'AudioVisualAligner':
        from src.alignment.multimodal_sync import AudioVisualAligner
        return AudioVisualAligner
    elif name == 'SceneAnalyzer':
        from src.alignment.scene_analyzer import SceneAnalyzer
        return SceneAnalyzer
    elif name == 'extract_keyframes':
        from src.alignment.keyframe_extractor import extract_keyframes
        return extract_keyframes
    elif name == 'SceneCacheManager':
        from src.alignment.scene_cache_manager import SceneCacheManager
        return SceneCacheManager
    elif name == 'get_cache_manager':
        from src.alignment.scene_cache_manager import get_cache_manager
        return get_cache_manager
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'AudioVisualAligner',
    'SceneAnalyzer',
    'extract_keyframes',
    'SceneCacheManager',
    'get_cache_manager',
]
