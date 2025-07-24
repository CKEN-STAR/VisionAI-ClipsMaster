#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 8小时稳定性测试
模拟长时间运行场景，检测内存泄漏、性能衰减等问题
"""

import sys
import os
import time
import json
import threading
import psutil
import gc
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

class LongTermStabilityTest:
    """长期稳定性测试器"""
    
    def __init__(self, duration_hours: int = 8):
        self.duration_hours = duration_hours
        self.duration_seconds = duration_hours * 3600
        self.start_time = None
        self.end_time = None
        
        # 监控数据
        self.memory_samples = []
        self.cpu_samples = []
        self.performance_samples = []
        self.error_count = 0
        self.warnings = []
        
        # 控制标志
        self.running = False
        self.monitor_thread = None
        
    def run_stability_test(self):
        """运行稳定性测试"""
        print(f"🚀 开始{self.duration_hours}小时稳定性测试")
        print(f"预计结束时间: {(datetime.now() + timedelta(hours=self.duration_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = datetime.now()
        self.running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
        
        try:
            # 主测试循环
            self._run_test_cycles()
            
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断测试")
            
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            self.error_count += 1
            
        finally:
            self.running = False
            self.end_time = datetime.now()
            
            # 等待监控线程结束
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            # 生成测试报告
            self._generate_stability_report()
    
    def _run_test_cycles(self):
        """运行测试循环"""
        cycle_count = 0
        cycle_duration = 300  # 每个循环5分钟
        
        while self.running and (datetime.now() - self.start_time).total_seconds() < self.duration_seconds:
            cycle_start = time.time()
            cycle_count += 1
            
            print(f"📊 执行测试循环 #{cycle_count}")
            
            try:
                # 模拟核心功能测试
                self._simulate_core_functions()
                
                # 模拟内存操作
                self._simulate_memory_operations()
                
                # 模拟文件操作
                self._simulate_file_operations()
                
                # 记录性能数据
                cycle_end = time.time()
                cycle_time = cycle_end - cycle_start
                
                self.performance_samples.append({
                    'cycle': cycle_count,
                    'duration': cycle_time,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 如果循环时间过长，记录警告
                if cycle_time > cycle_duration * 1.5:
                    self.warnings.append(f"循环#{cycle_count}执行时间过长: {cycle_time:.1f}秒")
                
                # 等待到下一个循环
                remaining_time = cycle_duration - cycle_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
                
            except Exception as e:
                self.error_count += 1
                self.warnings.append(f"循环#{cycle_count}发生错误: {e}")
                print(f"⚠️ 循环#{cycle_count}发生错误: {e}")
    
    def _simulate_core_functions(self):
        """模拟核心功能"""
        try:
            # 模拟语言检测
            test_texts = [
                "Hello, this is an English subtitle.",
                "你好，这是中文字幕。",
                "Mixed language: 你好 Hello 世界 World"
            ]
            
            for text in test_texts:
                # 简单的语言检测模拟
                if any(ord(char) > 127 for char in text):
                    detected_lang = "zh"
                else:
                    detected_lang = "en"
            
            # 模拟剧本重构
            original_script = ["Scene 1", "Scene 2", "Scene 3", "Scene 4", "Scene 5"]
            reconstructed_script = original_script[::2] + original_script[1::2]  # 重新排序
            
            # 模拟视频处理
            video_segments = [f"segment_{i}.mp4" for i in range(10)]
            processed_segments = [seg for seg in video_segments if "segment" in seg]
            
        except Exception as e:
            raise Exception(f"核心功能模拟失败: {e}")
    
    def _simulate_memory_operations(self):
        """模拟内存操作"""
        try:
            # 创建和释放大量数据
            large_data = []
            for i in range(100):
                data_chunk = [j for j in range(1000)]
                large_data.append(data_chunk)
            
            # 模拟数据处理
            processed_data = [sum(chunk) for chunk in large_data]
            
            # 清理内存
            del large_data
            del processed_data
            gc.collect()
            
        except Exception as e:
            raise Exception(f"内存操作模拟失败: {e}")
    
    def _simulate_file_operations(self):
        """模拟文件操作"""
        try:
            # 创建临时文件
            temp_dir = PROJECT_ROOT / "temp_stability_test"
            temp_dir.mkdir(exist_ok=True)
            
            # 写入测试文件
            test_file = temp_dir / f"test_{int(time.time())}.txt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("Stability test data\n" * 100)
            
            # 读取文件
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 删除临时文件
            test_file.unlink()
            
            # 清理临时目录（如果为空）
            try:
                temp_dir.rmdir()
            except OSError:
                pass  # 目录不为空，忽略
                
        except Exception as e:
            raise Exception(f"文件操作模拟失败: {e}")
    
    def _monitor_system(self):
        """监控系统资源"""
        while self.running:
            try:
                # 获取内存使用情况
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                # 获取CPU使用情况
                cpu_percent = process.cpu_percent()
                
                # 记录数据
                timestamp = time.time()
                self.memory_samples.append({
                    'timestamp': timestamp,
                    'memory_mb': memory_mb,
                    'datetime': datetime.now().isoformat()
                })
                
                self.cpu_samples.append({
                    'timestamp': timestamp,
                    'cpu_percent': cpu_percent,
                    'datetime': datetime.now().isoformat()
                })
                
                # 检查内存泄漏
                if len(self.memory_samples) > 10:
                    recent_memory = [s['memory_mb'] for s in self.memory_samples[-10:]]
                    memory_trend = recent_memory[-1] - recent_memory[0]
                    
                    if memory_trend > 100:  # 内存增长超过100MB
                        self.warnings.append(f"检测到可能的内存泄漏，增长: {memory_trend:.1f}MB")
                
                time.sleep(30)  # 每30秒采样一次
                
            except Exception as e:
                self.warnings.append(f"监控系统时发生错误: {e}")
                time.sleep(60)  # 发生错误时等待更长时间
    
    def _generate_stability_report(self):
        """生成稳定性测试报告"""
        if not self.start_time or not self.end_time:
            print("❌ 无法生成报告：测试时间信息不完整")
            return
        
        actual_duration = (self.end_time - self.start_time).total_seconds()
        
        # 计算统计数据
        if self.memory_samples:
            memory_values = [s['memory_mb'] for s in self.memory_samples]
            memory_stats = {
                'initial_mb': memory_values[0],
                'final_mb': memory_values[-1],
                'peak_mb': max(memory_values),
                'average_mb': sum(memory_values) / len(memory_values),
                'memory_growth_mb': memory_values[-1] - memory_values[0]
            }
        else:
            memory_stats = {'error': 'No memory data collected'}
        
        if self.cpu_samples:
            cpu_values = [s['cpu_percent'] for s in self.cpu_samples]
            cpu_stats = {
                'average_cpu': sum(cpu_values) / len(cpu_values),
                'peak_cpu': max(cpu_values)
            }
        else:
            cpu_stats = {'error': 'No CPU data collected'}
        
        if self.performance_samples:
            cycle_times = [s['duration'] for s in self.performance_samples]
            performance_stats = {
                'total_cycles': len(cycle_times),
                'average_cycle_time': sum(cycle_times) / len(cycle_times),
                'slowest_cycle_time': max(cycle_times)
            }
        else:
            performance_stats = {'error': 'No performance data collected'}
        
        # 生成报告
        report = {
            'test_info': {
                'planned_duration_hours': self.duration_hours,
                'actual_duration_seconds': actual_duration,
                'actual_duration_hours': actual_duration / 3600,
                'completion_rate': f"{(actual_duration / self.duration_seconds * 100):.1f}%",
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat()
            },
            'stability_metrics': {
                'memory_stats': memory_stats,
                'cpu_stats': cpu_stats,
                'performance_stats': performance_stats,
                'error_count': self.error_count,
                'warning_count': len(self.warnings)
            },
            'warnings': self.warnings,
            'raw_data': {
                'memory_samples_count': len(self.memory_samples),
                'cpu_samples_count': len(self.cpu_samples),
                'performance_samples_count': len(self.performance_samples)
            }
        }
        
        # 保存报告
        report_file = PROJECT_ROOT / f"test_output/stability_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        print("\n" + "="*60)
        print("📊 稳定性测试报告摘要")
        print("="*60)
        print(f"计划时长: {self.duration_hours}小时")
        print(f"实际时长: {actual_duration/3600:.1f}小时")
        print(f"完成率: {(actual_duration / self.duration_seconds * 100):.1f}%")
        
        if 'memory_growth_mb' in memory_stats:
            print(f"内存增长: {memory_stats['memory_growth_mb']:.1f}MB")
            print(f"峰值内存: {memory_stats['peak_mb']:.1f}MB")
        
        print(f"错误次数: {self.error_count}")
        print(f"警告次数: {len(self.warnings)}")
        print(f"报告文件: {report_file}")
        
        # 评估稳定性
        stability_score = self._calculate_stability_score(report)
        print(f"稳定性评分: {stability_score}/100")
        
        return report
    
    def _calculate_stability_score(self, report):
        """计算稳定性评分"""
        score = 100
        
        # 完成率扣分
        completion_rate = float(report['test_info']['completion_rate'].rstrip('%'))
        if completion_rate < 100:
            score -= (100 - completion_rate) * 0.5
        
        # 错误扣分
        score -= report['stability_metrics']['error_count'] * 10
        
        # 警告扣分
        score -= report['stability_metrics']['warning_count'] * 2
        
        # 内存增长扣分
        memory_stats = report['stability_metrics']['memory_stats']
        if 'memory_growth_mb' in memory_stats:
            if memory_stats['memory_growth_mb'] > 500:  # 内存增长超过500MB
                score -= 20
            elif memory_stats['memory_growth_mb'] > 200:  # 内存增长超过200MB
                score -= 10
        
        return max(0, int(score))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 长期稳定性测试')
    parser.add_argument('--hours', type=int, default=8, help='测试时长（小时），默认8小时')
    parser.add_argument('--quick', action='store_true', help='快速测试模式（5分钟）')
    
    args = parser.parse_args()
    
    if args.quick:
        duration = 5 / 60  # 5分钟转换为小时
        print("🚀 启动快速稳定性测试（5分钟）")
    else:
        duration = args.hours
        print(f"🚀 启动{duration}小时稳定性测试")
    
    # 创建并运行测试
    test = LongTermStabilityTest(duration_hours=duration)
    test.run_stability_test()


if __name__ == "__main__":
    main()
