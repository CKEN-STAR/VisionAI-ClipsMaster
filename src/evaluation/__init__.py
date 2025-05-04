"""
评估模块

提供内容质量评估、情感分析、叙事结构分析和观众参与度预测等功能。
"""

from src.evaluation.coherence_checker import (
    check_coherence,
    CoherenceMetrics
)

from src.evaluation.emotion_flow_evaluator import (
    evaluate_emotion_flow,
    EmotionMetrics
)

from src.evaluation.pacing_evaluator import (
    evaluate_pacing,
    PacingMetrics
)

from src.evaluation.narrative_structure_evaluator import (
    evaluate_narrative_structure,
    NarrativeMetrics
)

from src.evaluation.audience_engagement_predictor import (
    predict_engagement_score,
    EngagementFactors
)

__all__ = [
    'check_coherence',
    'CoherenceMetrics',
    'evaluate_emotion_flow',
    'EmotionMetrics',
    'evaluate_pacing',
    'PacingMetrics',
    'evaluate_narrative_structure',
    'NarrativeMetrics',
    'predict_engagement_score',
    'EngagementFactors'
]

from .pattern_evaluator import (
    PatternEvaluator,
    PatternFeature,
    evaluate_patterns,
    get_top_patterns,
    evaluate_and_explain
)

# 尝试导入解释器
try:
    from src.interpretability.pattern_explainer import explain_pattern, batch_explain_patterns
    has_explainer = True
except ImportError:
    has_explainer = False 