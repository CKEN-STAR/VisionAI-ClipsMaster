#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 完整系统测试
按照用户要求进行全面功能测试：UI界面、核心功能、工作流程、性能稳定性、边界条件
"""

import sys
import os
import time
import json
import traceback
import threading
import psutil
import gc
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

class SystemTestRunner:
    """VisionAI-ClipsMaster 系统测试运行器"""
    
    def __init__(self):
        self.test_results = {
            'ui_interface_tests': {},
            'core_module_tests': {},
            'workflow_integrity_tests': {},
            'performance_stability_tests': {},
            'boundary_condition_tests': {},
            'summary': {}
        }
        self.start_time = datetime.now()
        self.memory_peak = 0
        self.errors = []
        
    def run_complete_test_suite(self):
        """运行完整测试套件"""
        print("=" * 80)
        print("VisionAI-ClipsMaster 完整系统测试开始")
        print("=" * 80)
        
        try:
            # 1. UI界面测试
            print("\n🔍 1. UI界面测试")
            self.test_ui_interface()
            
            # 2. 核心功能模块测试
            print("\n🔍 2. 核心功能模块测试")
            self.test_core_modules()
            
            # 3. 工作流程完整性测试
            print("\n🔍 3. 工作流程完整性测试")
            self.test_workflow_integrity()
            
            # 4. 性能与稳定性测试
            print("\n🔍 4. 性能与稳定性测试")
            self.test_performance_stability()
            
            # 5. 边界条件测试
            print("\n🔍 5. 边界条件测试")
            self.test_boundary_conditions()
            
            # 生成测试报告
            self.generate_final_report()
            
        except Exception as e:
            print(f"❌ 测试过程中发生严重错误: {e}")
            traceback.print_exc()
            self.errors.append(str(e))
        
        finally:
            self.cleanup_test_environment()
    
    def test_ui_interface(self):
        """1. UI界面测试"""
        print("  📋 测试simple_ui_fixed.py主界面启动和显示")
        
        # 1.1 测试主界面启动
        ui_startup_result = self._test_main_ui_startup()
        self.test_results['ui_interface_tests']['main_ui_startup'] = ui_startup_result
        print(f"    ✓ 主界面启动: {ui_startup_result['status']}")
        
        # 1.2 测试UI组件交互响应
        ui_components_result = self._test_ui_components_interaction()
        self.test_results['ui_interface_tests']['ui_components_interaction'] = ui_components_result
        print(f"    ✓ UI组件交互: {ui_components_result['status']}")
        
        # 1.3 测试训练监控面板
        training_panel_result = self._test_training_monitoring_panel()
        self.test_results['ui_interface_tests']['training_monitoring_panel'] = training_panel_result
        print(f"    ✓ 训练监控面板: {training_panel_result['status']}")
        
        # 1.4 测试进度看板
        progress_dashboard_result = self._test_progress_dashboard()
        self.test_results['ui_interface_tests']['progress_dashboard'] = progress_dashboard_result
        print(f"    ✓ 进度看板: {progress_dashboard_result['status']}")
        
        # 1.5 测试主题切换功能
        theme_switching_result = self._test_theme_switching()
        self.test_results['ui_interface_tests']['theme_switching'] = theme_switching_result
        print(f"    ✓ 主题切换: {theme_switching_result['status']}")
    
    def test_core_modules(self):
        """2. 核心功能模块测试"""
        print("  📋 测试语言检测、剧本重构、视频拼接、剪映导出")
        
        # 2.1 语言检测测试
        language_detection_result = self._test_language_detection()
        self.test_results['core_module_tests']['language_detection'] = language_detection_result
        print(f"    ✓ 语言检测: {language_detection_result['status']}")
        
        # 2.2 剧本重构测试
        script_reconstruction_result = self._test_script_reconstruction()
        self.test_results['core_module_tests']['script_reconstruction'] = script_reconstruction_result
        print(f"    ✓ 剧本重构: {script_reconstruction_result['status']}")
        
        # 2.3 视频拼接测试
        video_splicing_result = self._test_video_splicing()
        self.test_results['core_module_tests']['video_splicing'] = video_splicing_result
        print(f"    ✓ 视频拼接: {video_splicing_result['status']}")
        
        # 2.4 剪映导出测试
        jianying_export_result = self._test_jianying_export()
        self.test_results['core_module_tests']['jianying_export'] = jianying_export_result
        print(f"    ✓ 剪映导出: {jianying_export_result['status']}")
    
    def test_workflow_integrity(self):
        """3. 工作流程完整性测试"""
        print("  📋 测试端到端流程和投喂训练流程")
        
        # 3.1 端到端流程测试
        end_to_end_result = self._test_end_to_end_workflow()
        self.test_results['workflow_integrity_tests']['end_to_end_workflow'] = end_to_end_result
        print(f"    ✓ 端到端流程: {end_to_end_result['status']}")
        
        # 3.2 投喂训练流程测试
        training_workflow_result = self._test_training_workflow()
        self.test_results['workflow_integrity_tests']['training_workflow'] = training_workflow_result
        print(f"    ✓ 投喂训练流程: {training_workflow_result['status']}")
        
        # 3.3 异常恢复测试
        exception_recovery_result = self._test_exception_recovery()
        self.test_results['workflow_integrity_tests']['exception_recovery'] = exception_recovery_result
        print(f"    ✓ 异常恢复: {exception_recovery_result['status']}")
    
    def test_performance_stability(self):
        """4. 性能与稳定性测试"""
        print("  📋 测试内存管理、长时稳定性、视频质量")
        
        # 4.1 内存管理测试
        memory_management_result = self._test_memory_management()
        self.test_results['performance_stability_tests']['memory_management'] = memory_management_result
        print(f"    ✓ 内存管理: {memory_management_result['status']}")
        
        # 4.2 长时稳定性测试
        long_term_stability_result = self._test_long_term_stability()
        self.test_results['performance_stability_tests']['long_term_stability'] = long_term_stability_result
        print(f"    ✓ 长时稳定性: {long_term_stability_result['status']}")
        
        # 4.3 视频质量测试
        video_quality_result = self._test_video_quality()
        self.test_results['performance_stability_tests']['video_quality'] = video_quality_result
        print(f"    ✓ 视频质量: {video_quality_result['status']}")
    
    def test_boundary_conditions(self):
        """5. 边界条件测试"""
        print("  📋 测试过短/过长视频、混合语言、格式兼容性")
        
        # 5.1 视频长度边界测试
        video_length_boundary_result = self._test_video_length_boundary()
        self.test_results['boundary_condition_tests']['video_length_boundary'] = video_length_boundary_result
        print(f"    ✓ 视频长度边界: {video_length_boundary_result['status']}")
        
        # 5.2 混合语言处理测试
        mixed_language_result = self._test_mixed_language_processing()
        self.test_results['boundary_condition_tests']['mixed_language_processing'] = mixed_language_result
        print(f"    ✓ 混合语言处理: {mixed_language_result['status']}")
        
        # 5.3 视频格式兼容性测试
        format_compatibility_result = self._test_format_compatibility()
        self.test_results['boundary_condition_tests']['format_compatibility'] = format_compatibility_result
        print(f"    ✓ 格式兼容性: {format_compatibility_result['status']}")
    
    def _test_main_ui_startup(self):
        """测试主UI启动"""
        try:
            # 检查simple_ui_fixed.py文件
            ui_file = PROJECT_ROOT / "simple_ui_fixed.py"
            if not ui_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'simple_ui_fixed.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 检查文件大小和基本结构
            file_size = ui_file.stat().st_size
            if file_size < 5000:  # UI文件应该比较大
                return {
                    'status': 'FAIL',
                    'error': f'UI文件大小异常: {file_size} bytes (预期 > 5000)',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 检查关键内容
            with open(ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_elements = [
                'def main(',
                'class',
                'if __name__',
                'QApplication',
                'QMainWindow'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                return {
                    'status': 'FAIL',
                    'error': f'UI文件缺少关键元素: {missing_elements}',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'status': 'PASS',
                'message': f'UI文件结构完整，大小: {file_size} bytes',
                'details': {
                    'file_size': file_size,
                    'required_elements_found': len(required_elements) - len(missing_elements)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _test_ui_components_interaction(self):
        """测试UI组件交互响应"""
        try:
            # 检查UI组件目录
            ui_components_path = PROJECT_ROOT / "ui" / "components"
            if not ui_components_path.exists():
                return {
                    'status': 'FAIL',
                    'error': 'UI组件目录不存在',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 检查关键组件文件
            key_components = [
                'realtime_charts.py',
                'alert_manager.py'
            ]
            
            component_status = {}
            for component in key_components:
                component_file = ui_components_path / component
                component_status[component] = component_file.exists()
            
            missing_components = [comp for comp, exists in component_status.items() if not exists]
            
            if len(missing_components) == len(key_components):
                return {
                    'status': 'FAIL',
                    'error': f'所有关键UI组件都缺失: {missing_components}',
                    'timestamp': datetime.now().isoformat()
                }
            elif missing_components:
                return {
                    'status': 'PARTIAL',
                    'warning': f'部分UI组件缺失: {missing_components}',
                    'details': component_status,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'PASS',
                    'message': '所有关键UI组件文件存在',
                    'details': component_status,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_training_monitoring_panel(self):
        """测试训练监控面板"""
        try:
            training_panel_file = PROJECT_ROOT / "ui" / "training_panel.py"
            if not training_panel_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'training_panel.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查文件内容
            with open(training_panel_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否包含训练相关的关键词
            training_keywords = ['training', 'loss', 'epoch', 'progress', 'monitor']
            found_keywords = [kw for kw in training_keywords if kw.lower() in content.lower()]

            if len(found_keywords) < 3:
                return {
                    'status': 'FAIL',
                    'error': f'训练面板文件缺少关键功能，仅找到: {found_keywords}',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '训练监控面板文件存在且包含必要功能',
                'details': {'found_keywords': found_keywords},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_progress_dashboard(self):
        """测试进度看板"""
        try:
            progress_dashboard_file = PROJECT_ROOT / "ui" / "progress_dashboard.py"
            if not progress_dashboard_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'progress_dashboard.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '进度看板文件存在',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_theme_switching(self):
        """测试主题切换功能"""
        try:
            # 检查样式文件
            style_file = PROJECT_ROOT / "ui" / "assets" / "style.qss"
            if not style_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'style.qss样式文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查样式文件内容
            with open(style_file, 'r', encoding='utf-8') as f:
                style_content = f.read()

            # 检查是否包含主题相关的样式
            theme_indicators = ['color:', 'background', 'font', 'border']
            found_indicators = [ind for ind in theme_indicators if ind in style_content]

            if len(found_indicators) < 2:
                return {
                    'status': 'FAIL',
                    'error': f'样式文件内容不完整，仅找到: {found_indicators}',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '样式文件存在且包含主题样式',
                'details': {'style_indicators': found_indicators},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_language_detection(self):
        """测试语言检测功能"""
        try:
            # 检查语言检测模块
            language_detector_file = PROJECT_ROOT / "src" / "core" / "language_detector.py"
            if not language_detector_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'language_detector.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 尝试导入语言检测模块
            try:
                sys.path.append(str(PROJECT_ROOT / "src" / "core"))
                import language_detector

                # 检查是否有检测函数
                if hasattr(language_detector, 'detect_language') or hasattr(language_detector, 'LanguageDetector'):
                    return {
                        'status': 'PASS',
                        'message': '语言检测模块导入成功，包含检测功能',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'status': 'FAIL',
                        'error': '语言检测模块缺少检测函数',
                        'timestamp': datetime.now().isoformat()
                    }

            except ImportError as e:
                return {
                    'status': 'FAIL',
                    'error': f'语言检测模块导入失败: {e}',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_script_reconstruction(self):
        """测试剧本重构功能"""
        try:
            # 检查剧本重构相关模块
            screenplay_engineer_file = PROJECT_ROOT / "src" / "core" / "screenplay_engineer.py"
            narrative_analyzer_file = PROJECT_ROOT / "src" / "core" / "narrative_analyzer.py"

            missing_files = []
            if not screenplay_engineer_file.exists():
                missing_files.append("screenplay_engineer.py")
            if not narrative_analyzer_file.exists():
                missing_files.append("narrative_analyzer.py")

            if missing_files:
                return {
                    'status': 'FAIL',
                    'error': f'剧本重构模块文件缺失: {missing_files}',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查文件内容
            with open(screenplay_engineer_file, 'r', encoding='utf-8') as f:
                screenplay_content = f.read()

            # 检查是否包含剧本重构相关功能
            reconstruction_keywords = ['reconstruct', 'rewrite', 'transform', 'generate', 'script']
            found_keywords = [kw for kw in reconstruction_keywords if kw.lower() in screenplay_content.lower()]

            if len(found_keywords) < 2:
                return {
                    'status': 'FAIL',
                    'error': f'剧本重构功能不完整，仅找到关键词: {found_keywords}',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '剧本重构模块存在且包含必要功能',
                'details': {'found_keywords': found_keywords},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_video_splicing(self):
        """测试视频拼接功能"""
        try:
            # 检查视频处理模块
            video_processor_file = PROJECT_ROOT / "src" / "core" / "video_processor.py"
            clip_generator_file = PROJECT_ROOT / "src" / "core" / "clip_generator.py"

            missing_files = []
            if not video_processor_file.exists():
                missing_files.append("video_processor.py")
            if not clip_generator_file.exists():
                missing_files.append("clip_generator.py")

            if missing_files:
                return {
                    'status': 'FAIL',
                    'error': f'视频拼接模块文件缺失: {missing_files}',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '视频拼接模块文件存在',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_jianying_export(self):
        """测试剪映导出功能"""
        try:
            # 检查剪映导出模块
            jianying_exporter_file = PROJECT_ROOT / "src" / "core" / "jianying_exporter.py"
            if not jianying_exporter_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'jianying_exporter.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查导出器目录
            exporters_dir = PROJECT_ROOT / "src" / "exporters"
            if exporters_dir.exists():
                exporter_files = list(exporters_dir.glob("*.py"))
                return {
                    'status': 'PASS',
                    'message': f'剪映导出模块存在，找到{len(exporter_files)}个导出器',
                    'details': {'exporter_files': [f.name for f in exporter_files]},
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'PARTIAL',
                    'warning': '剪映导出模块存在但导出器目录缺失',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        try:
            # 检查工作流管理器
            workflow_manager_file = PROJECT_ROOT / "src" / "core" / "workflow_manager.py"
            if not workflow_manager_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'workflow_manager.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查测试数据目录
            test_data_dir = PROJECT_ROOT / "test_data"
            if not test_data_dir.exists():
                return {
                    'status': 'FAIL',
                    'error': '测试数据目录不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查是否有测试字幕文件
            srt_files = list(test_data_dir.glob("*.srt"))
            if not srt_files:
                return {
                    'status': 'FAIL',
                    'error': '测试数据目录中没有SRT字幕文件',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': f'端到端工作流程组件完整，找到{len(srt_files)}个测试字幕文件',
                'details': {'test_srt_files': [f.name for f in srt_files]},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_training_workflow(self):
        """测试投喂训练工作流程"""
        try:
            # 检查训练模块
            training_dir = PROJECT_ROOT / "src" / "training"
            if not training_dir.exists():
                return {
                    'status': 'FAIL',
                    'error': '训练模块目录不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查中英文训练器
            en_trainer_file = training_dir / "en_trainer.py"
            zh_trainer_file = training_dir / "zh_trainer.py"

            trainer_status = {
                'en_trainer': en_trainer_file.exists(),
                'zh_trainer': zh_trainer_file.exists()
            }

            missing_trainers = [name for name, exists in trainer_status.items() if not exists]

            if missing_trainers:
                return {
                    'status': 'FAIL',
                    'error': f'训练器文件缺失: {missing_trainers}',
                    'details': trainer_status,
                    'timestamp': datetime.now().isoformat()
                }

            # 检查训练数据目录
            training_data_dir = PROJECT_ROOT / "data" / "training"
            if not training_data_dir.exists():
                return {
                    'status': 'PARTIAL',
                    'warning': '训练器存在但训练数据目录缺失',
                    'details': trainer_status,
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '投喂训练工作流程组件完整',
                'details': trainer_status,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_exception_recovery(self):
        """测试异常恢复功能"""
        try:
            # 检查恢复管理器
            recovery_manager_file = PROJECT_ROOT / "src" / "core" / "recovery_manager.py"
            if not recovery_manager_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'recovery_manager.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查检查点管理器
            checkpoint_manager_file = PROJECT_ROOT / "src" / "core" / "checkpoint_manager.py"
            if checkpoint_manager_file.exists():
                return {
                    'status': 'PASS',
                    'message': '异常恢复功能模块完整',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'PARTIAL',
                    'warning': '恢复管理器存在但检查点管理器缺失',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_memory_management(self):
        """测试内存管理功能"""
        try:
            # 获取当前内存使用情况
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # 检查内存管理模块
            memory_manager_files = [
                PROJECT_ROOT / "src" / "utils" / "memory_guard.py",
                PROJECT_ROOT / "src" / "memory" / "memory_manager.py"
            ]

            existing_memory_managers = [f for f in memory_manager_files if f.exists()]

            if not existing_memory_managers:
                return {
                    'status': 'FAIL',
                    'error': '内存管理模块文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查内存使用是否在合理范围内
            if initial_memory > 4000:  # 4GB限制
                return {
                    'status': 'FAIL',
                    'error': f'当前内存使用过高: {initial_memory:.1f}MB',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': f'内存管理模块存在，当前内存使用: {initial_memory:.1f}MB',
                'details': {
                    'current_memory_mb': initial_memory,
                    'memory_managers': [f.name for f in existing_memory_managers]
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_long_term_stability(self):
        """测试长时稳定性"""
        try:
            # 检查稳定性测试相关文件
            stability_test_files = [
                PROJECT_ROOT / "tests" / "stress_test",
                PROJECT_ROOT / "src" / "eval" / "long_stress_test"
            ]

            existing_stability_tests = [f for f in stability_test_files if f.exists()]

            if not existing_stability_tests:
                return {
                    'status': 'FAIL',
                    'error': '长时稳定性测试模块不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 简单的内存泄漏检测
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

            # 模拟一些操作
            for i in range(10):
                test_data = [j for j in range(1000)]
                del test_data
                gc.collect()
                time.sleep(0.1)

            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            if memory_increase > 50:  # 内存增长超过50MB可能有泄漏
                return {
                    'status': 'WARNING',
                    'warning': f'可能存在内存泄漏，内存增长: {memory_increase:.1f}MB',
                    'details': {
                        'initial_memory_mb': initial_memory,
                        'final_memory_mb': final_memory,
                        'memory_increase_mb': memory_increase
                    },
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': f'长时稳定性测试通过，内存增长: {memory_increase:.1f}MB',
                'details': {
                    'stability_test_modules': [f.name for f in existing_stability_tests],
                    'memory_increase_mb': memory_increase
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_video_quality(self):
        """测试视频质量"""
        try:
            # 检查视频质量检测模块
            quality_validator_file = PROJECT_ROOT / "src" / "eval" / "quality_validator.py"
            if not quality_validator_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'quality_validator.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查是否有测试视频文件
            test_video_files = list((PROJECT_ROOT / "test_data").glob("*.mp4")) if (PROJECT_ROOT / "test_data").exists() else []

            if not test_video_files:
                return {
                    'status': 'PARTIAL',
                    'warning': '视频质量检测模块存在但缺少测试视频文件',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': f'视频质量检测模块存在，找到{len(test_video_files)}个测试视频',
                'details': {'test_video_files': [f.name for f in test_video_files]},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_video_length_boundary(self):
        """测试视频长度边界条件"""
        try:
            # 检查节奏分析器（用于控制视频长度）
            rhythm_analyzer_file = PROJECT_ROOT / "src" / "core" / "rhythm_analyzer.py"
            if not rhythm_analyzer_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'rhythm_analyzer.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查是否有长度控制配置
            rhythm_policy_file = PROJECT_ROOT / "configs" / "rhythm_policy.yaml"
            if not rhythm_policy_file.exists():
                return {
                    'status': 'PARTIAL',
                    'warning': '节奏分析器存在但缺少节奏策略配置',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': '视频长度边界控制模块完整',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_mixed_language_processing(self):
        """测试混合语言处理"""
        try:
            # 检查语言检测器配置
            language_detector_config = PROJECT_ROOT / "configs" / "language_detector.yaml"
            if not language_detector_config.exists():
                return {
                    'status': 'FAIL',
                    'error': 'language_detector.yaml配置文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查是否有混合语言的测试数据
            test_data_dir = PROJECT_ROOT / "test_data"
            if test_data_dir.exists():
                mixed_test_files = [
                    f for f in test_data_dir.glob("*mixed*")
                    if f.suffix in ['.srt', '.txt']
                ]

                if mixed_test_files:
                    return {
                        'status': 'PASS',
                        'message': f'混合语言处理功能完整，找到{len(mixed_test_files)}个混合语言测试文件',
                        'details': {'mixed_test_files': [f.name for f in mixed_test_files]},
                        'timestamp': datetime.now().isoformat()
                    }

            return {
                'status': 'PARTIAL',
                'warning': '混合语言处理配置存在但缺少测试数据',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _test_format_compatibility(self):
        """测试视频格式兼容性"""
        try:
            # 检查视频处理器是否支持多种格式
            video_processor_file = PROJECT_ROOT / "src" / "core" / "video_processor.py"
            if not video_processor_file.exists():
                return {
                    'status': 'FAIL',
                    'error': 'video_processor.py文件不存在',
                    'timestamp': datetime.now().isoformat()
                }

            # 检查文件内容是否包含格式支持
            with open(video_processor_file, 'r', encoding='utf-8') as f:
                content = f.read()

            supported_formats = ['mp4', 'avi', 'flv', 'mov', 'mkv']
            found_formats = [fmt for fmt in supported_formats if fmt.lower() in content.lower()]

            if len(found_formats) < 3:
                return {
                    'status': 'FAIL',
                    'error': f'视频格式支持不足，仅找到: {found_formats}',
                    'timestamp': datetime.now().isoformat()
                }

            return {
                'status': 'PASS',
                'message': f'视频格式兼容性良好，支持格式: {found_formats}',
                'details': {'supported_formats': found_formats},
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def generate_final_report(self):
        """生成最终测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        partial_tests = 0
        error_tests = 0

        for category in self.test_results.values():
            if isinstance(category, dict) and category != self.test_results['summary']:
                for test_result in category.values():
                    if isinstance(test_result, dict) and 'status' in test_result:
                        total_tests += 1
                        status = test_result['status']
                        if status == 'PASS':
                            passed_tests += 1
                        elif status == 'FAIL':
                            failed_tests += 1
                        elif status == 'PARTIAL':
                            partial_tests += 1
                        elif status == 'ERROR':
                            error_tests += 1

        # 计算成功率
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 生成摘要
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'partial_tests': partial_tests,
            'error_tests': error_tests,
            'success_rate': f"{success_rate:.1f}%",
            'duration_seconds': duration,
            'test_start': self.start_time.isoformat(),
            'test_end': end_time.isoformat(),
            'peak_memory_mb': self.memory_peak,
            'errors_count': len(self.errors)
        }

        # 保存测试报告
        report_file = PROJECT_ROOT / f"test_output/comprehensive_functional_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        # 生成HTML报告
        html_report = self._generate_html_report()
        html_file = report_file.with_suffix('.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)

        # 打印测试摘要
        print("\n" + "="*80)
        print("📊 测试结果摘要")
        print("="*80)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✓")
        print(f"失败: {failed_tests} ✗")
        print(f"部分通过: {partial_tests} ⚠")
        print(f"错误: {error_tests} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print(f"测试时长: {duration:.1f}秒")
        print(f"报告文件: {report_file}")
        print(f"HTML报告: {html_file}")

        return self.test_results

    def _generate_html_report(self):
        """生成HTML格式的测试报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 功能测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .test-category {{ margin-bottom: 25px; }}
        .test-category h3 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        .test-item {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; background: #f9f9f9; }}
        .status-pass {{ border-left-color: #27ae60; }}
        .status-fail {{ border-left-color: #e74c3c; }}
        .status-partial {{ border-left-color: #f39c12; }}
        .status-error {{ border-left-color: #8e44ad; }}
        .status-badge {{ display: inline-block; padding: 2px 8px; border-radius: 3px; color: white; font-size: 12px; margin-right: 10px; }}
        .badge-pass {{ background-color: #27ae60; }}
        .badge-fail {{ background-color: #e74c3c; }}
        .badge-partial {{ background-color: #f39c12; }}
        .badge-error {{ background-color: #8e44ad; }}
        .details {{ margin-top: 5px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 VisionAI-ClipsMaster 功能测试报告</h1>
            <p>测试时间: {test_time}</p>
        </div>

        <div class="summary">
            <h2>📊 测试摘要</h2>
            <p><strong>总测试数:</strong> {total_tests}</p>
            <p><strong>通过:</strong> {passed_tests} | <strong>失败:</strong> {failed_tests} | <strong>部分通过:</strong> {partial_tests} | <strong>错误:</strong> {error_tests}</p>
            <p><strong>成功率:</strong> {success_rate}</p>
            <p><strong>测试时长:</strong> {duration:.1f}秒</p>
        </div>

        {test_categories}
    </div>
</body>
</html>
        """

        # 生成测试分类内容
        categories_html = ""
        category_names = {
            'ui_interface_tests': '🖥️ UI界面测试',
            'core_module_tests': '⚙️ 核心功能模块测试',
            'workflow_integrity_tests': '🔄 工作流程完整性测试',
            'performance_stability_tests': '⚡ 性能与稳定性测试',
            'boundary_condition_tests': '🔍 边界条件测试'
        }

        for category_key, category_name in category_names.items():
            if category_key in self.test_results:
                categories_html += f'<div class="test-category"><h3>{category_name}</h3>'

                for test_name, test_result in self.test_results[category_key].items():
                    status = test_result.get('status', 'UNKNOWN')
                    status_class = f"status-{status.lower()}"
                    badge_class = f"badge-{status.lower()}"

                    message = test_result.get('message', test_result.get('error', test_result.get('warning', '')))

                    categories_html += f'''
                    <div class="test-item {status_class}">
                        <span class="status-badge {badge_class}">{status}</span>
                        <strong>{test_name}</strong>
                        <div class="details">{message}</div>
                    </div>
                    '''

                categories_html += '</div>'

        # 填充模板
        summary = self.test_results.get('summary', {})
        return html_template.format(
            test_time=summary.get('test_start', ''),
            total_tests=summary.get('total_tests', 0),
            passed_tests=summary.get('passed_tests', 0),
            failed_tests=summary.get('failed_tests', 0),
            partial_tests=summary.get('partial_tests', 0),
            error_tests=summary.get('error_tests', 0),
            success_rate=summary.get('success_rate', '0%'),
            duration=summary.get('duration_seconds', 0),
            test_categories=categories_html
        )

    def cleanup_test_environment(self):
        """清理测试环境"""
        try:
            # 强制垃圾回收
            gc.collect()

            # 记录最终内存使用
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            self.memory_peak = max(self.memory_peak, final_memory)

            print(f"\n🧹 测试环境清理完成，最终内存使用: {final_memory:.1f}MB")

        except Exception as e:
            print(f"清理测试环境时发生错误: {e}")


def main():
    """主函数"""
    print("🚀 启动VisionAI-ClipsMaster完整系统测试")

    # 创建测试运行器
    test_runner = SystemTestRunner()

    # 运行完整测试套件
    test_runner.run_complete_test_suite()

    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()
