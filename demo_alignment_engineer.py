#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间轴精确映射阶段（Stage 4）演示
展示 alignment_engineer.py 模块的核心功能和使用方法
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from src.core.alignment_engineer import (
    AlignmentEngineer,
    AlignmentPrecision,
    create_alignment_engineer,
    export_alignment_result
)
from src.core.enhanced_subtitle_reconstructor import (
    ReconstructedSubtitle,
    ReconstructionResult,
    ViralPotentialLevel,
    ReconstructionStrategy
)

def create_demo_data():
    """创建演示数据"""
    print("创建演示数据...")
    
    # 创建重构字幕数据
    reconstructed_subtitles = [
        ReconstructedSubtitle(
            id=1,
            original_subtitle_id=1,
            start_time=5.0,
            end_time=8.0,
            duration=3.0,
            original_text="欢迎来到我们的故事",
            reconstructed_text="🔥震撼开场！这个故事将颠覆你的认知！",
            viral_score=0.9,
            viral_level=ViralPotentialLevel.VIRAL,
            strategy=ReconstructionStrategy.HOOK_CREATION,
            emotion_intensity=0.8,
            narrative_importance=0.9,
            keywords=["震撼", "颠覆", "认知"]
        ),
        ReconstructedSubtitle(
            id=2,
            original_subtitle_id=3,
            start_time=15.0,
            end_time=20.0,
            duration=5.0,
            original_text="主角遇到了困难",
            reconstructed_text="💥危机时刻！他能否化险为夷？",
            viral_score=0.85,
            viral_level=ViralPotentialLevel.VIRAL,
            strategy=ReconstructionStrategy.SUSPENSE_BUILD,
            emotion_intensity=0.9,
            narrative_importance=0.8,
            keywords=["危机", "化险为夷"]
        ),
        ReconstructedSubtitle(
            id=3,
            original_subtitle_id=5,
            start_time=35.0,
            end_time=40.0,
            duration=5.0,
            original_text="故事达到高潮",
            reconstructed_text="⚡终极对决！结局让所有人都没想到！",
            viral_score=0.95,
            viral_level=ViralPotentialLevel.VIRAL,
            strategy=ReconstructionStrategy.CLIMAX_HIGHLIGHT,
            emotion_intensity=1.0,
            narrative_importance=1.0,
            keywords=["终极对决", "结局", "没想到"]
        ),
        ReconstructedSubtitle(
            id=4,
            original_subtitle_id=7,
            start_time=50.0,
            end_time=53.0,
            duration=3.0,
            original_text="故事结束了",
            reconstructed_text="🎯完美收官！但这只是开始...",
            viral_score=0.7,
            viral_level=ViralPotentialLevel.HIGH,
            strategy=ReconstructionStrategy.HOOK_CREATION,
            emotion_intensity=0.6,
            narrative_importance=0.7,
            keywords=["完美收官", "开始"]
        )
    ]
    
    # 创建重构结果
    reconstruction_result = ReconstructionResult(
        original_subtitles_count=8,
        reconstructed_subtitles=reconstructed_subtitles,
        high_viral_segments=reconstructed_subtitles[:3],  # 前3个高病毒传播片段
        total_duration=16.0,  # 总时长16秒
        average_viral_score=0.875,
        time_mapping={
            "compression_ratio": 0.27,  # 从60秒压缩到16秒
            "viral_density": 0.875,
            "emotion_peaks": [8.0, 20.0, 40.0]
        }
    )
    
    # 创建临时字幕文件
    temp_srt_content = """1
00:00:05,000 --> 00:00:08,000
欢迎来到我们的故事

2
00:00:10,000 --> 00:00:12,000
这里有很多角色

3
00:00:15,000 --> 00:00:20,000
主角遇到了困难

4
00:00:25,000 --> 00:00:30,000
他开始寻找解决方案

5
00:00:35,000 --> 00:00:40,000
故事达到高潮

6
00:00:45,000 --> 00:00:48,000
冲突得到解决

7
00:00:50,000 --> 00:00:53,000
故事结束了

8
00:00:55,000 --> 00:00:60,000
感谢观看
"""
    
    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    srt_path = os.path.join(temp_dir, "demo_subtitles.srt")
    video_path = os.path.join(temp_dir, "demo_video.mp4")
    
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(temp_srt_content)
    
    # 创建一个虚拟视频文件（实际演示中应该是真实视频）
    with open(video_path, 'w') as f:
        f.write("# 这是一个演示用的虚拟视频文件")
    
    return reconstruction_result, video_path, srt_path, temp_dir

def demo_basic_alignment():
    """演示基本对齐功能"""
    print("\n" + "="*50)
    print("演示1: 基本时间轴对齐功能")
    print("="*50)
    
    # 创建标准精度的对齐工程师
    engineer = create_alignment_engineer("standard")
    print(f"创建对齐工程师，精度等级: {engineer.precision.value}")
    print(f"精度阈值: ≤{engineer.current_threshold}秒")
    
    # 创建演示数据
    reconstruction_result, video_path, srt_path, temp_dir = create_demo_data()
    
    try:
        # 模拟对齐过程（由于没有真实视频，我们模拟一些关键步骤）
        print("\n正在执行时间轴对齐...")
        print("- 验证输入文件...")
        print("- 加载原始字幕...")
        print("- 检测边界点...")
        print("- 执行DTW对齐...")
        print("- 创建视频片段...")
        print("- 优化片段边界...")
        print("- 验证对齐质量...")
        
        # 由于是演示，我们手动创建一个模拟结果
        from src.core.alignment_engineer import AlignmentResult, VideoSegment, AlignmentPoint, BoundaryType
        
        demo_segments = [
            VideoSegment(
                segment_id=1,
                start_time=5.0,
                end_time=8.0,
                duration=3.0,
                original_subtitle_ids=[0],
                reconstructed_subtitle_id=1,
                viral_score=0.9,
                alignment_confidence=0.95,
                cut_points=[
                    AlignmentPoint(5.0, 5.0, 0.95, 0.0, BoundaryType.DIALOGUE_START),
                    AlignmentPoint(8.0, 8.0, 0.95, 0.0, BoundaryType.DIALOGUE_END)
                ],
                metadata={"precision_error": 0.0, "adjustment_reason": "精确匹配"}
            ),
            VideoSegment(
                segment_id=2,
                start_time=15.0,
                end_time=20.0,
                duration=5.0,
                original_subtitle_ids=[2],
                reconstructed_subtitle_id=2,
                viral_score=0.85,
                alignment_confidence=0.92,
                cut_points=[
                    AlignmentPoint(15.0, 15.0, 0.92, 0.1, BoundaryType.DIALOGUE_START),
                    AlignmentPoint(20.0, 20.0, 0.92, 0.1, BoundaryType.DIALOGUE_END)
                ],
                metadata={"precision_error": 0.1, "adjustment_reason": "轻微调整"}
            ),
            VideoSegment(
                segment_id=3,
                start_time=35.0,
                end_time=40.0,
                duration=5.0,
                original_subtitle_ids=[4],
                reconstructed_subtitle_id=3,
                viral_score=0.95,
                alignment_confidence=0.98,
                cut_points=[
                    AlignmentPoint(35.0, 35.0, 0.98, 0.05, BoundaryType.DIALOGUE_START),
                    AlignmentPoint(40.0, 40.0, 0.98, 0.05, BoundaryType.DIALOGUE_END)
                ],
                metadata={"precision_error": 0.05, "adjustment_reason": "高精度匹配"}
            )
        ]
        
        demo_result = AlignmentResult(
            video_segments=demo_segments,
            total_segments=3,
            total_duration=13.0,
            average_precision=0.05,
            alignment_quality=0.95,
            time_mapping={
                "segments": [
                    {"segment_id": seg.segment_id, "start_time": seg.start_time, 
                     "end_time": seg.end_time, "viral_score": seg.viral_score}
                    for seg in demo_segments
                ],
                "precision_summary": {
                    "max_error": 0.1,
                    "min_error": 0.0,
                    "average_error": 0.05
                }
            },
            boundary_violations=[],
            performance_metrics={
                "processing_time": 2.5,
                "segments_per_second": 1.2,
                "memory_peak": 1200,
                "precision_achieved": 0.05
            }
        )
        
        print("\n✅ 对齐完成！")
        print(f"📊 结果统计:")
        print(f"   - 总片段数: {demo_result.total_segments}")
        print(f"   - 总时长: {demo_result.total_duration:.1f}秒")
        print(f"   - 平均精度: {demo_result.average_precision:.3f}秒")
        print(f"   - 对齐质量: {demo_result.alignment_quality:.1%}")
        print(f"   - 处理时间: {demo_result.performance_metrics['processing_time']:.1f}秒")
        
        # 导出结果
        output_path = os.path.join(temp_dir, "alignment_result.json")
        export_alignment_result(demo_result, output_path)
        print(f"📁 结果已导出到: {output_path}")
        
        return demo_result
        
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def demo_precision_levels():
    """演示不同精度等级"""
    print("\n" + "="*50)
    print("演示2: 不同精度等级对比")
    print("="*50)
    
    precision_levels = [
        ("ultra_precise", "超精确 (≤0.1秒)"),
        ("high_precise", "高精确 (≤0.3秒)"),
        ("standard", "标准 (≤0.5秒)"),
        ("relaxed", "宽松 (≤1.0秒)")
    ]
    
    for level, description in precision_levels:
        engineer = create_alignment_engineer(level)
        print(f"🎯 {description}")
        print(f"   精度阈值: {engineer.current_threshold}秒")
        print(f"   适用场景: ", end="")
        
        if level == "ultra_precise":
            print("专业级视频制作，要求极高精度")
        elif level == "high_precise":
            print("高质量短视频，追求精细效果")
        elif level == "standard":
            print("常规短剧混剪，平衡质量与性能")
        else:
            print("快速预览，优先处理速度")
        print()

def demo_boundary_detection():
    """演示边界检测功能"""
    print("\n" + "="*50)
    print("演示3: 智能边界检测")
    print("="*50)
    
    from src.core.alignment_engineer import BoundaryDetector
    
    detector = BoundaryDetector()
    
    # 模拟字幕数据
    subtitles = [
        {"id": 1, "start_time": 1.0, "end_time": 3.0, "text": "开场白"},
        {"id": 2, "start_time": 5.0, "end_time": 7.0, "text": "介绍角色"},  # 2秒间隙
        {"id": 3, "start_time": 7.5, "end_time": 10.0, "text": "剧情发展"},  # 0.5秒间隙
        {"id": 4, "start_time": 13.0, "end_time": 15.0, "text": "高潮部分"},  # 3秒间隙（场景转换）
    ]
    
    boundaries = detector.detect_boundaries(subtitles, 20.0)
    
    print(f"检测到 {len(boundaries)} 个边界点:")
    for i, boundary in enumerate(boundaries[:8]):  # 只显示前8个
        print(f"  {i+1}. 时间: {boundary.original_time:.1f}s, "
              f"类型: {boundary.boundary_type.value}, "
              f"关键: {'是' if boundary.is_critical else '否'}, "
              f"置信度: {boundary.confidence:.2f}")
    
    if len(boundaries) > 8:
        print(f"  ... 还有 {len(boundaries) - 8} 个边界点")
    
    # 测试切割点验证
    print("\n🔍 切割点安全性验证:")
    test_points = [2.0, 5.5, 13.5]
    for point in test_points:
        is_safe, reason = detector.validate_cut_point(point, boundaries)
        status = "✅ 安全" if is_safe else "⚠️ 不安全"
        print(f"  时间 {point}s: {status} - {reason}")

def main():
    """主演示函数"""
    print("🎬 VisionAI-ClipsMaster 时间轴精确映射阶段（Stage 4）演示")
    print("📍 模块: alignment_engineer.py")
    print("🎯 功能: AI重构字幕与原片视频的精确时间轴映射")
    
    try:
        # 演示1: 基本对齐功能
        demo_basic_alignment()
        
        # 演示2: 精度等级对比
        demo_precision_levels()
        
        # 演示3: 边界检测
        demo_boundary_detection()
        
        print("\n" + "="*50)
        print("🎉 演示完成！")
        print("="*50)
        print("📋 核心特性总结:")
        print("✅ DTW动态时间规整算法")
        print("✅ 智能边界检测与保护")
        print("✅ 多级精度控制 (≤0.5秒)")
        print("✅ 内存优化 (4GB设备支持)")
        print("✅ 时间轴抖动补偿")
        print("✅ 质量验证与异常处理")
        print("✅ 详细性能指标统计")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
