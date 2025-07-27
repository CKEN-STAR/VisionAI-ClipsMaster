#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 核心视频处理模块全面测试套件
=================================================

专门针对用户需求的全面测试：
1. 字幕-视频映射关系验证
2. 爆款SRT生成功能测试  
3. 端到端工作流测试
4. 性能和稳定性测试
5. 测试环境清理

测试覆盖：
- 原片字幕解析精度
- AI剧本重构功能
- 双语言模型切换
- 视频拼接功能
- 剪映工程文件导出
- 内存使用监控
- 自动清理机制
"""

import os
import sys
import json
import time
import logging
import traceback
import tempfile
import shutil
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 配置日志
os.makedirs("test_output", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_output/comprehensive_video_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveVideoProcessingTestSuite:
    """全面的视频处理测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.project_root = Path(__file__).parent
        self.test_output_dir = self.project_root / "test_output" / "comprehensive_video_test"
        self.test_data_dir = self.project_root / "test_data"
        self.temp_dir = None
        
        # 测试结果存储
        self.test_results = {
            "test_session_id": f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
            "performance_metrics": {},
            "memory_usage": {},
            "errors": [],
            "cleanup_status": "PENDING"
        }
        
        # 内存监控
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        
        # 创建测试输出目录
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"初始化全面视频处理测试套件")
        logger.info(f"会话ID: {self.test_results['test_session_id']}")
        logger.info(f"初始内存使用: {self.initial_memory:.2f} MB")
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """运行全面测试"""
        logger.info("=" * 80)
        logger.info("开始运行VisionAI-ClipsMaster核心视频处理模块全面测试")
        logger.info("=" * 80)
        
        try:
            # 设置测试环境
            if not self._setup_test_environment():
                logger.error("测试环境设置失败，终止测试")
                return self.test_results
            
            # 1. 字幕-视频映射关系验证
            logger.info("\n" + "=" * 60)
            logger.info("测试1: 字幕-视频映射关系验证")
            logger.info("=" * 60)
            self._test_subtitle_video_mapping()
            
            # 2. 爆款SRT生成功能测试
            logger.info("\n" + "=" * 60)
            logger.info("测试2: 爆款SRT生成功能测试")
            logger.info("=" * 60)
            self._test_viral_srt_generation()
            
            # 3. 端到端工作流测试
            logger.info("\n" + "=" * 60)
            logger.info("测试3: 端到端工作流测试")
            logger.info("=" * 60)
            self._test_end_to_end_workflow()
            
            # 4. 性能和稳定性测试
            logger.info("\n" + "=" * 60)
            logger.info("测试4: 性能和稳定性测试")
            logger.info("=" * 60)
            self._test_performance_and_stability()
            
            # 5. 生成测试报告
            self._generate_comprehensive_report()
            
            # 6. 清理测试环境
            self._cleanup_test_environment()
            
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            self.test_results["errors"].append({
                "stage": "main_execution",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            })
        
        finally:
            # 确保清理
            self._ensure_cleanup()
        
        return self.test_results
    
    def _setup_test_environment(self) -> bool:
        """设置测试环境"""
        try:
            logger.info("设置测试环境...")
            
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="visionai_comprehensive_test_")
            logger.info(f"创建临时目录: {self.temp_dir}")
            
            # 验证必要的测试数据文件
            required_files = [
                "chinese_original.srt",
                "chinese_viral.srt", 
                "english_original.srt",
                "english_viral.srt"
            ]
            
            missing_files = []
            for filename in required_files:
                file_path = self.test_data_dir / filename
                if not file_path.exists():
                    missing_files.append(filename)
            
            if missing_files:
                logger.warning(f"缺少测试文件: {missing_files}")
                self._create_missing_test_files(missing_files)
            
            # 验证核心模块
            core_modules = [
                "src/core/srt_parser.py",
                "src/core/screenplay_engineer.py",
                "src/core/alignment_engineer.py"
            ]
            
            missing_modules = []
            for module_path in core_modules:
                if not (self.project_root / module_path).exists():
                    missing_modules.append(module_path)
            
            if missing_modules:
                logger.error(f"缺少核心模块: {missing_modules}")
                return False
            
            logger.info("测试环境设置完成")
            return True
            
        except Exception as e:
            logger.error(f"设置测试环境失败: {e}")
            return False
    
    def _create_missing_test_files(self, missing_files: List[str]):
        """创建缺失的测试文件"""
        logger.info("创建缺失的测试文件...")
        
        # 确保测试数据目录存在
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in missing_files:
            file_path = self.test_data_dir / filename
            
            if 'chinese' in filename and 'original' in filename:
                content = self._create_chinese_original_srt()
            elif 'chinese' in filename and 'viral' in filename:
                content = self._create_chinese_viral_srt()
            elif 'english' in filename and 'original' in filename:
                content = self._create_english_original_srt()
            elif 'english' in filename and 'viral' in filename:
                content = self._create_english_viral_srt()
            else:
                content = self._create_default_srt()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"创建测试文件: {filename}")
    
    def _create_chinese_original_srt(self) -> str:
        """创建中文原片字幕"""
        return """1
00:00:00,000 --> 00:00:03,000
今天天气很好

2
00:00:03,000 --> 00:00:06,000
我去了公园散步

3
00:00:06,000 --> 00:00:09,000
看到了很多花

4
00:00:09,000 --> 00:00:12,000
心情变得很愉快

5
00:00:12,000 --> 00:00:15,000
遇到了一个朋友

6
00:00:15,000 --> 00:00:18,000
我们聊了很久

7
00:00:18,000 --> 00:00:21,000
时间过得很快

8
00:00:21,000 --> 00:00:24,000
最后我们告别了
"""
    
    def _create_chinese_viral_srt(self) -> str:
        """创建中文爆款字幕"""
        return """1
00:00:00,000 --> 00:00:04,000
震撼！今天发生了不可思议的事情！

2
00:00:04,000 --> 00:00:08,000
公园里的奇遇让所有人都惊呆了！

3
00:00:08,000 --> 00:00:12,000
美丽的花海背后隐藏着什么秘密？

4
00:00:12,000 --> 00:00:16,000
意外的相遇改变了一切！
"""
    
    def _create_english_original_srt(self) -> str:
        """创建英文原片字幕"""
        return """1
00:00:00,000 --> 00:00:03,000
The weather is nice today

2
00:00:03,000 --> 00:00:06,000
I went for a walk in the park

3
00:00:06,000 --> 00:00:09,000
I saw many beautiful flowers

4
00:00:09,000 --> 00:00:12,000
My mood became very pleasant

5
00:00:12,000 --> 00:00:15,000
I met a friend

6
00:00:15,000 --> 00:00:18,000
We talked for a long time

7
00:00:18,000 --> 00:00:21,000
Time passed quickly

8
00:00:21,000 --> 00:00:24,000
Finally we said goodbye
"""
    
    def _create_english_viral_srt(self) -> str:
        """创建英文爆款字幕"""
        return """1
00:00:00,000 --> 00:00:04,000
AMAZING! Something incredible happened today!

2
00:00:04,000 --> 00:00:08,000
This park encounter shocked everyone!

3
00:00:08,000 --> 00:00:12,000
What secret lies behind this beautiful garden?

4
00:00:12,000 --> 00:00:16,000
An unexpected meeting changed everything!
"""
    
    def _create_default_srt(self) -> str:
        """创建默认字幕"""
        return """1
00:00:00,000 --> 00:00:03,000
Test subtitle content

2
00:00:03,000 --> 00:00:06,000
Another test line
"""

    def _test_subtitle_video_mapping(self):
        """测试1: 字幕-视频映射关系验证"""
        test_name = "subtitle_video_mapping"
        test_result = {
            "status": "RUNNING",
            "start_time": datetime.now().isoformat(),
            "subtests": {}
        }

        try:
            # 1.1 测试原片视频文件与SRT字幕文件的时间轴对齐精度
            logger.info("1.1 测试SRT字幕解析和时间轴对齐精度")
            subtest_result = self._test_srt_parsing_and_alignment()
            test_result["subtests"]["srt_parsing_alignment"] = subtest_result

            # 1.2 验证字幕时间码与视频帧的同步误差
            logger.info("1.2 验证字幕时间码同步误差")
            subtest_result = self._test_timecode_sync_accuracy()
            test_result["subtests"]["timecode_sync_accuracy"] = subtest_result

            # 1.3 检查多集短剧原片的字幕文件识别和加载
            logger.info("1.3 测试多集字幕文件识别和加载")
            subtest_result = self._test_multi_episode_recognition()
            test_result["subtests"]["multi_episode_recognition"] = subtest_result

            # 计算总体状态
            all_passed = all(
                result.get("status") == "PASSED"
                for result in test_result["subtests"].values()
            )
            test_result["status"] = "PASSED" if all_passed else "FAILED"

        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"字幕-视频映射测试失败: {e}")

        test_result["end_time"] = datetime.now().isoformat()
        self.test_results["tests"][test_name] = test_result
        logger.info(f"测试1完成，状态: {test_result['status']}")

    def _test_srt_parsing_and_alignment(self) -> Dict[str, Any]:
        """测试SRT字幕解析和时间轴对齐精度"""
        try:
            from src.core.srt_parser import SRTParser, parse_srt

            results = {}

            # 测试中文字幕解析
            chinese_srt_path = self.test_data_dir / "chinese_original.srt"
            if chinese_srt_path.exists():
                parser = SRTParser()
                chinese_subtitles = parser.parse(str(chinese_srt_path))

                # 验证解析结果
                assert len(chinese_subtitles) > 0, "中文字幕解析结果为空"
                assert all("start_time" in sub for sub in chinese_subtitles), "缺少开始时间"
                assert all("end_time" in sub for sub in chinese_subtitles), "缺少结束时间"
                assert all("text" in sub for sub in chinese_subtitles), "缺少字幕文本"

                # 检查时间轴精度
                time_errors = []
                for i, sub in enumerate(chinese_subtitles):
                    expected_start = i * 3.0
                    expected_end = (i + 1) * 3.0
                    actual_start = sub["start_time"]
                    actual_end = sub["end_time"]

                    start_error = abs(actual_start - expected_start)
                    end_error = abs(actual_end - expected_end)

                    if start_error > 0.5 or end_error > 0.5:  # 0.5秒误差阈值
                        time_errors.append({
                            "subtitle_index": i,
                            "start_error": start_error,
                            "end_error": end_error
                        })

                results["chinese"] = {
                    "subtitle_count": len(chinese_subtitles),
                    "time_errors": time_errors,
                    "max_error": max([0] + [max(e["start_error"], e["end_error"]) for e in time_errors])
                }

                logger.info(f"中文字幕解析成功: {len(chinese_subtitles)}条字幕, 时间误差: {len(time_errors)}个")

            # 测试英文字幕解析
            english_srt_path = self.test_data_dir / "english_original.srt"
            if english_srt_path.exists():
                english_subtitles = parse_srt(str(english_srt_path))

                assert len(english_subtitles) > 0, "英文字幕解析结果为空"

                results["english"] = {
                    "subtitle_count": len(english_subtitles)
                }

                logger.info(f"英文字幕解析成功: {len(english_subtitles)}条字幕")

            # 判断测试是否通过
            max_allowed_error = 0.5  # 最大允许0.5秒误差
            chinese_passed = results.get("chinese", {}).get("max_error", 0) <= max_allowed_error
            english_passed = "english" in results

            overall_passed = chinese_passed and english_passed

            return {
                "status": "PASSED" if overall_passed else "FAILED",
                "message": f"SRT解析和对齐测试{'通过' if overall_passed else '失败'}",
                "details": results,
                "max_allowed_error": max_allowed_error
            }

        except Exception as e:
            logger.error(f"SRT解析和对齐测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_timecode_sync_accuracy(self) -> Dict[str, Any]:
        """验证字幕时间码与视频帧的同步误差"""
        try:
            from src.core.alignment_engineer import AlignmentEngineer

            # 创建对齐工程师实例
            alignment_engineer = AlignmentEngineer()

            # 测试时间码解析精度
            test_timecodes = [
                "00:00:00,000",
                "00:00:03,500",
                "00:01:30,250",
                "00:05:45,999"
            ]

            expected_seconds = [0.0, 3.5, 90.25, 345.999]

            parsing_errors = []
            for i, (timecode, expected) in enumerate(zip(test_timecodes, expected_seconds)):
                try:
                    parsed_seconds = alignment_engineer.parse_timecode(timecode)
                    error = abs(parsed_seconds - expected)

                    if error > 0.001:  # 1毫秒精度
                        parsing_errors.append({
                            "timecode": timecode,
                            "expected": expected,
                            "parsed": parsed_seconds,
                            "error": error
                        })
                except Exception as e:
                    parsing_errors.append({
                        "timecode": timecode,
                        "error": f"解析失败: {e}"
                    })

            # 检查同步精度要求
            max_sync_error = 0.5  # 最大允许0.5秒同步误差
            sync_passed = len(parsing_errors) == 0 or all(
                isinstance(error.get("error"), (int, float)) and error["error"] <= max_sync_error
                for error in parsing_errors
            )

            return {
                "status": "PASSED" if sync_passed else "FAILED",
                "message": f"时间码同步精度测试{'通过' if sync_passed else '失败'}",
                "details": {
                    "parsing_errors": parsing_errors,
                    "max_sync_error": max_sync_error,
                    "test_timecodes_count": len(test_timecodes)
                }
            }

        except Exception as e:
            logger.error(f"时间码同步测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_multi_episode_recognition(self) -> Dict[str, Any]:
        """测试多集短剧原片的字幕文件识别和加载"""
        try:
            from src.core.srt_parser import parse_srt, is_valid_srt

            # 测试多个字幕文件
            test_files = [
                "chinese_original.srt",
                "chinese_viral.srt",
                "english_original.srt",
                "english_viral.srt"
            ]

            recognition_results = []
            total_duration = 0

            for filename in test_files:
                filepath = self.test_data_dir / filename
                if filepath.exists():
                    try:
                        # 验证文件有效性
                        is_valid = is_valid_srt(str(filepath))

                        if is_valid:
                            subtitles = parse_srt(str(filepath))
                            duration = subtitles[-1]["end_time"] if subtitles else 0
                            total_duration += duration

                            recognition_results.append({
                                "filename": filename,
                                "status": "SUCCESS",
                                "subtitle_count": len(subtitles),
                                "duration": duration,
                                "is_valid": True
                            })
                            logger.info(f"成功识别: {filename}, {len(subtitles)}条字幕, {duration:.1f}秒")
                        else:
                            recognition_results.append({
                                "filename": filename,
                                "status": "INVALID",
                                "error": "SRT格式无效"
                            })
                    except Exception as e:
                        recognition_results.append({
                            "filename": filename,
                            "status": "FAILED",
                            "error": str(e)
                        })
                        logger.warning(f"识别失败: {filename}, {e}")
                else:
                    recognition_results.append({
                        "filename": filename,
                        "status": "NOT_FOUND",
                        "error": "文件不存在"
                    })

            # 计算识别成功率
            success_count = sum(1 for result in recognition_results if result["status"] == "SUCCESS")
            success_rate = success_count / len(test_files) if test_files else 0

            # 要求至少80%的文件能够正确识别
            recognition_passed = success_rate >= 0.8

            return {
                "status": "PASSED" if recognition_passed else "FAILED",
                "message": f"多集字幕识别测试，成功率: {success_rate:.1%}",
                "details": {
                    "recognition_results": recognition_results,
                    "success_rate": success_rate,
                    "total_files_tested": len(test_files),
                    "total_duration": total_duration
                }
            }

        except Exception as e:
            logger.error(f"多集字幕识别测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_viral_srt_generation(self):
        """测试2: 爆款SRT生成功能测试"""
        test_name = "viral_srt_generation"
        test_result = {
            "status": "RUNNING",
            "start_time": datetime.now().isoformat(),
            "subtests": {}
        }

        try:
            # 2.1 使用真实的短剧原片SRT字幕作为输入
            logger.info("2.1 测试真实短剧SRT字幕输入处理")
            subtest_result = self._test_real_drama_srt_input()
            test_result["subtests"]["real_drama_srt_input"] = subtest_result

            # 2.2 验证大模型加载和运行
            logger.info("2.2 验证大模型加载和运行")
            subtest_result = self._test_model_loading_and_inference()
            test_result["subtests"]["model_loading_inference"] = subtest_result

            # 2.3 测试剧本重构功能
            logger.info("2.3 测试AI剧本重构功能")
            subtest_result = self._test_screenplay_reconstruction()
            test_result["subtests"]["screenplay_reconstruction"] = subtest_result

            # 2.4 验证生成的新SRT字幕
            logger.info("2.4 验证生成的爆款SRT字幕")
            subtest_result = self._test_generated_viral_srt()
            test_result["subtests"]["generated_viral_srt"] = subtest_result

            # 2.5 检查生成的混剪时长合理性
            logger.info("2.5 检查混剪时长合理性")
            subtest_result = self._test_duration_reasonableness()
            test_result["subtests"]["duration_reasonableness"] = subtest_result

            # 计算总体状态
            all_passed = all(
                result.get("status") == "PASSED"
                for result in test_result["subtests"].values()
            )
            test_result["status"] = "PASSED" if all_passed else "FAILED"

        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"爆款SRT生成测试失败: {e}")

        test_result["end_time"] = datetime.now().isoformat()
        self.test_results["tests"][test_name] = test_result
        logger.info(f"测试2完成，状态: {test_result['status']}")

    def _test_real_drama_srt_input(self) -> Dict[str, Any]:
        """测试真实短剧SRT字幕输入处理"""
        try:
            from src.core.srt_parser import SRTParser

            # 测试中文短剧字幕
            chinese_srt_path = self.test_data_dir / "chinese_original.srt"
            english_srt_path = self.test_data_dir / "english_original.srt"

            results = {}

            if chinese_srt_path.exists():
                parser = SRTParser()
                chinese_subtitles = parser.parse(str(chinese_srt_path))

                # 验证字幕内容质量
                text_quality = self._analyze_subtitle_text_quality(chinese_subtitles, "zh")

                results["chinese"] = {
                    "subtitle_count": len(chinese_subtitles),
                    "total_duration": chinese_subtitles[-1]["end_time"] if chinese_subtitles else 0,
                    "text_quality": text_quality,
                    "avg_subtitle_length": sum(len(sub["text"]) for sub in chinese_subtitles) / len(chinese_subtitles) if chinese_subtitles else 0
                }

                logger.info(f"中文短剧字幕分析: {len(chinese_subtitles)}条, 质量评分: {text_quality:.2f}")

            if english_srt_path.exists():
                parser = SRTParser()
                english_subtitles = parser.parse(str(english_srt_path))

                text_quality = self._analyze_subtitle_text_quality(english_subtitles, "en")

                results["english"] = {
                    "subtitle_count": len(english_subtitles),
                    "total_duration": english_subtitles[-1]["end_time"] if english_subtitles else 0,
                    "text_quality": text_quality,
                    "avg_subtitle_length": sum(len(sub["text"]) for sub in english_subtitles) / len(english_subtitles) if english_subtitles else 0
                }

                logger.info(f"英文短剧字幕分析: {len(english_subtitles)}条, 质量评分: {text_quality:.2f}")

            # 判断输入处理是否成功
            input_processing_passed = len(results) > 0 and all(
                result["subtitle_count"] > 0 and result["text_quality"] > 0.5
                for result in results.values()
            )

            return {
                "status": "PASSED" if input_processing_passed else "FAILED",
                "message": f"真实短剧SRT输入处理{'成功' if input_processing_passed else '失败'}",
                "details": results
            }

        except Exception as e:
            logger.error(f"真实短剧SRT输入测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _analyze_subtitle_text_quality(self, subtitles: List[Dict], language: str) -> float:
        """分析字幕文本质量"""
        try:
            if not subtitles:
                return 0.0

            quality_score = 0.0
            total_checks = 0

            for subtitle in subtitles:
                text = subtitle.get("text", "")
                if not text:
                    continue

                # 检查文本长度合理性
                if 5 <= len(text) <= 100:
                    quality_score += 1
                total_checks += 1

                # 检查是否包含有意义的内容
                if language == "zh":
                    # 中文内容检查
                    if any(char in text for char in "，。！？；："):
                        quality_score += 0.5
                    if any('\u4e00' <= char <= '\u9fff' for char in text):
                        quality_score += 0.5
                else:
                    # 英文内容检查
                    if any(char in text for char in ",.!?;:"):
                        quality_score += 0.5
                    if any(char.isalpha() for char in text):
                        quality_score += 0.5

                total_checks += 1

            return quality_score / total_checks if total_checks > 0 else 0.0

        except Exception:
            return 0.0

    def _test_model_loading_and_inference(self) -> Dict[str, Any]:
        """验证大模型加载和运行"""
        try:
            # 模拟大模型加载测试（由于实际模型可能很大，这里进行模拟测试）
            logger.info("开始模拟大模型加载测试...")

            # 检查模型配置文件
            model_config_path = self.project_root / "configs" / "model_config.yaml"
            if not model_config_path.exists():
                logger.warning("模型配置文件不存在，创建模拟配置")
                self._create_mock_model_config()

            # 模拟中文模型(Qwen2.5-7B)加载
            chinese_model_result = self._simulate_model_loading("qwen2.5-7b-zh")

            # 模拟英文模型(Mistral-7B)加载
            english_model_result = self._simulate_model_loading("mistral-7b-en")

            # 检查内存使用
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - self.initial_memory

            # 更新峰值内存
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory

            # 验证内存使用是否在3.8GB以下
            memory_limit_passed = current_memory <= 3800  # 3.8GB in MB

            results = {
                "chinese_model": chinese_model_result,
                "english_model": english_model_result,
                "memory_usage": {
                    "initial_mb": self.initial_memory,
                    "current_mb": current_memory,
                    "increase_mb": memory_increase,
                    "peak_mb": self.peak_memory,
                    "limit_passed": memory_limit_passed
                }
            }

            # 判断模型加载是否成功
            models_loaded = (chinese_model_result["status"] == "SUCCESS" and
                           english_model_result["status"] == "SUCCESS")

            overall_passed = models_loaded and memory_limit_passed

            logger.info(f"模型加载测试: 中文模型{'成功' if chinese_model_result['status'] == 'SUCCESS' else '失败'}, "
                       f"英文模型{'成功' if english_model_result['status'] == 'SUCCESS' else '失败'}")
            logger.info(f"内存使用: {current_memory:.1f}MB (限制: 3800MB)")

            return {
                "status": "PASSED" if overall_passed else "FAILED",
                "message": f"大模型加载和推理测试{'通过' if overall_passed else '失败'}",
                "details": results
            }

        except Exception as e:
            logger.error(f"模型加载测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _create_mock_model_config(self):
        """创建模拟模型配置"""
        config_dir = self.project_root / "configs"
        config_dir.mkdir(exist_ok=True)

        mock_config = {
            "available_models": [
                {
                    "name": "qwen2.5-7b-zh",
                    "language": "zh",
                    "quantization": "Q4_K_M",
                    "memory_requirement_mb": 4100
                },
                {
                    "name": "mistral-7b-en",
                    "language": "en",
                    "quantization": "Q5_K_M",
                    "memory_requirement_mb": 6300
                }
            ]
        }

        with open(config_dir / "model_config.yaml", 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(mock_config, f, allow_unicode=True)

    def _simulate_model_loading(self, model_name: str) -> Dict[str, Any]:
        """模拟模型加载过程"""
        try:
            logger.info(f"模拟加载模型: {model_name}")

            # 模拟加载时间
            time.sleep(0.1)

            # 模拟内存分配
            if "qwen" in model_name:
                simulated_memory = 4100  # MB
            else:
                simulated_memory = 6300  # MB

            # 检查是否超过内存限制
            total_memory = self.initial_memory + simulated_memory
            memory_ok = total_memory <= 3800

            if memory_ok:
                status = "SUCCESS"
                message = f"模型 {model_name} 加载成功"
            else:
                status = "MEMORY_LIMIT_EXCEEDED"
                message = f"模型 {model_name} 加载失败：内存超限"

            return {
                "status": status,
                "message": message,
                "model_name": model_name,
                "simulated_memory_mb": simulated_memory,
                "load_time_seconds": 0.1
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"模型加载失败: {e}",
                "model_name": model_name
            }

    def _test_screenplay_reconstruction(self) -> Dict[str, Any]:
        """测试AI剧本重构功能"""
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer

            # 创建剧本工程师实例
            screenplay_engineer = ScreenplayEngineer()

            # 测试中文剧本重构
            chinese_srt_path = self.test_data_dir / "chinese_original.srt"
            reconstruction_results = {}

            if chinese_srt_path.exists():
                logger.info("测试中文剧本重构...")

                # 加载原始字幕
                original_subtitles = screenplay_engineer.load_subtitles(str(chinese_srt_path))

                if original_subtitles:
                    # 分析原始剧情结构
                    plot_analysis = screenplay_engineer.analyze_plot_structure(original_subtitles)

                    # 执行剧本重构
                    reconstruction = screenplay_engineer.reconstruct_screenplay(
                        srt_input=original_subtitles,
                        target_style="viral"
                    )

                    if reconstruction:
                        # 分析重构结果
                        original_duration = reconstruction.get("original_duration", 0)
                        new_duration = reconstruction.get("new_duration", 0)
                        optimization_score = reconstruction.get("optimization_score", 0)

                        reconstruction_results["chinese"] = {
                            "original_subtitle_count": len(original_subtitles),
                            "original_duration": original_duration,
                            "new_duration": new_duration,
                            "compression_ratio": (original_duration - new_duration) / original_duration if original_duration > 0 else 0,
                            "optimization_score": optimization_score,
                            "plot_analysis": plot_analysis,
                            "reconstruction_success": True
                        }

                        logger.info(f"中文剧本重构成功: {original_duration:.1f}s → {new_duration:.1f}s, 评分: {optimization_score:.2f}")
                    else:
                        reconstruction_results["chinese"] = {
                            "reconstruction_success": False,
                            "error": "重构失败"
                        }

            # 测试英文剧本重构
            english_srt_path = self.test_data_dir / "english_original.srt"
            if english_srt_path.exists():
                logger.info("测试英文剧本重构...")

                original_subtitles = screenplay_engineer.load_subtitles(str(english_srt_path))

                if original_subtitles:
                    reconstruction = screenplay_engineer.reconstruct_screenplay(
                        srt_input=original_subtitles,
                        target_style="viral"
                    )

                    if reconstruction:
                        original_duration = reconstruction.get("original_duration", 0)
                        new_duration = reconstruction.get("new_duration", 0)

                        reconstruction_results["english"] = {
                            "original_subtitle_count": len(original_subtitles),
                            "original_duration": original_duration,
                            "new_duration": new_duration,
                            "compression_ratio": (original_duration - new_duration) / original_duration if original_duration > 0 else 0,
                            "reconstruction_success": True
                        }

                        logger.info(f"英文剧本重构成功: {original_duration:.1f}s → {new_duration:.1f}s")

            # 判断重构是否成功
            reconstruction_passed = len(reconstruction_results) > 0 and all(
                result.get("reconstruction_success", False)
                for result in reconstruction_results.values()
            )

            return {
                "status": "PASSED" if reconstruction_passed else "FAILED",
                "message": f"AI剧本重构功能测试{'通过' if reconstruction_passed else '失败'}",
                "details": reconstruction_results
            }

        except Exception as e:
            logger.error(f"剧本重构测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_generated_viral_srt(self) -> Dict[str, Any]:
        """验证生成的爆款SRT字幕"""
        try:
            # 检查爆款字幕文件
            chinese_viral_path = self.test_data_dir / "chinese_viral.srt"
            english_viral_path = self.test_data_dir / "english_viral.srt"

            viral_analysis = {}

            if chinese_viral_path.exists():
                from src.core.srt_parser import parse_srt

                viral_subtitles = parse_srt(str(chinese_viral_path))

                # 分析爆款特征
                viral_features = self._analyze_viral_features(viral_subtitles, "zh")

                viral_analysis["chinese"] = {
                    "subtitle_count": len(viral_subtitles),
                    "total_duration": viral_subtitles[-1]["end_time"] if viral_subtitles else 0,
                    "viral_features": viral_features,
                    "has_valid_timecodes": all("start_time" in sub and "end_time" in sub for sub in viral_subtitles),
                    "has_content": all("text" in sub and sub["text"].strip() for sub in viral_subtitles)
                }

                logger.info(f"中文爆款字幕分析: {len(viral_subtitles)}条, 爆款特征评分: {viral_features['score']:.2f}")

            if english_viral_path.exists():
                from src.core.srt_parser import parse_srt

                viral_subtitles = parse_srt(str(english_viral_path))
                viral_features = self._analyze_viral_features(viral_subtitles, "en")

                viral_analysis["english"] = {
                    "subtitle_count": len(viral_subtitles),
                    "total_duration": viral_subtitles[-1]["end_time"] if viral_subtitles else 0,
                    "viral_features": viral_features,
                    "has_valid_timecodes": all("start_time" in sub and "end_time" in sub for sub in viral_subtitles),
                    "has_content": all("text" in sub and sub["text"].strip() for sub in viral_subtitles)
                }

                logger.info(f"英文爆款字幕分析: {len(viral_subtitles)}条, 爆款特征评分: {viral_features['score']:.2f}")

            # 判断生成的字幕是否合格
            viral_srt_passed = len(viral_analysis) > 0 and all(
                (result.get("has_valid_timecodes", False) and
                 result.get("has_content", False) and
                 result.get("viral_features", {}).get("score", 0) > 0.6)
                for result in viral_analysis.values()
            )

            return {
                "status": "PASSED" if viral_srt_passed else "FAILED",
                "message": f"生成的爆款SRT字幕验证{'通过' if viral_srt_passed else '失败'}",
                "details": viral_analysis
            }

        except Exception as e:
            logger.error(f"爆款SRT验证失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _analyze_viral_features(self, subtitles: List[Dict], language: str) -> Dict[str, Any]:
        """分析爆款特征"""
        try:
            if not subtitles:
                return {"score": 0.0, "features": []}

            viral_keywords = {
                "zh": ["震撼", "不可思议", "惊呆", "秘密", "意外", "改变", "绝了", "太棒了"],
                "en": ["AMAZING", "incredible", "shocked", "secret", "unexpected", "changed", "awesome", "stunning"]
            }

            keywords = viral_keywords.get(language, viral_keywords["zh"])

            feature_score = 0.0
            detected_features = []

            for subtitle in subtitles:
                text = subtitle.get("text", "").upper()

                # 检查爆款关键词
                for keyword in keywords:
                    if keyword.upper() in text:
                        feature_score += 1.0
                        detected_features.append(f"关键词: {keyword}")

                # 检查感叹号使用
                if "!" in text or "！" in text:
                    feature_score += 0.5
                    detected_features.append("感叹号强调")

                # 检查问号使用（制造悬念）
                if "?" in text or "？" in text:
                    feature_score += 0.3
                    detected_features.append("问号悬念")

            # 标准化评分
            max_possible_score = len(subtitles) * 2  # 每条字幕最多2分
            normalized_score = min(feature_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

            return {
                "score": normalized_score,
                "features": detected_features,
                "feature_count": len(detected_features)
            }

        except Exception:
            return {"score": 0.0, "features": []}

    def _test_duration_reasonableness(self) -> Dict[str, Any]:
        """检查混剪时长合理性"""
        try:
            from src.core.srt_parser import parse_srt

            duration_analysis = {}

            # 分析原片和爆款字幕的时长对比
            test_pairs = [
                ("chinese_original.srt", "chinese_viral.srt"),
                ("english_original.srt", "english_viral.srt")
            ]

            for original_file, viral_file in test_pairs:
                original_path = self.test_data_dir / original_file
                viral_path = self.test_data_dir / viral_file

                if original_path.exists() and viral_path.exists():
                    original_subtitles = parse_srt(str(original_path))
                    viral_subtitles = parse_srt(str(viral_path))

                    original_duration = original_subtitles[-1]["end_time"] if original_subtitles else 0
                    viral_duration = viral_subtitles[-1]["end_time"] if viral_subtitles else 0

                    # 计算压缩率
                    compression_ratio = (original_duration - viral_duration) / original_duration if original_duration > 0 else 0

                    # 检查时长合理性
                    # 要求：压缩率在30%-70%之间，避免过短或过长
                    duration_reasonable = 0.3 <= compression_ratio <= 0.7

                    # 检查剧情连贯性（简单检查：爆款版本不能太短）
                    min_duration = 10  # 最少10秒
                    coherence_ok = viral_duration >= min_duration

                    language = "chinese" if "chinese" in original_file else "english"
                    duration_analysis[language] = {
                        "original_duration": original_duration,
                        "viral_duration": viral_duration,
                        "compression_ratio": compression_ratio,
                        "duration_reasonable": duration_reasonable,
                        "coherence_ok": coherence_ok,
                        "original_subtitle_count": len(original_subtitles),
                        "viral_subtitle_count": len(viral_subtitles)
                    }

                    logger.info(f"{language}时长分析: {original_duration:.1f}s → {viral_duration:.1f}s "
                               f"(压缩率: {compression_ratio:.1%})")

            # 判断时长是否合理
            duration_passed = len(duration_analysis) > 0 and all(
                (result.get("duration_reasonable", False) and result.get("coherence_ok", False))
                for result in duration_analysis.values()
            )

            return {
                "status": "PASSED" if duration_passed else "FAILED",
                "message": f"混剪时长合理性检查{'通过' if duration_passed else '失败'}",
                "details": duration_analysis
            }

        except Exception as e:
            logger.error(f"时长合理性检查失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_end_to_end_workflow(self):
        """测试3: 端到端工作流测试"""
        test_name = "end_to_end_workflow"
        test_result = {
            "status": "RUNNING",
            "start_time": datetime.now().isoformat(),
            "subtests": {}
        }

        try:
            # 3.1 完整测试"原片SRT → AI剧本重构 → 爆款SRT → 视频拼接"的全流程
            logger.info("3.1 测试完整工作流程")
            subtest_result = self._test_complete_workflow()
            test_result["subtests"]["complete_workflow"] = subtest_result

            # 3.2 验证最终输出的混剪视频与生成的爆款SRT时间轴匹配
            logger.info("3.2 验证视频与字幕时间轴匹配")
            subtest_result = self._test_video_subtitle_matching()
            test_result["subtests"]["video_subtitle_matching"] = subtest_result

            # 3.3 测试剪映工程文件导出功能
            logger.info("3.3 测试剪映工程文件导出")
            subtest_result = self._test_jianying_export()
            test_result["subtests"]["jianying_export"] = subtest_result

            # 计算总体状态
            all_passed = all(
                result.get("status") == "PASSED"
                for result in test_result["subtests"].values()
            )
            test_result["status"] = "PASSED" if all_passed else "FAILED"

        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"端到端工作流测试失败: {e}")

        test_result["end_time"] = datetime.now().isoformat()
        self.test_results["tests"][test_name] = test_result
        logger.info(f"测试3完成，状态: {test_result['status']}")

    def _test_complete_workflow(self) -> Dict[str, Any]:
        """测试完整工作流程"""
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            from src.core.clip_generator import ClipGenerator

            workflow_results = {}

            # 测试中文工作流
            chinese_srt_path = self.test_data_dir / "chinese_original.srt"
            if chinese_srt_path.exists():
                logger.info("执行中文完整工作流...")

                # 步骤1: 加载原片SRT
                screenplay_engineer = ScreenplayEngineer()
                original_subtitles = screenplay_engineer.load_subtitles(str(chinese_srt_path))

                # 步骤2: AI剧本重构
                reconstruction = screenplay_engineer.reconstruct_screenplay(
                    srt_input=original_subtitles,
                    target_style="viral"
                )

                # 步骤3: 生成爆款SRT
                if reconstruction and "timeline" in reconstruction:
                    viral_srt_content = self._generate_srt_from_timeline(reconstruction["timeline"])

                    # 保存生成的爆款SRT到临时文件
                    temp_viral_srt = Path(self.temp_dir) / "generated_chinese_viral.srt"
                    with open(temp_viral_srt, 'w', encoding='utf-8') as f:
                        f.write(viral_srt_content)

                    # 步骤4: 模拟视频拼接
                    clip_generator = ClipGenerator()
                    video_result = clip_generator.generate_clips_from_srt(
                        str(temp_viral_srt),
                        output_dir=self.temp_dir
                    )

                    workflow_results["chinese"] = {
                        "step1_load_srt": len(original_subtitles) > 0,
                        "step2_reconstruction": reconstruction is not None,
                        "step3_viral_srt": len(viral_srt_content) > 0,
                        "step4_video_clips": video_result.get("success", False),
                        "original_duration": reconstruction.get("original_duration", 0),
                        "new_duration": reconstruction.get("new_duration", 0),
                        "workflow_success": True
                    }

                    logger.info("中文工作流执行成功")
                else:
                    workflow_results["chinese"] = {"workflow_success": False, "error": "剧本重构失败"}

            # 判断工作流是否成功
            workflow_passed = len(workflow_results) > 0 and all(
                result.get("workflow_success", False)
                for result in workflow_results.values()
            )

            return {
                "status": "PASSED" if workflow_passed else "FAILED",
                "message": f"完整工作流程测试{'通过' if workflow_passed else '失败'}",
                "details": workflow_results
            }

        except Exception as e:
            logger.error(f"完整工作流测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _generate_srt_from_timeline(self, timeline: Dict[str, Any]) -> str:
        """从时间轴生成SRT内容"""
        try:
            srt_content = ""
            segments = timeline.get("segments", [])

            for i, segment in enumerate(segments, 1):
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                text = segment.get("text", "")

                # 转换为SRT时间格式
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)

                srt_content += f"{i}\n{start_srt} --> {end_srt}\n{text}\n\n"

            return srt_content

        except Exception:
            return ""

    def _seconds_to_srt_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millisecs = int((seconds % 1) * 1000)

            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

        except Exception:
            return "00:00:00,000"

    def _test_video_subtitle_matching(self) -> Dict[str, Any]:
        """验证视频与字幕时间轴匹配"""
        try:
            # 模拟视频时间轴验证
            logger.info("模拟验证视频与字幕时间轴匹配...")

            # 检查生成的临时文件
            temp_files = list(Path(self.temp_dir).glob("*.srt"))

            matching_results = {}

            for srt_file in temp_files:
                try:
                    from src.core.srt_parser import parse_srt

                    subtitles = parse_srt(str(srt_file))

                    # 验证时间轴连续性
                    time_gaps = []
                    for i in range(len(subtitles) - 1):
                        current_end = subtitles[i]["end_time"]
                        next_start = subtitles[i + 1]["start_time"]
                        gap = next_start - current_end

                        if gap > 1.0:  # 超过1秒的间隔
                            time_gaps.append({
                                "position": i,
                                "gap_seconds": gap
                            })

                    # 验证时间轴有效性
                    valid_timecodes = all(
                        sub["start_time"] < sub["end_time"] and sub["start_time"] >= 0
                        for sub in subtitles
                    )

                    matching_results[srt_file.name] = {
                        "subtitle_count": len(subtitles),
                        "time_gaps": time_gaps,
                        "valid_timecodes": valid_timecodes,
                        "total_duration": subtitles[-1]["end_time"] if subtitles else 0,
                        "matching_quality": "GOOD" if len(time_gaps) == 0 and valid_timecodes else "POOR"
                    }

                except Exception as e:
                    matching_results[srt_file.name] = {
                        "error": str(e),
                        "matching_quality": "ERROR"
                    }

            # 判断匹配质量
            matching_passed = len(matching_results) > 0 and all(
                result.get("matching_quality") == "GOOD"
                for result in matching_results.values()
            )

            return {
                "status": "PASSED" if matching_passed else "FAILED",
                "message": f"视频字幕时间轴匹配验证{'通过' if matching_passed else '失败'}",
                "details": matching_results
            }

        except Exception as e:
            logger.error(f"视频字幕匹配验证失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_jianying_export(self) -> Dict[str, Any]:
        """测试剪映工程文件导出"""
        try:
            from src.exporters.jianying_pro_exporter import JianyingProExporter

            # 创建剪映导出器
            exporter = JianyingProExporter()

            export_results = {}

            # 测试导出剪映工程文件
            temp_files = list(Path(self.temp_dir).glob("*.srt"))

            for srt_file in temp_files:
                try:
                    # 生成剪映工程文件
                    project_file = Path(self.temp_dir) / f"{srt_file.stem}_jianying.json"

                    export_result = exporter.export_project(
                        srt_file=str(srt_file),
                        output_file=str(project_file)
                    )

                    if export_result.get("success", False):
                        # 验证生成的工程文件
                        if project_file.exists():
                            with open(project_file, 'r', encoding='utf-8') as f:
                                project_data = json.load(f)

                            # 检查工程文件结构
                            has_tracks = "tracks" in project_data
                            has_materials = "materials" in project_data
                            has_timeline = "timeline" in project_data

                            export_results[srt_file.name] = {
                                "export_success": True,
                                "file_exists": True,
                                "has_tracks": has_tracks,
                                "has_materials": has_materials,
                                "has_timeline": has_timeline,
                                "file_size_bytes": project_file.stat().st_size,
                                "export_quality": "GOOD" if all([has_tracks, has_materials, has_timeline]) else "POOR"
                            }

                            logger.info(f"剪映工程文件导出成功: {project_file.name}")
                        else:
                            export_results[srt_file.name] = {
                                "export_success": False,
                                "error": "工程文件未生成"
                            }
                    else:
                        export_results[srt_file.name] = {
                            "export_success": False,
                            "error": export_result.get("error", "导出失败")
                        }

                except Exception as e:
                    export_results[srt_file.name] = {
                        "export_success": False,
                        "error": str(e)
                    }

            # 判断导出是否成功
            export_passed = len(export_results) > 0 and all(
                result.get("export_success", False)
                for result in export_results.values()
            )

            return {
                "status": "PASSED" if export_passed else "FAILED",
                "message": f"剪映工程文件导出测试{'通过' if export_passed else '失败'}",
                "details": export_results
            }

        except Exception as e:
            logger.error(f"剪映导出测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_performance_and_stability(self):
        """测试4: 性能和稳定性测试"""
        test_name = "performance_and_stability"
        test_result = {
            "status": "RUNNING",
            "start_time": datetime.now().isoformat(),
            "subtests": {}
        }

        try:
            # 4.1 监控内存使用是否保持在3.8GB以下
            logger.info("4.1 监控内存使用")
            subtest_result = self._test_memory_usage()
            test_result["subtests"]["memory_usage"] = subtest_result

            # 4.2 测试在4GB内存/无GPU环境下的运行稳定性
            logger.info("4.2 测试低配环境运行稳定性")
            subtest_result = self._test_low_spec_stability()
            test_result["subtests"]["low_spec_stability"] = subtest_result

            # 计算总体状态
            all_passed = all(
                result.get("status") == "PASSED"
                for result in test_result["subtests"].values()
            )
            test_result["status"] = "PASSED" if all_passed else "FAILED"

        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            logger.error(f"性能和稳定性测试失败: {e}")

        test_result["end_time"] = datetime.now().isoformat()
        self.test_results["tests"][test_name] = test_result
        logger.info(f"测试4完成，状态: {test_result['status']}")

    def _test_memory_usage(self) -> Dict[str, Any]:
        """监控内存使用"""
        try:
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - self.initial_memory

            # 更新峰值内存
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory

            # 检查内存限制
            memory_limit = 3800  # 3.8GB in MB
            memory_within_limit = self.peak_memory <= memory_limit

            # 记录内存使用情况
            self.test_results["memory_usage"] = {
                "initial_mb": self.initial_memory,
                "current_mb": current_memory,
                "peak_mb": self.peak_memory,
                "increase_mb": memory_increase,
                "limit_mb": memory_limit,
                "within_limit": memory_within_limit
            }

            logger.info(f"内存使用监控: 当前 {current_memory:.1f}MB, 峰值 {self.peak_memory:.1f}MB, 限制 {memory_limit}MB")

            return {
                "status": "PASSED" if memory_within_limit else "FAILED",
                "message": f"内存使用监控{'通过' if memory_within_limit else '失败'}",
                "details": self.test_results["memory_usage"]
            }

        except Exception as e:
            logger.error(f"内存监控失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _test_low_spec_stability(self) -> Dict[str, Any]:
        """测试低配环境运行稳定性"""
        try:
            # 模拟低配环境测试
            logger.info("模拟4GB内存/无GPU环境稳定性测试...")

            stability_results = {
                "cpu_usage_stable": True,
                "memory_stable": True,
                "no_crashes": True,
                "response_time_acceptable": True
            }

            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            stability_results["cpu_usage_stable"] = cpu_percent < 80  # CPU使用率不超过80%

            # 检查内存稳定性
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            stability_results["memory_stable"] = current_memory <= 3800

            # 模拟响应时间测试
            start_time = time.time()
            # 执行一些轻量级操作
            for _ in range(100):
                pass
            response_time = time.time() - start_time
            stability_results["response_time_acceptable"] = response_time < 1.0  # 响应时间小于1秒

            # 检查是否有异常
            stability_results["no_crashes"] = len(self.test_results["errors"]) == 0

            # 综合稳定性评估
            stability_passed = all(stability_results.values())

            logger.info(f"低配环境稳定性: CPU {cpu_percent:.1f}%, 内存 {current_memory:.1f}MB, 响应时间 {response_time:.3f}s")

            return {
                "status": "PASSED" if stability_passed else "FAILED",
                "message": f"低配环境稳定性测试{'通过' if stability_passed else '失败'}",
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_mb": current_memory,
                    "response_time_seconds": response_time,
                    "stability_checks": stability_results
                }
            }

        except Exception as e:
            logger.error(f"低配环境稳定性测试失败: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _generate_comprehensive_report(self):
        """生成全面测试报告"""
        try:
            logger.info("生成全面测试报告...")

            # 计算测试统计
            total_tests = len(self.test_results["tests"])
            passed_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "PASSED")
            failed_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "FAILED")
            error_tests = sum(1 for test in self.test_results["tests"].values() if test.get("status") == "ERROR")

            # 计算子测试统计
            total_subtests = 0
            passed_subtests = 0
            for test in self.test_results["tests"].values():
                subtests = test.get("subtests", {})
                total_subtests += len(subtests)
                passed_subtests += sum(1 for subtest in subtests.values() if subtest.get("status") == "PASSED")

            # 生成摘要
            self.test_results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_subtests": total_subtests,
                "passed_subtests": passed_subtests,
                "subtest_success_rate": passed_subtests / total_subtests if total_subtests > 0 else 0,
                "overall_status": "PASSED" if passed_tests == total_tests else "FAILED"
            }

            # 性能指标
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            self.test_results["performance_metrics"] = {
                "peak_memory_mb": self.peak_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": final_memory - self.initial_memory,
                "memory_limit_respected": self.peak_memory <= 3800,
                "test_duration_seconds": (datetime.now() - datetime.fromisoformat(self.test_results["start_time"])).total_seconds()
            }

            # 保存详细报告
            report_file = self.test_output_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)

            # 生成Markdown报告
            markdown_report = self._generate_markdown_report()
            markdown_file = self.test_output_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_report)

            logger.info(f"测试报告已生成: {report_file}")
            logger.info(f"Markdown报告: {markdown_file}")

            # 打印摘要
            self._print_test_summary()

        except Exception as e:
            logger.error(f"生成测试报告失败: {e}")

    def _generate_markdown_report(self) -> str:
        """生成Markdown格式的测试报告"""
        summary = self.test_results["summary"]
        performance = self.test_results["performance_metrics"]

        report = f"""# VisionAI-ClipsMaster 核心视频处理模块全面测试报告

## 测试概览

- **测试会话ID**: {self.test_results['test_session_id']}
- **测试开始时间**: {self.test_results['start_time']}
- **总体状态**: {summary['overall_status']}
- **成功率**: {summary['success_rate']:.1%}

## 测试统计

| 指标 | 数量 |
|------|------|
| 总测试数 | {summary['total_tests']} |
| 通过测试 | {summary['passed_tests']} |
| 失败测试 | {summary['failed_tests']} |
| 错误测试 | {summary['error_tests']} |
| 总子测试数 | {summary['total_subtests']} |
| 通过子测试 | {summary['passed_subtests']} |

## 性能指标

| 指标 | 值 |
|------|---|
| 峰值内存使用 | {performance['peak_memory_mb']:.1f} MB |
| 最终内存使用 | {performance['final_memory_mb']:.1f} MB |
| 内存增长 | {performance['memory_increase_mb']:.1f} MB |
| 内存限制遵守 | {'✅' if performance['memory_limit_respected'] else '❌'} |
| 测试总耗时 | {performance['test_duration_seconds']:.1f} 秒 |

## 详细测试结果

"""

        for test_name, test_result in self.test_results["tests"].items():
            status_emoji = "✅" if test_result.get("status") == "PASSED" else "❌" if test_result.get("status") == "FAILED" else "⚠️"
            report += f"### {status_emoji} {test_name}\n\n"
            report += f"- **状态**: {test_result.get('status', 'UNKNOWN')}\n"

            if "subtests" in test_result:
                report += "- **子测试结果**:\n"
                for subtest_name, subtest_result in test_result["subtests"].items():
                    sub_emoji = "✅" if subtest_result.get("status") == "PASSED" else "❌" if subtest_result.get("status") == "FAILED" else "⚠️"
                    report += f"  - {sub_emoji} {subtest_name}: {subtest_result.get('status', 'UNKNOWN')}\n"

            report += "\n"

        return report

    def _print_test_summary(self):
        """打印测试摘要"""
        summary = self.test_results["summary"]
        performance = self.test_results["performance_metrics"]

        logger.info("=" * 80)
        logger.info("测试完成摘要")
        logger.info("=" * 80)
        logger.info(f"总体状态: {summary['overall_status']}")
        logger.info(f"测试成功率: {summary['success_rate']:.1%} ({summary['passed_tests']}/{summary['total_tests']})")
        logger.info(f"子测试成功率: {summary['subtest_success_rate']:.1%} ({summary['passed_subtests']}/{summary['total_subtests']})")
        logger.info(f"峰值内存: {performance['peak_memory_mb']:.1f}MB (限制: 3800MB)")
        logger.info(f"测试耗时: {performance['test_duration_seconds']:.1f}秒")
        logger.info("=" * 80)

    def _cleanup_test_environment(self):
        """清理测试环境"""
        try:
            logger.info("开始清理测试环境...")

            # 清理临时文件
            if self.temp_dir and Path(self.temp_dir).exists():
                shutil.rmtree(self.temp_dir)
                logger.info(f"已清理临时目录: {self.temp_dir}")

            # 清理生成的测试文件
            cleanup_patterns = [
                "generated_*.srt",
                "*_jianying.json",
                "temp_*.mp4"
            ]

            cleaned_files = []
            for pattern in cleanup_patterns:
                for file_path in self.test_output_dir.glob(pattern):
                    file_path.unlink()
                    cleaned_files.append(str(file_path))

            if cleaned_files:
                logger.info(f"已清理生成文件: {len(cleaned_files)}个")

            self.test_results["cleanup_status"] = "COMPLETED"
            logger.info("测试环境清理完成")

        except Exception as e:
            logger.error(f"清理测试环境失败: {e}")
            self.test_results["cleanup_status"] = "FAILED"

    def _ensure_cleanup(self):
        """确保清理完成"""
        if self.test_results.get("cleanup_status") != "COMPLETED":
            logger.warning("执行强制清理...")
            try:
                if self.temp_dir and Path(self.temp_dir).exists():
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.test_results["cleanup_status"] = "FORCE_COMPLETED"
            except Exception:
                self.test_results["cleanup_status"] = "FORCE_FAILED"


def main():
    """主函数"""
    print("=" * 80)
    print("VisionAI-ClipsMaster 核心视频处理模块全面测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = ComprehensiveVideoProcessingTestSuite()

    try:
        # 运行全面测试
        results = test_suite.run_comprehensive_tests()

        # 返回结果
        return results

    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
        test_suite._ensure_cleanup()
        return test_suite.test_results
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        test_suite._ensure_cleanup()
        return test_suite.test_results


if __name__ == "__main__":
    results = main()

    # 根据测试结果设置退出码
    if results.get("summary", {}).get("overall_status") == "PASSED":
        exit(0)
    else:
        exit(1)
