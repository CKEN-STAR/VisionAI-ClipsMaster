#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster CSS警告清理脚本

专门清理PyQt6不支持的CSS属性，减少控制台警告

作者: CKEN
版本: v1.0
日期: 2025-07-12
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class CSSCleaner:
    """CSS警告清理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.core_path = self.project_root / "VisionAI-ClipsMaster-Core"
        
        # 不支持的CSS属性列表
        self.unsupported_css = [
            "transform",
            "box-shadow", 
            "text-shadow",
            "transition",
            "-webkit-",
            "-moz-",
            "-ms-",
            "filter",
            "backdrop-filter",
            "clip-path",
            "mask",
            "animation"
        ]
        
        self.cleaned_files = {}
        self.total_warnings_removed = 0
        
        print(f"🧹 VisionAI-ClipsMaster CSS警告清理器")
        print(f"清理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def clean_css_warnings(self):
        """清理CSS警告"""
        print(f"\n{'='*60}")
        print(f"开始清理CSS警告")
        print(f"{'='*60}")
        
        # 查找包含CSS的Python文件
        ui_file = self.core_path / "simple_ui_fixed.py"
        
        if ui_file.exists():
            print(f"\n处理主UI文件: {ui_file.name}")
            self._clean_file_css(ui_file)
        
        # 查找其他可能包含CSS的文件
        for py_file in self.core_path.rglob("*.py"):
            if py_file == ui_file:
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含CSS相关内容
                if any(keyword in content.lower() for keyword in ['setstylesheet', 'qss', 'style=']):
                    print(f"\n处理文件: {py_file.relative_to(self.core_path)}")
                    self._clean_file_css(py_file)
                    
            except Exception as e:
                print(f"  ⚠️ 跳过文件 {py_file.name}: {str(e)}")
        
        self._print_summary()
    
    def _clean_file_css(self, file_path: Path):
        """清理单个文件的CSS"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            warnings_removed = 0
            
            # 查找CSS字符串模式
            css_patterns = [
                r'setStyleSheet\s*\(\s*["\']([^"\']*)["\']',
                r'QSS\s*=\s*["\']([^"\']*)["\']',
                r'style\s*=\s*["\']([^"\']*)["\']'
            ]
            
            for css_pattern in css_patterns:
                def replace_css(match):
                    nonlocal warnings_removed
                    css_content = match.group(1)
                    cleaned_css = self._clean_css_content(css_content)
                    
                    # 计算移除的属性数量
                    original_lines = css_content.count('\n') + 1
                    cleaned_lines = cleaned_css.count('\n') + 1
                    warnings_removed += max(0, original_lines - cleaned_lines)
                    
                    return match.group(0).replace(css_content, cleaned_css)
                
                content = re.sub(css_pattern, replace_css, content, flags=re.DOTALL)
            
            # 如果有修改，保存文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.cleaned_files[str(file_path.relative_to(self.core_path))] = warnings_removed
                self.total_warnings_removed += warnings_removed
                print(f"  ✅ 清理完成: 移除 {warnings_removed} 个CSS警告")
            else:
                print(f"  ℹ️ 无需清理")
                
        except Exception as e:
            print(f"  ❌ 清理失败: {str(e)}")
    
    def _clean_css_content(self, css_content: str) -> str:
        """清理CSS内容"""
        lines = css_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # 检查是否包含不支持的CSS属性
            should_keep = True
            
            for unsupported in self.unsupported_css:
                if unsupported in line.lower():
                    should_keep = False
                    break
            
            if should_keep:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _print_summary(self):
        """打印清理总结"""
        print(f"\n{'='*60}")
        print(f"CSS清理总结")
        print(f"{'='*60}")
        
        print(f"📊 清理统计:")
        print(f"  处理文件: {len(self.cleaned_files)}")
        print(f"  移除警告: {self.total_warnings_removed}")
        
        if self.cleaned_files:
            print(f"\n📋 详细清理结果:")
            for file_path, warnings in self.cleaned_files.items():
                print(f"  {file_path}: {warnings} 个警告")
        
        if self.total_warnings_removed > 0:
            print(f"\n🎉 CSS警告清理成功！")
            print(f"建议: 重新启动UI验证警告是否减少")
        else:
            print(f"\n💡 未发现需要清理的CSS警告")
            print(f"可能原因: CSS已经是PyQt6兼容的格式")


def main():
    """主函数"""
    try:
        cleaner = CSSCleaner()
        cleaner.clean_css_warnings()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n清理被用户中断")
        return 1
    except Exception as e:
        print(f"\n清理过程出错: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
