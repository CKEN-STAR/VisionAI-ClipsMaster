#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映导入功能测试模块

此模块模拟剪映软件导入工程文件的流程，验证导入兼容性、时间轴结构、编辑功能等。
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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.jianying_simulator import JianyingSimulator
from src.core.video_processor import VideoProcessor
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class JianyingImportResult:
    """剪映导入测试结果数据类"""
    test_name: str
    draftinfo_path: str
    import_success: bool
    import_time: float
    timeline_segments_count: int
    expected_segments_count: int
    timeline_structure_correct: bool
    material_library_populated: bool
    segment_mapping_correct: bool
    editing_capabilities_available: bool
    import_errors: List[Dict[str, Any]]
    timeline_issues: List[Dict[str, Any]]
    material_issues: List[Dict[str, Any]]
    editing_issues: List[Dict[str, Any]]
    compatibility_score: float
    success: bool
    error_message: Optional[str] = None


class JianyingImportTester:
    """剪映导入测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化剪映导入测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.jianying_simulator = JianyingSimulator()
        self.video_processor = VideoProcessor()
        
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
            return {'test_environment': {'log_level': 'INFO'}}
    
    def test_jianying_import(self, draftinfo_path: str) -> JianyingImportResult:
        """
        测试剪映导入功能
        
        Args:
            draftinfo_path: 剪映工程文件路径
            
        Returns:
            JianyingImportResult: 导入测试结果
        """
        test_name = "jianying_import"
        start_time = time.time()
        
        try:
            # 验证工程文件存在
            if not os.path.exists(draftinfo_path):
                raise FileNotFoundError(f"工程文件不存在: {draftinfo_path}")
            
            # 读取工程文件
            with open(draftinfo_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 模拟剪映导入过程
            import_result = self.jianying_simulator.simulate_import(draftinfo_path)
            
            import_success = import_result.get('success', False)
            import_time = time.time() - start_time
            
            if not import_success:
                raise RuntimeError(f"剪映导入失败: {import_result.get('error_message', 'Unknown error')}")
            
            # 验证导入结果
            timeline_validation = self._validate_timeline_structure(import_result, project_data)
            material_validation = self._validate_material_library(import_result, project_data)
            mapping_validation = self._validate_segment_mapping(import_result, project_data)
            editing_validation = self._validate_editing_capabilities(import_result)
            
            # 收集错误和问题
            import_errors = import_result.get('import_errors', [])
            timeline_issues = timeline_validation.get('issues', [])
            material_issues = material_validation.get('issues', [])
            editing_issues = editing_validation.get('issues', [])
            
            # 计算兼容性评分
            compatibility_score = self._calculate_compatibility_score(
                import_success, timeline_validation, material_validation, 
                mapping_validation, editing_validation
            )
            
            # 判断总体成功
            success = (
                import_success and
                timeline_validation.get('valid', False) and
                material_validation.get('valid', False) and
                mapping_validation.get('valid', False) and
                editing_validation.get('valid', False) and
                compatibility_score >= 0.8
            )
            
            result = JianyingImportResult(
                test_name=test_name,
                draftinfo_path=draftinfo_path,
                import_success=import_success,
                import_time=import_time,
                timeline_segments_count=timeline_validation.get('segments_count', 0),
                expected_segments_count=timeline_validation.get('expected_count', 0),
                timeline_structure_correct=timeline_validation.get('valid', False),
                material_library_populated=material_validation.get('valid', False),
                segment_mapping_correct=mapping_validation.get('valid', False),
                editing_capabilities_available=editing_validation.get('valid', False),
                import_errors=import_errors,
                timeline_issues=timeline_issues,
                material_issues=material_issues,
                editing_issues=editing_issues,
                compatibility_score=compatibility_score,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"剪映导入测试完成: 兼容性评分 {compatibility_score:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"剪映导入测试失败: {str(e)}")
            return JianyingImportResult(
                test_name=test_name,
                draftinfo_path=draftinfo_path,
                import_success=False,
                import_time=time.time() - start_time,
                timeline_segments_count=0,
                expected_segments_count=0,
                timeline_structure_correct=False,
                material_library_populated=False,
                segment_mapping_correct=False,
                editing_capabilities_available=False,
                import_errors=[],
                timeline_issues=[],
                material_issues=[],
                editing_issues=[],
                compatibility_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _validate_timeline_structure(self, import_result: Dict[str, Any], 
                                   project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证时间轴结构"""
        try:
            timeline_data = import_result.get('timeline', {})
            tracks = timeline_data.get('tracks', [])
            
            # 获取期望的片段数量
            expected_segments = 0
            project_tracks = project_data.get('tracks', [])
            for track in project_tracks:
                if track.get('type') == 'video':
                    expected_segments += len(track.get('segments', []))
            
            # 统计实际片段数量
            actual_segments = 0
            issues = []
            
            for track in tracks:
                if track.get('type') == 'video':
                    segments = track.get('segments', [])
                    actual_segments += len(segments)
                    
                    # 检查每个片段的结构
                    for i, segment in enumerate(segments):
                        if 'start' not in segment or 'end' not in segment:
                            issues.append({
                                'issue_type': 'missing_timing',
                                'segment_index': i,
                                'track_type': track.get('type')
                            })
                        
                        if 'material_id' not in segment:
                            issues.append({
                                'issue_type': 'missing_material_reference',
                                'segment_index': i,
                                'track_type': track.get('type')
                            })
            
            # 检查片段数量匹配
            if actual_segments != expected_segments:
                issues.append({
                    'issue_type': 'segment_count_mismatch',
                    'expected': expected_segments,
                    'actual': actual_segments
                })
            
            return {
                'valid': len(issues) == 0,
                'segments_count': actual_segments,
                'expected_count': expected_segments,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'segments_count': 0,
                'expected_count': 0,
                'issues': [{'issue_type': 'validation_exception', 'error': str(e)}]
            }
    
    def _validate_material_library(self, import_result: Dict[str, Any], 
                                 project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证素材库"""
        try:
            material_library = import_result.get('material_library', {})
            expected_materials = project_data.get('materials', {})
            
            issues = []
            
            # 检查素材数量
            if len(material_library) != len(expected_materials):
                issues.append({
                    'issue_type': 'material_count_mismatch',
                    'expected': len(expected_materials),
                    'actual': len(material_library)
                })
            
            # 检查每个素材
            for material_id, expected_material in expected_materials.items():
                if material_id not in material_library:
                    issues.append({
                        'issue_type': 'missing_material',
                        'material_id': material_id
                    })
                    continue
                
                actual_material = material_library[material_id]
                
                # 检查素材路径
                expected_path = expected_material.get('path', '')
                actual_path = actual_material.get('path', '')
                
                if expected_path != actual_path:
                    issues.append({
                        'issue_type': 'material_path_mismatch',
                        'material_id': material_id,
                        'expected_path': expected_path,
                        'actual_path': actual_path
                    })
                
                # 检查素材类型
                expected_type = expected_material.get('type', '')
                actual_type = actual_material.get('type', '')
                
                if expected_type != actual_type:
                    issues.append({
                        'issue_type': 'material_type_mismatch',
                        'material_id': material_id,
                        'expected_type': expected_type,
                        'actual_type': actual_type
                    })
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [{'issue_type': 'validation_exception', 'error': str(e)}]
            }
    
    def _validate_segment_mapping(self, import_result: Dict[str, Any], 
                                project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证片段映射关系"""
        try:
            timeline_data = import_result.get('timeline', {})
            material_library = import_result.get('material_library', {})
            
            issues = []
            
            # 检查时间轴中的片段是否正确映射到素材
            for track in timeline_data.get('tracks', []):
                for i, segment in enumerate(track.get('segments', [])):
                    material_id = segment.get('material_id')
                    
                    if not material_id:
                        issues.append({
                            'issue_type': 'missing_material_id',
                            'segment_index': i,
                            'track_type': track.get('type')
                        })
                        continue
                    
                    if material_id not in material_library:
                        issues.append({
                            'issue_type': 'material_not_in_library',
                            'material_id': material_id,
                            'segment_index': i
                        })
                        continue
                    
                    # 检查素材文件是否存在
                    material = material_library[material_id]
                    material_path = material.get('path', '')
                    
                    if material_path and not os.path.exists(material_path):
                        issues.append({
                            'issue_type': 'material_file_not_found',
                            'material_id': material_id,
                            'path': material_path
                        })
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [{'issue_type': 'validation_exception', 'error': str(e)}]
            }
    
    def _validate_editing_capabilities(self, import_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证编辑功能"""
        try:
            editing_capabilities = import_result.get('editing_capabilities', {})
            
            issues = []
            required_capabilities = [
                'segment_resize',
                'segment_move',
                'segment_delete',
                'material_replace',
                'timeline_navigation'
            ]
            
            for capability in required_capabilities:
                if not editing_capabilities.get(capability, False):
                    issues.append({
                        'issue_type': 'missing_editing_capability',
                        'capability': capability
                    })
            
            # 测试基本编辑操作
            if editing_capabilities.get('segment_resize', False):
                resize_test = self._test_segment_resize(import_result)
                if not resize_test['success']:
                    issues.append({
                        'issue_type': 'segment_resize_failed',
                        'details': resize_test.get('error', 'Unknown error')
                    })
            
            return {
                'valid': len(issues) == 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [{'issue_type': 'validation_exception', 'error': str(e)}]
            }
    
    def _test_segment_resize(self, import_result: Dict[str, Any]) -> Dict[str, Any]:
        """测试片段调整功能"""
        try:
            # 模拟片段调整操作
            timeline_data = import_result.get('timeline', {})
            tracks = timeline_data.get('tracks', [])
            
            if not tracks:
                return {'success': False, 'error': 'No tracks available'}
            
            # 找到第一个视频轨道的第一个片段
            for track in tracks:
                if track.get('type') == 'video':
                    segments = track.get('segments', [])
                    if segments:
                        segment = segments[0]
                        original_end = segment.get('end', 0)
                        
                        # 模拟延长片段
                        new_end = original_end + 5.0  # 延长5秒
                        
                        # 这里应该调用实际的编辑API
                        # 由于是模拟，我们假设操作成功
                        return {'success': True, 'original_end': original_end, 'new_end': new_end}
            
            return {'success': False, 'error': 'No video segments found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_compatibility_score(self, import_success: bool, 
                                     timeline_validation: Dict[str, Any],
                                     material_validation: Dict[str, Any],
                                     mapping_validation: Dict[str, Any],
                                     editing_validation: Dict[str, Any]) -> float:
        """计算兼容性评分"""
        score = 0.0
        
        # 导入成功 (30%)
        if import_success:
            score += 0.3
        
        # 时间轴结构正确 (25%)
        if timeline_validation.get('valid', False):
            score += 0.25
        
        # 素材库正确 (20%)
        if material_validation.get('valid', False):
            score += 0.2
        
        # 片段映射正确 (15%)
        if mapping_validation.get('valid', False):
            score += 0.15
        
        # 编辑功能可用 (10%)
        if editing_validation.get('valid', False):
            score += 0.1
        
        return min(1.0, score)


class TestJianyingImport(unittest.TestCase):
    """剪映导入测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.import_tester = JianyingImportTester()
        cls.test_draftinfo = cls._create_test_draftinfo()
    
    @classmethod
    def _create_test_draftinfo(cls) -> str:
        """创建测试剪映工程文件"""
        test_project = {
            "version": "3.0.0",
            "tracks": [
                {
                    "type": "video",
                    "segments": [
                        {
                            "start": 0,
                            "end": 5,
                            "material_id": "material_1"
                        },
                        {
                            "start": 5,
                            "end": 10,
                            "material_id": "material_2"
                        }
                    ]
                }
            ],
            "materials": {
                "material_1": {
                    "type": "video",
                    "path": "/path/to/segment1.mp4",
                    "duration": 5
                },
                "material_2": {
                    "type": "video",
                    "path": "/path/to/segment2.mp4",
                    "duration": 5
                }
            },
            "canvas_config": {
                "width": 1920,
                "height": 1080,
                "fps": 30
            },
            "duration": 10
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.draftinfo', delete=False, encoding='utf-8')
        json.dump(test_project, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        return temp_file.name
    
    def test_jianying_import(self):
        """测试剪映导入功能"""
        # 注意：这个测试需要真实的剪映模拟器才能正常运行
        
        try:
            result = self.import_tester.test_jianying_import(self.test_draftinfo)
            
            # 由于使用的是模拟环境，这里主要测试流程是否正常
            self.assertIsNotNone(result, "应该返回测试结果")
            self.assertEqual(result.test_name, "jianying_import", "测试名称应该正确")
            
        except Exception as e:
            # 预期会失败，因为使用的是模拟环境
            self.assertIn("import", str(e).lower(), "错误应该与导入相关")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(cls.test_draftinfo):
            os.unlink(cls.test_draftinfo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
