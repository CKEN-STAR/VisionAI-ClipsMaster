#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 导入分析和优化脚本
"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_imports_usage():
    """分析导入使用情况"""
    logger.info("🔍 开始分析导入使用情况")
    logger.info("=" * 60)
    
    # 读取文件内容
    with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析结果
    analysis_results = {
        'unused_imports': [],
        'conditional_imports': [],
        'type_hint_imports': [],
        'used_imports': [],
        'recommendations': {}
    }
    
    # 1. 提取所有导入语句
    logger.info("1. 提取所有导入语句")
    
    # 标准库导入
    standard_imports = [
        'tempfile', 'shutil', 'threading', 're', 'requests', 'logging'
    ]
    
    # 类型提示导入
    type_hint_imports = [
        'Dict', 'List', 'Any', 'Optional'
    ]
    
    # PyQt6导入
    pyqt_imports = [
        'QSize'
    ]
    
    # 条件导入（在try-except块中）
    conditional_imports = [
        'is_qt6', 'setup_panel_hotkeys', 'setup_global_hotkeys', 'AlertManager',
        'get_optimized_config', 'apply_optimizations', 'optimize_rendering_for_tier',
        'optimize_memory_for_tier', 'start_memory_monitoring', 'DiskCacheManager',
        'InputOptimizer', 'PowerAwareUI', 'ClipGenerator', 'SmartCompressor',
        'process_subtitle_text', 'score_video_quality', 'ProgressTracker',
        'TrainingFeeder'
    ]
    
    # 2. 检查每个导入的使用情况
    logger.info("2. 检查导入使用情况")
    
    # 检查标准库导入
    for imp in standard_imports:
        usage_count = content.count(imp)
        import_count = content.count(f'import {imp}')
        actual_usage = usage_count - import_count
        
        if actual_usage <= 0:
            analysis_results['unused_imports'].append({
                'name': imp,
                'type': 'standard_library',
                'usage_count': actual_usage,
                'recommendation': 'REMOVE'
            })
        else:
            analysis_results['used_imports'].append({
                'name': imp,
                'type': 'standard_library',
                'usage_count': actual_usage
            })
    
    # 检查类型提示导入
    for imp in type_hint_imports:
        # 检查是否在类型注解中使用
        type_usage = len(re.findall(rf'\b{imp}\\\1', content)) + len(re.findall(rf': {imp}\b', content))
        
        if type_usage > 0:
            analysis_results['type_hint_imports'].append({
                'name': imp,
                'type': 'type_hint',
                'usage_count': type_usage,
                'recommendation': 'KEEP'
            })
        else:
            analysis_results['unused_imports'].append({
                'name': imp,
                'type': 'type_hint',
                'usage_count': 0,
                'recommendation': 'REMOVE'
            })
    
    # 检查PyQt6导入
    for imp in pyqt_imports:
        usage_count = content.count(imp)
        import_count = content.count(f'{imp}')
        actual_usage = usage_count - import_count
        
        if actual_usage <= 0:
            analysis_results['unused_imports'].append({
                'name': imp,
                'type': 'pyqt6',
                'usage_count': actual_usage,
                'recommendation': 'REMOVE'
            })
        else:
            analysis_results['used_imports'].append({
                'name': imp,
                'type': 'pyqt6',
                'usage_count': actual_usage
            })
    
    # 检查条件导入
    for imp in conditional_imports:
        # 检查是否在try-except块外使用
        usage_patterns = [
            rf'\b{imp}\\\1',  # 函数调用
            rf'\b{imp}\\\1',  # 方法调用
            rf'= {imp}\b',  # 赋值
            rf'isinstance.*{imp}',  # isinstance检查
        ]
        
        total_usage = 0
        for pattern in usage_patterns:
            total_usage += len(re.findall(pattern, content))
        
        if total_usage > 0:
            analysis_results['conditional_imports'].append({
                'name': imp,
                'type': 'conditional',
                'usage_count': total_usage,
                'recommendation': 'KEEP'
            })
        else:
            # 检查是否在try-except块中定义但未使用
            try_except_pattern = rf'try:.*?from.*{imp}.*?except.*?:'
            if re.search(try_except_pattern, content, re.DOTALL):
                analysis_results['conditional_imports'].append({
                    'name': imp,
                    'type': 'conditional_unused',
                    'usage_count': 0,
                    'recommendation': 'REVIEW'
                })
            else:
                analysis_results['unused_imports'].append({
                    'name': imp,
                    'type': 'conditional',
                    'usage_count': 0,
                    'recommendation': 'REMOVE'
                })
    
    # 3. 生成建议
    logger.info("3. 生成优化建议")
    
    # 按优先级分类
    critical_removals = [item for item in analysis_results['unused_imports'] 
                        if item['recommendation'] == 'REMOVE' and item['type'] in ['standard_library', 'pyqt6']]
    
    optional_removals = [item for item in analysis_results['unused_imports'] 
                        if item['recommendation'] == 'REMOVE' and item['type'] == 'type_hint']
    
    review_items = [item for item in analysis_results['conditional_imports'] 
                   if item['recommendation'] == 'REVIEW']
    
    analysis_results['recommendations'] = {
        'critical_removals': critical_removals,
        'optional_removals': optional_removals,
        'review_items': review_items,
        'keep_items': analysis_results['type_hint_imports'] + 
                     [item for item in analysis_results['conditional_imports'] 
                      if item['recommendation'] == 'KEEP']
    }
    
    return analysis_results

def generate_optimization_plan(analysis_results):
    """生成优化计划"""
    logger.info("📋 生成优化计划")
    logger.info("=" * 60)
    
    plan = {
        'phase1_critical': [],
        'phase2_optional': [],
        'phase3_review': [],
        'keep_justified': []
    }
    
    # Phase 1: 关键移除（确定未使用的标准库和PyQt导入）
    for item in analysis_results['recommendations']['critical_removals']:
        plan['phase1_critical'].append({
            'import_name': item['name'],
            'import_type': item['type'],
            'action': 'REMOVE',
            'risk': 'LOW',
            'justification': f"未在代码中使用 (使用次数: {item['usage_count']})"
        })
    
    # Phase 2: 可选移除（未使用的类型提示）
    for item in analysis_results['recommendations']['optional_removals']:
        plan['phase2_optional'].append({
            'import_name': item['name'],
            'import_type': item['type'],
            'action': 'REMOVE',
            'risk': 'LOW',
            'justification': f"类型提示未使用 (使用次数: {item['usage_count']})"
        })
    
    # Phase 3: 需要审查的条件导入
    for item in analysis_results['recommendations']['review_items']:
        plan['phase3_review'].append({
            'import_name': item['name'],
            'import_type': item['type'],
            'action': 'REVIEW',
            'risk': 'MEDIUM',
            'justification': f"条件导入但未使用，需要确认是否为未来功能保留"
        })
    
    # 保留的导入
    for item in analysis_results['recommendations']['keep_items']:
        plan['keep_justified'].append({
            'import_name': item['name'],
            'import_type': item['type'],
            'action': 'KEEP',
            'risk': 'NONE',
            'justification': f"正在使用 (使用次数: {item['usage_count']})" if item['usage_count'] > 0 
                           else "条件导入，用于可选功能"
        })
    
    return plan

def display_analysis_results(analysis_results, optimization_plan):
    """显示分析结果"""
    logger.info("📊 显示分析结果")
    logger.info("=" * 60)
    
    print("\n" + "=" * 80)
    print("VisionAI-ClipsMaster 导入分析结果")
    print("=" * 80)
    
    # 统计信息
    total_unused = len(analysis_results['unused_imports'])
    total_conditional = len(analysis_results['conditional_imports'])
    total_used = len(analysis_results['used_imports'])
    total_type_hints = len(analysis_results['type_hint_imports'])
    
    print(f"\n📊 统计信息:")
    print(f"  - 未使用导入: {total_unused}")
    print(f"  - 条件导入: {total_conditional}")
    print(f"  - 正在使用: {total_used}")
    print(f"  - 类型提示: {total_type_hints}")
    
    # Phase 1: 关键移除
    print(f"\n🔴 Phase 1 - 关键移除 ({len(optimization_plan['phase1_critical'])} 项):")
    for item in optimization_plan['phase1_critical']:
        print(f"  ❌ {item['import_name']} ({item['import_type']}) - {item['justification']}")
    
    # Phase 2: 可选移除
    print(f"\n🟡 Phase 2 - 可选移除 ({len(optimization_plan['phase2_optional'])} 项):")
    for item in optimization_plan['phase2_optional']:
        print(f"  ⚠️ {item['import_name']} ({item['import_type']}) - {item['justification']}")
    
    # Phase 3: 需要审查
    print(f"\n🔵 Phase 3 - 需要审查 ({len(optimization_plan['phase3_review'])} 项):")
    for item in optimization_plan['phase3_review']:
        print(f"  🔍 {item['import_name']} ({item['import_type']}) - {item['justification']}")
    
    # 保留的导入
    print(f"\n✅ 保留的导入 ({len(optimization_plan['keep_justified'])} 项):")
    for item in optimization_plan['keep_justified']:
        print(f"  ✓ {item['import_name']} ({item['import_type']}) - {item['justification']}")
    
    print("\n" + "=" * 80)

def main():
    """主函数"""
    logger.info("🚀 开始VisionAI-ClipsMaster导入分析")
    logger.info("=" * 80)
    
    try:
        # 1. 分析导入使用情况
        analysis_results = analyze_imports_usage()
        
        # 2. 生成优化计划
        optimization_plan = generate_optimization_plan(analysis_results)
        
        # 3. 显示结果
        display_analysis_results(analysis_results, optimization_plan)
        
        # 4. 保存结果到文件
        import json
        with open("import_analysis_results.json", 'w', encoding='utf-8') as f:
            json.dump({
                'analysis_results': analysis_results,
                'optimization_plan': optimization_plan
            }, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ 分析完成，结果已保存到 import_analysis_results.json")
        
        return optimization_plan
        
    except Exception as e:
        logger.error(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
    
    if results:
        print("\n🎯 下一步: 根据优化计划逐步移除未使用的导入")
    else:
        print("\n❌ 分析失败，请检查错误信息")
