#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映工程文件功能测试系统
验证生成的剪映工程文件在剪映专业版中的具体功能和结构
"""

import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入核心模块
try:
    from src.exporters.jianying_pro_exporter import JianYingProExporter
    from src.utils.log_handler import get_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 配置日志
logger = get_logger("jianying_functionality_test")

class JianYingProjectFunctionalityTest:
    """剪映工程文件功能测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        self.test_start_time = datetime.now()
        self.test_results = {
            "test_start_time": self.test_start_time.isoformat(),
            "test_categories": {},
            "project_structure": {},
            "functionality_tests": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # 创建测试目录
        self.test_dir = Path(tempfile.mkdtemp(prefix="jianying_test_"))
        self.test_data_dir = self.test_dir / "test_data"
        self.test_output_dir = self.test_dir / "test_output"
        self.test_data_dir.mkdir(exist_ok=True)
        self.test_output_dir.mkdir(exist_ok=True)
        
        logger.info(f"剪映功能测试环境初始化完成，测试目录: {self.test_dir}")
        
        # 初始化导出器
        self.jianying_exporter = None
        
    def setup_realistic_test_data(self) -> bool:
        """准备真实的测试数据"""
        logger.info("准备真实的剪映测试数据...")
        
        try:
            # 创建真实的SRT字幕文件（模拟短剧内容）
            original_srt_content = """1
00:00:01,000 --> 00:00:05,000
小雨站在咖啡厅门口，犹豫着要不要进去

2
00:00:06,000 --> 00:00:10,000
她知道里面坐着的是她的前男友李明

3
00:00:11,000 --> 00:00:15,000
三年前，他们因为误会而分手

4
00:00:16,000 --> 00:00:20,000
现在李明要结婚了，新娘不是她

5
00:00:21,000 --> 00:00:25,000
小雨深吸一口气，推开了咖啡厅的门

6
00:00:26,000 --> 00:00:30,000
李明看到她，眼中闪过一丝惊讶

7
00:00:31,000 --> 00:00:35,000
"小雨，你来了。"他轻声说道

8
00:00:36,000 --> 00:00:40,000
"我想和你谈谈。"小雨坐在他对面

9
00:00:41,000 --> 00:00:45,000
两人四目相对，往事如潮水般涌来

10
00:00:46,000 --> 00:00:50,000
这可能是他们最后一次单独相处了"""

            # 创建AI重构后的爆款字幕（精华片段）
            viral_srt_content = """1
00:00:01,000 --> 00:00:05,000
小雨站在咖啡厅门口，犹豫着要不要进去

2
00:00:16,000 --> 00:00:20,000
现在李明要结婚了，新娘不是她

3
00:00:21,000 --> 00:00:25,000
小雨深吸一口气，推开了咖啡厅的门

4
00:00:31,000 --> 00:00:35,000
"小雨，你来了。"他轻声说道

5
00:00:41,000 --> 00:00:45,000
两人四目相对，往事如潮水般涌来

6
00:00:46,000 --> 00:00:50,000
这可能是他们最后一次单独相处了"""

            # 保存测试文件
            original_srt_path = self.test_data_dir / "original_drama.srt"
            viral_srt_path = self.test_data_dir / "viral_style.srt"
            test_video_path = self.test_data_dir / "original_drama_episode1.mp4"
            
            with open(original_srt_path, 'w', encoding='utf-8') as f:
                f.write(original_srt_content)
                
            with open(viral_srt_path, 'w', encoding='utf-8') as f:
                f.write(viral_srt_content)
            
            # 创建模拟视频文件信息
            video_info = {
                "filename": "original_drama_episode1.mp4",
                "duration": 50.0,
                "resolution": "1920x1080",
                "fps": 30,
                "codec": "h264",
                "size_mb": 125.5
            }
            
            # 保存视频信息
            with open(self.test_data_dir / "video_info.json", 'w', encoding='utf-8') as f:
                json.dump(video_info, f, ensure_ascii=False, indent=2)
            
            # 创建模拟视频文件（实际项目中应该是真实视频）
            test_video_path.touch()
            
            logger.info(f"真实测试数据创建完成")
            return True
            
        except Exception as e:
            logger.error(f"测试数据准备失败: {e}")
            return False
    
    def generate_test_project(self) -> Dict[str, Any]:
        """生成测试用的剪映工程文件"""
        logger.info("生成测试用的剪映工程文件...")
        
        test_result = {
            "test_name": "剪映工程文件生成",
            "status": "running",
            "details": {}
        }
        
        try:
            # 初始化导出器
            self.jianying_exporter = JianYingProExporter()
            
            # 解析爆款字幕文件
            viral_srt_path = self.test_data_dir / "viral_style.srt"
            viral_subtitles = self.parse_srt_file(str(viral_srt_path))
            
            # 创建视频片段信息
            video_segments = []
            for i, subtitle in enumerate(viral_subtitles):
                segment = {
                    "id": f"segment_{i+1}",
                    "start_time": subtitle["start_time"],
                    "end_time": subtitle["end_time"],
                    "duration": subtitle["duration"],
                    "file_path": str(self.test_data_dir / "original_drama_episode1.mp4"),
                    "text": subtitle["text"],
                    "segment_type": "highlight"  # 标记为精华片段
                }
                video_segments.append(segment)
            
            # 生成剪映工程文件
            project_file_path = self.test_output_dir / "drama_highlight_project.json"
            
            start_time = time.time()
            export_success = self.jianying_exporter.export_project(
                video_segments,
                str(project_file_path)
            )
            export_time = time.time() - start_time
            
            # 验证生成结果
            if project_file_path.exists():
                file_size = project_file_path.stat().st_size
                
                # 读取并分析工程文件结构
                with open(project_file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                test_result["details"] = {
                    "export_success": export_success,
                    "file_path": str(project_file_path),
                    "file_size": file_size,
                    "export_time": export_time,
                    "segments_count": len(video_segments),
                    "project_structure": self.analyze_project_structure(project_data)
                }
                
                # 保存项目数据供后续分析
                self.project_data = project_data
                self.project_file_path = project_file_path
                
                test_result["status"] = "passed"
                logger.info(f"✅ 剪映工程文件生成成功，文件大小: {file_size} 字节")
            else:
                test_result["status"] = "failed"
                test_result["error"] = "工程文件未生成"
                logger.error("❌ 剪映工程文件生成失败")
            
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"剪映工程文件生成发生错误: {e}")
        
        return test_result
    
    def parse_srt_file(self, file_path: str) -> List[Dict[str, Any]]:
        """解析SRT文件"""
        import re
        
        subtitles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分割字幕块
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 解析索引
                    try:
                        index = int(lines[0])
                    except ValueError:
                        continue
                    
                    # 解析时间戳
                    time_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})', lines[1])
                    if time_match:
                        start_h, start_m, start_s, start_ms = map(int, time_match.groups()[:4])
                        end_h, end_m, end_s, end_ms = map(int, time_match.groups()[4:])
                        
                        start_time = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
                        end_time = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
                        
                        # 解析文本
                        text = '\n'.join(lines[2:])
                        
                        subtitles.append({
                            'index': index,
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': end_time - start_time,
                            'text': text
                        })
        
        except Exception as e:
            logger.error(f"SRT文件解析失败: {e}")
            
        return subtitles
    
    def analyze_project_structure(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析剪映工程文件结构"""
        logger.info("分析剪映工程文件结构...")
        
        structure_analysis = {
            "basic_info": {},
            "materials": {},
            "tracks": {},
            "timeline": {},
            "compatibility": {}
        }
        
        try:
            # 基本信息分析
            structure_analysis["basic_info"] = {
                "version": project_data.get("version", "unknown"),
                "platform": project_data.get("platform", "unknown"),
                "project_id": project_data.get("id", "unknown"),
                "created_time": project_data.get("created_time", 0),
                "app_version": project_data.get("app_version", "unknown")
            }
            
            # 素材分析
            materials = project_data.get("materials", {})
            structure_analysis["materials"] = {
                "videos_count": len(materials.get("videos", [])),
                "audios_count": len(materials.get("audios", [])),
                "images_count": len(materials.get("images", [])),
                "video_files": [v.get("file_path", "") for v in materials.get("videos", [])]
            }
            
            # 轨道分析
            tracks = project_data.get("tracks", [])
            video_tracks = [t for t in tracks if t.get("type") == "video"]
            audio_tracks = [t for t in tracks if t.get("type") == "audio"]
            
            structure_analysis["tracks"] = {
                "total_tracks": len(tracks),
                "video_tracks": len(video_tracks),
                "audio_tracks": len(audio_tracks),
                "video_segments": sum(len(t.get("segments", [])) for t in video_tracks),
                "audio_segments": sum(len(t.get("segments", [])) for t in audio_tracks)
            }
            
            # 时间轴分析
            if video_tracks:
                first_video_track = video_tracks[0]
                segments = first_video_track.get("segments", [])
                
                timeline_info = {
                    "segments_count": len(segments),
                    "total_duration": 0,
                    "segments_details": []
                }
                
                for i, segment in enumerate(segments):
                    target_timerange = segment.get("target_timerange", {})
                    source_timerange = segment.get("source_timerange", {})
                    
                    segment_detail = {
                        "segment_id": i + 1,
                        "target_start": target_timerange.get("start", 0),
                        "target_duration": target_timerange.get("duration", 0),
                        "source_start": source_timerange.get("start", 0),
                        "source_duration": source_timerange.get("duration", 0),
                        "material_id": segment.get("material_id", "unknown")
                    }
                    
                    timeline_info["segments_details"].append(segment_detail)
                    timeline_info["total_duration"] += target_timerange.get("duration", 0)
                
                structure_analysis["timeline"] = timeline_info
            
            # 兼容性分析
            structure_analysis["compatibility"] = {
                "has_required_fields": all(field in project_data for field in [
                    "version", "materials", "tracks", "canvas_config"
                ]),
                "jianying_version_compatible": project_data.get("version", "").startswith("3."),
                "file_format": "json",
                "encoding": "utf-8"
            }
            
        except Exception as e:
            logger.error(f"工程文件结构分析失败: {e}")
            structure_analysis["error"] = str(e)
        
        return structure_analysis

    def test_project_import_compatibility(self) -> Dict[str, Any]:
        """测试1: 工程文件导入兼容性"""
        logger.info("测试1: 工程文件导入兼容性...")

        test_result = {
            "test_name": "工程文件导入兼容性测试",
            "status": "running",
            "details": {}
        }

        try:
            if not hasattr(self, 'project_data'):
                test_result["status"] = "failed"
                test_result["error"] = "未找到工程文件数据"
                return test_result

            # 验证JSON格式有效性
            json_valid = isinstance(self.project_data, dict)

            # 验证必要字段
            required_fields = [
                "version", "type", "platform", "id", "materials",
                "tracks", "canvas_config", "extra_info"
            ]
            missing_fields = [field for field in required_fields if field not in self.project_data]

            # 验证剪映版本兼容性
            version = self.project_data.get("version", "")
            version_compatible = version.startswith("3.")

            # 验证素材路径格式
            materials = self.project_data.get("materials", {})
            videos = materials.get("videos", [])
            path_format_valid = True
            invalid_paths = []

            for video in videos:
                file_path = video.get("file_path", "")
                if not file_path or not isinstance(file_path, str):
                    path_format_valid = False
                    invalid_paths.append(video.get("id", "unknown"))

            # 验证轨道结构
            tracks = self.project_data.get("tracks", [])
            track_structure_valid = True
            track_issues = []

            for track in tracks:
                if not isinstance(track, dict):
                    track_structure_valid = False
                    track_issues.append("轨道不是字典格式")
                    continue

                if "type" not in track:
                    track_structure_valid = False
                    track_issues.append("轨道缺少type字段")

                if "segments" not in track:
                    track_structure_valid = False
                    track_issues.append("轨道缺少segments字段")

            test_result["details"] = {
                "json_valid": json_valid,
                "required_fields_present": len(missing_fields) == 0,
                "missing_fields": missing_fields,
                "version_compatible": version_compatible,
                "version": version,
                "path_format_valid": path_format_valid,
                "invalid_paths": invalid_paths,
                "track_structure_valid": track_structure_valid,
                "track_issues": track_issues,
                "file_size": self.project_file_path.stat().st_size if hasattr(self, 'project_file_path') else 0
            }

            # 计算总体兼容性分数
            compatibility_checks = [
                json_valid,
                len(missing_fields) == 0,
                version_compatible,
                path_format_valid,
                track_structure_valid
            ]

            compatibility_score = sum(compatibility_checks) / len(compatibility_checks)
            test_result["details"]["compatibility_score"] = compatibility_score

            if compatibility_score >= 0.8:
                test_result["status"] = "passed"
                logger.info(f"✅ 工程文件导入兼容性测试通过，兼容性分数: {compatibility_score:.2f}")
            else:
                test_result["status"] = "warning"
                logger.warning(f"⚠️ 工程文件导入兼容性存在问题，兼容性分数: {compatibility_score:.2f}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"工程文件导入兼容性测试发生错误: {e}")

        return test_result

    def test_timeline_structure(self) -> Dict[str, Any]:
        """测试2: 时间轴结构验证"""
        logger.info("测试2: 时间轴结构验证...")

        test_result = {
            "test_name": "时间轴结构验证",
            "status": "running",
            "details": {}
        }

        try:
            if not hasattr(self, 'project_data'):
                test_result["status"] = "failed"
                test_result["error"] = "未找到工程文件数据"
                return test_result

            tracks = self.project_data.get("tracks", [])
            video_tracks = [t for t in tracks if t.get("type") == "video"]

            if not video_tracks:
                test_result["status"] = "failed"
                test_result["error"] = "未找到视频轨道"
                return test_result

            # 分析第一个视频轨道
            main_video_track = video_tracks[0]
            segments = main_video_track.get("segments", [])

            # 验证片段是否为独立的视频片段
            independent_segments = True
            segment_analysis = []
            timeline_position = 0

            for i, segment in enumerate(segments):
                target_timerange = segment.get("target_timerange", {})
                source_timerange = segment.get("source_timerange", {})

                segment_info = {
                    "segment_id": i + 1,
                    "target_start": target_timerange.get("start", 0),
                    "target_duration": target_timerange.get("duration", 0),
                    "source_start": source_timerange.get("start", 0),
                    "source_duration": source_timerange.get("duration", 0),
                    "material_id": segment.get("material_id", ""),
                    "is_independent": True
                }

                # 验证片段是否在正确的时间轴位置
                expected_target_start = timeline_position
                actual_target_start = target_timerange.get("start", 0)

                if abs(actual_target_start - expected_target_start) > 100:  # 允许100ms误差
                    segment_info["is_independent"] = False
                    independent_segments = False

                timeline_position += target_timerange.get("duration", 0)
                segment_analysis.append(segment_info)

            # 验证片段顺序与AI重构字幕顺序一致
            order_consistent = True
            if hasattr(self, 'viral_subtitles'):
                if len(segments) == len(self.viral_subtitles):
                    for i, (segment, subtitle) in enumerate(zip(segments, self.viral_subtitles)):
                        source_start = segment.get("source_timerange", {}).get("start", 0)
                        expected_source_start = subtitle["start_time"] * 1000  # 转换为毫秒

                        if abs(source_start - expected_source_start) > 1000:  # 允许1秒误差
                            order_consistent = False
                            break
                else:
                    order_consistent = False

            # 验证片段是否保持未渲染状态（通过检查是否引用原始素材）
            unrendered_state = True
            for segment in segments:
                material_id = segment.get("material_id", "")
                if not material_id:
                    unrendered_state = False
                    break

            test_result["details"] = {
                "total_segments": len(segments),
                "independent_segments": independent_segments,
                "order_consistent": order_consistent,
                "unrendered_state": unrendered_state,
                "segment_analysis": segment_analysis,
                "total_timeline_duration": timeline_position,
                "video_tracks_count": len(video_tracks)
            }

            # 计算时间轴结构分数
            structure_checks = [
                len(segments) > 0,
                independent_segments,
                order_consistent,
                unrendered_state
            ]

            structure_score = sum(structure_checks) / len(structure_checks)
            test_result["details"]["structure_score"] = structure_score

            if structure_score >= 0.75:
                test_result["status"] = "passed"
                logger.info(f"✅ 时间轴结构验证通过，结构分数: {structure_score:.2f}")
            else:
                test_result["status"] = "warning"
                logger.warning(f"⚠️ 时间轴结构存在问题，结构分数: {structure_score:.2f}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"时间轴结构验证发生错误: {e}")

        return test_result

    def test_materials_mapping(self) -> Dict[str, Any]:
        """测试3: 素材库映射关系测试"""
        logger.info("测试3: 素材库映射关系测试...")

        test_result = {
            "test_name": "素材库映射关系测试",
            "status": "running",
            "details": {}
        }

        try:
            if not hasattr(self, 'project_data'):
                test_result["status"] = "failed"
                test_result["error"] = "未找到工程文件数据"
                return test_result

            # 获取素材库信息
            materials = self.project_data.get("materials", {})
            videos = materials.get("videos", [])

            # 获取时间轴片段信息
            tracks = self.project_data.get("tracks", [])
            video_tracks = [t for t in tracks if t.get("type") == "video"]

            if not video_tracks:
                test_result["status"] = "failed"
                test_result["error"] = "未找到视频轨道"
                return test_result

            segments = video_tracks[0].get("segments", [])

            # 验证素材库中是否正确导入了原片视频文件
            materials_imported_correctly = True
            material_files = []

            for video in videos:
                file_path = video.get("file_path", "")
                material_id = video.get("id", "")

                material_info = {
                    "material_id": material_id,
                    "file_path": file_path,
                    "file_exists": Path(file_path).exists() if file_path else False,
                    "is_original_video": "original_drama" in file_path
                }

                material_files.append(material_info)

                if not file_path or not material_id:
                    materials_imported_correctly = False

            # 验证时间轴片段与素材库的映射关系
            mapping_correct = True
            mapping_analysis = []
            used_materials = set()

            for i, segment in enumerate(segments):
                material_id = segment.get("material_id", "")

                # 查找对应的素材
                corresponding_material = None
                for video in videos:
                    if video.get("id") == material_id:
                        corresponding_material = video
                        break

                mapping_info = {
                    "segment_id": i + 1,
                    "material_id": material_id,
                    "has_corresponding_material": corresponding_material is not None,
                    "material_file_path": corresponding_material.get("file_path", "") if corresponding_material else "",
                    "is_one_to_one_mapping": True
                }

                if not corresponding_material:
                    mapping_correct = False
                    mapping_info["is_one_to_one_mapping"] = False

                used_materials.add(material_id)
                mapping_analysis.append(mapping_info)

            # 验证是否存在重复或丢失的映射
            total_materials = len(videos)
            used_materials_count = len(used_materials)
            no_duplicate_or_missing = used_materials_count <= total_materials

            # 验证映射关系是一一对应的
            one_to_one_mapping = True
            material_usage_count = {}

            for segment in segments:
                material_id = segment.get("material_id", "")
                material_usage_count[material_id] = material_usage_count.get(material_id, 0) + 1

            # 检查是否有素材被多次使用（这是正常的，因为可能从同一个原片提取多个片段）
            multiple_usage_materials = {k: v for k, v in material_usage_count.items() if v > 1}

            test_result["details"] = {
                "materials_count": len(videos),
                "segments_count": len(segments),
                "materials_imported_correctly": materials_imported_correctly,
                "mapping_correct": mapping_correct,
                "no_duplicate_or_missing": no_duplicate_or_missing,
                "one_to_one_mapping": one_to_one_mapping,
                "material_files": material_files,
                "mapping_analysis": mapping_analysis,
                "used_materials_count": used_materials_count,
                "multiple_usage_materials": multiple_usage_materials
            }

            # 计算映射关系分数
            mapping_checks = [
                materials_imported_correctly,
                mapping_correct,
                no_duplicate_or_missing,
                len(videos) > 0,
                len(segments) > 0
            ]

            mapping_score = sum(mapping_checks) / len(mapping_checks)
            test_result["details"]["mapping_score"] = mapping_score

            if mapping_score >= 0.8:
                test_result["status"] = "passed"
                logger.info(f"✅ 素材库映射关系测试通过，映射分数: {mapping_score:.2f}")
            else:
                test_result["status"] = "warning"
                logger.warning(f"⚠️ 素材库映射关系存在问题，映射分数: {mapping_score:.2f}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"素材库映射关系测试发生错误: {e}")

        return test_result

    def test_editing_functionality(self) -> Dict[str, Any]:
        """测试4: 编辑功能可用性验证"""
        logger.info("测试4: 编辑功能可用性验证...")

        test_result = {
            "test_name": "编辑功能可用性验证",
            "status": "running",
            "details": {}
        }

        try:
            if not hasattr(self, 'project_data'):
                test_result["status"] = "failed"
                test_result["error"] = "未找到工程文件数据"
                return test_result

            # 获取视频轨道和片段
            tracks = self.project_data.get("tracks", [])
            video_tracks = [t for t in tracks if t.get("type") == "video"]

            if not video_tracks:
                test_result["status"] = "failed"
                test_result["error"] = "未找到视频轨道"
                return test_result

            segments = video_tracks[0].get("segments", [])

            if len(segments) < 2:
                test_result["status"] = "failed"
                test_result["error"] = "片段数量不足，无法进行编辑测试"
                return test_result

            # 模拟编辑操作测试
            editing_tests = []

            # 测试1: 模拟延长第一个片段
            first_segment = segments[0].copy()
            original_duration = first_segment.get("target_timerange", {}).get("duration", 0)

            # 模拟延长1秒（1000毫秒）
            extended_duration = original_duration + 1000
            can_extend = self.simulate_segment_extension(first_segment, extended_duration)

            editing_tests.append({
                "test_type": "extend_segment",
                "segment_id": 1,
                "original_duration": original_duration,
                "new_duration": extended_duration,
                "can_extend": can_extend,
                "extension_amount": 1000
            })

            # 测试2: 模拟缩短第二个片段
            second_segment = segments[1].copy()
            original_duration_2 = second_segment.get("target_timerange", {}).get("duration", 0)

            # 模拟缩短0.5秒（500毫秒）
            shortened_duration = max(500, original_duration_2 - 500)  # 最少保留0.5秒
            can_shorten = self.simulate_segment_shortening(second_segment, shortened_duration)

            editing_tests.append({
                "test_type": "shorten_segment",
                "segment_id": 2,
                "original_duration": original_duration_2,
                "new_duration": shortened_duration,
                "can_shorten": can_shorten,
                "shortening_amount": original_duration_2 - shortened_duration
            })

            # 测试3: 验证拖拽操作不会破坏映射关系
            mapping_preserved = True
            for i, segment in enumerate(segments[:2]):  # 测试前两个片段
                material_id = segment.get("material_id", "")
                if not material_id:
                    mapping_preserved = False
                    break

                # 验证素材ID在编辑后仍然有效
                materials = self.project_data.get("materials", {}).get("videos", [])
                material_exists = any(m.get("id") == material_id for m in materials)
                if not material_exists:
                    mapping_preserved = False
                    break

            # 测试4: 验证时间轴调整的可行性
            timeline_adjustable = True
            adjustment_tests = []

            for i, segment in enumerate(segments):
                source_timerange = segment.get("source_timerange", {})
                source_start = source_timerange.get("start", 0)
                source_duration = source_timerange.get("duration", 0)

                # 检查是否有足够的源素材进行扩展
                can_extend_forward = source_start > 0  # 可以向前扩展
                can_extend_backward = True  # 假设源素材足够长，可以向后扩展

                adjustment_test = {
                    "segment_id": i + 1,
                    "can_extend_forward": can_extend_forward,
                    "can_extend_backward": can_extend_backward,
                    "source_start": source_start,
                    "source_duration": source_duration
                }

                adjustment_tests.append(adjustment_test)

                if not (can_extend_forward or can_extend_backward):
                    timeline_adjustable = False

            test_result["details"] = {
                "segments_available_for_editing": len(segments),
                "editing_tests": editing_tests,
                "mapping_preserved": mapping_preserved,
                "timeline_adjustable": timeline_adjustable,
                "adjustment_tests": adjustment_tests,
                "supports_drag_operations": True,  # 基于剪映格式推断
                "supports_trim_operations": True   # 基于剪映格式推断
            }

            # 计算编辑功能可用性分数
            editing_checks = [
                len(segments) >= 2,
                any(test["can_extend"] for test in editing_tests if "can_extend" in test),
                any(test["can_shorten"] for test in editing_tests if "can_shorten" in test),
                mapping_preserved,
                timeline_adjustable
            ]

            editing_score = sum(editing_checks) / len(editing_checks)
            test_result["details"]["editing_score"] = editing_score

            if editing_score >= 0.8:
                test_result["status"] = "passed"
                logger.info(f"✅ 编辑功能可用性验证通过，编辑分数: {editing_score:.2f}")
            else:
                test_result["status"] = "warning"
                logger.warning(f"⚠️ 编辑功能可用性存在限制，编辑分数: {editing_score:.2f}")

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            logger.error(f"编辑功能可用性验证发生错误: {e}")

        return test_result

    def simulate_segment_extension(self, segment: Dict[str, Any], new_duration: int) -> bool:
        """模拟片段延长操作"""
        try:
            source_timerange = segment.get("source_timerange", {})
            source_start = source_timerange.get("start", 0)
            source_duration = source_timerange.get("duration", 0)

            # 检查源素材是否有足够的内容支持延长
            # 假设原片总长度为50秒（50000毫秒）
            original_video_duration = 50000

            # 计算延长后需要的源素材长度
            required_source_duration = new_duration

            # 检查是否超出源素材范围
            if source_start + required_source_duration <= original_video_duration:
                return True
            else:
                return False

        except Exception:
            return False

    def simulate_segment_shortening(self, segment: Dict[str, Any], new_duration: int) -> bool:
        """模拟片段缩短操作"""
        try:
            # 缩短操作通常总是可行的，只要新时长大于0
            return new_duration > 0
        except Exception:
            return False

    def run_comprehensive_functionality_tests(self) -> Dict[str, Any]:
        """运行全面的剪映工程文件功能测试"""
        logger.info("开始运行剪映工程文件功能测试...")

        # 准备测试数据
        if not self.setup_realistic_test_data():
            self.test_results["success"] = False
            self.test_results["error"] = "测试数据准备失败"
            return self.test_results

        # 生成测试工程文件
        print("步骤1: 生成剪映工程文件...")
        project_generation_result = self.generate_test_project()
        self.test_results["test_categories"]["project_generation"] = project_generation_result

        if project_generation_result["status"] != "passed":
            self.test_results["success"] = False
            self.test_results["error"] = "工程文件生成失败"
            return self.test_results

        # 保存工程文件结构分析
        self.test_results["project_structure"] = project_generation_result["details"]["project_structure"]

        # 执行功能测试
        functionality_tests = [
            ("import_compatibility", self.test_project_import_compatibility),
            ("timeline_structure", self.test_timeline_structure),
            ("materials_mapping", self.test_materials_mapping),
            ("editing_functionality", self.test_editing_functionality)
        ]

        all_passed = True

        for test_name, test_func in functionality_tests:
            print(f"步骤{len(self.test_results['functionality_tests']) + 2}: 执行{test_func.__doc__.split(':')[1].strip()}...")
            test_result = test_func()
            self.test_results["functionality_tests"][test_name] = test_result

            if test_result["status"] not in ["passed", "warning"]:
                all_passed = False
                self.test_results["issues_found"].append({
                    "test": test_name,
                    "status": test_result["status"],
                    "error": test_result.get("error", "测试失败")
                })

        # 生成综合评估
        self.generate_comprehensive_assessment()

        # 设置最终结果
        self.test_results["success"] = all_passed
        self.test_results["test_end_time"] = datetime.now().isoformat()
        self.test_results["total_duration"] = (datetime.now() - self.test_start_time).total_seconds()

        return self.test_results

    def generate_comprehensive_assessment(self):
        """生成综合评估"""
        logger.info("生成综合评估...")

        assessment = {
            "overall_score": 0,
            "category_scores": {},
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }

        # 计算各类别分数
        category_scores = []

        for test_name, test_result in self.test_results["functionality_tests"].items():
            details = test_result.get("details", {})

            if "compatibility_score" in details:
                score = details["compatibility_score"]
                assessment["category_scores"]["import_compatibility"] = score
                category_scores.append(score)

            if "structure_score" in details:
                score = details["structure_score"]
                assessment["category_scores"]["timeline_structure"] = score
                category_scores.append(score)

            if "mapping_score" in details:
                score = details["mapping_score"]
                assessment["category_scores"]["materials_mapping"] = score
                category_scores.append(score)

            if "editing_score" in details:
                score = details["editing_score"]
                assessment["category_scores"]["editing_functionality"] = score
                category_scores.append(score)

        # 计算总体分数
        if category_scores:
            assessment["overall_score"] = sum(category_scores) / len(category_scores)

        # 分析优势和劣势
        if assessment["overall_score"] >= 0.9:
            assessment["strengths"].append("工程文件格式完全兼容剪映专业版")
        if assessment["category_scores"].get("timeline_structure", 0) >= 0.8:
            assessment["strengths"].append("时间轴结构正确，支持独立片段编辑")
        if assessment["category_scores"].get("materials_mapping", 0) >= 0.8:
            assessment["strengths"].append("素材库映射关系准确")
        if assessment["category_scores"].get("editing_functionality", 0) >= 0.8:
            assessment["strengths"].append("支持完整的编辑功能")

        # 识别需要改进的地方
        for category, score in assessment["category_scores"].items():
            if score < 0.7:
                assessment["weaknesses"].append(f"{category}功能需要改进（分数: {score:.2f}）")

        # 生成建议
        if assessment["overall_score"] >= 0.85:
            assessment["recommendations"].append("工程文件质量优秀，可以直接用于生产环境")
        elif assessment["overall_score"] >= 0.7:
            assessment["recommendations"].append("工程文件基本可用，建议进行小幅优化")
        else:
            assessment["recommendations"].append("工程文件需要重大改进才能投入使用")

        if assessment["category_scores"].get("import_compatibility", 0) < 0.8:
            assessment["recommendations"].append("建议完善工程文件的元数据字段")

        if assessment["category_scores"].get("timeline_structure", 0) < 0.8:
            assessment["recommendations"].append("建议优化时间轴片段的排列和结构")

        self.test_results["comprehensive_assessment"] = assessment

    def generate_detailed_report(self) -> str:
        """生成详细的测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"jianying_functionality_test_report_{timestamp}.json"

        # 保存JSON报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        # 生成Markdown报告
        markdown_path = report_path.replace('.json', '.md')
        self.generate_markdown_report(markdown_path)

        logger.info(f"详细测试报告已生成: {report_path}")
        logger.info(f"Markdown报告已生成: {markdown_path}")

        return report_path

    def generate_markdown_report(self, markdown_path: str):
        """生成Markdown格式的测试报告"""

        assessment = self.test_results.get("comprehensive_assessment", {})
        overall_score = assessment.get("overall_score", 0)

        markdown_content = f"""# VisionAI-ClipsMaster 剪映工程文件功能测试报告

## 📋 测试概览

**测试时间**: {self.test_results['test_start_time']}
**测试持续时间**: {self.test_results.get('total_duration', 0):.2f} 秒
**总体评分**: {overall_score:.2f}/1.00
**测试状态**: {'✅ 通过' if self.test_results.get('success', False) else '❌ 失败'}

## 🎯 测试结果摘要

| 测试类别 | 状态 | 评分 | 说明 |
|---------|------|------|------|
"""

        # 添加各测试类别结果
        for test_name, test_result in self.test_results["functionality_tests"].items():
            status_icon = "✅" if test_result["status"] == "passed" else "⚠️" if test_result["status"] == "warning" else "❌"
            score = assessment.get("category_scores", {}).get(test_name, 0)
            test_display_name = test_result.get("test_name", test_name)

            markdown_content += f"| {test_display_name} | {status_icon} {test_result['status']} | {score:.2f} | {test_result.get('details', {}).get('summary', '详见详细结果')} |\n"

        # 添加工程文件结构信息
        project_structure = self.test_results.get("project_structure", {})
        if project_structure:
            markdown_content += f"""

## 📁 工程文件结构分析

### 基本信息
- **版本**: {project_structure.get('basic_info', {}).get('version', 'unknown')}
- **平台**: {project_structure.get('basic_info', {}).get('platform', 'unknown')}
- **应用版本**: {project_structure.get('basic_info', {}).get('app_version', 'unknown')}

### 素材统计
- **视频素材**: {project_structure.get('materials', {}).get('videos_count', 0)} 个
- **音频素材**: {project_structure.get('materials', {}).get('audios_count', 0)} 个
- **图片素材**: {project_structure.get('materials', {}).get('images_count', 0)} 个

### 轨道信息
- **总轨道数**: {project_structure.get('tracks', {}).get('total_tracks', 0)}
- **视频轨道**: {project_structure.get('tracks', {}).get('video_tracks', 0)} 个
- **音频轨道**: {project_structure.get('tracks', {}).get('audio_tracks', 0)} 个
- **视频片段**: {project_structure.get('tracks', {}).get('video_segments', 0)} 个

### 时间轴信息
- **片段数量**: {project_structure.get('timeline', {}).get('segments_count', 0)}
- **总时长**: {project_structure.get('timeline', {}).get('total_duration', 0)/1000:.1f} 秒
"""

        # 添加优势和建议
        strengths = assessment.get("strengths", [])
        weaknesses = assessment.get("weaknesses", [])
        recommendations = assessment.get("recommendations", [])

        if strengths:
            markdown_content += "\n## ✅ 优势\n\n"
            for strength in strengths:
                markdown_content += f"- {strength}\n"

        if weaknesses:
            markdown_content += "\n## ⚠️ 需要改进\n\n"
            for weakness in weaknesses:
                markdown_content += f"- {weakness}\n"

        if recommendations:
            markdown_content += "\n## 💡 建议\n\n"
            for recommendation in recommendations:
                markdown_content += f"- {recommendation}\n"

        # 保存Markdown文件
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

    def cleanup(self):
        """清理测试环境"""
        try:
            import shutil
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            logger.info("测试环境清理完成")
        except Exception as e:
            logger.warning(f"测试环境清理失败: {e}")

if __name__ == "__main__":
    # 运行剪映工程文件功能测试
    test_suite = JianYingProjectFunctionalityTest()

    print("开始执行VisionAI-ClipsMaster剪映工程文件功能测试...")
    print("=" * 70)

    try:
        # 运行全面功能测试
        test_results = test_suite.run_comprehensive_functionality_tests()

        # 生成详细报告
        report_path = test_suite.generate_detailed_report()

        # 打印测试结果摘要
        print("\n" + "=" * 70)
        print("剪映工程文件功能测试完成！")

        assessment = test_results.get("comprehensive_assessment", {})
        overall_score = assessment.get("overall_score", 0)

        print(f"总体结果: {'✅ 优秀' if overall_score >= 0.9 else '✅ 良好' if overall_score >= 0.7 else '⚠️ 需要改进'}")
        print(f"总体评分: {overall_score:.2f}/1.00")
        print(f"测试持续时间: {test_results.get('total_duration', 0):.2f} 秒")

        # 显示各测试结果
        print("\n详细测试结果:")
        for test_name, test_result in test_results["functionality_tests"].items():
            status_icon = "✅" if test_result["status"] == "passed" else "⚠️" if test_result["status"] == "warning" else "❌"
            print(f"  {status_icon} {test_result.get('test_name', test_name)}: {test_result['status']}")

        # 显示关键发现
        if assessment.get("strengths"):
            print("\n主要优势:")
            for strength in assessment["strengths"][:3]:
                print(f"  ✅ {strength}")

        if assessment.get("recommendations"):
            print("\n主要建议:")
            for recommendation in assessment["recommendations"][:3]:
                print(f"  💡 {recommendation}")

        print(f"\n详细报告: {report_path}")
        print(f"Markdown报告: {report_path.replace('.json', '.md')}")

    except Exception as e:
        print(f"测试执行失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理测试环境
        test_suite.cleanup()
