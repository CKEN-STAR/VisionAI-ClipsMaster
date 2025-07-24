#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速训练验证测试脚本
用于快速验证训练模块的基本功能
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.training.en_trainer import EnTrainer
from src.training.zh_trainer import ZhTrainer
from src.utils.memory_guard import get_memory_manager
from src.utils.device_manager import DeviceManager

class QuickTrainingTest:
    """快速训练测试类"""
    
    def __init__(self):
        """初始化测试"""
        self.memory_manager = get_memory_manager()
        self.device_manager = DeviceManager()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建简单测试数据
        self.test_data_en = [
            {
                "original": "John went to the store to buy groceries.",
                "viral": "SHOCKING: John's INCREDIBLE store visit will BLOW YOUR MIND!"
            },
            {
                "original": "The weather was beautiful today.",
                "viral": "AMAZING weather that will CHANGE EVERYTHING you know!"
            }
        ]
        
        self.test_data_zh = [
            {
                "original": "小明今天去学校上课。",
                "viral": "震撼！小明的学校之旅太精彩了！改变一切！"
            },
            {
                "original": "妈妈在厨房做饭。",
                "viral": "惊呆了！妈妈的厨艺史上最强！太震撼！"
            }
        ]
    
    def run_quick_test(self) -> dict:
        """运行快速测试"""
        self.logger.info("🚀 开始快速训练验证测试...")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        # 1. 测试英文训练器
        self.logger.info("\n📝 测试英文训练器...")
        en_result = self._test_english_trainer()
        results["tests"]["english_trainer"] = en_result
        
        # 2. 测试中文训练器
        self.logger.info("\n📝 测试中文训练器...")
        zh_result = self._test_chinese_trainer()
        results["tests"]["chinese_trainer"] = zh_result
        
        # 3. 测试设备管理器
        self.logger.info("\n🖥️ 测试设备管理器...")
        device_result = self._test_device_manager()
        results["tests"]["device_manager"] = device_result
        
        # 4. 测试内存管理
        self.logger.info("\n💾 测试内存管理...")
        memory_result = self._test_memory_management()
        results["tests"]["memory_management"] = memory_result
        
        # 生成摘要
        results["summary"] = self._generate_summary(results["tests"])
        results["end_time"] = datetime.now().isoformat()
        
        # 显示结果
        self._display_results(results)
        
        # 保存结果
        self._save_results(results)
        
        return results
    
    def _test_english_trainer(self) -> dict:
        """测试英文训练器"""
        try:
            trainer = EnTrainer(use_gpu=False)
            
            memory_before = self.memory_manager.get_memory_usage()
            start_time = time.time()
            
            # 执行训练
            training_result = trainer.train(
                training_data=self.test_data_en,
                progress_callback=self._progress_callback
            )
            
            end_time = time.time()
            memory_after = self.memory_manager.get_memory_usage()
            
            # 测试输出验证
            test_output = "AMAZING story about John's journey! INCREDIBLE results!"
            validation_result = trainer.validate_english_output(test_output)
            
            return {
                "success": training_result.get("success", False),
                "training_time": end_time - start_time,
                "memory_usage": {
                    "before": memory_before,
                    "after": memory_after,
                    "delta": memory_after - memory_before
                },
                "training_result": training_result,
                "validation_result": validation_result,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"英文训练器测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_chinese_trainer(self) -> dict:
        """测试中文训练器"""
        try:
            trainer = ZhTrainer(use_gpu=False)
            
            memory_before = self.memory_manager.get_memory_usage()
            start_time = time.time()
            
            # 执行训练
            training_result = trainer.train(
                training_data=self.test_data_zh,
                progress_callback=self._progress_callback
            )
            
            end_time = time.time()
            memory_after = self.memory_manager.get_memory_usage()
            
            # 测试输出验证
            test_output = "震撼！小明的故事太精彩了！改变一切！"
            validation_result = trainer.validate_chinese_output(test_output)
            
            return {
                "success": training_result.get("success", False),
                "training_time": end_time - start_time,
                "memory_usage": {
                    "before": memory_before,
                    "after": memory_after,
                    "delta": memory_after - memory_before
                },
                "training_result": training_result,
                "validation_result": validation_result,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"中文训练器测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_device_manager(self) -> dict:
        """测试设备管理器"""
        try:
            # 测试设备选择
            selected_device = self.device_manager.select_device()
            
            # 测试设备信息获取
            device_info = self.device_manager.get_device_info()
            
            # 测试GPU检测
            gpu_devices = self.device_manager.detect_gpus()
            
            # 测试CPU回退
            cpu_fallback = self.device_manager.test_cpu_fallback()
            
            # 处理设备信息的JSON序列化
            serializable_device_info = {}
            for key, value in device_info.items():
                if hasattr(value, 'value'):  # 处理Enum类型
                    serializable_device_info[key] = str(value)
                elif isinstance(value, list):
                    serializable_device_info[key] = [str(item) if hasattr(item, 'value') else item for item in value]
                else:
                    serializable_device_info[key] = value

            return {
                "success": True,
                "selected_device": str(selected_device),
                "device_info": serializable_device_info,
                "gpu_devices_count": len(gpu_devices),
                "cpu_fallback_available": cpu_fallback,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"设备管理器测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_memory_management(self) -> dict:
        """测试内存管理"""
        try:
            # 获取初始内存
            initial_memory = self.memory_manager.get_memory_usage()
            
            # 启动内存监控
            self.memory_manager.start_monitoring()
            
            # 模拟内存使用
            test_data = ["test"] * 10000  # 创建一些测试数据
            
            # 强制清理
            self.memory_manager.force_cleanup()
            
            # 停止监控
            self.memory_manager.stop_monitoring()
            
            final_memory = self.memory_manager.get_memory_usage()
            
            return {
                "success": True,
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_delta": final_memory - initial_memory,
                "cleanup_effective": final_memory <= initial_memory + 50,  # 50MB容差
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"内存管理测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _progress_callback(self, progress: float, message: str):
        """进度回调"""
        if progress in [0.0, 0.5, 1.0]:  # 只显示关键进度点
            self.logger.info(f"  进度: {progress:.0%} - {message}")
    
    def _generate_summary(self, tests: dict) -> dict:
        """生成测试摘要"""
        total_tests = len(tests)
        successful_tests = sum(1 for test in tests.values() if test.get("success", False))
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "overall_success": successful_tests == total_tests
        }
    
    def _display_results(self, results: dict):
        """显示测试结果"""
        summary = results["summary"]
        
        self.logger.info("\n" + "="*60)
        self.logger.info("🎯 快速测试结果摘要")
        self.logger.info("="*60)
        
        # 显示各项测试结果
        for test_name, test_result in results["tests"].items():
            status = "✅ 成功" if test_result.get("success", False) else "❌ 失败"
            self.logger.info(f"{test_name}: {status}")
            
            if not test_result.get("success", False) and test_result.get("error"):
                self.logger.info(f"  错误: {test_result['error']}")
        
        self.logger.info(f"\n总体结果: {'✅ 全部通过' if summary['overall_success'] else '❌ 部分失败'}")
        self.logger.info(f"成功率: {summary['success_rate']:.1%} ({summary['successful_tests']}/{summary['total_tests']})")
        
        # 显示建议
        if summary['overall_success']:
            self.logger.info("\n🎉 恭喜！所有基础功能测试通过！")
            self.logger.info("💡 建议: 可以运行完整的验证套件进行深度测试")
        else:
            self.logger.info("\n⚠️  部分测试失败，请检查相关模块")
            self.logger.info("💡 建议: 查看详细错误信息并修复问题")
    
    def _save_results(self, results: dict):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"quick_test_results_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"\n📄 测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster 快速训练验证测试")
    print("=" * 50)
    
    try:
        # 运行快速测试
        tester = QuickTrainingTest()
        results = tester.run_quick_test()
        
        # 返回适当的退出码
        if results["summary"]["overall_success"]:
            print("\n✅ 快速测试完成 - 所有基础功能正常！")
            sys.exit(0)
        else:
            print("\n❌ 快速测试发现问题 - 请查看详细日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行失败: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
