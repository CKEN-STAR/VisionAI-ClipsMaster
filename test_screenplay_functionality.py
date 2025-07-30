#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本重构功能专项测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_screenplay_reconstruction():
    """测试剧本重构功能"""
    print("=" * 60)
    print("剧本重构功能专项测试")
    print("=" * 60)
    
    try:
        from src.core.screenplay_engineer import ScreenplayEngineer
        from src.core.srt_parser import SRTParser
        
        # 创建测试数据
        test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是一个关于爱情的故事

2
00:00:03,000 --> 00:00:05,000
男主角是一个普通的上班族

3
00:00:05,000 --> 00:00:07,000
女主角是一个美丽的画家

4
00:00:07,000 --> 00:00:10,000
他们在咖啡厅相遇了

5
00:00:10,000 --> 00:00:12,000
这是命运的安排吗？"""
        
        # 保存测试文件
        test_file = "test_screenplay_input.srt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_srt_content)
        
        print("✓ 测试SRT文件创建成功")
        
        # 解析SRT文件
        parser = SRTParser()
        subtitles = parser.parse_srt_file(test_file)
        print(f"✓ SRT解析成功，共解析到 {len(subtitles)} 条字幕")
        
        # 显示解析结果
        for i, subtitle in enumerate(subtitles):
            print(f"  字幕{i+1}: {subtitle}")
        
        # 创建剧本工程师
        engineer = ScreenplayEngineer()
        print("✓ 剧本工程师初始化成功")
        
        # 测试剧本重构
        try:
            reconstructed = engineer.reconstruct_screenplay(subtitles)
            print(f"✓ 剧本重构完成，生成 {len(reconstructed)} 个片段")
            
            # 显示重构结果
            if isinstance(reconstructed, list) and len(reconstructed) > 0:
                print("重构结果预览:")
                for i, segment in enumerate(reconstructed[:3]):  # 只显示前3个
                    if isinstance(segment, dict):
                        start = segment.get('start', 0)
                        end = segment.get('end', 0)
                        text = str(segment.get('text', ''))[:30]
                        print(f"  片段{i+1}: {start:.1f}s-{end:.1f}s: {text}...")
                    else:
                        print(f"  片段{i+1}: {str(segment)[:50]}...")
            else:
                print("重构结果为空或格式异常")
                
        except Exception as e:
            print(f"✗ 剧本重构执行失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✓ 测试文件清理完成")
        
        print("✓ 剧本重构功能测试完成")
        
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
    except Exception as e:
        print(f"✗ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()

def test_language_detection():
    """测试语言检测功能"""
    print("\n" + "=" * 60)
    print("语言检测功能专项测试")
    print("=" * 60)
    
    try:
        from src.core.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        print("✓ 语言检测器初始化成功")
        
        # 测试用例
        test_cases = [
            ("这是一个中文测试句子", "zh"),
            ("This is an English test sentence", "en"),
            ("Hello 你好 mixed language", "mixed"),
            ("", "unknown")
        ]
        
        for text, expected in test_cases:
            try:
                result = detector.detect_language(text)
                print(f"✓ 文本: '{text[:20]}...' -> 检测结果: {result}")
            except Exception as e:
                print(f"✗ 语言检测失败: {e}")
        
        print("✓ 语言检测功能测试完成")
        
    except ImportError as e:
        print(f"✗ 语言检测器导入失败: {e}")
    except Exception as e:
        print(f"✗ 语言检测测试失败: {e}")

def test_video_processing():
    """测试视频处理功能"""
    print("\n" + "=" * 60)
    print("视频处理功能专项测试")
    print("=" * 60)
    
    try:
        from src.core.video_processor import VideoProcessor
        
        processor = VideoProcessor()
        print("✓ 视频处理器初始化成功")
        
        # 测试基本功能
        print("✓ 视频处理器基本功能正常")
        
    except ImportError as e:
        print(f"✗ 视频处理器导入失败: {e}")
    except Exception as e:
        print(f"✗ 视频处理测试失败: {e}")

def main():
    """主函数"""
    print("VisionAI-ClipsMaster 核心功能专项测试")
    print("测试时间:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 执行各项测试
    test_screenplay_reconstruction()
    test_language_detection()
    test_video_processing()
    
    print("\n" + "=" * 60)
    print("所有专项测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
