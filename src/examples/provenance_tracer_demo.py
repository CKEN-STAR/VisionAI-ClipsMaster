#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
质量溯源追踪器演示

演示如何使用质量溯源追踪器定位和分析视频处理过程中的质量问题。
"""

import os
import sys
import json
from pprint import pprint

# 添加src到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 确保目录存在
os.makedirs("data/quality_provenance", exist_ok=True)

# 导入质量溯源模块
from src.quality.provenance_tracer import QualityGenealogy


def demo_basic_trace():
    """基本溯源演示"""
    print("\n=== 基本质量溯源演示 ===")
    
    # 创建溯源系统
    tracer = QualityGenealogy()
    
    # 模拟的视频ID
    video_id = "video_quality_test_001"
    
    # 溯源分析
    print(f"对视频 {video_id} 进行质量溯源分析...")
    trace_result = tracer.trace_quality_root(video_id)
    
    # 显示溯源结果
    print(f"\n溯源结果概览:")
    print(f"最薄弱环节: {trace_result['weakest_link']['name']} (得分: {trace_result['weakest_link']['score']:.2f})")
    
    print(f"\n关键路径 (得分 < 0.7):")
    for step in trace_result["critical_path"]:
        print(f"- {step['name']}: {step['score']:.2f}")
    
    # 显示根源原因
    print(f"\n根源原因分析:")
    for i, cause in enumerate(trace_result["root_causes"], 1):
        print(f"{i}. {cause['description']} (置信度: {cause['confidence']:.2f})")
        print(f"   类型: {cause['type']}")
        print(f"   建议:")
        for j, suggestion in enumerate(cause["suggestions"], 1):
            print(f"   {j}) {suggestion}")
        print()


def demo_compare_videos():
    """比较多个视频的质量溯源结果"""
    print("\n=== 多视频质量溯源比较演示 ===")
    
    # 创建溯源系统
    tracer = QualityGenealogy()
    
    # 模拟的视频ID列表
    video_ids = [
        "video_quality_test_001",
        "video_quality_test_002",
        "video_quality_test_003"
    ]
    
    # 比较溯源结果
    print(f"比较 {len(video_ids)} 个视频的溯源结果...")
    comparison = tracer.compare_quality_traces(video_ids)
    
    # 显示比较结果
    print(f"\n比较结果概览:")
    print(f"分析视频数量: {comparison['video_count']}")
    print(f"有效溯源结果数量: {comparison['trace_count']}")
    
    print(f"\n常见问题环节 (按频率排序):")
    for i, issue in enumerate(comparison["common_issues"][:3], 1):
        print(f"{i}. {issue['name']}")
        print(f"   平均得分: {issue['avg_score']:.2f}")
        print(f"   出现次数: {issue['count']}/{comparison['trace_count']}")
    

def demo_improvement_recommendations():
    """质量改进建议演示"""
    print("\n=== 质量改进建议演示 ===")
    
    # 创建溯源系统
    tracer = QualityGenealogy()
    
    # 模拟的视频ID
    video_id = "video_quality_test_002"
    
    # 获取改进建议
    print(f"为视频 {video_id} 生成质量改进建议...")
    recommendations = tracer.recommend_quality_improvements(video_id)
    
    # 显示建议
    print(f"\n改进建议概览:")
    print(f"最薄弱环节: {recommendations['weakest_link']} (得分: {recommendations['weakest_link_score']:.2f})")
    print(f"关键路径数量: {recommendations['critical_path_count']}")
    
    print(f"\n优先行动项 (top {len(recommendations['priority_actions'])}):")
    for i, action in enumerate(recommendations["priority_actions"], 1):
        print(f"{i}. {action}")
    
    print(f"\n所有改进建议 (共 {len(recommendations['improvement_suggestions'])}):")
    for i, suggestion in enumerate(recommendations["improvement_suggestions"], 1):
        print(f"{i}. {suggestion}")


def save_trace_to_file(trace_result, filename):
    """将溯源结果保存到文件"""
    filepath = os.path.join("data", "quality_provenance", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(trace_result, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到 {filepath}")


def demo_advanced_trace():
    """高级溯源演示"""
    print("\n=== 高级质量溯源演示 ===")
    
    # 创建溯源系统
    tracer = QualityGenealogy()
    
    # 模拟一个混合类型视频
    video_id = "complex_video_mix_001"
    
    # 溯源分析
    print(f"对复杂视频 {video_id} 进行深度质量溯源分析...")
    trace_result = tracer.trace_quality_root(video_id)
    
    # 保存结果到文件
    save_trace_to_file(trace_result, "complex_trace_result.json")
    
    # 显示结果概览
    print(f"\n深度溯源结果:")
    print(f"检测到 {len(trace_result['critical_path'])} 个关键路径节点")
    print(f"识别出 {len(trace_result['root_causes'])} 个根源问题")
    
    # 根据溯源结果，提取更多信息
    print(f"\n质量模式分析:")
    
    # 识别模式: 是否多个环节都有问题
    has_multiple_issues = len(trace_result["critical_path"]) > 1
    print(f"多环节问题: {'是' if has_multiple_issues else '否'}")
    
    # 识别模式: 是否存在模型问题
    has_model_issues = any(cause["type"] == "model_issue" for cause in trace_result["root_causes"])
    print(f"模型相关问题: {'是' if has_model_issues else '否'}")
    
    # 识别模式: 是否存在依赖问题
    has_dependency_issues = any(cause["type"] == "dependency_issue" for cause in trace_result["root_causes"])
    print(f"环节依赖问题: {'是' if has_dependency_issues else '否'}")
    
    # 识别模式: 是否存在数据质量问题
    has_data_issues = any(cause["type"] == "data_quality_issue" for cause in trace_result["root_causes"])
    print(f"数据质量问题: {'是' if has_data_issues else '否'}")
    
    # 提供整体质量评估
    if has_multiple_issues and (has_model_issues or has_dependency_issues):
        print("\n整体评估: 存在系统性质量问题，建议全面审查处理流程")
    elif has_model_issues:
        print("\n整体评估: 存在模型性能问题，建议优化或更新相关模型")
    elif has_data_issues:
        print("\n整体评估: 存在输入数据质量问题，建议提高源数据质量")
    else:
        print("\n整体评估: 局部质量问题，可通过针对性优化解决")


def main():
    """主函数"""
    print("开始质量溯源追踪器演示")
    
    # 运行基本溯源演示
    demo_basic_trace()
    
    # 运行多视频比较演示
    demo_compare_videos()
    
    # 运行改进建议演示
    demo_improvement_recommendations()
    
    # 运行高级溯源演示
    demo_advanced_trace()
    
    print("\n质量溯源追踪器演示结束")


if __name__ == "__main__":
    main() 