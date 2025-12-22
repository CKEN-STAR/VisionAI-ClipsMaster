import math

from src.utils.memory_config import get_memory_config, reload_memory_config
from src.utils import memory_probes as mp


def test_get_memory_config_defaults_and_ranges():
    cfg = get_memory_config(refresh=True)
    assert 0.0 < cfg["threshold_warning"] < 1.0
    assert 0.0 < cfg["threshold_critical"] <= 1.0
    assert 0.0 < cfg["gc_threshold"] <= 1.0
    assert 0.0 < cfg["aggressive_threshold"] <= 1.0
    assert isinstance(cfg.get("pressurer", {}), dict)


def test_memory_probes_overlay_matches_config():
    cfg = get_memory_config(refresh=True)
    # PROBE_CONFIG should reflect central config values
    assert math.isclose(mp.PROBE_CONFIG["threshold_warning"], cfg["threshold_warning"], rel_tol=1e-6)
    assert math.isclose(mp.PROBE_CONFIG["threshold_critical"], cfg["threshold_critical"], rel_tol=1e-6)
    assert math.isclose(mp.PROBE_CONFIG["gc_threshold"], cfg["gc_threshold"], rel_tol=1e-6)
    assert math.isclose(mp.PROBE_CONFIG["aggressive_threshold"], cfg["aggressive_threshold"], rel_tol=1e-6)

