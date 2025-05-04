#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时预览模块演示

演示如何使用实时预览模块生成各种可视化，包括轨道对齐前后比较。
"""

import os
import sys
import logging
from typing import Dict, List, Any
import webbrowser
from datetime import datetime

# 设置日志格式，确保捕获所有信息
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("实时预览演示")

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
logger.debug(f"当前目录: {current_dir}")
logger.debug(f"父目录: {parent_dir}")
logger.debug(f"Python路径: {sys.path}")

try:
    # 导入预览模块
    from timecode.live_preview import (
        PreviewGenerator,
        generate_timeline_preview,
        generate_tracks_preview,
        generate_alignment_comparison
    )
    logger.debug("预览模块导入成功")

    # 导入多轨对齐模块
    from timecode.multi_track_align import (
        MultiTrackAligner,
        align_audio_video,
        align_multiple_tracks
    )
    logger.debug("多轨对齐模块导入成功")
except ImportError as e:
    logger.error(f"导入模块失败: {str(e)}")
    raise

def save_and_open_html(html_content: str, file_name: str) -> None:
    """保存HTML内容到文件并打开浏览器查看
    
    Args:
        html_content: HTML内容
        file_name: 保存的文件名
    """
    logger.info(f"保存HTML内容，长度: {len(html_content)}")
    
    # 创建当前目录下的output文件夹
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    
    # 完整的HTML页面
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VisionAI-ClipsMaster 实时预览</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #444; }}
            .container {{ margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <h1>VisionAI-ClipsMaster 实时预览</h1>
        <div class="container">
            {html_content}
        </div>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    
    # 保存文件
    file_path = os.path.join(output_dir, file_name)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        logger.info(f"预览已保存至: {file_path}")
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 在浏览器中打开
    try:
        webbrowser.open(f"file://{os.path.abspath(file_path)}")
        logger.info("已在浏览器中打开预览")
    except Exception as e:
        logger.error(f"无法打开浏览器: {e}")

def demo_scene_timeline():
    """演示场景时间轴预览"""
    logger.info("=== 场景时间轴预览演示 ===")
    
    # 创建测试场景数据
    scenes = [
        {"start": 0, "end": 20, "emotion_score": 0.5, "sentiment": "neutral", "tags": ["开场"]},
        {"start": 20, "end": 35, "emotion_score": 0.7, "sentiment": "positive", "tags": ["介绍"]},
        {"start": 35, "end": 60, "emotion_score": 0.4, "sentiment": "neutral", "tags": ["过渡"]},
        {"start": 60, "end": 80, "emotion_score": 0.9, "sentiment": "positive", "scene_type": "climax", "tags": ["高潮"]},
        {"start": 80, "end": 100, "emotion_score": 0.3, "sentiment": "negative", "tags": ["结束"]}
    ]
    
    # 生成预览
    logger.info("生成场景时间轴预览...")
    try:
        preview_gen = PreviewGenerator({
            "width": 12,
            "height": 5,
            "emotion_scale": 12,
            "font_size": 12
        })
        
        logger.debug("预览生成器创建成功，开始生成波形图...")
        timeline_html = preview_gen.generate_waveform(scenes)
        logger.info(f"生成的HTML内容长度: {len(timeline_html)}")
        
        # 保存并打开预览
        save_and_open_html(timeline_html, "scene_timeline_preview.html")
        logger.info("场景时间轴预览演示完成")
    except Exception as e:
        logger.error(f"场景时间轴预览生成失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def demo_multi_track():
    """演示多轨道预览"""
    logger.info("=== 多轨道预览演示 ===")
    
    # 创建测试轨道数据
    tracks = {
        "主视频": {
            "type": "video",
            "duration": 100.0,
            "scenes": [
                {"start_time": 0, "end_time": 25, "description": "开场"},
                {"start_time": 25, "end_time": 60, "description": "中间部分"},
                {"start_time": 60, "end_time": 100, "description": "结尾"}
            ]
        },
        "主音频": {
            "type": "audio",
            "duration": 105.0
        },
        "背景音乐": {
            "type": "audio",
            "duration": 120.0
        },
        "字幕": {
            "type": "subtitle",
            "duration": 95.0
        },
        "特效": {
            "type": "effects",
            "duration": 90.0
        }
    }
    
    # 生成预览
    logger.info("生成多轨道预览...")
    try:
        tracks_html = generate_tracks_preview(tracks)
        logger.info(f"生成的HTML内容长度: {len(tracks_html)}")
        
        # 保存并打开预览
        save_and_open_html(tracks_html, "multi_track_preview.html")
        logger.info("多轨道预览演示完成")
    except Exception as e:
        logger.error(f"多轨道预览生成失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def demo_alignment_comparison():
    """演示对齐前后比较"""
    logger.info("=== 对齐前后比较演示 ===")
    
    # 创建测试轨道数据
    before_tracks = {
        "主视频": {
            "type": "video",
            "duration": 100.0,
            "scenes": [
                {"start_time": 0, "end_time": 25},
                {"start_time": 25, "end_time": 60},
                {"start_time": 60, "end_time": 100}
            ]
        },
        "主音频": {
            "type": "audio",
            "duration": 105.0
        },
        "字幕": {
            "type": "subtitle",
            "duration": 95.0
        }
    }
    
    # 创建对齐器
    logger.info("对齐轨道中...")
    try:
        aligner = MultiTrackAligner()
        after_tracks = aligner.align_tracks(before_tracks)
        
        # 生成对齐前后比较预览
        logger.info("生成对齐前后比较预览...")
        comparison_html = generate_alignment_comparison(before_tracks, after_tracks)
        logger.info(f"生成的HTML内容长度: {len(comparison_html)}")
        
        # 保存并打开预览
        save_and_open_html(comparison_html, "alignment_comparison_preview.html")
        logger.info("对齐前后比较演示完成")
    except Exception as e:
        logger.error(f"对齐前后比较生成失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def demo_progressive_alignment():
    """演示渐进式对齐"""
    logger.info("=== 渐进式对齐演示 ===")
    
    # 创建测试轨道数据
    tracks = [
        {"id": "视频1", "type": "video", "duration": 90.0},
        {"id": "视频2", "type": "video", "duration": 100.0},
        {"id": "音频1", "type": "audio", "duration": 95.0},
        {"id": "音频2", "type": "audio", "duration": 105.0},
        {"id": "字幕", "type": "subtitle", "duration": 92.0}
    ]
    
    try:
        # 转换为字典格式
        tracks_dict = {track["id"]: track for track in tracks}
        
        # 创建HTML内容
        content = "<h2>渐进式对齐演示</h2>"
        
        # 添加原始轨道预览
        logger.info("生成原始轨道预览...")
        original_preview = generate_tracks_preview(tracks_dict)
        content += "<h3>原始轨道</h3>"
        content += original_preview
        
        # 渐进式对齐，每次添加一个轨道
        logger.info("进行渐进式对齐...")
        aligned_tracks = {}
        
        for i, track in enumerate(tracks):
            # 添加当前轨道
            track_id = track["id"]
            aligned_tracks[track_id] = track
            
            # 如果有多个轨道，进行对齐
            if i > 0:
                # 创建对齐器
                aligner = MultiTrackAligner()
                aligned_tracks = aligner.align_tracks(aligned_tracks)
                
                # 添加当前阶段预览
                content += f"<h3>添加并对齐轨道: {track_id}</h3>"
                stage_preview = generate_tracks_preview(aligned_tracks)
                content += stage_preview
        
        # 保存并打开预览
        logger.info(f"生成的HTML内容长度: {len(content)}")
        save_and_open_html(content, "progressive_alignment_preview.html")
        logger.info("渐进式对齐演示完成")
    except Exception as e:
        logger.error(f"渐进式对齐演示失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def demo_all():
    """运行所有演示"""
    logger.info("=== 运行所有演示 ===")
    demo_scene_timeline()
    demo_multi_track()
    demo_alignment_comparison()
    demo_progressive_alignment()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="实时预览模块演示")
    parser.add_argument('--demo', choices=['timeline', 'tracks', 'alignment', 'progressive', 'all'],
                       default='all', help='要运行的演示类型')
    
    args = parser.parse_args()
    logger.info(f"开始运行实时预览演示，选择的演示类型: {args.demo}")
    
    try:
        if args.demo == 'timeline':
            demo_scene_timeline()
        elif args.demo == 'tracks':
            demo_multi_track()
        elif args.demo == 'alignment':
            demo_alignment_comparison()
        elif args.demo == 'progressive':
            demo_progressive_alignment()
        else:
            demo_all()
        logger.info("演示完成")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 