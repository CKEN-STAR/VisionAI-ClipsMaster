#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 测试文档生成器

该脚本自动生成测试文档，包括：
1. 测试结构和统计信息
2. 测试类别和测试用例列表
3. 测试覆盖率报告
4. 测试结果摘要
"""

import os
import sys
import time
import glob
import json
import argparse
import importlib
import unittest
import textwrap
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any

# 项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent

# 报告目录
REPORTS_DIR = PROJECT_ROOT / "tests" / "reports"
DOCS_DIR = PROJECT_ROOT / "docs" / "tests"

# 确保目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# 文档文件路径
TEST_STRUCTURE_MD = DOCS_DIR / "TEST_STRUCTURE.md"
TEST_COVERAGE_MD = DOCS_DIR / "TEST_COVERAGE.md"
TEST_CASES_MD = DOCS_DIR / "TEST_CASES.md"
TEST_INDEX_MD = DOCS_DIR / "README.md"

def generate_test_structure_doc() -> None:
    """生成测试结构文档"""
    tests_dir = PROJECT_ROOT / "tests"
    
    # 查找所有测试目录
    test_dirs = [d for d in tests_dir.glob("*") if d.is_dir() and not d.name.startswith("__")]
    
    with open(TEST_STRUCTURE_MD, "w", encoding="utf-8") as f:
        f.write("# VisionAI-ClipsMaster 测试结构\n\n")
        f.write("本文档描述了项目的测试结构和组织方式。\n\n")
        
        # 测试目录总览
        f.write("## 测试目录结构\n\n")
        f.write("```\n")
        f.write("tests/\n")
        
        for test_dir in sorted(test_dirs):
            rel_path = test_dir.relative_to(tests_dir)
            f.write(f"├── {rel_path}/\n")
            
            # 查找子目录
            subdirs = [d for d in test_dir.glob("*") if d.is_dir() and not d.name.startswith("__")]
            for i, subdir in enumerate(sorted(subdirs)):
                prefix = "│   ├── " if i < len(subdirs) - 1 else "│   └── "
                subdir_rel = subdir.relative_to(test_dir)
                f.write(f"{prefix}{subdir_rel}/\n")
                
        f.write("```\n\n")
        
        # 测试类别描述
        f.write("## 测试类别说明\n\n")
        
        categories = {
            "unit": "单元测试，验证各个独立组件的功能",
            "functional": "功能测试，验证系统完整功能",
            "integration": "集成测试，验证组件之间的交互",
            "performance": "性能测试，评估系统性能和效率",
            "memory": "内存测试，确保系统在低配置环境下正常运行",
            "benchmarks": "基准测试，建立性能基准并监控变化",
            "security": "安全测试，验证系统安全性",
            "golden_samples": "黄金样本测试数据，提供参考基准",
            "utils": "测试工具函数",
        }
        
        for test_dir in sorted(test_dirs):
            dir_name = test_dir.name
            description = categories.get(dir_name, "")
            
            f.write(f"### {dir_name}\n\n")
            if description:
                f.write(f"{description}\n\n")
            
            # 统计测试文件和测试用例数量
            test_files = list(test_dir.glob("test_*.py"))
            test_count = len(test_files)
            
            f.write(f"- 测试文件数量: {test_count}\n")
            if test_files:
                f.write("- 主要测试文件:\n")
                for test_file in sorted(test_files)[:5]:  # 只显示前5个
                    rel_path = test_file.relative_to(PROJECT_ROOT)
                    f.write(f"  - `{rel_path}`\n")
                if len(test_files) > 5:
                    f.write(f"  - *... 以及 {len(test_files) - 5} 个其他文件*\n")
            f.write("\n")
        
        # 测试统计信息
        f.write("## 测试统计\n\n")
        
        total_tests = len(list(tests_dir.glob("**/test_*.py")))
        total_dirs = len(test_dirs)
        
        f.write(f"- 测试目录数量: {total_dirs}\n")
        f.write(f"- 测试文件总数: {total_tests}\n")
        
        # 添加更新时间
        f.write("\n---\n\n")
        f.write(f"*文档生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    print(f"已生成测试结构文档: {TEST_STRUCTURE_MD}")

def run_coverage_report() -> bool:
    """运行测试覆盖率报告"""
    try:
        coverage_cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--cov=src",
            "--cov-report=xml:tests/reports/coverage.xml",
            "--cov-report=html:tests/reports/coverage",
            "--quiet"
        ]
        
        print("正在运行覆盖率测试，请稍候...")
        process = subprocess.run(coverage_cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            print(f"覆盖率测试运行失败: {process.stderr}")
            return False
            
        return True
    except Exception as e:
        print(f"运行覆盖率报告时出错: {e}")
        return False

def generate_coverage_doc() -> None:
    """生成测试覆盖率文档"""
    # 检查覆盖率文件是否存在
    coverage_xml = REPORTS_DIR / "coverage.xml"
    
    if not coverage_xml.exists():
        if not run_coverage_report():
            print("无法生成覆盖率报告，跳过覆盖率文档生成")
            return
    
    # 解析覆盖率数据
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(coverage_xml)
        root = tree.getroot()
        
        # 提取整体覆盖率
        overall_coverage = float(root.get("line-rate", "0")) * 100
        
        # 提取各个包的覆盖率
        packages = []
        for package in root.findall(".//package"):
            package_name = package.get("name")
            package_coverage = float(package.get("line-rate", "0")) * 100
            
            # 计算该包中的行数、覆盖行和未覆盖行
            total_lines = 0
            covered_lines = 0
            
            for cls in package.findall(".//class"):
                lines = cls.findall(".//line")
                total_lines += len(lines)
                covered_lines += sum(1 for line in lines if line.get("hits") != "0")
            
            packages.append({
                "name": package_name,
                "coverage": package_coverage,
                "total_lines": total_lines,
                "covered_lines": covered_lines,
                "missed_lines": total_lines - covered_lines
            })
        
        # 按照覆盖率排序
        packages.sort(key=lambda x: x["coverage"], reverse=True)
        
        # 生成文档
        with open(TEST_COVERAGE_MD, "w", encoding="utf-8") as f:
            f.write("# VisionAI-ClipsMaster 测试覆盖率报告\n\n")
            f.write("本文档提供了项目的测试覆盖率分析。\n\n")
            
            # 整体覆盖率
            f.write(f"## 整体覆盖率: {overall_coverage:.2f}%\n\n")
            
            # 各个包的覆盖率
            f.write("## 各模块覆盖率\n\n")
            
            f.write("| 模块 | 覆盖率 | 总行数 | 已覆盖行数 | 未覆盖行数 |\n")
            f.write("|------|--------|--------|------------|------------|\n")
            
            for package in packages:
                f.write(f"| {package['name']} | {package['coverage']:.2f}% | ")
                f.write(f"{package['total_lines']} | {package['covered_lines']} | ")
                f.write(f"{package['missed_lines']} |\n")
            
            # 添加覆盖率标准说明
            f.write("\n## 覆盖率标准\n\n")
            f.write("项目测试覆盖率目标：\n\n")
            f.write("- 核心功能模块: ≥ 90%\n")
            f.write("- 辅助功能模块: ≥ 75%\n")
            f.write("- 整体覆盖率: ≥ 80%\n\n")
            
            # 添加覆盖率报告链接
            f.write("## 详细覆盖率报告\n\n")
            f.write("完整的 HTML 格式覆盖率报告位于：\n\n")
            f.write("```\n")
            f.write("tests/reports/coverage/index.html\n")
            f.write("```\n\n")
            
            # 添加查看报告的命令
            f.write("可以通过以下命令生成并查看最新的覆盖率报告：\n\n")
            f.write("```bash\n")
            f.write("pytest --cov=src --cov-report=html tests/\n")
            f.write("# 然后在浏览器中打开 tests/reports/coverage/index.html\n")
            f.write("```\n\n")
            
            # 添加更新时间
            f.write("---\n\n")
            f.write(f"*报告生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        print(f"已生成测试覆盖率文档: {TEST_COVERAGE_MD}")
    except Exception as e:
        print(f"生成覆盖率文档时出错: {e}")

def collect_test_cases() -> List[Dict[str, Any]]:
    """收集所有测试用例信息"""
    tests_dir = PROJECT_ROOT / "tests"
    test_files = list(tests_dir.glob("**/test_*.py"))
    
    all_tests = []
    
    for test_file in test_files:
        # 跳过__pycache__和.pytest_cache目录
        if "__pycache__" in str(test_file) or ".pytest_cache" in str(test_file):
            continue
            
        rel_path = test_file.relative_to(PROJECT_ROOT)
        module_path = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")
        
        try:
            # 尝试导入模块
            spec = importlib.util.spec_from_file_location(module_path, test_file)
            if not spec or not spec.loader:
                continue
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找测试类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if isinstance(attr, type) and issubclass(attr, unittest.TestCase) and attr != unittest.TestCase:
                    test_class = attr
                    
                    # 提取测试类文档字符串
                    class_doc = test_class.__doc__ or ""
                    class_doc = textwrap.dedent(class_doc).strip()
                    
                    # 查找测试方法
                    test_methods = []
                    for method_name in dir(test_class):
                        if method_name.startswith("test_"):
                            method = getattr(test_class, method_name)
                            
                            # 提取方法文档字符串
                            method_doc = method.__doc__ or ""
                            method_doc = textwrap.dedent(method_doc).strip()
                            
                            test_methods.append({
                                "name": method_name,
                                "doc": method_doc
                            })
                    
                    if test_methods:
                        category = str(rel_path.parent.name)
                        if category == "tests":
                            category = "root"
                            
                        all_tests.append({
                            "file": str(rel_path),
                            "class": attr_name,
                            "category": category,
                            "doc": class_doc,
                            "methods": test_methods
                        })
        except Exception as e:
            print(f"分析测试文件 {test_file} 时出错: {e}")
    
    return all_tests

def generate_test_cases_doc() -> None:
    """生成测试用例文档"""
    test_cases = collect_test_cases()
    
    with open(TEST_CASES_MD, "w", encoding="utf-8") as f:
        f.write("# VisionAI-ClipsMaster 测试用例目录\n\n")
        f.write("本文档列出了项目中的所有测试用例。\n\n")
        
        # 按类别组织测试用例
        categories = {}
        for test in test_cases:
            category = test["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(test)
        
        # 生成目录
        f.write("## 目录\n\n")
        
        for category in sorted(categories.keys()):
            f.write(f"- [{category}](#user-content-{category})\n")
            for test in categories[category]:
                safe_id = test["class"].lower().replace("_", "-")
                f.write(f"  - [{test['class']}](#user-content-{safe_id})\n")
        
        f.write("\n")
        
        # 生成详细测试用例
        for category in sorted(categories.keys()):
            f.write(f"## {category}\n\n")
            
            for test in categories[category]:
                f.write(f"### {test['class']}\n\n")
                
                if test["doc"]:
                    f.write(f"{test['doc']}\n\n")
                
                f.write(f"**文件:** `{test['file']}`\n\n")
                
                f.write("**测试方法:**\n\n")
                for method in test["methods"]:
                    f.write(f"- `{method['name']}`")
                    if method["doc"]:
                        f.write(f": {method['doc']}")
                    f.write("\n")
                
                f.write("\n")
        
        # 添加更新时间
        f.write("---\n\n")
        f.write(f"*文档生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    print(f"已生成测试用例文档: {TEST_CASES_MD}")

def generate_index_doc() -> None:
    """生成测试文档索引"""
    with open(TEST_INDEX_MD, "w", encoding="utf-8") as f:
        f.write("# VisionAI-ClipsMaster 测试文档\n\n")
        f.write("欢迎使用 VisionAI-ClipsMaster 测试文档，本文档提供了项目测试相关的完整指南。\n\n")
        
        # 文档概述
        f.write("## 文档概述\n\n")
        f.write("- [测试结构](TEST_STRUCTURE.md) - 测试目录结构和组织方式\n")
        f.write("- [测试用例目录](TEST_CASES.md) - 所有测试用例的详细列表\n")
        f.write("- [测试覆盖率报告](TEST_COVERAGE.md) - 项目测试覆盖率分析\n")
        f.write("- [测试安全指南](../TEST_SECURITY.md) - 测试数据安全和权限管理\n\n")
        
        # 测试执行指南
        f.write("## 测试执行指南\n\n")
        f.write("### 运行所有测试\n\n")
        f.write("```bash\n")
        f.write("# 使用 pytest 直接运行\n")
        f.write("pytest tests/\n\n")
        f.write("# 或使用提供的脚本\n")
        f.write("python run_tests.py\n")
        f.write("```\n\n")
        
        f.write("### 运行特定类别的测试\n\n")
        f.write("```bash\n")
        f.write("# 运行单元测试\n")
        f.write("python run_tests.py --category unit\n\n")
        f.write("# 运行内存测试\n")
        f.write("python tests/run_memory_tests.py\n")
        f.write("```\n\n")
        
        f.write("### 生成测试覆盖率报告\n\n")
        f.write("```bash\n")
        f.write("pytest --cov=src --cov-report=html tests/\n")
        f.write("```\n\n")
        
        # 测试环境设置
        f.write("## 测试环境设置\n\n")
        f.write("### 安装测试依赖\n\n")
        f.write("```bash\n")
        f.write("pip install -r tests/requirements-test.txt\n")
        f.write("```\n\n")
        
        f.write("### 测试目录权限设置\n\n")
        f.write("```bash\n")
        f.write("python scripts/secure_test_permissions.py --fix\n")
        f.write("```\n\n")
        
        # 测试开发指南
        f.write("## 测试开发指南\n\n")
        f.write("### 添加新测试\n\n")
        f.write("1. 在适当的测试目录中创建新的测试文件，命名为 `test_*.py`\n")
        f.write("2. 测试类应继承 `unittest.TestCase`\n")
        f.write("3. 测试方法应以 `test_` 开头\n")
        f.write("4. 添加详细的文档字符串描述测试目的\n\n")
        
        f.write("示例：\n\n")
        f.write("```python\n")
        f.write("class TestMyFeature(unittest.TestCase):\n")
        f.write("    \"\"\"我的功能测试类\"\"\"\n\n")
        f.write("    def test_something(self):\n")
        f.write("        \"\"\"测试某个特定行为\"\"\"\n")
        f.write("        # 测试代码\n")
        f.write("        self.assertTrue(True)\n")
        f.write("```\n\n")
        
        # 更新信息
        f.write("## 文档生成\n\n")
        f.write("本文档由自动化脚本生成，可通过以下命令更新：\n\n")
        f.write("```bash\n")
        f.write("python scripts/generate_test_docs.py\n")
        f.write("```\n\n")
        
        # 添加更新时间
        f.write("---\n\n")
        f.write(f"*文档生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    print(f"已生成测试文档索引: {TEST_INDEX_MD}")

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试文档生成器")
    parser.add_argument("--structure", action="store_true", help="生成测试结构文档")
    parser.add_argument("--coverage", action="store_true", help="生成测试覆盖率文档")
    parser.add_argument("--cases", action="store_true", help="生成测试用例文档")
    parser.add_argument("--index", action="store_true", help="生成测试文档索引")
    parser.add_argument("--all", action="store_true", help="生成所有文档")
    
    args = parser.parse_args()
    
    # 如果没有指定任何选项，默认生成所有文档
    if not any([args.structure, args.coverage, args.cases, args.index]):
        args.all = True
    
    start_time = time.time()
    
    if args.structure or args.all:
        generate_test_structure_doc()
    
    if args.coverage or args.all:
        generate_coverage_doc()
    
    if args.cases or args.all:
        generate_test_cases_doc()
    
    if args.index or args.all:
        generate_index_doc()
    
    elapsed_time = time.time() - start_time
    print(f"文档生成完成，耗时: {elapsed_time:.2f}秒")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 