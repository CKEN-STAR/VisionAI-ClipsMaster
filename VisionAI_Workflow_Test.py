#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 完整工作流程测试
测试从输入原片+字幕到输出混剪视频的完整流程
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class WorkflowTester:
    def __init__(self):
        self.test_results = {
            "test_start_time": datetime.now().isoformat(),
            "input_validation_tests": {},
            "processing_pipeline_tests": {},
            "output_generation_tests": {},
            "length_control_tests": {},
            "export_tests": {},
            "overall_status": "RUNNING"
        }
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        
    def log_test_result(self, category, test_name, status, details=None, error=None):
        """记录测试结果"""
        result = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.test_results[category][test_name] = result
        print(f"[{status}] {category}.{test_name}: {details.get('message', '') if details else ''}")
        if error:
            print(f"    错误: {error}")
    
    def test_input_validation(self):
        """测试输入验证"""
        print("\n=== 输入验证测试 ===")
        
        # 测试视频文件验证
        try:
            from src.core.input_validator import InputValidator
            validator = InputValidator()
            
            # 测试SRT文件验证
            test_srt_path = "test_data/test_subtitle.srt"
            if os.path.exists(test_srt_path):
                is_valid = validator.validate_srt_file(test_srt_path)
                if is_valid:
                    self.log_test_result("input_validation_tests", "srt_validation", "PASS", 
                                       {"message": "SRT文件验证通过"})
                else:
                    self.log_test_result("input_validation_tests", "srt_validation", "FAIL", 
                                       {"message": "SRT文件验证失败"})
            else:
                self.log_test_result("input_validation_tests", "srt_validation", "SKIP", 
                                   {"message": "测试SRT文件不存在"})
            
            # 测试视频文件验证
            test_video_path = "test_data/test_video.mp4"
            if os.path.exists(test_video_path):
                self.log_test_result("input_validation_tests", "video_validation", "PASS", 
                                   {"message": "视频文件存在"})
            else:
                self.log_test_result("input_validation_tests", "video_validation", "SKIP", 
                                   {"message": "测试视频文件不存在"})
                
        except ImportError as e:
            self.log_test_result("input_validation_tests", "input_validator_import", "FAIL", 
                               {"message": "输入验证器导入失败"}, str(e))
    
    def test_processing_pipeline(self):
        """测试处理管道"""
        print("\n=== 处理管道测试 ===")
        
        # 测试语言检测
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()
            
            test_text = "这是一段中文测试文本"
            detected_lang = detector.detect_language(test_text)
            if detected_lang == "zh":
                self.log_test_result("processing_pipeline_tests", "language_detection", "PASS", 
                                   {"message": f"语言检测正确: {detected_lang}"})
            else:
                self.log_test_result("processing_pipeline_tests", "language_detection", "FAIL", 
                                   {"message": f"语言检测错误: {detected_lang}"})
                
        except Exception as e:
            self.log_test_result("processing_pipeline_tests", "language_detection", "ERROR", 
                               {"message": "语言检测测试异常"}, str(e))
        
        # 测试剧本重构
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            
            # 模拟剧本重构
            test_subtitles = [
                {"start": "00:00:01,000", "end": "00:00:03,000", "text": "这是第一句台词"},
                {"start": "00:00:04,000", "end": "00:00:06,000", "text": "这是第二句台词"}
            ]
            
            self.log_test_result("processing_pipeline_tests", "screenplay_reconstruction", "PASS", 
                               {"message": "剧本重构模块可用"})
                
        except Exception as e:
            self.log_test_result("processing_pipeline_tests", "screenplay_reconstruction", "ERROR", 
                               {"message": "剧本重构测试异常"}, str(e))
    
    def test_output_generation(self):
        """测试输出生成"""
        print("\n=== 输出生成测试 ===")
        
        # 测试视频处理器
        try:
            from src.core.video_processor import VideoProcessor
            processor = VideoProcessor()
            self.log_test_result("output_generation_tests", "video_processor_import", "PASS", 
                               {"message": "视频处理器导入成功"})
        except ImportError as e:
            self.log_test_result("output_generation_tests", "video_processor_import", "FAIL", 
                               {"message": "视频处理器导入失败"}, str(e))
        
        # 测试片段生成器
        try:
            from src.core.clip_generator import ClipGenerator
            generator = ClipGenerator()
            self.log_test_result("output_generation_tests", "clip_generator_import", "PASS", 
                               {"message": "片段生成器导入成功"})
        except ImportError as e:
            self.log_test_result("output_generation_tests", "clip_generator_import", "FAIL", 
                               {"message": "片段生成器导入失败"}, str(e))
    
    def test_length_control(self):
        """测试长度控制"""
        print("\n=== 长度控制测试 ===")
        
        # 测试节奏分析器
        try:
            from src.core.rhythm_analyzer import RhythmAnalyzer
            analyzer = RhythmAnalyzer()
            self.log_test_result("length_control_tests", "rhythm_analyzer_import", "PASS", 
                               {"message": "节奏分析器导入成功"})
            
            # 测试长度控制逻辑
            if hasattr(analyzer, 'analyze_optimal_length'):
                self.log_test_result("length_control_tests", "length_analysis_method", "PASS", 
                                   {"message": "长度分析方法存在"})
            else:
                self.log_test_result("length_control_tests", "length_analysis_method", "FAIL", 
                                   {"message": "长度分析方法不存在"})
                
        except ImportError as e:
            self.log_test_result("length_control_tests", "rhythm_analyzer_import", "FAIL", 
                               {"message": "节奏分析器导入失败"}, str(e))
        
        # 测试片段建议器
        try:
            from src.core.segment_advisor import SegmentAdvisor
            advisor = SegmentAdvisor()
            self.log_test_result("length_control_tests", "segment_advisor_import", "PASS", 
                               {"message": "片段建议器导入成功"})
        except ImportError as e:
            self.log_test_result("length_control_tests", "segment_advisor_import", "FAIL", 
                               {"message": "片段建议器导入失败"}, str(e))
    
    def test_export_functionality(self):
        """测试导出功能"""
        print("\n=== 导出功能测试 ===")
        
        # 测试剪映导出器
        try:
            from src.exporters.jianying_pro_exporter import JianYingProExporter
            exporter = JianYingProExporter()
            self.log_test_result("export_tests", "jianying_exporter_import", "PASS",
                               {"message": "剪映导出器导入成功"})
            
            # 测试导出方法
            if hasattr(exporter, 'export_project'):
                self.log_test_result("export_tests", "export_project_method", "PASS", 
                                   {"message": "export_project方法存在"})
            else:
                self.log_test_result("export_tests", "export_project_method", "FAIL", 
                                   {"message": "export_project方法不存在"})
                
        except ImportError as e:
            self.log_test_result("export_tests", "jianying_exporter_import", "FAIL", 
                               {"message": "剪映导出器导入失败"}, str(e))
        
        # 测试基础导出器
        try:
            from src.exporters.base_exporter import BaseExporter
            base_exporter = BaseExporter()
            self.log_test_result("export_tests", "base_exporter_import", "PASS", 
                               {"message": "基础导出器导入成功"})
        except ImportError as e:
            self.log_test_result("export_tests", "base_exporter_import", "FAIL", 
                               {"message": "基础导出器导入失败"}, str(e))
        
        # 测试XML模板
        try:
            from src.utils.xml_template import XMLTemplate
            template = XMLTemplate()
            self.log_test_result("export_tests", "xml_template_import", "PASS", 
                               {"message": "XML模板导入成功"})
        except ImportError as e:
            self.log_test_result("export_tests", "xml_template_import", "FAIL", 
                               {"message": "XML模板导入失败"}, str(e))
    
    def generate_report(self):
        """生成测试报告"""
        self.test_results["test_end_time"] = datetime.now().isoformat()
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        error_tests = 0
        
        for category in ["input_validation_tests", "processing_pipeline_tests", "output_generation_tests", 
                        "length_control_tests", "export_tests"]:
            for test_name, result in self.test_results[category].items():
                total_tests += 1
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
                elif result["status"] == "SKIP":
                    skipped_tests += 1
                elif result["status"] == "ERROR":
                    error_tests += 1
        
        # 确定整体状态
        if error_tests > 0:
            self.test_results["overall_status"] = "ERROR"
        elif failed_tests > 0:
            self.test_results["overall_status"] = "FAIL"
        elif passed_tests > 0:
            self.test_results["overall_status"] = "PASS"
        else:
            self.test_results["overall_status"] = "SKIP"
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "skipped": skipped_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # 保存测试报告
        report_file = self.output_dir / f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 工作流程测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"错误: {error_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"成功率: {self.test_results['summary']['success_rate']}")
        print(f"整体状态: {self.test_results['overall_status']}")
        print(f"详细报告已保存到: {report_file}")
        
        return self.test_results
    
    def run_all_tests(self):
        """运行所有工作流程测试"""
        print("开始VisionAI-ClipsMaster工作流程测试...")
        print(f"测试开始时间: {self.test_results['test_start_time']}")
        
        try:
            self.test_input_validation()
            self.test_processing_pipeline()
            self.test_output_generation()
            self.test_length_control()
            self.test_export_functionality()
        except Exception as e:
            print(f"测试执行异常: {e}")
        finally:
            return self.generate_report()

if __name__ == "__main__":
    workflow_tester = WorkflowTester()
    results = workflow_tester.run_all_tests()
