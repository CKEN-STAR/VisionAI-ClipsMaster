"""
VisionAI-ClipsMaster 多轨时间轴对齐单元测试

此模块包含对多轨时间轴对齐功能的全面测试，
确保在各种场景和边界条件下对齐处理的正确性。
"""

import unittest
import sys
import os
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from timecode.multi_track_align import (
    MultiTrackAligner,
    align_audio_video,
    stretch_video,
    time_shift_audio,
    align_multiple_tracks,
    AlignMethod
)


class TestMultiTrackAligner(unittest.TestCase):
    """测试多轨时间轴对齐器的基础功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建测试轨道数据
        self.test_tracks = {
            "video_main": {
                "id": "video_main",
                "type": "video",
                "is_main": True,
                "duration": 100.0,
                "frame_rate": 30.0,
                "scenes": [
                    {"start_time": 0.0, "end_time": 30.0, "duration": 30.0},
                    {"start_time": 30.0, "end_time": 60.0, "duration": 30.0},
                    {"start_time": 60.0, "end_time": 100.0, "duration": 40.0}
                ]
            },
            "audio_main": {
                "id": "audio_main",
                "type": "audio",
                "duration": 105.0,
                "sample_rate": 44100
            },
            "subtitle_track": {
                "id": "subtitle_track",
                "type": "subtitle",
                "duration": 95.0,
                "subtitles": [
                    {"id": "sub1", "start_time": 5.0, "end_time": 10.0, "text": "测试字幕1"},
                    {"id": "sub2", "start_time": 15.0, "end_time": 20.0, "text": "测试字幕2"},
                    {"id": "sub3", "start_time": 80.0, "end_time": 90.0, "text": "测试字幕3"}
                ]
            },
            "effects_track": {
                "id": "effects_track",
                "type": "effects",
                "duration": 98.0,
                "keyframes": [10.0, 20.0, 30.0, 50.0, 70.0, 90.0]
            }
        }
        
        # 创建对齐器实例
        self.aligner = MultiTrackAligner()
    
    def test_initialization(self):
        """测试初始化和配置加载"""
        # 默认配置初始化
        default_aligner = MultiTrackAligner()
        self.assertEqual(default_aligner.config["alignment_threshold"], 1.0)
        
        # 自定义配置初始化
        custom_config = {
            "alignment_threshold": 2.0,
            "max_stretch_ratio": 0.95,
            "prefer_audio_intact": False
        }
        custom_aligner = MultiTrackAligner(custom_config)
        self.assertEqual(custom_aligner.config["alignment_threshold"], 2.0)
        self.assertEqual(custom_aligner.config["max_stretch_ratio"], 0.95)
        self.assertEqual(custom_aligner.config["prefer_audio_intact"], False)
    
    def test_find_base_track(self):
        """测试基准轨道选择逻辑"""
        # 测试当有is_base标记时
        tracks_with_base = self.test_tracks.copy()
        tracks_with_base["audio_main"]["is_base"] = True
        base_track_id = self.aligner._find_base_track(tracks_with_base)
        self.assertEqual(base_track_id, "audio_main")
        
        # 临时移除audio_main，再测试查找视频主轨道
        tracks_without_audio = {k: v for k, v in self.test_tracks.items() if k != "audio_main"}
        base_track_id = self.aligner._find_base_track(tracks_without_audio)
        self.assertEqual(base_track_id, "video_main")
        
        # 测试当没有标记时，选择最长轨道
        tracks_no_marks = {
            "track1": {"duration": 90.0},
            "track2": {"duration": 110.0},
            "track3": {"duration": 100.0}
        }
        base_track_id = self.aligner._find_base_track(tracks_no_marks)
        self.assertEqual(base_track_id, "track2")
    
    def test_align_tracks(self):
        """测试多轨道对齐主功能"""
        # 使用不包含音频的测试数据
        tracks_without_audio = {k: v for k, v in self.test_tracks.items() if k != "audio_main"}
        aligned_tracks = self.aligner.align_tracks(tracks_without_audio)
        
        # 验证所有轨道都已对齐到视频主轨的时长
        for track_id, track_data in aligned_tracks.items():
            if track_id != "video_main":  # 基准轨道不需要对齐
                self.assertEqual(track_data["duration"], 100.0)
                self.assertTrue("aligned" in track_data and track_data["aligned"])
                self.assertTrue("original_duration" in track_data)
    
    def test_align_audio_track(self):
        """测试音频轨道对齐"""
        # 音频轨道短于目标时长
        short_audio = {
            "id": "short_audio",
            "type": "audio",
            "duration": 90.0
        }
        aligned_audio = self.aligner._align_audio_track(short_audio, 100.0)
        self.assertEqual(aligned_audio["duration"], 100.0)
        self.assertTrue("stretch_ratio" in aligned_audio)
        
        # 音频轨道长于目标时长，但差异小于允许的时移
        long_audio_small_diff = {
            "id": "long_audio",
            "type": "audio",
            "duration": 102.0
        }
        self.aligner.config["max_shift_ms"] = 3000  # 3秒
        aligned_audio = self.aligner._align_audio_track(long_audio_small_diff, 100.0)
        self.assertEqual(aligned_audio["duration"], 100.0)
        self.assertTrue("time_shift" in aligned_audio)
        
        # 音频轨道长于目标时长，且差异大于允许的时移
        long_audio_large_diff = {
            "id": "long_audio",
            "type": "audio",
            "duration": 110.0
        }
        self.aligner.config["max_shift_ms"] = 1000  # 1秒
        aligned_audio = self.aligner._align_audio_track(long_audio_large_diff, 100.0)
        self.assertEqual(aligned_audio["duration"], 100.0)
        self.assertTrue("stretch_ratio" in aligned_audio)
    
    def test_align_video_track(self):
        """测试视频轨道对齐"""
        # 视频轨道短于目标时长，可以安全拉伸
        short_video = {
            "id": "short_video",
            "type": "video",
            "duration": 95.0,
            "frame_rate": 30.0
        }
        aligned_video = self.aligner._align_video_track(short_video, 100.0)
        self.assertEqual(aligned_video["duration"], 100.0)
        self.assertTrue("stretch_ratio" in aligned_video)
        
        # 视频轨道长于目标时长，但拉伸比例超出安全范围
        long_video = {
            "id": "long_video",
            "type": "video",
            "duration": 200.0,
            "frame_rate": 30.0
        }
        aligned_video = self.aligner._align_video_track(long_video, 100.0)
        self.assertEqual(aligned_video["duration"], 100.0)
        # 验证视频轨道包含适当的处理信息
        self.assertTrue("stretch_ratio" in aligned_video or "crop_info" in aligned_video)
    
    def test_align_subtitle_track(self):
        """测试字幕轨道对齐"""
        subtitle_track = self.test_tracks["subtitle_track"]
        aligned_subtitle = self.aligner._align_subtitle_track(subtitle_track, 100.0)
        
        # 验证字幕时长已调整
        self.assertEqual(aligned_subtitle["duration"], 100.0)
        
        # 验证字幕条目时间点已按比例调整
        original_sub = subtitle_track["subtitles"][0]
        aligned_sub = aligned_subtitle["subtitles"][0]
        scale_factor = 100.0 / 95.0
        self.assertAlmostEqual(aligned_sub["start_time"], original_sub["start_time"] * scale_factor, places=4)
        self.assertAlmostEqual(aligned_sub["end_time"], original_sub["end_time"] * scale_factor, places=4)
    
    def test_stretch_track(self):
        """测试轨道伸缩功能"""
        # 准备测试数据
        track_with_scenes = {
            "id": "test_track",
            "duration": 100.0,
            "scenes": [
                {"start_time": 0.0, "end_time": 25.0, "duration": 25.0},
                {"start_time": 25.0, "end_time": 50.0, "duration": 25.0},
                {"start_time": 50.0, "end_time": 100.0, "duration": 50.0}
            ],
            "keyframes": [10.0, 30.0, 60.0, 80.0]
        }
        
        # 伸缩测试
        stretch_ratio = 1.2
        stretched_track = self.aligner._stretch_track(track_with_scenes, stretch_ratio)
        
        # 验证时长调整
        self.assertEqual(stretched_track["duration"], 100.0 * stretch_ratio)
        
        # 验证场景时间点调整
        original_scene = track_with_scenes["scenes"][1]
        stretched_scene = stretched_track["scenes"][1]
        self.assertEqual(stretched_scene["start_time"], original_scene["start_time"] * stretch_ratio)
        self.assertEqual(stretched_scene["end_time"], original_scene["end_time"] * stretch_ratio)
        
        # 验证关键帧时间点调整
        self.assertEqual(stretched_track["keyframes"][2], track_with_scenes["keyframes"][2] * stretch_ratio)
    
    def test_shift_track(self):
        """测试轨道平移功能"""
        # 准备测试数据
        track_with_scenes = {
            "id": "test_track",
            "start_time": 10.0,
            "duration": 100.0,
            "scenes": [
                {"start_time": 0.0, "end_time": 25.0},
                {"start_time": 25.0, "end_time": 50.0},
                {"start_time": 50.0, "end_time": 100.0}
            ],
            "keyframes": [10.0, 30.0, 60.0, 80.0]
        }
        
        # 平移测试
        offset = 5.0
        shifted_track = self.aligner._shift_track(track_with_scenes, offset)
        
        # 验证开始时间调整
        self.assertEqual(shifted_track["start_time"], 15.0)
        
        # 验证场景时间点调整
        original_scene = track_with_scenes["scenes"][1]
        shifted_scene = shifted_track["scenes"][1]
        self.assertEqual(shifted_scene["start_time"], original_scene["start_time"] + offset)
        self.assertEqual(shifted_scene["end_time"], original_scene["end_time"] + offset)
        
        # 验证关键帧时间点调整
        self.assertEqual(shifted_track["keyframes"][2], track_with_scenes["keyframes"][2] + offset)
    
    def test_crop_track(self):
        """测试轨道裁剪功能"""
        # 准备测试数据
        track_with_scenes = {
            "id": "test_track",
            "duration": 100.0,
            "scenes": [
                {"start_time": 0.0, "end_time": 20.0},
                {"start_time": 20.0, "end_time": 50.0},
                {"start_time": 50.0, "end_time": 80.0},
                {"start_time": 80.0, "end_time": 100.0}
            ]
        }
        
        # 裁剪测试
        target_duration = 80.0
        cropped_track = self.aligner._crop_track(track_with_scenes, target_duration)
        
        # 验证时长调整
        self.assertEqual(cropped_track["duration"], target_duration)
        
        # 验证裁剪信息
        self.assertTrue("crop_info" in cropped_track)
        self.assertEqual(cropped_track["crop_info"]["original_duration"], 100.0)
        self.assertEqual(cropped_track["crop_info"]["target_duration"], 80.0)
    
    def test_pad_track(self):
        """测试轨道填充功能"""
        # 准备测试数据
        track_with_scenes = {
            "id": "test_track",
            "duration": 80.0,
            "scenes": [
                {"start_time": 0.0, "end_time": 20.0},
                {"start_time": 20.0, "end_time": 40.0},
                {"start_time": 40.0, "end_time": 80.0}
            ]
        }
        
        # 填充测试
        target_duration = 100.0
        padded_track = self.aligner._pad_track(track_with_scenes, target_duration)
        
        # 验证时长调整
        self.assertEqual(padded_track["duration"], target_duration)
        
        # 验证填充信息
        self.assertTrue("pad_info" in padded_track)
        self.assertEqual(padded_track["pad_info"]["original_duration"], 80.0)
        self.assertEqual(padded_track["pad_info"]["target_duration"], 100.0)
        
        # 验证场景时间点调整（应该偏移以适应前部填充）
        pad_amount = padded_track["pad_info"]["start_pad"]
        original_scene = track_with_scenes["scenes"][1]
        padded_scene = padded_track["scenes"][1]
        self.assertEqual(padded_scene["start_time"], original_scene["start_time"] + pad_amount)


class TestAlignmentFunctions(unittest.TestCase):
    """测试对齐辅助函数"""
    
    def test_align_audio_video(self):
        """测试音视频精确对齐"""
        # 音频长于视频
        audio_track = {"id": "audio", "type": "audio", "duration": 105.0}
        video_track = {"id": "video", "type": "video", "duration": 100.0, "frame_rate": 30.0}
        
        aligned_audio, aligned_video = align_audio_video(audio_track, video_track)
        
        # 验证视频已拉伸以匹配音频
        self.assertEqual(aligned_video["duration"], 105.0)
        self.assertTrue("stretch_ratio" in aligned_video)
        
        # 音频短于视频
        audio_track = {"id": "audio", "type": "audio", "duration": 95.0}
        video_track = {"id": "video", "type": "video", "duration": 100.0, "frame_rate": 30.0}
        
        aligned_audio, aligned_video = align_audio_video(audio_track, video_track)
        
        # 验证音频已调整以匹配视频
        self.assertEqual(aligned_audio["duration"], 100.0)
        self.assertTrue("time_shift" in aligned_audio)
        
        # 差异小于阈值不需调整
        audio_track = {"id": "audio", "type": "audio", "duration": 100.5}
        video_track = {"id": "video", "type": "video", "duration": 100.0, "frame_rate": 30.0}
        
        aligned_audio, aligned_video = align_audio_video(audio_track, video_track)
        
        # 验证无需调整
        self.assertEqual(aligned_audio, audio_track)
        self.assertEqual(aligned_video, video_track)
    
    def test_stretch_video(self):
        """测试视频拉伸函数"""
        video_track = {
            "id": "video",
            "type": "video",
            "duration": 100.0,
            "frame_rate": 30.0
        }
        
        # 拉伸测试
        target_duration = 110.0
        stretched_video = stretch_video(video_track, target_duration)
        
        # 验证时长调整
        self.assertEqual(stretched_video["duration"], target_duration)
        
        # 验证拉伸比例
        self.assertEqual(stretched_video["stretch_ratio"], 1.1)
        
        # 验证帧率调整
        self.assertEqual(stretched_video["frame_rate"], video_track["frame_rate"] / 1.1)
    
    def test_time_shift_audio(self):
        """测试音频时移函数"""
        audio_track = {
            "id": "audio",
            "type": "audio",
            "duration": 100.0
        }
        
        # 进行极小幅度时移测试
        target_duration = 100.01  # 非常小的差异
        shifted_audio = time_shift_audio(audio_track, target_duration, offset_ms=50)
        
        # 极小差异应该只使用时移
        self.assertEqual(shifted_audio["duration"], target_duration)
        self.assertTrue("time_shift" in shifted_audio)
        
        # 大幅调整测试
        target_duration = 110.0
        adjusted_audio = time_shift_audio(audio_track, target_duration, offset_ms=50)
        
        # 结合时移和速率调整
        self.assertEqual(adjusted_audio["duration"], target_duration)
        self.assertTrue("time_shift" in adjusted_audio)
        self.assertTrue("rate_adjust" in adjusted_audio)
    
    def test_align_multiple_tracks(self):
        """测试多轨道对齐函数"""
        tracks = [
            {"id": "track1", "type": "video", "duration": 100.0},
            {"id": "track2", "type": "audio", "duration": 105.0},
            {"id": "track3", "type": "subtitle", "duration": 95.0}
        ]
        
        aligned_tracks = align_multiple_tracks(tracks)
        
        # 验证所有轨道都对齐到最长轨道的时长
        for track in aligned_tracks:
            self.assertEqual(track["duration"], 105.0)


if __name__ == '__main__':
    unittest.main() 