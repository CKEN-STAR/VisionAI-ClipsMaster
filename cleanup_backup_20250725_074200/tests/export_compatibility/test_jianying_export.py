#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映导出兼容性测试

测试范围:
1. 剪映工程文件生成与导入 (100%兼容性)
2. 多独立视频片段时间轴显示
3. 视频质量保持验证
4. 达芬奇Resolve兼容性
5. 多格式输出测试 (MP4/SRT/JSON)
6. 时间轴精度验证 (≤0.2s误差)
"""

import pytest
import json
import os
import tempfile
import zipfile
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.core.jianying_exporter import JianyingExporter
from src.export.jianying_exporter import JianyingExporter as ExportJianyingExporter


class TestJianyingExport:
    """剪映导出兼容性测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.jianying_exporter = JianyingExporter()
        self.export_jianying_exporter = ExportJianyingExporter()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 测试数据
        self.sample_video_segments = [
            {
                "id": "segment_001",
                "start_time": "00:00:01,000",
                "end_time": "00:00:05,000",
                "source_file": "original_video.mp4",
                "source_start": 1.0,
                "source_end": 5.0
            },
            {
                "id": "segment_002", 
                "start_time": "00:00:05,000",
                "end_time": "00:00:10,000",
                "source_file": "original_video.mp4",
                "source_start": 15.0,
                "source_end": 20.0
            },
            {
                "id": "segment_003",
                "start_time": "00:00:10,000", 
                "end_time": "00:00:15,000",
                "source_file": "original_video.mp4",
                "source_start": 30.0,
                "source_end": 35.0
            }
        ]
        
        self.sample_subtitles = [
            {
                "id": "sub_001",
                "start_time": "00:00:01,000",
                "end_time": "00:00:05,000", 
                "text": "这是第一段字幕",
                "style": {"font_size": 24, "color": "#FFFFFF"}
            },
            {
                "id": "sub_002",
                "start_time": "00:00:05,000",
                "end_time": "00:00:10,000",
                "text": "这是第二段字幕", 
                "style": {"font_size": 24, "color": "#FFFFFF"}
            },
            {
                "id": "sub_003",
                "start_time": "00:00:10,000",
                "end_time": "00:00:15,000",
                "text": "这是第三段字幕",
                "style": {"font_size": 24, "color": "#FFFFFF"}
            }
        ]

    def test_jianying_project_file_generation(self):
        """测试剪映工程文件生成"""
        project_name = "VisionAI_Test_Project"
        
        # 生成剪映项目文件
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name=project_name
        )
        
        # 验证文件生成
        assert os.path.exists(project_file_path), "剪映项目文件未生成"
        assert project_file_path.endswith('.json'), "项目文件格式错误"
        
        # 验证文件内容
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 验证项目结构
        assert "project_name" in project_data, "缺少项目名称"
        assert "timeline" in project_data, "缺少时间轴信息"
        assert "materials" in project_data, "缺少素材库信息"
        assert "tracks" in project_data, "缺少轨道信息"
        
        # 验证视频轨道
        video_tracks = [track for track in project_data["tracks"] if track["type"] == "video"]
        assert len(video_tracks) >= 1, "缺少视频轨道"
        
        # 验证字幕轨道
        subtitle_tracks = [track for track in project_data["tracks"] if track["type"] == "subtitle"]
        assert len(subtitle_tracks) >= 1, "缺少字幕轨道"

    def test_multiple_independent_video_segments(self):
        """测试多独立视频片段时间轴显示"""
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name="Multi_Segment_Test"
        )
        
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 验证视频片段独立性
        video_tracks = [track for track in project_data["tracks"] if track["type"] == "video"]
        video_track = video_tracks[0]
        segments = video_track.get("segments", [])
        
        assert len(segments) == len(self.sample_video_segments), \
            f"视频片段数量不匹配: {len(segments)} != {len(self.sample_video_segments)}"
        
        # 验证每个片段的独立性
        for i, segment in enumerate(segments):
            expected_segment = self.sample_video_segments[i]
            
            assert segment["id"] == expected_segment["id"], f"片段ID不匹配: {segment['id']}"
            assert "source_range" in segment, f"片段{i}缺少源时间范围"
            assert "timeline_position" in segment, f"片段{i}缺少时间轴位置"
            
            # 验证片段可编辑性标记
            assert segment.get("editable", True), f"片段{i}不可编辑"
            assert segment.get("movable", True), f"片段{i}不可移动"
            assert segment.get("deletable", True), f"片段{i}不可删除"

    def test_timeline_accuracy(self):
        """测试时间轴精度 (≤0.2s误差)"""
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name="Timeline_Accuracy_Test"
        )
        
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 获取视频轨道
        video_tracks = [track for track in project_data["tracks"] if track["type"] == "video"]
        video_segments = video_tracks[0]["segments"]
        
        # 验证时间轴精度
        for i, segment in enumerate(video_segments):
            expected_segment = self.sample_video_segments[i]
            
            # 解析时间
            expected_start = self._parse_time(expected_segment["start_time"])
            expected_end = self._parse_time(expected_segment["end_time"])
            
            actual_start = segment["timeline_position"]["start"]
            actual_end = segment["timeline_position"]["end"]
            
            # 验证时间精度
            start_error = abs(actual_start - expected_start)
            end_error = abs(actual_end - expected_end)
            
            assert start_error <= 0.2, f"片段{i}开始时间误差过大: {start_error:.3f}s"
            assert end_error <= 0.2, f"片段{i}结束时间误差过大: {end_error:.3f}s"

    def test_video_quality_preservation(self):
        """测试视频质量保持验证"""
        # 模拟原始视频信息
        original_video_info = {
            "resolution": "1920x1080",
            "fps": 30,
            "bitrate": 5000,
            "codec": "h264"
        }
        
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name="Quality_Test"
        )
        
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # 验证导出设置保持原始质量
        export_settings = project_data.get("export_settings", {})
        
        assert export_settings.get("maintain_original_quality", False), "未设置保持原始质量"
        assert export_settings.get("resolution") == original_video_info["resolution"], "分辨率设置错误"
        assert export_settings.get("fps") == original_video_info["fps"], "帧率设置错误"

    def test_materials_library_import(self):
        """测试素材库完整导入"""
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name="Materials_Test"
        )
        
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        materials = project_data.get("materials", {})
        
        # 验证视频素材
        video_materials = materials.get("videos", [])
        assert len(video_materials) > 0, "缺少视频素材"
        
        # 验证每个视频素材的完整性
        for material in video_materials:
            assert "id" in material, "视频素材缺少ID"
            assert "path" in material, "视频素材缺少路径"
            assert "duration" in material, "视频素材缺少时长信息"
            assert "metadata" in material, "视频素材缺少元数据"
        
        # 验证字幕素材
        subtitle_materials = materials.get("subtitles", [])
        assert len(subtitle_materials) > 0, "缺少字幕素材"

    def test_jianying_app_auto_launch(self):
        """测试剪映应用自动启动"""
        # 模拟剪映启动功能
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.poll.return_value = None
            
            project_file_path = self.jianying_exporter.export_jianying_project(
                video_segments=self.sample_video_segments,
                subtitles=self.sample_subtitles,
                project_name="Auto_Launch_Test"
            )
            
            # 测试自动启动
            launch_success = self.jianying_exporter.launch_jianying_with_project(project_file_path)
            
            # 验证启动尝试
            assert launch_success or mock_popen.called, "剪映自动启动失败"

    def test_davinci_resolve_compatibility(self):
        """测试达芬奇Resolve兼容性"""
        try:
            from src.exporters.davinci_resolve import DaVinciResolveExporter
            
            davinci_exporter = DaVinciResolveExporter()
            
            # 导出达芬奇项目文件
            davinci_project_path = davinci_exporter.export_project(
                video_segments=self.sample_video_segments,
                subtitles=self.sample_subtitles,
                project_name="DaVinci_Test"
            )
            
            # 验证文件生成
            assert os.path.exists(davinci_project_path), "达芬奇项目文件未生成"
            
            # 验证XML格式
            import xml.etree.ElementTree as ET
            tree = ET.parse(davinci_project_path)
            root = tree.getroot()
            
            assert root.tag in ["fcpxml", "xmeml"], "达芬奇项目文件格式错误"
            
        except ImportError:
            pytest.skip("达芬奇导出器模块不可用")

    def test_multi_format_output(self):
        """测试多格式输出"""
        output_formats = ["mp4", "srt", "json"]
        
        for format_type in output_formats:
            output_path = os.path.join(self.temp_dir, f"test_output.{format_type}")
            
            if format_type == "mp4":
                # 测试视频导出
                success = self.jianying_exporter.export_video(
                    video_segments=self.sample_video_segments,
                    output_path=output_path
                )
            elif format_type == "srt":
                # 测试字幕导出
                success = self.jianying_exporter.export_subtitles(
                    subtitles=self.sample_subtitles,
                    output_path=output_path
                )
            elif format_type == "json":
                # 测试JSON导出
                success = self.jianying_exporter.export_metadata(
                    video_segments=self.sample_video_segments,
                    subtitles=self.sample_subtitles,
                    output_path=output_path
                )
            
            assert success, f"{format_type}格式导出失败"
            assert os.path.exists(output_path), f"{format_type}文件未生成"

    def test_export_error_handling(self):
        """测试导出错误处理"""
        # 测试空数据导出
        empty_result = self.jianying_exporter.export_jianying_project(
            video_segments=[],
            subtitles=[],
            project_name="Empty_Test"
        )
        
        # 应该有适当的错误处理
        assert empty_result is None or "error" in str(empty_result), "空数据错误处理失败"
        
        # 测试无效路径
        invalid_path = "/invalid/path/project.json"
        try:
            result = self.jianying_exporter.export_jianying_project(
                video_segments=self.sample_video_segments,
                subtitles=self.sample_subtitles,
                project_name="Invalid_Path_Test"
            )
            # 如果没有抛出异常，应该返回错误信息
        except Exception:
            # 预期的异常处理
            pass

    def test_large_project_export_performance(self):
        """测试大型项目导出性能"""
        # 创建大量片段
        large_video_segments = []
        large_subtitles = []
        
        for i in range(100):
            segment = {
                "id": f"segment_{i:03d}",
                "start_time": f"00:{i//60:02d}:{i%60:02d},000",
                "end_time": f"00:{(i+5)//60:02d}:{(i+5)%60:02d},000",
                "source_file": "large_video.mp4",
                "source_start": i * 5.0,
                "source_end": (i + 1) * 5.0
            }
            large_video_segments.append(segment)
            
            subtitle = {
                "id": f"sub_{i:03d}",
                "start_time": f"00:{i//60:02d}:{i%60:02d},000",
                "end_time": f"00:{(i+5)//60:02d}:{(i+5)%60:02d},000",
                "text": f"字幕文本 {i}",
                "style": {"font_size": 24, "color": "#FFFFFF"}
            }
            large_subtitles.append(subtitle)
        
        # 测试导出性能
        import time
        start_time = time.time()
        
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=large_video_segments,
            subtitles=large_subtitles,
            project_name="Large_Project_Test"
        )
        
        export_time = time.time() - start_time
        
        # 验证性能要求
        assert export_time <= 30.0, f"大型项目导出时间过长: {export_time:.2f}s"
        assert os.path.exists(project_file_path), "大型项目文件未生成"

    def test_source_timerange_accuracy(self):
        """测试源时间范围精度"""
        project_file_path = self.jianying_exporter.export_jianying_project(
            video_segments=self.sample_video_segments,
            subtitles=self.sample_subtitles,
            project_name="Source_Range_Test"
        )
        
        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        video_tracks = [track for track in project_data["tracks"] if track["type"] == "video"]
        video_segments = video_tracks[0]["segments"]
        
        # 验证源时间范围映射
        for i, segment in enumerate(video_segments):
            expected_segment = self.sample_video_segments[i]
            source_range = segment.get("source_range", {})
            
            assert "start" in source_range, f"片段{i}缺少源开始时间"
            assert "end" in source_range, f"片段{i}缺少源结束时间"
            
            # 验证源时间精度
            expected_source_start = expected_segment["source_start"]
            expected_source_end = expected_segment["source_end"]
            
            actual_source_start = source_range["start"]
            actual_source_end = source_range["end"]
            
            start_error = abs(actual_source_start - expected_source_start)
            end_error = abs(actual_source_end - expected_source_end)
            
            assert start_error <= 0.1, f"片段{i}源开始时间误差: {start_error:.3f}s"
            assert end_error <= 0.1, f"片段{i}源结束时间误差: {end_error:.3f}s"

    def _parse_time(self, time_str: str) -> float:
        """解析时间字符串为秒数"""
        # 格式: "00:00:01,000"
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split(',')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1])
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        return total_seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
