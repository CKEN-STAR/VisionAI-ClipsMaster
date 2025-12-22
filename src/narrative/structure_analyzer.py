#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
轻量级叙事结构分析器（兼容层）

部分模块依赖 `src.narrative.structure_analyzer.identify_narrative_beats`，
而代码库中缺失该模块/函数。此文件提供向后兼容的最小实现，
优先尝试基于锚点检测生成简要叙事节点；如失败则返回空映射，
让上层逻辑走默认分段路径（introduction/buildup/climax/resolution）。
"""
from typing import List, Dict, Any
from loguru import logger

try:
    from .anchor_detector import AnchorDetector
except Exception:
    AnchorDetector = None  # type: ignore


def identify_narrative_beats(scenes: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """识别叙事节点，返回 {scene_index: {"type": str, ...}} 的映射。
    - 优先基于 AnchorDetector 进行启发式识别
    - 失败或无结果时返回空字典，让调用方走默认分段逻辑
    """
    if not scenes:
        return {}

    try:
        if AnchorDetector is None:
            return {}

        detector = AnchorDetector()
        anchors = detector.detect_anchors(scenes) or []

        # 将部分锚点类型粗略映射为叙事节点类型
        mapping: Dict[int, Dict[str, Any]] = {}
        for a in anchors:
            try:
                idx = getattr(a, "start_idx", None)
                atype = getattr(a, "anchor_type", None)
                label = getattr(atype, "value", str(atype)) if atype is not None else "unknown"
                if idx is None:
                    continue
                if label in ("CLIMAX", "CONFLICT", "REVELATION"):
                    beat_type = "climax"
                elif label in ("TRANSITION", "SUSPENSE"):
                    beat_type = "buildup"
                elif label in ("RESOLUTION",):
                    beat_type = "resolution"
                else:
                    beat_type = "buildup"
                mapping[int(idx)] = {"type": beat_type, "source": "anchors"}
            except Exception:
                continue

        return mapping
    except Exception as e:
        logger.warning(f"identify_narrative_beats fallback: {e}")
        return {}

