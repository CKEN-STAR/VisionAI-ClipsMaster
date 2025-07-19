#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 硬件测试运行脚本
用于运行自适应测试框架的测试
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('tests', 'logs', 'hardware_test_run.log'))
    ]
)
logger = logging.getLogger('hardware_test_run')

# 确保日志目录存在
os.makedirs(os.path.join('tests', 'logs'), exist_ok=True)


def main():
    """主函数，解析命令行参数并运行测试"""
    parser = argparse.ArgumentParser(description='VisionAI-ClipsMaster 硬件自适应测试')
    
    # 添加命令行参数
    parser.add_argument('--test-type', choices=['all', 'render', 'memory', 'compute', 'disk', 'input', 'comparison', 'stress'],
                        default='all', help='测试类型')
    parser.add_argument('--profile', choices=['low', 'medium', 'high'],
                        default='medium', help='硬件配置')
    parser.add_argument('--duration', type=int, default=60,
                        help='压力测试持续时间（秒）')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 导入测试模块
    try:
        from tests.hardware_test.run_adaptive_tests import (
            run_all_tests, run_specific_test, run_profile_comparison, run_stress_test
        )
        
        logger.info(f"开始运行硬件自适应测试，类型: {args.test_type}, 配置: {args.profile}")
        
        # 运行测试
        start_time = time.time()
        
        if args.test_type == 'all':
            report = run_all_tests()
            logger.info("所有测试完成")
        elif args.test_type == 'comparison':
            report = run_profile_comparison()
            logger.info("配置比较测试完成")
        elif args.test_type == 'stress':
            report = run_stress_test(args.duration)
            logger.info(f"压力测试完成，持续时间: {args.duration}秒")
        else:
            report = run_specific_test(args.test_type, args.profile)
            logger.info(f"{args.test_type}测试完成")
        
        # 计算运行时间
        run_time = time.time() - start_time
        logger.info(f"测试运行时间: {run_time:.2f}秒")
        
        # 输出报告摘要
        if report:
            print("\n=== 测试报告摘要 ===")
            if "timestamp" in report:
                print(f"时间戳: {report['timestamp']}")
            if "results" in report:
                print("\n性能结果:")
                for metric_type, values in report["results"].items():
                    print(f"- {metric_type}: {values}")
            if "scores" in report:
                print("\n性能评分:")
                for profile, score in report["scores"].items():
                    if isinstance(score, dict) and "total" in score:
                        print(f"- {profile}: {score['total']:.2f}")
                    else:
                        print(f"- {profile}: {score}")
        
    except ImportError as e:
        logger.error(f"导入测试模块失败: {e}")
        print(f"错误: 导入测试模块失败: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"错误: 测试运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 