#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
覆盖率强制检查脚本
用于CI/CD流程中进行代码覆盖率检查，确保不同模块达到指定的覆盖率阈值
"""

import os
import sys
import json
import argparse
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Set

# 添加项目根目录到导入路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# 覆盖率阈值配置
COVERAGE_THRESHOLDS = {
    "core": 95.0,   # 核心模块覆盖率要求
    "utils": 95.0,  # 工具模块覆盖率要求
    "api": 80.0,    # API模块覆盖率要求
    "exporters": 80.0,  # 导出器模块覆盖率要求
    "default": 70.0  # 默认覆盖率要求
}

# 模块路径映射
MODULE_PATHS = {
    "core": "src/core",
    "utils": "src/utils",
    "api": "src/api",
    "exporters": "src/exporters"
}


def run_coverage_tests(test_dirs: List[str], output_dir: str = "coverage_reports") -> Tuple[bool, str]:
    """
    运行pytest覆盖率测试并生成报告
    
    Args:
        test_dirs: 测试目录列表
        output_dir: 输出目录
        
    Returns:
        成功与否，报告路径
    """
    # 确保输出目录存在
    output_path = project_root / output_dir
    output_path.mkdir(exist_ok=True, parents=True)
    
    xml_report = output_path / "coverage.xml"
    html_report_dir = output_path / "html"
    
    # 拼接测试目录参数
    test_paths = " ".join([str(project_root / test_dir) for test_dir in test_dirs])
    
    # 使用subprocess执行pytest命令
    try:
        cmd = (
            f"python -m pytest {test_paths} "
            f"--cov=src "
            f"--cov-report=xml:{xml_report} "
            f"--cov-report=html:{html_report_dir} "
            f"--cov-report=term "
        )
        
        print(f"执行覆盖率测试: {cmd}")
        
        # 设置环境变量解决编码问题
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=project_root,
            capture_output=True, 
            text=True,
            env=env
        )
        
        if result.returncode != 0:
            print(f"测试执行失败:\n{result.stderr}")
            return False, ""
        
        return True, str(xml_report)
    except Exception as e:
        print(f"运行测试时出错: {str(e)}")
        return False, ""


def parse_coverage_xml(xml_path: str) -> Dict[str, Dict]:
    """
    解析XML格式的覆盖率报告
    
    Args:
        xml_path: XML报告路径
        
    Returns:
        解析后的覆盖率数据，按模块分组
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # 提取整体覆盖率
        overall_coverage = float(root.attrib.get('line-rate', '0')) * 100
        
        # 按模块收集覆盖率数据
        module_data = {}
        
        # 处理每个文件的覆盖率
        for class_element in root.findall('.//class'):
            filename = class_element.attrib.get('filename', '')
            
            # 跳过非项目文件
            if not filename.startswith('src/'):
                continue
            
            # 计算文件覆盖率
            lines = class_element.findall('./lines/line')
            total_lines = len(lines)
            covered_lines = sum(1 for line in lines if line.attrib.get('hits', '0') != '0')
            
            if total_lines > 0:
                file_coverage = (covered_lines / total_lines) * 100
            else:
                file_coverage = 0.0
            
            # 添加到模块数据
            module_data[filename] = {
                'coverage': file_coverage,
                'covered_lines': covered_lines,
                'total_lines': total_lines,
                'missing_lines': [int(line.attrib.get('number')) for line in lines if line.attrib.get('hits', '0') == '0']
            }
        
        # 按模块分组统计
        grouped_data = {
            'overall': {
                'coverage': overall_coverage
            }
        }
        
        # 针对不同模块计算覆盖率
        for module_name, module_path in MODULE_PATHS.items():
            module_files = [f for f in module_data.keys() if f.startswith(module_path)]
            
            if module_files:
                total_covered = sum(module_data[f]['covered_lines'] for f in module_files)
                total_lines = sum(module_data[f]['total_lines'] for f in module_files)
                
                if total_lines > 0:
                    module_coverage = (total_covered / total_lines) * 100
                else:
                    module_coverage = 0.0
                
                grouped_data[module_name] = {
                    'coverage': module_coverage,
                    'covered_lines': total_covered,
                    'total_lines': total_lines,
                    'files': module_files
                }
        
        return grouped_data
        
    except Exception as e:
        print(f"解析覆盖率报告时出错: {str(e)}")
        return {'overall': {'coverage': 0.0}}


def check_coverage_thresholds(coverage_data: Dict[str, Dict]) -> Tuple[bool, List[str]]:
    """
    检查覆盖率数据是否达到阈值要求
    
    Args:
        coverage_data: 覆盖率数据
        
    Returns:
        是否全部通过，失败模块列表
    """
    all_passed = True
    failed_modules = []
    
    # 输出覆盖率检查结果表格
    print("\n覆盖率检查结果:")
    print("-" * 60)
    print(f"{'模块':<15} {'覆盖率':<10} {'阈值':<10} {'状态':<10}")
    print("-" * 60)
    
    # 检查每个模块
    for module_name in coverage_data:
        if module_name == 'overall':
            continue
            
        coverage = coverage_data[module_name]['coverage']
        threshold = COVERAGE_THRESHOLDS.get(module_name, COVERAGE_THRESHOLDS['default'])
        
        # 判断是否通过
        passed = coverage >= threshold
        status = "✅ 通过" if passed else "❌ 失败"
        
        # 输出结果
        print(f"{module_name:<15} {coverage:.2f}%{' ':<10} {threshold:.2f}%{' ':<10} {status}")
        
        if not passed:
            all_passed = False
            failed_modules.append(module_name)
    
    # 输出整体结果
    overall_coverage = coverage_data['overall']['coverage']
    print("-" * 60)
    print(f"{'整体覆盖率':<15} {overall_coverage:.2f}%")
    print("-" * 60)
    
    return all_passed, failed_modules


def generate_coverage_badge(coverage: float, output_path: str) -> None:
    """
    生成覆盖率徽章的JSON文件(用于CI/CD展示)
    
    Args:
        coverage: 覆盖率数值
        output_path: 输出路径
    """
    # 颜色判断
    if coverage >= 90:
        color = "brightgreen"
    elif coverage >= 80:
        color = "green"
    elif coverage >= 70:
        color = "yellowgreen"
    elif coverage >= 60:
        color = "yellow"
    else:
        color = "red"
    
    # 创建徽章数据
    data = {
        "schemaVersion": 1,
        "label": "coverage",
        "message": f"{coverage:.1f}%",
        "color": color
    }
    
    # 写入JSON文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        print(f"已生成覆盖率徽章: {output_path}")
    except Exception as e:
        print(f"生成覆盖率徽章时出错: {str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="代码覆盖率强制检查工具")
    parser.add_argument('--test-dirs', nargs='+', default=['tests/unit_test'], 
                        help='测试目录列表(默认: tests/unit_test)')
    parser.add_argument('--output-dir', default='coverage_reports',
                        help='输出目录(默认: coverage_reports)')
    parser.add_argument('--badge', default='coverage_badge.json',
                        help='徽章JSON文件路径(默认: coverage_badge.json)')
    parser.add_argument('--strict', action='store_true',
                        help='严格模式，如果覆盖率未达标则返回非零退出码')
    
    args = parser.parse_args()
    
    # 运行覆盖率测试
    success, report_path = run_coverage_tests(args.test_dirs, args.output_dir)
    
    if not success or not report_path:
        print("覆盖率测试运行失败")
        sys.exit(1)
    
    # 解析覆盖率报告
    coverage_data = parse_coverage_xml(report_path)
    
    # 检查覆盖率阈值
    all_passed, failed_modules = check_coverage_thresholds(coverage_data)
    
    # 生成徽章
    overall_coverage = coverage_data['overall']['coverage']
    badge_path = os.path.join(args.output_dir, args.badge)
    generate_coverage_badge(overall_coverage, badge_path)
    
    # 输出总结信息
    if all_passed:
        print("\n✅ 恭喜！所有模块的覆盖率均达到了要求阈值。")
    else:
        print("\n❌ 注意：以下模块的覆盖率未达标：")
        for module in failed_modules:
            threshold = COVERAGE_THRESHOLDS.get(module, COVERAGE_THRESHOLDS['default'])
            current = coverage_data[module]['coverage']
            print(f"  - {module}: 当前 {current:.2f}%, 要求 {threshold:.2f}%")
    
    # 严格模式下，未达标则返回错误码
    if args.strict and not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main() 