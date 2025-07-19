#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 核心功能验证测试
"""

import sys
import os
import json
sys.path.append('.')

def test_core_functions():
    """测试核心功能"""
    print('=== VisionAI-ClipsMaster 核心功能验证测试 ===\n')
    
    test_results = {
        "screenplay_reconstruction": False,
        "language_detection": False,
        "model_switching": False,
        "jianying_export": False
    }
    
    # 测试1: AI剧本重构功能
    print('📝 测试1: AI剧本重构功能')
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        
        # 创建测试数据
        test_subtitles = [
            {'start_time': 0.0, 'end_time': 2.0, 'text': '今天天气很好'},
            {'start_time': 2.0, 'end_time': 4.0, 'text': '我去了公园散步'},
            {'start_time': 4.0, 'end_time': 6.0, 'text': '看到了很多花'},
            {'start_time': 6.0, 'end_time': 8.0, 'text': '心情变得很愉快'}
        ]
        
        engineer = ScreenplayEngineer()
        result = engineer.generate_screenplay(test_subtitles, language='zh')
        
        if result and 'screenplay' in result:
            print(f'✅ 剧本重构成功，生成{len(result["screenplay"])}个片段')
            print(f'   处理时间: {result.get("processing_time", 0):.3f}秒')
            test_results["screenplay_reconstruction"] = True
        else:
            print('❌ 剧本重构失败')
            
    except Exception as e:
        print(f'❌ 剧本重构测试失败: {e}')
    
    print()
    
    # 测试2: 语言检测功能
    print('🌐 测试2: 语言检测功能')
    try:
        from src.core.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        
        # 测试中文
        zh_result = detector.detect_from_text('这是一段中文测试文本，用于验证语言检测功能')
        print(f'✅ 中文检测结果: {zh_result}')
        
        # 测试英文
        en_result = detector.detect_from_text('This is an English test text for language detection')
        print(f'✅ 英文检测结果: {en_result}')
        
        if zh_result == 'zh' and en_result == 'en':
            test_results["language_detection"] = True
        
    except Exception as e:
        print(f'❌ 语言检测测试失败: {e}')
    
    print()
    
    # 测试3: 模型切换功能
    print('🔄 测试3: 模型切换功能')
    try:
        from src.core.model_switcher import ModelSwitcher
        
        switcher = ModelSwitcher()
        
        # 测试切换到中文模型
        zh_switch = switcher.switch_model('zh')
        print(f'✅ 切换到中文模型: {zh_switch}')
        print(f'   当前模型: {switcher.get_current_model()}')
        
        # 测试切换到英文模型
        en_switch = switcher.switch_model('en')
        print(f'✅ 切换到英文模型: {en_switch}')
        print(f'   当前模型: {switcher.get_current_model()}')
        
        if zh_switch and en_switch:
            test_results["model_switching"] = True
        
    except Exception as e:
        print(f'❌ 模型切换测试失败: {e}')
    
    print()
    
    # 测试4: 剪映导出功能
    print('📤 测试4: 剪映导出功能')
    try:
        from src.exporters.jianying_pro_exporter import JianYingProExporter
        
        exporter = JianYingProExporter()
        
        # 创建测试项目数据
        test_project = {
            'project_name': 'CoreFunctionTest',
            'segments': [
                {'start_time': 0.0, 'end_time': 2.0, 'text': '测试片段1'},
                {'start_time': 2.0, 'end_time': 4.0, 'text': '测试片段2'}
            ],
            'subtitles': []
        }
        
        # 测试导出
        output_path = 'test_output.json'
        success = exporter.export_project(test_project, output_path)
        
        if success:
            print('✅ 剪映项目导出成功')
            test_results["jianying_export"] = True
            # 清理测试文件
            if os.path.exists(output_path):
                os.remove(output_path)
        else:
            print('❌ 剪映项目导出失败')
            
    except Exception as e:
        print(f'❌ 剪映导出测试失败: {e}')
    
    print()
    print('=== 核心功能验证测试完成 ===')
    
    # 统计结果
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f'\n📊 测试结果统计:')
    print(f'   通过测试: {passed_tests}/{total_tests}')
    print(f'   成功率: {success_rate:.1f}%')
    
    if success_rate >= 75:
        print('🎉 核心功能基本正常，可以进行下一步优化')
    else:
        print('⚠️  部分核心功能存在问题，需要修复')
    
    return test_results

if __name__ == "__main__":
    test_core_functions()
