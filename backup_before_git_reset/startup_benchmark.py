#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 启动基准测试
监控和测试启动性能
"""

import time
import psutil
from pathlib import Path

class StartupBenchmark:
    """启动基准测试"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.checkpoints = []
        
    def checkpoint(self, name: str):
        """记录检查点"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        memory_mb = self.process.memory_info().rss / 1024**2
        
        self.checkpoints.append({
            "name": name,
            "elapsed_time": elapsed,
            "memory_mb": memory_mb,
            "timestamp": current_time
        })
        
        print(f"⏱️ {name}: {elapsed:.3f}秒, 内存: {memory_mb:.1f}MB")
    
    def run_benchmark(self):
        """运行基准测试"""
        print("🚀 启动基准测试开始...")
        
        self.checkpoint("测试开始")
        
        # 测试模块导入
        try:
            import simple_ui_fixed
            self.checkpoint("UI模块导入完成")
        except Exception as e:
            print(f"❌ UI模块导入失败: {e}")
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            self.checkpoint("AI引擎导入完成")
        except Exception as e:
            print(f"❌ AI引擎导入失败: {e}")
        
        try:
            from src.core.language_detector import LanguageDetector
            self.checkpoint("语言检测器导入完成")
        except Exception as e:
            print(f"❌ 语言检测器导入失败: {e}")
        
        self.checkpoint("基准测试完成")
        
        # 生成报告
        total_time = self.checkpoints[-1]["elapsed_time"]
        peak_memory = max(cp["memory_mb"] for cp in self.checkpoints)
        
        print(f"\n📊 基准测试结果:")
        print(f"   总启动时间: {total_time:.3f}秒")
        print(f"   峰值内存: {peak_memory:.1f}MB")
        print(f"   目标达成: {'✅' if total_time <= 5.0 else '❌'}")
        
        return {
            "total_time": total_time,
            "peak_memory": peak_memory,
            "target_met": total_time <= 5.0,
            "checkpoints": self.checkpoints
        }

def main():
    """主函数"""
    benchmark = StartupBenchmark()
    return benchmark.run_benchmark()

if __name__ == "__main__":
    main()
