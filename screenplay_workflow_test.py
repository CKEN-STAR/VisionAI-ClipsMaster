#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剧本重构工作流测试
端到端测试从原片字幕到爆款字幕生成的完整流程
"""

import sys
import os
import json
import time
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class ScreenplayWorkflowTester:
    def __init__(self):
        self.results = {
            "test_time": datetime.now().isoformat(),
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "test_results": {},
            "performance_metrics": {},
            "errors": []
        }
        
        # 创建临时目录用于测试
        self.temp_dir = Path(tempfile.mkdtemp(prefix="screenplay_test_"))
        
        # 测试用的SRT字幕样本
        self.sample_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是一个关于爱情的故事

2
00:00:03,500 --> 00:00:06,000
男主角是一个普通的上班族

3
00:00:06,500 --> 00:00:09,000
女主角是一个美丽的咖啡店老板

4
00:00:09,500 --> 00:00:12,000
他们在一个雨天相遇了

5
00:00:12,500 --> 00:00:15,000
从此开始了一段美好的恋情

6
00:00:15,500 --> 00:00:18,000
但是命运总是充满挑战

7
00:00:18,500 --> 00:00:21,000
他们经历了许多困难

8
00:00:21,500 --> 00:00:24,000
最终他们克服了所有障碍

9
00:00:24,500 --> 00:00:27,000
走向了幸福的结局"""

    def create_test_srt_file(self) -> Path:
        """创建测试用的SRT文件"""
        srt_file = self.temp_dir / "test_original.srt"
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(self.sample_srt_content)
        return srt_file

    def test_srt_parser(self):
        """测试SRT解析器功能"""
        print("测试SRT解析器功能...")
        
        try:
            from src.core.srt_parser import SRTParser
            
            # 创建测试文件
            srt_file = self.create_test_srt_file()
            
            parser = SRTParser()
            
            test_result = {
                "status": "success",
                "parsed_segments": 0,
                "total_duration": 0.0,
                "parsing_time": 0.0
            }
            
            # 测试解析
            start_time = time.time()
            segments = parser.parse_srt_file(str(srt_file))
            parsing_time = time.time() - start_time
            
            test_result["parsed_segments"] = len(segments)
            test_result["parsing_time"] = parsing_time
            
            if segments:
                # 计算总时长
                last_segment = segments[-1]
                test_result["total_duration"] = last_segment.get("end_time", 0.0)
                
                print(f"  解析了 {len(segments)} 个字幕段")
                print(f"  总时长: {test_result['total_duration']:.2f}秒")
                print(f"  解析耗时: {parsing_time:.3f}秒")
            
            print("  ✓ SRT解析器功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ SRT解析器功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_narrative_analyzer(self):
        """测试叙事分析器功能"""
        print("测试叙事分析器功能...")
        
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            analyzer = NarrativeAnalyzer()
            
            test_result = {
                "status": "success",
                "analysis_results": {},
                "analysis_time": 0.0
            }
            
            # 测试文本分析
            test_texts = [
                "这是一个关于爱情的故事，男主角深深地爱着女主角。",
                "他们在咖啡厅相遇，开始了一段美好的恋情。",
                "但是命运总是充满挑战，他们经历了许多困难。"
            ]
            
            start_time = time.time()
            for i, text in enumerate(test_texts):
                analysis = analyzer.analyze_narrative_structure(text)
                test_result["analysis_results"][f"text_{i+1}"] = analysis
                print(f"  文本{i+1}分析: {analysis.get('narrative_type', 'unknown')}")
            
            analysis_time = time.time() - start_time
            test_result["analysis_time"] = analysis_time
            
            print(f"  分析耗时: {analysis_time:.3f}秒")
            print("  ✓ 叙事分析器功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 叙事分析器功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_screenplay_engineer(self):
        """测试剧本工程师功能"""
        print("测试剧本工程师功能...")
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            
            engineer = ScreenplayEngineer()
            
            test_result = {
                "status": "success",
                "reconstruction_results": {},
                "generation_time": 0.0
            }
            
            # 创建测试字幕数据
            srt_file = self.create_test_srt_file()
            
            start_time = time.time()
            
            # 测试剧本重构
            reconstructed_script = engineer.reconstruct_screenplay(str(srt_file))
            
            generation_time = time.time() - start_time
            test_result["generation_time"] = generation_time
            test_result["reconstruction_results"] = reconstructed_script
            
            if reconstructed_script:
                print(f"  重构了 {len(reconstructed_script.get('segments', []))} 个片段")
                print(f"  生成耗时: {generation_time:.3f}秒")
                
                # 检查重构结果的质量
                segments = reconstructed_script.get('segments', [])
                if segments:
                    print(f"  第一个片段: {segments[0].get('text', '')[:50]}...")
            
            print("  ✓ 剧本工程师功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 剧本工程师功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_rhythm_analyzer(self):
        """测试节奏分析器功能"""
        print("测试节奏分析器功能...")
        
        try:
            from src.core.rhythm_analyzer import RhythmAnalyzer
            
            analyzer = RhythmAnalyzer()
            
            test_result = {
                "status": "success",
                "rhythm_analysis": {},
                "analysis_time": 0.0
            }
            
            # 创建测试字幕数据
            srt_file = self.create_test_srt_file()
            
            start_time = time.time()
            
            # 测试节奏分析
            rhythm_analysis = analyzer.analyze_rhythm(str(srt_file))
            
            analysis_time = time.time() - start_time
            test_result["analysis_time"] = analysis_time
            test_result["rhythm_analysis"] = rhythm_analysis
            
            if rhythm_analysis:
                print(f"  分析了节奏模式: {rhythm_analysis.get('pattern_type', 'unknown')}")
                print(f"  平均节奏: {rhythm_analysis.get('average_pace', 0):.2f}")
                print(f"  分析耗时: {analysis_time:.3f}秒")
            
            print("  ✓ 节奏分析器功能测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 节奏分析器功能测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        print("测试端到端工作流...")
        
        try:
            # 导入所有需要的模块
            from src.core.srt_parser import SRTParser
            from src.core.narrative_analyzer import NarrativeAnalyzer
            from src.core.screenplay_engineer import ScreenplayEngineer
            from src.core.rhythm_analyzer import RhythmAnalyzer
            
            test_result = {
                "status": "success",
                "workflow_steps": {},
                "total_time": 0.0
            }
            
            # 创建测试文件
            srt_file = self.create_test_srt_file()
            
            start_time = time.time()
            
            # 步骤1: 解析原始字幕
            print("  步骤1: 解析原始字幕...")
            parser = SRTParser()
            segments = parser.parse_srt_file(str(srt_file))
            test_result["workflow_steps"]["parse"] = {"segments": len(segments)}
            
            # 步骤2: 分析叙事结构
            print("  步骤2: 分析叙事结构...")
            analyzer = NarrativeAnalyzer()
            narrative_analysis = analyzer.analyze_segments(segments)
            test_result["workflow_steps"]["analyze"] = narrative_analysis
            
            # 步骤3: 重构剧本
            print("  步骤3: 重构剧本...")
            engineer = ScreenplayEngineer()
            reconstructed = engineer.reconstruct_from_segments(segments)
            test_result["workflow_steps"]["reconstruct"] = reconstructed
            
            # 步骤4: 分析节奏
            print("  步骤4: 分析节奏...")
            rhythm_analyzer = RhythmAnalyzer()
            rhythm = rhythm_analyzer.analyze_segments(segments)
            test_result["workflow_steps"]["rhythm"] = rhythm
            
            total_time = time.time() - start_time
            test_result["total_time"] = total_time
            
            print(f"  端到端工作流完成，总耗时: {total_time:.3f}秒")
            print("  ✓ 端到端工作流测试通过")
            return test_result
            
        except Exception as e:
            print(f"  ✗ 端到端工作流测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def run_comprehensive_test(self):
        """运行全面的剧本重构工作流测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 剧本重构工作流测试")
        print("=" * 60)
        
        tests = [
            ("SRT解析器功能", self.test_srt_parser),
            ("叙事分析器功能", self.test_narrative_analyzer),
            ("剧本工程师功能", self.test_screenplay_engineer),
            ("节奏分析器功能", self.test_rhythm_analyzer),
            ("端到端工作流", self.test_end_to_end_workflow)
        ]
        
        self.results["total_tests"] = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n测试: {test_name}")
            try:
                result = test_func()
                self.results["test_results"][test_name] = result
                
                if result.get("status") == "success":
                    self.results["successful_tests"] += 1
                    print(f"  ✓ {test_name} 测试通过")
                else:
                    self.results["failed_tests"] += 1
                    print(f"  ✗ {test_name} 测试失败")
                    
            except Exception as e:
                self.results["failed_tests"] += 1
                error_msg = f"测试异常: {e}"
                self.results["test_results"][test_name] = {
                    "status": "error",
                    "error": error_msg
                }
                self.results["errors"].append(f"{test_name}: {error_msg}")
                print(f"  ✗ {error_msg}")
        
        # 清理临时文件
        self.cleanup()
        
        # 生成报告
        self.generate_report()
        
        return self.results

    def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"\n临时目录已清理: {self.temp_dir}")
        except Exception as e:
            print(f"\n清理临时文件失败: {e}")

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("剧本重构工作流测试结果汇总")
        print("=" * 60)
        
        print(f"总测试数: {self.results['total_tests']}")
        print(f"通过测试: {self.results['successful_tests']}")
        print(f"失败测试: {self.results['failed_tests']}")
        print(f"成功率: {(self.results['successful_tests']/self.results['total_tests']*100):.1f}%")
        
        if self.results["failed_tests"] > 0:
            print(f"\n失败的测试:")
            for test_name, result in self.results["test_results"].items():
                if result.get("status") != "success":
                    print(f"  - {test_name}: {result.get('error', 'Unknown error')}")
        
        # 保存详细报告
        report_file = f"screenplay_workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = ScreenplayWorkflowTester()
    results = tester.run_comprehensive_test()
    
    # 返回退出码
    if results["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
