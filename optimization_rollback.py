#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化回滚工具
当优化出现问题时，安全恢复到优化前状态
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class OptimizationRollback:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_base = self.project_root.parent
        self.log_file = self.project_root / "rollback_log.txt"
        
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def find_backup_directories(self) -> List[Path]:
        """查找可用的备份目录"""
        backup_dirs = []
        
        # 查找备份目录模式
        patterns = [
            "VisionAI-ClipsMaster-backup-*",
            "*backup*"
        ]
        
        for pattern in patterns:
            for backup_dir in self.backup_base.glob(pattern):
                if backup_dir.is_dir() and backup_dir != self.project_root:
                    backup_dirs.append(backup_dir)
        
        # 按修改时间排序（最新的在前）
        backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return backup_dirs
    
    def find_git_backup_branches(self) -> List[str]:
        """查找Git备份分支"""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            branches = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'backup' in line.lower() and not line.startswith('*'):
                    # 清理分支名
                    branch_name = line.replace('remotes/origin/', '').strip()
                    if branch_name:
                        branches.append(branch_name)
            
            return branches
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return []
    
    def validate_backup(self, backup_path: Path) -> Dict[str, bool]:
        """验证备份完整性"""
        validation_results = {}
        
        # 检查关键文件
        critical_files = [
            "simple_ui_fixed.py",
            "src/core/__init__.py",
            "configs/model_config.yaml",
            "requirements.txt"
        ]
        
        for file_path in critical_files:
            full_path = backup_path / file_path
            validation_results[file_path] = full_path.exists()
        
        return validation_results
    
    def rollback_from_directory(self, backup_dir: Path) -> bool:
        """从目录备份恢复"""
        try:
            self.log(f"开始从目录备份恢复: {backup_dir}")
            
            # 验证备份
            validation = self.validate_backup(backup_dir)
            missing_files = [k for k, v in validation.items() if not v]
            
            if missing_files:
                self.log(f"备份不完整，缺失文件: {missing_files}", "WARNING")
                response = input("备份不完整，是否继续？(y/N): ")
                if response.lower() != 'y':
                    return False
            
            # 创建当前状态的临时备份
            temp_backup = self.project_root.parent / f"temp-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.log(f"创建临时备份: {temp_backup}")
            shutil.copytree(self.project_root, temp_backup, dirs_exist_ok=True)
            
            # 清理当前目录（保留.git）
            for item in self.project_root.iterdir():
                if item.name == '.git':
                    continue
                    
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            # 从备份恢复
            for item in backup_dir.iterdir():
                if item.name == '.git':
                    continue
                    
                dest_path = self.project_root / item.name
                
                if item.is_dir():
                    shutil.copytree(item, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_path)
            
            self.log("目录备份恢复完成")
            
            # 清理临时备份
            shutil.rmtree(temp_backup)
            
            return True
            
        except Exception as e:
            self.log(f"目录备份恢复失败: {e}", "ERROR")
            return False
    
    def rollback_from_git_branch(self, branch_name: str) -> bool:
        """从Git分支恢复"""
        try:
            self.log(f"开始从Git分支恢复: {branch_name}")
            
            # 检查当前Git状态
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                self.log("检测到未提交的更改，创建临时提交")
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.project_root,
                    check=True
                )
                subprocess.run(
                    ["git", "commit", "-m", f"Temporary commit before rollback - {datetime.now()}"],
                    cwd=self.project_root,
                    check=True
                )
            
            # 切换到备份分支
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=self.project_root,
                check=True
            )
            
            self.log("Git分支恢复完成")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"Git分支恢复失败: {e}", "ERROR")
            return False
    
    def interactive_rollback(self) -> bool:
        """交互式回滚选择"""
        self.log("开始交互式回滚流程")
        
        # 查找可用的恢复选项
        backup_dirs = self.find_backup_directories()
        git_branches = self.find_git_backup_branches()
        
        if not backup_dirs and not git_branches:
            self.log("未找到可用的备份", "ERROR")
            return False
        
        print("\n=== 可用的恢复选项 ===")
        options = []
        
        # 添加目录备份选项
        for i, backup_dir in enumerate(backup_dirs):
            mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)
            print(f"{len(options) + 1}. 目录备份: {backup_dir.name} (创建时间: {mtime})")
            options.append(("directory", backup_dir))
        
        # 添加Git分支选项
        for branch in git_branches:
            print(f"{len(options) + 1}. Git分支: {branch}")
            options.append(("git", branch))
        
        print(f"{len(options) + 1}. 取消回滚")
        
        # 用户选择
        while True:
            try:
                choice = int(input(f"\n请选择恢复选项 (1-{len(options) + 1}): "))
                
                if choice == len(options) + 1:
                    self.log("用户取消回滚")
                    return False
                
                if 1 <= choice <= len(options):
                    option_type, option_value = options[choice - 1]
                    break
                else:
                    print("无效选择，请重新输入")
                    
            except ValueError:
                print("请输入有效数字")
        
        # 确认回滚
        print(f"\n选择的恢复选项: {option_type} - {option_value}")
        confirm = input("确认执行回滚？这将覆盖当前项目状态 (y/N): ")
        
        if confirm.lower() != 'y':
            self.log("用户取消回滚")
            return False
        
        # 执行回滚
        if option_type == "directory":
            return self.rollback_from_directory(option_value)
        elif option_type == "git":
            return self.rollback_from_git_branch(option_value)
        
        return False
    
    def auto_rollback(self) -> bool:
        """自动回滚（选择最新备份）"""
        self.log("开始自动回滚流程")
        
        # 优先使用Git分支
        git_branches = self.find_git_backup_branches()
        if git_branches:
            latest_branch = git_branches[0]  # 假设按时间排序
            self.log(f"使用最新Git分支: {latest_branch}")
            return self.rollback_from_git_branch(latest_branch)
        
        # 使用目录备份
        backup_dirs = self.find_backup_directories()
        if backup_dirs:
            latest_backup = backup_dirs[0]  # 按修改时间排序，最新的在前
            self.log(f"使用最新目录备份: {latest_backup}")
            return self.rollback_from_directory(latest_backup)
        
        self.log("未找到可用的备份", "ERROR")
        return False
    
    def verify_rollback(self) -> bool:
        """验证回滚结果"""
        self.log("验证回滚结果")
        
        try:
            # 检查关键文件
            critical_files = [
                "simple_ui_fixed.py",
                "src/core/__init__.py",
                "configs/model_config.yaml"
            ]
            
            for file_path in critical_files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    self.log(f"关键文件缺失: {file_path}", "ERROR")
                    return False
            
            # 尝试基本导入测试
            sys.path.insert(0, str(self.project_root))
            try:
                import src.core
                self.log("核心模块导入成功")
            except ImportError as e:
                self.log(f"核心模块导入失败: {e}", "ERROR")
                return False
            
            self.log("回滚验证通过")
            return True
            
        except Exception as e:
            self.log(f"回滚验证失败: {e}", "ERROR")
            return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    rollback = OptimizationRollback(project_root)
    
    # 检查命令行参数
    auto_mode = "--auto" in sys.argv
    
    if auto_mode:
        success = rollback.auto_rollback()
    else:
        success = rollback.interactive_rollback()
    
    if success:
        # 验证回滚结果
        if rollback.verify_rollback():
            print("\n✅ 回滚成功！项目已恢复到优化前状态")
            print("建议运行功能测试确认所有功能正常")
        else:
            print("\n⚠️ 回滚完成但验证失败，请手动检查项目状态")
            return 1
    else:
        print("\n❌ 回滚失败")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
