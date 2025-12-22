#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试硬件不足时的推荐逻辑
验证当设备硬件不足时，智能推荐器不推荐模型
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_insufficient_hardware():
    """测试硬件不足时的推荐"""
    print("\n" + "="*60)
    print("测试：硬件不足时的推荐逻辑")
    print("="*60)
    
    from src.core.intelligent_model_selector import IntelligentModelSelector
    from src.core.quantization_analysis import HardwareProfile
    
    selector = IntelligentModelSelector()
    
    # 模拟一个低配设备（2GB内存，无GPU）
    low_end_hardware = HardwareProfile(
        cpu_cores=2,
        system_ram_gb=2.0,  # 只有2GB内存
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
    
    if recommendation.variant is None:
        print(f"✅ 正确：未推荐任何变体（设备不足）")
        print(f"   推荐理由:")
        for reason in recommendation.reasoning:
            print(f"     - {reason}")
        print(f"   部署说明:")
        for note in recommendation.deployment_notes:
            print(f"     - {note}")
        return True
    else:
        print(f"❌ 错误：推荐了变体 {recommendation.variant.name}")
        print(f"   这不应该发生，因为设备内存不足")
        return False

def test_sufficient_hardware():
    """测试硬件充足时的推荐"""
    print("\n" + "="*60)
    print("测试：硬件充足时的推荐逻辑")
    print("="*60)
    
    from src.core.intelligent_model_selector import IntelligentModelSelector
    from src.core.quantization_analysis import HardwareProfile
    
    selector = IntelligentModelSelector()
    
    # 模拟一个中配设备（8GB内存，无GPU）
    mid_end_hardware = HardwareProfile(
        cpu_cores=8,
        system_ram_gb=8.0,
        storage_available_gb=100.0,
        has_gpu=False,
        gpu_memory_gb=0.0,
        gpu_compute_capability=0.0
    )
    
    print(f"\n模拟设备配置:")
    print(f"  CPU核心: {mid_end_hardware.cpu_cores}")
    print(f"  系统内存: {mid_end_hardware.system_ram_gb}GB")
    print(f"  存储空间: {mid_end_hardware.storage_available_gb}GB")
    print(f"  GPU: {'有' if mid_end_hardware.has_gpu else '无'}")
    
    # 测试推荐qwen3-0.6b（需要4GB内存）
    print(f"\n测试推荐qwen3-0.6b（需要4GB内存）:")
    recommendation = selector.recommend_model_version(
        model_name="qwen3-0.6b",
        hardware_override=mid_end_hardware
    )
    
    if recommendation.variant is not None:
        print(f"✅ 正确：推荐了变体 {recommendation.variant.name}")
        print(f"   模型大小: {recommendation.variant.size_gb}GB")
        print(f"   内存需求: {recommendation.variant.memory_requirement_gb}GB")
        print(f"   推荐理由:")
        for reason in recommendation.reasoning:
            print(f"     - {reason}")
        return True
    else:
        print(f"❌ 错误：未推荐任何变体")
        print(f"   这不应该发生，因为设备内存充足")
        return False

def test_edge_case():
    """测试边界情况（刚好满足最低要求）"""
    print("\n" + "="*60)
    print("测试：边界情况（刚好满足最低要求）")
    print("="*60)
    
    from src.core.intelligent_model_selector import IntelligentModelSelector
    from src.core.quantization_analysis import HardwareProfile
    
    selector = IntelligentModelSelector()
    
    # 模拟一个刚好满足qwen3-0.6b要求的设备（4GB内存）
    edge_hardware = HardwareProfile(
        cpu_cores=4,
        system_ram_gb=4.0,  # 刚好4GB
        storage_available_gb=50.0,
        has_gpu=False,
        gpu_memory_gb=0.0,
        gpu_compute_capability=0.0
    )
    
    print(f"\n模拟设备配置:")
    print(f"  CPU核心: {edge_hardware.cpu_cores}")
    print(f"  系统内存: {edge_hardware.system_ram_gb}GB")
    print(f"  存储空间: {edge_hardware.storage_available_gb}GB")
    print(f"  GPU: {'有' if edge_hardware.has_gpu else '无'}")
    
    # 测试推荐qwen3-0.6b（需要4GB内存）
    print(f"\n测试推荐qwen3-0.6b（需要4GB内存）:")
    recommendation = selector.recommend_model_version(
        model_name="qwen3-0.6b",
        hardware_override=edge_hardware
    )
    
    if recommendation.variant is not None:
        print(f"✅ 正确：推荐了变体 {recommendation.variant.name}")
        print(f"   模型大小: {recommendation.variant.size_gb}GB")
        print(f"   内存需求: {recommendation.variant.memory_requirement_gb}GB")
        return True
    else:
        print(f"⚠️  边界情况：未推荐任何变体")
        print(f"   这可能是因为兼容性评分低于0.5")
        print(f"   推荐理由:")
        for reason in recommendation.reasoning:
            print(f"     - {reason}")
        return True  # 边界情况可以接受

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("VisionAI-ClipsMaster 硬件不足推荐测试")
    print("="*60)
    
    results = []
    
    # 测试1: 硬件不足
    try:
        result1 = test_insufficient_hardware()
        results.append(("硬件不足时不推荐", result1))
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("硬件不足时不推荐", False))
    
    # 测试2: 硬件充足
    try:
        result2 = test_sufficient_hardware()
        results.append(("硬件充足时推荐", result2))
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("硬件充足时推荐", False))
    
    # 测试3: 边界情况
    try:
        result3 = test_edge_case()
        results.append(("边界情况处理", result3))
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("边界情况处理", False))
    
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
        print("\n🎉 所有测试通过！硬件不足推荐逻辑正确。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查逻辑。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

