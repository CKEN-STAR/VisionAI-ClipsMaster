#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 短剧混剪AI工具

基于大模型的短剧混剪系统，可分析原片字幕，理解剧情，
重构更吸引人的叙事结构，生成新字幕，并据此拼接原片片段。

特点：
- 双模型架构：使用Qwen2.5-7B处理中文内容，Mistral-7B处理英文内容
- 自动语言检测：可根据字幕内容自动切换模型
- 低配置支持：针对4GB内存无独显设备优化
- 投喂训练：用户可提供"原片字幕+爆款混剪字幕"对进行训练
- 内存安全：内置内存泄漏检测和线程安全管理
"""

import os
import sys
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 导入核心组件
from src.core.language_detector import LanguageDetector
from src.core.model_loader import ModelLoader
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.clip_generator import ClipGenerator
from src.core.srt_parser import import_srt, export_srt
from src.core.device_id import get_device_id, get_device_info, save_device_report
from src.core.environment_manager import get_environment_manager, detect_current_environment, get_optimal_config, check_feature_availability

# 导入内存安全组件
from ui.utils.memory_leak_detector import start_memory_monitoring, stop_memory_monitoring, take_memory_snapshot, generate_memory_report
from ui.utils.thread_manager import ThreadTracker

# 设置日志
logging.basicConfig(
    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),
        logging.FileHandler("visionai_clips.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("VisionAI-ClipsMaster")

class VisionAIClipsMaster:
    """VisionAI-ClipsMaster主应用类"""
    
    def __init__(self):
        """初始化VisionAI-ClipsMaster应用"""
        # 检测运行环境
        self.env_manager = get_environment_manager()
        self.environment = self.env_manager.detect_environment()
        self.config = self.env_manager.get_optimal_config()
        
        logger.info(f"运行环境: {self.env_manager.get_device_summary()}")
        
        # 初始化线程跟踪器
        self.thread_tracker = ThreadTracker.get_instance()
        
        # 启动内存监控
        self._start_memory_monitoring()
        
        # 根据环境初始化组件
        self.language_detector = LanguageDetector()
        self.screenplay_engineer = ScreenplayEngineer(
            use_low_memory=self.config["models"]["use_low_memory"]
        )
        self.clip_generator = ClipGenerator(
            threads=self.config["performance"]["threads"],
            use_gpu=self.config["performance"]["use_gpu"]
        )
        self.model_loader = ModelLoader(
            preferred_model=self.config["models"]["preferred_model"],
            use_quantization=self.config["models"]["use_quantization"]
        )
        
        # 生成设备ID
        try:
            self.device_id = get_device_id()
            logger.info(f"设备ID: {self.device_id[:8]}...")
        except Exception as e:
            logger.warning(f"获取设备ID失败: {e}")
            self.device_id = None
        
        # 创建必要的目录
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # 检查功能可用性
        self._check_feature_availability()
        
        # 拍摄初始内存快照
        self.initial_memory_snapshot = take_memory_snapshot()
        
        logger.info("VisionAI-ClipsMaster初始化完成")
        
    def _start_memory_monitoring(self):
        """启动内存监控"""
        try:
            # 每60秒监控一次内存使用情况
            start_memory_monitoring(interval=60)
            logger.info("内存监控已启动，每60秒记录一次")
        except Exception as e:
            logger.warning(f"启动内存监控失败: {str(e)}")
            
    def __del__(self):
        """析构函数，确保资源正确释放"""
        try:
            # 停止内存监控
            stop_memory_monitoring()
            
            # 生成内存报告
            try:
                report = generate_memory_report()
                report_path = self.reports_dir / f"memory_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report)
                logger.info(f"内存使用报告已保存至: {report_path}")
            except Exception as e:
                logger.warning(f"生成内存报告失败: {str(e)}")
                
            # 清理所有线程
            self.thread_tracker.cleanup_all_threads()
            
        except Exception as e:
            logger.error(f"应用清理时出错: {str(e)}")
    
    def _check_feature_availability(self):
        """检查功能可用性并记录到日志"""
        for feature in ["4k_processing", "real_time_enhancement", "batch_processing"]:
            available, reason = self.env_manager.check_feature_availability(feature)
            if not available:
                logger.warning(f"功能受限: {feature} - {reason}")
    
    def process_video(self, video_path: str, subtitle_path: str, 
                      output_path: Optional[str] = None,
                      preset: Optional[str] = None) -> Dict[str, Any]:
        """处理视频和字幕，生成混剪"""
        try:
            # 检查是否可以处理4K视频
            if "4k" in video_path.lower() and not check_feature_availability("4k_processing"):
                logger.warning("检测到4K视频，但当前设备不完全支持4K处理，可能会导致性能下降")
                
            # 1. 检测字幕语言
            logger.info(f"正在检测字幕文件 {subtitle_path} 的语言...")
            language = self.language_detector.detect_subtitle_language(subtitle_path)
            logger.info(f"检测到语言: {language}")
            
            # 2. 根据语言选择适当的模型
            model_name = self.language_detector.get_model_for_language(language)
            logger.info(f"选择模型: {model_name}")
            
            # 3. 导入SRT字幕
            logger.info(f"正在导入字幕文件: {subtitle_path}")
            original_subtitles = self.screenplay_engineer.import_srt(subtitle_path)
            if not original_subtitles:
                logger.error(f"无法导入字幕文件: {subtitle_path}")
                return {"error": "无法导入字幕文件"}
            
            logger.info(f"成功导入字幕，共 {len(original_subtitles)} 条")
            
            # 4. 生成新的剧本
            logger.info("正在生成混剪剧本...")
            
            # 根据环境配置选择批处理大小
            batch_size = self.config["performance"]["batch_size"]
            
            result = self.screenplay_engineer.generate_screenplay(
                original_subtitles,
                language=language,
                preset_name=preset,
                batch_size=batch_size
            )
            
            if "error" in result:
                logger.error(f"生成剧本失败: {result['error']}")
                return result
            
            logger.info(f"成功生成剧本，共 {result['total_segments']} 条")
            
            # 5. 导出新的SRT文件
            if not output_path:
                output_name = Path(video_path).stem + "_remixed"
                output_video = self.output_dir / f"{output_name}.mp4"
                output_srt = self.output_dir / f"{output_name}.srt"
            else:
                output_video = Path(output_path)
                output_srt = output_video.with_suffix(".srt")
            
            logger.info(f"正在导出新字幕: {output_srt}")
            self.screenplay_engineer.export_srt(result["screenplay"], str(output_srt))
            
            # 6. 生成混剪视频
            logger.info(f"正在生成混剪视频: {output_video}")
            
            # 根据环境配置选择视频质量
            preview_quality = self.config["performance"]["preview_quality"]
            
            clip_result = self.clip_generator.generate_clips(
                video_path, 
                result["screenplay"],
                str(output_video),
                quality=preview_quality
            )
            
            if clip_result.get("status") != "success":
                logger.error(f"生成混剪视频失败: {clip_result.get('error')}")
                return {"error": clip_result.get("error")}
            
            logger.info(f"混剪视频生成成功: {output_video}")
            
            # 返回结果
            return {
                "status": "success",
                "video_path": str(output_video),
                "subtitle_path": str(output_srt),
                "segments_count": result["total_segments"],
                "language": language,
                "model": model_name,
                "device_id": self.device_id[:8] if self.device_id else "未知",
                "device_tier": self.env_manager.compatibility.get("device_tier", "未知"),
                "processing_time": clip_result.get("processing_time", 0),
                "environment": {
                    "ram": self.environment.get("ram", 0),
                    "cpu": self.environment.get("cpu", "Unknown"),
                    "gpu": self.environment.get("gpu", "Unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"处理视频时出错: {str(e)}")
            return {"error": str(e)}
    
    def train_model(self, original_srt_path: str, remix_srt_path: str) -> Dict[str, Any]:
        """投喂训练功能 - 使用原片字幕和混剪字幕对训练模型"""
        try:
            # 检测语言
            language = self.language_detector.detect_subtitle_language(original_srt_path)
            logger.info(f"检测到训练数据语言: {language}")
            
            # 加载字幕
            original_subtitles = self.screenplay_engineer.import_srt(original_srt_path)
            remix_subtitles = self.screenplay_engineer.import_srt(remix_srt_path)
            
            # TODO: 实现训练逻辑
            logger.info(f"正在训练模型，使用 {len(original_subtitles)} 条原片字幕和 {len(remix_subtitles)} 条混剪字幕")
            
            # 这里仅为演示，实际训练功能待实现
            time.sleep(2)  # 模拟训练过程
            
            return {
                "status": "success",
                "message": f"接收训练数据成功，数据ID: TRAIN_123456",
                "language": language,
                "pairs_count": 10,  # 示例值
                "device_id": self.device_id[:8] if self.device_id else "未知",
            }
            
        except Exception as e:
            logger.error(f"训练模型时出错: {str(e)}")
            return {"error": str(e)}
    
    def export_jianying_project(self, video_path: str, subtitle_path: str, 
                                output_path: Optional[str] = None) -> Dict[str, Any]:
        """导出剪映工程文件"""
        try:
            # 导入SRT字幕
            subtitles = self.screenplay_engineer.import_srt(subtitle_path)
            
            if not subtitles:
                return {"error": "无法导入字幕文件"}
            
            # 设置输出路径
            if not output_path:
                output_path = str(self.output_dir / f"{Path(video_path).stem}_jianying.zip")
            
            # 导出剪映工程
            result = self.clip_generator.export_jianying_project(subtitles, video_path, output_path)
            
            if result:
                return {
                    "status": "success",
                    "project_path": output_path,
                    "segments_count": len(subtitles),
                    "device_id": self.device_id[:8] if self.device_id else "未知",
                    "device_tier": self.env_manager.compatibility.get("device_tier", "未知")
                }
            else:
                return {"error": "导出剪映工程失败"}
            
        except Exception as e:
            logger.error(f"导出剪映工程时出错: {str(e)}")
            return {"error": str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息，包括设备ID和关键硬件参数"""
        try:
            # 获取设备详细信息
            device_info = get_device_info()
            
            # 提取关键信息
            system_info = {
                "device_id": self.device_id,
                "device_tier": self.env_manager.compatibility.get("device_tier", "未知"),
                "system": device_info.get("components", {}).get("system", {}),
                "cpu": device_info.get("components", {}).get("cpu", {}),
                "memory_total": self.environment.get("ram", 0),
                "gpu": self.environment.get("gpu", "未知"),
                "disk_info": device_info.get("components", {}).get("disk", {}),
                "optimal_config": self.config,
                "expected_performance": self.env_manager.get_expected_performance()
            }
            
            return system_info
            
        except Exception as e:
            logger.error(f"获取系统信息时出错: {str(e)}")
            return {"error": str(e)}
    
    def run_user_experience_test(self, test_type: str = "all") -> Dict[str, Any]:
        """运行用户体验测试

        Args:
            test_type: 测试类型，可选项：funnel（转化漏斗分析）、onboarding（新手引导测试）、
                      emotional（情感化设计测试）、cognitive（认知负荷测试）、all（所有测试）

        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            logger.info(f"正在运行用户体验测试: {test_type}")
            
            # 根据测试类型运行相应测试
            if test_type == "funnel" or test_type == "all":
                logger.info("正在运行用户反馈漏斗分析...")
                
                try:
                    # 动态导入模块
                    from tests.user_experience.funnel_analysis import analyze_conversion_funnel
                    
                    # 运行转化漏斗分析
                    funnel_results = analyze_conversion_funnel()
                    
                    logger.info(f"用户反馈漏斗分析完成: 生成到导出阶段转化率 {funnel_results.get('生成到导出', 0)}%")
                    return {
                        "status": "success", 
                        "test_type": test_type,
                        "results": {
                            "funnel": funnel_results
                        }
                    }
                except ImportError:
                    logger.error("无法导入转化漏斗分析模块，请确保安装了所有依赖")
                    return {"error": "无法导入转化漏斗分析模块，请确保安装了所有依赖"}
                except Exception as e:
                    logger.error(f"运行转化漏斗分析时出错: {str(e)}")
                    return {"error": f"转化漏斗分析失败: {str(e)}"}
            
            # 其他测试类型暂未实现
            elif test_type in ["onboarding", "emotional", "cognitive"]:
                logger.warning(f"测试类型 {test_type} 暂未实现")
                return {"status": "warning", "message": f"测试类型 {test_type} 暂未实现"}
            
            else:
                logger.error(f"未知的测试类型: {test_type}")
                return {"error": f"未知的测试类型: {test_type}"}
            
        except Exception as e:
            logger.error(f"运行用户体验测试时出错: {str(e)}")
            return {"error": str(e)}


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster - 短剧混剪AI工具")
    
    parser.add_argument("--video", "-v", type=str, help="输入视频文件路径")
    parser.add_argument("--subtitle", "-s", type=str, help="输入字幕文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出视频文件路径")
    parser.add_argument("--preset", "-p", type=str, choices=["快节奏", "情感化", "冲突型", "默认"], 
                        default="默认", help="混剪预设风格")
    parser.add_argument("--train", "-t", action="store_true", help="训练模式")
    parser.add_argument("--remix-subtitle", "-r", type=str, help="训练模式下的混剪字幕文件路径")
    parser.add_argument("--export-jianying", "-e", action="store_true", help="导出剪映工程")
    parser.add_argument("--device-info", "-d", action="store_true", help="显示设备信息")
    parser.add_argument("--save-device-report", type=str, help="保存设备报告到指定路径")
    parser.add_argument("--check-environment", "-c", action="store_true", help="检查环境兼容性")
    parser.add_argument("--memory-monitor", "-m", action="store_true", help="启动内存监控并生成报告")
    parser.add_argument("--memory-report", type=str, help="生成内存报告并保存到指定路径")
    parser.add_argument("--user-experience-test", "-u", type=str, 
                        choices=["funnel", "onboarding", "emotional", "cognitive", "all"],
                        help="运行用户体验测试")
    parser.add_argument("--hardware-benchmark", type=str, 
                       choices=["current", "scaling", "all"], 
                       help="运行硬件性能基准测试，'current'测试当前设备，'scaling'测试不同配置下的缩放性能，'all'运行所有测试")
    parser.add_argument("--quant-benchmark", type=str, 
                       choices=["current", "scaling", "all"], 
                       help="运行量化等级性能对比测试，'current'测试当前设备，'scaling'测试不同配置下的缩放性能，'all'运行所有测试")
    parser.add_argument("--lang-comparison", "-l", type=str,
                       choices=["Q2_K", "Q4_K_M", "Q5_K", "Q6_K", "Q8_0", "FP16"],
                       default="Q4_K_M",
                       help="运行中英文模型性能对比测试，可指定量化等级")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    app = VisionAIClipsMaster()
    
    # 设备信息模式
    if args.device_info:
        device_id = get_device_id()
        device_info = app.get_system_info()
        
        print("\n设备信息:")
        print("-" * 40)
        print(f"设备ID: {device_id}")
        print(f"设备等级: {device_info.get('device_tier', '未知')}")
        print(f"系统: {device_info.get('system', {}).get('platform', '未知')}")
        print(f"CPU: {device_info.get('cpu', {}).get('name', '未知')}")
        print(f"GPU: {device_info.get('gpu', '未知')}")
        print(f"内存: {device_info.get('memory_total', 0):.2f} GB")
        print(f"配置: {device_info.get('optimal_config', {}).get('models', {}).get('preferred_model', '未知')}")
        print("-" * 40)
        return 0
    
    # 检查环境兼容性
    if args.check_environment:
        env_manager = get_environment_manager()
        
        print("\n环境兼容性报告:")
        print("=" * 60)
        print(f"设备摘要: {env_manager.get_device_summary()}")
        
        compatibility = env_manager.compatibility
        if compatibility:
            tier = compatibility.get("device_tier", "未知")
            tier_names = {
                "entry": "入门级",
                "mid": "中端",
                "high": "高端",
                "premium": "顶级"
            }
            print(f"设备等级: {tier_names.get(tier, tier)}")
            
            print("\n功能支持状态:")
            features = [
                ("basic_processing", "基本视频处理"),
                ("4k_processing", "4K视频处理"),
                ("real_time_enhancement", "实时视频增强"),
                ("batch_processing", "批量处理"),
                ("multi_language", "多语言支持")
            ]
            
            for feature_id, feature_name in features:
                available, reason = env_manager.check_feature_availability(feature_id)
                status = "✅ 支持" if available else "❌ 不支持"
                print(f"- {feature_name}: {status} ({reason})")
        
            performance = env_manager.get_expected_performance()
            print("\n预期性能:")
            print(f"- 处理速度: {performance.get('processing_speed', '未知')}")
            print(f"- 最大分辨率: {performance.get('max_resolution', '未知')}")
        
            if compatibility.get("recommendations", []):
                print("\n优化建议:")
                for rec in compatibility["recommendations"]:
                    print(f"- {rec}")
        
        print("=" * 60)
        return 0
    
    # 保存设备报告
    if args.save_device_report:
        report_path = save_device_report(args.save_device_report)
        print(f"设备报告已保存到: {report_path}")
        return 0
    
    # 硬件基准测试
    if args.hardware_benchmark:
        try:
            # 导入硬件基准测试模块
            from tests.performance.hardware_benchmark import benchmark_device_performance, test_hardware_scaling
            
            print("\n===== 硬件性能基准测试 =====\n")
            
            if args.hardware_benchmark == "current" or args.hardware_benchmark == "all":
                print("\n1. 当前设备性能测试:\n")
                results = benchmark_device_performance()
                
                print(f"\n平均实时处理因子: {results['summary']['average_realtime_factor']:.2f}x")
                print(f"最大处理帧率: {results['summary']['max_fps']:.1f} FPS")
                
                # 判断设备性能等级
                avg_factor = results['summary']['average_realtime_factor']
                if avg_factor < 1.0:
                    tier = "低端 (低于实时处理)"
                elif avg_factor < 3.0:
                    tier = "中端 (1-3倍实时处理)"
                else:
                    tier = "高端 (3倍以上实时处理)"
                
                print(f"性能等级: {tier}")
            
            if args.hardware_benchmark == "scaling" or args.hardware_benchmark == "all":
                print("\n2. 硬件配置缩放测试:\n")
                results = test_hardware_scaling()
                
                print("\n性能缩放测试结果:")
                print("-" * 50)
                print(f"{'硬件配置':<20} {'处理时间(秒)':<15} {'实时因子':<10} {'结果':<10}")
                print("-" * 50)
                
                for name, result in results.items():
                    status = "✓ 通过" if result["meets_target"] else "✗ 未达标"
                    hw = result["hardware"]
                    print(f"{hw['cpu']:<20} {result['time']:<15.2f} {result['processing']['realtime_factor']:<10.2f} {status}")
            
            print("\n测试完成!")
            return 0
            
        except ImportError as e:
            print(f"硬件基准测试模块导入失败: {e}")
            return 1
    
    # 量化等级性能测试
    if args.quant_benchmark:
        try:
            # 导入量化基准测试模块
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from tests.performance.quantization_test import run_quant_benchmark
            
            print("\n===== 量化等级性能对比测试 =====\n")
            
            # 运行量化基准测试
            results = run_quant_benchmark()
            
            # 打印结果表格已在run_quant_benchmark内部实现
            
            print("\n测试完成!")
            return 0
            
        except ImportError as e:
            print(f"量化性能测试模块导入失败: {e}")
            print(f"请确保 tests/performance/quantization_test.py 文件存在")
            return 1
            
    # 内存监控模式
    if args.memory_monitor:
        try:
            # 启动内存监控
            print("\n===== 启动内存监控 =====\n")
            print("内存监控已启动，将在后台运行")
            print("请执行您的常规操作，监控将自动记录内存使用情况")
            print("完成后，使用 --memory-report 参数生成报告")
            
            # 已在应用初始化时启动了内存监控，这里不需要额外操作
            
            # 等待用户输入以结束监控
            input("\n按回车键停止监控并生成报告...")
            
            # 生成报告
            report = generate_memory_report()
            report_path = app.reports_dir / f"memory_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\n内存监控报告已保存至: {report_path}")
            return 0
            
        except Exception as e:
            print(f"内存监控失败: {e}")
            return 1
            
    # 生成内存报告
    if args.memory_report:
        try:
            # 生成报告
            report = generate_memory_report()
            
            # 保存报告
            report_path = args.memory_report
            if not report_path.endswith(".txt"):
                report_path += ".txt"
                
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            
            print(f"\n内存使用报告已保存至: {report_path}")
            return 0
            
        except Exception as e:
            print(f"生成内存报告失败: {e}")
            return 1
    
    # 中英文模型差异测试
    if args.lang_comparison:
        try:
            # 导入中英文模型对比测试模块
            from tests.run_language_test import run_language_comparison_test
            
            print("\n===== 中英文模型性能对比测试 =====\n")
            
            # 运行测试，使用指定的量化等级
            success = run_language_comparison_test(args.lang_comparison)
            
            if success:
                print("\n中英文模型性能对比测试完成，结果符合预期!")
            else:
                print("\n中英文模型性能对比测试完成，但结果不符合预期，请检查详细日志。")
            
            return 0 if success else 1
            
        except ImportError as e:
            print(f"中英文模型对比测试模块导入失败: {e}")
            print(f"请确保 tests/performance/lang_comparison.py 和 tests/run_language_test.py 文件存在")
            return 1
    
    # 用户体验测试
    if args.user_experience_test:
        result = app.run_user_experience_test(args.user_experience_test)
        
        if "error" in result:
            print(f"用户体验测试失败: {result['error']}")
            return 1
        
        print(f"用户体验测试完成: {args.user_experience_test}")
        return 0
    
    # 训练模式
    if args.train:
        if not args.subtitle or not args.remix_subtitle:
            print("错误: 训练模式需要同时提供原片字幕(--subtitle)和混剪字幕(--remix-subtitle)")
            return 1
        
        result = app.train_model(args.subtitle, args.remix_subtitle)
        
        if "error" in result:
            print(f"训练失败: {result['error']}")
            return 1
        
        print(f"训练数据收集成功: {result['message']}")
        return 0
    
    # 导出剪映工程
    elif args.export_jianying:
        if not args.video or not args.subtitle:
            print("错误: 导出剪映工程需要同时提供视频(--video)和字幕(--subtitle)")
            return 1
        
        result = app.export_jianying_project(args.video, args.subtitle, args.output)
        
        if "error" in result:
            print(f"导出剪映工程失败: {result['error']}")
            return 1
        
        print(f"剪映工程导出成功: {result['project_path']}")
        return 0
        
    # 默认模式：处理视频或显示帮助信息
    else:
        if not args.video or not args.subtitle:
            # 显示帮助信息
            print("\nVisionAI-ClipsMaster - 短剧混剪AI工具")
            print("===========================================")
            print("基本功能:")
            print("  --video, -v       - 输入视频文件路径")
            print("  --subtitle, -s    - 输入字幕文件路径")
            print("  --output, -o      - 输出视频文件路径")
            print("  --preset, -p      - 混剪预设风格")
            print("")
            print("内存与性能监控:")
            print("  --memory-monitor, -m  - 启动内存监控并生成报告")
            print("  --memory-report       - 生成内存报告并保存到指定路径")
            print("  --device-info, -d     - 显示设备信息")
            print("  --check-environment, -c - 检查环境兼容性")
            print("")
            print("性能测试:")
            print("  --hardware-benchmark  - 运行硬件性能基准测试")
            print("  --quant-benchmark     - 运行量化等级性能对比测试")
            print("  --lang-comparison, -l - 运行中英文模型性能对比测试")
            print("")
            print("示例:")
            print("  python app.py -v input.mp4 -s input.srt -o output.mp4")
            print("  python app.py --memory-monitor")
            print("  python app.py --memory-report memory_analysis.txt")
            print("  python app.py --device-info")
            return 1

        result = app.process_video(args.video, args.subtitle, args.output, args.preset)
        
        if "error" in result:
            print(f"处理失败: {result['error']}")
            return 1
        
        print(f"混剪视频生成成功: {result['video_path']}")
        print(f"混剪字幕保存至: {result['subtitle_path']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        return 0
        

if __name__ == "__main__":
    sys.exit(main())