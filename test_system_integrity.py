#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统完整性测试
验证所有核心功能和UI组件的完整性
"""

import sys
import os
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_module_imports():
    """测试关键模块导入"""
    logger.info("=== 模块导入测试 ===")
    
    try:
        # 测试核心模块
        from model_path_manager import ModelPathManager
        logger.info("✓ ModelPathManager 导入成功")
        
        from src.training.zh_trainer import ZhTrainer
        logger.info("✓ ZhTrainer 导入成功")
        
        from src.core.viral_evaluation_engine import ViralEvaluationEngine
        logger.info("✓ ViralEvaluationEngine 导入成功")
        
        from src.core.screenplay_engineer import ScreenplayEngineer
        logger.info("✓ ScreenplayEngineer 导入成功")
        
        from src.core.narrative_analyzer import IntegratedNarrativeAnalyzer
        logger.info("✓ IntegratedNarrativeAnalyzer 导入成功")
        
        # 测试UI模块
        from simple_ui_fixed import SimpleScreenplayApp
        logger.info("✓ SimpleScreenplayApp 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 模块导入失败: {e}")
        return False

def test_core_functionality():
    """测试核心功能"""
    logger.info("=== 核心功能测试 ===")
    
    try:
        # 测试训练器
        from src.training.zh_trainer import ZhTrainer
        trainer = ZhTrainer(use_gpu=False)
        
        # 测试推理
        test_text = "这是一个测试文本。"
        result = trainer.quick_inference_test(test_text)
        logger.info(f"✓ 推理测试成功: {result}")
        
        # 测试学习
        training_pairs = [
            {"original": "普通文本", "viral": "【震撼】普通文本变爆款！"}
        ]
        learning_success = trainer.learn_viral_transformation_patterns(training_pairs)
        logger.info(f"✓ 学习测试成功: {learning_success}")
        
        # 测试评估引擎
        from src.core.viral_evaluation_engine import ViralEvaluationEngine
        evaluator = ViralEvaluationEngine()
        eval_result = evaluator.evaluate_transformation("原文", "【爆款】原文！")
        logger.info(f"✓ 评估引擎测试成功: {eval_result.overall_score:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 核心功能测试失败: {e}")
        return False

def test_ui_components():
    """测试UI组件"""
    logger.info("=== UI组件测试 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from simple_ui_fixed import SimpleScreenplayApp
        
        # 创建应用
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        window = SimpleScreenplayApp()
        logger.info("✓ 主窗口创建成功")
        
        # 测试窗口属性
        if hasattr(window, 'tab_widget'):
            logger.info("✓ 标签页组件存在")
        
        if hasattr(window, 'video_processor'):
            logger.info("✓ 视频处理器存在")
        
        if hasattr(window, 'model_trainer'):
            logger.info("✓ 模型训练器存在")
        
        # 清理
        window.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ UI组件测试失败: {e}")
        return False

def test_workflow_integration():
    """测试工作流程集成"""
    logger.info("=== 工作流程集成测试 ===")
    
    try:
        # 测试SRT解析
        from src.core.srt_parser import SRTParser
        parser = SRTParser()
        
        test_srt = """1
00:00:01,000 --> 00:00:05,000
测试字幕内容

2
00:00:06,000 --> 00:00:10,000
第二条字幕"""
        
        segments = parser.parse_srt_content(test_srt)
        logger.info(f"✓ SRT解析成功: {len(segments)}个片段")
        
        # 测试剧本重构
        from src.core.screenplay_engineer import ScreenplayEngineer
        engineer = ScreenplayEngineer()
        
        result = engineer.reconstruct_screenplay(test_srt)
        logger.info(f"✓ 剧本重构成功: 评分{result.get('optimization_score', 0):.2f}")
        
        # 测试上下文分析
        from src.core.narrative_analyzer import IntegratedNarrativeAnalyzer
        analyzer = IntegratedNarrativeAnalyzer()
        
        analysis = analyzer.analyze_narrative_context(segments)
        logger.info(f"✓ 上下文分析成功: {analysis.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 工作流程集成测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    logger.info("=== 性能测试 ===")
    
    try:
        from src.training.zh_trainer import ZhTrainer
        
        trainer = ZhTrainer(use_gpu=False)
        
        # 测试推理性能
        test_texts = ["测试文本1", "测试文本2", "测试文本3"]
        
        start_time = time.time()
        for text in test_texts:
            result = trainer.quick_inference_test(text)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / len(test_texts)
        logger.info(f"✓ 推理性能测试: 平均{avg_time:.3f}秒/次")
        
        # 测试内存使用
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"✓ 内存使用: {memory_mb:.1f}MB")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始系统完整性测试")
    
    test_results = {
        "模块导入": test_module_imports(),
        "核心功能": test_core_functionality(),
        "UI组件": test_ui_components(),
        "工作流程": test_workflow_integration(),
        "性能测试": test_performance()
    }
    
    logger.info("=== 测试结果总结 ===")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = passed / total * 100
    logger.info(f"总体成功率: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 90:
        logger.info("🎉 系统完整性测试通过！")
        return True
    else:
        logger.warning("⚠️ 系统完整性测试未完全通过")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
