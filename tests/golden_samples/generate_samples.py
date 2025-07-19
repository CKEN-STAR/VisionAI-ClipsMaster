#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
黄金样本生成脚本

此脚本用于生成标准黄金样本，用于系统性能和质量评估。
黄金样本覆盖基础场景、复杂场景和边缘情况，以确保系统在各种情况下的鲁棒性。
"""

import os
import sys
import json
import shutil
import hashlib
import datetime
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 导入项目模块
try:
    from src.utils.file_handler import ensure_dir
    from src.utils.video_processor import get_video_info
    from src.utils.subtitle_parser import parse_subtitle
except ImportError:
    # 在导入失败的情况下，提供基本实现
    def ensure_dir(path):
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)
        
    def get_video_info(video_path):
        """获取视频信息"""
        # 简化实现，返回基本信息
        return {"duration": 0, "width": 0, "height": 0}
    
    def parse_subtitle(subtitle_path):
        """解析字幕文件"""
        # 简化实现，返回空列表
        return []

# 黄金样本库目录
GOLDEN_SAMPLES_DIR = project_root / "tests" / "golden_samples"
ZH_SAMPLES_DIR = GOLDEN_SAMPLES_DIR / "zh"
EN_SAMPLES_DIR = GOLDEN_SAMPLES_DIR / "en"
RESOURCES_DIR = project_root / "tests" / "resources"
FFMPEG_PATH = shutil.which("ffmpeg")

def create_golden_samples():
    """生成标准黄金样本库"""
    print("正在创建标准黄金样本库...")
    
    # 确保目录存在
    ensure_dir(GOLDEN_SAMPLES_DIR)
    ensure_dir(ZH_SAMPLES_DIR)
    ensure_dir(EN_SAMPLES_DIR)
    ensure_dir(RESOURCES_DIR)
    
    # 定义黄金样本
    samples = [
        {"name": "base_30s", "duration": 30, "lang": "zh", "type": "剧情混剪"},
        {"name": "complex_1m", "duration": 60, "lang": "en", "type": "多场景切换"},
        {"name": "edge_5s", "duration": 5, "lang": "zh", "type": "超短视频"}
    ]
    
    # 添加更多样本以覆盖更多场景
    extended_samples = [
        {"name": "dialog_heavy", "duration": 45, "lang": "zh", "type": "对白密集型"},
        {"name": "multi_speaker", "duration": 40, "lang": "en", "type": "多人对话"},
        {"name": "action_scene", "duration": 25, "lang": "zh", "type": "动作场景"},
        {"name": "narrative", "duration": 35, "lang": "en", "type": "旁白主导"},
        {"name": "special_chars", "duration": 20, "lang": "zh", "type": "特殊字符"},
        {"name": "empty_segments", "duration": 15, "lang": "en", "type": "空白片段"}
    ]
    
    samples.extend(extended_samples)
    
    # 遍历生成样本
    for sample in samples:
        print(f"处理样本: {sample['name']} ({sample['lang']})")
        
        # 基于样本信息生成样本文件
        sample_files = render_sample(sample)
        
        # 计算样本哈希值用于验证
        if sample_files:
            for file_path in sample_files:
                hash_value = calculate_hash(file_path)
                print(f"  - {os.path.basename(file_path)}: {hash_value}")
    
    # 保存样本元数据
    save_sample_metadata(samples)
    
    print("黄金样本库创建完成")
    return samples

def render_sample(sample: Dict[str, Any]) -> List[str]:
    """
    根据样本信息渲染样本文件
    
    Args:
        sample: 样本信息
        
    Returns:
        List[str]: 生成的样本文件路径列表
    """
    # 确定样本目录
    sample_dir = ZH_SAMPLES_DIR if sample["lang"] == "zh" else EN_SAMPLES_DIR
    
    # 视频文件路径
    video_path = sample_dir / f"{sample['name']}.mp4"
    srt_path = sample_dir / f"{sample['name']}.srt"
    
    # 生成测试视频
    if not os.path.exists(video_path):
        generate_test_video(video_path, sample["duration"], sample["type"])
    
    # 生成测试字幕
    if not os.path.exists(srt_path):
        generate_test_subtitles(srt_path, sample["duration"], sample["type"], sample["lang"])
    
    return [str(video_path), str(srt_path)]

def generate_test_video(output_path: Path, duration: int, content_type: str) -> bool:
    """
    生成测试视频
    
    Args:
        output_path: 输出路径
        duration: 视频时长(秒)
        content_type: 内容类型
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    print(f"  生成测试视频: {output_path}")
    
    # 确保目录存在
    ensure_dir(output_path.parent)
    
    # 检查ffmpeg是否可用
    if not FFMPEG_PATH:
        # 如果ffmpeg不可用，创建占位视频文件
        print("  警告: ffmpeg未安装，创建占位视频文件")
        with open(output_path, 'wb') as f:
            # 写入一个简单的文件头，表示这是测试文件
            f.write(b'TEST_VIDEO_' + content_type.encode() + b'_' + str(duration).encode())
        return True
    
    try:
        # 基于内容类型调整视频生成参数
        if content_type == "剧情混剪" or content_type == "多场景切换":
            # 使用测试源生成带场景变化的视频
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", 
                "-i", f"testsrc=duration={duration}:size=1280x720:rate=30",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264", 
                str(output_path)
            ]
        elif content_type == "超短视频":
            # 使用简单纯色背景
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", 
                "-i", f"color=c=blue:duration={duration}:size=640x480:rate=30",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264", 
                str(output_path)
            ]
        elif content_type == "动作场景":
            # 使用噪点生成更复杂的纹理
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi",
                "-i", f"nullsrc=size=1280x720:duration={duration},geq=random(1)*255:128:128",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                str(output_path)
            ]
        else:
            # 默认测试源
            cmd = [
                FFMPEG_PATH, "-y",
                "-f", "lavfi", 
                "-i", f"testsrc=duration={duration}:size=1280x720:rate=30",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264", 
                str(output_path)
            ]
        
        # 执行命令
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return os.path.exists(output_path)
    
    except Exception as e:
        print(f"  生成测试视频失败: {str(e)}")
        return False

def generate_test_subtitles(output_path: Path, duration: int, content_type: str, lang: str) -> bool:
    """
    生成测试字幕
    
    Args:
        output_path: 输出路径
        duration: 字幕对应视频时长(秒)
        content_type: 内容类型
        lang: 语言代码 (zh/en)
        
    Returns:
        bool: 成功返回True，失败返回False
    """
    print(f"  生成测试字幕: {output_path}")
    
    # 确保目录存在
    ensure_dir(output_path.parent)
    
    try:
        # 基于内容类型和语言生成字幕
        subtitles = []
        
        if lang == "zh":
            if content_type == "剧情混剪":
                subtitles = generate_zh_narrative_subtitles(duration)
            elif content_type == "超短视频":
                subtitles = generate_zh_short_subtitles(duration)
            elif content_type == "对白密集型":
                subtitles = generate_zh_dialog_subtitles(duration)
            elif content_type == "动作场景":
                subtitles = generate_zh_action_subtitles(duration)
            elif content_type == "特殊字符":
                subtitles = generate_special_chars_subtitles(duration, lang)
            else:
                subtitles = generate_default_subtitles(duration, lang)
        else:  # en
            if content_type == "多场景切换":
                subtitles = generate_en_complex_subtitles(duration)
            elif content_type == "多人对话":
                subtitles = generate_en_multi_speaker_subtitles(duration)
            elif content_type == "旁白主导":
                subtitles = generate_en_narrative_subtitles(duration)
            elif content_type == "空白片段":
                subtitles = generate_empty_segment_subtitles(duration, lang)
            else:
                subtitles = generate_default_subtitles(duration, lang)
        
        # 写入SRT文件
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles, 1):
                f.write(f"{i}\n")
                f.write(f"{format_timestamp(sub['start'])} --> {format_timestamp(sub['end'])}\n")
                f.write(f"{sub['text']}\n\n")
        
        return os.path.exists(output_path)
    
    except Exception as e:
        print(f"  生成测试字幕失败: {str(e)}")
        return False

def format_timestamp(seconds: float) -> str:
    """
    将秒数格式化为SRT时间戳
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间戳
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def generate_zh_narrative_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成中文叙事字幕"""
    # 每段字幕约3秒
    segments = duration // 3
    subtitles = []
    
    narrative_texts = [
        "明月微光，照亮小镇的街道。",
        "老街上行人渐稀，唯有他独自伫立。",
        "窗台上的花已凋零，书页被风轻轻翻动。",
        "时光从指尖悄然滑落，如水般流走。",
        "他回首望去，却已不见昔日那个人影。",
        "晨曦微露，又是新的一天开始。",
        "远山含黛，云雾缭绕。",
        "春风拂过树梢，嫩芽探出新绿。",
        "湖水微波荡漾，倒映着蓝天白云。",
        "小路蜿蜒向前，不知通往何方。"
    ]
    
    start_time = 0
    for i in range(min(segments, len(narrative_texts))):
        end_time = start_time + 3.0
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": narrative_texts[i % len(narrative_texts)]
        })
        start_time = end_time
    
    return subtitles

def generate_zh_short_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成超短中文字幕"""
    subtitles = []
    
    if duration <= 5:
        subtitles.append({
            "start": 0.0,
            "end": duration,
            "text": "珍惜当下，把握瞬间。"
        })
    else:
        subtitles.append({
            "start": 0.0,
            "end": duration / 2,
            "text": "珍惜当下，把握瞬间。"
        })
        subtitles.append({
            "start": duration / 2,
            "end": duration,
            "text": "生活如此短暂，却又如此美好。"
        })
    
    return subtitles

def generate_zh_dialog_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成中文对白密集型字幕"""
    subtitles = []
    
    dialogs = [
        "李明：你好，好久不见了。",
        "王芳：是啊，有一年多了吧？",
        "李明：时间过得真快，你最近怎么样？",
        "王芳：还不错，刚换了新工作。",
        "李明：恭喜啊，在哪个公司？",
        "王芳：在一家科技公司，做产品经理。",
        "李明：听起来不错，工作顺利吗？",
        "王芳：刚开始有点忙，不过慢慢适应了。",
        "李明：那就好，有时间一起聚聚吧。",
        "王芳：好啊，找个周末约起来。",
        "李明：记得叫上老张，他也想见见大家。",
        "王芳：没问题，我会联系他的。"
    ]
    
    # 每段对白约2.5秒
    segment_duration = 2.5
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(dialogs))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": dialogs[i % len(dialogs)]
        })
        start_time = end_time
    
    return subtitles

def generate_zh_action_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成中文动作场景字幕"""
    subtitles = []
    
    actions = [
        "【急促的脚步声】",
        "【玻璃碎裂声】",
        "男主角：小心背后！",
        "【枪声】",
        "女主角：这边走！快！",
        "【汽车引擎轰鸣】",
        "男配角：他们追上来了！",
        "【急刹车声】",
        "男主角：跳！现在！",
        "【爆炸声】"
    ]
    
    # 每段动作约2秒
    segment_duration = 2.0
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(actions))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": actions[i % len(actions)]
        })
        start_time = end_time
    
    return subtitles

def generate_en_complex_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成英文复杂场景字幕"""
    subtitles = []
    
    scenes = [
        "NARRATOR: In the heart of the city...",
        "JOHN: I've been waiting for this moment.",
        "[Flashback - 5 years earlier]",
        "YOUNG JOHN: I'll come back for you, I promise.",
        "MARY: You never should have left.",
        "[Present day]",
        "JOHN: Things have changed. I've changed.",
        "NARRATOR: But some promises are meant to be broken.",
        "[Phone ringing]",
        "JOHN: Hello? No, that's impossible...",
        "[Scene shifts to airport]",
        "AIRPORT ANNOUNCER: Flight 247 to London is now boarding.",
        "MARY: You're leaving again, aren't you?",
        "JOHN: This time it's different."
    ]
    
    # 每个场景约4秒
    segment_duration = 4.0
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(scenes))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": scenes[i % len(scenes)]
        })
        start_time = end_time
    
    return subtitles

def generate_en_multi_speaker_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成英文多人对话字幕"""
    subtitles = []
    
    conversation = [
        "DAVID: Has anyone seen the report I left on the table?",
        "SARAH: Which report? The quarterly analysis?",
        "MICHAEL: I put it in your inbox this morning.",
        "DAVID: No, I'm talking about the client proposal.",
        "EMMA: Oh, I think Jennifer took it for review.",
        "JENNIFER: Yes, I have it. Give me 10 minutes to finish reading it.",
        "DAVID: Great, we need to discuss it before the meeting.",
        "MICHAEL: What time is the client coming in?",
        "SARAH: They'll be here at 2:30. Conference room A.",
        "EMMA: Should I order lunch for everyone?",
        "DAVID: Yes, please. Something light.",
        "JENNIFER: No seafood for me, remember?",
        "MICHAEL: And I'm vegetarian this month.",
        "EMMA: Got it. I'll take care of it."
    ]
    
    # 每句对话约3秒
    segment_duration = 3.0
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(conversation))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": conversation[i % len(conversation)]
        })
        start_time = end_time
    
    return subtitles

def generate_en_narrative_subtitles(duration: int) -> List[Dict[str, Any]]:
    """生成英文旁白主导字幕"""
    subtitles = []
    
    narration = [
        "In the beginning, there was darkness.",
        "Mankind has always been fascinated by the unknown.",
        "The journey began centuries ago, when explorers first looked to the stars.",
        "Through triumph and tragedy, we persevered.",
        "Science became our guiding light in an endless void.",
        "Each discovery brought new questions, new mysteries to solve.",
        "In the face of impossibility, human ingenuity prevailed.",
        "What once seemed like fantasy slowly became reality.",
        "And yet, the greatest discoveries still await us.",
        "Beyond our atmosphere, beyond our solar system.",
        "The universe beckons, whispering secrets we have yet to comprehend."
    ]
    
    # 每段旁白约3.5秒
    segment_duration = 3.5
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(narration))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": narration[i % len(narration)]
        })
        start_time = end_time
    
    return subtitles

def generate_special_chars_subtitles(duration: int, lang: str) -> List[Dict[str, Any]]:
    """生成包含特殊字符的字幕"""
    subtitles = []
    
    if lang == "zh":
        special_texts = [
            "测试特殊符号：@#¥%…&*（）——+",
            "表情符号测试：😊😂🤔💯❤️👍",
            "混合字符：中文English数字123",
            "标点符号：，。？！；：""''",
            "特殊文本：【加粗】［斜体］「引用」",
            "数学符号：∑∏√∂∞≈≠≤≥÷×",
            "箭头符号：↑↓←→↔↕↖↗↘↙",
            "括号嵌套：（这是{嵌套[括号]测试}）"
        ]
    else:  # en
        special_texts = [
            "Special characters: @#$%^&*()_+",
            "Emoji test: 😊😂🤔💯❤️👍",
            "Mixed text: English中文Numbers123",
            "Punctuation: ,.?!;:\"'",
            "Formatting: [Bold] {Italic} 'Quote'",
            "Math symbols: ∑∏√∂∞≈≠≤≥÷×",
            "Arrows: ↑↓←→↔↕↖↗↘↙",
            "Nested brackets: (This is {nested [bracket] test})"
        ]
    
    # 每段约3秒
    segment_duration = 3.0
    start_time = 0
    
    for i in range(min(int(duration / segment_duration), len(special_texts))):
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": special_texts[i % len(special_texts)]
        })
        start_time = end_time
    
    return subtitles

def generate_empty_segment_subtitles(duration: int, lang: str) -> List[Dict[str, Any]]:
    """生成包含空白片段的字幕"""
    subtitles = []
    
    # 创建有空白间隙的字幕
    if lang == "zh":
        texts = ["开始说话", "这是第二句话", "这中间会有一段空白", "现在继续说话", "结束"]
    else:  # en
        texts = ["Starting to speak", "This is the second line", "There will be a gap", "Now continuing", "The end"]
    
    # 设置时间点，确保中间有空白
    time_points = [0, 3, 6, 10, 13, 15]  # 注意10和6之间有4秒空白
    
    for i in range(len(texts)):
        subtitles.append({
            "start": time_points[i],
            "end": time_points[i+1],
            "text": texts[i]
        })
    
    return subtitles

def generate_default_subtitles(duration: int, lang: str) -> List[Dict[str, Any]]:
    """生成默认字幕"""
    subtitles = []
    
    if lang == "zh":
        default_texts = [
            "这是默认的测试字幕。",
            "用于验证基本字幕功能。",
            "包含多行测试内容。",
            "感谢使用VisionAI-ClipsMaster。"
        ]
    else:  # en
        default_texts = [
            "This is a default test subtitle.",
            "Used to verify basic subtitle functionality.",
            "Contains multiple lines of test content.",
            "Thank you for using VisionAI-ClipsMaster."
        ]
    
    # 平均分配时间
    segment_duration = duration / len(default_texts)
    start_time = 0
    
    for text in default_texts:
        end_time = start_time + segment_duration
        subtitles.append({
            "start": start_time,
            "end": end_time,
            "text": text
        })
        start_time = end_time
    
    return subtitles

def calculate_hash(file_path: str) -> str:
    """
    计算文件的SHA-256哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 哈希值字符串
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"  计算哈希值失败: {str(e)}")
        return "hash_calculation_failed"

def calculate_video_hash(file_path: str) -> str:
    """
    计算视频文件的哈希值 - 使用帧采样方法降低计算量
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        str: 哈希值字符串
    """
    try:
        import cv2
        import numpy as np
        
        # 打开视频文件
        cap = cv2.VideoCapture(file_path)
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # 每秒采样一帧
        sample_rate = max(1, int(fps))
        frames_to_sample = min(30, int(duration))  # 最多采样30帧
        
        hasher = hashlib.sha256()
        
        # 均匀采样帧
        for i in range(frames_to_sample):
            # 计算帧位置
            frame_pos = int((i / frames_to_sample) * frame_count)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            # 读取帧
            ret, frame = cap.read()
            if ret:
                # 将帧调整为统一大小以确保一致性
                frame = cv2.resize(frame, (320, 240))
                
                # 更新哈希
                hasher.update(frame.tobytes())
        
        # 释放视频文件
        cap.release()
        
        return hasher.hexdigest()
    except Exception as e:
        print(f"  计算视频哈希值失败: {str(e)}")
        # 如果视频处理失败，回退到普通文件哈希
        return calculate_hash(file_path)

def calculate_xml_hash(file_path: str) -> str:
    """
    计算XML文件的哈希值 - 忽略空白字符和时间戳等变动元素
    
    Args:
        file_path: XML文件路径
        
    Returns:
        str: 哈希值字符串
    """
    try:
        import re
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除空白字符
        content = re.sub(r'\s+', '', content)
        
        # 移除版本标记和时间戳
        content = re.sub(r'<timestamp>[^<]+</timestamp>', '<timestamp></timestamp>', content)
        content = re.sub(r'<created_at>[^<]+</created_at>', '<created_at></created_at>', content)
        
        # 计算哈希
        hasher = hashlib.sha256()
        hasher.update(content.encode('utf-8'))
        
        return hasher.hexdigest()
    
    except Exception as e:
        print(f"  计算XML哈希值失败: {str(e)}")
        # 如果XML处理失败，回退到普通文件哈希
        return calculate_hash(file_path)

def save_sample_metadata(samples: List[Dict[str, Any]]) -> None:
    """
    保存样本元数据到JSON文件
    
    Args:
        samples: 样本列表
    """
    metadata_path = GOLDEN_SAMPLES_DIR / "metadata.json"
    
    # 为每个样本添加额外信息
    for sample in samples:
        # 确定样本目录
        sample_dir = ZH_SAMPLES_DIR if sample["lang"] == "zh" else EN_SAMPLES_DIR
        
        # 视频文件路径
        video_path = sample_dir / f"{sample['name']}.mp4"
        srt_path = sample_dir / f"{sample['name']}.srt"
        
        # 添加文件哈希值和路径
        if os.path.exists(video_path):
            sample["video_path"] = str(video_path.relative_to(project_root))
            sample["video_hash"] = calculate_video_hash(str(video_path))
        
        if os.path.exists(srt_path):
            sample["srt_path"] = str(srt_path.relative_to(project_root))
            sample["srt_hash"] = calculate_hash(str(srt_path))
    
    # 添加元数据
    metadata = {
        "version": "1.0",
        "created_at": datetime.datetime.now().isoformat(),
        "samples_count": len(samples),
        "samples": samples
    }
    
    # 写入JSON文件
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"样本元数据已保存到: {metadata_path}")

def get_scene_types() -> List[str]:
    """获取支持的场景类型列表
    
    Returns:
        List[str]: 场景类型列表
    """
    return [
        "action",     # 动作
        "comedy",     # 喜剧
        "drama",      # 剧情
        "family",     # 家庭
        "historical", # 历史
        "romance",    # 爱情
        "sci-fi",     # 科幻
        "thriller",   # 惊悚
        "wuxia",      # 武侠
        "youth"       # 青春
    ]

def create_golden_sample(version: str) -> Dict[str, Dict[str, str]]:
    """创建特定版本的黄金样本
    
    Args:
        version: 版本标识，如 "1.0.0"
        
    Returns:
        Dict: 哈希值字典 {"video": {样本名: 哈希值}, "xml": {样本名: 哈希值}}
    """
    print(f"正在创建版本 {version} 的黄金样本...")
    
    # 创建输出目录
    version_dir = GOLDEN_SAMPLES_DIR / "output" / version
    ensure_dir(version_dir)
    
    # 获取场景类型
    scene_types = get_scene_types()
    
    # 哈希值字典
    hashes = {"video": {}, "xml": {}}
    
    # 为每种场景类型创建样本
    for scene_type in scene_types:
        sample_id = f"golden_sample_{scene_type}_{version.replace('.', '_')}"
        video_path = version_dir / f"{sample_id}.mp4"
        srt_path = version_dir / f"{sample_id}.srt"
        xml_path = version_dir / f"{sample_id}.mp4.xml"
        
        # 生成测试视频
        generate_test_video(video_path, 30, scene_type)
        
        # 生成测试字幕
        generate_test_subtitles(srt_path, 30, scene_type, "zh")
        
        # 生成XML配置
        generate_xml_config(xml_path, scene_type, sample_id)
        
        # 计算哈希值
        video_hash = calculate_video_hash(str(video_path))
        xml_hash = calculate_xml_hash(str(xml_path))
        
        hashes["video"][sample_id] = video_hash
        hashes["xml"][sample_id] = xml_hash
        
        print(f"  已创建样本: {sample_id}")
    
    # 保存哈希信息
    hash_dir = GOLDEN_SAMPLES_DIR / "hashes"
    ensure_dir(hash_dir)
    hash_file = hash_dir / f"golden_hash_{version}.json"
    
    with open(hash_file, 'w', encoding='utf-8') as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)
    
    print(f"黄金样本版本 {version} 创建完成")
    return hashes

def update_golden_samples_index():
    """更新黄金样本索引文件"""
    index_path = GOLDEN_SAMPLES_DIR / "index.json"
    
    # 初始化索引
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
    else:
        index_data = {
            "last_updated": datetime.datetime.now().isoformat(),
            "versions": {},
            "samples": {}
        }
    
    # 扫描输出目录
    output_dir = GOLDEN_SAMPLES_DIR / "output"
    ensure_dir(output_dir)
    
    for version_dir in output_dir.iterdir():
        if version_dir.is_dir():
            version = version_dir.name
            
            # 收集版本中的样本
            samples = []
            for video_file in version_dir.glob("*.mp4"):
                sample_id = video_file.stem
                samples.append(sample_id)
                
                # 添加样本信息
                if sample_id not in index_data.get("samples", {}):
                    # 从ID中提取场景类型
                    if "_" in sample_id:
                        scene_type = sample_id.split("_")[2]  # golden_sample_TYPE_...
                    else:
                        scene_type = "unknown"
                    
                    # 添加样本信息
                    index_data.setdefault("samples", {})[sample_id] = {
                        "id": sample_id,
                        "type": scene_type,
                        "files": {
                            "video": str(video_file.relative_to(project_root)),
                            "xml": str((video_file.parent / f"{sample_id}.mp4.xml").relative_to(project_root)),
                            "srt": str((video_file.parent / f"{sample_id}.srt").relative_to(project_root))
                        }
                    }
            
            # 添加版本信息
            if samples and version not in index_data.get("versions", {}):
                # 创建示例哈希值
                video_hash = "PLACEHOLDER"
                xml_hash = "PLACEHOLDER"
                
                # 查找哈希文件
                hash_file = GOLDEN_SAMPLES_DIR / "hashes" / f"golden_hash_{version}.json"
                if os.path.exists(hash_file):
                    with open(hash_file, 'r', encoding='utf-8') as f:
                        try:
                            hash_data = json.load(f)
                            # 使用第一个样本的哈希值作为版本哈希
                            if samples and samples[0] in hash_data.get("video", {}):
                                video_hash = hash_data["video"][samples[0]]
                            if samples and samples[0] in hash_data.get("xml", {}):
                                xml_hash = hash_data["xml"][samples[0]]
                        except:
                            pass
                
                # 添加版本信息
                index_data.setdefault("versions", {})[version] = {
                    "path": str(version_dir.relative_to(project_root)),
                    "samples": samples,
                    "hashes": {
                        "video": video_hash,
                        "xml": xml_hash
                    }
                }
    
    # 更新时间戳
    index_data["last_updated"] = datetime.datetime.now().isoformat()
    
    # 保存索引
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"黄金样本索引已更新: {index_path}")

def generate_xml_config(xml_path: Path, scene_type: str, sample_id: str) -> bool:
    """生成XML配置文件
    
    Args:
        xml_path: XML文件路径
        scene_type: 场景类型
        sample_id: 样本ID
        
    Returns:
        bool: 生成是否成功
    """
    print(f"  生成XML配置: {xml_path}")
    
    try:
        # 创建基本XML结构
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project version="1.0">
    <info>
        <name>Golden Sample - {scene_type}</name>
        <type>{scene_type}</type>
        <duration>30.0</duration>
        <resolution>1280x720</resolution>
        <framerate>30</framerate>
        <description>This is a golden standard sample for {scene_type} scene type.</description>
        <created_by>VisionAI-ClipsMaster</created_by>
        <sample_id>{sample_id}</sample_id>
    </info>
    
    <timeline>
        <track type="video">
            <clip start="0" end="30" source="{sample_id}.mp4">
                <effects>
                    <effect type="color_grading" preset="standard"/>
                </effects>
            </clip>
        </track>
        
        <track type="subtitle">
            <clip start="0" end="30" source="{sample_id}.srt">
                <settings>
                    <font>Arial</font>
                    <size>42</size>
                    <color>#FFFFFF</color>
                    <background>#80000000</background>
                    <position>bottom_center</position>
                </settings>
            </clip>
        </track>
    </timeline>
    
    <metadata>
        <golden_standard>true</golden_standard>
        <test_purpose>quality_comparison</test_purpose>
        <category>{scene_type}</category>
        <tags>golden_sample, {scene_type}, test, benchmark</tags>
    </metadata>
</project>
"""
        
        # 确保目录存在
        os.makedirs(os.path.dirname(xml_path), exist_ok=True)
        
        # 写入XML文件
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return os.path.exists(xml_path)
    
    except Exception as e:
        print(f"  生成XML配置失败: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="黄金样本生成工具")
    parser.add_argument("--force", action="store_true", help="强制重新生成所有样本")
    args = parser.parse_args()
    
    # 如果需要强制重新生成
    if args.force:
        # 清理现有样本
        if os.path.exists(ZH_SAMPLES_DIR):
            shutil.rmtree(ZH_SAMPLES_DIR)
        if os.path.exists(EN_SAMPLES_DIR):
            shutil.rmtree(EN_SAMPLES_DIR)
    
    # 生成样本
    create_golden_samples() 