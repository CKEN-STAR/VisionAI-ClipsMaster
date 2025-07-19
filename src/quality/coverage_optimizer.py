#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import ast
import json
import coverage
import importlib
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any

# 添加项目根目录到导入路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from src.utils.log_handler import get_logger
from src.core.report_manager import report_manager

logger = get_logger(__name__)


class CoverageAnalyzer:
    """测试覆盖率分析器，用于识别未被测试覆盖的代码路径和优化建议"""

    def __init__(self, src_dir: str = "src", exclude_dirs: List[str] = None,
                 test_dir: str = "tests", coverage_threshold: float = 80.0):
        """初始化覆盖率分析器
        
        Args:
            src_dir: 源代码目录
            exclude_dirs: 排除的目录列表
            test_dir: 测试代码目录
            coverage_threshold: 覆盖率阈值(百分比)
        """
        self.project_root = project_root
        self.src_dir = self.project_root / src_dir
        self.test_dir = self.project_root / test_dir
        self.exclude_dirs = exclude_dirs or ["__pycache__", "migrations", "tests"]
        self.coverage_threshold = coverage_threshold
        
        # 覆盖率对象
        self.cov = coverage.Coverage(
            source=[src_dir],
            omit=[
                f"*/{exclude}/*" for exclude in self.exclude_dirs
            ] + ["*/site-packages/*", "*/dist-packages/*"]
        )
        
        # 结果存储
        self.uncovered_paths = []
        self.module_coverage = {}
        self.coverage_report = {}
        self.optimization_suggestions = []
        
    def find_uncovered_paths(self) -> List[str]:
        """基于代码静态扫描识别未被覆盖的路径
        
        Returns:
            未被测试覆盖的代码路径列表
        """
        uncovered = []
        
        # 遍历源代码文件
        for root, dirs, files in os.walk(self.src_dir):
            # 排除指定目录
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            # 处理Python文件
            for file in files:
                if not file.endswith(".py") or file.startswith("__"):
                    continue
                    
                file_path = Path(root) / file
                relative_path = file_path.relative_to(self.project_root)
                
                # 检查是否有对应的测试文件
                test_file = self._find_test_file(relative_path)
                if not test_file:
                    uncovered.append(str(relative_path))
                    continue
                
                # 分析代码中未测试的函数/方法
                uncovered_items = self._analyze_file_coverage(file_path, test_file)
                uncovered.extend(uncovered_items)
        
        self.uncovered_paths = uncovered
        return uncovered
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """运行覆盖率分析并生成报告
        
        Returns:
            覆盖率分析报告字典
        """
        logger.info("开始运行测试覆盖率分析...")
        
        try:
            # 启动覆盖率测量
            self.cov.start()
            
            # 运行测试套件
            import pytest
            test_args = ["-xvs", str(self.test_dir)]
            pytest.main(test_args)
            
            # 停止覆盖率测量
            self.cov.stop()
            
            # 生成报告
            self.cov.save()
            
            # 获取覆盖率数据
            self.coverage_report = self._generate_coverage_data()
            
            # 生成优化建议
            self.optimization_suggestions = self._generate_optimization_suggestions()
            
            # 更新报告管理器
            self._update_report_manager()
            
            return self.coverage_report
            
        except Exception as e:
            logger.error(f"运行覆盖率分析时出错: {str(e)}")
            return {"error": str(e)}
    
    def get_critical_modules(self) -> List[str]:
        """获取关键模块列表(覆盖率低于阈值的模块)
        
        Returns:
            需要重点关注的模块列表
        """
        if not self.module_coverage:
            # 如果还没有运行分析，先运行
            self.run_coverage_analysis()
            
        critical_modules = []
        for module, data in self.module_coverage.items():
            if data.get("coverage", 0) < self.coverage_threshold:
                critical_modules.append(module)
                
        return critical_modules
    
    def export_coverage_report(self, output_path: Optional[str] = None) -> str:
        """导出覆盖率报告
        
        Args:
            output_path: 输出路径，默认为output/reports/coverage_report.json
            
        Returns:
            报告文件路径
        """
        if not output_path:
            report_dir = self.project_root / "output" / "reports"
            report_dir.mkdir(exist_ok=True, parents=True)
            output_path = report_dir / "coverage_report.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.coverage_report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"覆盖率报告已保存至: {output_path}")
        return str(output_path)
    
    def _find_test_file(self, src_file_path: Path) -> Optional[Path]:
        """查找对应的测试文件
        
        Args:
            src_file_path: 源码文件路径
            
        Returns:
            测试文件路径，如果不存在则返回None
        """
        # 方式1: test_文件名
        filename = src_file_path.name
        test_filename = f"test_{filename}"
        test_path = self.test_dir / test_filename
        if test_path.exists():
            return test_path
            
        # 方式2: 保持目录结构的测试文件
        parts = list(src_file_path.parts)
        if parts[0] == "src":
            parts[0] = "tests"
            test_path = self.project_root.joinpath(*parts)
            if test_path.exists():
                return test_path
                
        # 方式3: 模块名_test.py
        module_name = filename.replace(".py", "")
        test_filename = f"{module_name}_test.py"
        
        # 递归查找测试目录
        for root, _, files in os.walk(self.test_dir):
            if test_filename in files:
                return Path(root) / test_filename
                
        return None
    
    def _analyze_file_coverage(self, file_path: Path, test_file_path: Path) -> List[str]:
        """分析单个文件的测试覆盖情况
        
        Args:
            file_path: 源码文件路径
            test_file_path: 测试文件路径
            
        Returns:
            未被测试的函数/方法列表
        """
        uncovered_items = []
        
        try:
            # 解析源文件
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            src_tree = ast.parse(source, filename=str(file_path))
            
            # 提取源文件中的函数和方法名
            src_functions = self._extract_functions(src_tree)
            
            # 解析测试文件
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_source = f.read()
                
            test_tree = ast.parse(test_source, filename=str(test_file_path))
            
            # 检查是否每个函数都有测试
            for func_name in src_functions:
                if not self._is_function_tested(func_name, test_tree):
                    rel_path = file_path.relative_to(self.project_root)
                    uncovered_items.append(f"{rel_path}::{func_name}")
        
        except Exception as e:
            logger.warning(f"分析文件覆盖率时出错: {file_path}, {str(e)}")
            
        return uncovered_items
    
    def _extract_functions(self, tree: ast.AST) -> List[str]:
        """从AST中提取函数和方法名
        
        Args:
            tree: 解析后的AST
            
        Returns:
            函数/方法名列表
        """
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 排除私有方法和特殊方法
                if not node.name.startswith('_') or node.name in ('__init__'):
                    functions.append(node.name)
                    
        return functions
    
    def _is_function_tested(self, func_name: str, test_tree: ast.AST) -> bool:
        """检查函数是否在测试文件中被测试
        
        Args:
            func_name: 函数名
            test_tree: 测试文件的AST
            
        Returns:
            是否被测试
        """
        test_function_pattern = f"test_{func_name}"
        
        for node in ast.walk(test_tree):
            if isinstance(node, ast.FunctionDef):
                if node.name == test_function_pattern:
                    return True
                    
                # 检查函数体中是否调用了该函数
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and hasattr(subnode, 'func'):
                        if hasattr(subnode.func, 'id') and subnode.func.id == func_name:
                            return True
                        elif hasattr(subnode.func, 'attr') and subnode.func.attr == func_name:
                            return True
        
        return False
    
    def _generate_coverage_data(self) -> Dict[str, Any]:
        """生成覆盖率数据报告
        
        Returns:
            覆盖率数据字典
        """
        # 获取覆盖率数据
        coverage_data = self.cov.get_data()
        
        # 按模块组织覆盖率数据
        module_data = {}
        overall_coverage = 0
        measured_files = 0
        
        for file_path in coverage_data.measured_files():
            if not file_path.startswith(str(self.src_dir)):
                continue
                
            try:
                # 相对路径
                rel_path = Path(file_path).relative_to(self.project_root)
                module_name = str(rel_path)
                
                # 分析文件覆盖率
                file_coverage = coverage_data.line_percent(file_path)
                
                # 获取未覆盖的行
                analysis = self.cov.analysis2(file_path)
                missing_lines = analysis[3]
                
                module_data[module_name] = {
                    "coverage": file_coverage,
                    "missing_lines": missing_lines,
                    "status": "good" if file_coverage >= self.coverage_threshold else "warning" 
                }
                
                overall_coverage += file_coverage
                measured_files += 1
                
            except Exception as e:
                logger.warning(f"处理覆盖率数据时出错: {file_path}, {str(e)}")
                
        # 计算平均覆盖率
        if measured_files > 0:
            overall_coverage /= measured_files
        
        self.module_coverage = module_data
        
        # 构建覆盖率报告
        return {
            "timestamp": self.cov.config.run_timestamp,
            "overall_coverage": round(overall_coverage, 2),
            "coverage_threshold": self.coverage_threshold,
            "status": "good" if overall_coverage >= self.coverage_threshold else "warning",
            "modules": module_data,
            "uncovered_paths": self.uncovered_paths,
            "optimization_suggestions": self.optimization_suggestions
        }
    
    def _generate_optimization_suggestions(self) -> List[Dict[str, str]]:
        """生成覆盖率优化建议
        
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 基于未覆盖路径生成建议
        if not self.uncovered_paths:
            self.find_uncovered_paths()
            
        # 对于每个未覆盖文件，生成建议
        for path in self.uncovered_paths:
            if "::" in path:  # 函数级别
                file_path, func_name = path.split("::")
                suggestions.append({
                    "type": "function",
                    "path": file_path,
                    "item": func_name,
                    "suggestion": f"为{file_path}中的{func_name}函数添加单元测试"
                })
            else:  # 文件级别
                suggestions.append({
                    "type": "file",
                    "path": path,
                    "item": path,
                    "suggestion": f"为{path}创建测试用例"
                })
        
        # 基于模块覆盖率生成建议
        for module, data in self.module_coverage.items():
            if data.get("coverage", 0) < self.coverage_threshold:
                suggestions.append({
                    "type": "module",
                    "path": module,
                    "item": f"覆盖率: {data.get('coverage')}%",
                    "suggestion": f"提高{module}的测试覆盖率，重点关注未覆盖的行: {data.get('missing_lines', [])[:5]}..."
                })
        
        return suggestions
    
    def _update_report_manager(self):
        """更新报告管理器中的覆盖率数据"""
        try:
            # 向报告管理器添加覆盖率指标
            report_manager.set_performance_metric("测试覆盖率", 
                                               self.coverage_report.get("overall_coverage", 0))
            
            # 添加关键覆盖率问题
            for suggestion in self.optimization_suggestions[:5]:  # 最多添加5个建议
                report_manager.add_error(
                    "测试覆盖率不足",
                    suggestion.get("path", "未知"),
                    suggestion.get("item", "未知项目"),
                    suggestion.get("suggestion", "增加测试用例")
                )
        except Exception as e:
            logger.warning(f"更新报告管理器时出错: {str(e)}")


# CLI入口
def main():
    """命令行入口函数"""
    analyzer = CoverageAnalyzer()
    
    # 运行覆盖率分析
    report = analyzer.run_coverage_analysis()
    
    # 导出报告
    report_path = analyzer.export_coverage_report()
    
    print(f"覆盖率分析完成!")
    print(f"总体覆盖率: {report.get('overall_coverage')}%")
    print(f"报告已保存至: {report_path}")
    
    # 输出关键模块
    critical_modules = analyzer.get_critical_modules()
    if critical_modules:
        print("\n需要重点关注的模块:")
        for module in critical_modules:
            print(f" - {module}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 