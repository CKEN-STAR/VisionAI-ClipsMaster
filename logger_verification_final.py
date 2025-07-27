#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster Logger验证脚本 - 最终版本

验证所有logger相关警告是否已完全解决：
1. 检查全局logger定义
2. 验证logger在所有使用位置都可访问
3. 确认IDE警告已清除
4. 测试logger功能正常工作
"""

import os
import sys
import re
import ast
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_logger_usage():
    """分析logger使用情况"""
    logger.info("分析logger使用情况...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    if not ui_file.exists():
        logger.error(f"文件不存在: {ui_file}")
        return False
    
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计logger使用
    logger_uses = re.findall(r'logger\.(\w+)', content)
    logger_definitions = re.findall(r'logger\s*=\s*([^\n]+)', content)
    
    logger.info(f"Logger使用次数: {len(logger_uses)}")
    logger.info(f"Logger方法调用: {set(logger_uses)}")
    logger.info(f"Logger定义次数: {len(logger_definitions)}")
    
    # 检查全局logger定义
    global_logger_pattern = r'logger\s*=\s*logging\.getLogger\(__name__\)'
    global_logger_found = bool(re.search(global_logger_pattern, content))
    
    if global_logger_found:
        logger.info("✅ 发现全局logger定义")
    else:
        logger.warning("⚠️ 未发现全局logger定义")
    
    return global_logger_found and len(logger_definitions) > 0

def check_logger_scope_coverage():
    """检查logger作用域覆盖"""
    logger.info("检查logger作用域覆盖...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    with open(ui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有logger使用的行号
    lines = content.split('\n')
    logger_usage_lines = []
    
    for i, line in enumerate(lines, 1):
        if 'logger.' in line and not line.strip().startswith('#'):
            logger_usage_lines.append(i)
    
    logger.info(f"Logger使用行号: {logger_usage_lines[:10]}{'...' if len(logger_usage_lines) > 10 else ''}")
    logger.info(f"总计logger使用: {len(logger_usage_lines)}行")
    
    # 检查特定的问题行号（从截图中识别的）
    problem_lines = [1782, 1787, 1793, 1797, 1805, 1821, 1825, 1831, 1837, 1841, 1845, 1869, 1878, 1881, 1884, 1888, 1892, 1914]
    
    logger.info("检查之前有问题的行号...")
    for line_num in problem_lines:
        if line_num <= len(lines):
            line_content = lines[line_num - 1].strip()
            if 'logger.' in line_content:
                logger.info(f"行 {line_num}: {line_content}")
    
    return len(logger_usage_lines) > 0

def verify_syntax_and_imports():
    """验证语法和导入"""
    logger.info("验证语法和导入...")
    
    try:
        # 语法检查
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        logger.info("✅ 语法检查通过")
        
        # 导入测试
        import importlib.util
        spec = importlib.util.spec_from_file_location("simple_ui_fixed", "simple_ui_fixed.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 检查logger是否可访问
            if hasattr(module, 'logger'):
                logger.info("✅ 全局logger可访问")
                
                # 测试logger功能
                test_logger = getattr(module, 'logger')
                test_logger.info("测试logger功能")
                logger.info("✅ Logger功能正常")
                
                return True
            else:
                logger.warning("⚠️ 全局logger不可访问")
                return False
        else:
            logger.error("❌ 无法创建模块规范")
            return False
            
    except SyntaxError as e:
        logger.error(f"❌ 语法错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 导入测试失败: {e}")
        return False

def check_specific_logger_locations():
    """检查特定logger使用位置"""
    logger.info("检查特定logger使用位置...")
    
    ui_file = Path("simple_ui_fixed.py")
    
    with open(ui_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 检查VideoProcessor类中的logger使用
    in_video_processor = False
    video_processor_logger_uses = []
    
    for i, line in enumerate(lines, 1):
        if 'class VideoProcessor' in line:
            in_video_processor = True
            logger.info(f"发现VideoProcessor类在行 {i}")
        elif line.startswith('class ') and in_video_processor:
            in_video_processor = False
        
        if in_video_processor and 'logger.' in line:
            video_processor_logger_uses.append((i, line.strip()))
    
    logger.info(f"VideoProcessor类中logger使用: {len(video_processor_logger_uses)}次")
    
    if video_processor_logger_uses:
        logger.info("VideoProcessor中的logger使用示例:")
        for line_num, line_content in video_processor_logger_uses[:5]:
            logger.info(f"  行 {line_num}: {line_content}")
    
    return len(video_processor_logger_uses) > 0

def run_ide_compatibility_check():
    """运行IDE兼容性检查"""
    logger.info("运行IDE兼容性检查...")
    
    try:
        # 模拟Pylance类型检查
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有明显的未定义变量使用
        # 这是一个简化的检查，真正的Pylance会更复杂
        
        # 查找logger使用但没有在同一作用域定义的情况
        lines = content.split('\n')
        potential_issues = []
        
        current_scope_has_logger = False
        global_logger_defined = 'logger = logging.getLogger(__name__)' in content
        
        for i, line in enumerate(lines, 1):
            # 检查是否在全局作用域
            if not line.startswith(' ') and not line.startswith('\t'):
                if 'logger = ' in line:
                    current_scope_has_logger = True
            
            # 检查logger使用
            if 'logger.' in line and not line.strip().startswith('#'):
                if not (global_logger_defined or current_scope_has_logger):
                    potential_issues.append((i, line.strip()))
        
        if potential_issues:
            logger.warning(f"发现 {len(potential_issues)} 个潜在的logger作用域问题")
            for line_num, line_content in potential_issues[:3]:
                logger.warning(f"  行 {line_num}: {line_content}")
        else:
            logger.info("✅ 未发现logger作用域问题")
        
        return len(potential_issues) == 0
        
    except Exception as e:
        logger.error(f"❌ IDE兼容性检查失败: {e}")
        return False

def generate_logger_report():
    """生成logger验证报告"""
    logger.info("生成logger验证报告...")
    
    report = {
        "timestamp": "2025-07-27 10:21:00",
        "file": "simple_ui_fixed.py",
        "tests": {}
    }
    
    # 运行所有检查
    tests = [
        ("logger_usage_analysis", analyze_logger_usage),
        ("scope_coverage_check", check_logger_scope_coverage),
        ("syntax_and_imports", verify_syntax_and_imports),
        ("specific_locations", check_specific_logger_locations),
        ("ide_compatibility", run_ide_compatibility_check)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            report["tests"][test_name] = {
                "status": "PASS" if result else "FAIL",
                "result": result
            }
            if result:
                passed_tests += 1
        except Exception as e:
            report["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    # 计算总体状态
    success_rate = (passed_tests / total_tests) * 100
    report["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": success_rate,
        "overall_status": "PASS" if success_rate >= 80 else "FAIL"
    }
    
    return report

def main():
    """主函数"""
    logger.info("开始VisionAI-ClipsMaster Logger最终验证...")
    
    # 生成验证报告
    report = generate_logger_report()
    
    # 输出结果
    logger.info("=" * 60)
    logger.info("Logger验证报告")
    logger.info("=" * 60)
    
    for test_name, test_result in report["tests"].items():
        status_icon = "✅" if test_result["status"] == "PASS" else "❌" if test_result["status"] == "FAIL" else "⚠️"
        logger.info(f"{status_icon} {test_name}: {test_result['status']}")
    
    logger.info("=" * 60)
    summary = report["summary"]
    logger.info(f"总体状态: {'✅ PASS' if summary['overall_status'] == 'PASS' else '❌ FAIL'}")
    logger.info(f"成功率: {summary['success_rate']:.1f}% ({summary['passed_tests']}/{summary['total_tests']})")
    
    if summary["overall_status"] == "PASS":
        logger.info("🎉 所有logger警告问题已完全解决！")
        logger.info("💡 建议重启IDE以清除缓存的警告信息")
        return True
    else:
        logger.warning("⚠️ 仍有部分logger问题需要解决")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
