#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster API方法验证脚本
用于确认核心模块的实际方法名和接口
"""

import sys
import inspect
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def inspect_class_methods(cls, class_name):
    """检查类的所有方法"""
    print(f"\n🔍 {class_name} 类方法检查:")
    print("=" * 50)
    
    methods = []
    for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
        if not name.startswith('_'):  # 排除私有方法
            methods.append(name)
    
    for name in dir(cls):
        if not name.startswith('_') and callable(getattr(cls, name)):
            if name not in methods:
                methods.append(name)
    
    methods = sorted(set(methods))
    
    if methods:
        for method in methods:
            try:
                sig = inspect.signature(getattr(cls, method))
                print(f"  ✅ {method}{sig}")
            except:
                print(f"  ✅ {method}(...)")
    else:
        print("  ❌ 未找到公共方法")
    
    return methods

def main():
    """主验证函数"""
    print("🚀 VisionAI-ClipsMaster API方法验证")
    print("=" * 60)
    
    verification_results = {}
    
    # 1. 验证对齐工程师
    try:
        from src.core.alignment_engineer import AlignmentEngineer
        print(f"✅ 成功导入 AlignmentEngineer")
        alignment_engineer = AlignmentEngineer()
        methods = inspect_class_methods(alignment_engineer, "AlignmentEngineer")
        verification_results["AlignmentEngineer"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "align_subtitles_to_video",
            "has_expected": "align_subtitles_to_video" in methods
        }
    except Exception as e:
        print(f"❌ AlignmentEngineer 导入失败: {e}")
        verification_results["AlignmentEngineer"] = {"imported": False, "error": str(e)}
    
    # 2. 验证剧本工程师
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        print(f"✅ 成功导入 ScreenplayEngineer")
        screenplay_engineer = ScreenplayEngineer()
        methods = inspect_class_methods(screenplay_engineer, "ScreenplayEngineer")
        verification_results["ScreenplayEngineer"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "reconstruct",
            "has_expected": "reconstruct" in methods
        }
    except Exception as e:
        print(f"❌ ScreenplayEngineer 导入失败: {e}")
        verification_results["ScreenplayEngineer"] = {"imported": False, "error": str(e)}
    
    # 3. 验证语言检测器
    try:
        from src.core.language_detector import LanguageDetector
        print(f"✅ 成功导入 LanguageDetector")
        language_detector = LanguageDetector()
        methods = inspect_class_methods(language_detector, "LanguageDetector")
        verification_results["LanguageDetector"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "detect",
            "has_expected": "detect" in methods
        }
    except Exception as e:
        print(f"❌ LanguageDetector 导入失败: {e}")
        verification_results["LanguageDetector"] = {"imported": False, "error": str(e)}
    
    # 4. 验证课程学习
    try:
        from src.training.curriculum import CurriculumLearning
        print(f"✅ 成功导入 CurriculumLearning")
        curriculum = CurriculumLearning()
        methods = inspect_class_methods(curriculum, "CurriculumLearning")
        verification_results["CurriculumLearning"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "create_learning_plan",
            "has_expected": "create_learning_plan" in methods
        }
    except Exception as e:
        print(f"❌ CurriculumLearning 导入失败: {e}")
        verification_results["CurriculumLearning"] = {"imported": False, "error": str(e)}
    
    # 5. 验证数据分离器
    try:
        from src.training.data_splitter import DataSplitter
        print(f"✅ 成功导入 DataSplitter")
        data_splitter = DataSplitter()
        methods = inspect_class_methods(data_splitter, "DataSplitter")
        verification_results["DataSplitter"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "split_and_process",
            "has_expected": "split_and_process" in methods
        }
    except Exception as e:
        print(f"❌ DataSplitter 导入失败: {e}")
        verification_results["DataSplitter"] = {"imported": False, "error": str(e)}
    
    # 6. 验证叙事分析器
    try:
        from src.core.narrative_analyzer import NarrativeAnalyzer
        print(f"✅ 成功导入 NarrativeAnalyzer")
        narrative_analyzer = NarrativeAnalyzer()
        methods = inspect_class_methods(narrative_analyzer, "NarrativeAnalyzer")
        verification_results["NarrativeAnalyzer"] = {
            "imported": True,
            "methods": methods,
            "expected_method": "analyze",
            "has_expected": "analyze" in methods
        }
    except Exception as e:
        print(f"❌ NarrativeAnalyzer 导入失败: {e}")
        verification_results["NarrativeAnalyzer"] = {"imported": False, "error": str(e)}
    
    # 生成修复建议
    print("\n\n📋 API修复建议报告")
    print("=" * 60)
    
    for class_name, result in verification_results.items():
        if result.get("imported"):
            expected = result.get("expected_method")
            has_expected = result.get("has_expected", False)
            methods = result.get("methods", [])
            
            print(f"\n🔧 {class_name}:")
            if has_expected:
                print(f"  ✅ 方法 '{expected}' 存在")
            else:
                print(f"  ❌ 方法 '{expected}' 不存在")
                print(f"  📝 可用方法: {', '.join(methods[:5])}")
                
                # 尝试找到相似的方法名
                similar_methods = []
                for method in methods:
                    if any(keyword in method.lower() for keyword in expected.split('_')):
                        similar_methods.append(method)
                
                if similar_methods:
                    print(f"  💡 建议使用: {', '.join(similar_methods)}")
        else:
            print(f"\n❌ {class_name}: 导入失败 - {result.get('error', 'Unknown error')}")
    
    print(f"\n\n📊 验证总结:")
    print(f"总类数: {len(verification_results)}")
    imported_count = sum(1 for r in verification_results.values() if r.get("imported"))
    method_match_count = sum(1 for r in verification_results.values() if r.get("has_expected"))
    
    print(f"成功导入: {imported_count}/{len(verification_results)}")
    print(f"方法匹配: {method_match_count}/{len(verification_results)}")
    print(f"整体匹配率: {method_match_count/len(verification_results)*100:.1f}%")

if __name__ == "__main__":
    main()
