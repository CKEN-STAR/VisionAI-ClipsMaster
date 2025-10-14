#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实训练系统测试脚本
验证训练系统是否正确配置并能正常工作
"""

import sys
import os

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_dependencies():
    """测试必需依赖是否已安装"""
    print("=" * 70)
    print("📦 检查训练系统依赖...")
    print("=" * 70)
    
    dependencies = {
        "torch": "PyTorch深度学习框架",
        "transformers": "Hugging Face Transformers",
        "peft": "LoRA/QLoRA微调支持",
        "datasets": "训练数据集处理",
    }
    
    missing = []
    installed = []
    
    for lib, desc in dependencies.items():
        try:
            if lib == "torch":
                import torch
                version = torch.__version__
                cuda_available = torch.cuda.is_available()
                installed.append(f"✅ {lib} v{version} - {desc}")
                if cuda_available:
                    installed.append(f"   🚀 CUDA可用: {torch.cuda.get_device_name(0)}")
                else:
                    installed.append(f"   ⚠️ CUDA不可用，将使用CPU训练")
            elif lib == "transformers":
                import transformers
                version = transformers.__version__
                installed.append(f"✅ {lib} v{version} - {desc}")
            elif lib == "peft":
                import peft
                version = peft.__version__
                installed.append(f"✅ {lib} v{version} - {desc}")
            elif lib == "datasets":
                import datasets
                version = datasets.__version__
                installed.append(f"✅ {lib} v{version} - {desc}")
        except ImportError:
            missing.append(f"❌ {lib} - {desc}")
    
    # 打印结果
    for msg in installed:
        print(msg)
    
    if missing:
        print("\n缺少以下依赖:")
        for msg in missing:
            print(msg)
        print("\n请运行以下命令安装:")
        print("pip install peft>=0.4.0 datasets>=2.14.0")
        return False
    else:
        print("\n✅ 所有必需依赖已安装！")
        return True


def test_trainer_import():
    """测试训练器是否能正确导入"""
    print("\n" + "=" * 70)
    print("🔧 测试训练器导入...")
    print("=" * 70)
    
    try:
        from src.training.zh_trainer import ZhTrainer
        print("✅ 中文训练器导入成功")
        
        from src.training.en_trainer import EnTrainer
        print("✅ 英文训练器导入成功")
        
        from src.training.trainer import ModelTrainer
        print("✅ 主训练器导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 训练器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trainer_initialization():
    """测试训练器初始化"""
    print("\n" + "=" * 70)
    print("🚀 测试训练器初始化...")
    print("=" * 70)
    
    try:
        from src.training.zh_trainer import ZhTrainer
        from src.training.en_trainer import EnTrainer
        
        # 测试中文训练器
        zh_trainer = ZhTrainer(use_gpu=False)
        print(f"✅ 中文训练器初始化成功: {zh_trainer.model_name}")
        
        # 测试英文训练器
        en_trainer = EnTrainer(use_gpu=False)
        print(f"✅ 英文训练器初始化成功: {en_trainer.model_name}")
        
        return True
    except Exception as e:
        print(f"❌ 训练器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_loading():
    """测试模型加载（不实际加载，只检查配置）"""
    print("\n" + "=" * 70)
    print("📥 检查模型配置...")
    print("=" * 70)
    
    try:
        from src.training.zh_trainer import ZhTrainer
        
        zh_trainer = ZhTrainer(use_gpu=False)
        
        print(f"中文模型配置:")
        print(f"  - 模型名称: {zh_trainer.model_name}")
        print(f"  - 语言: {zh_trainer.language}")
        print(f"  - 量化: {zh_trainer.config.get('quantization')}")
        print(f"  - 批次大小: {zh_trainer.config.get('batch_size')}")
        print(f"  - 学习率: {zh_trainer.config.get('learning_rate')}")
        print(f"  - 训练轮数: {zh_trainer.config.get('epochs')}")
        
        print("\n⚠️ 注意: 实际模型加载需要下载模型文件到 ./models/cache/")
        print("   中文模型: Qwen/Qwen2-1.5B-Instruct")
        print("   英文模型: microsoft/DialoGPT-medium")
        
        return True
    except Exception as e:
        print(f"❌ 模型配置检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_training_data_preparation():
    """测试训练数据准备"""
    print("\n" + "=" * 70)
    print("📊 测试训练数据准备...")
    print("=" * 70)
    
    try:
        from src.training.zh_trainer import ZhTrainer
        
        zh_trainer = ZhTrainer(use_gpu=False)
        
        # 创建测试数据
        test_data = [
            {
                "original": "这是一个普通的剧本",
                "viral": "【震撼】这是一个令人震惊的爆款剧本！"
            },
            {
                "original": "今天天气很好",
                "viral": "【独家】今天的天气好到让人难以置信！"
            }
        ]
        
        # 准备数据
        processed_data = zh_trainer.prepare_chinese_data(test_data)
        
        print(f"✅ 数据准备成功:")
        print(f"  - 样本数量: {processed_data['statistics']['total_samples']}")
        print(f"  - 平均长度: {processed_data['statistics']['avg_length']:.1f}")
        print(f"  - 中文字符比例: {processed_data['statistics']['chinese_char_ratio']:.2%}")
        print(f"  - 词汇量: {processed_data['statistics']['vocabulary_size']}")
        
        return True
    except Exception as e:
        print(f"❌ 数据准备失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("🎯 VisionAI-ClipsMaster 真实训练系统测试")
    print("=" * 70)
    
    results = []
    
    # 运行所有测试
    results.append(("依赖检查", test_dependencies()))
    results.append(("训练器导入", test_trainer_import()))
    results.append(("训练器初始化", test_trainer_initialization()))
    results.append(("模型配置", test_model_loading()))
    results.append(("数据准备", test_training_data_preparation()))
    
    # 打印总结
    print("\n" + "=" * 70)
    print("📋 测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！真实训练系统已就绪！")
        print("\n下一步:")
        print("1. 确保已下载模型到 ./models/cache/")
        print("2. 准备训练数据（原始剧本 + 爆款剧本对）")
        print("3. 在UI中点击'开始训练'按钮")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    exit(main())

