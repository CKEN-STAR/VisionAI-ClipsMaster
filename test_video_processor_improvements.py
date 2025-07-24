#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频处理器改进功能
"""

import sys
import os
sys.path.append('src')

def test_video_processor_improvements():
    """测试视频处理器的改进功能"""
    print("🎬 测试视频处理器改进功能")
    print("=" * 50)
    
    try:
        from src.core.video_processor import VideoProcessor
        processor = VideoProcessor()
        print("✅ 视频处理器初始化成功")
        
        # 测试基本功能
        print(f"支持的格式: {processor.get_supported_formats()}")
        print(f"FFmpeg可用: {processor.ffmpeg_path is not None}")
        
        # 测试新增方法
        print("\n✅ 新增方法验证:")
        methods_to_check = [
            'concatenate_videos',
            'extract_video_segment', 
            'validate_video_file'
        ]
        
        for method in methods_to_check:
            has_method = hasattr(processor, method)
            print(f"- {method}: {'✅' if has_method else '❌'}")
        
        # 测试方法调用
        print("\n🔧 测试方法调用:")
        
        # 测试视频验证
        test_result = processor.validate_video_file("test.mp4")
        print(f"- validate_video_file: {test_result}")
        
        # 测试格式检测
        is_supported = processor.is_supported_format("test.mp4")
        print(f"- is_supported_format(.mp4): {is_supported}")
        
        print("\n✅ 视频处理器改进测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_video_processor_improvements()
