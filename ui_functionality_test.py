#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI功能专项测试
=================================

此脚本专门测试UI界面功能，验证：
1. UI模块的正确导入
2. 主窗口、训练面板、进度看板等组件的可用性
3. UI资源文件的完整性
4. 主题和样式系统的功能

测试策略：
- 避免创建实际的Qt应用程序实例
- 只测试模块导入和类定义
- 验证UI资源文件的存在性
- 测试UI配置的正确性
"""

import os
import sys
import time
import json
import logging
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UIFunctionalityTest:
    """UI功能测试器"""
    
    def __init__(self):
        self.test_results = []
        self.test_data_dir = PROJECT_ROOT / "test_output" / "ui_functionality_test"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("UI功能测试器初始化完成")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有UI功能测试"""
        logger.info("开始执行UI功能测试")
        start_time = time.time()
        
        try:
            # 1. 测试UI模块导入
            self._test_ui_module_imports()
            
            # 2. 测试UI组件可用性
            self._test_ui_components_availability()
            
            # 3. 测试UI资源文件
            self._test_ui_resources()
            
            # 4. 测试UI配置
            self._test_ui_configuration()
            
            # 5. 测试主题系统
            self._test_theme_system()
            
        except Exception as e:
            logger.error(f"测试执行过程中发生错误: {e}")
        
        # 生成测试报告
        total_time = time.time() - start_time
        report = self._generate_test_report(total_time)
        
        logger.info(f"UI功能测试完成，总耗时: {total_time:.2f}秒")
        return report
    
    def _test_ui_module_imports(self):
        """测试UI模块导入"""
        logger.info("测试UI模块导入...")
        
        ui_modules = [
            'simple_ui_fixed',
            'src.ui.main_window',
            'src.ui.training_panel',
            'src.ui.progress_dashboard',
            'src.ui.components',
            'src.ui.alert_manager',
            'src.ui.realtime_charts'
        ]
        
        import_results = []
        successful_imports = 0
        
        for module_name in ui_modules:
            try:
                # 检查模块是否存在
                spec = importlib.util.find_spec(module_name)
                if spec is not None:
                    import_results.append({
                        'module': module_name,
                        'found': True,
                        'path': str(spec.origin) if spec.origin else 'built-in',
                        'imported': False
                    })
                    
                    # 尝试导入（但不创建实例）
                    try:
                        module = importlib.import_module(module_name)
                        import_results[-1]['imported'] = True
                        import_results[-1]['attributes'] = [attr for attr in dir(module) 
                                                          if not attr.startswith('_')][:5]
                        successful_imports += 1
                    except Exception as e:
                        import_results[-1]['import_error'] = str(e)
                else:
                    import_results.append({
                        'module': module_name,
                        'found': False,
                        'imported': False
                    })
                    
            except Exception as e:
                import_results.append({
                    'module': module_name,
                    'found': False,
                    'imported': False,
                    'error': str(e)
                })
        
        success_rate = (successful_imports / len(ui_modules)) * 100
        
        self.test_results.append({
            'test_name': 'UI模块导入测试',
            'success': success_rate >= 70,  # 70%以上成功率视为通过
            'details': {
                'total_modules': len(ui_modules),
                'successful_imports': successful_imports,
                'success_rate_percent': success_rate,
                'import_results': import_results
            }
        })
        
        if success_rate >= 70:
            logger.info(f"✓ UI模块导入测试通过，成功率: {success_rate:.1f}%")
        else:
            logger.error(f"✗ UI模块导入测试失败，成功率: {success_rate:.1f}%")
    
    def _test_ui_components_availability(self):
        """测试UI组件可用性"""
        logger.info("测试UI组件可用性...")
        
        try:
            # 检查PyQt6可用性
            pyqt6_available = False
            pyqt6_version = "unknown"
            try:
                import PyQt6
                pyqt6_available = True
                pyqt6_version = getattr(PyQt6, '__version__', 'unknown')
            except ImportError:
                pass
            
            # 检查主要UI类的定义
            ui_classes = []
            
            # 检查simple_ui_fixed中的主窗口类
            try:
                import simple_ui_fixed
                if hasattr(simple_ui_fixed, 'VisionAIClipsMaster'):
                    ui_classes.append({
                        'class_name': 'VisionAIClipsMaster',
                        'module': 'simple_ui_fixed',
                        'available': True
                    })
                else:
                    ui_classes.append({
                        'class_name': 'VisionAIClipsMaster',
                        'module': 'simple_ui_fixed',
                        'available': False,
                        'reason': 'Class not found in module'
                    })
            except ImportError as e:
                ui_classes.append({
                    'class_name': 'VisionAIClipsMaster',
                    'module': 'simple_ui_fixed',
                    'available': False,
                    'reason': f'Module import failed: {e}'
                })
            
            # 检查其他UI组件
            other_components = [
                ('src.ui.training_panel', 'TrainingPanel'),
                ('src.ui.progress_dashboard', 'ProgressDashboard'),
                ('src.ui.alert_manager', 'AlertManager')
            ]
            
            for module_name, class_name in other_components:
                try:
                    spec = importlib.util.find_spec(module_name)
                    if spec is not None:
                        ui_classes.append({
                            'class_name': class_name,
                            'module': module_name,
                            'available': True,
                            'note': 'Module found but class not verified'
                        })
                    else:
                        ui_classes.append({
                            'class_name': class_name,
                            'module': module_name,
                            'available': False,
                            'reason': 'Module not found'
                        })
                except Exception as e:
                    ui_classes.append({
                        'class_name': class_name,
                        'module': module_name,
                        'available': False,
                        'reason': str(e)
                    })
            
            available_components = sum(1 for comp in ui_classes if comp['available'])
            availability_rate = (available_components / len(ui_classes)) * 100
            
            self.test_results.append({
                'test_name': 'UI组件可用性测试',
                'success': pyqt6_available and availability_rate >= 50,
                'details': {
                    'pyqt6_available': pyqt6_available,
                    'pyqt6_version': pyqt6_version,
                    'total_components': len(ui_classes),
                    'available_components': available_components,
                    'availability_rate_percent': availability_rate,
                    'ui_classes': ui_classes
                }
            })
            
            if pyqt6_available and availability_rate >= 50:
                logger.info(f"✓ UI组件可用性测试通过，可用率: {availability_rate:.1f}%")
            else:
                logger.error(f"✗ UI组件可用性测试失败，PyQt6: {pyqt6_available}, 可用率: {availability_rate:.1f}%")
            
        except Exception as e:
            logger.error(f"✗ UI组件可用性测试失败: {e}")
            self.test_results.append({
                'test_name': 'UI组件可用性测试',
                'success': False,
                'error': str(e)
            })
    
    def _test_ui_resources(self):
        """测试UI资源文件"""
        logger.info("测试UI资源文件...")
        
        try:
            # 检查UI资源目录
            ui_dirs = [
                PROJECT_ROOT / "ui",
                PROJECT_ROOT / "ui" / "assets",
                PROJECT_ROOT / "ui" / "themes",
                PROJECT_ROOT / "src" / "ui"
            ]
            
            dir_results = []
            for ui_dir in ui_dirs:
                dir_results.append({
                    'path': str(ui_dir),
                    'exists': ui_dir.exists(),
                    'is_directory': ui_dir.is_dir() if ui_dir.exists() else False
                })
            
            # 检查样式文件
            style_files = [
                PROJECT_ROOT / "ui" / "assets" / "style.qss",
                PROJECT_ROOT / "src" / "ui" / "assets" / "style.qss"
            ]
            
            style_results = []
            for style_file in style_files:
                style_results.append({
                    'path': str(style_file),
                    'exists': style_file.exists(),
                    'size_bytes': style_file.stat().st_size if style_file.exists() else 0
                })
            
            # 检查图标文件
            icon_dirs = [
                PROJECT_ROOT / "ui" / "assets" / "icons",
                PROJECT_ROOT / "src" / "ui" / "assets" / "icons"
            ]
            
            icon_results = []
            for icon_dir in icon_dirs:
                if icon_dir.exists():
                    icon_files = list(icon_dir.glob("*.png")) + list(icon_dir.glob("*.svg"))
                    icon_results.append({
                        'path': str(icon_dir),
                        'exists': True,
                        'icon_count': len(icon_files),
                        'icon_files': [f.name for f in icon_files[:5]]  # 只显示前5个
                    })
                else:
                    icon_results.append({
                        'path': str(icon_dir),
                        'exists': False,
                        'icon_count': 0
                    })
            
            existing_dirs = sum(1 for result in dir_results if result['exists'])
            existing_styles = sum(1 for result in style_results if result['exists'])
            
            self.test_results.append({
                'test_name': 'UI资源文件测试',
                'success': existing_dirs >= 2,  # 至少2个目录存在
                'details': {
                    'ui_directories': dir_results,
                    'style_files': style_results,
                    'icon_directories': icon_results,
                    'existing_dirs_count': existing_dirs,
                    'existing_styles_count': existing_styles
                }
            })
            
            if existing_dirs >= 2:
                logger.info(f"✓ UI资源文件测试通过，存在{existing_dirs}个UI目录")
            else:
                logger.error(f"✗ UI资源文件测试失败，只有{existing_dirs}个UI目录存在")
            
        except Exception as e:
            logger.error(f"✗ UI资源文件测试失败: {e}")
            self.test_results.append({
                'test_name': 'UI资源文件测试',
                'success': False,
                'error': str(e)
            })
    
    def _test_ui_configuration(self):
        """测试UI配置"""
        logger.info("测试UI配置...")
        
        try:
            # 检查UI配置文件
            config_files = [
                PROJECT_ROOT / "configs" / "ui_settings.yaml",
                PROJECT_ROOT / "configs" / "ui_optimization.json",
                PROJECT_ROOT / "src" / "ui" / "config"
            ]
            
            config_results = []
            for config_file in config_files:
                if config_file.exists():
                    if config_file.is_file():
                        try:
                            content = config_file.read_text(encoding='utf-8')
                            config_results.append({
                                'path': str(config_file),
                                'exists': True,
                                'type': 'file',
                                'size_bytes': len(content),
                                'valid': len(content) > 0
                            })
                        except Exception as e:
                            config_results.append({
                                'path': str(config_file),
                                'exists': True,
                                'type': 'file',
                                'valid': False,
                                'error': str(e)
                            })
                    else:
                        config_results.append({
                            'path': str(config_file),
                            'exists': True,
                            'type': 'directory'
                        })
                else:
                    config_results.append({
                        'path': str(config_file),
                        'exists': False
                    })
            
            existing_configs = sum(1 for result in config_results if result['exists'])
            
            self.test_results.append({
                'test_name': 'UI配置测试',
                'success': existing_configs >= 1,  # 至少1个配置文件存在
                'details': {
                    'config_files': config_results,
                    'existing_configs_count': existing_configs
                }
            })
            
            if existing_configs >= 1:
                logger.info(f"✓ UI配置测试通过，存在{existing_configs}个配置文件")
            else:
                logger.error(f"✗ UI配置测试失败，没有找到UI配置文件")
            
        except Exception as e:
            logger.error(f"✗ UI配置测试失败: {e}")
            self.test_results.append({
                'test_name': 'UI配置测试',
                'success': False,
                'error': str(e)
            })
    
    def _test_theme_system(self):
        """测试主题系统"""
        logger.info("测试主题系统...")
        
        try:
            # 检查主题相关模块
            theme_modules = [
                'src.ui.theme_switcher',
                'src.ui.theme_settings_dialog'
            ]
            
            theme_results = []
            for module_name in theme_modules:
                try:
                    spec = importlib.util.find_spec(module_name)
                    if spec is not None:
                        theme_results.append({
                            'module': module_name,
                            'available': True,
                            'path': str(spec.origin) if spec.origin else 'built-in'
                        })
                    else:
                        theme_results.append({
                            'module': module_name,
                            'available': False,
                            'reason': 'Module not found'
                        })
                except Exception as e:
                    theme_results.append({
                        'module': module_name,
                        'available': False,
                        'reason': str(e)
                    })
            
            available_theme_modules = sum(1 for result in theme_results if result['available'])
            
            self.test_results.append({
                'test_name': '主题系统测试',
                'success': available_theme_modules >= 1,  # 至少1个主题模块可用
                'details': {
                    'theme_modules': theme_results,
                    'available_theme_modules': available_theme_modules
                }
            })
            
            if available_theme_modules >= 1:
                logger.info(f"✓ 主题系统测试通过，{available_theme_modules}个主题模块可用")
            else:
                logger.error(f"✗ 主题系统测试失败，没有可用的主题模块")
            
        except Exception as e:
            logger.error(f"✗ 主题系统测试失败: {e}")
            self.test_results.append({
                'test_name': '主题系统测试',
                'success': False,
                'error': str(e)
            })

    def _generate_test_report(self, total_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        report = {
            'summary': {
                'test_type': 'UI功能测试',
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': round(total_time, 2),
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results
        }

        # 保存报告
        report_path = self.test_data_dir / f"ui_functionality_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        self._print_test_summary(report)

        return report

    def _print_test_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        summary = report['summary']

        print("\n" + "="*60)
        print("UI功能测试报告")
        print("="*60)
        print(f"测试时间: {summary['timestamp']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print(f"总耗时: {summary['total_duration']:.2f}秒")
        print("-"*60)

        # 打印各测试结果
        for result in self.test_results:
            status = "✓" if result['success'] else "✗"
            print(f"{status} {result['test_name']}")
            if not result['success']:
                print(f"  错误: {result.get('error', '测试失败')}")

        print("="*60)

        if summary['failed_tests'] > 0:
            print("⚠️  发现问题，需要进一步检查UI功能")
        else:
            print("🎉 UI功能测试全部通过！")

        print("="*60)


def main():
    """主函数"""
    print("VisionAI-ClipsMaster UI功能专项测试")
    print("="*50)

    # 创建测试器
    tester = UIFunctionalityTest()

    # 运行所有测试
    try:
        report = tester.run_all_tests()

        # 根据测试结果返回适当的退出码
        if report['summary']['failed_tests'] > 0:
            sys.exit(1)  # 有测试失败
        else:
            sys.exit(0)  # 所有测试通过

    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(2)
    except Exception as e:
        print(f"\n测试执行过程中发生严重错误: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
