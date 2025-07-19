#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能分析工具
分析当前系统的性能状况，识别优化点
"""

import sys
import os
import time
import psutil
import gc
from pathlib import Path
sys.path.append('.')

def analyze_startup_performance():
    """分析启动性能"""
    print("🚀 启动性能分析")
    print("-" * 50)
    
    startup_times = {}
    
    # 测试核心模块导入时间
    modules_to_test = [
        ('screenplay_engineer', 'src.core.screenplay_engineer'),
        ('model_switcher', 'src.core.model_switcher'),
        ('language_detector', 'src.core.language_detector'),
        ('jianying_exporter', 'src.exporters.jianying_pro_exporter'),
    ]
    
    for module_name, module_path in modules_to_test:
        start_time = time.time()
        try:
            __import__(module_path)
            import_time = time.time() - start_time
            startup_times[module_name] = import_time
            print(f"✅ {module_name}: {import_time:.3f}秒")
        except Exception as e:
            print(f"❌ {module_name}: 导入失败 - {e}")
            startup_times[module_name] = -1
    
    total_startup_time = sum(t for t in startup_times.values() if t > 0)
    print(f"\n📊 总启动时间: {total_startup_time:.3f}秒")
    
    # 评估启动性能
    if total_startup_time <= 5.0:
        print("🎉 启动性能优秀 (≤5秒)")
    elif total_startup_time <= 10.0:
        print("✅ 启动性能良好 (≤10秒)")
    else:
        print("⚠️  启动性能需要优化 (>10秒)")
    
    return startup_times

def analyze_memory_usage():
    """分析内存使用情况"""
    print("\n💾 内存使用分析")
    print("-" * 50)
    
    # 获取系统内存信息
    memory = psutil.virtual_memory()
    print(f"系统总内存: {memory.total / 1024**3:.2f} GB")
    print(f"可用内存: {memory.available / 1024**3:.2f} GB")
    print(f"内存使用率: {memory.percent:.1f}%")
    
    # 获取当前进程内存使用
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"当前进程内存: {memory_info.rss / 1024**2:.2f} MB")
    
    # 测试模块加载后的内存使用
    print("\n模块加载内存影响:")
    
    # 记录基准内存
    gc.collect()
    baseline_memory = process.memory_info().rss
    
    # 测试加载大型模块
    try:
        import torch
        torch_memory = process.memory_info().rss
        torch_impact = (torch_memory - baseline_memory) / 1024**2
        print(f"PyTorch加载: +{torch_impact:.2f} MB")
    except ImportError:
        print("PyTorch未安装")
    
    # 评估内存使用
    current_memory_mb = memory_info.rss / 1024**2
    if current_memory_mb <= 400:
        print(f"🎉 内存使用优秀 ({current_memory_mb:.1f}MB ≤ 400MB)")
    elif current_memory_mb <= 800:
        print(f"✅ 内存使用良好 ({current_memory_mb:.1f}MB ≤ 800MB)")
    else:
        print(f"⚠️  内存使用需要优化 ({current_memory_mb:.1f}MB > 800MB)")
    
    return {
        "total_memory_gb": memory.total / 1024**3,
        "available_memory_gb": memory.available / 1024**3,
        "memory_usage_percent": memory.percent,
        "process_memory_mb": memory_info.rss / 1024**2
    }

def analyze_file_structure():
    """分析文件结构和大小"""
    print("\n📁 文件结构分析")
    print("-" * 50)
    
    project_root = Path('.')
    
    # 统计各类文件
    file_stats = {
        'python_files': 0,
        'config_files': 0,
        'model_files': 0,
        'test_files': 0,
        'total_size_mb': 0
    }
    
    for file_path in project_root.rglob('*'):
        if file_path.is_file():
            file_size = file_path.stat().st_size
            file_stats['total_size_mb'] += file_size / 1024**2
            
            if file_path.suffix == '.py':
                file_stats['python_files'] += 1
            elif file_path.suffix in ['.yaml', '.json', '.ini']:
                file_stats['config_files'] += 1
            elif 'model' in str(file_path).lower():
                file_stats['model_files'] += 1
            elif 'test' in str(file_path).lower():
                file_stats['test_files'] += 1
    
    print(f"Python文件: {file_stats['python_files']}")
    print(f"配置文件: {file_stats['config_files']}")
    print(f"模型文件: {file_stats['model_files']}")
    print(f"测试文件: {file_stats['test_files']}")
    print(f"项目总大小: {file_stats['total_size_mb']:.2f} MB")
    
    return file_stats

def generate_optimization_recommendations(startup_times, memory_stats, file_stats):
    """生成优化建议"""
    print("\n🎯 优化建议")
    print("=" * 50)
    
    recommendations = []
    
    # 启动时间优化建议
    total_startup = sum(t for t in startup_times.values() if t > 0)
    if total_startup > 5.0:
        recommendations.append({
            "category": "启动优化",
            "priority": "高",
            "suggestion": "实施延迟加载机制，将非核心模块改为按需导入",
            "expected_improvement": f"预计可减少{(total_startup - 3.0):.1f}秒启动时间"
        })
    
    # 内存优化建议
    if memory_stats['process_memory_mb'] > 400:
        recommendations.append({
            "category": "内存优化",
            "priority": "高",
            "suggestion": "实施内存池管理和智能垃圾回收机制",
            "expected_improvement": f"预计可减少{(memory_stats['process_memory_mb'] - 300):.0f}MB内存使用"
        })
    
    # 文件结构优化建议
    if file_stats['total_size_mb'] > 100:
        recommendations.append({
            "category": "存储优化",
            "priority": "中",
            "suggestion": "清理冗余文件，压缩静态资源",
            "expected_improvement": f"预计可减少{(file_stats['total_size_mb'] * 0.3):.0f}MB存储空间"
        })
    
    # 输出建议
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['category']} (优先级: {rec['priority']})")
        print(f"   建议: {rec['suggestion']}")
        print(f"   预期效果: {rec['expected_improvement']}")
    
    if not recommendations:
        print("🎉 当前性能表现良好，无需特别优化！")
    
    return recommendations

def main():
    """主函数"""
    print("=== VisionAI-ClipsMaster 性能分析报告 ===")
    print(f"分析时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行各项分析
    startup_times = analyze_startup_performance()
    memory_stats = analyze_memory_usage()
    file_stats = analyze_file_structure()
    
    # 生成优化建议
    recommendations = generate_optimization_recommendations(
        startup_times, memory_stats, file_stats
    )
    
    # 生成总结
    print("\n📋 性能分析总结")
    print("=" * 50)
    
    total_startup = sum(t for t in startup_times.values() if t > 0)
    memory_mb = memory_stats['process_memory_mb']
    
    performance_score = 100
    if total_startup > 5.0:
        performance_score -= 20
    if memory_mb > 400:
        performance_score -= 20
    if len(recommendations) > 2:
        performance_score -= 10
    
    print(f"性能评分: {performance_score}/100")
    
    if performance_score >= 90:
        print("🏆 性能优秀，系统运行流畅")
    elif performance_score >= 70:
        print("✅ 性能良好，可进行小幅优化")
    else:
        print("⚠️  性能需要改进，建议实施优化措施")
    
    return {
        "startup_times": startup_times,
        "memory_stats": memory_stats,
        "file_stats": file_stats,
        "recommendations": recommendations,
        "performance_score": performance_score
    }

if __name__ == "__main__":
    main()
