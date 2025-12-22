#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模型下载配置的正确性
验证智能推荐下载器只下载原始FP16模型，不下载预量化模型
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_enhanced_model_downloader_config():
    """测试EnhancedModelDownloader的配置"""
    print("\n" + "="*60)
    print("测试1: EnhancedModelDownloader配置验证")
    print("="*60)

    from src.core.enhanced_model_downloader import EnhancedModelDownloader

    downloader = EnhancedModelDownloader()
    model_configs = downloader._load_download_configs()
    
    # 检查Qwen2.5-7B配置
    qwen_config = model_configs.get("qwen2.5-7b")
    if qwen_config:
        print(f"\n✅ Qwen2.5-7B配置:")
        print(f"   名称: {qwen_config['name']}")
        print(f"   描述: {qwen_config['description']}")
        print(f"   大小: {qwen_config['total_size'] / 1e9:.1f}GB")
        print(f"   目标目录: {qwen_config['target_dir']}")
        
        # 检查URL是否指向原始模型
        first_file_url = qwen_config['files'][0]['url']
        if "GPTQ" in first_file_url or "gptq" in first_file_url:
            print(f"   ❌ 错误：URL指向GPTQ量化模型")
            print(f"   URL: {first_file_url}")
            return False
        else:
            print(f"   ✅ 正确：URL指向原始模型")
            print(f"   URL: {first_file_url}")
    
    # 检查Mistral-7B配置
    mistral_config = model_configs.get("mistral-7b")
    if mistral_config:
        print(f"\n✅ Mistral-7B配置:")
        print(f"   名称: {mistral_config['name']}")
        print(f"   描述: {mistral_config['description']}")
        print(f"   大小: {mistral_config['total_size'] / 1e9:.1f}GB")
        print(f"   目标目录: {mistral_config['target_dir']}")
        
        # 检查URL是否指向原始模型
        first_file_url = mistral_config['files'][0]['url']
        if "GPTQ" in first_file_url or "gptq" in first_file_url or "TheBloke" in first_file_url:
            print(f"   ❌ 错误：URL指向GPTQ量化模型")
            print(f"   URL: {first_file_url}")
            return False
        else:
            print(f"   ✅ 正确：URL指向原始模型")
            print(f"   URL: {first_file_url}")
    
    return True

def test_intelligent_model_selector_config():
    """测试IntelligentModelSelector的配置"""
    print("\n" + "="*60)
    print("测试2: IntelligentModelSelector配置验证")
    print("="*60)
    
    from src.core.intelligent_model_selector import create_multi_tier_download_config
    
    config = create_multi_tier_download_config()
    
    print(f"\n配置的模型数量: {len(config)}")
    
    for model_name, variants in config.items():
        print(f"\n模型: {model_name}")
        print(f"  变体数量: {len(variants)}")
        
        # 检查是否只有FP16变体
        if len(variants) > 1:
            print(f"  ❌ 错误：存在多个变体（应该只有FP16）")
            print(f"  变体: {list(variants.keys())}")
            return False
        
        if "fp16" not in variants:
            print(f"  ❌ 错误：缺少FP16变体")
            return False
        
        fp16_config = variants["fp16"]
        print(f"  ✅ 正确：只有FP16变体")
        print(f"     名称: {fp16_config['name']}")
        print(f"     大小: {fp16_config['size_gb']}GB")
        print(f"     URL: {fp16_config['urls'][0]}")
        print(f"     目标目录: {fp16_config['target_dir']}")
        
        # 检查URL是否指向原始模型
        url = fp16_config['urls'][0]
        if "GPTQ" in url or "gptq" in url or "TheBloke" in url:
            print(f"  ❌ 错误：URL指向GPTQ量化模型")
            return False
        
        # 检查目标目录是否正确
        if "int4" in fp16_config['target_dir'] or "int8" in fp16_config['target_dir']:
            print(f"  ❌ 错误：目标目录包含量化标识")
            return False
    
    return True

def test_model_converter_compatibility():
    """测试模型转换器的兼容性"""
    print("\n" + "="*60)
    print("测试3: 模型转换器兼容性验证")
    print("="*60)
    
    from models.converters.model_converter import ModelConverter
    
    converter = ModelConverter()
    
    print(f"\n✅ 支持的输出格式: {converter.supported_formats}")
    print(f"✅ 支持的量化类型: {list(converter.quantization_types.keys())}")
    
    # 验证GGUF转换方法存在
    if hasattr(converter, '_convert_to_gguf'):
        print(f"✅ GGUF转换方法存在")
    else:
        print(f"❌ GGUF转换方法不存在")
        return False
    
    # 验证量化类型
    expected_quant_types = ['Q4_K_M', 'Q5_K', 'Q2_K', 'Q8_0']
    for quant_type in expected_quant_types:
        if quant_type in converter.quantization_types:
            print(f"✅ 支持量化类型: {quant_type}")
        else:
            print(f"❌ 不支持量化类型: {quant_type}")
            return False
    
    return True

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("VisionAI-ClipsMaster 模型下载配置测试")
    print("="*60)
    
    results = []
    
    # 测试1: EnhancedModelDownloader配置
    try:
        result1 = test_enhanced_model_downloader_config()
        results.append(("EnhancedModelDownloader配置", result1))
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        results.append(("EnhancedModelDownloader配置", False))
    
    # 测试2: IntelligentModelSelector配置
    try:
        result2 = test_intelligent_model_selector_config()
        results.append(("IntelligentModelSelector配置", result2))
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        results.append(("IntelligentModelSelector配置", False))
    
    # 测试3: 模型转换器兼容性
    try:
        result3 = test_model_converter_compatibility()
        results.append(("模型转换器兼容性", result3))
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        results.append(("模型转换器兼容性", False))
    
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
        print("\n🎉 所有测试通过！模型下载配置正确。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

