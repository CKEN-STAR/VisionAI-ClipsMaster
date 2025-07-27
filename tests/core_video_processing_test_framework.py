#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 核心视频处理模块完整测试框架
实现视频-字幕映射精度验证、爆款SRT生成功能测试、端到端工作流验证等
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import tempfile
import shutil

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class CoreVideoProcessingTestFramework:
    """核心视频处理模块测试框架"""
    
    def __init__(self):
        self.test_start_time = datetime.now()
        self.test_results = {
            "framework_info": {
                "name": "VisionAI-ClipsMaster Core Video Processing Test",
                "version": "1.0.0",
                "start_time": self.test_start_time.isoformat(),
                "test_environment": self._get_environment_info()
            },
            "test_modules": {},
            "performance_metrics": {},
            "quality_assessments": {},
            "errors": [],
            "summary": {}
        }
        
        # 创建测试目录结构
        self.test_dir = project_root / "test_output" / "core_video_processing"
        self.test_data_dir = project_root / "test_data" / "core_processing"
        self.temp_dir = self.test_dir / "temp"
        
        self._setup_test_environment()
        self._setup_logging()
        
    def _get_environment_info(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
        }
    
    def _setup_test_environment(self):
        """设置测试环境"""
        # 创建测试目录
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.test_data_dir / "videos").mkdir(exist_ok=True)
        (self.test_data_dir / "subtitles").mkdir(exist_ok=True)
        (self.test_data_dir / "expected_outputs").mkdir(exist_ok=True)
        (self.test_dir / "reports").mkdir(exist_ok=True)
        (self.test_dir / "logs").mkdir(exist_ok=True)
        
    def _setup_logging(self):
        """设置日志系统"""
        log_file = self.test_dir / "logs" / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("核心视频处理测试框架初始化完成")
        
    def prepare_test_data(self):
        """准备测试数据"""
        self.logger.info("开始准备测试数据...")
        
        try:
            # 创建中文测试字幕
            self._create_chinese_test_subtitles()
            
            # 创建英文测试字幕
            self._create_english_test_subtitles()
            
            # 创建混合语言测试字幕
            self._create_mixed_language_subtitles()
            
            # 创建模拟视频文件信息
            self._create_mock_video_metadata()
            
            # 创建测试配置
            self._create_test_configurations()
            
            self.logger.info("测试数据准备完成")
            return True
            
        except Exception as e:
            self.logger.error(f"测试数据准备失败: {e}")
            self.test_results["errors"].append({
                "module": "data_preparation",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return False
    
    def _create_chinese_test_subtitles(self):
        """创建中文测试字幕"""
        chinese_original = """1
00:00:01,000 --> 00:00:05,000
这是一个关于爱情的故事，男主角是一个普通的上班族。

2
00:00:05,500 --> 00:00:10,000
女主角是一个独立自强的设计师，两人在咖啡厅相遇。

3
00:00:10,500 --> 00:00:15,000
他们开始了一段美好的恋情，但是面临着各种挑战。

4
00:00:15,500 --> 00:00:20,000
男主角的前女友突然回国，带来了意想不到的麻烦。

5
00:00:20,500 --> 00:00:25,000
女主角开始怀疑男主角的真心，两人关系出现裂痕。

6
00:00:25,500 --> 00:00:30,000
经过一系列的误会和解释，他们最终重归于好。

7
00:00:30,500 --> 00:00:35,000
故事的结局是两人决定结婚，过上幸福的生活。"""

        chinese_viral = """1
00:00:01,000 --> 00:00:03,000
爱情来得太突然！上班族遇见独立女设计师

2
00:00:05,500 --> 00:00:08,000
咖啡厅偶遇，一见钟情的浪漫开始了

3
00:00:15,500 --> 00:00:18,000
前女友回国！三角恋情即将爆发

4
00:00:20,500 --> 00:00:23,000
信任危机！女主开始怀疑男主的真心

5
00:00:30,500 --> 00:00:33,000
真相大白！误会解除，爱情重燃

6
00:00:33,500 --> 00:00:35,000
完美结局：求婚成功，幸福美满！"""

        # 保存文件
        with open(self.test_data_dir / "subtitles" / "chinese_original.srt", 'w', encoding='utf-8') as f:
            f.write(chinese_original)
            
        with open(self.test_data_dir / "subtitles" / "chinese_viral.srt", 'w', encoding='utf-8') as f:
            f.write(chinese_viral)
    
    def _create_english_test_subtitles(self):
        """创建英文测试字幕"""
        english_original = """1
00:00:01,000 --> 00:00:05,000
This is a story about love. The male protagonist is an ordinary office worker.

2
00:00:05,500 --> 00:00:10,000
The female protagonist is an independent designer. They meet at a coffee shop.

3
00:00:10,500 --> 00:00:15,000
They begin a beautiful romance, but face various challenges.

4
00:00:15,500 --> 00:00:20,000
The male protagonist's ex-girlfriend suddenly returns, bringing unexpected trouble.

5
00:00:20,500 --> 00:00:25,000
The female protagonist begins to doubt the male protagonist's sincerity.

6
00:00:25,500 --> 00:00:30,000
After a series of misunderstandings and explanations, they reconcile.

7
00:00:30,500 --> 00:00:35,000
The story ends with them deciding to marry and live happily."""

        english_viral = """1
00:00:01,000 --> 00:00:03,000
Love strikes suddenly! Office worker meets independent designer

2
00:00:05,500 --> 00:00:08,000
Coffee shop encounter - love at first sight begins!

3
00:00:15,500 --> 00:00:18,000
Ex-girlfriend returns! Love triangle about to explode

4
00:00:20,500 --> 00:00:23,000
Trust crisis! She doubts his true feelings

5
00:00:30,500 --> 00:00:33,000
Truth revealed! Misunderstanding cleared, love rekindled

6
00:00:33,500 --> 00:00:35,000
Perfect ending: Proposal accepted, happily ever after!"""

        # 保存文件
        with open(self.test_data_dir / "subtitles" / "english_original.srt", 'w', encoding='utf-8') as f:
            f.write(english_original)
            
        with open(self.test_data_dir / "subtitles" / "english_viral.srt", 'w', encoding='utf-8') as f:
            f.write(english_viral)
    
    def _create_mixed_language_subtitles(self):
        """创建混合语言测试字幕"""
        mixed_content = """1
00:00:01,000 --> 00:00:05,000
这是一个love story，男主角是一个ordinary office worker。

2
00:00:05,500 --> 00:00:10,000
女主角是independent designer，他们在coffee shop相遇。

3
00:00:10,500 --> 00:00:15,000
Beautiful romance开始了，但是face various challenges。"""

        with open(self.test_data_dir / "subtitles" / "mixed_language.srt", 'w', encoding='utf-8') as f:
            f.write(mixed_content)
    
    def _create_mock_video_metadata(self):
        """创建模拟视频元数据"""
        video_metadata = {
            "test_video_1.mp4": {
                "duration": 35.0,
                "fps": 25.0,
                "resolution": "1920x1080",
                "format": "mp4",
                "size_mb": 50.2
            },
            "test_video_2.avi": {
                "duration": 35.0,
                "fps": 30.0,
                "resolution": "1280x720",
                "format": "avi",
                "size_mb": 45.8
            },
            "test_video_3.flv": {
                "duration": 35.0,
                "fps": 24.0,
                "resolution": "854x480",
                "format": "flv",
                "size_mb": 25.3
            }
        }
        
        with open(self.test_data_dir / "videos" / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(video_metadata, f, indent=2, ensure_ascii=False)
    
    def _create_test_configurations(self):
        """创建测试配置"""
        test_config = {
            "alignment_precision_threshold": 0.5,  # 时间轴对齐精度阈值（秒）
            "memory_limit_gb": 4.0,  # 内存限制
            "model_switch_timeout": 1.5,  # 模型切换超时（秒）
            "supported_video_formats": ["mp4", "avi", "flv"],
            "supported_subtitle_formats": ["srt"],
            "test_scenarios": {
                "basic_alignment": True,
                "multi_format_compatibility": True,
                "language_detection": True,
                "screenplay_reconstruction": True,
                "end_to_end_workflow": True,
                "performance_benchmarks": True
            }
        }
        
        with open(self.test_data_dir / "test_config.json", 'w', encoding='utf-8') as f:
            json.dump(test_config, f, indent=2, ensure_ascii=False)
        
        self.test_config = test_config

    def run_comprehensive_tests(self):
        """运行完整的测试套件"""
        self.logger.info("开始运行VisionAI-ClipsMaster完整测试套件...")

        try:
            # 导入测试模块
            from test_alignment_precision import AlignmentPrecisionTester
            from test_viral_srt_generation import ViralSRTGenerationTester
            from test_system_integration import SystemIntegrationTester

            # 1. 视频-字幕映射精度验证
            self.logger.info("=" * 60)
            self.logger.info("1. 开始视频-字幕映射精度验证测试")
            alignment_tester = AlignmentPrecisionTester(self)
            alignment_results = alignment_tester.run_all_tests()
            self.test_results["test_modules"]["alignment_precision"] = alignment_results

            # 2. AI剧本重构功能测试
            self.logger.info("=" * 60)
            self.logger.info("2. 开始AI剧本重构功能测试")
            viral_tester = ViralSRTGenerationTester(self)
            viral_results = viral_tester.run_all_tests()
            self.test_results["test_modules"]["viral_srt_generation"] = viral_results

            # 3. 端到端工作流验证
            self.logger.info("=" * 60)
            self.logger.info("3. 开始端到端工作流验证测试")
            integration_tester = SystemIntegrationTester(self)
            integration_results = integration_tester.run_all_tests()
            self.test_results["test_modules"]["system_integration"] = integration_results

            # 4. 生成综合测试报告
            self._generate_comprehensive_report()

            # 5. 清理测试环境
            self._cleanup_test_environment()

            self.logger.info("=" * 60)
            self.logger.info("✅ VisionAI-ClipsMaster完整测试套件执行完成")

            return self.test_results

        except Exception as e:
            self.logger.error(f"测试套件执行失败: {e}")
            self.test_results["errors"].append({
                "module": "comprehensive_test_suite",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return self.test_results

    def _generate_comprehensive_report(self):
        """生成综合测试报告"""
        self.logger.info("生成综合测试报告...")

        # 计算总体统计
        total_modules = len(self.test_results["test_modules"])
        successful_modules = 0
        total_test_cases = 0
        passed_test_cases = 0

        for module_name, module_results in self.test_results["test_modules"].items():
            if module_results.get("test_cases"):
                total_test_cases += len(module_results["test_cases"])
                passed_test_cases += sum(1 for tc in module_results["test_cases"]
                                       if tc.get("status") in ["completed", "passed"])

            # 检查模块是否成功
            if not module_results.get("errors"):
                successful_modules += 1

        # 生成性能指标
        self.test_results["performance_metrics"] = {
            "total_execution_time": (datetime.now() - self.test_start_time).total_seconds(),
            "modules_tested": total_modules,
            "successful_modules": successful_modules,
            "module_success_rate": successful_modules / total_modules if total_modules > 0 else 0,
            "total_test_cases": total_test_cases,
            "passed_test_cases": passed_test_cases,
            "test_case_success_rate": passed_test_cases / total_test_cases if total_test_cases > 0 else 0
        }

        # 生成质量评估
        self.test_results["quality_assessments"] = {
            "alignment_precision_score": self._extract_metric("alignment_precision", "precision_metrics", "success_rate", 0),
            "viral_generation_score": self._extract_metric("viral_srt_generation", "generation_metrics", "success_rate", 0),
            "integration_workflow_score": self._extract_metric("system_integration", "workflow_metrics", "success_rate", 0),
            "overall_system_quality": 0
        }

        # 计算总体质量评分
        quality_scores = [
            self.test_results["quality_assessments"]["alignment_precision_score"],
            self.test_results["quality_assessments"]["viral_generation_score"],
            self.test_results["quality_assessments"]["integration_workflow_score"]
        ]
        valid_scores = [score for score in quality_scores if score > 0]
        self.test_results["quality_assessments"]["overall_system_quality"] = (
            sum(valid_scores) / len(valid_scores) if valid_scores else 0
        )

        # 生成总结
        self.test_results["summary"] = {
            "test_execution_status": "completed" if successful_modules == total_modules else "partial_failure",
            "critical_issues": len(self.test_results["errors"]),
            "performance_rating": self._calculate_performance_rating(),
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }

        # 保存详细报告
        self._save_detailed_report()

    def _extract_metric(self, module_name: str, metric_category: str, metric_name: str, default_value: Any) -> Any:
        """从测试结果中提取指标"""
        try:
            return self.test_results["test_modules"][module_name][metric_category][metric_name]
        except (KeyError, TypeError):
            return default_value

    def _calculate_performance_rating(self) -> str:
        """计算性能评级"""
        overall_quality = self.test_results["quality_assessments"]["overall_system_quality"]

        if overall_quality >= 0.9:
            return "优秀 (A)"
        elif overall_quality >= 0.8:
            return "良好 (B)"
        elif overall_quality >= 0.7:
            return "合格 (C)"
        elif overall_quality >= 0.6:
            return "需改进 (D)"
        else:
            return "不合格 (F)"

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        alignment_score = self.test_results["quality_assessments"]["alignment_precision_score"]
        if alignment_score < 0.8:
            recommendations.append("建议优化视频-字幕对齐算法，提高时间轴精度")

        viral_score = self.test_results["quality_assessments"]["viral_generation_score"]
        if viral_score < 0.8:
            recommendations.append("建议改进AI剧本重构模型，提升爆款特征识别能力")

        integration_score = self.test_results["quality_assessments"]["integration_workflow_score"]
        if integration_score < 0.8:
            recommendations.append("建议优化系统集成流程，提高端到端工作流稳定性")

        if len(self.test_results["errors"]) > 0:
            recommendations.append("建议修复测试过程中发现的错误和异常")

        if not recommendations:
            recommendations.append("系统整体表现良好，建议继续保持当前质量水平")

        return recommendations

    def _generate_next_steps(self) -> List[str]:
        """生成后续步骤"""
        next_steps = [
            "1. 审查测试报告中的详细结果和指标",
            "2. 根据建议优化相应的系统模块",
            "3. 在真实环境中进行用户验收测试",
            "4. 准备生产环境部署配置",
            "5. 建立持续集成和监控机制"
        ]

        return next_steps

    def _save_detailed_report(self):
        """保存详细测试报告"""
        report_file = self.test_dir / "reports" / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"详细测试报告已保存: {report_file}")

        # 生成简化的HTML报告
        self._generate_html_report(report_file.with_suffix('.html'))

    def _generate_html_report(self, html_file: Path):
        """生成HTML格式的测试报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007acc; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007acc; }}
        .metric-label {{ color: #666; font-size: 14px; }}
        .status-passed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
        .status-warning {{ color: #ffc107; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .recommendations {{ background: #e7f3ff; padding: 15px; border-radius: 6px; border-left: 4px solid #007acc; }}
        .recommendations ul {{ margin: 10px 0; padding-left: 20px; }}
        .test-module {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 6px; }}
        .test-module h3 {{ margin-top: 0; color: #007acc; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>VisionAI-ClipsMaster 综合测试报告</h1>
            <p>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>测试版本: {self.test_results['framework_info']['version']}</p>
        </div>

        <div class="section">
            <h2>📊 总体指标</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{self.test_results['performance_metrics']['module_success_rate']:.1%}</div>
                    <div class="metric-label">模块成功率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{self.test_results['performance_metrics']['test_case_success_rate']:.1%}</div>
                    <div class="metric-label">测试用例通过率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{self.test_results['quality_assessments']['overall_system_quality']:.1%}</div>
                    <div class="metric-label">系统整体质量</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{self.test_results['summary']['performance_rating']}</div>
                    <div class="metric-label">性能评级</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🔍 测试模块详情</h2>
            <div class="test-module">
                <h3>1. 视频-字幕映射精度验证</h3>
                <p>精度评分: <span class="metric-value">{self.test_results['quality_assessments']['alignment_precision_score']:.1%}</span></p>
                <p>状态: <span class="{'status-passed' if self.test_results['quality_assessments']['alignment_precision_score'] >= 0.8 else 'status-warning'}">
                    {'✅ 通过' if self.test_results['quality_assessments']['alignment_precision_score'] >= 0.8 else '⚠️ 需优化'}
                </span></p>
            </div>

            <div class="test-module">
                <h3>2. AI剧本重构功能</h3>
                <p>生成质量评分: <span class="metric-value">{self.test_results['quality_assessments']['viral_generation_score']:.1%}</span></p>
                <p>状态: <span class="{'status-passed' if self.test_results['quality_assessments']['viral_generation_score'] >= 0.8 else 'status-warning'}">
                    {'✅ 通过' if self.test_results['quality_assessments']['viral_generation_score'] >= 0.8 else '⚠️ 需优化'}
                </span></p>
            </div>

            <div class="test-module">
                <h3>3. 端到端工作流集成</h3>
                <p>集成评分: <span class="metric-value">{self.test_results['quality_assessments']['integration_workflow_score']:.1%}</span></p>
                <p>状态: <span class="{'status-passed' if self.test_results['quality_assessments']['integration_workflow_score'] >= 0.8 else 'status-warning'}">
                    {'✅ 通过' if self.test_results['quality_assessments']['integration_workflow_score'] >= 0.8 else '⚠️ 需优化'}
                </span></p>
            </div>
        </div>

        <div class="section">
            <h2>💡 改进建议</h2>
            <div class="recommendations">
                <ul>
                    {''.join(f'<li>{rec}</li>' for rec in self.test_results['summary']['recommendations'])}
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>📋 后续步骤</h2>
            <div class="recommendations">
                <ol>
                    {''.join(f'<li>{step}</li>' for step in self.test_results['summary']['next_steps'])}
                </ol>
            </div>
        </div>

        <div class="section">
            <h2>🔧 环境信息</h2>
            <p><strong>平台:</strong> {self.test_results['framework_info']['test_environment']['platform']}</p>
            <p><strong>Python版本:</strong> {self.test_results['framework_info']['test_environment']['python_version']}</p>
            <p><strong>CPU核心数:</strong> {self.test_results['framework_info']['test_environment']['cpu_count']}</p>
            <p><strong>总内存:</strong> {self.test_results['framework_info']['test_environment']['memory_total_gb']} GB</p>
            <p><strong>可用内存:</strong> {self.test_results['framework_info']['test_environment']['memory_available_gb']} GB</p>
        </div>
    </div>
</body>
</html>
        """

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"HTML测试报告已生成: {html_file}")

    def _cleanup_test_environment(self):
        """清理测试环境"""
        self.logger.info("开始清理测试环境...")

        try:
            # 清理临时文件
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.logger.info("✅ 临时文件清理完成")

            # 清理生成的测试视频文件
            output_dir = self.test_dir / "output"
            if output_dir.exists():
                for file in output_dir.glob("test_*.mp4"):
                    file.unlink()
                self.logger.info("✅ 测试视频文件清理完成")

            # 清理模型缓存（如果存在）
            cache_dir = project_root / "models" / "cache"
            if cache_dir.exists():
                for file in cache_dir.glob("test_*.cache"):
                    file.unlink()
                self.logger.info("✅ 模型缓存清理完成")

            # 重置日志文件大小（保留最新的日志）
            log_dir = self.test_dir / "logs"
            if log_dir.exists():
                log_files = sorted(log_dir.glob("test_*.log"), key=lambda x: x.stat().st_mtime)
                # 保留最新的3个日志文件
                for old_log in log_files[:-3]:
                    old_log.unlink()
                self.logger.info("✅ 历史日志清理完成")

            self.logger.info("🧹 测试环境清理完成")

        except Exception as e:
            self.logger.warning(f"测试环境清理时出现警告: {e}")

if __name__ == "__main__":
    # 初始化测试框架
    framework = CoreVideoProcessingTestFramework()

    # 准备测试数据
    if framework.prepare_test_data():
        print("✅ 测试环境初始化完成")
        print(f"📁 测试目录: {framework.test_dir}")
        print(f"📁 测试数据目录: {framework.test_data_dir}")

        # 运行完整测试套件
        print("\n🚀 开始执行完整测试套件...")
        test_results = framework.run_comprehensive_tests()

        # 显示测试结果摘要
        print("\n" + "="*60)
        print("📊 测试结果摘要")
        print("="*60)
        print(f"模块成功率: {test_results['performance_metrics']['module_success_rate']:.1%}")
        print(f"测试用例通过率: {test_results['performance_metrics']['test_case_success_rate']:.1%}")
        print(f"系统整体质量: {test_results['quality_assessments']['overall_system_quality']:.1%}")
        print(f"性能评级: {test_results['summary']['performance_rating']}")
        print(f"执行时间: {test_results['performance_metrics']['total_execution_time']:.1f} 秒")

        if test_results['summary']['test_execution_status'] == 'completed':
            print("\n🎉 所有测试模块执行成功！")
        else:
            print(f"\n⚠️ 测试执行完成，但有 {test_results['summary']['critical_issues']} 个关键问题需要关注")

        print(f"\n📄 详细报告已保存到: {framework.test_dir / 'reports'}")

    else:
        print("❌ 测试环境初始化失败")
        sys.exit(1)
