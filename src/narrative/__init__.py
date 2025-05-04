"""
叙事锚点和结构模块

提供识别关键情节锚点和选择最佳叙事结构的功能，用于构建和优化叙事结构
"""

from src.narrative.anchor_detector import AnchorDetector
from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.narrative.structure_selector import StructureSelector, select_narrative_structure

__all__ = [
    'AnchorDetector', 'AnchorType', 'AnchorInfo',
    'StructureSelector', 'select_narrative_structure'
] 