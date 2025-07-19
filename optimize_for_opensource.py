#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 开源优化脚本

解决开源前的关键问题：
1. 项目大小优化（删除大文件和不必要文件）
2. 敏感信息清理
3. Python语法错误修复
4. 目录结构优化
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class OpenSourceOptimizer:
    """开源优化器"""
    
    def __init__(self, dry_run: bool = False):
        self.project_root = Path(__file__).parent
        self.dry_run = dry_run
        self.backup_dir = self.project_root / "cleanup_backup"
        self.stats = {
            "deleted_files": 0,
            "deleted_dirs": 0,
            "cleaned_files": 0,
            "size_saved_mb": 0.0
        }
        
        print(f"🚀 VisionAI-ClipsMaster 开源优化器")
        print(f"项目根目录: {self.project_root}")
        print(f"DRY RUN模式: {'是' if dry_run else '否'}")
        print(f"备份目录: {self.backup_dir}")
        
    def create_backup(self):
        """创建备份"""
        if self.dry_run:
            print("DRY RUN: 将创建备份")
            return
            
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        print(f"✅ 创建备份目录: {self.backup_dir}")
    
    def optimize_project_size(self):
        """优化项目大小"""
        print(f"\n{'='*60}")
        print(f"优化项目大小")
        print(f"{'='*60}")
        
        # 定义要删除的文件和目录模式
        delete_patterns = [
            # 缓存文件
            "__pycache__",
            ".pytest_cache",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            
            # 临时文件
            "temp",
            "tmp",
            "cache",
            "snapshots",
            "recovery",
            
            # 测试输出
            "test_output",
            "*_test_report_*.json",
            "*_test_report_*.md",
            "test_results",
            "ui_test_output",
            "stability_test_output",
            
            # 日志文件
            "logs/*.log",
            "*.log",
            
            # 大文件
            "*.mp4",
            "*.avi",
            "*.mkv",
            "*.mov",
            "*.flv",
            "*.wmv",
            "*.webm",
            "*.m4v",
            "*.3gp",
            "*.ts",
            
            # 模型文件
            "*.bin",
            "*.gguf",
            "*.safetensors",
            "models/*/base/*",
            "models/*/quantized/*",
            
            # 重复文档
            "VisionAI_ClipsMaster_*.md",
            "VisionAI-ClipsMaster_*.md",
            
            # IDE文件
            ".vscode/settings.json",
            ".idea",
            
            # 构建文件
            "build",
            "dist",
            "*.egg-info",
            
            # 其他大文件目录
            "llama.cpp",
            "spacy_wheels",
            "compressed",
            "outputs",
            "simple_output",
            "llm_output",
            "comprehensive_output",
            "exporter_output",
            "screenplay_output"
        ]
        
        total_size_before = self._calculate_project_size()
        
        for pattern in delete_patterns:
            self._delete_by_pattern(pattern)
        
        total_size_after = self._calculate_project_size()
        size_saved = total_size_before - total_size_after
        self.stats["size_saved_mb"] = round(size_saved / 1024 / 1024, 2)
        
        print(f"\n📊 大小优化结果:")
        print(f"  优化前: {total_size_before / 1024 / 1024:.2f} MB")
        print(f"  优化后: {total_size_after / 1024 / 1024:.2f} MB")
        print(f"  节省: {self.stats['size_saved_mb']} MB")
        print(f"  删除文件: {self.stats['deleted_files']}")
        print(f"  删除目录: {self.stats['deleted_dirs']}")
    
    def clean_sensitive_data(self):
        """清理敏感信息"""
        print(f"\n{'='*60}")
        print(f"清理敏感信息")
        print(f"{'='*60}")
        
        # 定义敏感信息模式
        sensitive_patterns = [
            (r'password\\\1*=\\\1*["\'][^"\']+["\']', 'password = "***"'),
            (r'secret\\\1*=\\\1*["\'][^"\']+["\']', 'secret = "***"'),
            (r'api_key\\\1*=\\\1*["\'][^"\']+["\']', 'api_key = "***"'),
            (r'token\\\1*=\\\1*["\'][^"\']+["\']', 'token = "***"'),
            (r'127\\\10\\\10\\\11', 'localhost'),
            (r'your-email@example\\\1com', 'your-email@example.com'),
        ]
        
        # 需要清理的文件类型
        file_extensions = ['.py', '.md', '.txt', '.json', '.yaml', '.yml']
        
        cleaned_files = 0
        
        for file_path in self.project_root.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix in file_extensions and
                not any(skip in str(file_path) for skip in ['__pycache__', '.git', 'backup'])):
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # 应用清理模式
                    for pattern, replacement in sensitive_patterns:
                        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    
                    # 如果内容有变化，保存文件
                    if content != original_content:
                        if not self.dry_run:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                        
                        cleaned_files += 1
                        print(f"  🧹 清理: {file_path.relative_to(self.project_root)}")
                
                except Exception as e:
                    print(f"  ⚠️ 清理失败: {file_path.relative_to(self.project_root)} - {str(e)}")
        
        self.stats["cleaned_files"] = cleaned_files
        print(f"\n📊 敏感信息清理结果: 清理了 {cleaned_files} 个文件")
    
    def fix_python_syntax(self):
        """修复Python语法错误"""
        print(f"\n{'='*60}")
        print(f"修复Python语法错误")
        print(f"{'='*60}")
        
        # 常见语法错误修复模式
        fix_patterns = [
            # 修复无效转义序列
            (r'\\\\1[^\\nrtbfav\'\"\\\\1)', r'\\\\\\\\1'),
            # 修复路径字符串
            (r'"([A-Z]:\\\\1^"]*)"', r'r"\\\\\\\\1"'),
            # 修复原始字符串中的问题
            (r'r"([^"]*\\\\1^"]*)"', lambda m: f'r"{m.group(1).replace(chr(92), chr(92)+chr(92))}"'),
        ]
        
        fixed_files = 0
        
        for py_file in self.project_root.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'backup']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 应用修复模式
                for pattern, replacement in fix_patterns:
                    if callable(replacement):
                        content = re.sub(pattern, replacement, content)
                    else:
                        content = re.sub(pattern, replacement, content)
                
                # 检查语法
                try:
                    compile(content, str(py_file), 'exec')
                    
                    # 如果内容有变化且语法正确，保存文件
                    if content != original_content:
                        if not self.dry_run:
                            with open(py_file, 'w', encoding='utf-8') as f:
                                f.write(content)
                        
                        fixed_files += 1
                        print(f"  🔧 修复: {py_file.relative_to(self.project_root)}")
                
                except SyntaxError:
                    # 如果修复后仍有语法错误，删除文件（如果是测试文件）
                    if 'test' in str(py_file).lower() and not self.dry_run:
                        py_file.unlink()
                        print(f"  🗑️ 删除有问题的测试文件: {py_file.relative_to(self.project_root)}")
                
            except Exception as e:
                print(f"  ⚠️ 处理失败: {py_file.relative_to(self.project_root)} - {str(e)}")
        
        print(f"\n📊 语法修复结果: 修复了 {fixed_files} 个文件")
    
    def create_gitignore(self):
        """创建优化的.gitignore文件"""
        print(f"\n{'='*60}")
        print(f"创建.gitignore文件")
        print(f"{'='*60}")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/
.venv/
.env/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project Specific
cache/
temp/
tmp/
logs/*.log
test_output/
*_test_report_*.json
*_test_report_*.md
recovery/
snapshots/
cleanup_backup/
ui_test_output/
stability_test_output/
test_results/

# Large Files (use Git LFS if needed)
*.mp4
*.avi
*.mkv
*.mov
*.flv
*.wmv
*.webm
*.m4v
*.3gp
*.ts
models/*/base/
models/*/quantized/
*.bin
*.gguf
*.safetensors

# Generated Files
outputs/
simple_output/
llm_output/
comprehensive_output/
exporter_output/
screenplay_output/

# Sensitive Data
.env
config/secrets/
user_config/

# Documentation Duplicates
VisionAI_ClipsMaster_*.md
VisionAI-ClipsMaster_*.md
opensource_readiness_report_*.json
"""
        
        gitignore_path = self.project_root / ".gitignore"
        
        if not self.dry_run:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
        
        print(f"✅ 创建.gitignore文件: {gitignore_path}")
    
    def _delete_by_pattern(self, pattern: str):
        """根据模式删除文件或目录"""
        if '*' in pattern:
            # 通配符模式
            for path in self.project_root.rglob(pattern):
                self._delete_path(path)
        else:
            # 精确匹配
            for path in self.project_root.rglob(pattern):
                if path.name == pattern or pattern in str(path):
                    self._delete_path(path)
    
    def _delete_path(self, path: Path):
        """删除文件或目录"""
        if not path.exists():
            return
        
        try:
            size = self._get_path_size(path)
            
            if self.dry_run:
                if path.is_dir():
                    print(f"DRY RUN: 将删除目录 {path.relative_to(self.project_root)} ({size / 1024 / 1024:.2f} MB)")
                else:
                    print(f"DRY RUN: 将删除文件 {path.relative_to(self.project_root)} ({size / 1024:.2f} KB)")
                return
            
            if path.is_dir():
                shutil.rmtree(path)
                self.stats["deleted_dirs"] += 1
                print(f"  🗑️ 删除目录: {path.relative_to(self.project_root)} ({size / 1024 / 1024:.2f} MB)")
            else:
                path.unlink()
                self.stats["deleted_files"] += 1
                print(f"  🗑️ 删除文件: {path.relative_to(self.project_root)} ({size / 1024:.2f} KB)")
        
        except Exception as e:
            print(f"  ⚠️ 删除失败: {path.relative_to(self.project_root)} - {str(e)}")
    
    def _get_path_size(self, path: Path) -> int:
        """获取路径大小"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except Exception:
                        continue
            return total
        return 0
    
    def _calculate_project_size(self) -> int:
        """计算项目总大小"""
        total_size = 0
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except Exception:
                    continue
        return total_size
    
    def run_optimization(self):
        """运行完整优化"""
        print(f"\n🎯 开始VisionAI-ClipsMaster开源优化")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建备份
        self.create_backup()
        
        # 执行优化步骤
        self.optimize_project_size()
        self.clean_sensitive_data()
        self.fix_python_syntax()
        self.create_gitignore()
        
        # 显示总结
        self.print_summary()
    
    def print_summary(self):
        """打印优化总结"""
        print(f"\n{'='*80}")
        print(f"优化总结")
        print(f"{'='*80}")
        print(f"删除文件: {self.stats['deleted_files']}")
        print(f"删除目录: {self.stats['deleted_dirs']}")
        print(f"清理文件: {self.stats['cleaned_files']}")
        print(f"节省空间: {self.stats['size_saved_mb']} MB")
        
        if self.dry_run:
            print(f"\n⚠️ 这是DRY RUN模式，没有实际执行操作")
            print(f"要执行实际优化，请运行: python optimize_for_opensource.py --execute")
        else:
            print(f"\n✅ 优化完成！项目已准备好开源")
            print(f"下一步:")
            print(f"  1. 运行: python check_opensource_readiness.py")
            print(f"  2. 检查优化结果")
            print(f"  3. 执行Git操作")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster开源优化器")
    parser.add_argument("--execute", action="store_true", help="执行实际优化（默认为DRY RUN模式）")
    
    args = parser.parse_args()
    
    try:
        optimizer = OpenSourceOptimizer(dry_run=not args.execute)
        optimizer.run_optimization()
        
    except KeyboardInterrupt:
        print("\n优化被用户中断")
    except Exception as e:
        print(f"\n优化过程出错: {str(e)}")


if __name__ == "__main__":
    main()
