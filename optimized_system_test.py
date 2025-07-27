#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化系统集成测试
验证所有优化功能：模型训练、GPU/CPU兼容性、路径管理
"""

import os
import sys
import json
import time
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class OptimizedSystemTest:
    """优化系统集成测试"""
    
    def __init__(self):
        """初始化测试"""
        self.test_start_time = time.time()
        self.test_results = []
        self.logger = self._setup_logger()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="optimized_test_"))
        
        self.logger.info("🚀 优化系统集成测试开始")
        self.logger.info(f"📁 测试目录: {self.temp_dir}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('optimized_system_test.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def test_enhanced_trainer(self) -> Dict[str, Any]:
        """测试增强训练器"""
        self.logger.info("=" * 60)
        self.logger.info("测试1: 增强训练器功能验证")
        self.logger.info("=" * 60)
        
        test_result = {
            "test_name": "enhanced_trainer",
            "start_time": time.time(),
            "status": "running",
            "details": {}
        }
        
        try:
            # 导入增强训练器
            from src.training.enhanced_trainer import EnhancedTrainer
            
            # 创建训练器实例
            trainer = EnhancedTrainer(use_gpu=None)  # 自动检测
            
            # 创建测试数据
            test_data = [
                {"original": "这是一个普通的剧情描述", "viral": "震撼！这个剧情让人欲罢不能！"},
                {"original": "角色之间的对话很平淡", "viral": "绝了！这段对话太有深度了！"},
                {"original": "故事发展比较缓慢", "viral": "节奏完美！每一秒都是高潮！"},
                {"original": "结局还算不错", "viral": "神结局！完全没想到会这样！"},
                {"original": "演员表演一般", "viral": "演技炸裂！每个表情都是戏！"}
            ] * 10  # 扩展到50个样本
            
            # 执行训练
            def progress_callback(progress, message):
                self.logger.info(f"训练进度: {progress:.1%} - {message}")
                return True
            
            training_result = trainer.train(test_data, progress_callback)
            
            # 验证结果
            if training_result["success"]:
                accuracy = training_result["final_accuracy"]
                test_result["status"] = "passed" if accuracy >= 0.8 else "partial"
                test_result["details"] = {
                    "accuracy": accuracy,
                    "device": training_result["device"],
                    "training_time": training_result["training_time"],
                    "epochs": training_result["epochs_completed"]
                }
                
                if accuracy >= 0.8:
                    self.logger.info(f"✅ 训练器测试通过: 准确率 {accuracy:.2%}")
                else:
                    self.logger.warning(f"⚠️ 训练器部分通过: 准确率 {accuracy:.2%}")
            else:
                test_result["status"] = "failed"
                test_result["error"] = training_result.get("error", "未知错误")
                self.logger.error(f"❌ 训练器测试失败: {test_result['error']}")
                
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            self.logger.error(f"❌ 训练器测试异常: {e}")
        
        test_result["duration"] = time.time() - test_result["start_time"]
        return test_result
    
    def test_gpu_cpu_manager(self) -> Dict[str, Any]:
        """测试GPU/CPU管理器"""
        self.logger.info("=" * 60)
        self.logger.info("测试2: GPU/CPU兼容性管理器")
        self.logger.info("=" * 60)
        
        test_result = {
            "test_name": "gpu_cpu_manager",
            "start_time": time.time(),
            "status": "running",
            "details": {}
        }
        
        try:
            # 导入GPU/CPU管理器
            from src.core.gpu_cpu_manager import GPUCPUManager
            
            # 创建管理器实例
            manager = GPUCPUManager()
            
            # 获取系统报告
            system_report = manager.get_system_report()
            
            # 获取最优配置
            optimal_config = manager.get_optimal_config("training")
            
            # 自动配置PyTorch
            torch_config = manager.auto_configure_torch()
            
            # 检查兼容性
            requirements = {"memory_gb": 4, "cuda_version": "11.0"}
            compatibility = manager.check_compatibility(requirements)
            
            test_result["status"] = "passed"
            test_result["details"] = {
                "recommended_device": system_report["recommended_device"],
                "gpu_available": system_report["gpu_info"]["cuda_available"],
                "gpu_count": system_report["gpu_info"]["gpu_count"],
                "cpu_cores": system_report["cpu_info"]["cores"],
                "memory_gb": system_report["system_info"]["memory_total_gb"],
                "torch_config_success": torch_config["success"],
                "optimal_batch_size": optimal_config["batch_size"],
                "compatibility": compatibility["compatible"]
            }
            
            self.logger.info(f"✅ GPU/CPU管理器测试通过")
            self.logger.info(f"📱 推荐设备: {system_report['recommended_device']}")
            self.logger.info(f"⚙️ 最优批次大小: {optimal_config['batch_size']}")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            self.logger.error(f"❌ GPU/CPU管理器测试失败: {e}")
        
        test_result["duration"] = time.time() - test_result["start_time"]
        return test_result
    
    def test_path_manager(self) -> Dict[str, Any]:
        """测试路径管理器"""
        self.logger.info("=" * 60)
        self.logger.info("测试3: 路径管理器功能验证")
        self.logger.info("=" * 60)
        
        test_result = {
            "test_name": "path_manager",
            "start_time": time.time(),
            "status": "running",
            "details": {}
        }
        
        try:
            # 导入路径管理器
            from src.core.path_manager import PathManager
            
            # 创建管理器实例
            manager = PathManager()
            
            # 创建测试文件
            test_file = self.temp_dir / "test_video.mp4"
            test_file.write_text("test video content")
            
            # 测试路径解析
            resolved_path = manager.resolve_file_path(test_file)
            
            # 测试可移植路径
            portable_path = manager.create_portable_path(test_file)
            restored_path = manager.resolve_portable_path(portable_path)
            
            # 测试项目结构验证
            validation = manager.validate_project_structure()
            
            # 测试路径映射
            file_list = [str(test_file), "nonexistent.mp4"]
            path_mapping = manager.create_path_mapping(file_list)
            
            # 获取路径报告
            path_report = manager.get_path_report()
            
            test_result["status"] = "passed"
            test_result["details"] = {
                "path_resolution_success": resolved_path is not None,
                "portable_path_created": portable_path is not None,
                "project_structure_valid": validation["valid"],
                "missing_files_count": len(validation["missing_files"]),
                "path_mapping_success": len(path_mapping) > 0,
                "cache_size": path_report["cache_size"]
            }
            
            self.logger.info(f"✅ 路径管理器测试通过")
            self.logger.info(f"📁 项目结构: {'有效' if validation['valid'] else '需要修复'}")
            self.logger.info(f"🔍 路径缓存: {path_report['cache_size']} 项")
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            self.logger.error(f"❌ 路径管理器测试失败: {e}")
        
        test_result["duration"] = time.time() - test_result["start_time"]
        return test_result
    
    def test_integrated_workflow(self) -> Dict[str, Any]:
        """测试集成工作流程"""
        self.logger.info("=" * 60)
        self.logger.info("测试4: 集成工作流程验证")
        self.logger.info("=" * 60)
        
        test_result = {
            "test_name": "integrated_workflow",
            "start_time": time.time(),
            "status": "running",
            "details": {}
        }
        
        try:
            # 运行原有的端到端测试
            from complete_e2e_integration_test import CompleteE2EIntegrationTester
            
            e2e_tester = CompleteE2EIntegrationTester()
            
            # 执行核心步骤
            step1 = e2e_tester.create_realistic_test_data()
            step2 = e2e_tester.test_subtitle_understanding_and_script_reconstruction()
            step3 = e2e_tester.test_viral_subtitle_generation()
            step4 = e2e_tester.test_video_editing_processing()
            step5 = e2e_tester.test_jianying_project_file_generation()
            
            # 评估结果
            all_steps = [step1, step2, step3, step4, step5]
            success_count = sum(1 for step in all_steps if step.get("status") == "success")
            success_rate = success_count / len(all_steps)
            
            test_result["status"] = "passed" if success_rate >= 0.8 else "partial"
            test_result["details"] = {
                "total_steps": len(all_steps),
                "successful_steps": success_count,
                "success_rate": success_rate,
                "step_results": [step.get("status", "unknown") for step in all_steps]
            }
            
            if success_rate >= 0.8:
                self.logger.info(f"✅ 集成工作流程测试通过: {success_rate:.1%}")
            else:
                self.logger.warning(f"⚠️ 集成工作流程部分通过: {success_rate:.1%}")
            
            # 清理测试数据
            e2e_tester.cleanup_test_files()
            
        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            self.logger.error(f"❌ 集成工作流程测试失败: {e}")
        
        test_result["duration"] = time.time() - test_result["start_time"]
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("🎯 开始优化系统集成测试")
        
        # 执行所有测试
        test_methods = [
            self.test_enhanced_trainer,
            self.test_gpu_cpu_manager,
            self.test_path_manager,
            self.test_integrated_workflow
        ]
        
        for test_method in test_methods:
            try:
                result = test_method()
                self.test_results.append(result)
            except Exception as e:
                self.logger.error(f"测试方法 {test_method.__name__} 执行失败: {e}")
                self.test_results.append({
                    "test_name": test_method.__name__,
                    "status": "failed",
                    "error": str(e),
                    "duration": 0
                })
        
        # 生成总结报告
        return self.generate_final_report()
    
    def generate_final_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "passed")
        partial_tests = sum(1 for r in self.test_results if r["status"] == "partial")
        failed_tests = sum(1 for r in self.test_results if r["status"] == "failed")
        
        success_rate = (passed_tests + partial_tests * 0.5) / total_tests if total_tests > 0 else 0
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "partial_tests": partial_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "total_duration": time.time() - self.test_start_time
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "status": "优秀" if success_rate >= 0.95 else "良好" if success_rate >= 0.8 else "需要改进"
        }
        
        # 保存报告
        report_file = f"optimized_system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        self.logger.info("=" * 80)
        self.logger.info("🎉 优化系统集成测试完成")
        self.logger.info("=" * 80)
        self.logger.info(f"📊 总测试数: {total_tests}")
        self.logger.info(f"✅ 通过: {passed_tests}")
        self.logger.info(f"⚠️ 部分通过: {partial_tests}")
        self.logger.info(f"❌ 失败: {failed_tests}")
        self.logger.info(f"🎯 成功率: {success_rate:.1%}")
        self.logger.info(f"⏱️ 总耗时: {report['test_summary']['total_duration']:.2f}秒")
        self.logger.info(f"📄 报告文件: {report_file}")
        
        return report
    
    def cleanup(self):
        """清理测试环境"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"🧹 测试目录已清理: {self.temp_dir}")
        except Exception as e:
            self.logger.warning(f"⚠️ 清理测试目录失败: {e}")

def main():
    """主函数"""
    tester = OptimizedSystemTest()
    
    try:
        report = tester.run_all_tests()
        return 0 if report["test_summary"]["success_rate"] >= 0.95 else 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())
