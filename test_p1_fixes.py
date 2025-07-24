#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1级别问题修复验证测试
验证重要问题是否已经修复
"""

import os
import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_trainer_methods():
    """测试训练器核心方法"""
    print("🔧 测试训练器核心方法...")
    
    results = {}
    
    # 测试中文训练器
    try:
        from src.training.zh_trainer import ZhTrainer
        zh_trainer = ZhTrainer()
        
        # 检查核心方法
        methods = ['train', 'validate', 'save_model']
        for method in methods:
            if hasattr(zh_trainer, method):
                print(f"✅ ZhTrainer.{method} 方法存在")
                results[f'zh_trainer_{method}'] = True
            else:
                print(f"❌ ZhTrainer.{method} 方法缺失")
                results[f'zh_trainer_{method}'] = False
        
        # 测试方法调用
        try:
            # 测试validate方法
            test_data = [
                {"original": "今天天气很好", "expected": "今天天气真不错"},
                {"original": "我去了公园", "expected": "我去公园散步了"}
            ]
            validate_result = zh_trainer.validate(test_data)
            if validate_result.get('success'):
                print("✅ ZhTrainer.validate 方法调用成功")
                results['zh_trainer_validate_call'] = True
            else:
                print("⚠️ ZhTrainer.validate 方法调用有问题")
                results['zh_trainer_validate_call'] = False
        except Exception as e:
            print(f"❌ ZhTrainer.validate 调用失败: {e}")
            results['zh_trainer_validate_call'] = False
        
        # 测试save_model方法
        try:
            save_result = zh_trainer.save_model("test_model_zh.bin")
            if save_result.get('success'):
                print("✅ ZhTrainer.save_model 方法调用成功")
                results['zh_trainer_save_call'] = True
            else:
                print("⚠️ ZhTrainer.save_model 方法调用有问题")
                results['zh_trainer_save_call'] = False
        except Exception as e:
            print(f"❌ ZhTrainer.save_model 调用失败: {e}")
            results['zh_trainer_save_call'] = False
            
    except Exception as e:
        print(f"❌ ZhTrainer 测试失败: {e}")
        results['zh_trainer'] = False
    
    # 测试英文训练器
    try:
        from src.training.en_trainer import EnTrainer
        en_trainer = EnTrainer()
        
        # 检查核心方法
        methods = ['train', 'validate', 'save_model']
        for method in methods:
            if hasattr(en_trainer, method):
                print(f"✅ EnTrainer.{method} 方法存在")
                results[f'en_trainer_{method}'] = True
            else:
                print(f"❌ EnTrainer.{method} 方法缺失")
                results[f'en_trainer_{method}'] = False
        
        # 测试方法调用
        try:
            # 测试validate方法
            test_data = [
                {"original": "Today is a good day", "expected": "Today is a wonderful day"},
                {"original": "I went to the park", "expected": "I went for a walk in the park"}
            ]
            validate_result = en_trainer.validate(test_data)
            if validate_result.get('success'):
                print("✅ EnTrainer.validate 方法调用成功")
                results['en_trainer_validate_call'] = True
            else:
                print("⚠️ EnTrainer.validate 方法调用有问题")
                results['en_trainer_validate_call'] = False
        except Exception as e:
            print(f"❌ EnTrainer.validate 调用失败: {e}")
            results['en_trainer_validate_call'] = False
        
        # 测试save_model方法
        try:
            save_result = en_trainer.save_model("test_model_en.bin")
            if save_result.get('success'):
                print("✅ EnTrainer.save_model 方法调用成功")
                results['en_trainer_save_call'] = True
            else:
                print("⚠️ EnTrainer.save_model 方法调用有问题")
                results['en_trainer_save_call'] = False
        except Exception as e:
            print(f"❌ EnTrainer.save_model 调用失败: {e}")
            results['en_trainer_save_call'] = False
            
    except Exception as e:
        print(f"❌ EnTrainer 测试失败: {e}")
        results['en_trainer'] = False
    
    return all(results.values())

def test_curriculum_fix():
    """测试课程学习模块修复"""
    print("\n🔧 测试课程学习模块...")
    
    try:
        # 测试原始类名
        from src.training.curriculum import CurriculumLearning
        curriculum_learning = CurriculumLearning()
        print("✅ CurriculumLearning 导入成功")
        
        # 测试别名
        from src.training.curriculum import Curriculum
        curriculum = Curriculum()
        print("✅ Curriculum 别名导入成功")
        
        # 验证它们是同一个类
        if CurriculumLearning == Curriculum:
            print("✅ 别名设置正确")
        else:
            print("⚠️ 别名设置可能有问题")
        
        # 测试基本方法
        if hasattr(curriculum, 'get_stages'):
            stages = curriculum.get_stages()
            print(f"✅ Curriculum.get_stages 方法可用，返回 {len(stages)} 个阶段")
        else:
            print("⚠️ Curriculum.get_stages 方法不可用")
        
        return True
        
    except ImportError as e:
        print(f"❌ Curriculum 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ Curriculum 测试失败: {e}")
        return False

def test_alignment_engineer_fix():
    """测试时间轴对齐工程师修复"""
    print("\n🔧 测试时间轴对齐工程师...")
    
    try:
        # 测试原始类名
        from src.core.alignment_engineer import PrecisionAlignmentEngineer
        precision_engineer = PrecisionAlignmentEngineer()
        print("✅ PrecisionAlignmentEngineer 导入成功")
        
        # 测试别名
        from src.core.alignment_engineer import AlignmentEngineer
        alignment_engineer = AlignmentEngineer()
        print("✅ AlignmentEngineer 别名导入成功")
        
        # 验证它们是同一个类
        if PrecisionAlignmentEngineer == AlignmentEngineer:
            print("✅ 别名设置正确")
        else:
            print("⚠️ 别名设置可能有问题")
        
        # 测试基本方法
        if hasattr(alignment_engineer, 'align_subtitle_to_video'):
            print("✅ AlignmentEngineer.align_subtitle_to_video 方法可用")
        else:
            print("⚠️ AlignmentEngineer.align_subtitle_to_video 方法不可用")
        
        return True
        
    except ImportError as e:
        print(f"❌ AlignmentEngineer 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ AlignmentEngineer 测试失败: {e}")
        return False

def test_import_stability():
    """测试导入稳定性"""
    print("\n🔧 测试P1级别模块导入稳定性...")
    
    modules = [
        'src.training.zh_trainer',
        'src.training.en_trainer',
        'src.training.curriculum',
        'src.core.alignment_engineer'
    ]
    
    success_count = 0
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"❌ {module} 导入失败: {e}")
    
    success_rate = success_count / len(modules) * 100
    print(f"\nP1级别导入成功率: {success_rate:.1f}% ({success_count}/{len(modules)})")
    
    return success_rate >= 100

def main():
    """主测试函数"""
    print("🎬 开始P1级别问题修复验证测试")
    print("=" * 60)
    
    start_time = time.time()
    
    # 执行测试
    test_results = {
        'trainer_methods': test_trainer_methods(),
        'curriculum_fix': test_curriculum_fix(),
        'alignment_engineer_fix': test_alignment_engineer_fix(),
        'import_stability': test_import_stability()
    }
    
    # 生成报告
    print("\n" + "=" * 60)
    print("📊 P1级别修复验证报告")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n总体结果: {passed_tests}/{total_tests} 通过")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    print(f"测试时长: {time.time() - start_time:.2f}秒")
    
    if passed_tests == total_tests:
        print("\n🎉 所有P1级别问题已成功修复！")
        return True
    else:
        print(f"\n⚠️ 还有 {total_tests - passed_tests} 个问题需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
