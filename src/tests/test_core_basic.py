import pytest
from src.core import term_recommender, custom_terms, data_validator, input_sanitizer, degradation, model_validator, auto_recovery, language_detector, model_switcher, resume_loader, unload_manager, memory_mapper, preloader, cache_manager, model_sharding, fallback_engine

def test_term_recommender_basic(base_config):
    recommender = term_recommender.TermRecommender()
    result = recommender.recommend("测试术语")
    assert isinstance(result, list)

def test_custom_terms_load(base_config):
    terms = custom_terms.CustomTerms()
    assert hasattr(terms, 'get_terms')

def test_data_validator_valid(base_config):
    validator = data_validator.DataValidator()
    assert validator.validate({}) is not None

def test_input_sanitizer_clean(base_config):
    sanitizer = input_sanitizer.InputSanitizer()
    assert hasattr(sanitizer, 'sanitize')

def test_degradation_manager(base_config):
    manager = degradation.DegradationManager()
    state = manager.get_state()
    assert 'video_quality' in state

def test_model_validator_basic(base_config):
    validator = model_validator.ModelValidator()
    assert hasattr(validator, 'validate')

def test_auto_recovery_strategy(base_config):
    assert hasattr(auto_recovery, 'execute_strategies')

def test_language_detector_detect(base_config):
    detector = language_detector.LanguageDetector()
    assert hasattr(detector, 'detect')

def test_model_switcher_switch(base_config):
    switcher = model_switcher.ModelSwitcher()
    assert hasattr(switcher, 'switch')

def test_resume_loader_load(base_config):
    loader = resume_loader.ResumeLoader()
    assert hasattr(loader, 'load')

def test_unload_manager_unload(base_config):
    manager = unload_manager.UnloadManager()
    assert hasattr(manager, 'unload')

def test_memory_mapper_map(base_config):
    mapper = memory_mapper.MemoryMapper()
    assert hasattr(mapper, 'map')

def test_preloader_preload(base_config):
    pre = preloader.Preloader()
    assert hasattr(pre, 'preload')

def test_cache_manager_cache(base_config):
    manager = cache_manager.CacheManager()
    assert hasattr(manager, 'cache')

def test_model_sharding_shard(base_config):
    sharder = model_sharding.ModelSharding()
    assert hasattr(sharder, 'shard')

def test_fallback_engine_status(base_config):
    engine = fallback_engine.FallbackEngine()
    status = engine.get_fallback_status()
    assert isinstance(status, dict) 