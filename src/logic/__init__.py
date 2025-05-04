#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
逻辑分析模块

提供用于分析和验证混剪剧本逻辑的工具，包括时空连续性、角色行为一致性等。
"""

from src.logic.spatiotemporal_checker import (
    SpatiotemporalValidator,
    validate_spatiotemporal_logic,
    parse_time_ms,
    format_time_ms
)

from src.logic.prop_continuity import (
    PropTracker,
    track_props
)

from src.logic.causality_engine import (
    CausalityValidator,
    validate_causality,
    CausalityType,
    EventNode
)

from src.logic.dialogue_validator import (
    DialogueValidator,
    validate_dialogue_consistency
)

from src.logic.emotion_continuity import (
    EmotionTransitionMonitor,
    validate_emotion_continuity,
    EmotionCategory,
    EmotionDiscontinuityError
)

from src.logic.conflict_resolution import (
    ConflictResolver,
    validate_conflict_resolution,
    ConflictType,
    ResolutionMethod,
    ConflictResolutionError
)

from src.logic.multithread_coordinator import (
    NarrativeThreadIntegrator,
    validate_narrative_thread_consistency,
    NarrativeRelationType,
    ThreadConsistencyProblem,
    NarrativeEvent,
    NarrativeThread,
    NarrativeThreadError
)

from src.logic.cultural_validator import (
    CulturalContextChecker,
    validate_cultural_context,
    CulturalEra,
    CulturalRegion,
    CulturalErrorType,
    CulturalRule,
    CulturalError
)

from src.logic.sandbox_detector import (
    LogicSandbox,
    validate_logic_sandbox,
    LogicDefectType,
    LogicDefect,
    LogicSandboxError
)

__all__ = [
    'SpatiotemporalValidator',
    'validate_spatiotemporal_logic',
    'parse_time_ms',
    'format_time_ms',
    'PropTracker',
    'track_props',
    'CausalityValidator',
    'validate_causality',
    'CausalityType',
    'EventNode',
    'DialogueValidator',
    'validate_dialogue_consistency',
    'EmotionTransitionMonitor',
    'validate_emotion_continuity',
    'EmotionCategory',
    'EmotionDiscontinuityError',
    'ConflictResolver',
    'validate_conflict_resolution',
    'ConflictType',
    'ResolutionMethod',
    'ConflictResolutionError',
    'NarrativeThreadIntegrator',
    'validate_narrative_thread_consistency',
    'NarrativeRelationType',
    'ThreadConsistencyProblem',
    'NarrativeEvent',
    'NarrativeThread',
    'NarrativeThreadError',
    'CulturalContextChecker',
    'validate_cultural_context',
    'CulturalEra',
    'CulturalRegion',
    'CulturalErrorType',
    'CulturalRule',
    'CulturalError',
    'LogicSandbox',
    'validate_logic_sandbox',
    'LogicDefectType',
    'LogicDefect',
    'LogicSandboxError'
] 