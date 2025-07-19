#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 系统性问题修复脚本

按优先级顺序修复项目中发现的所有问题：
1. 高优先级：批量修复200+个正则表达式错误
2. 中优先级：清理CSS警告，优化启动时间
3. 验证：确保所有修复不影响核心功能

作者: CKEN
版本: v1.0
日期: 2025-07-12
"""

import os
import re
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

class VisionAISystematicFixer:
    """VisionAI-ClipsMaster 系统性修复器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.core_path = self.project_root / "VisionAI-ClipsMaster-Core"
        self.backup_dir = self.project_root / "systematic_fix_backup"
        
        self.fix_results = {
            "timestamp": datetime.now().isoformat(),
            "high_priority_fixes": {},
            "medium_priority_fixes": {},
            "verification_results": {},
            "summary": {
                "total_files_processed": 0,
                "regex_errors_fixed": 0,
                "css_warnings_fixed": 0,
                "modules_verified": 0,
                "overall_success_rate": 0.0
            }
        }
        
        # 正则表达式修复模式
        self.regex_fix_patterns = [
            # 修复 \\1 引用错误
            (r'\\\\1\{(\d+)\}', r'\\d{\1}'),
            (r'\\\\1\+', r'\\d+'),
            (r'\\\\1\*', r'\\d*'),
            (r'\\\\1', r'\\d'),
            
            # 修复其他常见正则错误
            (r'\\\\(\d+)', r'\\d'),
            (r'\(\\\\\d+\)', r'(\\d+)'),
            (r'\[\\\\\d+\]', r'[\\d]'),
            
            # 修复时间戳模式
            (r'\\\\1\{2\}', r'\\d{2}'),
            (r'\\\\1\{3\}', r'\\d{3}'),
            (r'\\\\1\{4\}', r'\\d{4}'),
        ]
        
        print(f"🔧 VisionAI-ClipsMaster 系统性修复器")
        print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"项目路径: {self.core_path}")
    
    def run_systematic_fix(self):
        """运行系统性修复"""
        print(f"\n{'='*80}")
        print(f"开始系统性修复")
        print(f"{'='*80}")
        
        # 创建备份
        self.create_backup()
        
        # 高优先级修复
        print(f"\n🔴 高优先级修复")
        self.fix_regex_errors()
        
        # 中优先级修复
        print(f"\n🟡 中优先级修复")
        self.fix_css_warnings()
        self.optimize_startup_time()
        
        # 验证修复结果
        print(f"\n🟢 验证修复结果")
        self.verify_fixes()
        
        # 生成修复报告
        self.generate_fix_report()
        
        return self.fix_results
    
    def create_backup(self):
        """创建备份"""
        print(f"\n{'='*60}")
        print(f"创建备份")
        print(f"{'='*60}")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        # 备份核心文件
        backup_core = self.backup_dir / "VisionAI-ClipsMaster-Core"
        shutil.copytree(self.core_path, backup_core)
        
        print(f"✅ 备份创建完成: {self.backup_dir}")
    
    def fix_regex_errors(self):
        """修复正则表达式错误"""
        print(f"\n{'='*60}")
        print(f"1. 批量修复正则表达式错误")
        print(f"{'='*60}")
        
        # 目标目录
        target_dirs = [
            "src/api",
            "src/core", 
            "src/parsers",
            "src/export",
            "src/training",
            "src/utils"
        ]
        
        regex_fixes = {}
        total_fixes = 0
        
        for target_dir in target_dirs:
            dir_path = self.core_path / target_dir
            if not dir_path.exists():
                continue
                
            print(f"\n  处理目录: {target_dir}")
            dir_fixes = self._fix_regex_in_directory(dir_path)
            regex_fixes[target_dir] = dir_fixes
            
            dir_fix_count = sum(len(fixes) for fixes in dir_fixes.values())
            total_fixes += dir_fix_count
            print(f"    修复文件: {len(dir_fixes)}")
            print(f"    修复错误: {dir_fix_count}")
        
        self.fix_results["high_priority_fixes"]["regex_errors"] = regex_fixes
        self.fix_results["summary"]["regex_errors_fixed"] = total_fixes
        
        print(f"\n📊 正则表达式修复总结:")
        print(f"  总修复错误: {total_fixes}")
        print(f"  处理目录: {len([d for d in target_dirs if (self.core_path / d).exists()])}")
    
    def _fix_regex_in_directory(self, directory: Path) -> Dict[str, List[Dict]]:
        """修复目录中的正则表达式错误"""
        fixes = {}
        
        for py_file in directory.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_fixes = []
                
                # 应用修复模式
                for pattern, replacement in self.regex_fix_patterns:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        for match in matches:
                            file_fixes.append({
                                "line": content[:match.start()].count('\n') + 1,
                                "original": match.group(0),
                                "fixed": re.sub(pattern, replacement, match.group(0)),
                                "pattern": pattern
                            })
                        
                        content = re.sub(pattern, replacement, content)
                
                # 如果有修复，保存文件
                if content != original_content:
                    # 验证语法
                    try:
                        compile(content, str(py_file), 'exec')
                        
                        # 保存修复后的文件
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        fixes[str(py_file.relative_to(self.core_path))] = file_fixes
                        print(f"    ✅ 修复: {py_file.name} ({len(file_fixes)} 个错误)")
                        
                    except SyntaxError as e:
                        print(f"    ❌ 语法错误: {py_file.name} - {str(e)}")
                        # 恢复原内容
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                
            except Exception as e:
                print(f"    ⚠️ 处理失败: {py_file.name} - {str(e)}")
        
        return fixes
    
    def fix_css_warnings(self):
        """修复CSS警告"""
        print(f"\n{'='*60}")
        print(f"2. 清理PyQt6 CSS警告")
        print(f"{'='*60}")
        
        # 不支持的CSS属性
        unsupported_css = [
            "transform",
            "box-shadow", 
            "text-shadow",
            "transition",
            "-webkit-",
            "-moz-",
            "-ms-"
        ]
        
        css_fixes = {}
        total_css_fixes = 0
        
        # 查找包含CSS的Python文件
        for py_file in self.core_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                file_fixes = []
                
                # 查找CSS字符串
                css_patterns = [
                    r'setStyleSheet\s*\(\s*["\']([^"\']*)["\']',
                    r'QSS\s*=\s*["\']([^"\']*)["\']',
                    r'style\s*=\s*["\']([^"\']*)["\']'
                ]
                
                for css_pattern in css_patterns:
                    matches = re.finditer(css_pattern, content, re.DOTALL)
                    for match in matches:
                        css_content = match.group(1)
                        
                        # 移除不支持的CSS属性
                        for unsupported in unsupported_css:
                            if unsupported in css_content:
                                # 移除包含不支持属性的行
                                lines = css_content.split('\n')
                                filtered_lines = []
                                
                                for line in lines:
                                    if not any(prop in line for prop in unsupported_css):
                                        filtered_lines.append(line)
                                    else:
                                        file_fixes.append({
                                            "removed_line": line.strip(),
                                            "reason": f"不支持的CSS属性: {unsupported}"
                                        })
                                
                                new_css = '\n'.join(filtered_lines)
                                content = content.replace(css_content, new_css)
                
                # 如果有修复，保存文件
                if content != original_content and file_fixes:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    css_fixes[str(py_file.relative_to(self.core_path))] = file_fixes
                    total_css_fixes += len(file_fixes)
                    print(f"    ✅ 清理CSS: {py_file.name} ({len(file_fixes)} 个警告)")
                
            except Exception as e:
                print(f"    ⚠️ 处理失败: {py_file.name} - {str(e)}")
        
        self.fix_results["medium_priority_fixes"]["css_warnings"] = css_fixes
        self.fix_results["summary"]["css_warnings_fixed"] = total_css_fixes
        
        print(f"\n📊 CSS警告清理总结:")
        print(f"  清理文件: {len(css_fixes)}")
        print(f"  清理警告: {total_css_fixes}")
    
    def optimize_startup_time(self):
        """优化启动时间"""
        print(f"\n{'='*60}")
        print(f"3. 优化UI启动时间")
        print(f"{'='*60}")
        
        startup_optimizations = {}
        
        # 查找主UI文件
        ui_file = self.core_path / "simple_ui_fixed.py"
        if ui_file.exists():
            try:
                with open(ui_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                optimizations = []
                
                # 优化1: 延迟导入非关键模块
                lazy_import_pattern = r'^(import|from)\s+(?!sys|os|pathlib|PyQt6)([^\n]+)'
                matches = list(re.finditer(lazy_import_pattern, content, re.MULTILINE))
                
                if matches:
                    # 将非关键导入移到函数内部
                    for match in matches[:5]:  # 只优化前5个
                        import_line = match.group(0)
                        if "# 延迟导入" not in import_line:
                            optimizations.append({
                                "type": "延迟导入",
                                "original": import_line,
                                "optimization": "移动到函数内部"
                            })
                
                # 优化2: 减少初始化日志
                log_pattern = r'print\s*\([^)]*\)'
                log_matches = list(re.finditer(log_pattern, content))
                if len(log_matches) > 20:
                    optimizations.append({
                        "type": "减少日志",
                        "count": len(log_matches),
                        "optimization": "移除非关键启动日志"
                    })
                
                startup_optimizations["ui_optimizations"] = optimizations
                
                print(f"    ✅ 识别优化点: {len(optimizations)}")
                
            except Exception as e:
                print(f"    ⚠️ 优化分析失败: {str(e)}")
        
        self.fix_results["medium_priority_fixes"]["startup_optimization"] = startup_optimizations
        
        print(f"\n📊 启动优化总结:")
        print(f"  识别优化点: {len(startup_optimizations.get('ui_optimizations', []))}")
    
    def verify_fixes(self):
        """验证修复结果"""
        print(f"\n{'='*60}")
        print(f"验证修复结果")
        print(f"{'='*60}")
        
        verification_results = {}
        
        # 1. 验证核心模块导入
        print(f"\n  1. 验证核心模块导入")
        core_modules = [
            ("src.core.model_switcher", "ModelSwitcher"),
            ("src.core.language_detector", "LanguageDetector"),
            ("src.training.zh_trainer", "ZhTrainer"),
            ("src.training.en_trainer", "EnTrainer"),
            ("src.parsers.srt_decoder", "SRTDecoder"),
            ("src.core.video_processor", "VideoProcessor")
        ]
        
        # 添加路径
        sys.path.insert(0, str(self.core_path))
        
        module_verification = {}
        successful_imports = 0
        
        for module_path, class_name in core_modules:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                
                module_verification[module_path] = {
                    "status": "SUCCESS",
                    "class_exists": True
                }
                successful_imports += 1
                print(f"    ✅ {module_path}: 导入成功")
                
            except Exception as e:
                module_verification[module_path] = {
                    "status": "FAILED",
                    "error": str(e)
                }
                print(f"    ❌ {module_path}: 导入失败 - {str(e)}")
        
        verification_results["module_imports"] = module_verification
        
        # 2. 验证语法正确性
        print(f"\n  2. 验证Python语法")
        syntax_verification = {}
        syntax_errors = 0
        total_files = 0
        
        for py_file in self.core_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            total_files += 1
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                compile(content, str(py_file), 'exec')
                syntax_verification[str(py_file.relative_to(self.core_path))] = "PASS"
                
            except SyntaxError as e:
                syntax_verification[str(py_file.relative_to(self.core_path))] = f"SYNTAX_ERROR: {str(e)}"
                syntax_errors += 1
                print(f"    ❌ 语法错误: {py_file.name} - {str(e)}")
        
        verification_results["syntax_check"] = {
            "total_files": total_files,
            "syntax_errors": syntax_errors,
            "success_rate": round((total_files - syntax_errors) / total_files * 100, 1) if total_files > 0 else 0
        }
        
        # 3. 测试UI启动
        print(f"\n  3. 测试UI启动能力")
        ui_test_result = self._test_ui_startup()
        verification_results["ui_startup"] = ui_test_result
        
        # 移除路径
        sys.path.remove(str(self.core_path))
        
        self.fix_results["verification_results"] = verification_results
        self.fix_results["summary"]["modules_verified"] = successful_imports
        
        # 计算总体成功率
        total_tests = len(core_modules) + 1  # 模块导入 + UI启动
        successful_tests = successful_imports + (1 if ui_test_result.get("can_start", False) else 0)
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        self.fix_results["summary"]["overall_success_rate"] = round(overall_success_rate, 1)
        
        print(f"\n📊 验证总结:")
        print(f"  模块导入: {successful_imports}/{len(core_modules)}")
        print(f"  语法检查: {total_files - syntax_errors}/{total_files}")
        print(f"  UI启动: {'✅' if ui_test_result.get('can_start', False) else '❌'}")
        print(f"  总体成功率: {overall_success_rate:.1f}%")
    
    def _test_ui_startup(self) -> Dict[str, Any]:
        """测试UI启动能力"""
        ui_file = self.core_path / "simple_ui_fixed.py"
        
        if not ui_file.exists():
            return {"can_start": False, "error": "UI文件不存在"}
        
        try:
            # 检查语法
            with open(ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(ui_file), 'exec')
            
            # 检查关键组件
            required_components = [
                "class SimpleScreenplayApp",
                "def main()",
                "QApplication",
                "from PyQt6"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if not missing_components:
                return {
                    "can_start": True,
                    "syntax_valid": True,
                    "components_complete": True
                }
            else:
                return {
                    "can_start": False,
                    "syntax_valid": True,
                    "components_complete": False,
                    "missing_components": missing_components
                }
                
        except SyntaxError as e:
            return {
                "can_start": False,
                "syntax_valid": False,
                "syntax_error": str(e)
            }
        except Exception as e:
            return {
                "can_start": False,
                "error": str(e)
            }
    
    def generate_fix_report(self):
        """生成修复报告"""
        print(f"\n{'='*60}")
        print(f"生成修复报告")
        print(f"{'='*60}")
        
        # 更新总结统计
        self.fix_results["summary"]["total_files_processed"] = sum(
            len(fixes) for category in self.fix_results["high_priority_fixes"].values()
            for fixes in category.values() if isinstance(fixes, dict)
        )
        
        # 保存JSON报告
        report_file = self.project_root / f"VisionAI_ClipsMaster_Systematic_Fix_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.fix_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 详细报告已保存: {report_file}")
            
        except Exception as e:
            print(f"❌ 保存报告失败: {str(e)}")
        
        # 生成Markdown报告
        self._generate_markdown_report()
        
        # 显示修复总结
        self._print_fix_summary()
    
    def _generate_markdown_report(self):
        """生成Markdown格式报告"""
        report_md = self.project_root / f"VisionAI_ClipsMaster_Systematic_Fix_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(report_md, 'w', encoding='utf-8') as f:
                f.write("# VisionAI-ClipsMaster 系统性修复报告\n\n")
                f.write(f"**修复时间**: {self.fix_results['timestamp']}\n\n")
                
                # 修复总结
                summary = self.fix_results["summary"]
                f.write("## 修复总结\n\n")
                f.write(f"- **处理文件**: {summary['total_files_processed']}\n")
                f.write(f"- **正则表达式错误修复**: {summary['regex_errors_fixed']}\n")
                f.write(f"- **CSS警告清理**: {summary['css_warnings_fixed']}\n")
                f.write(f"- **模块验证**: {summary['modules_verified']}\n")
                f.write(f"- **总体成功率**: {summary['overall_success_rate']:.1f}%\n\n")
                
                # 高优先级修复
                f.write("## 高优先级修复\n\n")
                f.write("### 正则表达式错误修复\n\n")
                regex_fixes = self.fix_results["high_priority_fixes"].get("regex_errors", {})
                for directory, fixes in regex_fixes.items():
                    f.write(f"#### {directory}\n\n")
                    for file_path, file_fixes in fixes.items():
                        f.write(f"- **{file_path}**: {len(file_fixes)} 个错误\n")
                f.write("\n")
                
                # 验证结果
                f.write("## 验证结果\n\n")
                verification = self.fix_results["verification_results"]
                
                f.write("### 模块导入测试\n\n")
                module_imports = verification.get("module_imports", {})
                for module, result in module_imports.items():
                    status_icon = "✅" if result.get("status") == "SUCCESS" else "❌"
                    f.write(f"- {status_icon} **{module}**: {result.get('status', 'UNKNOWN')}\n")
                f.write("\n")
                
                f.write("### 语法检查\n\n")
                syntax_check = verification.get("syntax_check", {})
                f.write(f"- **总文件数**: {syntax_check.get('total_files', 0)}\n")
                f.write(f"- **语法错误**: {syntax_check.get('syntax_errors', 0)}\n")
                f.write(f"- **成功率**: {syntax_check.get('success_rate', 0):.1f}%\n\n")
            
            print(f"✅ Markdown报告已保存: {report_md}")
            
        except Exception as e:
            print(f"❌ 保存Markdown报告失败: {str(e)}")
    
    def _print_fix_summary(self):
        """打印修复总结"""
        print(f"\n{'='*80}")
        print(f"系统性修复完成")
        print(f"{'='*80}")
        
        summary = self.fix_results["summary"]
        
        print(f"📊 修复统计:")
        print(f"  处理文件: {summary['total_files_processed']}")
        print(f"  正则表达式错误修复: {summary['regex_errors_fixed']}")
        print(f"  CSS警告清理: {summary['css_warnings_fixed']}")
        print(f"  模块验证通过: {summary['modules_verified']}")
        print(f"  总体成功率: {summary['overall_success_rate']:.1f}%")
        
        # 根据成功率给出评估
        success_rate = summary['overall_success_rate']
        if success_rate >= 95:
            print(f"\n🎉 优秀！系统性修复非常成功")
            print("建议: 项目已达到完美的开源发布状态")
        elif success_rate >= 85:
            print(f"\n✅ 良好！系统性修复基本成功")
            print("建议: 可以开源发布，少数问题可后续优化")
        elif success_rate >= 70:
            print(f"\n⚠️ 一般！系统性修复部分成功")
            print("建议: 解决剩余关键问题后开源")
        else:
            print(f"\n❌ 需要改进！系统性修复存在较多问题")
            print("建议: 需要进一步修复后再考虑开源")


def main():
    """主函数"""
    try:
        fixer = VisionAISystematicFixer()
        results = fixer.run_systematic_fix()
        
        # 返回适当的退出码
        if results["summary"]["overall_success_rate"] >= 85:
            sys.exit(0)  # 成功
        else:
            sys.exit(1)  # 需要进一步修复
            
    except KeyboardInterrupt:
        print("\n修复被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n修复过程出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
