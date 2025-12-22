#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPTQ配置清理验证测试

验证所有模型配置文件中的GPTQ相关配置已被完全清理
"""

import os
import sys
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def test_gptq_cleanup():
    """测试GPTQ配置清理"""
    print("\n" + "=" * 60)
    print("GPTQ配置清理验证测试")
    print("=" * 60)
    
    # 获取所有模型配置文件
    config_dir = project_root / "configs" / "models" / "available_models"
    config_files = list(config_dir.glob("*.yaml"))
    
    print(f"\n找到 {len(config_files)} 个模型配置文件")
    
    all_passed = True
    total_checks = 0
    passed_checks = 0
    
    for config_file in config_files:
        print(f"\n{'=' * 60}")
        print(f"检查文件: {config_file.name}")
        print(f"{'=' * 60}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查1: model_format应该是huggingface
        if config.get('model', {}).get('model_format') == 'huggingface':
            print("✅ model_format = huggingface")
            passed_checks += 1
        else:
            print(f"❌ model_format = {config.get('model', {}).get('model_format')} (应该是huggingface)")
            all_passed = False
        total_checks += 1
        
        # 检查2: 不应该有size_int4字段
        if 'size_int4' not in config.get('model', {}):
            print("✅ 没有size_int4字段")
            passed_checks += 1
        else:
            print(f"❌ 仍然存在size_int4字段: {config['model']['size_int4']}")
            all_passed = False
        total_checks += 1
        
        # 检查3: 不应该有size_int8字段
        if 'size_int8' not in config.get('model', {}):
            print("✅ 没有size_int8字段")
            passed_checks += 1
        else:
            print(f"❌ 仍然存在size_int8字段: {config['model']['size_int8']}")
            all_passed = False
        total_checks += 1
        
        # 检查4: quantization.default_level应该是FP16
        if config.get('quantization', {}).get('default_level') == 'FP16':
            print("✅ quantization.default_level = FP16")
            passed_checks += 1
        else:
            print(f"❌ quantization.default_level = {config.get('quantization', {}).get('default_level')} (应该是FP16)")
            all_passed = False
        total_checks += 1
        
        # 检查5: 不应该有gptq_config字段
        if 'gptq_config' not in config.get('quantization', {}):
            print("✅ 没有gptq_config字段")
            passed_checks += 1
        else:
            print(f"❌ 仍然存在gptq_config字段")
            all_passed = False
        total_checks += 1
        
        # 检查6: 不应该有llm_int8_config字段
        if 'llm_int8_config' not in config.get('quantization', {}):
            print("✅ 没有llm_int8_config字段")
            passed_checks += 1
        else:
            print(f"❌ 仍然存在llm_int8_config字段")
            all_passed = False
        total_checks += 1
        
        # 检查7: download.quantized_versions应该只有fp16
        quantized_versions = config.get('download', {}).get('quantized_versions', {})
        if set(quantized_versions.keys()) == {'fp16'}:
            print("✅ download.quantized_versions只包含fp16")
            passed_checks += 1
        else:
            print(f"❌ download.quantized_versions包含其他变体: {list(quantized_versions.keys())}")
            all_passed = False
        total_checks += 1
        
        # 检查8: 不应该有mirror_sources字段
        if 'mirror_sources' not in config.get('download', {}):
            print("✅ 没有mirror_sources字段")
            passed_checks += 1
        else:
            print(f"❌ 仍然存在mirror_sources字段")
            all_passed = False
        total_checks += 1
        
        # 检查9: hardware_requirements应该使用FP16
        hw_req = config.get('hardware_requirements', {})
        if 'fp16' in hw_req and 'int4' not in hw_req and 'int8' not in hw_req:
            print("✅ hardware_requirements只包含fp16")
            passed_checks += 1
        else:
            print(f"❌ hardware_requirements包含INT4/INT8: {list(hw_req.keys())}")
            all_passed = False
        total_checks += 1
        
        # 检查10: benchmark应该使用FP16
        benchmark = config.get('benchmark', {})
        if 'fp16' in benchmark and 'int4' not in benchmark and 'int8' not in benchmark:
            print("✅ benchmark只包含fp16")
            passed_checks += 1
        else:
            print(f"❌ benchmark包含INT4/INT8: {list(benchmark.keys())}")
            all_passed = False
        total_checks += 1
    
    # 打印总结
    print(f"\n{'=' * 60}")
    print("测试结果汇总")
    print(f"{'=' * 60}")
    print(f"总检查项: {total_checks}")
    print(f"通过检查: {passed_checks}")
    print(f"失败检查: {total_checks - passed_checks}")
    print(f"通过率: {passed_checks / total_checks * 100:.1f}%")
    
    if all_passed:
        print("\n🎉 所有GPTQ配置已完全清理！")
        return True
    else:
        print("\n❌ 仍有GPTQ配置残留，请检查！")
        return False


if __name__ == "__main__":
    success = test_gptq_cleanup()
    sys.exit(0 if success else 1)

