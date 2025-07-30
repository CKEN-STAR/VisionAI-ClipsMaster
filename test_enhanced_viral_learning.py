#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试增强版爆款转换学习算法
使用新的多维度评估引擎
"""

import time
from src.training.zh_trainer import ZhTrainer
from src.core.viral_evaluation_engine import ViralEvaluationEngine

def test_enhanced_viral_learning():
    """测试增强版爆款转换学习功能"""
    
    print('=== 增强版爆款转换学习算法测试 ===')
    
    # 初始化训练器和评估引擎
    trainer = ZhTrainer(use_gpu=False)
    evaluation_engine = ViralEvaluationEngine()
    
    print(f'训练器评估引擎状态: {"已加载" if trainer.evaluation_engine else "未加载"}')
    
    # 测试文本集合
    test_texts = [
        "小明在公园里散步，看到了一只小猫。",
        "今天天气很好，阳光明媚。",
        "他遇到了一个神秘的老人，老人给了他一个盒子。",
        "这个故事发生在一个普通的下午。",
        "最终，一切都改变了。"
    ]
    
    print('\n1. 学习前转换效果测试')
    print('-' * 50)
    
    before_results = []
    for i, text in enumerate(test_texts):
        result = trainer.quick_inference_test(text)
        before_results.append(result)
        
        # 使用评估引擎评估
        if evaluation_engine:
            eval_result = evaluation_engine.evaluate_transformation(text, result)
            print(f'文本 {i+1}: {text}')
            print(f'转换后: {result}')
            print(f'评估得分: {eval_result.overall_score:.3f}')
            print(f'改进检测: {"✓" if eval_result.improvement_detected else "✗"}')
            print(f'置信度: {eval_result.confidence:.3f}')
            print(f'维度得分: {eval_result.dimension_scores}')
            print()
    
    print('\n2. 执行深度学习过程')
    print('-' * 50)
    
    learning_start = time.time()
    learning_success = trainer.quick_training_test('data/training/zh')
    learning_time = time.time() - learning_start
    
    print(f'学习结果: {"成功" if learning_success else "失败"}')
    print(f'学习耗时: {learning_time:.3f}秒')
    print(f'学到的转换规则数: {len(trainer.viral_patterns["transformation_rules"])}')
    print(f'学习历史记录数: {len(trainer.learning_history)}')
    
    print('\n3. 学习后转换效果测试')
    print('-' * 50)
    
    after_results = []
    improvement_scores = []
    
    for i, text in enumerate(test_texts):
        result = trainer.quick_inference_test(text)
        after_results.append(result)
        
        # 使用评估引擎评估
        if evaluation_engine:
            eval_result = evaluation_engine.evaluate_transformation(
                text, result, 
                learning_context={
                    "training_samples": len(trainer.learning_history),
                    "learning_success_rate": 1.0 if learning_success else 0.0
                }
            )
            improvement_scores.append(eval_result.overall_score)
            
            print(f'文本 {i+1}: {text}')
            print(f'转换后: {result}')
            print(f'评估得分: {eval_result.overall_score:.3f}')
            print(f'改进检测: {"✓" if eval_result.improvement_detected else "✗"}')
            print(f'置信度: {eval_result.confidence:.3f}')
            print(f'最强维度: {eval_result.quality_metrics.get("top_dimension", "unknown")}')
            print(f'改进强度: {eval_result.quality_metrics.get("improvement_strength", "unknown")}')
            
            if eval_result.recommendations:
                print(f'建议: {eval_result.recommendations[0]}')
            print()
    
    print('\n4. 多样性和质量分析')
    print('-' * 50)
    
    # 分析结果多样性
    before_unique = len(set(before_results))
    after_unique = len(set(after_results))
    
    print(f'学习前结果多样性: {before_unique}/{len(test_texts)} ({before_unique/len(test_texts)*100:.1f}%)')
    print(f'学习后结果多样性: {after_unique}/{len(test_texts)} ({after_unique/len(test_texts)*100:.1f}%)')
    
    # 分析质量改进
    if improvement_scores:
        avg_score = sum(improvement_scores) / len(improvement_scores)
        high_quality_count = sum(1 for score in improvement_scores if score >= 0.5)
        
        print(f'平均评估得分: {avg_score:.3f}')
        print(f'高质量转换数: {high_quality_count}/{len(improvement_scores)} ({high_quality_count/len(improvement_scores)*100:.1f}%)')
    
    print('\n5. 学习效果综合评估')
    print('-' * 50)
    
    # 综合评估学习效果
    learning_effectiveness = {
        "learning_success": learning_success,
        "rules_learned": len(trainer.viral_patterns["transformation_rules"]),
        "diversity_improvement": after_unique > before_unique,
        "quality_score": sum(improvement_scores) / len(improvement_scores) if improvement_scores else 0.0,
        "high_quality_rate": (sum(1 for score in improvement_scores if score >= 0.5) / len(improvement_scores)) if improvement_scores else 0.0
    }
    
    # 计算总体成功率
    success_indicators = [
        learning_effectiveness["learning_success"],
        learning_effectiveness["rules_learned"] > 0,
        learning_effectiveness["quality_score"] >= 0.4,
        learning_effectiveness["high_quality_rate"] >= 0.6
    ]
    
    overall_success_rate = sum(success_indicators) / len(success_indicators)
    
    print(f'学习成功: {"✓" if learning_effectiveness["learning_success"] else "✗"}')
    print(f'规则学习: {"✓" if learning_effectiveness["rules_learned"] > 0 else "✗"} ({learning_effectiveness["rules_learned"]}条)')
    print(f'多样性改进: {"✓" if learning_effectiveness["diversity_improvement"] else "✗"}')
    print(f'质量得分: {learning_effectiveness["quality_score"]:.3f} {"✓" if learning_effectiveness["quality_score"] >= 0.4 else "✗"}')
    print(f'高质量率: {learning_effectiveness["high_quality_rate"]:.1%} {"✓" if learning_effectiveness["high_quality_rate"] >= 0.6 else "✗"}')
    print(f'总体成功率: {overall_success_rate:.1%}')
    
    print('\n6. 性能基准测试')
    print('-' * 50)
    
    # 性能测试
    performance_results = trainer.benchmark_inference_performance(test_texts[:3])  # 使用前3个文本
    print(f'性能基准测试结果:')
    print(f'  CPU平均时间: {performance_results.get("avg_cpu_time", 0):.3f}秒')
    print(f'  GPU平均时间: {performance_results.get("avg_gpu_time", 0):.3f}秒')
    print(f'  加速比: {performance_results.get("speedup", 0):.2f}x')
    
    print('\n=== 增强版爆款转换学习算法测试完成 ===')
    
    return {
        "overall_success_rate": overall_success_rate,
        "learning_effectiveness": learning_effectiveness,
        "performance_results": performance_results,
        "evaluation_available": trainer.evaluation_engine is not None
    }

if __name__ == "__main__":
    result = test_enhanced_viral_learning()
    print(f'\n🎯 最终测试结果: {result}')
    
    # 判断是否达到目标
    target_success_rate = 0.9  # 90%目标
    if result["overall_success_rate"] >= target_success_rate:
        print(f'🎉 测试通过！成功率 {result["overall_success_rate"]:.1%} 达到目标 {target_success_rate:.1%}')
    else:
        print(f'⚠️  测试未完全通过，成功率 {result["overall_success_rate"]:.1%} 未达到目标 {target_success_rate:.1%}')
