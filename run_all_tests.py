#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 一键测试启动器
运行所有测试套件并生成综合报告
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🎬 VisionAI-ClipsMaster 全面测试启动器")
        print("=" * 80)
        print("将依次运行：环境检查、核心模块测试、性能测试、系统集成测试")
        print()
        
        self.start_time = datetime.now()
        
        # 1. 生成测试数据
        self._run_test_data_generation()
        
        # 2. 运行核心模块测试
        self._run_core_module_tests()
        
        # 3. 运行性能和稳定性测试
        self._run_performance_tests()
        
        # 4. 运行系统集成测试
        self._run_system_integration_tests()
        
        self.end_time = datetime.now()
        
        # 5. 生成综合报告
        self._generate_comprehensive_report()
        
        # 6. 显示最终结果
        self._display_final_results()
    
    def _run_test_data_generation(self):
        """运行测试数据生成"""
        print("📝 1. 生成测试数据")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                [sys.executable, "generate_test_data.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ 测试数据生成成功")
                self.test_results['test_data_generation'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'duration': 'N/A'
                }
            else:
                print("❌ 测试数据生成失败")
                print(f"错误信息: {result.stderr}")
                self.test_results['test_data_generation'] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': 'N/A'
                }
        
        except subprocess.TimeoutExpired:
            print("⏰ 测试数据生成超时")
            self.test_results['test_data_generation'] = {
                'status': 'timeout',
                'error': '生成超时',
                'duration': '60s+'
            }
        except Exception as e:
            print(f"❌ 测试数据生成异常: {e}")
            self.test_results['test_data_generation'] = {
                'status': 'error',
                'error': str(e),
                'duration': 'N/A'
            }
    
    def _run_core_module_tests(self):
        """运行核心模块测试"""
        print("\n🔧 2. 核心模块测试")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "test_core_modules.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ 核心模块测试通过")
                # 解析测试结果
                output_lines = result.stdout.split('\n')
                test_summary = self._parse_unittest_output(output_lines)
                
                self.test_results['core_module_tests'] = {
                    'status': 'success',
                    'summary': test_summary,
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
            else:
                print("❌ 核心模块测试失败")
                print(f"错误信息: {result.stderr}")
                self.test_results['core_module_tests'] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
        
        except subprocess.TimeoutExpired:
            print("⏰ 核心模块测试超时")
            self.test_results['core_module_tests'] = {
                'status': 'timeout',
                'error': '测试超时',
                'duration': '300s+'
            }
        except Exception as e:
            print(f"❌ 核心模块测试异常: {e}")
            self.test_results['core_module_tests'] = {
                'status': 'error',
                'error': str(e),
                'duration': f"{time.time() - start_time:.2f}s"
            }
    
    def _run_performance_tests(self):
        """运行性能和稳定性测试"""
        print("\n⚡ 3. 性能和稳定性测试")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "test_performance_stability.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ 性能测试通过")
                self.test_results['performance_tests'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
            else:
                print("❌ 性能测试失败")
                print(f"错误信息: {result.stderr}")
                self.test_results['performance_tests'] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
        
        except subprocess.TimeoutExpired:
            print("⏰ 性能测试超时")
            self.test_results['performance_tests'] = {
                'status': 'timeout',
                'error': '测试超时',
                'duration': '600s+'
            }
        except Exception as e:
            print(f"❌ 性能测试异常: {e}")
            self.test_results['performance_tests'] = {
                'status': 'error',
                'error': str(e),
                'duration': f"{time.time() - start_time:.2f}s"
            }
    
    def _run_system_integration_tests(self):
        """运行系统集成测试"""
        print("\n🔗 4. 系统集成测试")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "comprehensive_system_test_suite.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=900  # 15分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print("✅ 系统集成测试通过")
                self.test_results['system_integration_tests'] = {
                    'status': 'success',
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
            else:
                print("❌ 系统集成测试失败")
                print(f"错误信息: {result.stderr}")
                self.test_results['system_integration_tests'] = {
                    'status': 'failed',
                    'error': result.stderr,
                    'output': result.stdout,
                    'duration': f"{duration:.2f}s"
                }
        
        except subprocess.TimeoutExpired:
            print("⏰ 系统集成测试超时")
            self.test_results['system_integration_tests'] = {
                'status': 'timeout',
                'error': '测试超时',
                'duration': '900s+'
            }
        except Exception as e:
            print(f"❌ 系统集成测试异常: {e}")
            self.test_results['system_integration_tests'] = {
                'status': 'error',
                'error': str(e),
                'duration': f"{time.time() - start_time:.2f}s"
            }
    
    def _parse_unittest_output(self, output_lines: List[str]) -> Dict[str, Any]:
        """解析unittest输出"""
        summary = {
            'tests_run': 0,
            'failures': 0,
            'errors': 0,
            'success_rate': 0.0
        }
        
        for line in output_lines:
            if '运行测试:' in line:
                try:
                    summary['tests_run'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '失败:' in line:
                try:
                    summary['failures'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '错误:' in line:
                try:
                    summary['errors'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '成功率:' in line:
                try:
                    rate_str = line.split(':')[1].strip().replace('%', '')
                    summary['success_rate'] = float(rate_str)
                except:
                    pass
        
        return summary
    
    def _generate_comprehensive_report(self):
        """生成综合报告"""
        print("\n📊 生成综合测试报告...")
        
        # 计算总体统计
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        successful_tests = sum(1 for result in self.test_results.values() 
                             if result.get('status') == 'success')
        total_tests = len(self.test_results)
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 生成报告数据
        report_data = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'total_test_suites': total_tests,
                'successful_suites': successful_tests,
                'overall_success_rate': overall_success_rate
            },
            'test_results': self.test_results,
            'system_info': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform,
                'working_directory': str(self.project_root)
            }
        }
        
        # 保存JSON报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_report_file = self.project_root / f"comprehensive_test_report_{timestamp}.json"
        
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 综合测试报告已保存: {json_report_file}")
        
        # 生成简化的文本报告
        text_report_file = self.project_root / f"test_summary_{timestamp}.txt"
        self._generate_text_report(text_report_file, report_data)
        
        print(f"📄 测试摘要已保存: {text_report_file}")
    
    def _generate_text_report(self, filepath: Path, report_data: Dict[str, Any]):
        """生成文本格式报告"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("VisionAI-ClipsMaster 综合测试报告\n")
            f.write("=" * 50 + "\n\n")
            
            # 测试摘要
            summary = report_data['test_summary']
            f.write(f"测试开始时间: {summary['start_time']}\n")
            f.write(f"测试结束时间: {summary['end_time']}\n")
            f.write(f"总耗时: {summary['total_duration_seconds']:.2f}秒\n")
            f.write(f"测试套件总数: {summary['total_test_suites']}\n")
            f.write(f"成功套件数: {summary['successful_suites']}\n")
            f.write(f"总体成功率: {summary['overall_success_rate']:.1f}%\n\n")
            
            # 各测试套件结果
            f.write("各测试套件详情:\n")
            f.write("-" * 30 + "\n")
            
            for test_name, result in report_data['test_results'].items():
                status_icon = {
                    'success': '✅',
                    'failed': '❌',
                    'timeout': '⏰',
                    'error': '💥'
                }.get(result.get('status', 'unknown'), '❓')
                
                f.write(f"{status_icon} {test_name}: {result.get('status', 'unknown')}\n")
                f.write(f"   耗时: {result.get('duration', 'N/A')}\n")
                
                if result.get('error'):
                    f.write(f"   错误: {result['error'][:100]}...\n")
                
                f.write("\n")
    
    def _display_final_results(self):
        """显示最终结果"""
        print("\n" + "=" * 80)
        print("🎯 VisionAI-ClipsMaster 综合测试完成")
        print("=" * 80)
        
        # 统计结果
        successful_tests = sum(1 for result in self.test_results.values() 
                             if result.get('status') == 'success')
        total_tests = len(self.test_results)
        
        print(f"\n📊 测试结果统计:")
        print(f"  总测试套件: {total_tests}")
        print(f"  成功套件: {successful_tests}")
        print(f"  失败套件: {total_tests - successful_tests}")
        print(f"  总体成功率: {(successful_tests / total_tests * 100):.1f}%")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"  总耗时: {duration:.2f}秒")
        
        # 显示各套件状态
        print(f"\n📋 各测试套件状态:")
        for test_name, result in self.test_results.items():
            status_icon = {
                'success': '✅',
                'failed': '❌',
                'timeout': '⏰',
                'error': '💥'
            }.get(result.get('status', 'unknown'), '❓')
            
            print(f"  {status_icon} {test_name}: {result.get('status', 'unknown')}")
        
        # 最终评估
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 90:
            print(f"\n🎉 测试结果优秀！系统状态良好，可以投入使用。")
        elif success_rate >= 70:
            print(f"\n⚠️  测试结果良好，但存在一些问题需要关注。")
        else:
            print(f"\n❌ 测试结果不理想，系统存在严重问题，需要立即修复。")
        
        print(f"\n📁 详细报告已保存到项目根目录")

def main():
    """主函数"""
    runner = TestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()
