#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立的剧本工程师测试脚本
避开循环导入问题
"""

import os
import sys
import logging
import re
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("screenplay_test")

# 测试文件路径
ZH_TEST_SRT = "tests/golden_samples/zh/1_20250317_203031.srt"
OUTPUT_DIR = "screenplay_output"
OUTPUT_SRT = os.path.join(OUTPUT_DIR, "generated.srt")


def parse_srt(srt_path):
    """解析SRT字幕文件"""
    logger.info(f"解析SRT文件: {srt_path}")
    
    # SRT时间码格式的正则表达式
    timestamp_pattern = re.compile(
        r'(\\\1{2}):(\\\1{2}):(\\\1{2}),(\\\1{3})\\\1+-->\\\1+(\\\1{2}):(\\\1{2}):(\\\1{2}),(\\\1{3})(?:\\\1+.*?)?$'
    )
    
    # 检查文件存在
    if not os.path.exists(srt_path):
        logger.error(f"SRT文件不存在: {srt_path}")
        return None
    
    subtitles = []
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按空行分割字幕块
        blocks = re.split(r'\n\\\1*\n', content.strip())
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            # 提取索引
            try:
                index = int(lines[0].strip())
            except ValueError:
                index = i + 1
            
            # 提取时间戳
            timestamp_match = None
            for j, line in enumerate(lines):
                match = timestamp_pattern.match(line.strip())
                if match:
                    timestamp_match = match
                    content_start_index = j + 1
                    break
            
            if not timestamp_match:
                continue
            
            # 解析时间戳
            start_time = (
                int(timestamp_match.group(1)) * 3600 +  # 小时
                int(timestamp_match.group(2)) * 60 +    # 分钟
                int(timestamp_match.group(3)) +         # 秒
                int(timestamp_match.group(4)) / 1000    # 毫秒
            )
            
            end_time = (
                int(timestamp_match.group(5)) * 3600 +  # 小时
                int(timestamp_match.group(6)) * 60 +    # 分钟
                int(timestamp_match.group(7)) +         # 秒
                int(timestamp_match.group(8)) / 1000    # 毫秒
            )
            
            # 提取字幕内容
            content = '\n'.join(lines[content_start_index:]).strip()
            
            # 添加到字幕列表
            subtitles.append({
                "id": index,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "text": content
            })
        
        logger.info(f"成功解析字幕，共 {len(subtitles)} 条")
        return subtitles
        
    except Exception as e:
        logger.error(f"解析SRT文件失败: {str(e)}")
        return None


def generate_screenplay(subtitles, language="zh", preset_name="默认"):
    """生成混剪剧本"""
    logger.info(f"开始生成剧本，语言: {language}, 预设: {preset_name}")
    
    # 这里模拟剧本生成，实际项目中会调用大模型
    # 在这个测试中，我们将使用跳段选择策略来模拟大模型的行为
    
    # 定义预设
    presets = {
        "默认": {"interval": 3, "min_duration": 0.5},
        "快节奏": {"interval": 2, "min_duration": 0.3},
        "情感化": {"interval": 4, "min_duration": 1.0},
        "冲突型": {"interval": 1, "min_duration": 0.8}
    }
    
    preset = presets.get(preset_name, presets["默认"])
    interval = preset["interval"]
    min_duration = preset["min_duration"]
    
    # 选择字幕
    selected_subtitles = []
    for i in range(0, len(subtitles), interval):
        subtitle = subtitles[i]
        if subtitle["duration"] >= min_duration:
            selected_subtitles.append(subtitle)
    
    # 模拟些微变化，使片段看起来更像是被大模型重新组织过
    for i, subtitle in enumerate(selected_subtitles):
        # 模拟加入一些情感标记
        emotion_tags = ["[激动]", "[疑惑]", "[高兴]", "[悲伤]", "[愤怒]"]
        if i % 5 == 0:
            subtitle["text"] = f"{emotion_tags[i % len(emotion_tags)]} {subtitle['text']}"
    
    logger.info(f"成功生成剧本，共 {len(selected_subtitles)} 条")
    
    return {
        "status": "success",
        "screenplay": selected_subtitles,
        "total_segments": len(selected_subtitles),
        "language": language,
        "preset": preset_name
    }


def format_timecode(seconds):
    """将秒数格式化为SRT时间码格式 (00:00:00,000)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def export_srt(subtitles, output_path):
    """导出SRT字幕文件"""
    logger.info(f"导出SRT文件: {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, subtitle in enumerate(subtitles):
                index = i + 1
                start_time = format_timecode(subtitle["start_time"])
                end_time = format_timecode(subtitle["end_time"])
                text = subtitle["text"]
                
                f.write(f"{index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        logger.info(f"成功导出SRT文件: {output_path}")
        return True
    except Exception as e:
        logger.error(f"导出SRT文件失败: {str(e)}")
        return False


def main():
    """主函数"""
    logger.info("开始独立剧本工程师测试")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 解析原始字幕
    subtitles = parse_srt(ZH_TEST_SRT)
    if not subtitles:
        logger.error("解析字幕失败，无法继续测试")
        return 1
    
    # 生成剧本
    result = generate_screenplay(subtitles, language="zh", preset_name="默认")
    if "error" in result:
        logger.error(f"生成剧本失败: {result['error']}")
        return 1
    
    # 导出新字幕
    if not export_srt(result["screenplay"], OUTPUT_SRT):
        logger.error("导出新字幕失败")
        return 1
    
    # 保存结果元数据
    metadata_path = os.path.join(OUTPUT_DIR, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump({
            "original_subtitles": len(subtitles),
            "selected_subtitles": len(result["screenplay"]),
            "language": result["language"],
            "preset": result["preset"]
        }, f, indent=2)
    
    logger.info(f"已保存元数据: {metadata_path}")
    logger.info(f"剧本测试完成")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 