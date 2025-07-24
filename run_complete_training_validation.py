#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行完整训练验证测试
按照用户要求的5个核心测试模块顺序执行所有测试
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path

class CompleteTrainingValidationRunner:
    """完整训练验证测试运行器"""
    
    def __init__(self):
        """初始化运行器"""
        self.setup_logging()
        self.start_time = time.time()
        self.test_results = {}
        
        self.logger.info("🚀 完整训练验证测试运行器初始化完成")
    
    def setup_logging(self):
        """设置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"complete_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("CompleteValidationRunner")
    
    def run_all_tests(self) -> dict:
        """运行所有测试"""
        print("🎯 VisionAI-ClipsMaster 完整训练验证测试")
        print("=" * 80)
        print("按照用户要求执行5个核心测试模块：")
        print("1. 训练模块功能验证")
        print("2. 学习效果量化测试")
        print("3. GPU加速性能测试")
        print("4. 训练稳定性验证")
        print("5. 输出验证")
        print("=" * 80)
        
        try:
            # 1. 运行综合训练验证测试
            self.logger.info("📋 1/4 运行综合训练验证测试...")
            print("\n🔧 步骤 1/4: 运行综合训练验证测试")
            result1 = self._run_script("comprehensive_training_validation_system.py")
            self.test_results["comprehensive_validation"] = result1
            
            # 2. 运行训练效果评估
            self.logger.info("📊 2/4 运行训练效果评估...")
            print("\n📊 步骤 2/4: 运行训练效果评估")
            result2 = self._run_script("training_effectiveness_evaluator.py")
            self.test_results["effectiveness_evaluation"] = result2
            
            # 3. 运行GPU性能测试（可选）
            self.logger.info("🎮 3/4 运行GPU性能测试...")
            print("\n🎮 步骤 3/4: 运行GPU性能测试")
            result3 = self._run_script("gpu_training_performance_test.py")
            self.test_results["gpu_performance"] = result3
            
            # 4. 生成最终报告
            self.logger.info("📋 4/4 生成最终综合报告...")
            print("\n📋 步骤 4/4: 生成最终综合报告")
            result4 = self._run_script("final_training_validation_report.py")
            self.test_results["final_report"] = result4
            
            # 计算总耗时
            total_duration = time.time() - self.start_time
            
            # 显示测试结果摘要
            self._display_test_summary(total_duration)
            
            return {
                "success": True,
                "total_duration": total_duration,
                "test_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"完整测试运行失败: {str(e)}"
            self.logger.error(error_msg)
            print(f"\n❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def _run_script(self, script_name: str) -> dict:
        """运行单个测试脚本"""
        script_path = Path(script_name)
        
        if not script_path.exists():
            error_msg = f"测试脚本不存在: {script_name}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            self.logger.info(f"执行脚本: {script_name}")
            start_time = time.time()
            
            # 运行脚本
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"✅ {script_name} 执行成功，耗时: {duration:.2f}秒")
                return {
                    "success": True,
                    "duration": duration,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                error_msg = f"{script_name} 执行失败，返回码: {result.returncode}"
                self.logger.error(error_msg)
                self.logger.error(f"错误输出: {result.stderr}")
                return {
                    "success": False,
                    "error": error_msg,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            error_msg = f"{script_name} 执行超时"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"{script_name} 执行异常: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _display_test_summary(self, total_duration: float):
        """显示测试结果摘要"""
        print("\n" + "=" * 80)
        print("📊 完整训练验证测试结果摘要")
        print("=" * 80)
        
        # 统计成功/失败的测试
        successful_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        total_tests = len(self.test_results)
        
        print(f"⏱️  总耗时: {total_duration:.2f}秒")
        print(f"✅ 成功测试: {successful_tests}/{total_tests}")
        print(f"❌ 失败测试: {total_tests - successful_tests}/{total_tests}")
        
        # 显示各个测试的状态
        print("\n📋 详细测试状态:")
        test_names = {
            "comprehensive_validation": "综合训练验证测试",
            "effectiveness_evaluation": "训练效果评估",
            "gpu_performance": "GPU性能测试",
            "final_report": "最终报告生成"
        }
        
        for test_key, test_name in test_names.items():
            if test_key in self.test_results:
                result = self.test_results[test_key]
                status = "✅ 成功" if result.get("success", False) else "❌ 失败"
                duration = result.get("duration", 0)
                print(f"  {test_name}: {status} ({duration:.2f}秒)")
                
                if not result.get("success", False) and "error" in result:
                    print(f"    错误: {result['error']}")
        
        # 显示生成的报告位置
        print("\n📁 生成的测试报告:")
        report_dirs = [
            "test_output/training_validation",
            "test_output/training_effectiveness", 
            "test_output/gpu_performance",
            "test_output/final_validation_report"
        ]
        
        for report_dir in report_dirs:
            if Path(report_dir).exists():
                print(f"  📊 {report_dir}")
        
        # 显示关键指标
        print("\n🎯 关键测试指标:")
        
        # 尝试从最终报告中提取关键指标
        final_report_dir = Path("test_output/final_validation_report")
        if final_report_dir.exists():
            try:
                import json
                latest_json = max(final_report_dir.glob("final_training_validation_report_*.json"), 
                                key=lambda f: f.stat().st_mtime)
                
                with open(latest_json, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                executive_summary = report_data.get("executive_summary", {})
                print(f"  🏆 总体状态: {executive_summary.get('overall_status', 'UNKNOWN')}")
                
                performance_highlights = executive_summary.get("performance_highlights", {})
                print(f"  📈 测试覆盖率: {performance_highlights.get('test_coverage', 'N/A')}")
                print(f"  📊 改进率: {performance_highlights.get('improvement_rate', 'N/A')}")
                print(f"  🔒 稳定性: {performance_highlights.get('stability_status', 'N/A')}")
                
                achievements = executive_summary.get("key_achievements", [])
                if achievements:
                    print(f"  🎉 关键成就: {len(achievements)}项")
                
            except Exception as e:
                print(f"  ⚠️ 无法读取最终报告: {str(e)}")
        
        print("\n" + "=" * 80)
        
        if successful_tests == total_tests:
            print("🎉 所有测试成功完成！VisionAI-ClipsMaster训练验证测试通过！")
        else:
            print("⚠️ 部分测试失败，请检查日志文件获取详细信息。")
        
        print("=" * 80)
    
    def check_prerequisites(self) -> bool:
        """检查运行前提条件"""
        self.logger.info("🔍 检查运行前提条件...")
        
        # 检查必要的脚本文件
        required_scripts = [
            "comprehensive_training_validation_system.py",
            "training_effectiveness_evaluator.py", 
            "gpu_training_performance_test.py",
            "final_training_validation_report.py"
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if not Path(script).exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            self.logger.error(f"缺少必要的测试脚本: {missing_scripts}")
            return False
        
        # 检查Python版本
        if sys.version_info < (3, 7):
            self.logger.error("需要Python 3.7或更高版本")
            return False
        
        # 检查必要的目录
        required_dirs = ["src", "data", "configs"]
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                self.logger.warning(f"建议的目录不存在: {dir_name}")
        
        self.logger.info("✅ 前提条件检查通过")
        return True


def main():
    """主函数"""
    runner = CompleteTrainingValidationRunner()
    
    try:
        # 检查前提条件
        if not runner.check_prerequisites():
            print("❌ 前提条件检查失败，请确保所有必要文件存在")
            return
        
        # 运行所有测试
        results = runner.run_all_tests()
        
        if results.get("success", False):
            print(f"\n🎊 完整训练验证测试成功完成！")
            print(f"📊 详细报告请查看 test_output/ 目录")
        else:
            print(f"\n💥 测试运行失败: {results.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"\n💥 运行器异常: {str(e)}")
        runner.logger.error(f"运行器异常: {str(e)}")


if __name__ == "__main__":
    main()
