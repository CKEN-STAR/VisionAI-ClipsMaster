#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试实时预览模块
"""

import os
import logging
from timecode.live_preview import PreviewGenerator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_preview_generator():
    """测试预览生成器的基本功能"""
    logger.info("创建测试场景数据...")
    
    # 测试场景数据
    test_scenes = [
        {"start": 0, "end": 15, "emotion_score": 0.5, "sentiment": "neutral"},
        {"start": 15, "end": 30, "emotion_score": 0.8, "sentiment": "positive"},
        {"start": 30, "end": 50, "emotion_score": 0.3, "sentiment": "negative"},
        {"start": 50, "end": 75, "emotion_score": 0.9, "scene_type": "climax"}
    ]
    
    # 测试轨道
    test_tracks = {
        "main_video": {
            "type": "video",
            "duration": 75.0,
            "scenes": [
                {"start_time": 0, "end_time": 25},
                {"start_time": 25, "end_time": 50},
                {"start_time": 50, "end_time": 75}
            ]
        },
        "main_audio": {
            "type": "audio",
            "duration": 80.0
        },
        "subtitle": {
            "type": "subtitle",
            "duration": 70.0
        }
    }
    
    logger.info("创建预览生成器...")
    preview_gen = PreviewGenerator({
        "width": 10,
        "height": 5,
        "output_format": "html"
    })
    
    logger.info("生成波形图预览...")
    try:
        waveform_html = preview_gen.generate_waveform(test_scenes)
        logger.info(f"波形图HTML长度: {len(waveform_html)}")
        
        # 保存HTML文件
        with open("test_waveform.html", "w", encoding="utf-8") as f:
            f.write(f"<html><body>{waveform_html}</body></html>")
        logger.info(f"波形图已保存至: {os.path.abspath('test_waveform.html')}")
    except Exception as e:
        logger.error(f"生成波形图失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("生成轨道视图预览...")
    try:
        tracks_html = preview_gen.generate_track_view(test_tracks)
        logger.info(f"轨道视图HTML长度: {len(tracks_html)}")
        
        # 保存HTML文件
        with open("test_tracks.html", "w", encoding="utf-8") as f:
            f.write(f"<html><body>{tracks_html}</body></html>")
        logger.info(f"轨道视图已保存至: {os.path.abspath('test_tracks.html')}")
    except Exception as e:
        logger.error(f"生成轨道视图失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("开始测试实时预览模块...")
    test_preview_generator()
    logger.info("测试完成") 