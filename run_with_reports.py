#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试报告生成工具

此脚本用于运行UI测试并生成交互报告，方便用户执行测试并查看结果。
"""

import os
import sys
import time
import logging
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("report_generator")

# 导入测试模块
try:
    from tests.interaction.report_generator import InteractiveReport
    from tests.interaction.ui_test_runner import UITestRunner
    from tests.interaction.accessibility import A11yValidator
    from tests.interaction.performance_bench import PerformanceBenchmark
    HAS_TEST_MODULES = True
except ImportError as e:
    logger.error(f"导入测试模块失败: {e}")
    HAS_TEST_MODULES = False

# 尝试导入PyQt
try:
    from PyQt6.QtWidgets import QApplication
    HAS_PYQT6 = True
    HAS_PYQT5 = False
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        HAS_PYQT6 = False
        HAS_PYQT5 = True
    except ImportError:
        logger.error("未找到PyQt库，无法运行UI测试")
        HAS_PYQT6 = False
        HAS_PYQT5 = False

def run_tests_with_report(args):
    """运行测试并生成报告
    
    Args:
        args: 命令行参数
    """
    if not HAS_TEST_MODULES:
        logger.error("缺少必要的测试模块，无法运行测试")
        return
    
    if not (HAS_PYQT6 or HAS_PYQT5):
        logger.error("未找到PyQt库，无法运行UI测试")
        return
    
    # 创建QApplication实例
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建报告对象
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = InteractiveReport(f"VisionAI-ClipsMaster 交互测试报告 - {timestamp}")
    
    logger.info("开始运行UI测试...")
    
    # 运行UI测试
    if args.run_ui_tests:
        ui_runner = UITestRunner(app=app, report_dir=args.output_dir)
        ui_runner.report = report
        test_results = ui_runner.run_tests(
            test_pattern=args.test_pattern,
            include_tags=args.include_tags,
            exclude_tags=args.exclude_tags
        )
        logger.info(f"UI测试完成，测试结果: {test_results}")
    
    # 运行可访问性测试
    if args.run_accessibility:
        logger.info("开始运行可访问性测试...")
        
        # 尝试导入简易UI
        try:
            from simple_ui import SimpleScreenplayApp
            window = SimpleScreenplayApp()
            window.show()
            
            # 运行可访问性验证
            validator = A11yValidator(app=app, level=args.wcag_level, report=report)
            compliance = validator.validate_compliance(window)
            
            logger.info(f"可访问性测试完成，合规性: {compliance}")
            
            # 关闭窗口
            window.close()
        except ImportError as e:
            logger.error(f"导入SimpleScreenplayApp失败: {e}")
    
    # 运行性能测试
    if args.run_performance:
        logger.info("开始运行性能测试...")
        
        # 尝试导入简易UI
        try:
            from simple_ui import SimpleScreenplayApp
            window = SimpleScreenplayApp()
            window.show()
            
            # 运行性能测试
            bench = PerformanceBenchmark(app=app, report=report)
            perf_results = bench.run_benchmark(
                "简易UI性能测试",
                window,
                duration=args.perf_duration,
                sample_interval=args.perf_interval
            )
            
            logger.info(f"性能测试完成，结果: {perf_results}")
            
            # 关闭窗口
            window.close()
        except ImportError as e:
            logger.error(f"导入SimpleScreenplayApp失败: {e}")
    
    # 生成报告
    html_path = report.generate_html_report(
        os.path.join(args.output_dir, f"interactive_{timestamp}.html")
    )
    json_path = report.save_json_report(
        os.path.join(args.output_dir, f"interactive_{timestamp}.json")
    )
    
    logger.info(f"HTML报告已生成: {html_path}")
    logger.info(f"JSON报告已保存: {json_path}")
    
    # 如果指定了自动打开报告，则打开
    if args.open_report:
        try:
            webbrowser.open(f"file://{os.path.abspath(html_path)}")
            logger.info("已在浏览器中打开报告")
        except Exception as e:
            logger.error(f"打开报告失败: {e}")
    
    return html_path, json_path

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试报告生成工具")
    
    # 测试选项
    parser.add_argument("--ui", dest="run_ui_tests", action="store_true",
                       help="运行UI测试")
    parser.add_argument("--accessibility", dest="run_accessibility", action="store_true",
                       help="运行可访问性测试")
    parser.add_argument("--performance", dest="run_performance", action="store_true",
                       help="运行性能测试")
    parser.add_argument("--all", dest="run_all", action="store_true",
                       help="运行所有测试")
    
    # UI测试选项
    parser.add_argument("--pattern", dest="test_pattern", default="test_*.py",
                       help="测试文件匹配模式")
    parser.add_argument("--include", dest="include_tags", default=None,
                       help="包含的测试标签（逗号分隔）")
    parser.add_argument("--exclude", dest="exclude_tags", default=None,
                       help="排除的测试标签（逗号分隔）")
    
    # 可访问性测试选项
    parser.add_argument("--wcag", dest="wcag_level", default="AA",
                       choices=["A", "AA", "AAA"],
                       help="WCAG合规级别")
    
    # 性能测试选项
    parser.add_argument("--duration", dest="perf_duration", type=float, default=10.0,
                       help="性能测试持续时间（秒）")
    parser.add_argument("--interval", dest="perf_interval", type=float, default=0.1,
                       help="性能采样间隔（秒）")
    
    # 输出选项
    parser.add_argument("--output", dest="output_dir", default="reports",
                       help="输出目录")
    parser.add_argument("--open", dest="open_report", action="store_true",
                       help="自动打开生成的报告")
    
    args = parser.parse_args()
    
    # 如果指定了run_all，则运行所有测试
    if args.run_all:
        args.run_ui_tests = True
        args.run_accessibility = True
        args.run_performance = True
    
    # 如果没有指定任何测试，默认运行所有测试
    if not (args.run_ui_tests or args.run_accessibility or args.run_performance):
        args.run_ui_tests = True
        args.run_accessibility = True
        args.run_performance = True
    
    # 处理include_tags和exclude_tags
    if args.include_tags:
        args.include_tags = [tag.strip() for tag in args.include_tags.split(",")]
    if args.exclude_tags:
        args.exclude_tags = [tag.strip() for tag in args.exclude_tags.split(",")]
    
    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 运行测试并生成报告
    run_tests_with_report(args)

if __name__ == "__main__":
    main() 