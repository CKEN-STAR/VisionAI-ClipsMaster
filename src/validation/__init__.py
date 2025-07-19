#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证沙盒包

提供用于验证脚本质量的工具，检测剧情漏洞、角色一致性问题和情感流程缺陷等。
"""

from src.validation.sandbox import (
    validate_script,
    visualize_sandbox,
    SandboxValidator
)

from src.validation.character_behavior_analyzer import (
    CharacterPersonaDatabase,
    CharacterBehaviorValidator,
    validate_character_behavior
)

__all__ = [
    'validate_script', 
    'visualize_sandbox', 
    'SandboxValidator',
    'CharacterPersonaDatabase',
    'CharacterBehaviorValidator',
    'validate_character_behavior'
] 