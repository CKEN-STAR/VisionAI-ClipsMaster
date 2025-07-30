#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试改进后的爆款转换学习算法
"""

from src.training.zh_trainer import ZhTrainer

def test_viral_learning():
    """测试爆款转换学习功能"""
    
    # 测试改进后的爆款转换学习
    trainer = ZhTrainer(use_gpu=False)

    print('=== 测试爆款转换学习算法 ===')

    # 测试学习前的转换能力
    test_input = '小王在公园里散步，看到了一只小猫。'
    before_result = trainer.quick_inference_test(test_input)
    print(f'学习前转换: {before_result}')

    # 执行学习过程
    print('\n执行学习过程...')
    learning_success = trainer.quick_training_test('data/training/zh')
    print(f'学习结果: {learning_success}')

    # 测试学习后的转换能力
    after_result1 = trainer.quick_inference_test(test_input)
    print(f'\n学习后转换: {after_result1}')

    # 再次测试以验证变化
    after_result2 = trainer.quick_inference_test(test_input)
    print(f'再次测试: {after_result2}')

    print(f'\n转换次数: {trainer.transformation_count}')
    print(f'学习历史记录数: {len(trainer.learning_history)}')
    print(f'学到的转换规则数: {len(trainer.viral_patterns["transformation_rules"])}')

    # 分析学习效果
    print('\n=== 学习效果分析 ===')
    
    # 检查是否有变化
    results = [before_result, after_result1, after_result2]
    unique_results = set(results)
    
    print(f'生成结果的多样性: {len(unique_results)} 种不同结果')
    
    # 检查是否学到了新的模式
    if len(trainer.viral_patterns["transformation_rules"]) > 0:
        print('✓ 成功学到了转换规则')
        for i, rule in enumerate(trainer.viral_patterns["transformation_rules"]):
            print(f'  规则 {i+1}: {rule}')
    else:
        print('✗ 未学到转换规则')
    
    # 检查结果是否有改进
    viral_indicators = ["震撼", "惊人", "绝密", "【", "】", "！"]
    
    before_score = sum(1 for indicator in viral_indicators if indicator in before_result)
    after_score1 = sum(1 for indicator in viral_indicators if indicator in after_result1)
    after_score2 = sum(1 for indicator in viral_indicators if indicator in after_result2)
    
    print(f'\n爆款特征评分:')
    print(f'  学习前: {before_score}')
    print(f'  学习后1: {after_score1}')
    print(f'  学习后2: {after_score2}')
    
    improvement = (after_score1 > before_score) or (after_score2 > before_score)
    print(f'  是否有改进: {"✓" if improvement else "✗"}')

    print('\n爆款转换学习算法测试完成！')
    
    return {
        "learning_success": learning_success,
        "rules_learned": len(trainer.viral_patterns["transformation_rules"]),
        "improvement_detected": improvement,
        "diversity": len(unique_results)
    }

if __name__ == "__main__":
    result = test_viral_learning()
    print(f'\n最终结果: {result}')
