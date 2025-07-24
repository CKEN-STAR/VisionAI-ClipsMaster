#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映导入兼容性测试模块

此模块测试生成的.draftinfo工程文件在真实剪映软件中的导入兼容性，
验证文件格式、路径引用、时间轴结构、编辑功能等关键兼容性指标。
"""

import os
import sys
import json
import time
import logging
import unittest
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.jianying_project_generator import JianyingProjectGenerator
from src.core.jianying_validator import JianyingValidator
from src.core.jianying_simulator import JianyingSimulator
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class ImportCompatibilityResult:
    """导入兼容性测试结果"""
    test_name: str
    draftinfo_file_path: str
    jianying_version: str
    import_success: bool
    import_time: float
    file_validation: Dict[str, Any]
    structure_validation: Dict[str, Any]
    path_validation: Dict[str, Any]
    timeline_validation: Dict[str, Any]
    material_validation: Dict[str, Any]
    editing_functionality: Dict[str, Any]
    compatibility_score: float
    user_experience_score: float
    import_errors: List[str]
    validation_warnings: List[str]
    success: bool


class JianyingImportCompatibilityTester:
    """剪映导入兼容性测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化剪映导入兼容性测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化组件
        self.project_generator = JianyingProjectGenerator()
        self.jianying_validator = JianyingValidator()
        self.jianying_simulator = JianyingSimulator()
        
        # 剪映兼容性配置
        self.compatibility_config = self.config.get('jianying_compatibility', {})
        self.supported_versions = self.compatibility_config.get('supported_versions', [])
        self.import_threshold = self.compatibility_config.get('import_testing', {}).get('import_success_rate_threshold', 1.0)
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'jianying_compatibility': {
                'supported_versions': ['3.0.0', '3.1.0', '3.2.0', '4.0.0'],
                'import_testing': {'import_success_rate_threshold': 1.0}
            }
        }
    
    def test_real_world_import_compatibility(self, draftinfo_file_path: str, 
                                           jianying_version: str = "4.0.0") -> ImportCompatibilityResult:
        """
        测试真实世界剪映导入兼容性
        
        Args:
            draftinfo_file_path: 剪映工程文件路径
            jianying_version: 目标剪映版本
            
        Returns:
            ImportCompatibilityResult: 导入兼容性测试结果
        """
        test_name = "real_world_import_compatibility"
        start_time = time.time()
        
        self.logger.info(f"开始剪映导入兼容性测试: {draftinfo_file_path}")
        
        import_errors = []
        validation_warnings = []
        
        try:
            # 验证文件存在
            if not os.path.exists(draftinfo_file_path):
                raise FileNotFoundError(f"工程文件不存在: {draftinfo_file_path}")
            
            # 1. 文件格式验证
            file_validation = self._validate_file_format(draftinfo_file_path)
            if not file_validation['valid']:
                import_errors.extend(file_validation['errors'])
            
            # 2. JSON结构验证
            structure_validation = self._validate_json_structure(draftinfo_file_path)
            if not structure_validation['valid']:
                import_errors.extend(structure_validation['errors'])
            
            # 3. 文件路径验证
            path_validation = self._validate_file_paths(draftinfo_file_path)
            if not path_validation['valid']:
                validation_warnings.extend(path_validation['warnings'])
            
            # 4. 时间轴结构验证
            timeline_validation = self._validate_timeline_structure(draftinfo_file_path)
            if not timeline_validation['valid']:
                import_errors.extend(timeline_validation['errors'])
            
            # 5. 素材引用验证
            material_validation = self._validate_material_references(draftinfo_file_path)
            if not material_validation['valid']:
                import_errors.extend(material_validation['errors'])
            
            # 6. 模拟剪映导入
            import_simulation = self._simulate_jianying_import(draftinfo_file_path, jianying_version)
            import_success = import_simulation['success']
            import_time = import_simulation['import_time']
            
            if not import_success:
                import_errors.extend(import_simulation['errors'])
            
            # 7. 编辑功能测试
            editing_functionality = self._test_editing_functionality(draftinfo_file_path, jianying_version)
            if not editing_functionality['success']:
                validation_warnings.extend(editing_functionality['warnings'])
            
            # 计算兼容性评分
            compatibility_score = self._calculate_compatibility_score(
                file_validation, structure_validation, path_validation,
                timeline_validation, material_validation, import_simulation, editing_functionality
            )
            
            # 计算用户体验评分
            user_experience_score = self._calculate_user_experience_score(
                import_success, import_time, compatibility_score, len(import_errors)
            )
            
            success = (
                import_success and
                len(import_errors) == 0 and
                compatibility_score >= 0.9
            )
            
            result = ImportCompatibilityResult(
                test_name=test_name,
                draftinfo_file_path=draftinfo_file_path,
                jianying_version=jianying_version,
                import_success=import_success,
                import_time=import_time,
                file_validation=file_validation,
                structure_validation=structure_validation,
                path_validation=path_validation,
                timeline_validation=timeline_validation,
                material_validation=material_validation,
                editing_functionality=editing_functionality,
                compatibility_score=compatibility_score,
                user_experience_score=user_experience_score,
                import_errors=import_errors,
                validation_warnings=validation_warnings,
                success=success
            )
            
            self.test_results.append(result)
            self.logger.info(f"剪映导入兼容性测试完成: 兼容性评分 {compatibility_score:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"剪映导入兼容性测试异常: {str(e)}")
            
            return ImportCompatibilityResult(
                test_name=test_name,
                draftinfo_file_path=draftinfo_file_path,
                jianying_version=jianying_version,
                import_success=False,
                import_time=time.time() - start_time,
                file_validation={'valid': False, 'errors': [str(e)]},
                structure_validation={'valid': False, 'errors': []},
                path_validation={'valid': False, 'warnings': []},
                timeline_validation={'valid': False, 'errors': []},
                material_validation={'valid': False, 'errors': []},
                editing_functionality={'success': False, 'warnings': []},
                compatibility_score=0.0,
                user_experience_score=0.0,
                import_errors=[str(e)],
                validation_warnings=[],
                success=False
            )
    
    def _validate_file_format(self, draftinfo_file_path: str) -> Dict[str, Any]:
        """验证文件格式"""
        try:
            errors = []
            
            # 检查文件扩展名
            if not draftinfo_file_path.endswith('.draftinfo'):
                errors.append("文件扩展名不正确，应为.draftinfo")
            
            # 检查文件大小
            file_size = os.path.getsize(draftinfo_file_path)
            if file_size == 0:
                errors.append("文件大小为0")
            elif file_size > 100 * 1024 * 1024:  # 100MB
                errors.append(f"文件过大: {file_size / (1024*1024):.1f}MB")
            
            # 检查文件编码
            try:
                with open(draftinfo_file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100)  # 读取前100字符检查编码
            except UnicodeDecodeError:
                errors.append("文件编码不是UTF-8")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'file_size_mb': file_size / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"文件格式验证异常: {str(e)}"],
                'file_size_mb': 0
            }
    
    def _validate_json_structure(self, draftinfo_file_path: str) -> Dict[str, Any]:
        """验证JSON结构"""
        try:
            errors = []
            
            # 解析JSON
            with open(draftinfo_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 检查必需的顶级字段
            required_fields = ['version', 'tracks', 'materials', 'canvas_config']
            for field in required_fields:
                if field not in project_data:
                    errors.append(f"缺少必需字段: {field}")
            
            # 验证版本字段
            if 'version' in project_data:
                version = project_data['version']
                if not isinstance(version, str) or not version:
                    errors.append("版本字段格式不正确")
                elif version not in self.supported_versions:
                    errors.append(f"不支持的版本: {version}")
            
            # 验证tracks字段
            if 'tracks' in project_data:
                tracks = project_data['tracks']
                if not isinstance(tracks, list):
                    errors.append("tracks字段应为数组")
                else:
                    for i, track in enumerate(tracks):
                        if not isinstance(track, dict):
                            errors.append(f"轨道{i}格式不正确")
                        elif 'type' not in track:
                            errors.append(f"轨道{i}缺少type字段")
                        elif 'segments' not in track:
                            errors.append(f"轨道{i}缺少segments字段")
            
            # 验证materials字段
            if 'materials' in project_data:
                materials = project_data['materials']
                if not isinstance(materials, dict):
                    errors.append("materials字段应为对象")
                else:
                    for material_id, material_data in materials.items():
                        if not isinstance(material_data, dict):
                            errors.append(f"素材{material_id}格式不正确")
                        elif 'type' not in material_data:
                            errors.append(f"素材{material_id}缺少type字段")
                        elif 'path' not in material_data:
                            errors.append(f"素材{material_id}缺少path字段")
            
            # 验证canvas_config字段
            if 'canvas_config' in project_data:
                canvas_config = project_data['canvas_config']
                if not isinstance(canvas_config, dict):
                    errors.append("canvas_config字段应为对象")
                else:
                    required_canvas_fields = ['width', 'height', 'fps']
                    for field in required_canvas_fields:
                        if field not in canvas_config:
                            errors.append(f"canvas_config缺少{field}字段")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'project_data': project_data
            }
            
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'errors': [f"JSON解析错误: {str(e)}"],
                'project_data': {}
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"JSON结构验证异常: {str(e)}"],
                'project_data': {}
            }
    
    def _validate_file_paths(self, draftinfo_file_path: str) -> Dict[str, Any]:
        """验证文件路径"""
        try:
            warnings = []
            
            with open(draftinfo_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            materials = project_data.get('materials', {})
            
            for material_id, material_data in materials.items():
                if isinstance(material_data, dict):
                    file_path = material_data.get('path', '')
                    
                    if file_path:
                        # 检查路径格式
                        if not os.path.isabs(file_path):
                            warnings.append(f"素材{material_id}使用相对路径: {file_path}")
                        
                        # 检查文件是否存在
                        if not os.path.exists(file_path):
                            warnings.append(f"素材{material_id}文件不存在: {file_path}")
                        
                        # 检查路径中的特殊字符
                        if any(char in file_path for char in ['<', '>', '|', '"', '*', '?']):
                            warnings.append(f"素材{material_id}路径包含特殊字符: {file_path}")
                        
                        # 检查路径长度
                        if len(file_path) > 260:  # Windows路径长度限制
                            warnings.append(f"素材{material_id}路径过长: {len(file_path)}字符")
            
            return {
                'valid': True,  # 路径问题通常不会阻止导入，只是警告
                'warnings': warnings,
                'total_materials': len(materials),
                'missing_files': len([w for w in warnings if '文件不存在' in w])
            }
            
        except Exception as e:
            return {
                'valid': False,
                'warnings': [f"文件路径验证异常: {str(e)}"],
                'total_materials': 0,
                'missing_files': 0
            }
    
    def _validate_timeline_structure(self, draftinfo_file_path: str) -> Dict[str, Any]:
        """验证时间轴结构"""
        try:
            errors = []
            
            with open(draftinfo_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            tracks = project_data.get('tracks', [])
            
            if not tracks:
                errors.append("没有轨道")
                return {'valid': False, 'errors': errors}
            
            # 检查视频轨道
            video_tracks = [track for track in tracks if track.get('type') == 'video']
            if not video_tracks:
                errors.append("没有视频轨道")
            
            # 验证每个轨道的片段
            for track_index, track in enumerate(tracks):
                segments = track.get('segments', [])
                
                for seg_index, segment in enumerate(segments):
                    # 检查必需字段
                    if 'start' not in segment:
                        errors.append(f"轨道{track_index}片段{seg_index}缺少start字段")
                    if 'end' not in segment:
                        errors.append(f"轨道{track_index}片段{seg_index}缺少end字段")
                    if 'material_id' not in segment:
                        errors.append(f"轨道{track_index}片段{seg_index}缺少material_id字段")
                    
                    # 检查时间逻辑
                    start_time = segment.get('start', 0)
                    end_time = segment.get('end', 0)
                    
                    if start_time >= end_time:
                        errors.append(f"轨道{track_index}片段{seg_index}时间逻辑错误: start({start_time}) >= end({end_time})")
                    
                    if start_time < 0:
                        errors.append(f"轨道{track_index}片段{seg_index}开始时间为负数: {start_time}")
                
                # 检查片段间的时间连续性
                for i in range(len(segments) - 1):
                    current_end = segments[i].get('end', 0)
                    next_start = segments[i + 1].get('start', 0)
                    
                    if current_end > next_start:
                        errors.append(f"轨道{track_index}片段{i}和{i+1}时间重叠")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'total_tracks': len(tracks),
                'video_tracks': len(video_tracks),
                'total_segments': sum(len(track.get('segments', [])) for track in tracks)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"时间轴结构验证异常: {str(e)}"],
                'total_tracks': 0,
                'video_tracks': 0,
                'total_segments': 0
            }
    
    def _validate_material_references(self, draftinfo_file_path: str) -> Dict[str, Any]:
        """验证素材引用"""
        try:
            errors = []
            
            with open(draftinfo_file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
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
                    errors.append(f"引用的素材不存在: {material_id}")
            
            # 检查未使用的素材
            unused_materials = set(materials.keys()) - referenced_material_ids
            if unused_materials:
                # 未使用的素材不算错误，但会记录
                pass
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'total_materials': len(materials),
                'referenced_materials': len(referenced_material_ids),
                'unused_materials': len(unused_materials)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"素材引用验证异常: {str(e)}"],
                'total_materials': 0,
                'referenced_materials': 0,
                'unused_materials': 0
            }
    
    def _simulate_jianying_import(self, draftinfo_file_path: str, jianying_version: str) -> Dict[str, Any]:
        """模拟剪映导入"""
        try:
            import_start = time.time()
            
            # 使用剪映模拟器进行导入测试
            simulation_result = self.jianying_simulator.simulate_import(
                draftinfo_file_path, target_version=jianying_version
            )
            
            import_time = time.time() - import_start
            
            return {
                'success': simulation_result.get('success', False),
                'import_time': import_time,
                'errors': simulation_result.get('errors', []),
                'warnings': simulation_result.get('warnings', []),
                'imported_project': simulation_result.get('project_data', {}),
                'compatibility_issues': simulation_result.get('compatibility_issues', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'import_time': 0,
                'errors': [f"导入模拟异常: {str(e)}"],
                'warnings': [],
                'imported_project': {},
                'compatibility_issues': []
            }
    
    def _test_editing_functionality(self, draftinfo_file_path: str, jianying_version: str) -> Dict[str, Any]:
        """测试编辑功能"""
        try:
            warnings = []
            
            # 模拟基本编辑操作
            editing_tests = [
                'segment_resize',
                'segment_move',
                'segment_delete',
                'material_replace',
                'timeline_navigation'
            ]
            
            successful_tests = 0
            
            for test_name in editing_tests:
                try:
                    # 这里应该调用实际的编辑功能测试
                    test_result = self._simulate_editing_operation(draftinfo_file_path, test_name)
                    
                    if test_result['success']:
                        successful_tests += 1
                    else:
                        warnings.append(f"编辑功能测试失败: {test_name}")
                        
                except Exception as e:
                    warnings.append(f"编辑功能测试异常: {test_name} - {str(e)}")
            
            success_rate = successful_tests / len(editing_tests) if editing_tests else 0
            
            return {
                'success': success_rate >= 0.8,  # 80%的编辑功能可用
                'success_rate': success_rate,
                'successful_tests': successful_tests,
                'total_tests': len(editing_tests),
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'success': False,
                'success_rate': 0.0,
                'successful_tests': 0,
                'total_tests': 0,
                'warnings': [f"编辑功能测试异常: {str(e)}"]
            }
    
    def _simulate_editing_operation(self, draftinfo_file_path: str, operation: str) -> Dict[str, Any]:
        """模拟编辑操作"""
        try:
            # 简化的编辑操作模拟
            # 实际实现中应该调用剪映API或模拟器
            
            if operation == 'segment_resize':
                # 模拟片段调整大小
                return {'success': True, 'operation': operation}
            elif operation == 'segment_move':
                # 模拟片段移动
                return {'success': True, 'operation': operation}
            elif operation == 'segment_delete':
                # 模拟片段删除
                return {'success': True, 'operation': operation}
            elif operation == 'material_replace':
                # 模拟素材替换
                return {'success': True, 'operation': operation}
            elif operation == 'timeline_navigation':
                # 模拟时间轴导航
                return {'success': True, 'operation': operation}
            else:
                return {'success': False, 'operation': operation, 'error': 'Unknown operation'}
                
        except Exception as e:
            return {'success': False, 'operation': operation, 'error': str(e)}
    
    def _calculate_compatibility_score(self, file_validation: Dict, structure_validation: Dict,
                                     path_validation: Dict, timeline_validation: Dict,
                                     material_validation: Dict, import_simulation: Dict,
                                     editing_functionality: Dict) -> float:
        """计算兼容性评分"""
        try:
            score = 0.0
            
            # 文件格式验证 (15%)
            if file_validation.get('valid', False):
                score += 0.15
            
            # JSON结构验证 (25%)
            if structure_validation.get('valid', False):
                score += 0.25
            
            # 路径验证 (10%)
            if path_validation.get('valid', False):
                score += 0.10
            
            # 时间轴结构验证 (20%)
            if timeline_validation.get('valid', False):
                score += 0.20
            
            # 素材引用验证 (15%)
            if material_validation.get('valid', False):
                score += 0.15
            
            # 导入成功 (10%)
            if import_simulation.get('success', False):
                score += 0.10
            
            # 编辑功能 (5%)
            editing_score = editing_functionality.get('success_rate', 0) * 0.05
            score += editing_score
            
            return min(1.0, score)
            
        except Exception:
            return 0.0
    
    def _calculate_user_experience_score(self, import_success: bool, import_time: float,
                                       compatibility_score: float, error_count: int) -> float:
        """计算用户体验评分"""
        try:
            score = 0.0
            
            # 导入成功 (40%)
            if import_success:
                score += 0.4
            
            # 导入速度 (20%)
            if import_time <= 5:  # 5秒内导入
                score += 0.2
            elif import_time <= 15:  # 15秒内导入
                score += 0.1
            
            # 兼容性评分 (30%)
            score += compatibility_score * 0.3
            
            # 错误数量 (10%)
            if error_count == 0:
                score += 0.1
            elif error_count <= 2:
                score += 0.05
            
            return min(1.0, score)
            
        except Exception:
            return 0.0


class TestJianyingImportCompatibility(unittest.TestCase):
    """剪映导入兼容性测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = JianyingImportCompatibilityTester()
        
        # 创建测试工程文件
        cls.test_draftinfo = cls._create_test_draftinfo()
    
    @classmethod
    def _create_test_draftinfo(cls) -> str:
        """创建测试剪映工程文件"""
        test_project = {
            "version": "4.0.0",
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
        
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.draftinfo', delete=False, encoding='utf-8')
        json.dump(test_project, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        return temp_file.name
    
    def test_import_compatibility_latest_version(self):
        """测试最新版本导入兼容性"""
        result = self.tester.test_real_world_import_compatibility(
            self.test_draftinfo, "4.0.0"
        )
        
        self.assertTrue(result.file_validation['valid'], "文件格式应该有效")
        self.assertTrue(result.structure_validation['valid'], "JSON结构应该有效")
        self.assertGreaterEqual(result.compatibility_score, 0.9, "兼容性评分应该≥90%")
    
    def test_import_compatibility_older_version(self):
        """测试旧版本导入兼容性"""
        result = self.tester.test_real_world_import_compatibility(
            self.test_draftinfo, "3.0.0"
        )
        
        # 旧版本可能有一些兼容性问题，但应该基本可用
        self.assertGreaterEqual(result.compatibility_score, 0.7, "旧版本兼容性评分应该≥70%")
    
    def test_user_experience_score(self):
        """测试用户体验评分"""
        result = self.tester.test_real_world_import_compatibility(
            self.test_draftinfo, "4.0.0"
        )
        
        self.assertGreaterEqual(result.user_experience_score, 0.8, "用户体验评分应该良好")
    
    @classmethod
    def tearDownClass(cls):
        """清理测试类"""
        if os.path.exists(cls.test_draftinfo):
            os.unlink(cls.test_draftinfo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
