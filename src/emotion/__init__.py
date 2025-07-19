#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感分析包

提供情感分析、情感强度图谱构建和情感流程检测功能。
用于增强视频混剪的情感表达和叙事效果。
"""

from src.emotion.intensity_mapper import EmotionMapper, build_intensity_curve
from src.emotion.visualizer import EmotionVisualizer, visualize_intensity_curve
from src.emotion.focus_locator import EmotionFocusLocator, locate_emotional_cores, find_emotion_focus_ranges
from src.emotion.lexicon_enhancer import EmotionLexicon, intensify_text, reduce_emotion, adjust_emotion_level
from src.emotion.multimodal_resonance import EmotionalResonance, apply_multimodal_resonance, process_script_with_resonance
from src.emotion.rhythm_tuner import EmotionRhythm, adjust_pacing, process_scene_sequence
from src.emotion.consistency_check import EmotionValidator, validate_emotion_consistency, get_consistency_suggestions
from src.emotion.memory_trigger import EmotionMemoryTrigger, implant_memory_hooks

__all__ = [
    'EmotionMapper', 
    'build_intensity_curve', 
    'EmotionVisualizer', 
    'visualize_intensity_curve',
    'EmotionFocusLocator',
    'locate_emotional_cores',
    'find_emotion_focus_ranges',
    'EmotionLexicon',
    'intensify_text',
    'reduce_emotion',
    'adjust_emotion_level',
    'EmotionalResonance',
    'apply_multimodal_resonance',
    'process_script_with_resonance',
    'EmotionRhythm',
    'adjust_pacing',
    'process_scene_sequence',
    'EmotionValidator',
    'validate_emotion_consistency',
    'get_consistency_suggestions',
    'EmotionMemoryTrigger',
    'implant_memory_hooks'
] 