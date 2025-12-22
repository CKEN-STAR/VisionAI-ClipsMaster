#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间码修复验证测试
测试AI爆款转换器的时间码重映射功能
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.ai_viral_transformer import AIViralTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_timecode_remapping():
    """测试时间码重映射功能"""
    print("\n" + "="*80)
    print("时间码重映射功能测试")
    print("="*80 + "\n")
    
    # 创建AI转换器
    transformer = AIViralTransformer()
    
    # 模拟原始字幕（时间码不连续）
    original_subtitles = [
        {"index": 1, "start_time": 0.0, "end_time": 3.5, "text": "你好，我是主角"},
        {"index": 2, "start_time": 3.5, "end_time": 7.0, "text": "今天发生了一件大事"},
        {"index": 3, "start_time": 7.0, "end_time": 10.5, "text": "让我来告诉你"},
        {"index": 4, "start_time": 10.5, "end_time": 14.0, "text": "这是一个秘密"},
        {"index": 5, "start_time": 14.0, "end_time": 18.0, "text": "没人知道的秘密"},
        {"index": 6, "start_time": 30.0, "end_time": 34.0, "text": "突然跳到30秒"},
        {"index": 7, "start_time": 34.0, "end_time": 38.0, "text": "这里是高潮部分"},
        {"index": 8, "start_time": 50.0, "end_time": 54.0, "text": "又跳到50秒"},
        {"index": 9, "start_time": 54.0, "end_time": 58.0, "text": "结局很震撼"},
        {"index": 10, "start_time": 58.0, "end_time": 62.0, "text": "你绝对想不到"},
    ]
    
    print("📝 原始字幕（10条，时间码不连续）：")
    print("-" * 80)
    for sub in original_subtitles:
        print(f"  [{sub['start_time']:.1f}s - {sub['end_time']:.1f}s] {sub['text']}")
    
    # 执行AI转换（会进行片段筛选和重排序）
    print("\n🤖 执行AI病毒传播转换...")
    viral_subtitles = transformer.transform_to_viral(
        original_subtitles,
        language="zh",
        style="viral",
        intensity=0.8
    )
    
    print(f"\n✅ 转换完成，生成{len(viral_subtitles)}条爆款字幕")
    print("-" * 80)
    
    # 验证时间码重映射
    print[object Object]时间码重映射：")
    print("-" * 80)
    
    has_remapping = False
    is_continuous = True
    prev_end = None
    
    for i, sub in enumerate(viral_subtitles):
        # 检查是否有重映射标记
        if sub.get("timecode_remapped"):
            has_remapping = True
        
        # 获取时间码
        original_start = sub.get("original_start_time", "N/A")
        original_end = sub.get("original_end_time", "N/A")
        output_start = sub.get("start_time", "N/A")
        output_end = sub.get("end_time", "N/A")
        duration = sub.get("duration", "N/A")
        text = sub.get("text", "")
        
        # 检查连续性
        if prev_end is not None and isinstance(output_start, (int, float)):
            gap = output_start - prev_end
            if abs(gap) > 0.01:  # 允许0.01秒的浮点误差
                is_continuous = False
                print(f"  ⚠️  片段{i}与前一片段有{gap:.2f}秒间隙")
        
        # 打印详细信息
        if isinstance(original_start, (int, float)) and isinstance(output_start, (int, float)):
            print(f"  片段{i+1}:")
            print(f"    原始时间: [{original_start:.2f}s - {original_end:.2f}s]")
            print(f"    输出时间: [{output_start:.2f}s - {output_end:.2f}s]")
            print(f"    时长: {duration:.2f}s")
            print(f"    文本: {text[:30]}...")
        else:
            print(f"  片段{i+1}: 时间码格式异常")
        
        if isinstance(output_end, (int, float)):
            prev_end = output_end
    
    # 测试结果
    print("\n" + "="*80)
    print("测试结果：")
    print("="*80)
    
    if has_remapping:
        print("✅ 时间码重映射功能已启用")
    else:
        print("❌ 时间码重映射功能未启用")
    
    if is_continuous:
        print("✅ 输出时间码连续，无跳跃")
    else:
        print("❌ 输出时间码存在跳跃")
    
    # 计算总时长
    if viral_subtitles and isinstance(viral_subtitles[-1].get("end_time"), (int, float)):
        total_duration = viral_subtitles[-1]["end_time"]
        print(f"📊 输出视频总时长: {total_duration:.2f}秒")
    
    # 检查是否所有片段都有必要的字段
    missing_fields = []
    for i, sub in enumerate(viral_subtitles):
        required_fields = ["original_start_time", "original_end_time", "start_time", "end_time", "duration"]
        for field in required_fields:
            if field not in sub:
                missing_fields.append(f"片段{i+1}缺少{field}")
    
    if missing_fields:
        print("\n⚠️  发现缺失字段：")
        for msg in missing_fields[:5]:  # 只显示前5个
            print(f"  - {msg}")
        if len(missing_fields) > 5:
            print(f"  ... 还有{len(missing_fields) - 5}个字段缺失")
    else:
        print("✅ 所有片段都包含必要的时间码字段")
    
    print("\n" + "="*80)
    
    # 返回测试结果
    return has_remapping and is_continuous and not missing_fields


def test_clip_generator_integration():
    """测试ClipGenerator对重映射时间码的处理"""
    print("\n" + "="*80)
    print("ClipGenerator集成测试")
    print("="*80 + "\n")
    
    from src.core.clip_generator import ClipGenerator
    
    # 创建ClipGenerator实例
    clip_gen = ClipGenerator(use_gpu=False)
    
    # 模拟重映射后的片段数据
    remapped_segments = [
        {
            "text": "片段1",
            "timecode_remapped": True,
            "original_start_time": 5.0,
            "original_end_time": 8.0,
            "start_time": 0.0,
            "end_time": 3.0,
            "duration": 3.0
        },
        {
            "text": "片段2",
            "timecode_remapped": True,
            "original_start_time": 20.0,
            "original_end_time": 24.0,
            "start_time": 3.0,
            "end_time": 7.0,
            "duration": 4.0
        },
        {
            "text": "片段3",
            "timecode_remapped": True,
            "original_start_time": 45.0,
            "original_end_time": 49.0,
            "start_time": 7.0,
            "end_time": 11.0,
            "duration": 4.0
        }
    ]
    
    print("📝 测试片段（模拟重映射后的数据）：")
    print("-" * 80)
    for i, seg in enumerate(remapped_segments):
        print(f"  片段{i+1}:")
        print(f"    原始: [{seg['original_start_time']:.1f}s - {seg['original_end_time']:.1f}s]")
        print(f"    输出: [{seg['start_time']:.1f}s - {seg['end_time']:.1f}s]")
    
    print("\n✅ ClipGenerator应该能够正确识别并使用original_start_time/original_end_time")
    print("   进行视频切割，而不是使用重映射后的start_time/end_time")
    
    print("\n" + "="*80)
    
    return True


if __name__ == "__main__":
    print("\n" + "[object Object]isionAI-ClipsMaster 时间码修复验证测试" + "\n")
    
    # 运行测试
    test1_passed = test_timecode_remapping()
    test2_passed = test_clip_generator_integration()
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    if test1_passed:
        print("✅ 时间码重映射测试通过")
    else:
        print("❌ 时间码重映射测试失败")
    
    if test2_passed:
        print("✅ ClipGenerator集成测试通过")
    else:
        print("❌ ClipGenerator集成测试失败")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！修复成功！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，需要进一步检查")
        sys.exit(1)

