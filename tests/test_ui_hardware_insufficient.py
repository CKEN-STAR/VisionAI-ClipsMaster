#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试UI在硬件不足时的显示逻辑
验证智能推荐下载器在设备硬件不足时的UI行为
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_ui_hardware_insufficient_display():
    """测试UI在硬件不足时的显示"""
    print("\n" + "="*60)
    print("测试：UI硬件不足显示逻辑")
    print("="*60)
    
    from src.core.intelligent_model_selector import IntelligentModelSelector, ModelRecommendation
    from src.core.quantization_analysis import HardwareProfile
    
    selector = IntelligentModelSelector()
    
    # 模拟一个低配设备（2GB内存，无GPU）
    low_end_hardware = HardwareProfile(
        cpu_cores=2,
        system_ram_gb=2.0,
        storage_available_gb=50.0,
        has_gpu=False,
        gpu_memory_gb=0.0,
        gpu_compute_capability=0.0
    )
    
    print(f"\n模拟设备配置:")
    print(f"  CPU核心: {low_end_hardware.cpu_cores}")
    print(f"  系统内存: {low_end_hardware.system_ram_gb}GB")
    print(f"  存储空间: {low_end_hardware.storage_available_gb}GB")
    print(f"  GPU: {'有' if low_end_hardware.has_gpu else '无'}")
    
    # 测试推荐Mistral-7B（需要18GB内存）
    print(f"\n测试推荐Mistral-7B（需要18GB内存）:")
    recommendation = selector.recommend_model_version(
        model_name="mistral-7b",
        hardware_override=low_end_hardware
    )
    
    # 验证推荐结果
    print(f"\n推荐结果验证:")
    print(f"  variant is None: {recommendation.variant is None}")
    print(f"  confidence_score: {recommendation.confidence_score}")
    print(f"  reasoning条数: {len(recommendation.reasoning)}")
    print(f"  deployment_notes条数: {len(recommendation.deployment_notes)}")
    
    # 验证UI应该显示的内容
    print(f"\nUI应该显示的内容:")
    print(f"  推荐理由:")
    for reason in recommendation.reasoning:
        print(f"    - {reason}")
    
    print(f"\n  部署说明:")
    for note in recommendation.deployment_notes:
        print(f"    - {note}")
    
    # 验证关键字段
    has_error_message = any("硬件不足" in reason for reason in recommendation.reasoning)
    has_solution = any("升级" in note or "选择更小" in note for note in recommendation.deployment_notes)
    
    if recommendation.variant is None and has_error_message and has_solution:
        print(f"\n✅ 测试通过：UI应该正确显示硬件不足信息")
        return True
    else:
        print(f"\n❌ 测试失败：UI显示信息不完整")
        return False

def test_recommendation_structure():
    """测试推荐结果的数据结构"""
    print("\n" + "="*60)
    print("测试：推荐结果数据结构")
    print("="*60)
    
    from src.core.intelligent_model_selector import IntelligentModelSelector
    from src.core.quantization_analysis import HardwareProfile
    
    selector = IntelligentModelSelector()
    
    # 低配设备
    low_end_hardware = HardwareProfile(
        cpu_cores=2,
        system_ram_gb=2.0,
        storage_available_gb=50.0,
        has_gpu=False,
        gpu_memory_gb=0.0,
        gpu_compute_capability=0.0
    )
    
    recommendation = selector.recommend_model_version(
        model_name="mistral-7b",
        hardware_override=low_end_hardware
    )
    
    # 验证数据结构
    print(f"\n数据结构验证:")
    print(f"  model_name: {recommendation.model_name}")
    print(f"  variant: {recommendation.variant}")
    print(f"  confidence_score: {recommendation.confidence_score}")
    print(f"  reasoning类型: {type(recommendation.reasoning)}")
    print(f"  compatibility_assessment类型: {type(recommendation.compatibility_assessment)}")
    print(f"  alternative_options类型: {type(recommendation.alternative_options)}")
    print(f"  deployment_notes类型: {type(recommendation.deployment_notes)}")
    
    # 验证必需字段
    checks = [
        ("model_name存在", recommendation.model_name is not None),
        ("variant为None", recommendation.variant is None),
        ("confidence_score为0", recommendation.confidence_score == 0.0),
        ("reasoning非空", len(recommendation.reasoning) > 0),
        ("compatibility_assessment存在", recommendation.compatibility_assessment is not None),
        ("deployment_notes非空", len(recommendation.deployment_notes) > 0),
    ]
    
    print(f"\n字段检查:")
    all_passed = True
    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")
        if not check_result:
            all_passed = False
    
    if all_passed:
        print(f"\n✅ 测试通过：数据结构完整")
        return True
    else:
        print(f"\n❌ 测试失败：数据结构不完整")
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("VisionAI-ClipsMaster UI硬件不足显示测试")
    print("="*60)
    
    results = []
    
    # 测试1: UI显示逻辑
    try:
        result1 = test_ui_hardware_insufficient_display()
        results.append(("UI硬件不足显示", result1))
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("UI硬件不足显示", False))
    
    # 测试2: 数据结构验证
    try:
        result2 = test_recommendation_structure()
        results.append(("推荐结果数据结构", result2))
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("推荐结果数据结构", False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！UI硬件不足显示逻辑正确。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查逻辑。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

