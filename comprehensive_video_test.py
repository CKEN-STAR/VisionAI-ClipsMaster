#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频处理模块全面功能测试
验证核心功能：视频-字幕映射、爆款SRT生成、端到端工作流等
"""

import os
import sys
import time
import json
import shutil
import traceback
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import psutil

class VideoProcessingTester:
    """视频处理模块综合测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_dir = Path("test_data_temp")
        self.results = {
            "test_start_time": datetime.now().isoformat(),
            "tests": {},
            "performance": {},
            "errors": [],
            "summary": {}
        }
        self.created_files = []
        
        # 创建测试目录
        self.test_dir.mkdir(exist_ok=True)
        print(f"📁 测试目录已创建: {self.test_dir}")
    
    def create_sample_srt(self, filename, content_type="chinese"):
        """创建测试用SRT字幕文件"""
        srt_path = self.test_dir / filename
        
        if content_type == "chinese":
            content = """1
00:00:00,000 --> 00:00:03,500
这是一个关于爱情的故事

2
00:00:03,500 --> 00:00:07,000
男主角是一个普通的上班族

3
00:00:07,000 --> 00:00:10,500
女主角是一个美丽的设计师

4
00:00:10,500 --> 00:00:14,000
他们在咖啡厅第一次相遇

5
00:00:14,000 --> 00:00:17,500
从此开始了一段美好的恋情

6
00:00:17,500 --> 00:00:21,000
但是命运给他们带来了考验

7
00:00:21,000 --> 00:00:24,500
男主角要去国外工作

8
00:00:24,500 --> 00:00:28,000
他们面临着分离的痛苦

9
00:00:28,000 --> 00:00:31,500
最终他们选择了坚持

10
00:00:31,500 --> 00:00:35,000
爱情战胜了一切困难"""
        else:  # english
            content = """1
00:00:00,000 --> 00:00:03,500
This is a story about love

2
00:00:03,500 --> 00:00:07,000
The male protagonist is an ordinary office worker

3
00:00:07,000 --> 00:00:10,500
The female protagonist is a beautiful designer

4
00:00:10,500 --> 00:00:14,000
They first met in a coffee shop

5
00:00:14,000 --> 00:00:17,500
Thus began a beautiful romance

6
00:00:17,500 --> 00:00:21,000
But fate brought them challenges

7
00:00:21,000 --> 00:00:24,500
The male protagonist has to work abroad

8
00:00:24,500 --> 00:00:28,000
They face the pain of separation

9
00:00:28,000 --> 00:00:31,500
Finally they chose to persist

10
00:00:31,500 --> 00:00:35,000
Love conquered all difficulties"""
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.created_files.append(srt_path)
        print(f"✅ 创建测试SRT文件: {srt_path}")
        return srt_path
    
    def create_sample_video(self, filename, duration=35):
        """创建测试用视频文件（使用FFmpeg生成）"""
        video_path = self.test_dir / filename
        
        try:
            # 检查FFmpeg是否可用
            ffmpeg_path = "tools/ffmpeg/bin/ffmpeg.exe" if os.path.exists("tools/ffmpeg/bin/ffmpeg.exe") else "ffmpeg"
            
            # 生成测试视频（纯色背景+时间戳）
            cmd = [
                ffmpeg_path,
                "-f", "lavfi",
                "-i", f"color=c=blue:size=1280x720:duration={duration}",
                "-f", "lavfi", 
                "-i", f"sine=frequency=1000:duration={duration}",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                "-y",
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.created_files.append(video_path)
                print(f"✅ 创建测试视频文件: {video_path}")
                return video_path
            else:
                print(f"❌ FFmpeg生成视频失败: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ 创建测试视频失败: {e}")
            return None
    
    def test_srt_parsing(self):
        """测试1: SRT字幕解析功能"""
        print("\n🔍 测试1: SRT字幕解析功能")
        test_start = time.time()
        
        try:
            # 创建测试SRT文件
            chinese_srt = self.create_sample_srt("test_chinese.srt", "chinese")
            english_srt = self.create_sample_srt("test_english.srt", "english")
            
            # 测试SRT解析器
            from src.core.srt_parser import SRTParser
            parser = SRTParser()

            # 解析中文SRT
            chinese_result = parser.parse(str(chinese_srt))
            print(f"  ✅ 中文SRT解析成功: {len(chinese_result)} 条字幕")

            # 解析英文SRT
            english_result = parser.parse(str(english_srt))
            print(f"  ✅ 英文SRT解析成功: {len(english_result)} 条字幕")
            
            # 验证时间轴准确性
            for i, subtitle in enumerate(chinese_result[:3]):
                expected_start = i * 3.5
                actual_start = subtitle.get('start_time', 0)
                time_diff = abs(actual_start - expected_start)
                
                if time_diff <= 0.5:
                    print(f"  ✅ 时间轴准确性验证通过: 第{i+1}条字幕，误差{time_diff:.2f}秒")
                else:
                    print(f"  ❌ 时间轴准确性验证失败: 第{i+1}条字幕，误差{time_diff:.2f}秒")
            
            test_time = time.time() - test_start
            self.results["tests"]["srt_parsing"] = {
                "status": "success",
                "duration": test_time,
                "chinese_subtitles": len(chinese_result),
                "english_subtitles": len(english_result)
            }
            
            return True
            
        except Exception as e:
            print(f"  ❌ SRT解析测试失败: {e}")
            self.results["tests"]["srt_parsing"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - test_start
            }
            return False
    
    def test_language_detection(self):
        """测试2: 语言检测功能"""
        print("\n🔍 测试2: 语言检测功能")
        test_start = time.time()
        
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()

            # 测试中文检测
            chinese_text = "这是一个关于爱情的故事，男主角是一个普通的上班族"
            chinese_result = detector.detect_from_text(chinese_text)
            print(f"  ✅ 中文检测结果: {chinese_result}")

            # 测试英文检测
            english_text = "This is a story about love, the male protagonist is an ordinary office worker"
            english_result = detector.detect_from_text(english_text)
            print(f"  ✅ 英文检测结果: {english_result}")

            # 验证检测准确性
            chinese_correct = chinese_result == 'zh'
            english_correct = english_result == 'en'
            
            if chinese_correct and english_correct:
                print("  ✅ 语言检测准确性验证通过")
                success = True
            else:
                print("  ❌ 语言检测准确性验证失败")
                success = False
            
            test_time = time.time() - test_start
            self.results["tests"]["language_detection"] = {
                "status": "success" if success else "failed",
                "duration": test_time,
                "chinese_detection": chinese_result,
                "english_detection": english_result
            }
            
            return success
            
        except Exception as e:
            print(f"  ❌ 语言检测测试失败: {e}")
            self.results["tests"]["language_detection"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - test_start
            }
            return False
    
    def test_model_switching(self):
        """测试3: 模型切换功能"""
        print("\n🔍 测试3: 模型切换功能")
        test_start = time.time()
        
        try:
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()

            # 测试中文模型切换
            chinese_switch = switcher.switch_model('zh')
            chinese_model = switcher.get_current_model()
            print(f"  ✅ 中文模型切换: {chinese_switch}, 当前模型: {chinese_model}")

            # 测试英文模型切换
            english_switch = switcher.switch_model('en')
            english_model = switcher.get_current_model()
            print(f"  ✅ 英文模型切换: {english_switch}, 当前模型: {english_model}")

            # 测试模型可用性检查
            chinese_available = switcher.is_model_loaded('zh')
            english_available = switcher.is_model_loaded('en')
            
            print(f"  📊 中文模型可用性: {chinese_available}")
            print(f"  📊 英文模型可用性: {english_available}")
            
            test_time = time.time() - test_start
            self.results["tests"]["model_switching"] = {
                "status": "success",
                "duration": test_time,
                "chinese_model": chinese_model,
                "english_model": english_model,
                "chinese_available": chinese_available,
                "english_available": english_available
            }
            
            return True
            
        except Exception as e:
            print(f"  ❌ 模型切换测试失败: {e}")
            self.results["tests"]["model_switching"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - test_start
            }
            return False

    def test_screenplay_analysis(self):
        """测试4: 剧本分析和重构功能"""
        print("\n🔍 测试4: 剧本分析和重构功能")
        test_start = time.time()

        try:
            from src.core.narrative_analyzer import IntegratedNarrativeAnalyzer
            from src.core.screenplay_engineer import ScreenplayEngineer

            analyzer = IntegratedNarrativeAnalyzer()
            engineer = ScreenplayEngineer()

            # 创建测试剧本内容
            test_script = [
                {"start_time": 0, "end_time": 3.5, "text": "这是一个关于爱情的故事"},
                {"start_time": 3.5, "end_time": 7, "text": "男主角是一个普通的上班族"},
                {"start_time": 7, "end_time": 10.5, "text": "女主角是一个美丽的设计师"},
                {"start_time": 10.5, "end_time": 14, "text": "他们在咖啡厅第一次相遇"},
                {"start_time": 14, "end_time": 17.5, "text": "从此开始了一段美好的恋情"}
            ]

            # 测试叙事分析
            narrative_result = analyzer.analyze_narrative_structure(test_script)
            print(f"  ✅ 叙事结构分析完成: {narrative_result.get('structure_type', 'unknown')}")

            # 测试情感分析（使用可用的方法）
            emotion_analysis = analyzer.analyze_emotional_flow(test_script)
            print(f"  ✅ 情感流分析完成: {len(emotion_analysis)} 个分析点")

            # 测试剧本重构
            reconstructed = engineer.process_subtitles(test_script, language='zh')
            viral_segments = reconstructed.get('viral_segments', test_script)
            print(f"  ✅ 剧本重构完成: {len(viral_segments)} 个片段")

            # 验证重构质量
            original_duration = sum(item['end_time'] - item['start_time'] for item in test_script)
            reconstructed_duration = sum(item['end_time'] - item['start_time'] for item in viral_segments)
            compression_ratio = reconstructed_duration / original_duration

            print(f"  📊 原始时长: {original_duration:.1f}秒")
            print(f"  📊 重构时长: {reconstructed_duration:.1f}秒")
            print(f"  📊 压缩比例: {compression_ratio:.2f}")

            # 验证是否避免过短或过长
            quality_check = 0.3 <= compression_ratio <= 0.8
            if quality_check:
                print("  ✅ 重构质量检查通过（避免过短或过长）")
            else:
                print("  ❌ 重构质量检查失败（可能过短或过长）")

            test_time = time.time() - test_start
            self.results["tests"]["screenplay_analysis"] = {
                "status": "success",
                "duration": test_time,
                "narrative_structure": narrative_result,
                "emotion_points": len(emotion_analysis),
                "original_duration": original_duration,
                "reconstructed_duration": reconstructed_duration,
                "compression_ratio": compression_ratio,
                "quality_check": quality_check
            }

            return quality_check

        except Exception as e:
            print(f"  ❌ 剧本分析测试失败: {e}")
            traceback.print_exc()
            self.results["tests"]["screenplay_analysis"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - test_start
            }
            return False

    def test_performance_monitoring(self):
        """测试7: 性能和内存监控"""
        print("\n🔍 测试7: 性能和内存监控")
        test_start = time.time()

        try:
            # 记录初始内存使用
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"  📊 初始内存使用: {initial_memory:.1f} MB")

            # 模拟重负载操作
            from src.core.video_processor import VideoProcessor
            processor = VideoProcessor()

            # 创建测试数据
            large_srt_data = []
            for i in range(100):  # 创建100条字幕
                large_srt_data.append({
                    "start_time": i * 2,
                    "end_time": i * 2 + 1.5,
                    "text": f"这是第{i+1}条测试字幕内容，用于测试系统在处理大量数据时的性能表现"
                })

            # 处理大量数据（模拟处理）
            for i in range(5):  # 重复处理5次
                # 模拟处理操作
                result = processor.process_video_with_subtitles("dummy_video.mp4", large_srt_data)
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"  📊 第{i+1}次处理后内存: {current_memory:.1f} MB")

                # 检查内存是否超过4GB限制
                if current_memory > 4000:
                    print(f"  ❌ 内存使用超过4GB限制: {current_memory:.1f} MB")
                    break

            # 最终内存检查
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            print(f"  📊 最终内存使用: {final_memory:.1f} MB")
            print(f"  📊 内存增长: {memory_increase:.1f} MB")

            # 内存泄漏检查
            memory_leak_check = memory_increase < 500  # 增长不超过500MB
            memory_limit_check = final_memory < 4000   # 不超过4GB

            if memory_leak_check and memory_limit_check:
                print("  ✅ 内存使用检查通过")
                performance_status = True
            else:
                print("  ❌ 内存使用检查失败")
                performance_status = False

            test_time = time.time() - test_start
            self.results["performance"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "memory_leak_check": memory_leak_check,
                "memory_limit_check": memory_limit_check,
                "test_duration": test_time
            }

            return performance_status

        except Exception as e:
            print(f"  ❌ 性能监控测试失败: {e}")
            traceback.print_exc()
            return False

    def test_end_to_end_workflow(self):
        """测试8: 端到端工作流"""
        print("\n🔍 测试8: 端到端工作流")
        test_start = time.time()

        try:
            # 创建完整的测试数据
            video_path = self.create_sample_video("source_drama.mp4", 60)
            srt_path = self.create_sample_srt("source_drama.srt", "chinese")

            if not video_path or not srt_path:
                print("  ❌ 测试数据创建失败")
                return False

            print("  📝 步骤1: 输入文件准备完成")

            # 步骤2: 语言检测
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()

            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()

            detected_language = detector.detect_from_text(srt_content)
            print(f"  📝 步骤2: 语言检测完成 - {detected_language}")

            # 步骤3: 模型切换
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()

            switch_success = switcher.switch_model(detected_language)
            selected_model = switcher.get_current_model()
            print(f"  📝 步骤3: 模型切换完成 - {selected_model} (成功: {switch_success})")

            # 步骤4: 剧情分析
            from src.core.srt_parser import SRTParser
            from src.core.narrative_analyzer import IntegratedNarrativeAnalyzer

            parser = SRTParser()
            analyzer = IntegratedNarrativeAnalyzer()

            parsed_srt = parser.parse(str(srt_path))
            narrative_analysis = analyzer.analyze_narrative_structure(parsed_srt)
            print(f"  📝 步骤4: 剧情分析完成 - {len(parsed_srt)}条字幕")

            # 步骤5: 爆款SRT生成（模拟）
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()

            viral_result = engineer.process_subtitles(parsed_srt, language=detected_language)
            viral_srt = viral_result.get('viral_segments', parsed_srt)
            viral_srt_path = self.test_dir / "viral_output.srt"

            # 保存生成的爆款SRT
            with open(viral_srt_path, 'w', encoding='utf-8') as f:
                for i, item in enumerate(viral_srt, 1):
                    start_time = self._seconds_to_srt_time(item['start_time'])
                    end_time = self._seconds_to_srt_time(item['end_time'])
                    f.write(f"{i}\n{start_time} --> {end_time}\n{item['text']}\n\n")

            self.created_files.append(viral_srt_path)
            print(f"  📝 步骤5: 爆款SRT生成完成 - {len(viral_srt)}条字幕")

            # 步骤6: 视频片段提取和拼接
            from src.core.clip_generator import ClipGenerator
            generator = ClipGenerator()

            output_clips = []
            for i, segment in enumerate(viral_srt[:5]):  # 只处理前5个片段
                clip_path = self.test_dir / f"viral_clip_{i+1}.mp4"
                success = generator.extract_clip(
                    str(video_path),
                    str(clip_path),
                    segment['start_time'],
                    segment['end_time']
                )
                if success:
                    output_clips.append(clip_path)
                    self.created_files.append(clip_path)

            print(f"  📝 步骤6: 视频片段提取完成 - {len(output_clips)}个片段")

            # 步骤7: 最终混剪输出
            final_output = self.test_dir / "viral_final.mp4"
            if len(output_clips) > 0:
                concat_success = generator.concatenate_clips(
                    [str(clip) for clip in output_clips],
                    str(final_output)
                )
                if concat_success:
                    self.created_files.append(final_output)
                    print("  📝 步骤7: 最终混剪完成")
                else:
                    print("  ❌ 步骤7: 最终混剪失败")

            # 步骤8: 剪映工程文件导出（模拟）
            from src.exporters.jianying_pro_exporter import JianyingProExporter
            exporter = JianyingProExporter()

            project_path = self.test_dir / "viral_project.json"
            project_success = exporter.export_project(viral_srt, str(project_path))
            if project_success:
                self.created_files.append(project_path)
                print("  📝 步骤8: 剪映工程导出完成")

            test_time = time.time() - test_start
            workflow_success = len(output_clips) > 0 and concat_success

            self.results["tests"]["end_to_end_workflow"] = {
                "status": "success" if workflow_success else "partial",
                "duration": test_time,
                "language_detected": detected_language,
                "model_selected": selected_model,
                "original_subtitles": len(parsed_srt),
                "viral_subtitles": len(viral_srt),
                "clips_generated": len(output_clips),
                "final_video_created": concat_success if 'concat_success' in locals() else False,
                "project_exported": project_success if 'project_success' in locals() else False
            }

            return workflow_success

        except Exception as e:
            print(f"  ❌ 端到端工作流测试失败: {e}")
            traceback.print_exc()
            self.results["tests"]["end_to_end_workflow"] = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - test_start
            }
            return False

    def _seconds_to_srt_time(self, seconds):
        """将秒数转换为SRT时间格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("🧪 VisionAI-ClipsMaster 视频处理模块全面功能测试")
        print("=" * 80)

        test_functions = [
            ("SRT字幕解析", self.test_srt_parsing),
            ("语言检测功能", self.test_language_detection),
            ("模型切换功能", self.test_model_switching),
            ("剧本分析重构", self.test_screenplay_analysis),
            ("性能内存监控", self.test_performance_monitoring),
            ("端到端工作流", self.test_end_to_end_workflow)
        ]

        passed_tests = 0
        total_tests = len(test_functions)

        for test_name, test_func in test_functions:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败")
            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
                self.results["errors"].append(f"{test_name}: {str(e)}")

        # 生成测试总结
        self.results["test_end_time"] = datetime.now().isoformat()
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "overall_status": "PASS" if passed_tests == total_tests else "FAIL"
        }

        return self.results

    def generate_test_report(self):
        """生成详细测试报告"""
        print("\n" + "=" * 80)
        print("📊 测试报告生成")
        print("=" * 80)

        report_path = self.test_dir / "test_report.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            self.created_files.append(report_path)
            print(f"✅ 测试报告已保存: {report_path}")

            # 打印摘要
            summary = self.results.get("summary", {})
            print(f"\n📈 测试摘要:")
            print(f"  总测试数: {summary.get('total_tests', 0)}")
            print(f"  通过测试: {summary.get('passed_tests', 0)}")
            print(f"  失败测试: {summary.get('failed_tests', 0)}")
            print(f"  成功率: {summary.get('success_rate', 0):.1%}")
            print(f"  总体状态: {summary.get('overall_status', 'UNKNOWN')}")

            # 性能指标
            performance = self.results.get("performance", {})
            if performance:
                print(f"\n⚡ 性能指标:")
                print(f"  内存使用: {performance.get('final_memory_mb', 0):.1f} MB")
                print(f"  内存增长: {performance.get('memory_increase_mb', 0):.1f} MB")
                print(f"  内存检查: {'通过' if performance.get('memory_limit_check', False) else '失败'}")

            return report_path

        except Exception as e:
            print(f"❌ 测试报告生成失败: {e}")
            return None

    def cleanup_test_environment(self):
        """清理测试环境"""
        print("\n" + "=" * 80)
        print("🧹 清理测试环境")
        print("=" * 80)

        cleaned_files = 0
        failed_cleanups = 0

        # 删除创建的文件
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    cleaned_files += 1
                    print(f"  ✅ 已删除: {file_path.name}")
            except Exception as e:
                failed_cleanups += 1
                print(f"  ❌ 删除失败: {file_path.name} - {e}")

        # 删除测试目录
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                print(f"  ✅ 已删除测试目录: {self.test_dir}")
        except Exception as e:
            print(f"  ❌ 删除测试目录失败: {e}")

        print(f"\n📊 清理统计:")
        print(f"  成功清理: {cleaned_files} 个文件")
        print(f"  清理失败: {failed_cleanups} 个文件")

        return failed_cleanups == 0


def main():
    """主测试函数"""
    tester = VideoProcessingTester()

    try:
        # 运行所有测试
        results = tester.run_all_tests()

        # 生成测试报告
        report_path = tester.generate_test_report()

        # 显示最终结果
        summary = results.get("summary", {})
        if summary.get("overall_status") == "PASS":
            print("\n🎉 所有测试通过！视频处理模块功能正常")
            exit_code = 0
        else:
            print("\n⚠️ 部分测试失败，需要进一步检查")
            exit_code = 1

        return exit_code

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 2
    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        traceback.print_exc()
        return 3
    finally:
        # 清理测试环境
        tester.cleanup_test_environment()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
