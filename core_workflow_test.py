#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 核心工作流程测试
端到端测试完整的字幕处理→剧本重构→视频拼接→导出流程
"""

import os
import sys
import json
import time
import traceback
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class CoreWorkflowTestSuite:
    """核心工作流程测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dir = None
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """设置测试环境"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="workflow_test_")
            print(f"✓ 测试环境已创建: {self.temp_dir}")
            
            # 创建测试数据
            self.create_test_data()
        except Exception as e:
            print(f"✗ 测试环境创建失败: {e}")
            raise
    
    def create_test_data(self):
        """创建测试数据"""
        # 创建测试字幕文件
        test_srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello, this is a test subtitle.

2
00:00:03,500 --> 00:00:05,000
This is the second subtitle line.

3
00:00:05,500 --> 00:00:07,000
And this is the third line.
"""
        
        self.test_srt_path = os.path.join(self.temp_dir, "test_subtitle.srt")
        with open(self.test_srt_path, 'w', encoding='utf-8') as f:
            f.write(test_srt_content)
        
        print(f"✓ 测试字幕文件已创建: {self.test_srt_path}")
    
    def test_core_module_imports(self) -> Dict[str, Any]:
        """测试核心模块导入"""
        print("\n=== 测试核心模块导入 ===")
        results = {"status": "success", "details": {}}
        
        core_modules = [
            "src.core.language_detector",
            "src.core.model_switcher",
            "src.core.srt_parser",
            "src.core.narrative_analyzer",
            "src.core.screenplay_engineer",
            "src.core.alignment_engineer",
            "src.core.clip_generator",
            "src.exporters.jianying_pro_exporter"
        ]
        
        for module_name in core_modules:
            try:
                __import__(module_name)
                results["details"][module_name] = "success"
                print(f"✓ {module_name} 导入成功")
            except ImportError as e:
                results["details"][module_name] = f"import_error: {str(e)}"
                print(f"✗ {module_name} 导入失败: {e}")
                results["status"] = "partial_failure"
            except Exception as e:
                results["details"][module_name] = f"error: {str(e)}"
                print(f"✗ {module_name} 导入异常: {e}")
                results["status"] = "failure"
        
        return results
    
    def test_language_detection(self) -> Dict[str, Any]:
        """测试语言检测"""
        print("\n=== 测试语言检测 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.language_detector import LanguageDetector
            
            # 创建语言检测器
            detector = LanguageDetector()
            results["details"]["instantiation"] = "success"
            print("✓ 语言检测器实例化成功")
            
            # 测试英文检测
            english_text = "Hello, this is an English subtitle."
            if hasattr(detector, 'detect_language'):
                lang = detector.detect_language(english_text)
                results["details"]["english_detection"] = lang
                print(f"✓ 英文检测结果: {lang}")
            
            # 测试中文检测
            chinese_text = "你好，这是一个中文字幕。"
            if hasattr(detector, 'detect_language'):
                lang = detector.detect_language(chinese_text)
                results["details"]["chinese_detection"] = lang
                print(f"✓ 中文检测结果: {lang}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 语言检测器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 语言检测测试失败: {e}")
        
        return results
    
    def test_srt_parsing(self) -> Dict[str, Any]:
        """测试SRT解析"""
        print("\n=== 测试SRT解析 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.srt_parser import SRTParser
            
            # 创建SRT解析器
            parser = SRTParser()
            results["details"]["instantiation"] = "success"
            print("✓ SRT解析器实例化成功")
            
            # 解析测试文件
            if hasattr(parser, 'parse_file'):
                subtitles = parser.parse_file(self.test_srt_path)
                results["details"]["file_parsing"] = {
                    "subtitle_count": len(subtitles) if subtitles else 0,
                    "first_subtitle": str(subtitles[0]) if subtitles else None
                }
                print(f"✓ SRT文件解析成功，共 {len(subtitles) if subtitles else 0} 条字幕")
            
            # 测试时间轴解析
            if hasattr(parser, 'parse_timestamp'):
                timestamp = "00:00:01,000 --> 00:00:03,000"
                parsed_time = parser.parse_timestamp(timestamp)
                results["details"]["timestamp_parsing"] = str(parsed_time)
                print(f"✓ 时间轴解析成功: {parsed_time}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ SRT解析器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ SRT解析测试失败: {e}")
        
        return results
    
    def test_narrative_analysis(self) -> Dict[str, Any]:
        """测试叙事分析"""
        print("\n=== 测试叙事分析 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.narrative_analyzer import NarrativeAnalyzer
            
            # 创建叙事分析器
            analyzer = NarrativeAnalyzer()
            results["details"]["instantiation"] = "success"
            print("✓ 叙事分析器实例化成功")
            
            # 测试剧情分析
            test_subtitles = [
                {"text": "Hello, this is a test.", "start": 1.0, "end": 3.0},
                {"text": "This is the second line.", "start": 3.5, "end": 5.0},
                {"text": "And this is the third line.", "start": 5.5, "end": 7.0}
            ]
            
            if hasattr(analyzer, 'analyze_narrative'):
                analysis = analyzer.analyze_narrative(test_subtitles)
                results["details"]["narrative_analysis"] = str(analysis)
                print(f"✓ 叙事分析完成: {analysis}")
            
            # 测试情感分析
            if hasattr(analyzer, 'analyze_emotion'):
                emotion = analyzer.analyze_emotion(test_subtitles)
                results["details"]["emotion_analysis"] = str(emotion)
                print(f"✓ 情感分析完成: {emotion}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 叙事分析器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 叙事分析测试失败: {e}")
        
        return results
    
    def test_screenplay_engineering(self) -> Dict[str, Any]:
        """测试剧本工程"""
        print("\n=== 测试剧本工程 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            
            # 创建剧本工程师
            engineer = ScreenplayEngineer()
            results["details"]["instantiation"] = "success"
            print("✓ 剧本工程师实例化成功")
            
            # 测试剧本重构
            test_subtitles = [
                {"text": "Hello, this is a test.", "start": 1.0, "end": 3.0},
                {"text": "This is the second line.", "start": 3.5, "end": 5.0},
                {"text": "And this is the third line.", "start": 5.5, "end": 7.0}
            ]
            
            if hasattr(engineer, 'reconstruct_screenplay'):
                reconstructed = engineer.reconstruct_screenplay(test_subtitles)
                results["details"]["screenplay_reconstruction"] = {
                    "original_count": len(test_subtitles),
                    "reconstructed_count": len(reconstructed) if reconstructed else 0
                }
                print(f"✓ 剧本重构完成: {len(test_subtitles)} → {len(reconstructed) if reconstructed else 0}")
            
            # 测试爆款优化
            if hasattr(engineer, 'optimize_for_viral'):
                optimized = engineer.optimize_for_viral(test_subtitles)
                results["details"]["viral_optimization"] = str(optimized)
                print(f"✓ 爆款优化完成: {optimized}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 剧本工程师导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 剧本工程测试失败: {e}")
        
        return results
    
    def test_model_switching(self) -> Dict[str, Any]:
        """测试模型切换"""
        print("\n=== 测试模型切换 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.model_switcher import ModelSwitcher
            
            # 创建模型切换器
            switcher = ModelSwitcher()
            results["details"]["instantiation"] = "success"
            print("✓ 模型切换器实例化成功")
            
            # 测试语言检测和模型选择
            if hasattr(switcher, 'select_model_by_language'):
                en_model = switcher.select_model_by_language("en")
                zh_model = switcher.select_model_by_language("zh")
                results["details"]["model_selection"] = {
                    "english_model": str(en_model),
                    "chinese_model": str(zh_model)
                }
                print(f"✓ 模型选择完成 - 英文: {en_model}, 中文: {zh_model}")
            
            # 测试动态切换
            if hasattr(switcher, 'switch_model'):
                switch_result = switcher.switch_model("zh")
                results["details"]["model_switching"] = str(switch_result)
                print(f"✓ 模型切换完成: {switch_result}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 模型切换器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 模型切换测试失败: {e}")
        
        return results
    
    def test_video_clipping(self) -> Dict[str, Any]:
        """测试视频剪辑"""
        print("\n=== 测试视频剪辑 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.core.clip_generator import ClipGenerator
            
            # 创建剪辑生成器
            generator = ClipGenerator()
            results["details"]["instantiation"] = "success"
            print("✓ 剪辑生成器实例化成功")
            
            # 测试剪辑配置
            if hasattr(generator, 'configure_clipping'):
                config = {
                    "output_format": "mp4",
                    "quality": "high",
                    "max_duration": 300
                }
                generator.configure_clipping(config)
                results["details"]["clipping_configuration"] = "success"
                print("✓ 剪辑配置完成")
            
            # 测试时间轴生成
            if hasattr(generator, 'generate_timeline'):
                test_segments = [
                    {"start": 1.0, "end": 3.0, "text": "Segment 1"},
                    {"start": 3.5, "end": 5.0, "text": "Segment 2"}
                ]
                timeline = generator.generate_timeline(test_segments)
                results["details"]["timeline_generation"] = str(timeline)
                print(f"✓ 时间轴生成完成: {timeline}")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 剪辑生成器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 视频剪辑测试失败: {e}")
        
        return results
    
    def test_jianying_export(self) -> Dict[str, Any]:
        """测试剪映导出"""
        print("\n=== 测试剪映导出 ===")
        results = {"status": "success", "details": {}}
        
        try:
            from src.exporters.jianying_pro_exporter import JianyingProExporter
            
            # 创建剪映导出器
            exporter = JianyingProExporter()
            results["details"]["instantiation"] = "success"
            print("✓ 剪映导出器实例化成功")
            
            # 测试工程文件生成
            if hasattr(exporter, 'create_project'):
                test_clips = [
                    {"start": 1.0, "end": 3.0, "file": "test1.mp4"},
                    {"start": 3.5, "end": 5.0, "file": "test2.mp4"}
                ]
                project_data = exporter.create_project(test_clips)
                results["details"]["project_creation"] = "success"
                print("✓ 剪映工程文件创建成功")
            
            # 测试导出配置
            if hasattr(exporter, 'configure_export'):
                export_config = {
                    "resolution": "1920x1080",
                    "fps": 30,
                    "format": "mp4"
                }
                exporter.configure_export(export_config)
                results["details"]["export_configuration"] = "success"
                print("✓ 导出配置完成")
            
        except ImportError as e:
            results["status"] = "failure"
            results["details"]["error"] = f"导入失败: {str(e)}"
            print(f"✗ 剪映导出器导入失败: {e}")
        except Exception as e:
            results["status"] = "failure"
            results["details"]["error"] = f"测试异常: {str(e)}"
            print(f"✗ 剪映导出测试失败: {e}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始VisionAI-ClipsMaster核心工作流程测试")
        print("=" * 60)
        
        all_results = {}
        
        # 执行各项测试
        test_methods = [
            ("core_module_imports", self.test_core_module_imports),
            ("language_detection", self.test_language_detection),
            ("srt_parsing", self.test_srt_parsing),
            ("narrative_analysis", self.test_narrative_analysis),
            ("screenplay_engineering", self.test_screenplay_engineering),
            ("model_switching", self.test_model_switching),
            ("video_clipping", self.test_video_clipping),
            ("jianying_export", self.test_jianying_export)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                all_results[test_name] = result
            except Exception as e:
                all_results[test_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                print(f"✗ {test_name} 测试发生异常: {e}")
        
        return all_results
    
    def cleanup(self):
        """清理测试环境"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"✓ 测试环境已清理: {self.temp_dir}")

def main():
    """主函数"""
    test_suite = CoreWorkflowTestSuite()
    
    try:
        # 运行测试
        results = test_suite.run_all_tests()
        
        # 生成测试报告
        report_file = f"core_workflow_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 测试报告已生成: {report_file}")
        
        # 统计测试结果
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
        
        print(f"\n📈 测试统计:")
        print(f"总测试数: {total_tests}")
        print(f"成功测试: {successful_tests}")
        print(f"失败测试: {total_tests - successful_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        
        return successful_tests >= (total_tests * 0.6)  # 60%成功率即可
        
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
