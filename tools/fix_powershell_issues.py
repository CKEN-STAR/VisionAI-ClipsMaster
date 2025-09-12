#!/usr/bin/env python3
"""
PowerShell脚本问题修复工具
自动修复PowerShell脚本中的常见问题
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple

class PowerShellFixer:
    """PowerShell脚本修复器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.fixes_applied = []
        
    def find_powershell_files(self) -> List[Path]:
        """查找所有PowerShell文件"""
        return list(self.project_root.glob("*.ps1"))
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_error_variable_usage(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复$error变量使用问题"""
        fixes = []
        
        # 查找$error变量的赋值使用
        patterns = [
            (r'\$error\s*=', '$scriptErrors ='),
            (r'\$error\[', '$scriptErrors['),
            (r'\$error\.', '$scriptErrors.'),
            (r'foreach\s*\(\s*\$error\s+in', 'foreach ($scriptError in'),
            (r'if\s*\(\s*\$error\s*\)', 'if ($scriptErrors)'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                fixes.append(f"将 $error 变量重命名为 $scriptErrors")
        
        return content, fixes
    
    def fix_unapproved_verbs(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复未批准的PowerShell动词"""
        fixes = []
        
        # 常见的未批准动词映射
        verb_mappings = {
            'Build-': 'Start-Build',
            'Clean-': 'Clear-',
            'Create-': 'New-',
            'Make-': 'New-',
            'Delete-': 'Remove-',
            'Execute-': 'Invoke-',
            'Run-': 'Start-',
            'Launch-': 'Start-',
            'Kill-': 'Stop-',
            'Destroy-': 'Remove-'
        }
        
        # 查找函数定义
        function_pattern = r'function\s+([A-Za-z]+-[A-Za-z]+)'
        functions = re.findall(function_pattern, content)
        
        for func_name in functions:
            for old_verb, new_verb in verb_mappings.items():
                if func_name.startswith(old_verb):
                    new_func_name = func_name.replace(old_verb, new_verb, 1)
                    
                    # 替换函数定义
                    content = re.sub(
                        rf'function\s+{re.escape(func_name)}\b',
                        f'function {new_func_name}',
                        content
                    )
                    
                    # 替换函数调用
                    content = re.sub(
                        rf'\b{re.escape(func_name)}\b',
                        new_func_name,
                        content
                    )
                    
                    fixes.append(f"将函数 {func_name} 重命名为 {new_func_name}")
                    break
        
        return content, fixes
    
    def fix_encoding_issues(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复编码问题"""
        fixes = []
        
        # 确保文件以UTF-8 BOM开头（PowerShell推荐）
        if not content.startswith('\ufeff'):
            # 不添加BOM，因为可能会导致其他问题
            pass
        
        # 修复常见的编码问题字符
        replacements = [
            ('鈥?', '"'),
            ('鈥?', '"'),
            ('鈥?', "'"),
            ('鈥?', "'"),
            ('鈥?', '...'),
            ('鈥?', '-'),
            ('鈥?', '-'),
        ]
        
        for old_char, new_char in replacements:
            if old_char in content:
                content = content.replace(old_char, new_char)
                fixes.append(f"修复编码字符: {old_char} -> {new_char}")
        
        return content, fixes
    
    def fix_syntax_issues(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复语法问题"""
        fixes = []
        
        # 修复常见的语法问题
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # 修复字符串终止符问题
            if line.strip().endswith('"') and line.count('"') % 2 != 0:
                # 查找未闭合的字符串
                if line.count('"') == 1:
                    line = line + '"'
                    fixes.append(f"修复第{i+1}行未闭合的字符串")
            
            # 修复大括号匹配问题
            if '{' in line and '}' not in line:
                # 检查是否需要添加闭合大括号
                indent = len(line) - len(line.lstrip())
                if i < len(lines) - 1:
                    next_line = lines[i + 1]
                    if next_line.strip() and len(next_line) - len(next_line.lstrip()) <= indent:
                        # 可能需要添加闭合大括号
                        pass
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes
    
    def fix_file(self, file_path: Path) -> List[str]:
        """修复单个PowerShell文件"""
        print(f"🔧 修复文件: {file_path}")
        
        # 备份原文件
        backup_path = self.backup_file(file_path)
        print(f"📄 已备份到: {backup_path}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        all_fixes = []
        
        # 应用各种修复
        content, fixes = self.fix_error_variable_usage(content, file_path)
        all_fixes.extend(fixes)
        
        content, fixes = self.fix_unapproved_verbs(content, file_path)
        all_fixes.extend(fixes)
        
        content, fixes = self.fix_encoding_issues(content, file_path)
        all_fixes.extend(fixes)
        
        content, fixes = self.fix_syntax_issues(content, file_path)
        all_fixes.extend(fixes)
        
        # 写回修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if all_fixes:
            print(f"✅ 应用了 {len(all_fixes)} 个修复:")
            for fix in all_fixes:
                print(f"   - {fix}")
        else:
            print("ℹ️  未发现需要修复的问题")
        
        return all_fixes
    
    def fix_all_files(self) -> dict:
        """修复所有PowerShell文件"""
        ps_files = self.find_powershell_files()
        
        if not ps_files:
            print("❌ 未找到PowerShell文件")
            return {}
        
        print(f"🔍 找到 {len(ps_files)} 个PowerShell文件")
        
        results = {}
        
        for ps_file in ps_files:
            fixes = self.fix_file(ps_file)
            results[str(ps_file)] = fixes
            self.fixes_applied.extend(fixes)
            print()
        
        return results
    
    def generate_report(self, results: dict) -> str:
        """生成修复报告"""
        report = []
        report.append("# PowerShell脚本修复报告")
        report.append("=" * 50)
        report.append("")
        
        total_fixes = sum(len(fixes) for fixes in results.values())
        report.append(f"📊 总计修复: {total_fixes} 个问题")
        report.append(f"📁 处理文件: {len(results)} 个")
        report.append("")
        
        for file_path, fixes in results.items():
            report.append(f"## 文件: {Path(file_path).name}")
            if fixes:
                for fix in fixes:
                    report.append(f"- ✅ {fix}")
            else:
                report.append("- ℹ️  无需修复")
            report.append("")
        
        if total_fixes > 0:
            report.append("## 建议")
            report.append("1. 测试修复后的脚本功能")
            report.append("2. 如有问题，可从.backup文件恢复")
            report.append("3. 运行PowerShell语法检查验证修复效果")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🚀 PowerShell脚本修复工具")
    print("=" * 50)
    
    fixer = PowerShellFixer()
    results = fixer.fix_all_files()
    
    # 生成报告
    report = fixer.generate_report(results)
    
    # 保存报告
    report_file = Path("powershell_fix_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📄 修复报告已保存到:", report_file)
    print()
    print(report)

if __name__ == "__main__":
    main()
