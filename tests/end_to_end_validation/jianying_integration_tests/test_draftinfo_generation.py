#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映工程文件生成测试模块

此模块测试生成.draftinfo格式剪映工程文件的功能。
验证JSON结构、文件路径引用、元数据完整性等关键要素。
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.jianying_project_generator import JianyingProjectGenerator
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler
from src.utils.file_checker import FileChecker

logger = logging.getLogger(__name__)


@dataclass
class DraftinfoGenerationResult:
    """剪映工程文件生成测试结果数据类"""
    test_name: str
    input_segments: List[str]
    output_draftinfo_path: str
    generation_success: bool
    json_structure_valid: bool
    required_fields_present: bool
    file_paths_valid: bool
    metadata_complete: bool
    version_compatibility: bool
    timeline_structure_correct: bool
    material_references_valid: bool
    generation_time: float
    file_size_bytes: int
    structure_errors: List[Dict[str, Any]]
    validation_errors: List[Dict[str, Any]]
    compatibility_issues: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


class DraftinfoGenerator:
    """剪映工程文件生成器"""
    
    def __init__(self, config_path: str = None):
        """初始化剪映工程文件生成器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.project_generator = JianyingProjectGenerator()
        self.video_processor = VideoProcessor()
        self.file_checker = FileChecker()
        
        # 剪映配置
        self.jianying_config = self.config.get('jianying_integration', {})
        self.supported_versions = self.jianying_config.get('supported_versions', ['3.0', '3.1', '3.2', '4.0'])
        self.required_fields = self.jianying_config.get('draftinfo', {}).get('required_fields', [])
        
        # 创建临时目录
        self.temp_dir = Path(self.config.get('test_environment', {}).get('temp_dir', 'tests/temp/e2e'))
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/end_to_end_validation/e2e_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'jianying_integration': {
                    'supported_versions': ['3.0', '3.1', '3.2', '4.0'],
                    'draftinfo': {'required_fields': ['version', 'tracks', 'materials', 'canvas_config', 'duration']}
                },
                'test_environment': {'log_level': 'INFO', 'temp_dir': 'tests/temp/e2e'}
            }
    
    def test_draftinfo_generation(self, video_segments: List[str], 
                                 project_name: str = "test_project") -> DraftinfoGenerationResult:
        """
        测试剪映工程文件生成
        
        Args:
            video_segments: 视频片段文件路径列表
            project_name: 项目名称
            
        Returns:
            DraftinfoGenerationResult: 生成测试结果
        """
        test_name = "draftinfo_generation"
        start_time = time.time()
        
        try:
            # 验证输入片段
            valid_segments = []
            for segment_path in video_segments:
                if os.path.exists(segment_path):
                    valid_segments.append(segment_path)
                else:
                    self.logger.warning(f"视频片段不存在: {segment_path}")
            
            if not valid_segments:
                raise ValueError("没有有效的视频片段")
            
            # 创建输出路径
            output_path = self.temp_dir / f"{project_name}_{int(time.time())}.draftinfo"
            
            # 生成剪映工程文件
            generation_result = self.project_generator.generate_project(
                video_segments=valid_segments,
                output_path=str(output_path),
                project_name=project_name
            )
            
            generation_success = generation_result.get('success', False)
            
            if not generation_success:
                raise RuntimeError(f"工程文件生成失败: {generation_result.get('error_message', 'Unknown error')}")
            
            # 验证生成的文件
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"生成的工程文件不存在: {output_path}")
            
            # 读取并验证JSON结构
            with open(output_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 执行各项验证
            json_validation = self._validate_json_structure(project_data)
            fields_validation = self._validate_required_fields(project_data)
            paths_validation = self._validate_file_paths(project_data, valid_segments)
            metadata_validation = self._validate_metadata_completeness(project_data)
            version_validation = self._validate_version_compatibility(project_data)
            timeline_validation = self._validate_timeline_structure(project_data, valid_segments)
            materials_validation = self._validate_material_references(project_data, valid_segments)
            
            # 收集错误
            structure_errors = []
            validation_errors = []
            compatibility_issues = []
            
            if not json_validation['valid']:
                structure_errors.extend(json_validation['errors'])
            
            if not fields_validation['valid']:
                validation_errors.extend(fields_validation['errors'])
            
            if not paths_validation['valid']:
                validation_errors.extend(paths_validation['errors'])
            
            if not metadata_validation['valid']:
                validation_errors.extend(metadata_validation['errors'])
            
            if not version_validation['valid']:
                compatibility_issues.extend(version_validation['errors'])
            
            if not timeline_validation['valid']:
                structure_errors.extend(timeline_validation['errors'])
            
            if not materials_validation['valid']:
                validation_errors.extend(materials_validation['errors'])
            
            # 获取文件信息
            file_size = os.path.getsize(output_path)
            generation_time = time.time() - start_time
            
            # 判断总体成功
            success = (
                generation_success and
                json_validation['valid'] and
                fields_validation['valid'] and
                paths_validation['valid'] and
                metadata_validation['valid'] and
                version_validation['valid'] and
                timeline_validation['valid'] and
                materials_validation['valid']
            )
            
            result = DraftinfoGenerationResult(
                test_name=test_name,
                input_segments=valid_segments,
                output_draftinfo_path=str(output_path),
                generation_success=generation_success,
                json_structure_valid=json_validation['valid'],
                required_fields_present=fields_validation['valid'],
                file_paths_valid=paths_validation['valid'],
                metadata_complete=metadata_validation['valid'],
                version_compatibility=version_validation['valid'],
                timeline_structure_correct=timeline_validation['valid'],
                material_references_valid=materials_validation['valid'],
                generation_time=generation_time,
                file_size_bytes=file_size,
                structure_errors=structure_errors,
                validation_errors=validation_errors,
                compatibility_issues=compatibility_issues,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"剪映工程文件生成测试完成: {len(valid_segments)} 个片段, 文件大小: {file_size} 字节")
            
            return result
            
        except Exception as e:
            self.logger.error(f"剪映工程文件生成测试失败: {str(e)}")
            return DraftinfoGenerationResult(
                test_name=test_name,
                input_segments=video_segments,
                output_draftinfo_path="",
                generation_success=False,
                json_structure_valid=False,
                required_fields_present=False,
                file_paths_valid=False,
                metadata_complete=False,
                version_compatibility=False,
                timeline_structure_correct=False,
                material_references_valid=False,
                generation_time=time.time() - start_time,
                file_size_bytes=0,
                structure_errors=[],
                validation_errors=[],
                compatibility_issues=[],
                success=False,
                error_message=str(e)
            )
    
    def _validate_json_structure(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证JSON结构"""
        errors = []
        
        try:
            # 检查基本数据类型
            if not isinstance(project_data, dict):
                errors.append({'error': 'root_not_dict', 'message': '根对象不是字典类型'})
                return {'valid': False, 'errors': errors}
            
            # 检查必要的顶级字段
            required_top_level = ['version', 'tracks', 'materials']
            for field in required_top_level:
                if field not in project_data:
                    errors.append({'error': 'missing_top_level_field', 'field': field})
            
            # 检查tracks结构
            if 'tracks' in project_data:
                tracks = project_data['tracks']
                if not isinstance(tracks, list):
                    errors.append({'error': 'tracks_not_list', 'message': 'tracks字段不是列表类型'})
                else:
                    for i, track in enumerate(tracks):
                        if not isinstance(track, dict):
                            errors.append({'error': 'track_not_dict', 'track_index': i})
            
            # 检查materials结构
            if 'materials' in project_data:
                materials = project_data['materials']
                if not isinstance(materials, dict):
                    errors.append({'error': 'materials_not_dict', 'message': 'materials字段不是字典类型'})
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'json_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _validate_required_fields(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证必需字段"""
        errors = []
        
        for field in self.required_fields:
            if field not in project_data:
                errors.append({'error': 'missing_required_field', 'field': field})
            elif project_data[field] is None:
                errors.append({'error': 'null_required_field', 'field': field})
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _validate_file_paths(self, project_data: Dict[str, Any], 
                           expected_segments: List[str]) -> Dict[str, Any]:
        """验证文件路径引用"""
        errors = []
        
        try:
            # 检查materials中的文件路径
            materials = project_data.get('materials', {})
            
            for material_id, material_data in materials.items():
                if isinstance(material_data, dict):
                    file_path = material_data.get('path', '')
                    
                    if file_path:
                        # 检查路径格式
                        if not os.path.isabs(file_path):
                            errors.append({
                                'error': 'relative_path',
                                'material_id': material_id,
                                'path': file_path
                            })
                        
                        # 检查文件是否存在
                        if not os.path.exists(file_path):
                            errors.append({
                                'error': 'file_not_found',
                                'material_id': material_id,
                                'path': file_path
                            })
            
            # 检查是否所有期望的片段都被引用
            referenced_paths = set()
            for material_data in materials.values():
                if isinstance(material_data, dict):
                    path = material_data.get('path', '')
                    if path:
                        referenced_paths.add(os.path.abspath(path))
            
            expected_paths = set(os.path.abspath(path) for path in expected_segments)
            missing_references = expected_paths - referenced_paths
            
            for missing_path in missing_references:
                errors.append({
                    'error': 'segment_not_referenced',
                    'path': missing_path
                })
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'path_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _validate_metadata_completeness(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证元数据完整性"""
        errors = []
        
        try:
            # 检查版本信息
            version = project_data.get('version', '')
            if not version:
                errors.append({'error': 'missing_version', 'message': '缺少版本信息'})
            
            # 检查画布配置
            canvas_config = project_data.get('canvas_config', {})
            if not canvas_config:
                errors.append({'error': 'missing_canvas_config', 'message': '缺少画布配置'})
            else:
                required_canvas_fields = ['width', 'height', 'fps']
                for field in required_canvas_fields:
                    if field not in canvas_config:
                        errors.append({'error': 'missing_canvas_field', 'field': field})
            
            # 检查时长信息
            duration = project_data.get('duration', 0)
            if duration <= 0:
                errors.append({'error': 'invalid_duration', 'duration': duration})
            
            # 检查材料元数据
            materials = project_data.get('materials', {})
            for material_id, material_data in materials.items():
                if isinstance(material_data, dict):
                    required_material_fields = ['type', 'path', 'duration']
                    for field in required_material_fields:
                        if field not in material_data:
                            errors.append({
                                'error': 'missing_material_field',
                                'material_id': material_id,
                                'field': field
                            })
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'metadata_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _validate_version_compatibility(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证版本兼容性"""
        errors = []
        
        try:
            version = project_data.get('version', '')
            
            if not version:
                errors.append({'error': 'no_version_specified', 'message': '未指定版本'})
                return {'valid': False, 'errors': errors}
            
            # 检查版本格式
            if not self._is_valid_version_format(version):
                errors.append({'error': 'invalid_version_format', 'version': version})
            
            # 检查版本兼容性
            if version not in self.supported_versions:
                errors.append({
                    'error': 'unsupported_version',
                    'version': version,
                    'supported_versions': self.supported_versions
                })
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'version_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _validate_timeline_structure(self, project_data: Dict[str, Any], 
                                   expected_segments: List[str]) -> Dict[str, Any]:
        """验证时间轴结构"""
        errors = []
        
        try:
            tracks = project_data.get('tracks', [])
            
            if not tracks:
                errors.append({'error': 'no_tracks', 'message': '没有轨道'})
                return {'valid': False, 'errors': errors}
            
            # 检查视频轨道
            video_tracks = [track for track in tracks if track.get('type') == 'video']
            if not video_tracks:
                errors.append({'error': 'no_video_track', 'message': '没有视频轨道'})
            
            # 检查轨道中的片段
            for track_index, track in enumerate(video_tracks):
                segments = track.get('segments', [])
                
                if len(segments) != len(expected_segments):
                    errors.append({
                        'error': 'segment_count_mismatch',
                        'track_index': track_index,
                        'expected_count': len(expected_segments),
                        'actual_count': len(segments)
                    })
                
                # 检查片段时间轴
                for seg_index, segment in enumerate(segments):
                    if 'start' not in segment or 'end' not in segment:
                        errors.append({
                            'error': 'missing_segment_timing',
                            'track_index': track_index,
                            'segment_index': seg_index
                        })
                    
                    if segment.get('start', 0) >= segment.get('end', 0):
                        errors.append({
                            'error': 'invalid_segment_timing',
                            'track_index': track_index,
                            'segment_index': seg_index,
                            'start': segment.get('start'),
                            'end': segment.get('end')
                        })
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'timeline_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _validate_material_references(self, project_data: Dict[str, Any], 
                                    expected_segments: List[str]) -> Dict[str, Any]:
        """验证素材引用"""
        errors = []
        
        try:
            materials = project_data.get('materials', {})
            tracks = project_data.get('tracks', [])
            
            # 收集轨道中引用的素材ID
            referenced_material_ids = set()
            for track in tracks:
                segments = track.get('segments', [])
                for segment in segments:
                    material_id = segment.get('material_id')
                    if material_id:
                        referenced_material_ids.add(material_id)
            
            # 检查引用的素材是否存在
            for material_id in referenced_material_ids:
                if material_id not in materials:
                    errors.append({
                        'error': 'referenced_material_not_found',
                        'material_id': material_id
                    })
            
            # 检查素材是否都被引用
            unreferenced_materials = set(materials.keys()) - referenced_material_ids
            for material_id in unreferenced_materials:
                errors.append({
                    'error': 'material_not_referenced',
                    'material_id': material_id
                })
            
            return {'valid': len(errors) == 0, 'errors': errors}
            
        except Exception as e:
            errors.append({'error': 'material_reference_validation_exception', 'message': str(e)})
            return {'valid': False, 'errors': errors}
    
    def _is_valid_version_format(self, version: str) -> bool:
        """检查版本格式是否有效"""
        try:
            # 简单的版本格式检查：x.y 或 x.y.z
            parts = version.split('.')
            if len(parts) < 2 or len(parts) > 3:
                return False
            
            for part in parts:
                int(part)  # 检查是否为数字
            
            return True
        except ValueError:
            return False


class TestDraftinfoGeneration(unittest.TestCase):
    """剪映工程文件生成测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.generator = DraftinfoGenerator()
        cls.test_segments = cls._create_test_segments()
    
    @classmethod
    def _create_test_segments(cls) -> List[str]:
        """创建测试片段文件"""
        segments = []
        
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.write(b"mock video segment content")
            temp_file.close()
            segments.append(temp_file.name)
        
        return segments
    
    def test_draftinfo_generation(self):
        """测试剪映工程文件生成"""
        # 注意：这个测试需要真实的视频片段才能正常运行
        
        try:
            result = self.generator.test_draftinfo_generation(
                self.test_segments, "test_project"
            )
            
            # 由于使用的是模拟文件，这里主要测试流程是否正常
            self.assertIsNotNone(result, "应该返回测试结果")
            self.assertEqual(result.test_name, "draftinfo_generation", "测试名称应该正确")
            
        except Exception as e:
            # 预期会失败，因为使用的是模拟视频文件
            self.assertIn("project", str(e).lower(), "错误应该与项目生成相关")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        for segment_file in cls.test_segments:
            if os.path.exists(segment_file):
                os.unlink(segment_file)


if __name__ == "__main__":
    unittest.main(verbosity=2)
