# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any

from src.core.screenplay_engineer import ScreenplayEngineer
# 避免触发 src.quality.__init__ 的重载依赖（如 torch），按文件路径惰性加载 dynamic_probes
import importlib.util

def _load_dynamic_probes_module():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    mod_path = os.path.join(root, "src", "quality", "dynamic_probes.py")
    spec = importlib.util.spec_from_file_location("dyn_probes", mod_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod

dyn_probes = _load_dynamic_probes_module()
QualityProbe = dyn_probes.QualityProbe


def _mk_segments() -> List[Dict[str, Any]]:
    return [
        {"start_time": 0.0, "end_time": 2.0, "text": "A"},
        {"start_time": 10.0, "end_time": 12.0, "text": "B"},  # 有 8s 缝隙
        {"start_time": 12.0, "end_time": 15.0, "text": "C"},
    ]


def test_postprocess_bridging_and_time_axis():
    eng = ScreenplayEngineer()
    segments = _mk_segments()
    out = eng._postprocess_screenplay_for_coherence(
        segments,
        language="zh",
        gap_threshold=2.0,
        enable_bridging=True,
    )

    # 桥接短语注入（第二段应被加前缀）
    assert out[1]["text"] != "B"
    assert out[1]["text"].startswith(("与此同时", "随后", "转眼间", "这时", "接着"))

    # 输出时间轴线性化
    assert out[0]["output_start"] == 0.0 and out[0]["output_end"] == 2.0
    assert out[1]["output_start"] == 2.0 and out[1]["output_end"] == 4.0
    assert out[2]["output_start"] == 4.0 and out[2]["output_end"] == 7.0


def test_postprocess_disable_bridging():
    eng = ScreenplayEngineer()
    segments = _mk_segments()
    out = eng._postprocess_screenplay_for_coherence(
        segments,
        language="zh",
        gap_threshold=2.0,
        enable_bridging=False,
    )
    assert out[1]["text"] == "B"


def test_export_srt_uses_output_axis(tmp_path):
    eng = ScreenplayEngineer()
    segments = [
        {"start_time": 0.0, "end_time": 2.0, "output_start": 0.0, "output_end": 1.0, "text": "ONE"},
        {"start_time": 10.0, "end_time": 12.0, "output_start": 1.0, "output_end": 2.0, "text": "TWO"},
    ]
    out_path = tmp_path / "test.srt"
    ok = eng.export_srt(segments, str(out_path))
    assert ok
    content = out_path.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:01,000" in content
    assert "00:00:01,000 --> 00:00:02,000" in content


def test_narrative_coherence_on_output_axis():
    probe = QualityProbe()
    segments = [
        {"output_start": 0.0, "output_end": 1.0},
        {"output_start": 1.0, "output_end": 2.0},
        {"output_start": 2.0, "output_end": 3.0},
    ]
    score = probe.analyze_narrative_coherence(segments)
    assert score >= 0.99

