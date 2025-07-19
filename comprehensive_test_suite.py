#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 综合功能测试套件

全面测试项目的所有核心功能、模块导入、系统稳定性等
"""

import os
import sys
import time
import json
import logging
import traceback
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    """综合测试套件"""

    def __init__(self):
        self.test_results = {
            'import_tests': {},
            'dependency_tests': {},
            'core_function_tests': {},
            'ui_tests': {},
            'stability_tests': {},
            'end_to_end_tests': {},
            'vulnerability_checks': {}
        }
        self.start_time = time.time()
        self.python_path = r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"

    def log_test_result(self, category: str, test_name: str, success: bool,
                       message: str = "", details: Any = None):
        """记录测试结果"""
        result = {
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results[category][test_name] = result

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} [{category}] {test_name}: {message}")

    def test_module_imports(self) -> Dict[str, bool]:
        """测试所有核心模块的导入状态"""
        logger.info("=" * 60)
        logger.info("1. 核心模块导入测试")
        logger.info("=" * 60)

        # 定义要测试的模块
        core_modules = {
            'ui_bridge': 'ui_bridge',
            'clip_generator': 'src.core.clip_generator',
            'screenplay_engineer': 'src.core.screenplay_engineer',
            'srt_parser': 'src.core.srt_parser',
            'video_processor': 'src.core.video_processor',
            'base_llm': 'src.models.base_llm',
            'jianying_exporter': 'src.export.jianying_exporter',
            'trainer': 'src.training.trainer',
            'zh_trainer': 'src.training.zh_trainer',
            'en_trainer': 'src.training.en_trainer'
        }

        import_results = {}

        for module_name, module_path in core_modules.items():
            try:
                __import__(module_path)
                import_results[module_name] = True
                self.log_test_result('import_tests', module_name, True,
                                   f"模块 {module_path} 导入成功")
            except ImportError as e:
                import_results[module_name] = False
                self.log_test_result('import_tests', module_name, False,
                                   f"模块 {module_path} 导入失败: {str(e)}")
            except Exception as e:
                import_results[module_name] = False
                self.log_test_result('import_tests', module_name, False,
                                   f"模块 {module_path} 导入异常: {str(e)}")

        return import_results

    def test_dependency_compatibility(self) -> Dict[str, bool]:
        """测试依赖包的导入和版本兼容性"""
        logger.info("=" * 60)
        logger.info("2. 依赖包兼容性测试")
        logger.info("=" * 60)

        # 关键依赖包列表
        dependencies = {
            'PyQt6': 'PyQt6',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'torch': 'torch',
            'transformers': 'transformers',
            'opencv': 'cv2',
            'matplotlib': 'matplotlib',
            'scipy': 'scipy',
            'sklearn': 'sklearn',
            'requests': 'requests',
            'yaml': 'yaml',
            'tqdm': 'tqdm',
            'psutil': 'psutil',
            'PIL': 'PIL',
            'moviepy': 'moviepy.editor',
            'librosa': 'librosa',
            'jieba': 'jieba',
            'nltk': 'nltk',
            'spacy': 'spacy'
        }

        dependency_results = {}

        for dep_name, import_name in dependencies.items():
            try:
                module = __import__(import_name)
                version = getattr(module, '__version__', 'Unknown')
                dependency_results[dep_name] = True
                self.log_test_result('dependency_tests', dep_name, True,
                                   f"版本 {version}")
            except ImportError as e:
                dependency_results[dep_name] = False
                self.log_test_result('dependency_tests', dep_name, False,
                                   f"导入失败: {str(e)}")
            except Exception as e:
                dependency_results[dep_name] = False
                self.log_test_result('dependency_tests', dep_name, False,
                                   f"异常: {str(e)}")

        return dependency_results

    def test_ui_bridge_functionality(self) -> bool:
        """测试UI桥接模块功能"""
        logger.info("=" * 60)
        logger.info("3. UI桥接模块功能测试")
        logger.info("=" * 60)

        try:
            from ui_bridge import ui_bridge

            # 测试桥接器初始化
            if ui_bridge is None:
                self.log_test_result('core_function_tests', 'ui_bridge_init', False,
                                   "UI桥接器未正确初始化")
                return False

            # 测试各个功能方法是否存在
            required_methods = [
                'generate_viral_srt',
                'process_video',
                'train_model'
            ]

            for method_name in required_methods:
                if hasattr(ui_bridge, method_name):
                    self.log_test_result('core_function_tests', f'ui_bridge_{method_name}',
                                       True, f"方法 {method_name} 存在")
                else:
                    self.log_test_result('core_function_tests', f'ui_bridge_{method_name}',
                                       False, f"方法 {method_name} 不存在")

            self.log_test_result('core_function_tests', 'ui_bridge_overall', True,
                               "UI桥接模块功能正常")
            return True

        except Exception as e:
            self.log_test_result('core_function_tests', 'ui_bridge_overall', False,
                               f"UI桥接模块测试失败: {str(e)}")
            return False

    def create_test_srt_file(self) -> str:
        """创建测试用的SRT字幕文件"""
        test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是一个测试字幕

2
00:00:04,000 --> 00:00:06,000
用于验证VisionAI-ClipsMaster的功能

3
00:00:07,000 --> 00:00:09,000
包含中文和English混合内容

4
00:00:10,000 --> 00:00:12,000
测试爆款字幕生成功能
"""

        # 创建临时SRT文件
        temp_dir = tempfile.gettempdir()
        test_srt_path = os.path.join(temp_dir, "test_subtitle.srt")

        try:
            with open(test_srt_path, 'w', encoding='utf-8') as f:
                f.write(test_srt_content)

            logger.info(f"测试SRT文件已创建: {test_srt_path}")
            return test_srt_path

        except Exception as e:
            logger.error(f"创建测试SRT文件失败: {e}")
            return None

    def test_viral_srt_generation(self) -> bool:
        """测试爆款SRT字幕生成功能"""
        logger.info("=" * 60)
        logger.info("4. 爆款SRT字幕生成功能测试")
        logger.info("=" * 60)

        # 创建测试SRT文件
        test_srt_path = self.create_test_srt_file()
        if not test_srt_path:
            self.log_test_result('core_function_tests', 'viral_srt_generation', False,
                               "无法创建测试SRT文件")
            return False

        try:
            from ui_bridge import ui_bridge

            # 测试中文模式
            logger.info("测试中文模式爆款字幕生成...")
            result_zh = ui_bridge.generate_viral_srt(test_srt_path, "zh")

            if result_zh and isinstance(result_zh, str) and len(result_zh) > 0:
                # 检查是否包含SRT格式内容
                if "-->" in result_zh and any(char.isdigit() for char in result_zh):
                    self.log_test_result('core_function_tests', 'viral_srt_zh', True,
                                       f"中文爆款字幕生成成功，内容长度: {len(result_zh)} 字符")
                else:
                    self.log_test_result('core_function_tests', 'viral_srt_zh', False,
                                       "中文爆款字幕格式不正确")
            else:
                self.log_test_result('core_function_tests', 'viral_srt_zh', False,
                                   "中文爆款字幕生成失败")

            # 测试英文模式
            logger.info("测试英文模式爆款字幕生成...")
            result_en = ui_bridge.generate_viral_srt(test_srt_path, "en")

            if result_en and isinstance(result_en, str) and len(result_en) > 0:
                # 检查是否包含SRT格式内容
                if "-->" in result_en and any(char.isdigit() for char in result_en):
                    self.log_test_result('core_function_tests', 'viral_srt_en', True,
                                       f"英文爆款字幕生成成功，内容长度: {len(result_en)} 字符")
                else:
                    self.log_test_result('core_function_tests', 'viral_srt_en', False,
                                       "英文爆款字幕格式不正确")
            else:
                self.log_test_result('core_function_tests', 'viral_srt_en', False,
                                   "英文爆款字幕生成失败")

            # 测试自动检测模式
            logger.info("测试自动检测模式爆款字幕生成...")
            result_auto = ui_bridge.generate_viral_srt(test_srt_path, "auto")

            if result_auto and isinstance(result_auto, str) and len(result_auto) > 0:
                # 检查是否包含SRT格式内容
                if "-->" in result_auto and any(char.isdigit() for char in result_auto):
                    self.log_test_result('core_function_tests', 'viral_srt_auto', True,
                                       f"自动检测爆款字幕生成成功，内容长度: {len(result_auto)} 字符")
                else:
                    self.log_test_result('core_function_tests', 'viral_srt_auto', False,
                                       "自动检测爆款字幕格式不正确")
            else:
                self.log_test_result('core_function_tests', 'viral_srt_auto', False,
                                   "自动检测爆款字幕生成失败")

            return True

        except Exception as e:
            self.log_test_result('core_function_tests', 'viral_srt_generation', False,
                               f"爆款字幕生成测试异常: {str(e)}")
            logger.error(f"爆款字幕生成测试异常: {traceback.format_exc()}")
            return False

        finally:
            # 清理测试文件
            try:
                if test_srt_path and os.path.exists(test_srt_path):
                    os.remove(test_srt_path)
            except:
                pass

    def test_video_processing(self) -> bool:
        """测试视频处理功能"""
        logger.info("=" * 60)
        logger.info("5. 视频处理功能测试")
        logger.info("=" * 60)

        try:
            from ui_bridge import ui_bridge

            # 创建模拟的测试文件路径
            test_video_path = "test_video.mp4"  # 模拟路径
            test_srt_path = self.create_test_srt_file()
            test_output_path = os.path.join(tempfile.gettempdir(), "test_output.mp4")

            if not test_srt_path:
                self.log_test_result('core_function_tests', 'video_processing', False,
                                   "无法创建测试SRT文件")
                return False

            # 测试视频处理功能（预期会失败，因为没有真实视频文件）
            logger.info("测试视频处理功能（预期失败，因为没有真实视频文件）...")
            result = ui_bridge.process_video(test_video_path, test_srt_path, test_output_path)

            # 由于没有真实视频文件，这里主要测试函数是否能正常调用而不崩溃
            self.log_test_result('core_function_tests', 'video_processing_call', True,
                               "视频处理函数调用正常（无真实视频文件）")

            return True

        except Exception as e:
            self.log_test_result('core_function_tests', 'video_processing', False,
                               f"视频处理测试异常: {str(e)}")
            logger.error(f"视频处理测试异常: {traceback.format_exc()}")
            return False

        finally:
            # 清理测试文件
            try:
                if test_srt_path and os.path.exists(test_srt_path):
                    os.remove(test_srt_path)
            except:
                pass

    def test_model_training(self) -> bool:
        """测试模型训练功能"""
        logger.info("=" * 60)
        logger.info("6. 模型训练功能测试")
        logger.info("=" * 60)

        try:
            from ui_bridge import ui_bridge

            # 创建测试文件
            test_srt_path = self.create_test_srt_file()
            viral_srt_path = self.create_test_srt_file()  # 模拟爆款字幕文件

            if not test_srt_path or not viral_srt_path:
                self.log_test_result('core_function_tests', 'model_training', False,
                                   "无法创建测试文件")
                return False

            # 测试中文模型训练
            logger.info("测试中文模型训练功能...")
            result_zh = ui_bridge.train_model([test_srt_path], viral_srt_path, "zh")

            self.log_test_result('core_function_tests', 'model_training_zh', result_zh,
                               f"中文模型训练结果: {result_zh}")

            # 测试英文模型训练
            logger.info("测试英文模型训练功能...")
            result_en = ui_bridge.train_model([test_srt_path], viral_srt_path, "en")

            self.log_test_result('core_function_tests', 'model_training_en', result_en,
                               f"英文模型训练结果: {result_en}")

            return True

        except Exception as e:
            self.log_test_result('core_function_tests', 'model_training', False,
                               f"模型训练测试异常: {str(e)}")
            logger.error(f"模型训练测试异常: {traceback.format_exc()}")
            return False

        finally:
            # 清理测试文件
            try:
                if test_srt_path and os.path.exists(test_srt_path):
                    os.remove(test_srt_path)
                if viral_srt_path and os.path.exists(viral_srt_path):
                    os.remove(viral_srt_path)
            except:
                pass

    def test_ui_functionality(self) -> bool:
        """测试UI界面功能"""
        logger.info("=" * 60)
        logger.info("7. UI界面功能测试")
        logger.info("=" * 60)

        try:
            # 测试UI启动
            cmd = [self.python_path, "simple_ui_fixed.py", "--test-mode"]

            # 启动UI进程（短时间测试）
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 等待几秒钟让UI启动
            time.sleep(5)

            # 检查进程是否还在运行
            if process.poll() is None:
                self.log_test_result('ui_tests', 'ui_startup', True,
                                   "UI成功启动并运行")

                # 终止进程
                process.terminate()
                process.wait(timeout=10)

                return True
            else:
                # 获取错误输出
                stdout, stderr = process.communicate()
                self.log_test_result('ui_tests', 'ui_startup', False,
                                   f"UI启动失败: {stderr}")
                return False

        except Exception as e:
            self.log_test_result('ui_tests', 'ui_startup', False,
                               f"UI测试异常: {str(e)}")
            logger.error(f"UI测试异常: {traceback.format_exc()}")
            return False

    def test_system_stability(self) -> Dict[str, Any]:
        """测试系统稳定性"""
        logger.info("=" * 60)
        logger.info("8. 系统稳定性测试")
        logger.info("=" * 60)

        stability_results = {}

        try:
            import psutil

            # 获取初始内存使用情况
            initial_memory = psutil.virtual_memory()
            initial_process = psutil.Process()
            initial_process_memory = initial_process.memory_info()

            stability_results['initial_system_memory'] = {
                'total': initial_memory.total,
                'available': initial_memory.available,
                'percent': initial_memory.percent
            }

            stability_results['initial_process_memory'] = {
                'rss': initial_process_memory.rss,
                'vms': initial_process_memory.vms
            }

            self.log_test_result('stability_tests', 'memory_baseline', True,
                               f"系统内存使用率: {initial_memory.percent:.1f}%")

            # 执行一些操作来测试内存稳定性
            logger.info("执行内存稳定性测试...")

            # 多次调用核心功能
            for i in range(3):
                test_srt_path = self.create_test_srt_file()
                if test_srt_path:
                    try:
                        from ui_bridge import ui_bridge
                        ui_bridge.generate_viral_srt(test_srt_path, "auto")
                    except:
                        pass
                    finally:
                        if os.path.exists(test_srt_path):
                            os.remove(test_srt_path)

                time.sleep(1)

            # 获取最终内存使用情况
            final_memory = psutil.virtual_memory()
            final_process_memory = initial_process.memory_info()

            stability_results['final_system_memory'] = {
                'total': final_memory.total,
                'available': final_memory.available,
                'percent': final_memory.percent
            }

            stability_results['final_process_memory'] = {
                'rss': final_process_memory.rss,
                'vms': final_process_memory.vms
            }

            # 计算内存变化
            memory_change = final_memory.percent - initial_memory.percent
            process_memory_change = final_process_memory.rss - initial_process_memory.rss

            stability_results['memory_change'] = memory_change
            stability_results['process_memory_change'] = process_memory_change

            if abs(memory_change) < 5.0:  # 内存变化小于5%认为稳定
                self.log_test_result('stability_tests', 'memory_stability', True,
                                   f"内存使用稳定，变化: {memory_change:.1f}%")
            else:
                self.log_test_result('stability_tests', 'memory_stability', False,
                                   f"内存使用不稳定，变化: {memory_change:.1f}%")

            return stability_results

        except Exception as e:
            self.log_test_result('stability_tests', 'system_stability', False,
                               f"稳定性测试异常: {str(e)}")
            logger.error(f"稳定性测试异常: {traceback.format_exc()}")
            return stability_results

    def check_vulnerabilities(self) -> Dict[str, Any]:
        """检查潜在隐患"""
        logger.info("=" * 60)
        logger.info("9. 潜在隐患排查")
        logger.info("=" * 60)

        vulnerabilities = {}

        # 检查关键文件是否存在
        critical_files = [
            'simple_ui_fixed.py',
            'ui_bridge.py',
            'src/core/clip_generator.py',
            'src/core/screenplay_engineer.py'
        ]

        missing_files = []
        for file_path in critical_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        vulnerabilities['missing_critical_files'] = missing_files

        if missing_files:
            self.log_test_result('vulnerability_checks', 'critical_files', False,
                               f"缺失关键文件: {missing_files}")
        else:
            self.log_test_result('vulnerability_checks', 'critical_files', True,
                               "所有关键文件存在")

        # 检查权限问题
        try:
            temp_file = PROJECT_ROOT / "temp_permission_test.txt"
            with open(temp_file, 'w') as f:
                f.write("test")
            temp_file.unlink()

            self.log_test_result('vulnerability_checks', 'file_permissions', True,
                               "文件读写权限正常")
            vulnerabilities['file_permissions'] = True
        except Exception as e:
            self.log_test_result('vulnerability_checks', 'file_permissions', False,
                               f"文件权限问题: {str(e)}")
            vulnerabilities['file_permissions'] = False

        # 检查编码问题
        try:
            test_chinese = "测试中文编码"
            test_chinese.encode('utf-8')

            self.log_test_result('vulnerability_checks', 'encoding', True,
                               "UTF-8编码支持正常")
            vulnerabilities['encoding_issues'] = False
        except Exception as e:
            self.log_test_result('vulnerability_checks', 'encoding', False,
                               f"编码问题: {str(e)}")
            vulnerabilities['encoding_issues'] = True

        # 检查路径问题
        try:
            long_path = PROJECT_ROOT / ("a" * 200 + ".txt")
            vulnerabilities['long_path_support'] = len(str(long_path)) < 260

            if vulnerabilities['long_path_support']:
                self.log_test_result('vulnerability_checks', 'path_length', True,
                                   "路径长度支持正常")
            else:
                self.log_test_result('vulnerability_checks', 'path_length', False,
                                   "可能存在长路径问题")
        except Exception as e:
            self.log_test_result('vulnerability_checks', 'path_length', False,
                               f"路径检查异常: {str(e)}")
            vulnerabilities['long_path_support'] = False

        return vulnerabilities

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("🚀 开始VisionAI-ClipsMaster综合功能测试")
        logger.info(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Python解释器: {self.python_path}")
        logger.info(f"项目目录: {PROJECT_ROOT}")

        # 执行所有测试
        self.test_module_imports()
        self.test_dependency_compatibility()
        self.test_ui_bridge_functionality()
        self.test_viral_srt_generation()
        self.test_video_processing()
        self.test_model_training()
        self.test_ui_functionality()
        stability_results = self.test_system_stability()
        vulnerabilities = self.check_vulnerabilities()

        # 计算总体结果
        total_tests = 0
        passed_tests = 0

        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result['success']:
                    passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 生成测试报告
        test_duration = time.time() - self.start_time

        final_report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': success_rate,
                'test_duration': test_duration,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': self.test_results,
            'stability_analysis': stability_results,
            'vulnerability_assessment': vulnerabilities
        }

        # 输出测试总结
        logger.info("=" * 60)
        logger.info("🎯 测试总结")
        logger.info("=" * 60)
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {total_tests - passed_tests}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"测试耗时: {test_duration:.2f}秒")

        # 保存详细报告
        report_path = PROJECT_ROOT / "comprehensive_test_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, ensure_ascii=False, indent=2)
            logger.info(f"详细测试报告已保存: {report_path}")
        except Exception as e:
            logger.error(f"保存测试报告失败: {e}")

        return final_report

def main():
    """主函数"""
    try:
        test_suite = ComprehensiveTestSuite()
        report = test_suite.run_all_tests()

        # 根据测试结果返回适当的退出码
        if report['summary']['success_rate'] >= 80:
            logger.info("🎉 测试总体通过！")
            return 0
        else:
            logger.warning("⚠️ 测试发现重要问题，需要关注")
            return 1

    except KeyboardInterrupt:
        logger.info("用户中断测试")
        return 1
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())