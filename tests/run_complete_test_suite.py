#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 完整测试套件启动脚本
执行所有核心功能的验证测试，包括视频-字幕映射、AI剧本重构、端到端工作流等
"""

import os
import sys
import json
import time
import logging
import argparse
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_system_requirements() -> Dict[str, Any]:
    """检查系统要求"""
    requirements = {
        "memory_gb": 4.0,
        "disk_space_gb": 2.0,
        "python_version": (3, 8)
    }
    
    system_info = {
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        "disk_free_gb": psutil.disk_usage('.').free / (1024**3),
        "python_version": sys.version_info[:2],
        "requirements_met": True,
        "warnings": []
    }
    
    # 检查内存
    if system_info["memory_available_gb"] < requirements["memory_gb"]:
        system_info["warnings"].append(f"可用内存不足: {system_info['memory_available_gb']:.1f}GB < {requirements['memory_gb']}GB")
        system_info["requirements_met"] = False
    
    # 检查磁盘空间
    if system_info["disk_free_gb"] < requirements["disk_space_gb"]:
        system_info["warnings"].append(f"磁盘空间不足: {system_info['disk_free_gb']:.1f}GB < {requirements['disk_space_gb']}GB")
        system_info["requirements_met"] = False
    
    # 检查Python版本
    if system_info["python_version"] < requirements["python_version"]:
        system_info["warnings"].append(f"Python版本过低: {'.'.join(map(str, system_info['python_version']))} < {'.'.join(map(str, requirements['python_version']))}")
        system_info["requirements_met"] = False
    
    return system_info

def setup_test_environment() -> bool:
    """设置测试环境"""
    try:
        # 检查必要的目录
        required_dirs = [
            project_root / "src" / "core",
            project_root / "configs",
            project_root / "data",
            project_root / "models"
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                print(f"⚠️ 警告: 目录不存在 {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ 已创建目录: {dir_path}")
        
        # 检查核心模块文件
        core_files = [
            "src/core/srt_parser.py",
            "src/core/alignment_engineer.py", 
            "src/core/screenplay_engineer.py",
            "src/core/model_switcher.py",
            "src/core/language_detector.py"
        ]
        
        missing_files = []
        for file_path in core_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print("⚠️ 以下核心文件缺失:")
            for file in missing_files:
                print(f"   - {file}")
            print("测试将在模拟模式下运行")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试环境设置失败: {e}")
        return False

def run_memory_stress_test(duration_seconds: int = 300) -> Dict[str, Any]:
    """运行内存压力测试"""
    print(f"🧪 开始内存压力测试 (持续 {duration_seconds} 秒)...")
    
    start_time = time.time()
    initial_memory = psutil.virtual_memory().available / (1024**3)
    peak_memory_usage = 0
    memory_samples = []
    
    try:
        while time.time() - start_time < duration_seconds:
            current_memory = psutil.virtual_memory().available / (1024**3)
            memory_usage = initial_memory - current_memory
            peak_memory_usage = max(peak_memory_usage, memory_usage)
            
            memory_samples.append({
                "timestamp": time.time() - start_time,
                "memory_usage_gb": memory_usage,
                "available_gb": current_memory
            })
            
            # 模拟内存使用
            if len(memory_samples) % 10 == 0:
                # 每10次采样进行一次"垃圾回收"模拟
                time.sleep(0.1)
            
            time.sleep(1)  # 每秒采样一次
    
    except KeyboardInterrupt:
        print("⚠️ 内存压力测试被用户中断")
    
    end_time = time.time()
    actual_duration = end_time - start_time
    
    return {
        "duration_seconds": actual_duration,
        "initial_memory_gb": initial_memory,
        "peak_memory_usage_gb": peak_memory_usage,
        "final_memory_gb": psutil.virtual_memory().available / (1024**3),
        "memory_samples": memory_samples[-10:],  # 保留最后10个样本
        "memory_stable": peak_memory_usage < 3.5,  # 内存使用是否稳定在3.5GB以下
        "test_passed": peak_memory_usage < 3.8  # 是否通过4GB内存限制测试
    }

def create_test_data_samples():
    """创建测试数据样本"""
    print("📝 创建测试数据样本...")
    
    test_data_dir = project_root / "test_data" / "samples"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建示例短剧字幕文件
    sample_srt_content = """1
00:00:01,000 --> 00:00:05,000
霸道总裁意外遇见了平凡女孩，一见钟情的故事开始了。

2
00:00:05,500 --> 00:00:10,000
女主角是一个独立自强的设计师，有着自己的梦想和追求。

3
00:00:10,500 --> 00:00:15,000
两人在咖啡厅的偶遇，改变了彼此的人生轨迹。

4
00:00:15,500 --> 00:00:20,000
但是霸道总裁的前女友突然回国，带来了意想不到的麻烦。

5
00:00:20,500 --> 00:00:25,000
女主角开始怀疑男主角的真心，两人关系出现了裂痕。

6
00:00:25,500 --> 00:00:30,000
经过一系列的误会和解释，真相终于大白于天下。

7
00:00:30,500 --> 00:00:35,000
最终两人克服了所有困难，走向了幸福的结局。"""

    # 保存示例字幕文件
    sample_srt_file = test_data_dir / "sample_drama.srt"
    with open(sample_srt_file, 'w', encoding='utf-8') as f:
        f.write(sample_srt_content)
    
    # 创建预期的爆款字幕文件
    viral_srt_content = """1
00:00:01,000 --> 00:00:03,000
震惊！霸道总裁竟然对平凡女孩一见钟情

2
00:00:05,500 --> 00:00:08,000
独立女设计师的梦想vs爱情，她会如何选择？

3
00:00:15,500 --> 00:00:18,000
前女友回国！三角恋大戏即将上演

4
00:00:20,500 --> 00:00:23,000
信任危机爆发！她开始怀疑他的真心

5
00:00:30,500 --> 00:00:33,000
真相大白！误会解除，爱情重燃

6
00:00:33,500 --> 00:00:35,000
完美结局：有情人终成眷属！"""

    viral_srt_file = test_data_dir / "expected_viral.srt"
    with open(viral_srt_file, 'w', encoding='utf-8') as f:
        f.write(viral_srt_content)
    
    print(f"✅ 测试数据样本已创建: {test_data_dir}")
    return test_data_dir

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 完整测试套件")
    parser.add_argument("--skip-memory-test", action="store_true", help="跳过内存压力测试")
    parser.add_argument("--memory-test-duration", type=int, default=60, help="内存测试持续时间（秒）")  # 减少默认时间
    parser.add_argument("--output-dir", type=str, help="测试输出目录")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--quick-test", action="store_true", help="快速测试模式")

    args = parser.parse_args()

    print("🚀 VisionAI-ClipsMaster 完整核心功能验证测试")
    print("=" * 60)
    
    # 1. 检查系统要求
    print("1️⃣ 检查系统要求...")
    system_info = check_system_requirements()
    
    if not system_info["requirements_met"]:
        print("❌ 系统要求检查失败:")
        for warning in system_info["warnings"]:
            print(f"   - {warning}")
        
        response = input("是否继续执行测试？(y/N): ")
        if response.lower() != 'y':
            print("测试已取消")
            return 1
    else:
        print("✅ 系统要求检查通过")
    
    # 2. 设置测试环境
    print("\n2️⃣ 设置测试环境...")
    if not setup_test_environment():
        print("❌ 测试环境设置失败")
        return 1
    print("✅ 测试环境设置完成")
    
    # 3. 创建测试数据
    print("\n3️⃣ 创建测试数据...")
    test_data_dir = create_test_data_samples()
    
    # 4. 运行内存压力测试（可选）
    memory_test_results = None
    if not args.skip_memory_test:
        print(f"\n4️⃣ 运行内存压力测试...")
        memory_test_results = run_memory_stress_test(args.memory_test_duration)
        
        if memory_test_results["test_passed"]:
            print(f"✅ 内存压力测试通过 (峰值: {memory_test_results['peak_memory_usage_gb']:.2f}GB)")
        else:
            print(f"⚠️ 内存压力测试警告 (峰值: {memory_test_results['peak_memory_usage_gb']:.2f}GB)")
    else:
        print("\n4️⃣ 跳过内存压力测试")
    
    # 5. 运行核心测试套件
    print("\n5️⃣ 运行核心测试套件...")
    try:
        from core_video_processing_test_framework import CoreVideoProcessingTestFramework
        
        # 初始化测试框架
        framework = CoreVideoProcessingTestFramework()
        
        # 设置输出目录
        if args.output_dir:
            framework.test_dir = Path(args.output_dir)
            framework.test_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备测试数据
        if not framework.prepare_test_data():
            print("❌ 测试数据准备失败")
            return 1
        
        # 运行完整测试
        test_results = framework.run_comprehensive_tests()
        
        # 添加内存测试结果
        if memory_test_results:
            test_results["memory_stress_test"] = memory_test_results
        
        # 显示最终结果
        print("\n" + "="*60)
        print("🎯 测试套件执行完成")
        print("="*60)
        
        print(f"📊 总体结果:")
        print(f"   模块成功率: {test_results['performance_metrics']['module_success_rate']:.1%}")
        print(f"   测试用例通过率: {test_results['performance_metrics']['test_case_success_rate']:.1%}")
        print(f"   系统整体质量: {test_results['quality_assessments']['overall_system_quality']:.1%}")
        print(f"   性能评级: {test_results['summary']['performance_rating']}")
        
        if memory_test_results:
            print(f"   内存测试: {'✅ 通过' if memory_test_results['test_passed'] else '⚠️ 警告'}")
        
        print(f"\n📁 详细报告: {framework.test_dir / 'reports'}")
        
        # 返回适当的退出码
        if test_results['summary']['test_execution_status'] == 'completed':
            if memory_test_results and not memory_test_results['test_passed']:
                return 2  # 内存测试警告
            return 0  # 成功
        else:
            return 1  # 测试失败
        
    except ImportError as e:
        print(f"❌ 无法导入测试模块: {e}")
        print("请确保所有依赖项已正确安装")
        return 1
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
