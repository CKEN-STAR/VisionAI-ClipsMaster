#!/usr/bin/env python
"""基准测试运行脚本

此脚本用于运行所有基准测试并生成性能报告。
"""

import os
import sys
import argparse
import time
from pathlib import Path

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.benchmarks.benchmark_runner import BenchmarkRunner
from loguru import logger


def setup_logger(log_level="INFO"):
    """设置日志记录器
    
    Args:
        log_level: 日志级别
    """
    logger.remove()  # 移除默认处理程序
    
    # 添加控制台处理程序
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # 添加文件处理程序
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level
    )
    
    return log_file


def parse_args():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 性能基准测试工具")
    
    parser.add_argument("--output", "-o", default="benchmark_results", 
                        help="测试结果输出目录")
    
    parser.add_argument("--test-type", "-t", choices=["all", "device", "inference", "quality"], 
                        default="all", help="测试类型")
    
    parser.add_argument("--iterations", "-i", type=int, default=5, 
                        help="每项测试的迭代次数")
    
    parser.add_argument("--no-warmup", action="store_true", 
                        help="禁用预热")
    
    parser.add_argument("--quant-levels", nargs="+", 
                        default=["Q2_K", "Q4_K_M", "Q5_K", "Q6_K", "Q8_0"],
                        help="要测试的量化级别")
    
    parser.add_argument("--batch-sizes", nargs="+", type=int, 
                        default=[1, 2, 4, 8, 16],
                        help="要测试的批处理大小")
    
    parser.add_argument("--samples-dir", default="test/samples",
                        help="测试样本目录")
    
    parser.add_argument("--golden-dir", default="test/golden_samples",
                        help="黄金样本目录")
    
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="日志级别")
                        
    parser.add_argument("--simulate", action="store_true",
                        help="模拟模式，不实际加载模型")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    log_file = setup_logger(args.log_level)
    logger.info(f"日志将保存到: {log_file}")
    
    # 初始化基准测试运行器
    runner = BenchmarkRunner(output_dir=args.output)
    
    # 更新配置
    runner.config["test_iterations"] = args.iterations
    runner.config["warm_up"] = not args.no_warmup
    runner.config["quantization_levels"] = args.quant_levels
    runner.config["batch_sizes"] = args.batch_sizes
    runner.config["test_samples_dir"] = args.samples_dir
    runner.config["golden_samples_dir"] = args.golden_dir
    runner.config["simulate_mode"] = args.simulate  # 添加模拟模式配置
    
    # 根据测试类型运行测试
    start_time = time.time()
    
    try:
        if args.test_type == "device":
            runner.run_device_benchmark()
        elif args.test_type == "inference":
            runner.run_inference_benchmark()
        elif args.test_type == "quality":
            runner.run_quality_benchmark()
        else:  # all
            runner.run_all_benchmarks()
        
        # 生成报告
        report = runner.generate_comprehensive_report()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"基准测试完成，耗时: {duration:.2f}秒")
        logger.info(f"报告保存在: {runner.run_dir}")
        
        # 打印关键结果
        if "system_info" in report:
            logger.info(f"系统性能等级: {report['system_info'].get('performance_level', 'unknown')}")
            logger.info(f"系统性能得分: {report['system_info'].get('total_score', 0):.2f}")
        
        # 打印建议
        if "recommendations" in report:
            logger.info("优化建议:")
            for i, rec in enumerate(report["recommendations"][:5], 1):  # 只显示前5条
                logger.info(f"{i}. {rec}")
            
            if len(report["recommendations"]) > 5:
                logger.info(f"... 共 {len(report['recommendations'])} 条建议，详见报告")
        
    except Exception as e:
        logger.error(f"基准测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 