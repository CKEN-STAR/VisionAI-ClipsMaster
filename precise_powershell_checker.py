#!/usr/bin/env python3
"""
精确的PowerShell问题检测工具
只检测真正的问题，避免误报
"""

import re
from pathlib import Path
from typing import List, Tuple

class PrecisePowerShellChecker:
    """精确的PowerShell检查器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
    
    def check_error_variable_misuse(self, content: str, file_path: Path) -> List[str]:
        """检查$error变量的误用"""
        issues = []
        
        # 只检查真正的$error变量赋值或修改
        problematic_patterns = [
            r'\$error\s*=',  # $error = something
            r'\$error\s*\+=',  # $error += something
            r'\$error\s*\[.*\]\s*=',  # $error[index] = something
            r'\$error\..*\s*=',  # $error.property = something
            r'foreach\s*\(\s*\$error\s+in',  # foreach ($error in ...)
        ]
        
        # 排除的正常用法
        normal_patterns = [
            r'\$ErrorActionPreference',
            r'Write-Error',
            r'-ErrorAction',
            r'-ErrorVariable',
            r'\$\?\s*-and\s*\$error',  # $? and $error (读取)
            r'if\s*\(\s*\$error\s*\)',  # if ($error) (读取)
            r'\$error\s*\|',  # $error | (管道，读取)
            r'\$error\s*\.',  # $error.Count等属性读取
            r'\$error\s*\[',  # $error[0]等索引读取
        ]
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 跳过注释行
            if line_stripped.startswith('#'):
                continue
            
            # 检查是否包含问题模式
            for pattern in problematic_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 检查是否是正常用法
                    is_normal = False
                    for normal_pattern in normal_patterns:
                        if re.search(normal_pattern, line, re.IGNORECASE):
                            is_normal = True
                            break
                    
                    if not is_normal:
                        issues.append(f"第{i}行: 不当使用只读变量 $error - {line_stripped}")
        
        return issues
    
    def check_unapproved_verbs(self, content: str, file_path: Path) -> List[str]:
        """检查未批准的PowerShell动词"""
        issues = []
        
        # PowerShell批准的动词列表（部分）
        approved_verbs = {
            'Add', 'Clear', 'Close', 'Copy', 'Enter', 'Exit', 'Find', 'Format',
            'Get', 'Hide', 'Join', 'Lock', 'Move', 'New', 'Open', 'Optimize',
            'Pop', 'Push', 'Redo', 'Remove', 'Rename', 'Reset', 'Resize',
            'Search', 'Select', 'Set', 'Show', 'Skip', 'Split', 'Step',
            'Switch', 'Undo', 'Unlock', 'Watch', 'Backup', 'Checkpoint',
            'Compare', 'Compress', 'Convert', 'ConvertFrom', 'ConvertTo',
            'Dismount', 'Edit', 'Expand', 'Export', 'Group', 'Import',
            'Initialize', 'Limit', 'Merge', 'Mount', 'Out', 'Publish',
            'Restore', 'Save', 'Sync', 'Unpublish', 'Update', 'Approve',
            'Assert', 'Complete', 'Confirm', 'Deny', 'Disable', 'Enable',
            'Install', 'Invoke', 'Register', 'Request', 'Restart', 'Resume',
            'Start', 'Stop', 'Submit', 'Suspend', 'Uninstall', 'Unregister',
            'Wait', 'Debug', 'Measure', 'Ping', 'Repair', 'Resolve',
            'Test', 'Trace', 'Connect', 'Disconnect', 'Read', 'Receive',
            'Send', 'Write', 'Block', 'Grant', 'Protect', 'Revoke',
            'Unblock', 'Unprotect', 'Use'
        }
        
        # 查找函数定义
        function_pattern = r'function\s+([A-Za-z]+-[A-Za-z]+)'
        functions = re.findall(function_pattern, content)
        
        for func_name in functions:
            if '-' in func_name:
                verb = func_name.split('-')[0]
                if verb not in approved_verbs:
                    issues.append(f"函数 {func_name} 使用了未批准的动词: {verb}")
        
        return issues
    
    def check_syntax_issues(self, content: str, file_path: Path) -> List[str]:
        """检查语法问题"""
        issues = []
        
        lines = content.split('\n')
        
        # 检查字符串匹配
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 跳过注释
            if line_stripped.startswith('#'):
                continue
            
            # 检查引号匹配
            single_quotes = line.count("'")
            double_quotes = line.count('"')
            
            if single_quotes % 2 != 0:
                issues.append(f"第{i}行: 单引号不匹配")
            
            if double_quotes % 2 != 0:
                issues.append(f"第{i}行: 双引号不匹配")
        
        # 检查大括号匹配
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces != close_braces:
            issues.append(f"大括号不匹配: {open_braces} 个开括号, {close_braces} 个闭括号")
        
        return issues
    
    def check_file(self, file_path: Path) -> dict:
        """检查单个PowerShell文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        issues = {
            'error_variable': self.check_error_variable_misuse(content, file_path),
            'unapproved_verbs': self.check_unapproved_verbs(content, file_path),
            'syntax_issues': self.check_syntax_issues(content, file_path)
        }
        
        return issues
    
    def check_all_files(self) -> dict:
        """检查所有PowerShell文件"""
        ps_files = list(self.project_root.glob("*.ps1"))
        results = {}
        
        for ps_file in ps_files:
            issues = self.check_file(ps_file)
            if any(issues.values()):  # 只记录有问题的文件
                results[str(ps_file)] = issues
        
        return results
    
    def print_results(self, results: dict):
        """打印检查结果"""
        print("🔍 精确PowerShell问题检测结果")
        print("=" * 50)
        
        if not results:
            print("✅ 未发现任何PowerShell问题！")
            return
        
        total_issues = 0
        
        for file_path, issues in results.items():
            file_name = Path(file_path).name
            print(f"\n📁 文件: {file_name}")
            
            for category, issue_list in issues.items():
                if issue_list:
                    category_name = {
                        'error_variable': '$error变量误用',
                        'unapproved_verbs': '未批准动词',
                        'syntax_issues': '语法问题'
                    }.get(category, category)
                    
                    print(f"  🔴 {category_name}:")
                    for issue in issue_list:
                        print(f"    - {issue}")
                        total_issues += 1
        
        print(f"\n📊 总计发现 {total_issues} 个问题")

def main():
    """主函数"""
    checker = PrecisePowerShellChecker()
    results = checker.check_all_files()
    checker.print_results(results)
    
    return len(results)

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
