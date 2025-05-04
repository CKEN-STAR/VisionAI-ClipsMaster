#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 受众/用户分析模块

包含用户行为追踪、偏好分析、画像构建以及个性化和内容适配功能。
"""

# 尝试导入各个组件，如果导入失败则跳过
try:
    from src.audience.profile_builder import (
        UserProfileEngine, 
        get_profile_engine, 
        get_user_profile
    )
except ImportError:
    pass

try:
    from src.audience.preference_analyzer import PreferenceAnalyzer
except ImportError:
    pass

try:
    from src.audience.behavior_tracker import BehaviorTracker
except ImportError:
    pass

try:
    from src.audience.content_morpher import (
        ContentMorpher, 
        adapt_content, 
        enhance_for_audience
    )
except ImportError:
    pass

try:
    from src.audience.cross_platform import (
        PlatformAdapter, 
        adapt_for_platform, 
        get_platform_specs
    )
except ImportError:
    pass

try:
    from src.audience.privacy_guard import (
        PrivacyGuard, 
        anonymize_content, 
        check_privacy_compliance
    )
except ImportError:
    pass

try:
    from src.audience.ab_router import (
        ABTestRouter, 
        route_to_variant, 
        create_test_variants
    )
except ImportError:
    pass

try:
    from src.audience.cognitive_optimizer import (
        CognitiveOptimizer, 
        optimize_cognitive_load, 
        analyze_cognitive_factors
    )
except ImportError:
    pass

try:
    from src.audience.generation_gap import (
        GenerationBridge,
        detect_content_generation,
        bridge_gap,
        insert_cultural_elements
    )
except ImportError:
    pass

try:
    from src.audience.evolution_tracker import (
        PreferenceEvolution,
        detect_preference_shift,
        track_preference_changes,
        get_preference_evolution_summary
    )
except ImportError:
    pass

# 直接暴露重要函数
def get_generation_bridge():
    """获取代际差异桥接器实例"""
    try:
        from src.audience.generation_gap import GenerationBridge
        return GenerationBridge()
    except ImportError:
        return None

def get_preference_evolution_tracker():
    """获取偏好进化追踪器实例"""
    try:
        from src.audience.evolution_tracker import PreferenceEvolution
        return PreferenceEvolution()
    except ImportError:
        return None

def get_cognitive_optimizer():
    """获取认知负载优化器实例"""
    try:
        from src.audience.cognitive_optimizer import CognitiveOptimizer
        return CognitiveOptimizer()
    except ImportError:
        return None

def get_ab_router():
    """获取AB测试路由器实例"""
    try:
        from src.audience.ab_router import ABTestRouter
        return ABTestRouter()
    except ImportError:
        return None

def get_privacy_guard():
    """获取隐私保护器实例"""
    try:
        from src.audience.privacy_guard import PrivacyGuard
        return PrivacyGuard()
    except ImportError:
        return None

def get_platform_adapter():
    """获取跨平台适配器实例"""
    try:
        from src.audience.cross_platform import PlatformAdapter
        return PlatformAdapter()
    except ImportError:
        return None

def get_content_morpher():
    """获取内容变形器实例"""
    try:
        from src.audience.content_morpher import ContentMorpher
        return ContentMorpher()
    except ImportError:
        return None

# 模块版本信息
__version__ = "0.8.0" 