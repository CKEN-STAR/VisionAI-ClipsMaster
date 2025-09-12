#!/usr/bin/env python3
"""
高级PowerShell修复工具
修复引号不匹配等语法问题
"""

import re
import shutil
from pathlib import Path
from typing import List, Tuple

class AdvancedPowerShellFixer:
    """高级PowerShell修复器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup2")
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def fix_quote_mismatch(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复引号不匹配问题"""
        fixes = []
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            original_line = line
            
            # 跳过注释行
            if line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
            
            # 检查双引号
            double_quotes = line.count('"')
            if double_quotes % 2 != 0:
                # 尝试修复双引号不匹配
                line = self._fix_double_quotes(line)
                if line != original_line:
                    fixes.append(f"修复第{i+1}行双引号不匹配")
            
            # 检查单引号
            single_quotes = line.count("'")
            if single_quotes % 2 != 0:
                # 尝试修复单引号不匹配
                line = self._fix_single_quotes(line)
                if line != original_line:
                    fixes.append(f"修复第{i+1}行单引号不匹配")
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes
    
    def _fix_double_quotes(self, line: str) -> str:
        """修复双引号不匹配"""
        # 常见的修复策略
        
        # 1. 如果行末缺少引号
        if line.count('"') == 1 and not line.strip().endswith('"'):
            # 检查是否是字符串开始
            quote_pos = line.find('"')
            if quote_pos >= 0:
                # 在行末添加引号
                return line + '"'
        
        # 2. 如果行中有奇数个引号，尝试转义
        if line.count('"') % 2 != 0:
            # 查找可能需要转义的引号
            # 这是一个简化的策略，实际情况可能更复杂
            parts = line.split('"')
            if len(parts) >= 3:
                # 尝试转义中间的引号
                middle_parts = parts[1:-1]
                for i, part in enumerate(middle_parts):
                    if i % 2 == 1:  # 奇数位置的部分可能需要转义
                        middle_parts[i] = part.replace('"', '`"')
                
                return '"'.join([parts[0]] + middle_parts + [parts[-1]])
        
        return line
    
    def _fix_single_quotes(self, line: str) -> str:
        """修复单引号不匹配"""
        # 类似双引号的修复策略
        if line.count("'") == 1 and not line.strip().endswith("'"):
            quote_pos = line.find("'")
            if quote_pos >= 0:
                return line + "'"
        
        return line
    
    def fix_string_literals(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复字符串字面量问题"""
        fixes = []
        
        # 修复常见的字符串问题
        patterns = [
            # 修复here-string的问题
            (r'@"\s*\n(.*?)\n"@', r'@"\n\1\n"@'),
            # 修复转义字符问题
            (r'\\n', r'`n'),
            (r'\\t', r'`t'),
            (r'\\r', r'`r'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                fixes.append(f"修复字符串字面量格式")
        
        return content, fixes
    
    def fix_encoding_characters(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        """修复编码字符问题"""
        fixes = []
        
        # 常见的编码问题字符映射
        char_mappings = [
            ('鈥?', '"'),
            ('鈥?', '"'),
            ('鈥?', "'"),
            ('鈥?', "'"),
            ('鈥?', '...'),
            ('鈥?', '-'),
            ('鈥?', '-'),
            ('锟?', ''),  # 常见的乱码
            ('锟斤拷', ''),
            ('鎻?', ''),
            ('鍙?', ''),
            ('鐨?', ''),
            ('涓?', ''),
            ('鏄?', ''),
            ('鍦?', ''),
            ('浜?', ''),
            ('鏈?', ''),
            ('涓?', ''),
            ('鍙?', ''),
            ('鍒?', ''),
            ('鍜?', ''),
            ('鐨?', ''),
            ('鍦?', ''),
            ('鏈?', ''),
            ('鏄?', ''),
            ('涓?', ''),
            ('鍙?', ''),
            ('鍒?', ''),
            ('鍜?', ''),
        ]
        
        for old_char, new_char in char_mappings:
            if old_char in content:
                content = content.replace(old_char, new_char)
                fixes.append(f"修复编码字符: {old_char} -> {new_char}")
        
        return content, fixes
    
    def fix_file(self, file_path: Path) -> List[str]:
        """修复单个PowerShell文件"""
        print(f"🔧 修复文件: {file_path.name}")
        
        # 备份原文件
        backup_path = self.backup_file(file_path)
        print(f"📄 已备份到: {backup_path.name}")
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        all_fixes = []
        
        # 应用各种修复
        content, fixes = self.fix_quote_mismatch(content, file_path)
        all_fixes.extend(fixes)
        
        content, fixes = self.fix_string_literals(content, file_path)
        all_fixes.extend(fixes)
        
        content, fixes = self.fix_encoding_characters(content, file_path)
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
        ps_files = list(self.project_root.glob("*.ps1"))
        
        if not ps_files:
            print("❌ 未找到PowerShell文件")
            return {}
        
        print(f"🔍 找到 {len(ps_files)} 个PowerShell文件")
        
        results = {}
        
        for ps_file in ps_files:
            fixes = self.fix_file(ps_file)
            results[str(ps_file)] = fixes
            print()
        
        return results

def main():
    """主函数"""
    print("🚀 高级PowerShell修复工具")
    print("=" * 50)
    
    fixer = AdvancedPowerShellFixer()
    results = fixer.fix_all_files()
    
    total_fixes = sum(len(fixes) for fixes in results.values())
    print(f"📊 总计应用了 {total_fixes} 个修复")
    
    return 0

if __name__ == "__main__":
    exit(main())
