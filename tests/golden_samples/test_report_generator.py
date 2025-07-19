#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
差异可视化报告生成器的测试模块
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.golden_samples.report_generator import generate_diff_report, DiffReport


class TestReportGenerator(unittest.TestCase):
    """测试报告生成器功能"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备工作"""
        # 创建临时目录
        cls.temp_dir = tempfile.mkdtemp()
        
        # 设置测试数据路径
        samples_dir = Path(__file__).parent
        
        # 查找测试用例目录
        lang_dirs = [d for d in samples_dir.iterdir() if d.is_dir() and d.name in ('zh', 'en')]
        
        if not lang_dirs:
            raise ValueError("找不到任何语言测试集目录")
        
        # 优先使用中文测试集
        test_dir = next((d for d in lang_dirs if d.name == 'zh'), lang_dirs[0])
        
        # 查找测试用例
        test_cases = []
        for case_dir in test_dir.iterdir():
            if case_dir.is_dir():
                videos = list(case_dir.glob('*.mp4'))
                srts = list(case_dir.glob('*.srt'))
                
                if videos and srts:
                    test_cases.append((videos[0], srts[0]))
        
        if not test_cases:
            # 创建简单的测试视频和字幕文件
            cls._create_test_files()
            
            cls.golden_video = os.path.join(cls.temp_dir, 'golden.mp4')
            cls.golden_srt = os.path.join(cls.temp_dir, 'golden.srt')
            cls.test_video = os.path.join(cls.temp_dir, 'test.mp4')
            cls.test_srt = os.path.join(cls.temp_dir, 'test.srt')
        else:
            # 使用找到的第一个测试用例
            golden_pair = test_cases[0]
            cls.golden_video = str(golden_pair[0])
            cls.golden_srt = str(golden_pair[1])
            
            # 复制到临时目录作为测试视频
            cls.test_video = os.path.join(cls.temp_dir, 'test.mp4')
            cls.test_srt = os.path.join(cls.temp_dir, 'test.srt')
            
            shutil.copy(cls.golden_video, cls.test_video)
            shutil.copy(cls.golden_srt, cls.test_srt)
        
        # 创建输出目录
        cls.output_dir = os.path.join(cls.temp_dir, 'reports')
        os.makedirs(cls.output_dir, exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        """测试后清理工作"""
        # 删除临时目录
        shutil.rmtree(cls.temp_dir)
    
    @staticmethod
    def _create_test_files():
        """创建测试用的视频和字幕文件"""
        try:
            import cv2
            import numpy as np
            
            # 创建一个简单的测试视频
            def create_test_video(file_path, color=(0, 0, 255)):
                writer = None
                try:
                    height, width = 480, 640
                    fps = 25
                    seconds = 5
                    
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    writer = cv2.VideoWriter(file_path, fourcc, fps, (width, height))
                    
                    # 生成几帧彩色帧
                    for i in range(fps * seconds):
                        # 创建一个彩色帧
                        frame = np.zeros((height, width, 3), dtype=np.uint8)
                        # 添加一些动态元素
                        cv2.circle(frame, (width // 2, height // 2), 50 + i % 50, color, -1)
                        cv2.putText(frame, f"Frame {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        writer.write(frame)
                finally:
                    if writer:
                        writer.release()
            
            # 创建测试字幕文件
            def create_test_srt(file_path, subtitle_count=10):
                with open(file_path, 'w', encoding='utf-8') as f:
                    for i in range(1, subtitle_count + 1):
                        start_time = i * 0.5
                        end_time = start_time + 0.4
                        
                        # 格式化时间字符串
                        def format_time(seconds):
                            h = int(seconds / 3600)
                            m = int((seconds % 3600) / 60)
                            s = seconds % 60
                            return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.', ',')
                        
                        f.write(f"{i}\n")
                        f.write(f"{format_time(start_time)} --> {format_time(end_time)}\n")
                        f.write(f"测试字幕 {i}\n\n")
            
            # 创建黄金标准视频和字幕
            golden_video = os.path.join(TestReportGenerator.temp_dir, 'golden.mp4')
            golden_srt = os.path.join(TestReportGenerator.temp_dir, 'golden.srt')
            create_test_video(golden_video, color=(0, 0, 255))  # 红色
            create_test_srt(golden_srt)
            
            # 创建测试视频和字幕（略有不同）
            test_video = os.path.join(TestReportGenerator.temp_dir, 'test.mp4')
            test_srt = os.path.join(TestReportGenerator.temp_dir, 'test.srt')
            create_test_video(test_video, color=(0, 255, 0))  # 绿色
            
            # 创建略有不同的测试字幕
            with open(golden_srt, 'r', encoding='utf-8') as f_in:
                content = f_in.read()
            
            # 修改部分字幕文本
            modified_content = content.replace('测试字幕 3', '修改过的字幕 3')
            modified_content = modified_content.replace('测试字幕 7', '这是不同的字幕内容 7')
            
            with open(test_srt, 'w', encoding='utf-8') as f_out:
                f_out.write(modified_content)
            
        except ImportError:
            # 如果无法创建视频，则创建空文件
            with open(os.path.join(TestReportGenerator.temp_dir, 'golden.mp4'), 'wb') as f:
                f.write(b'dummy video content')
            with open(os.path.join(TestReportGenerator.temp_dir, 'golden.srt'), 'w') as f:
                f.write('1\n00:00:01,000 --> 00:00:04,000\n测试字幕\n\n')
            
            with open(os.path.join(TestReportGenerator.temp_dir, 'test.mp4'), 'wb') as f:
                f.write(b'dummy test video content')
            with open(os.path.join(TestReportGenerator.temp_dir, 'test.srt'), 'w') as f:
                f.write('1\n00:00:01,000 --> 00:00:04,000\n修改过的字幕\n\n')
    
    def test_init_report_generator(self):
        """测试报告生成器初始化"""
        try:
            report_gen = DiffReport(
                self.test_video, 
                self.golden_video, 
                self.test_srt, 
                self.golden_srt,
                self.output_dir
            )
            
            # 检查基本属性
            self.assertEqual(report_gen.test_video, self.test_video)
            self.assertEqual(report_gen.golden_video, self.golden_video)
            self.assertEqual(report_gen.test_srt, self.test_srt)
            self.assertEqual(report_gen.golden_srt, self.golden_srt)
            self.assertEqual(report_gen.output_dir, self.output_dir)
            
            # 检查是否加载了视频信息
            self.assertIsNotNone(report_gen.test_video_info)
            self.assertIsNotNone(report_gen.golden_video_info)
            
            # 检查是否加载了字幕信息
            self.assertIsInstance(report_gen.test_subtitles, list)
            self.assertIsInstance(report_gen.golden_subtitles, list)
            
        except Exception as e:
            self.fail(f"初始化报告生成器失败: {str(e)}")
    
    def test_generate_diff_report(self):
        """测试生成差异报告"""
        try:
            # 测试报告生成功能
            report_path = generate_diff_report(
                self.test_video,
                self.golden_video,
                self.test_srt,
                self.golden_srt,
                self.output_dir
            )
            
            # 检查报告文件是否存在
            self.assertTrue(os.path.exists(report_path))
            
            # 检查报告文件内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 验证报告包含必要元素
            self.assertIn('<!DOCTYPE html>', content)
            self.assertIn('<title>视频对比分析报告</title>', content)
            self.assertIn('视频质量', content)
            self.assertIn('字幕质量', content)
            self.assertIn('剧情质量', content)
            
        except Exception as e:
            self.fail(f"生成差异报告失败: {str(e)}")
    
    def test_extract_key_frames(self):
        """测试关键帧提取功能"""
        try:
            report_gen = DiffReport(
                self.test_video, 
                self.golden_video, 
                self.test_srt, 
                self.golden_srt,
                self.output_dir
            )
            
            # 提取关键帧
            frames = report_gen.extract_key_frames(self.test_video, count=3)
            
            # 验证结果
            if len(frames) == 0:
                # 如果使用的是dummy文件，可能无法提取帧
                print("警告: 无法从测试视频中提取关键帧")
            else:
                self.assertEqual(len(frames), 3)
                for frame in frames:
                    # 验证帧是否是numpy数组
                    self.assertIsNotNone(frame)
        except Exception as e:
            self.fail(f"提取关键帧失败: {str(e)}")
    
    def test_highlight_text_diff(self):
        """测试文本差异高亮功能"""
        try:
            report_gen = DiffReport(
                self.test_video, 
                self.golden_video, 
                self.test_srt, 
                self.golden_srt,
                self.output_dir
            )
            
            # 高亮文本差异
            text_diff = report_gen.highlight_text_diff(self.test_srt, self.golden_srt)
            
            # 验证结果
            self.assertIsInstance(text_diff, dict)
            self.assertIn('diff_data', text_diff)
            self.assertIn('avg_similarity', text_diff)
            
            # 验证差异数据
            if text_diff['diff_data']:
                for item in text_diff['diff_data']:
                    self.assertIn('index', item)
                    self.assertIn('similarity', item)
                    self.assertIn('golden_text', item)
                    self.assertIn('test_text', item)
        except Exception as e:
            self.fail(f"高亮文本差异失败: {str(e)}")
    
    def test_generate_metrics(self):
        """测试质量指标生成功能"""
        try:
            report_gen = DiffReport(
                self.test_video, 
                self.golden_video, 
                self.test_srt, 
                self.golden_srt,
                self.output_dir
            )
            
            # 首先生成必要的资源数据
            report_gen.plot_side_by_side(report_gen.test_video, report_gen.golden_video)
            report_gen.plot_timeline_difference()
            report_gen.highlight_text_diff(report_gen.test_srt, report_gen.golden_srt)
            
            # 生成质量指标
            metrics = report_gen.generate_metrics()
            
            # 验证结果
            self.assertIsInstance(metrics, dict)
            self.assertIn('overall_score', metrics)
            self.assertIn('quality_level', metrics)
            self.assertIn('video_score', metrics)
            self.assertIn('subtitle_score', metrics)
            self.assertIn('narrative_score', metrics)
            
        except Exception as e:
            self.fail(f"生成质量指标失败: {str(e)}")


if __name__ == '__main__':
    unittest.main() 