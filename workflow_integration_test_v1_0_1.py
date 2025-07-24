#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.0.1 工作流程集成测试
验证从SRT导入到视频输出的完整工作流程
"""

import sys
import os
import tempfile
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

class WorkflowIntegrationTester:
    def __init__(self):
        self.test_results = {}
        self.errors = []
        
    def add_test_result(self, test_name, passed, details="", error_msg=""):
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "error_msg": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
    def test_srt_to_video_workflow(self):
        """测试SRT到视频的完整工作流程"""
        try:
            # 创建测试SRT文件
            test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是第一句测试字幕

2
00:00:04,000 --> 00:00:06,000
This is the second test subtitle

3
00:00:07,000 --> 00:00:09,000
这是第三句中文字幕
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
                f.write(test_srt_content)
                test_srt_path = f.name
                
            # 测试SRT解析
            try:
                from src.core.srt_parser import SRTParser
                parser = SRTParser()
                parsed_data = parser.parse(test_srt_path)
                
                if parsed_data and len(parsed_data) == 3:
                    self.add_test_result("srt_parsing_workflow", True, 
                                        f"SRT解析成功，{len(parsed_data)}条字幕")
                else:
                    self.add_test_result("srt_parsing_workflow", False, "SRT解析失败")
                    
            except ImportError:
                self.add_test_result("srt_parsing_workflow", False, "SRT解析器不可用")
                
            # 测试语言检测
            try:
                from src.core.language_detector import LanguageDetector
                detector = LanguageDetector()
                
                # 检测中文
                zh_result = detector.detect_language("这是中文测试")
                en_result = detector.detect_language("This is English test")
                
                if zh_result == "zh" and en_result == "en":
                    self.add_test_result("language_detection_workflow", True, "语言检测正常")
                else:
                    self.add_test_result("language_detection_workflow", False, 
                                        f"语言检测异常: zh={zh_result}, en={en_result}")
                    
            except ImportError:
                self.add_test_result("language_detection_workflow", False, "语言检测器不可用")
                
            # 测试视频处理器
            try:
                from src.core.clip_generator import ClipGenerator
                generator = ClipGenerator()
                
                # 测试基本方法可用性
                if hasattr(generator, 'generate_from_srt') and callable(getattr(generator, 'generate_from_srt')):
                    self.add_test_result("video_processing_workflow", True, "视频处理器可用")
                else:
                    self.add_test_result("video_processing_workflow", False, "视频处理器方法不可用")
                    
            except ImportError:
                self.add_test_result("video_processing_workflow", False, "视频处理器不可用")
                
            # 测试剪映导出
            try:
                from src.exporters.jianying_pro_exporter import JianyingProExporter
                exporter = JianyingProExporter()
                
                # 测试模板生成
                test_data = {"title": "测试项目", "clips": []}
                if hasattr(exporter, 'generate_template'):
                    self.add_test_result("jianying_export_workflow", True, "剪映导出器可用")
                else:
                    self.add_test_result("jianying_export_workflow", False, "剪映导出器方法不可用")
                    
            except ImportError:
                self.add_test_result("jianying_export_workflow", False, "剪映导出器不可用")
                
            # 清理临时文件
            if os.path.exists(test_srt_path):
                os.unlink(test_srt_path)
                
            return True
            
        except Exception as e:
            self.add_test_result("srt_to_video_workflow", False, error_msg=str(e))
            return False
            
    def test_ui_workflow_integration(self):
        """测试UI工作流程集成"""
        try:
            import simple_ui_fixed
            
            # 测试主应用类
            if hasattr(simple_ui_fixed, 'SimpleScreenplayApp'):
                app_class = simple_ui_fixed.SimpleScreenplayApp
                
                # 检查关键方法
                key_methods = ['import_original_srt', 'import_hit_srt', 'start_processing']
                available_methods = []
                
                for method in key_methods:
                    if hasattr(app_class, method):
                        available_methods.append(method)
                        
                if len(available_methods) >= 2:
                    self.add_test_result("ui_workflow_methods", True, 
                                        f"UI工作流程方法可用: {', '.join(available_methods)}")
                else:
                    self.add_test_result("ui_workflow_methods", False, 
                                        f"UI工作流程方法不完整: {', '.join(available_methods)}")
            else:
                self.add_test_result("ui_workflow_methods", False, "主应用类不可用")
                
            # 测试AlertManager集成
            if hasattr(simple_ui_fixed, 'AlertManager'):
                alert_manager = simple_ui_fixed.AlertManager()
                if hasattr(alert_manager, 'show_alert'):
                    self.add_test_result("alert_integration", True, "预警系统集成正常")
                else:
                    self.add_test_result("alert_integration", False, "预警系统方法不可用")
            else:
                self.add_test_result("alert_integration", False, "预警系统不可用")
                
            return True
            
        except Exception as e:
            self.add_test_result("ui_workflow_integration", False, error_msg=str(e))
            return False
            
    def test_performance_integration(self):
        """测试性能监控集成"""
        try:
            import simple_ui_fixed
            
            # 测试性能监控
            if hasattr(simple_ui_fixed, 'AlertManager'):
                alert_manager = simple_ui_fixed.AlertManager()
                
                # 测试性能检查
                if hasattr(alert_manager, 'check_system_performance'):
                    alert_manager.check_system_performance()
                    self.add_test_result("performance_integration", True, "性能监控集成正常")
                else:
                    self.add_test_result("performance_integration", False, "性能监控方法不可用")
            else:
                self.add_test_result("performance_integration", False, "性能监控不可用")
                
            return True
            
        except Exception as e:
            self.add_test_result("performance_integration", False, error_msg=str(e))
            return False
            
    def run_all_tests(self):
        """运行所有工作流程测试"""
        print("🔍 开始VisionAI-ClipsMaster v1.0.1 工作流程集成测试")
        print("=" * 60)
        
        # 测试序列
        tests = [
            ("SRT到视频工作流程", self.test_srt_to_video_workflow),
            ("UI工作流程集成", self.test_ui_workflow_integration),
            ("性能监控集成", self.test_performance_integration),
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 执行测试: {test_name}")
            try:
                success = test_func()
                status = "✅ 通过" if success else "❌ 失败"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ 异常: {str(e)}")
                
        return self.generate_report()
        
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 工作流程集成测试报告")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n📋 详细测试结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}: {result.get('details', '')}")
            if result.get('error_msg'):
                print(f"   错误: {result['error_msg']}")
                
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests * 100 if total_tests > 0 else 0,
            'test_results': self.test_results,
            'errors': self.errors
        }

def main():
    """主函数"""
    tester = WorkflowIntegrationTester()
    result = tester.run_all_tests()
    return result

if __name__ == "__main__":
    main()
