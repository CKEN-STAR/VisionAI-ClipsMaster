"""
时间码处理模块

此模块提供与视频时间码相关的功能，包括：
1. 视频时长分析和计算
2. 时间码格式处理与转换
3. 视频帧率处理
4. 字幕时间点校准
5. 关键场景保护机制
6. 智能压缩算法
7. 毫秒级间隙消除
8. 安全余量管理
9. 过渡帧智能插入
10. 多轨时间轴对齐
11. 实时预览与可视化
12. 异常溢出处理
13. 版本化时间轴存档
"""

from .base_analyzer import BaseAnalyzer, analyze_source_duration, verify_duration
from .key_scene_protector import KeySceneGuard, mark_protected_scenes, verify_scene_protection
from .smart_compressor import SmartCompressor, compress_video, CompressionLevel
from .gap_eraser import GapEraser, eliminate_gaps
from .safety_margin import MarginKeeper, apply_safety_margin, adjust_for_safety
from .transition_inserter import TransitionInserter, insert_transitions, create_transition_frame, TransitionType
from .multi_track_align import (
    MultiTrackAligner, 
    align_audio_video, 
    stretch_video, 
    time_shift_audio, 
    align_multiple_tracks,
    AlignMethod
)
from .live_preview import (
    PreviewGenerator,
    generate_timeline_preview,
    generate_tracks_preview,
    generate_alignment_comparison
)
from .overflow_handler import (
    OverflowRescuer,
    handle_overflow,
    sum_duration,
    RescueMode,
    CriticalOverflowError
)
from .version_archiver import TimelineArchiver

__all__ = [
    'BaseAnalyzer',
    'analyze_source_duration',
    'verify_duration',
    'KeySceneGuard',
    'mark_protected_scenes',
    'verify_scene_protection',
    'SmartCompressor',
    'compress_video',
    'CompressionLevel',
    'GapEraser',
    'eliminate_gaps',
    'MarginKeeper',
    'apply_safety_margin',
    'adjust_for_safety',
    'TransitionInserter',
    'insert_transitions',
    'create_transition_frame',
    'TransitionType',
    'MultiTrackAligner',
    'align_audio_video',
    'stretch_video',
    'time_shift_audio',
    'align_multiple_tracks',
    'AlignMethod',
    'PreviewGenerator',
    'generate_timeline_preview',
    'generate_tracks_preview',
    'generate_alignment_comparison',
    'OverflowRescuer',
    'handle_overflow',
    'sum_duration',
    'RescueMode',
    'CriticalOverflowError',
    'TimelineArchiver',
] 