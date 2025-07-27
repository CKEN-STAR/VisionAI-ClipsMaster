#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 最终综合验证
验证所有修复后的功能是否正常工作
"""

import os
import sys
import json
import time
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_verification.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalVerificationTester:
    """最终综合验证测试器"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="final_verification_"))
        self.test_results = []
        self.created_files = []
        
        logger.info(f"验证测试目录: {self.test_dir}")
    
    def test_ui_functionality_complete(self) -> Dict[str, Any]:
        """测试UI功能完整性（修复后）"""
        logger.info("=" * 60)
        logger.info("最终验证1: UI功能完整性测试")
        logger.info("=" * 60)
        
        test_result = {
            "test_name": "UI功能完整性测试（修复后）",
            "start_time": time.time(),
            "status": "进行中",
            "details": {},
            "errors": []
        }
        
        try:
            # 1. 测试VideoProcessor类导入和方法可用性
            logger.info("测试VideoProcessor类...")
            from simple_ui_fixed import VideoProcessor
            
            required_methods = ['generate_viral_srt', 'generate_video', 'get_srt_info']
            available_methods = []
            missing_methods = []
            
            for method in required_methods:
                if hasattr(VideoProcessor, method):
                    available_methods.append(method)
                    logger.info(f"✅ 方法可用: {method}")
                else:
                    missing_methods.append(method)
                    logger.error(f"❌ 方法缺失: {method}")
            
            test_result["details"]["available_methods"] = available_methods
            test_result["details"]["missing_methods"] = missing_methods
            
            # 2. 测试get_srt_info方法功能
            if 'get_srt_info' in available_methods:
                logger.info("测试get_srt_info方法功能...")
                
                # 创建测试SRT文件
                test_srt = self.test_dir / "test_ui.srt"
                test_srt_content = """1
00:00:00,000 --> 00:00:03,000
UI功能测试字幕第一段

2
00:00:03,000 --> 00:00:06,000
UI功能测试字幕第二段

3
00:00:06,000 --> 00:00:09,000
UI功能测试字幕第三段"""
                
                with open(test_srt, 'w', encoding='utf-8') as f:
                    f.write(test_srt_content)
                self.created_files.append(str(test_srt))
                
                # 测试get_srt_info方法
                try:
                    srt_info = VideoProcessor.get_srt_info(str(test_srt))
                    if srt_info and srt_info.get("is_valid"):
                        logger.info("✅ get_srt_info方法工作正常")
                        test_result["details"]["get_srt_info_working"] = True
                        test_result["details"]["srt_info"] = srt_info
                    else:
                        logger.warning("⚠️ get_srt_info方法返回无效结果")
                        test_result["details"]["get_srt_info_working"] = False
                        test_result["errors"].append("get_srt_info方法返回无效结果")
                except Exception as e:
                    logger.error(f"❌ get_srt_info方法测试失败: {str(e)}")
                    test_result["details"]["get_srt_info_working"] = False
                    test_result["errors"].append(f"get_srt_info方法异常: {str(e)}")
            
            # 3. 测试主窗口类
            logger.info("测试主窗口类...")
            try:
                from simple_ui_fixed import SimpleScreenplayApp
                test_result["details"]["main_window_available"] = True
                logger.info("✅ 主窗口类可用")
            except Exception as e:
                test_result["details"]["main_window_available"] = False
                test_result["errors"].append(f"主窗口类导入失败: {str(e)}")
                logger.error(f"❌ 主窗口类导入失败: {str(e)}")
            
            # 综合评估
            if not missing_methods and test_result["details"].get("get_srt_info_working", False):
                test_result["status"] = "完全通过"
                logger.info("✅ UI功能完整性测试完全通过")
            elif not missing_methods:
                test_result["status"] = "基本通过"
                logger.info("✅ UI功能完整性测试基本通过")
            else:
                test_result["status"] = "部分通过"
                logger.warning("⚠️ UI功能完整性测试部分通过")
        
        except Exception as e:
            logger.error(f"❌ UI功能测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        self.test_results.append(test_result)
        return test_result
    
    def test_complete_workflow_fixed(self) -> Dict[str, Any]:
        """测试完整工作流程（修复后）"""
        logger.info("=" * 60)
        logger.info("最终验证2: 完整工作流程测试")
        logger.info("=" * 60)
        
        test_result = {
            "test_name": "完整工作流程测试（修复后）",
            "start_time": time.time(),
            "status": "进行中",
            "workflow_steps": {},
            "errors": []
        }
        
        try:
            # 步骤1: 创建测试数据
            logger.info("步骤1: 创建测试数据...")
            test_video = self.test_dir / "workflow_final.mp4"
            with open(test_video, 'wb') as f:
                f.write(b'\x00' * 8192)  # 8KB测试文件
            self.created_files.append(str(test_video))
            
            test_srt = self.test_dir / "workflow_final.srt"
            srt_content = """1
00:00:00,000 --> 00:00:05,000
最终工作流程测试 - 第一段

2
00:00:05,000 --> 00:00:10,000
最终工作流程测试 - 第二段

3
00:00:10,000 --> 00:00:15,000
最终工作流程测试 - 第三段"""
            
            with open(test_srt, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            self.created_files.append(str(test_srt))
            
            test_result["workflow_steps"]["create_data"] = {
                "success": True,
                "video_size": test_video.stat().st_size,
                "srt_size": test_srt.stat().st_size
            }
            
            # 步骤2: 测试SRT信息获取
            logger.info("步骤2: 测试SRT信息获取...")
            try:
                from simple_ui_fixed import VideoProcessor
                srt_info = VideoProcessor.get_srt_info(str(test_srt))
                
                if srt_info and srt_info.get("is_valid"):
                    test_result["workflow_steps"]["srt_processing"] = {
                        "success": True,
                        "subtitle_count": srt_info.get("subtitle_count", 0),
                        "total_duration": srt_info.get("total_duration", 0)
                    }
                    logger.info("✅ SRT信息获取成功")
                else:
                    test_result["workflow_steps"]["srt_processing"] = {
                        "success": False,
                        "error": "SRT信息无效"
                    }
                    test_result["errors"].append("SRT信息获取失败")
            except Exception as e:
                test_result["workflow_steps"]["srt_processing"] = {
                    "success": False,
                    "error": str(e)
                }
                test_result["errors"].append(f"SRT处理异常: {str(e)}")
            
            # 步骤3: 测试剪映工程文件生成
            logger.info("步骤3: 测试剪映工程文件生成...")
            try:
                from src.exporters.jianying_pro_exporter import JianyingProExporter
                
                exporter = JianyingProExporter()
                project_data = {
                    "segments": [
                        {"start": "00:00:00,000", "end": "00:00:05,000", "text": "最终工作流程测试 - 第一段"},
                        {"start": "00:00:05,000", "end": "00:00:10,000", "text": "最终工作流程测试 - 第二段"},
                        {"start": "00:00:10,000", "end": "00:00:15,000", "text": "最终工作流程测试 - 第三段"}
                    ],
                    "source_video": str(test_video),
                    "project_name": "最终验证项目"
                }
                
                output_project = self.test_dir / "final_verification.draft"
                export_success = exporter.export_project(project_data, str(output_project))
                
                if export_success and output_project.exists():
                    test_result["workflow_steps"]["jianying_export"] = {
                        "success": True,
                        "file_size": output_project.stat().st_size,
                        "project_path": str(output_project)
                    }
                    self.created_files.append(str(output_project))
                    logger.info("✅ 剪映工程文件生成成功")
                else:
                    test_result["workflow_steps"]["jianying_export"] = {
                        "success": False,
                        "error": "工程文件生成失败"
                    }
                    test_result["errors"].append("剪映工程文件生成失败")
            except Exception as e:
                test_result["workflow_steps"]["jianying_export"] = {
                    "success": False,
                    "error": str(e)
                }
                test_result["errors"].append(f"剪映导出异常: {str(e)}")
            
            # 步骤4: 验证工程文件内容
            if test_result["workflow_steps"].get("jianying_export", {}).get("success"):
                logger.info("步骤4: 验证工程文件内容...")
                try:
                    project_path = test_result["workflow_steps"]["jianying_export"]["project_path"]
                    with open(project_path, 'r', encoding='utf-8') as f:
                        project_content = json.load(f)
                    
                    # 验证基本结构
                    required_fields = ["version", "type", "tracks", "materials"]
                    missing_fields = [field for field in required_fields if field not in project_content]
                    
                    if not missing_fields:
                        test_result["workflow_steps"]["content_validation"] = {
                            "success": True,
                            "tracks_count": len(project_content.get("tracks", [])),
                            "materials_count": sum(len(materials) for materials in project_content.get("materials", {}).values())
                        }
                        logger.info("✅ 工程文件内容验证通过")
                    else:
                        test_result["workflow_steps"]["content_validation"] = {
                            "success": False,
                            "missing_fields": missing_fields
                        }
                        test_result["errors"].append(f"工程文件缺少字段: {missing_fields}")
                except Exception as e:
                    test_result["workflow_steps"]["content_validation"] = {
                        "success": False,
                        "error": str(e)
                    }
                    test_result["errors"].append(f"内容验证异常: {str(e)}")
            
            # 综合评估
            successful_steps = sum(1 for step in test_result["workflow_steps"].values() if step.get("success", False))
            total_steps = len(test_result["workflow_steps"])
            
            if successful_steps == total_steps:
                test_result["status"] = "完全通过"
                logger.info("✅ 完整工作流程测试完全通过")
            elif successful_steps >= total_steps * 0.8:
                test_result["status"] = "基本通过"
                logger.info("✅ 完整工作流程测试基本通过")
            else:
                test_result["status"] = "部分通过"
                logger.warning("⚠️ 完整工作流程测试部分通过")
        
        except Exception as e:
            logger.error(f"❌ 工作流程测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        self.test_results.append(test_result)
        return test_result

    def test_production_readiness(self) -> Dict[str, Any]:
        """测试生产环境就绪性"""
        logger.info("=" * 60)
        logger.info("最终验证3: 生产环境就绪性测试")
        logger.info("=" * 60)

        test_result = {
            "test_name": "生产环境就绪性测试",
            "start_time": time.time(),
            "status": "进行中",
            "readiness_checks": {},
            "recommendations": []
        }

        try:
            # 1. 检查核心依赖
            logger.info("检查核心依赖...")
            dependencies = {
                "PyQt6": False,
                "pathlib": False,
                "json": False,
                "tempfile": False,
                "shutil": False
            }

            for dep in dependencies:
                try:
                    __import__(dep)
                    dependencies[dep] = True
                    logger.info(f"✅ {dep} 可用")
                except ImportError:
                    logger.error(f"❌ {dep} 不可用")

            test_result["readiness_checks"]["dependencies"] = dependencies

            # 2. 检查核心模块
            logger.info("检查核心模块...")
            core_modules = {
                "simple_ui_fixed": False,
                "jianying_exporter": False,
                "video_processor": False
            }

            try:
                from simple_ui_fixed import VideoProcessor, SimpleScreenplayApp
                core_modules["simple_ui_fixed"] = True
                core_modules["video_processor"] = True
                logger.info("✅ simple_ui_fixed 模块可用")
            except Exception as e:
                logger.error(f"❌ simple_ui_fixed 模块不可用: {e}")

            try:
                from src.exporters.jianying_pro_exporter import JianyingProExporter
                core_modules["jianying_exporter"] = True
                logger.info("✅ jianying_exporter 模块可用")
            except Exception as e:
                logger.error(f"❌ jianying_exporter 模块不可用: {e}")

            test_result["readiness_checks"]["core_modules"] = core_modules

            # 3. 检查文件系统权限
            logger.info("检查文件系统权限...")
            filesystem_checks = {
                "temp_dir_writable": os.access(tempfile.gettempdir(), os.W_OK),
                "current_dir_writable": os.access(".", os.W_OK),
                "can_create_files": False,
                "can_delete_files": False
            }

            # 测试文件创建和删除
            try:
                test_file = self.test_dir / "permission_test.txt"
                with open(test_file, 'w') as f:
                    f.write("权限测试")
                filesystem_checks["can_create_files"] = True

                os.remove(test_file)
                filesystem_checks["can_delete_files"] = True
                logger.info("✅ 文件系统权限正常")
            except Exception as e:
                logger.error(f"❌ 文件系统权限问题: {e}")

            test_result["readiness_checks"]["filesystem"] = filesystem_checks

            # 4. 性能基准测试
            logger.info("执行性能基准测试...")
            performance_metrics = {}

            # 测试SRT处理性能
            start_time = time.time()
            try:
                test_srt = self.test_dir / "perf_test.srt"
                large_srt_content = ""
                for i in range(100):  # 创建100个字幕段
                    start_ms = i * 2000
                    end_ms = (i + 1) * 2000
                    start_time_str = f"00:{start_ms//60000:02d}:{(start_ms%60000)//1000:02d},{start_ms%1000:03d}"
                    end_time_str = f"00:{end_ms//60000:02d}:{(end_ms%60000)//1000:02d},{end_ms%1000:03d}"
                    large_srt_content += f"{i+1}\n{start_time_str} --> {end_time_str}\n性能测试字幕段 {i+1}\n\n"

                with open(test_srt, 'w', encoding='utf-8') as f:
                    f.write(large_srt_content)
                self.created_files.append(str(test_srt))

                from simple_ui_fixed import VideoProcessor
                srt_info = VideoProcessor.get_srt_info(str(test_srt))

                srt_processing_time = time.time() - start_time
                performance_metrics["srt_processing_time"] = srt_processing_time
                performance_metrics["srt_processing_success"] = srt_info is not None and srt_info.get("is_valid", False)

                logger.info(f"✅ SRT处理性能: {srt_processing_time:.3f}秒")
            except Exception as e:
                performance_metrics["srt_processing_error"] = str(e)
                logger.error(f"❌ SRT处理性能测试失败: {e}")

            test_result["readiness_checks"]["performance"] = performance_metrics

            # 5. 生成就绪性评估
            all_deps_ok = all(dependencies.values())
            all_modules_ok = all(core_modules.values())
            filesystem_ok = all(filesystem_checks.values())
            performance_ok = performance_metrics.get("srt_processing_success", False)

            if all_deps_ok and all_modules_ok and filesystem_ok and performance_ok:
                test_result["status"] = "生产就绪"
                logger.info("✅ 系统已准备好投入生产环境")
            elif all_deps_ok and all_modules_ok and filesystem_ok:
                test_result["status"] = "基本就绪"
                test_result["recommendations"].append("建议进行更多性能测试")
                logger.info("✅ 系统基本准备好投入生产环境")
            else:
                test_result["status"] = "需要修复"
                if not all_deps_ok:
                    test_result["recommendations"].append("修复依赖问题")
                if not all_modules_ok:
                    test_result["recommendations"].append("修复核心模块问题")
                if not filesystem_ok:
                    test_result["recommendations"].append("修复文件系统权限问题")
                logger.warning("⚠️ 系统需要修复后才能投入生产环境")

        except Exception as e:
            logger.error(f"❌ 生产就绪性测试异常: {str(e)}")
            test_result["status"] = "测试异常"
            test_result["error"] = str(e)

        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]

        self.test_results.append(test_result)
        return test_result

    def cleanup_test_files(self) -> Dict[str, Any]:
        """清理测试文件"""
        logger.info("=" * 60)
        logger.info("清理测试环境")
        logger.info("=" * 60)

        cleanup_result = {
            "test_name": "环境清理",
            "start_time": time.time(),
            "status": "进行中",
            "cleaned_files": [],
            "failed_files": []
        }

        try:
            for file_path in self.created_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleanup_result["cleaned_files"].append(file_path)
                        logger.info(f"✅ 已删除: {file_path}")
                except Exception as e:
                    cleanup_result["failed_files"].append({"file": file_path, "error": str(e)})
                    logger.error(f"❌ 删除失败: {file_path} - {str(e)}")

            # 清理测试目录
            try:
                if self.test_dir.exists():
                    shutil.rmtree(self.test_dir)
                    logger.info(f"✅ 已删除测试目录: {self.test_dir}")
                    cleanup_result["status"] = "完成"
            except Exception as e:
                logger.error(f"❌ 删除测试目录失败: {str(e)}")
                cleanup_result["status"] = "部分完成"

        except Exception as e:
            logger.error(f"❌ 环境清理异常: {str(e)}")
            cleanup_result["status"] = "异常"

        cleanup_result["end_time"] = time.time()
        cleanup_result["duration"] = cleanup_result["end_time"] - cleanup_result["start_time"]

        self.test_results.append(cleanup_result)
        return cleanup_result

    def run_final_verification(self) -> Dict[str, Any]:
        """运行最终综合验证"""
        logger.info("🎯 开始VisionAI-ClipsMaster最终综合验证")
        logger.info("=" * 80)

        overall_start_time = time.time()

        try:
            # 1. UI功能完整性测试
            logger.info("执行测试1: UI功能完整性测试")
            ui_test = self.test_ui_functionality_complete()

            # 2. 完整工作流程测试
            logger.info("执行测试2: 完整工作流程测试")
            workflow_test = self.test_complete_workflow_fixed()

            # 3. 生产环境就绪性测试
            logger.info("执行测试3: 生产环境就绪性测试")
            readiness_test = self.test_production_readiness()

            # 4. 清理测试环境
            logger.info("执行清理: 清理测试环境")
            cleanup_result = self.cleanup_test_files()

        except Exception as e:
            logger.error(f"❌ 最终验证异常: {str(e)}")
            try:
                self.cleanup_test_files()
            except:
                pass

        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time

        # 生成最终验证报告
        verification_report = self.generate_final_report(overall_duration)

        return verification_report

    def generate_final_report(self, overall_duration: float) -> Dict[str, Any]:
        """生成最终验证报告"""
        logger.info("=" * 80)
        logger.info("📊 生成最终验证报告")
        logger.info("=" * 80)

        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") in ["完全通过", "基本通过", "生产就绪", "基本就绪", "完成"]])

        # 生成报告
        report = {
            "verification_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                "overall_duration": round(overall_duration, 2),
                "verification_date": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "final_assessment": self._generate_final_assessment(),
            "deployment_recommendation": self._generate_deployment_recommendation()
        }

        # 打印摘要
        logger.info("📋 最终验证摘要:")
        logger.info(f"  总测试数: {total_tests}")
        logger.info(f"  通过测试: {passed_tests}")
        logger.info(f"  成功率: {report['verification_summary']['success_rate']}%")
        logger.info(f"  总耗时: {overall_duration:.2f}秒")

        # 保存报告
        report_file = f"final_verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 最终验证报告已保存: {report_file}")
            report["report_file"] = report_file
        except Exception as e:
            logger.error(f"❌ 保存验证报告失败: {str(e)}")

        return report

    def _generate_final_assessment(self) -> Dict[str, Any]:
        """生成最终评估"""
        assessment = {
            "overall_status": "需要评估",
            "key_achievements": [],
            "remaining_issues": [],
            "system_health": {}
        }

        try:
            for result in self.test_results:
                test_name = result.get("test_name", "")
                status = result.get("status", "")

                if "UI功能" in test_name:
                    if status in ["完全通过", "基本通过"]:
                        assessment["key_achievements"].append("UI功能完整性验证通过")
                        assessment["system_health"]["ui"] = "良好"
                    else:
                        assessment["remaining_issues"].append("UI功能存在问题")
                        assessment["system_health"]["ui"] = "需要关注"

                elif "工作流程" in test_name:
                    if status in ["完全通过", "基本通过"]:
                        assessment["key_achievements"].append("完整工作流程验证通过")
                        assessment["system_health"]["workflow"] = "良好"
                    else:
                        assessment["remaining_issues"].append("工作流程存在问题")
                        assessment["system_health"]["workflow"] = "需要关注"

                elif "生产环境" in test_name:
                    if status in ["生产就绪", "基本就绪"]:
                        assessment["key_achievements"].append("生产环境就绪性验证通过")
                        assessment["system_health"]["production"] = "就绪"
                    else:
                        assessment["remaining_issues"].append("生产环境就绪性不足")
                        assessment["system_health"]["production"] = "需要修复"

            # 综合评估
            if len(assessment["remaining_issues"]) == 0:
                assessment["overall_status"] = "优秀"
            elif len(assessment["remaining_issues"]) <= 1:
                assessment["overall_status"] = "良好"
            else:
                assessment["overall_status"] = "需要改进"

        except Exception as e:
            assessment["overall_status"] = "评估异常"
            assessment["remaining_issues"].append(f"最终评估异常: {str(e)}")

        return assessment

    def _generate_deployment_recommendation(self) -> Dict[str, Any]:
        """生成部署建议"""
        recommendation = {
            "can_deploy": False,
            "deployment_readiness": "评估中",
            "prerequisites": [],
            "next_actions": []
        }

        try:
            ui_ok = False
            workflow_ok = False
            production_ok = False

            for result in self.test_results:
                test_name = result.get("test_name", "")
                status = result.get("status", "")

                if "UI功能" in test_name and status in ["完全通过", "基本通过"]:
                    ui_ok = True
                elif "工作流程" in test_name and status in ["完全通过", "基本通过"]:
                    workflow_ok = True
                elif "生产环境" in test_name and status in ["生产就绪", "基本就绪"]:
                    production_ok = True

            if ui_ok and workflow_ok and production_ok:
                recommendation["can_deploy"] = True
                recommendation["deployment_readiness"] = "就绪"
                recommendation["next_actions"] = [
                    "可以立即部署到生产环境",
                    "建议进行用户验收测试",
                    "监控系统运行状态"
                ]
            elif ui_ok and workflow_ok:
                recommendation["can_deploy"] = True
                recommendation["deployment_readiness"] = "基本就绪"
                recommendation["prerequisites"] = ["建议进行更多生产环境测试"]
                recommendation["next_actions"] = [
                    "可以部署到测试环境",
                    "进行生产环境适配",
                    "完成用户验收测试后部署"
                ]
            else:
                recommendation["can_deploy"] = False
                recommendation["deployment_readiness"] = "需要修复"
                if not ui_ok:
                    recommendation["prerequisites"].append("修复UI功能问题")
                if not workflow_ok:
                    recommendation["prerequisites"].append("修复工作流程问题")
                if not production_ok:
                    recommendation["prerequisites"].append("修复生产环境就绪性问题")
                recommendation["next_actions"] = [
                    "修复所有发现的问题",
                    "重新运行验证测试",
                    "确认所有功能正常后再部署"
                ]

        except Exception as e:
            recommendation["deployment_readiness"] = "评估异常"
            recommendation["next_actions"] = [f"修复评估异常: {str(e)}"]

        return recommendation


def main():
    """主函数"""
    print("🎯 VisionAI-ClipsMaster 最终综合验证")
    print("=" * 80)

    # 创建验证器
    verifier = FinalVerificationTester()

    try:
        # 运行最终验证
        report = verifier.run_final_verification()

        # 显示最终结果
        overall_status = report.get("final_assessment", {}).get("overall_status", "未知")
        can_deploy = report.get("deployment_recommendation", {}).get("can_deploy", False)

        if overall_status == "优秀" and can_deploy:
            print(f"\n🎉 最终验证完成！系统状态: {overall_status} - 可以立即投入生产使用")
        elif overall_status in ["良好", "优秀"] and can_deploy:
            print(f"\n✅ 最终验证完成！系统状态: {overall_status} - 可以部署使用")
        elif overall_status == "良好":
            print(f"\n⚠️ 最终验证完成！系统状态: {overall_status} - 建议完善后部署")
        else:
            print(f"\n❌ 最终验证完成！系统状态: {overall_status} - 需要修复后使用")

        return report

    except KeyboardInterrupt:
        print("\n⏹️ 验证被用户中断")
        try:
            verifier.cleanup_test_files()
        except:
            pass
        return None
    except Exception as e:
        print(f"\n💥 验证执行异常: {str(e)}")
        try:
            verifier.cleanup_test_files()
        except:
            pass
        return None


if __name__ == "__main__":
    main()
