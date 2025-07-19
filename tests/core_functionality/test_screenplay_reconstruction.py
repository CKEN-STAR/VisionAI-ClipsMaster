#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster AI剧本重构核心逻辑测试

测试范围:
1. 原片字幕→剧情理解→重新编排→生成爆款字幕的完整流程
2. 双语言模型切换和处理能力
3. 剧本重构质量评估
4. 时间轴精度验证
"""

import pytest
import time
import json
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# 导入核心模块
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.narrative_analyzer import NarrativeAnalyzer
from src.core.model_switcher import ModelSwitcher
from src.core.language_detector import LanguageDetector


class TestScreenplayReconstruction:
    """AI剧本重构核心逻辑测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.screenplay_engineer = ScreenplayEngineer()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.model_switcher = ModelSwitcher()
        self.language_detector = LanguageDetector()
        
        # 测试数据
        self.sample_chinese_subtitles = [
            {"start_time": "00:00:01,000", "end_time": "00:00:03,000", "text": "今天天气真好"},
            {"start_time": "00:00:04,000", "end_time": "00:00:06,000", "text": "我们去公园散步吧"},
            {"start_time": "00:00:07,000", "end_time": "00:00:09,000", "text": "突然下起了雨"}
        ]
        
        self.sample_english_subtitles = [
            {"start_time": "00:00:01,000", "end_time": "00:00:03,000", "text": "What a beautiful day"},
            {"start_time": "00:00:04,000", "end_time": "00:00:06,000", "text": "Let's go to the park"},
            {"start_time": "00:00:07,000", "end_time": "00:00:09,000", "text": "Suddenly it started raining"}
        ]

    def test_complete_reconstruction_workflow_chinese(self):
        """测试中文剧本重构完整工作流程"""
        # 1. 语言检测
        detected_lang = self.language_detector.detect_from_text("今天天气真好")
        assert detected_lang == "zh", f"中文语言检测失败: {detected_lang}"
        
        # 2. 模型切换
        switch_success = self.model_switcher.switch_model("zh")
        assert switch_success, "中文模型切换失败"
        
        # 3. 剧本重构
        start_time = time.time()
        result = self.screenplay_engineer.generate_screenplay(
            self.sample_chinese_subtitles, 
            language="zh",
            preset_name="爆款"
        )
        reconstruction_time = time.time() - start_time
        
        # 验证结果
        assert result["language"] == "zh", "语言标识错误"
        assert len(result["screenplay"]) > 0, "重构剧本为空"
        assert reconstruction_time < 5.0, f"重构时间过长: {reconstruction_time:.2f}s"
        
        # 验证剧本质量
        screenplay = result["screenplay"]
        for segment in screenplay:
            assert "sentiment" in segment, "缺少情感标签"
            assert "start_time" in segment, "缺少开始时间"
            assert "end_time" in segment, "缺少结束时间"
            assert "text" in segment, "缺少文本内容"

    def test_complete_reconstruction_workflow_english(self):
        """测试英文剧本重构完整工作流程"""
        # 1. 语言检测
        detected_lang = self.language_detector.detect_from_text("What a beautiful day")
        assert detected_lang == "en", f"英文语言检测失败: {detected_lang}"
        
        # 2. 模型切换
        switch_success = self.model_switcher.switch_model("en")
        assert switch_success, "英文模型切换失败"
        
        # 3. 剧本重构
        result = self.screenplay_engineer.generate_screenplay(
            self.sample_english_subtitles,
            language="en",
            preset_name="viral"
        )
        
        # 验证结果
        assert result["language"] == "en", "语言标识错误"
        assert len(result["screenplay"]) > 0, "重构剧本为空"

    def test_narrative_structure_analysis(self):
        """测试叙事结构分析"""
        # 测试中文叙事分析
        zh_analysis = self.narrative_analyzer.analyze_narrative_structure(
            self.sample_chinese_subtitles
        )
        assert zh_analysis["status"] == "success", "中文叙事分析失败"
        assert "emotion_curve" in zh_analysis, "缺少情感曲线分析"
        assert "coherence" in zh_analysis, "缺少连贯性分析"
        
        # 测试英文叙事分析
        en_analysis = self.narrative_analyzer.analyze_narrative_structure(
            self.sample_english_subtitles
        )
        assert en_analysis["status"] == "success", "英文叙事分析失败"

    def test_timeline_accuracy(self):
        """测试时间轴精度 (≤0.5秒误差)"""
        result = self.screenplay_engineer.generate_screenplay(
            self.sample_chinese_subtitles,
            language="zh"
        )
        
        original_times = [(s["start_time"], s["end_time"]) for s in self.sample_chinese_subtitles]
        reconstructed_times = [(s["start_time"], s["end_time"]) for s in result["screenplay"]]
        
        # 验证时间轴精度
        for i, (orig, recon) in enumerate(zip(original_times, reconstructed_times)):
            # 这里简化验证，实际应该解析时间格式计算差值
            assert orig[0] == recon[0], f"第{i}段开始时间不匹配"
            assert orig[1] == recon[1], f"第{i}段结束时间不匹配"

    def test_reconstruction_quality_metrics(self):
        """测试重构质量指标"""
        result = self.screenplay_engineer.generate_screenplay(
            self.sample_chinese_subtitles,
            language="zh",
            preset_name="爆款"
        )
        
        screenplay = result["screenplay"]
        
        # 质量指标验证
        assert len(screenplay) >= len(self.sample_chinese_subtitles), "重构后片段数量不能减少"
        
        # 情感标签覆盖率
        sentiment_coverage = sum(1 for s in screenplay if s.get("sentiment")) / len(screenplay)
        assert sentiment_coverage >= 0.8, f"情感标签覆盖率不足: {sentiment_coverage:.2f}"
        
        # 处理时间验证
        assert result["processing_time"] < 10.0, f"处理时间过长: {result['processing_time']:.2f}s"

    def test_mixed_language_handling(self):
        """测试混合语言处理能力"""
        mixed_subtitles = [
            {"start_time": "00:00:01,000", "end_time": "00:00:03,000", "text": "Hello 你好"},
            {"start_time": "00:00:04,000", "end_time": "00:00:06,000", "text": "This is a test 这是测试"},
        ]
        
        # 语言检测应该能处理混合文本
        detected_lang = self.language_detector.detect_from_text("Hello 你好 world 世界")
        assert detected_lang in ["zh", "en"], f"混合语言检测失败: {detected_lang}"
        
        # 重构应该能处理混合语言字幕
        result = self.screenplay_engineer.generate_screenplay(
            mixed_subtitles,
            language="auto"
        )
        assert len(result["screenplay"]) > 0, "混合语言重构失败"

    def test_error_handling_and_fallback(self):
        """测试错误处理和回退机制"""
        # 测试空输入
        empty_result = self.screenplay_engineer.generate_screenplay([], language="zh")
        assert empty_result["total_segments"] == 0, "空输入处理错误"
        
        # 测试无效时间格式
        invalid_subtitles = [
            {"start_time": "invalid", "end_time": "invalid", "text": "测试文本"}
        ]
        
        # 应该有错误处理机制，不会崩溃
        try:
            result = self.screenplay_engineer.generate_screenplay(invalid_subtitles, language="zh")
            # 验证错误处理
            assert "error" in result or len(result["screenplay"]) == 0, "错误处理机制失效"
        except Exception as e:
            pytest.fail(f"缺少错误处理机制: {str(e)}")

    @pytest.mark.performance
    def test_performance_benchmarks(self):
        """测试性能基准"""
        # 大量数据性能测试
        large_subtitles = self.sample_chinese_subtitles * 100  # 300个片段
        
        start_time = time.time()
        result = self.screenplay_engineer.generate_screenplay(
            large_subtitles,
            language="zh"
        )
        processing_time = time.time() - start_time
        
        # 性能要求
        assert processing_time < 30.0, f"大数据处理时间过长: {processing_time:.2f}s"
        assert len(result["screenplay"]) == len(large_subtitles), "大数据处理结果不完整"

    def test_memory_usage_during_reconstruction(self):
        """测试重构过程中的内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行重构
        result = self.screenplay_engineer.generate_screenplay(
            self.sample_chinese_subtitles * 50,  # 150个片段
            language="zh"
        )
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # 内存使用验证 (应该在合理范围内)
        assert memory_increase < 100, f"内存使用过多: {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
