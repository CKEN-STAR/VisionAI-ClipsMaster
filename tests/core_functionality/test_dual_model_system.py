#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 双语言模型系统测试

测试范围:
1. Mistral-7B英文模型 + Qwen2.5-7B中文模型切换
2. 模型切换延迟测试 (≤1.5秒)
3. 语言检测准确性 (≥95%)
4. 内存管理和模型卸载
5. 并发模型切换稳定性
"""

import pytest
import time
import threading
from typing import Dict, Any
from unittest.mock import Mock, patch

from src.core.model_switcher import ModelSwitcher
from src.core.language_detector import LanguageDetector
from src.utils.memory_guard import MemoryGuard


class TestDualModelSystem:
    """双语言模型系统测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.model_switcher = ModelSwitcher()
        self.language_detector = LanguageDetector()
        self.memory_guard = MemoryGuard()
        
        # 测试语料
        self.test_texts = {
            "zh": [
                "今天天气真好，我们去公园散步吧",
                "这是一个关于爱情的故事",
                "突然间，一切都变了",
                "他们终于在一起了",
                "故事的结局很美好"
            ],
            "en": [
                "What a beautiful day, let's go to the park",
                "This is a story about love",
                "Suddenly, everything changed",
                "They finally got together",
                "The story has a happy ending"
            ],
            "mixed": [
                "Hello 你好 world 世界",
                "This is 这是 a test 测试",
                "English and 中文 mixed content"
            ]
        }

    def test_language_detection_accuracy(self):
        """测试语言检测准确性 (目标: ≥95%)"""
        correct_detections = 0
        total_tests = 0
        
        # 测试中文检测
        for text in self.test_texts["zh"]:
            detected = self.language_detector.detect_from_text(text)
            if detected == "zh":
                correct_detections += 1
            total_tests += 1
        
        # 测试英文检测
        for text in self.test_texts["en"]:
            detected = self.language_detector.detect_from_text(text)
            if detected == "en":
                correct_detections += 1
            total_tests += 1
        
        # 计算准确率
        accuracy = correct_detections / total_tests
        assert accuracy >= 0.95, f"语言检测准确率不足: {accuracy:.2%} (目标: ≥95%)"

    def test_model_switching_performance(self):
        """测试模型切换性能 (目标: ≤1.5秒)"""
        # 测试中文→英文切换
        start_time = time.time()
        zh_success = self.model_switcher.switch_model("zh")
        zh_switch_time = time.time() - start_time
        
        assert zh_success, "中文模型切换失败"
        assert zh_switch_time <= 1.5, f"中文模型切换时间过长: {zh_switch_time:.2f}s"
        
        # 测试英文→中文切换
        start_time = time.time()
        en_success = self.model_switcher.switch_model("en")
        en_switch_time = time.time() - start_time
        
        assert en_success, "英文模型切换失败"
        assert en_switch_time <= 1.5, f"英文模型切换时间过长: {en_switch_time:.2f}s"
        
        # 测试重复切换 (应该更快)
        start_time = time.time()
        repeat_success = self.model_switcher.switch_model("en")
        repeat_time = time.time() - start_time
        
        assert repeat_success, "重复模型切换失败"
        assert repeat_time <= 0.5, f"重复切换时间过长: {repeat_time:.2f}s"

    def test_model_availability_check(self):
        """测试模型可用性检查"""
        # 检查支持的模型
        available_models = self.model_switcher.available_models
        assert "zh" in available_models, "缺少中文模型配置"
        assert "en" in available_models, "缺少英文模型配置"
        
        # 检查模型文件路径
        assert available_models["zh"] == "qwen2.5-7b-zh", "中文模型名称错误"
        assert available_models["en"] == "mistral-7b-en", "英文模型名称错误"

    def test_current_model_tracking(self):
        """测试当前模型状态跟踪"""
        # 初始状态
        initial_model = self.model_switcher.get_current_model()
        
        # 切换到中文模型
        self.model_switcher.switch_model("zh")
        current_model = self.model_switcher.get_current_model()
        assert current_model == "qwen2.5-7b-zh", f"当前模型状态错误: {current_model}"
        
        # 切换到英文模型
        self.model_switcher.switch_model("en")
        current_model = self.model_switcher.get_current_model()
        assert current_model == "mistral-7b-en", f"当前模型状态错误: {current_model}"

    def test_model_loading_status(self):
        """测试模型加载状态检查"""
        # 检查模型是否已加载
        zh_loaded_before = self.model_switcher.is_model_loaded("zh")
        en_loaded_before = self.model_switcher.is_model_loaded("en")
        
        # 加载中文模型
        self.model_switcher.switch_model("zh")
        zh_loaded_after = self.model_switcher.is_model_loaded("zh")
        
        # 验证加载状态变化
        assert zh_loaded_after, "中文模型加载状态检查失败"

    def test_mixed_language_processing(self):
        """测试混合语言处理"""
        for mixed_text in self.test_texts["mixed"]:
            detected_lang = self.language_detector.detect_from_text(mixed_text)
            
            # 混合语言应该检测为主要语言
            assert detected_lang in ["zh", "en"], f"混合语言检测失败: {detected_lang}"
            
            # 模型切换应该成功
            switch_success = self.model_switcher.switch_model(detected_lang)
            assert switch_success, f"混合语言模型切换失败: {detected_lang}"

    def test_concurrent_model_switching(self):
        """测试并发模型切换稳定性"""
        results = []
        errors = []
        
        def switch_model_thread(language: str, thread_id: int):
            try:
                success = self.model_switcher.switch_model(language)
                results.append((thread_id, language, success))
            except Exception as e:
                errors.append((thread_id, language, str(e)))
        
        # 创建多个并发切换线程
        threads = []
        for i in range(5):
            lang = "zh" if i % 2 == 0 else "en"
            thread = threading.Thread(target=switch_model_thread, args=(lang, i))
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=10)
        
        # 验证结果
        assert len(errors) == 0, f"并发切换出现错误: {errors}"
        assert len(results) == 5, f"并发切换结果不完整: {len(results)}/5"
        
        # 验证所有切换都成功
        for thread_id, language, success in results:
            assert success, f"线程{thread_id}的{language}模型切换失败"

    def test_memory_management_during_switching(self):
        """测试模型切换时的内存管理"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行多次模型切换
        for _ in range(10):
            self.model_switcher.switch_model("zh")
            self.model_switcher.switch_model("en")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内
        assert memory_increase < 200, f"模型切换内存泄漏: {memory_increase:.2f}MB"

    def test_error_handling_invalid_language(self):
        """测试无效语言的错误处理"""
        # 测试不支持的语言
        invalid_languages = ["fr", "de", "ja", "ko", "invalid"]
        
        for lang in invalid_languages:
            success = self.model_switcher.switch_model(lang)
            assert not success, f"不应该支持语言: {lang}"
        
        # 当前模型状态不应该改变
        current_model = self.model_switcher.get_current_model()
        # 验证模型状态一致性

    def test_language_detection_edge_cases(self):
        """测试语言检测边界情况"""
        edge_cases = {
            "": "zh",  # 空字符串默认中文
            "   ": "zh",  # 空白字符默认中文
            "123456": "zh",  # 纯数字默认中文
            "!@#$%^&*()": "zh",  # 纯符号默认中文
            "a": "en",  # 单个英文字符
            "中": "zh",  # 单个中文字符
        }
        
        for text, expected_lang in edge_cases.items():
            detected = self.language_detector.detect_from_text(text)
            assert detected == expected_lang, f"边界情况检测错误: '{text}' -> {detected} (期望: {expected_lang})"

    @pytest.mark.performance
    def test_rapid_switching_stress(self):
        """测试快速切换压力测试"""
        start_time = time.time()
        switch_count = 0
        
        # 30秒内快速切换
        while time.time() - start_time < 30:
            lang = "zh" if switch_count % 2 == 0 else "en"
            success = self.model_switcher.switch_model(lang)
            if success:
                switch_count += 1
        
        # 验证切换性能
        total_time = time.time() - start_time
        avg_switch_time = total_time / switch_count if switch_count > 0 else float('inf')
        
        assert switch_count >= 20, f"切换次数不足: {switch_count}"
        assert avg_switch_time <= 1.5, f"平均切换时间过长: {avg_switch_time:.2f}s"

    def test_model_configuration_validation(self):
        """测试模型配置验证"""
        # 验证模型配置完整性
        switcher = ModelSwitcher()
        
        # 检查必要的配置项
        assert hasattr(switcher, 'available_models'), "缺少available_models配置"
        assert hasattr(switcher, 'model_cache'), "缺少model_cache配置"
        
        # 检查模型路径配置
        for lang, model_name in switcher.available_models.items():
            assert isinstance(model_name, str), f"{lang}模型名称类型错误"
            assert len(model_name) > 0, f"{lang}模型名称为空"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
