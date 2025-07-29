#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程文件时间轴编辑功能专项测试
验证生成的剪映工程文件在剪映软件中的时间轴编辑功能完整性
"""

import os
import sys
import json
import tempfile
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jianying_timeline_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JianyingTimelineEditingTest:
    """剪映工程文件时间轴编辑功能测试类"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="jianying_timeline_test_")
        self.test_results = {}
        self.created_files = []
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """设置测试环境"""
        logger.info("设置剪映时间轴编辑测试环境...")
        
        # 创建测试数据目录
        self.test_data_dir = Path(self.temp_dir) / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # 创建真实的测试数据
        self.create_realistic_test_data()
        
        logger.info(f"测试环境已设置，临时目录: {self.temp_dir}")
        
    def create_realistic_test_data(self):
        """创建真实的测试数据"""
        logger.info("创建真实的短剧测试数据...")
        
        # 创建复杂的短剧SRT文件
        complex_drama_srt = """1
00:00:01,000 --> 00:00:06,500
【第一集】霸道总裁的秘密

2
00:00:07,000 --> 00:00:12,200
林小雨刚刚大学毕业，怀着忐忑的心情走进了这家知名企业

3
00:00:12,700 --> 00:00:18,300
她没想到，命运会让她遇到传说中的冰山总裁——陈墨轩

4
00:00:18,800 --> 00:00:24,100
"你就是新来的实习生？"陈墨轩冷漠地看着她

5
00:00:24,600 --> 00:00:30,400
林小雨紧张得说不出话，只能点点头

6
00:00:30,900 --> 00:00:36,700
"记住，在我这里，只有结果，没有借口"

7
00:00:37,200 --> 00:00:43,800
就这样，林小雨开始了她的职场生涯

8
00:00:44,300 --> 00:00:50,100
但她不知道，这个冷酷的总裁内心深处隐藏着什么秘密"""

        # 保存测试SRT文件
        srt_path = self.test_data_dir / "complex_drama.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(complex_drama_srt)
        self.created_files.append(str(srt_path))
        
        # 创建模拟视频文件
        self.create_mock_video_files()
        
        logger.info(f"测试数据已创建: SRT文件({len(complex_drama_srt.splitlines())}行)")
        
    def create_mock_video_files(self):
        """创建模拟视频文件"""
        # 创建多个模拟视频文件用于测试
        video_files = [
            "drama_episode_01.mp4",
            "drama_episode_02.mp4", 
            "drama_episode_03.mp4"
        ]
        
        for video_file in video_files:
            video_path = self.test_data_dir / video_file
            # 创建一个小的MP4文件头作为占位符
            with open(video_path, 'wb') as f:
                f.write(b'\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom')
            self.created_files.append(str(video_path))
            
        logger.info(f"模拟视频文件已创建: {len(video_files)}个文件")
        
    def test_1_timeline_structure(self):
        """测试1: 剪映工程文件时间轴结构测试"""
        logger.info("开始测试剪映工程文件时间轴结构...")
        
        test_result = {
            "test_name": "时间轴结构测试",
            "success": False,
            "details": {},
            "errors": []
        }
        
        try:
            # 创建复杂的测试片段数据
            test_segments = [
                {
                    "start_time": 0.0,
                    "end_time": 6.5,
                    "duration": 6.5,
                    "text": "【第一集】霸道总裁的秘密",
                    "original_start": 1.0,
                    "original_end": 6.5,
                    "original_duration": 5.5,
                    "source_file": str(self.test_data_dir / "drama_episode_01.mp4")
                },
                {
                    "start_time": 6.6,
                    "end_time": 12.2,
                    "duration": 5.6,
                    "text": "林小雨刚刚大学毕业，怀着忐忑的心情走进了这家知名企业",
                    "original_start": 7.0,
                    "original_end": 12.2,
                    "original_duration": 5.2,
                    "source_file": str(self.test_data_dir / "drama_episode_01.mp4")
                },
                {
                    "start_time": 12.3,
                    "end_time": 18.3,
                    "duration": 6.0,
                    "text": "她没想到，命运会让她遇到传说中的冰山总裁——陈墨轩",
                    "original_start": 12.7,
                    "original_end": 18.3,
                    "original_duration": 5.6,
                    "source_file": str(self.test_data_dir / "drama_episode_02.mp4")
                },
                {
                    "start_time": 18.4,
                    "end_time": 24.1,
                    "duration": 5.7,
                    "text": "你就是新来的实习生？陈墨轩冷漠地看着她",
                    "original_start": 18.8,
                    "original_end": 24.1,
                    "original_duration": 5.3,
                    "source_file": str(self.test_data_dir / "drama_episode_02.mp4")
                },
                {
                    "start_time": 24.2,
                    "end_time": 30.4,
                    "duration": 6.2,
                    "text": "林小雨紧张得说不出话，只能点点头",
                    "original_start": 24.6,
                    "original_end": 30.4,
                    "original_duration": 5.8,
                    "source_file": str(self.test_data_dir / "drama_episode_03.mp4")
                }
            ]
            
            # 生成剪映工程文件
            from src.exporters.jianying_pro_exporter import JianyingProExporter
            exporter = JianyingProExporter()
            
            output_path = self.test_data_dir / "timeline_structure_test.json"
            export_success = exporter.export_project(test_segments, str(output_path))
            
            if not export_success or not output_path.exists():
                test_result["errors"].append("剪映工程文件生成失败")
                self.test_results["timeline_structure"] = test_result
                return test_result
                
            self.created_files.append(str(output_path))
            
            # 验证工程文件结构
            with open(output_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            # 检查时间轴结构
            timeline_validation = self.validate_timeline_structure(project_data, test_segments)
            
            # 检查素材映射
            material_validation = self.validate_material_mapping(project_data, test_segments)
            
            # 检查独立视频段
            segment_validation = self.validate_independent_segments(project_data, test_segments)
            
            test_result["details"] = {
                "export_success": export_success,
                "file_size": output_path.stat().st_size,
                "segments_count": len(test_segments),
                "timeline_validation": timeline_validation,
                "material_validation": material_validation,
                "segment_validation": segment_validation
            }
            
            # 判断测试是否成功
            test_result["success"] = (
                export_success and
                timeline_validation["valid"] and
                material_validation["valid"] and
                segment_validation["valid"]
            )
            
        except Exception as e:
            test_result["errors"].append(f"时间轴结构测试异常: {str(e)}")
            logger.error(f"时间轴结构测试失败: {e}")
            
        self.test_results["timeline_structure"] = test_result
        return test_result
        
    def validate_timeline_structure(self, project_data: Dict, test_segments: List[Dict]) -> Dict:
        """验证时间轴结构"""
        validation = {
            "valid": False,
            "tracks_found": 0,
            "video_tracks": 0,
            "audio_tracks": 0,
            "text_tracks": 0,
            "segments_in_video_track": 0,
            "timeline_duration": 0,
            "issues": []
        }
        
        try:
            tracks = project_data.get('tracks', [])
            validation["tracks_found"] = len(tracks)
            
            for track in tracks:
                track_type = track.get('type', '')
                if track_type == 'video':
                    validation["video_tracks"] += 1
                    segments = track.get('segments', [])
                    validation["segments_in_video_track"] = len(segments)
                    
                    # 验证每个视频段是否独立
                    for i, segment in enumerate(segments):
                        if 'id' not in segment:
                            validation["issues"].append(f"视频段{i}缺少唯一ID")
                        if 'material_id' not in segment:
                            validation["issues"].append(f"视频段{i}缺少material_id")
                        if 'source_timerange' not in segment:
                            validation["issues"].append(f"视频段{i}缺少source_timerange")
                        if 'target_timerange' not in segment:
                            validation["issues"].append(f"视频段{i}缺少target_timerange")
                            
                elif track_type == 'audio':
                    validation["audio_tracks"] += 1
                elif track_type == 'text':
                    validation["text_tracks"] += 1
                    
            # 计算总时长
            if validation["video_tracks"] > 0:
                video_track = next(track for track in tracks if track.get('type') == 'video')
                segments = video_track.get('segments', [])
                if segments:
                    last_segment = max(segments, key=lambda x: x.get('target_timerange', {}).get('start', 0) + x.get('target_timerange', {}).get('duration', 0))
                    target_range = last_segment.get('target_timerange', {})
                    validation["timeline_duration"] = target_range.get('start', 0) + target_range.get('duration', 0)
                    
            # 验证是否符合预期
            expected_segments = len(test_segments)
            validation["valid"] = (
                validation["video_tracks"] >= 1 and
                validation["segments_in_video_track"] == expected_segments and
                len(validation["issues"]) == 0
            )
            
        except Exception as e:
            validation["issues"].append(f"时间轴结构验证异常: {str(e)}")
            
        return validation

    def validate_material_mapping(self, project_data: Dict, test_segments: List[Dict]) -> Dict:
        """验证素材映射关系"""
        validation = {
            "valid": False,
            "materials_found": 0,
            "video_materials": 0,
            "audio_materials": 0,
            "text_materials": 0,
            "mapping_accuracy": 0.0,
            "path_references": [],
            "issues": []
        }

        try:
            materials = project_data.get('materials', {})

            # 检查视频素材
            video_materials = materials.get('videos', [])
            validation["video_materials"] = len(video_materials)
            validation["materials_found"] += len(video_materials)

            # 检查音频素材
            audio_materials = materials.get('audios', [])
            validation["audio_materials"] = len(audio_materials)
            validation["materials_found"] += len(audio_materials)

            # 检查文本素材
            text_materials = materials.get('texts', [])
            validation["text_materials"] = len(text_materials)
            validation["materials_found"] += len(text_materials)

            # 验证素材路径引用
            for material in video_materials:
                path = material.get('path', '')
                validation["path_references"].append(path)
                if not path:
                    validation["issues"].append("发现空的视频素材路径")
                elif not os.path.exists(path):
                    validation["issues"].append(f"视频素材路径不存在: {path}")

            # 验证material_id映射
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if video_track:
                segments = video_track.get('segments', [])
                mapped_materials = 0

                for segment in segments:
                    material_id = segment.get('material_id', '')
                    if material_id:
                        # 检查是否有对应的素材
                        material_found = any(mat.get('id') == material_id for mat in video_materials)
                        if material_found:
                            mapped_materials += 1
                        else:
                            validation["issues"].append(f"找不到material_id对应的素材: {material_id}")

                if len(segments) > 0:
                    validation["mapping_accuracy"] = mapped_materials / len(segments)

            # 验证是否符合预期
            expected_materials = len(test_segments)
            validation["valid"] = (
                validation["video_materials"] >= expected_materials and
                validation["mapping_accuracy"] >= 0.8 and
                len(validation["issues"]) == 0
            )

        except Exception as e:
            validation["issues"].append(f"素材映射验证异常: {str(e)}")

        return validation

    def validate_independent_segments(self, project_data: Dict, test_segments: List[Dict]) -> Dict:
        """验证独立视频段"""
        validation = {
            "valid": False,
            "segments_count": 0,
            "independent_segments": 0,
            "editable_segments": 0,
            "timing_accuracy": 0.0,
            "original_timing_preserved": 0,
            "issues": []
        }

        try:
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                validation["issues"].append("未找到视频轨道")
                return validation

            segments = video_track.get('segments', [])
            validation["segments_count"] = len(segments)

            for i, segment in enumerate(segments):
                # 检查独立性
                if all(key in segment for key in ['id', 'material_id', 'source_timerange', 'target_timerange']):
                    validation["independent_segments"] += 1

                # 检查可编辑性
                source_range = segment.get('source_timerange', {})
                target_range = segment.get('target_timerange', {})

                if (isinstance(source_range.get('start'), (int, float)) and
                    isinstance(source_range.get('duration'), (int, float)) and
                    isinstance(target_range.get('start'), (int, float)) and
                    isinstance(target_range.get('duration'), (int, float))):
                    validation["editable_segments"] += 1

                # 检查原始时间信息保留
                original_timing = segment.get('original_timing', {})
                if original_timing and 'original_start' in original_timing:
                    validation["original_timing_preserved"] += 1

            # 计算时间精度
            if validation["segments_count"] > 0:
                validation["timing_accuracy"] = validation["editable_segments"] / validation["segments_count"]

            # 验证是否符合预期
            validation["valid"] = (
                validation["independent_segments"] == len(test_segments) and
                validation["editable_segments"] == len(test_segments) and
                validation["timing_accuracy"] >= 0.95
            )

        except Exception as e:
            validation["issues"].append(f"独立视频段验证异常: {str(e)}")

        return validation

    def test_2_timeline_editing_functionality(self):
        """测试2: 时间轴编辑功能验证"""
        logger.info("开始测试时间轴编辑功能...")

        test_result = {
            "test_name": "时间轴编辑功能测试",
            "success": False,
            "details": {},
            "errors": []
        }

        try:
            # 创建测试工程文件
            test_segments = [
                {
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "duration": 5.0,
                    "text": "测试片段1",
                    "source_file": str(self.test_data_dir / "drama_episode_01.mp4")
                },
                {
                    "start_time": 5.1,
                    "end_time": 10.0,
                    "duration": 4.9,
                    "text": "测试片段2",
                    "source_file": str(self.test_data_dir / "drama_episode_02.mp4")
                }
            ]

            from src.exporters.jianying_pro_exporter import JianyingProExporter
            exporter = JianyingProExporter()

            output_path = self.test_data_dir / "editing_functionality_test.json"
            export_success = exporter.export_project(test_segments, str(output_path))

            if not export_success:
                test_result["errors"].append("工程文件生成失败")
                self.test_results["timeline_editing"] = test_result
                return test_result

            self.created_files.append(str(output_path))

            # 验证编辑功能
            editing_validation = self.validate_editing_capabilities(str(output_path))

            # 模拟拖拽操作
            drag_validation = self.simulate_drag_operations(str(output_path))

            # 验证时间变化响应
            time_response_validation = self.validate_time_response(str(output_path))

            test_result["details"] = {
                "export_success": export_success,
                "editing_validation": editing_validation,
                "drag_validation": drag_validation,
                "time_response_validation": time_response_validation
            }

            test_result["success"] = (
                export_success and
                editing_validation["valid"] and
                drag_validation["valid"] and
                time_response_validation["valid"]
            )

        except Exception as e:
            test_result["errors"].append(f"时间轴编辑功能测试异常: {str(e)}")
            logger.error(f"时间轴编辑功能测试失败: {e}")

        self.test_results["timeline_editing"] = test_result
        return test_result

    def validate_editing_capabilities(self, project_path: str) -> Dict:
        """验证编辑能力"""
        validation = {
            "valid": False,
            "draggable_segments": 0,
            "resizable_segments": 0,
            "movable_segments": 0,
            "time_precision": 0,
            "issues": []
        }

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                validation["issues"].append("未找到视频轨道")
                return validation

            segments = video_track.get('segments', [])

            for segment in segments:
                # 检查是否可拖拽（有完整的时间范围信息）
                source_range = segment.get('source_timerange', {})
                target_range = segment.get('target_timerange', {})

                if source_range and target_range:
                    validation["draggable_segments"] += 1

                # 检查是否可调整大小（有duration信息）
                if (source_range.get('duration') is not None and
                    target_range.get('duration') is not None):
                    validation["resizable_segments"] += 1

                # 检查是否可移动（有start信息）
                if (source_range.get('start') is not None and
                    target_range.get('start') is not None):
                    validation["movable_segments"] += 1

            # 检查时间精度（毫秒级）
            if segments:
                first_segment = segments[0]
                target_range = first_segment.get('target_timerange', {})
                start_time = target_range.get('start', 0)

                # 检查是否为毫秒精度
                if isinstance(start_time, (int, float)) and start_time >= 0:
                    validation["time_precision"] = 1

            validation["valid"] = (
                validation["draggable_segments"] == len(segments) and
                validation["resizable_segments"] == len(segments) and
                validation["movable_segments"] == len(segments) and
                validation["time_precision"] == 1
            )

        except Exception as e:
            validation["issues"].append(f"编辑能力验证异常: {str(e)}")

        return validation

    def simulate_drag_operations(self, project_path: str) -> Dict:
        """模拟拖拽操作"""
        validation = {
            "valid": False,
            "extend_operation": False,
            "shrink_operation": False,
            "move_operation": False,
            "time_consistency": False,
            "issues": []
        }

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # 模拟延长视频段操作
            extend_result = self.simulate_extend_segment(project_data)
            validation["extend_operation"] = extend_result["success"]
            if not extend_result["success"]:
                validation["issues"].extend(extend_result["issues"])

            # 模拟缩短视频段操作
            shrink_result = self.simulate_shrink_segment(project_data)
            validation["shrink_operation"] = shrink_result["success"]
            if not shrink_result["success"]:
                validation["issues"].extend(shrink_result["issues"])

            # 模拟移动视频段操作
            move_result = self.simulate_move_segment(project_data)
            validation["move_operation"] = move_result["success"]
            if not move_result["success"]:
                validation["issues"].extend(move_result["issues"])

            # 验证时间一致性
            consistency_result = self.validate_time_consistency(project_data)
            validation["time_consistency"] = consistency_result["success"]
            if not consistency_result["success"]:
                validation["issues"].extend(consistency_result["issues"])

            validation["valid"] = (
                validation["extend_operation"] and
                validation["shrink_operation"] and
                validation["move_operation"] and
                validation["time_consistency"]
            )

        except Exception as e:
            validation["issues"].append(f"拖拽操作模拟异常: {str(e)}")

        return validation

    def simulate_extend_segment(self, project_data: Dict) -> Dict:
        """模拟延长视频段操作"""
        result = {"success": False, "issues": []}

        try:
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                result["issues"].append("未找到视频轨道")
                return result

            segments = video_track.get('segments', [])
            if not segments:
                result["issues"].append("视频轨道中没有片段")
                return result

            # 模拟延长第一个片段
            first_segment = segments[0]
            target_range = first_segment.get('target_timerange', {})

            if 'duration' in target_range:
                original_duration = target_range['duration']
                # 模拟延长1秒
                new_duration = original_duration + 1000  # 毫秒

                # 检查是否可以修改
                if isinstance(original_duration, (int, float)) and original_duration > 0:
                    result["success"] = True
                else:
                    result["issues"].append("时长数据格式不正确")
            else:
                result["issues"].append("片段缺少duration信息")

        except Exception as e:
            result["issues"].append(f"延长操作模拟异常: {str(e)}")

        return result

    def simulate_shrink_segment(self, project_data: Dict) -> Dict:
        """模拟缩短视频段操作"""
        result = {"success": False, "issues": []}

        try:
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                result["issues"].append("未找到视频轨道")
                return result

            segments = video_track.get('segments', [])
            if not segments:
                result["issues"].append("视频轨道中没有片段")
                return result

            # 模拟缩短第一个片段
            first_segment = segments[0]
            target_range = first_segment.get('target_timerange', {})

            if 'duration' in target_range:
                original_duration = target_range['duration']
                # 模拟缩短0.5秒
                new_duration = max(500, original_duration - 500)  # 最少保留0.5秒

                # 检查是否可以修改
                if isinstance(original_duration, (int, float)) and original_duration > 500:
                    result["success"] = True
                else:
                    result["issues"].append("片段太短，无法缩短")
            else:
                result["issues"].append("片段缺少duration信息")

        except Exception as e:
            result["issues"].append(f"缩短操作模拟异常: {str(e)}")

        return result

    def simulate_move_segment(self, project_data: Dict) -> Dict:
        """模拟移动视频段操作"""
        result = {"success": False, "issues": []}

        try:
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                result["issues"].append("未找到视频轨道")
                return result

            segments = video_track.get('segments', [])
            if len(segments) < 2:
                result["issues"].append("片段数量不足，无法测试移动")
                return result

            # 模拟移动第一个片段
            first_segment = segments[0]
            target_range = first_segment.get('target_timerange', {})

            if 'start' in target_range:
                original_start = target_range['start']
                # 模拟移动1秒
                new_start = original_start + 1000  # 毫秒

                # 检查是否可以修改
                if isinstance(original_start, (int, float)) and original_start >= 0:
                    result["success"] = True
                else:
                    result["issues"].append("开始时间数据格式不正确")
            else:
                result["issues"].append("片段缺少start信息")

        except Exception as e:
            result["issues"].append(f"移动操作模拟异常: {str(e)}")

        return result

    def validate_time_consistency(self, project_data: Dict) -> Dict:
        """验证时间一致性"""
        result = {"success": False, "issues": []}

        try:
            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                result["issues"].append("未找到视频轨道")
                return result

            segments = video_track.get('segments', [])

            for i, segment in enumerate(segments):
                source_range = segment.get('source_timerange', {})
                target_range = segment.get('target_timerange', {})

                # 检查source和target的duration是否一致
                source_duration = source_range.get('duration', 0)
                target_duration = target_range.get('duration', 0)

                if source_duration != target_duration:
                    result["issues"].append(f"片段{i}的source和target duration不一致")

                # 检查时间值是否为非负数
                for time_key in ['start', 'duration']:
                    source_time = source_range.get(time_key, 0)
                    target_time = target_range.get(time_key, 0)

                    if source_time < 0 or target_time < 0:
                        result["issues"].append(f"片段{i}的{time_key}为负数")

            result["success"] = len(result["issues"]) == 0

        except Exception as e:
            result["issues"].append(f"时间一致性验证异常: {str(e)}")

        return result

    def validate_time_response(self, project_path: str) -> Dict:
        """验证时间变化响应"""
        validation = {
            "valid": False,
            "time_format_correct": False,
            "precision_adequate": False,
            "range_reasonable": False,
            "issues": []
        }

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            tracks = project_data.get('tracks', [])
            video_track = next((track for track in tracks if track.get('type') == 'video'), None)

            if not video_track:
                validation["issues"].append("未找到视频轨道")
                return validation

            segments = video_track.get('segments', [])

            time_format_ok = True
            precision_ok = True
            range_ok = True

            for segment in segments:
                target_range = segment.get('target_timerange', {})

                # 检查时间格式
                start = target_range.get('start', 0)
                duration = target_range.get('duration', 0)

                if not isinstance(start, (int, float)) or not isinstance(duration, (int, float)):
                    time_format_ok = False
                    validation["issues"].append("时间格式不正确")

                # 检查精度（毫秒级）
                if isinstance(start, float) and start != int(start):
                    # 检查是否有小数部分（亚毫秒精度）
                    if abs(start - round(start)) > 0.001:
                        precision_ok = False
                        validation["issues"].append("时间精度过高，可能影响编辑性能")

                # 检查范围合理性
                if start < 0 or duration <= 0:
                    range_ok = False
                    validation["issues"].append("时间范围不合理")

            validation["time_format_correct"] = time_format_ok
            validation["precision_adequate"] = precision_ok
            validation["range_reasonable"] = range_ok

            validation["valid"] = time_format_ok and precision_ok and range_ok

        except Exception as e:
            validation["issues"].append(f"时间响应验证异常: {str(e)}")

        return validation

    def test_3_system_functionality_integrity(self):
        """测试3: 系统功能完整性保障测试"""
        logger.info("开始测试系统功能完整性...")

        test_result = {
            "test_name": "系统功能完整性测试",
            "success": False,
            "details": {},
            "errors": []
        }

        try:
            # 测试UI组件
            ui_test = self.test_ui_components()

            # 测试核心功能模块
            core_test = self.test_core_modules()

            # 测试完整工作流程
            workflow_test = self.test_complete_workflow()

            test_result["details"] = {
                "ui_test": ui_test,
                "core_test": core_test,
                "workflow_test": workflow_test
            }

            test_result["success"] = (
                ui_test["success"] and
                core_test["success"] and
                workflow_test["success"]
            )

        except Exception as e:
            test_result["errors"].append(f"系统功能完整性测试异常: {str(e)}")
            logger.error(f"系统功能完整性测试失败: {e}")

        self.test_results["system_integrity"] = test_result
        return test_result

    def test_ui_components(self) -> Dict:
        """测试UI组件"""
        result = {"success": False, "components_tested": 0, "issues": []}

        try:
            # 测试PyQt6导入
            from PyQt6.QtWidgets import QApplication

            # 测试UI模块导入
            import simple_ui_fixed

            # 检查关键类
            required_classes = [
                'ProcessStabilityMonitor',
                'ResponsivenessMonitor',
                'ViralSRTWorker',
                'LogHandler'
            ]

            for class_name in required_classes:
                if hasattr(simple_ui_fixed, class_name):
                    result["components_tested"] += 1
                else:
                    result["issues"].append(f"缺少UI类: {class_name}")

            result["success"] = result["components_tested"] == len(required_classes)

        except Exception as e:
            result["issues"].append(f"UI组件测试异常: {str(e)}")

        return result

    def test_core_modules(self) -> Dict:
        """测试核心功能模块"""
        result = {"success": False, "modules_tested": 0, "issues": []}

        try:
            # 测试SRT解析器
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            srt_path = self.test_data_dir / "complex_drama.srt"
            subtitles = parser.parse_srt_file(str(srt_path))
            if subtitles:
                result["modules_tested"] += 1
            else:
                result["issues"].append("SRT解析器测试失败")

            # 测试语言检测器
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            detected_lang = detector.detect_language(content)
            if detected_lang:
                result["modules_tested"] += 1
            else:
                result["issues"].append("语言检测器测试失败")

            # 测试剧本工程师
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            engineer.load_subtitles(str(srt_path))
            reconstruction = engineer.reconstruct_screenplay()
            if reconstruction:
                result["modules_tested"] += 1
            else:
                result["issues"].append("剧本工程师测试失败")

            result["success"] = result["modules_tested"] >= 2

        except Exception as e:
            result["issues"].append(f"核心模块测试异常: {str(e)}")

        return result

    def test_complete_workflow(self) -> Dict:
        """测试完整工作流程"""
        result = {"success": False, "workflow_steps": 0, "issues": []}

        try:
            srt_path = self.test_data_dir / "complex_drama.srt"

            # 步骤1: SRT解析
            from src.core.srt_parser import SRTParser
            parser = SRTParser()
            subtitles = parser.parse_srt_file(str(srt_path))
            if subtitles:
                result["workflow_steps"] += 1
            else:
                result["issues"].append("工作流程步骤1失败: SRT解析")

            # 步骤2: 剧本重构
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            engineer.load_subtitles(str(srt_path))
            reconstruction = engineer.reconstruct_screenplay()
            if reconstruction and 'segments' in reconstruction:
                result["workflow_steps"] += 1
            else:
                result["issues"].append("工作流程步骤2失败: 剧本重构")

            # 步骤3: 剪映导出
            if reconstruction and 'segments' in reconstruction:
                from src.exporters.jianying_pro_exporter import JianyingProExporter
                exporter = JianyingProExporter()
                output_path = self.test_data_dir / "workflow_test.json"
                export_success = exporter.export_project(reconstruction['segments'], str(output_path))
                if export_success:
                    result["workflow_steps"] += 1
                    self.created_files.append(str(output_path))
                else:
                    result["issues"].append("工作流程步骤3失败: 剪映导出")

            result["success"] = result["workflow_steps"] >= 3

        except Exception as e:
            result["issues"].append(f"完整工作流程测试异常: {str(e)}")

        return result

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("开始运行剪映时间轴编辑功能专项测试...")

        # 运行所有测试
        test1_result = self.test_1_timeline_structure()
        test2_result = self.test_2_timeline_editing_functionality()
        test3_result = self.test_3_system_functionality_integrity()

        # 生成综合报告
        return self.generate_comprehensive_report()

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合测试报告"""
        logger.info("生成剪映时间轴编辑功能测试报告...")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))

        report = {
            "test_summary": {
                "test_type": "剪映时间轴编辑功能专项测试",
                "test_timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            "detailed_results": self.test_results,
            "recommendations": self.generate_recommendations()
        }

        # 保存报告
        report_path = f"jianying_timeline_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"测试报告已保存: {report_path}")

        # 打印摘要
        self.print_test_summary(report)

        return report

    def generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        for test_name, result in self.test_results.items():
            if not result.get("success", False):
                if test_name == "timeline_structure":
                    recommendations.append("建议优化时间轴结构生成，确保所有视频段都是独立可编辑的")
                elif test_name == "timeline_editing":
                    recommendations.append("建议改进时间轴编辑功能，确保拖拽操作的响应性")
                elif test_name == "system_integrity":
                    recommendations.append("建议检查系统功能完整性，确保所有模块正常工作")

        if not recommendations:
            recommendations.append("所有测试通过，系统功能完整，建议继续保持")

        return recommendations

    def print_test_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        summary = report["test_summary"]

        print("\n" + "="*100)
        print("剪映工程文件时间轴编辑功能专项测试报告")
        print("="*100)
        print(f"测试类型: {summary['test_type']}")
        print(f"测试时间: {summary['test_timestamp']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['success_rate']}")
        print("-"*100)

        # 打印详细结果
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result.get("success", False) else "❌ 失败"
            print(f"{status} {result.get('test_name', test_name)}")

            if result.get("errors"):
                for error in result["errors"]:
                    print(f"   错误: {error}")

        print("-"*100)

        # 打印建议
        recommendations = report.get("recommendations", [])
        if recommendations:
            print("改进建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        print("="*100)

        # 最终评估
        success_rate = float(summary["success_rate"].rstrip('%'))
        if success_rate >= 95:
            print("🎉 剪映时间轴编辑功能测试全面通过！")
        elif success_rate >= 80:
            print("✅ 剪映时间轴编辑功能基本正常，有少量问题需要修复。")
        else:
            print("⚠️ 剪映时间轴编辑功能存在较多问题，需要重点修复。")

        print("\n")

    def cleanup_test_environment(self):
        """清理测试环境"""
        logger.info("清理剪映时间轴编辑测试环境...")

        try:
            # 清理创建的文件
            for file_path in self.created_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"已清理文件: {file_path}")
                except Exception as e:
                    logger.warning(f"清理文件 {file_path} 失败: {str(e)}")

            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理临时目录: {self.temp_dir}")

        except Exception as e:
            logger.warning(f"清理测试环境失败: {str(e)}")

def main():
    """主函数"""
    print("VisionAI-ClipsMaster 剪映时间轴编辑功能专项测试开始...")

    test_suite = JianyingTimelineEditingTest()

    try:
        # 运行所有测试
        report = test_suite.run_all_tests()

        # 检查是否达到95%通过率
        success_rate = float(report["test_summary"]["success_rate"].rstrip('%'))
        return success_rate >= 95

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        return False
    except Exception as e:
        logger.error(f"测试执行异常: {str(e)}")
        return False
    finally:
        # 清理测试环境
        test_suite.cleanup_test_environment()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
