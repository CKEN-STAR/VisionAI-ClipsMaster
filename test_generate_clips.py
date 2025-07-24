#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试generate_clips方法
"""

import sys
import os
import tempfile

# 添加路径
sys.path.insert(0, 'src')

try:
    from core.clip_generator import ClipGenerator
    
    print("=== 测试generate_clips方法 ===")
    
    # 创建ClipGenerator实例
    cg = ClipGenerator()
    print("ClipGenerator实例创建成功")

    # 检查ffmpeg_path属性
    if hasattr(cg, 'ffmpeg_path'):
        print(f"ffmpeg_path: {cg.ffmpeg_path}")
    else:
        print("错误: ClipGenerator没有ffmpeg_path属性")
        print(f"实例属性: {[attr for attr in dir(cg) if not attr.startswith('_')]}")
        exit(1)
    
    # 创建测试视频文件
    test_video = "test_video.mp4"
    
    # 创建一个简单的测试视频（使用FFmpeg）
    import subprocess
    
    # 检查FFmpeg是否可用
    try:
        result = subprocess.run([cg.ffmpeg_path, "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"FFmpeg可用: {cg.ffmpeg_path}")
            
            # 创建测试视频
            cmd = [
                cg.ffmpeg_path,
                '-f', 'lavfi',
                '-i', 'testsrc=duration=10:size=320x240:rate=1',
                '-y',
                test_video
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(test_video):
                print(f"测试视频创建成功: {test_video}")
                
                # 测试generate_clips方法
                test_segments = [
                    {"start": "00:00:00,000", "end": "00:00:02,000", "text": "片段1"},
                    {"start": "00:00:02,000", "end": "00:00:04,000", "text": "片段2"}
                ]
                
                output_path = "test_output.mp4"
                
                print("调用generate_clips方法...")
                result = cg.generate_clips(test_video, test_segments, output_path)
                
                print(f"generate_clips返回结果: {result}")
                
                if result.get('status') == 'success':
                    print("✓ generate_clips方法测试成功")
                    if os.path.exists(output_path):
                        print(f"✓ 输出文件创建成功: {output_path}")
                    else:
                        print("✗ 输出文件不存在")
                else:
                    print(f"✗ generate_clips方法失败: {result.get('error', '未知错误')}")
                
                # 清理文件
                for file in [test_video, output_path]:
                    if os.path.exists(file):
                        os.remove(file)
                        
            else:
                print(f"测试视频创建失败: {result.stderr}")
        else:
            print(f"FFmpeg不可用: {result.stderr}")
            
    except Exception as e:
        print(f"FFmpeg测试失败: {e}")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()
