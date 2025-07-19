#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
边界条件测试运行脚本

此脚本用于运行视频处理边界条件专项测试，并生成详细报告
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
import subprocess
import datetime

# 添加项目根目录到导入路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# 测试配置
TEST_RESOURCES_DIR = project_root / "tests" / "resources"
TEST_OUTPUT_DIR = project_root / "tests" / "output"
TEST_REPORTS_DIR = project_root / "tests" / "reports"

# 边界条件测试文件
EDGE_CASE_TEST_FILE = project_root / "tests" / "unit_test" / "test_edge_cases.py"

# 确保测试目录存在
TEST_RESOURCES_DIR.mkdir(exist_ok=True, parents=True)
TEST_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
TEST_REPORTS_DIR.mkdir(exist_ok=True, parents=True)


def run_edge_tests(verbose=True, html_report=True):
    """
    运行边界条件测试
    
    Args:
        verbose: 是否显示详细测试输出
        html_report: 是否生成HTML报告
        
    Returns:
        成功与否，测试结果
    """
    print("正在运行视频处理边界条件测试...")
    
    # 构建命令参数
    cmd = ["pytest"]
    
    # 添加测试文件
    cmd.append(str(EDGE_CASE_TEST_FILE))
    
    # 设置详细度
    if verbose:
        cmd.append("-v")
    
    # 添加HTML报告
    if html_report:
        report_path = TEST_REPORTS_DIR / f"edge_case_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        cmd.extend(["--html", str(report_path), "--self-contained-html"])
    
    # 添加JUnit报告用于CI/CD集成
    junit_path = TEST_REPORTS_DIR / "edge_case_junit.xml"
    cmd.extend(["--junitxml", str(junit_path)])
    
    # 运行测试
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        # 解析测试结果
        success = result.returncode == 0
        
        # 如果测试成功
        if success:
            print("✅ 边界条件测试全部通过！")
            if html_report:
                print(f"HTML报告生成于: {report_path}")
        else:
            print("❌ 边界条件测试存在失败项！")
            print(result.stdout)
            print(result.stderr)
            if html_report:
                print(f"HTML报告生成于: {report_path}")
        
        # 记录测试结果摘要
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "success": success,
            "report_path": str(report_path) if html_report else None,
            "junit_path": str(junit_path)
        }
        
        # 写入结果摘要
        summary_path = TEST_REPORTS_DIR / "edge_case_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return success, summary
        
    except Exception as e:
        print(f"测试运行失败: {str(e)}")
        return False, {"error": str(e)}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="边界条件测试运行工具")
    parser.add_argument("--no-verbose", action="store_true", help="不显示详细测试输出")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    
    args = parser.parse_args()
    
    # 运行边界条件测试
    success, summary = run_edge_tests(
        verbose=not args.no_verbose,
        html_report=not args.no_html
    )
    
    # 设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 