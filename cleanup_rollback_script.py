#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 项目清理回滚脚本
用于在误删文件后恢复项目状态
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

class CleanupRollback:
    def __init__(self):
        self.backup_dir = "cleanup_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.deleted_files_log = "deleted_files_log.json"
        self.git_available = self.check_git_available()
        
    def check_git_available(self):
        """检查Git是否可用"""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def create_backup_before_cleanup(self, files_to_delete):
        """在删除前创建备份"""
        print(f"创建备份目录: {self.backup_dir}")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        backup_manifest = {
            "backup_time": datetime.now().isoformat(),
            "files": []
        }
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                # 创建相对路径的备份结构
                backup_path = os.path.join(self.backup_dir, file_path)
                backup_dir = os.path.dirname(backup_path)
                
                if backup_dir:
                    os.makedirs(backup_dir, exist_ok=True)
                
                if os.path.isfile(file_path):
                    shutil.copy2(file_path, backup_path)
                    backup_manifest["files"].append({
                        "original": file_path,
                        "backup": backup_path,
                        "type": "file"
                    })
                elif os.path.isdir(file_path):
                    shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
                    backup_manifest["files"].append({
                        "original": file_path,
                        "backup": backup_path,
                        "type": "directory"
                    })
        
        # 保存备份清单
        with open(os.path.join(self.backup_dir, "backup_manifest.json"), 'w', encoding='utf-8') as f:
            json.dump(backup_manifest, f, indent=2, ensure_ascii=False)
        
        print(f"备份完成，共备份 {len(backup_manifest['files'])} 个项目")
        return backup_manifest
    
    def create_git_checkpoint(self):
        """创建Git检查点"""
        if not self.git_available:
            print("Git不可用，跳过Git检查点创建")
            return None
            
        try:
            # 检查是否有未提交的更改
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                # 有未提交的更改，创建临时提交
                subprocess.run(['git', 'add', '.'], check=True)
                commit_msg = f"Cleanup checkpoint - {datetime.now().isoformat()}"
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                
                # 获取提交哈希
                result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                      capture_output=True, text=True, check=True)
                commit_hash = result.stdout.strip()
                
                print(f"Git检查点已创建: {commit_hash}")
                return commit_hash
            else:
                # 获取当前提交哈希
                result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                      capture_output=True, text=True, check=True)
                commit_hash = result.stdout.strip()
                print(f"当前Git状态: {commit_hash}")
                return commit_hash
                
        except subprocess.CalledProcessError as e:
            print(f"Git操作失败: {e}")
            return None
    
    def restore_from_backup(self, backup_dir=None):
        """从备份恢复文件"""
        if backup_dir is None:
            # 查找最新的备份目录
            backup_dirs = [d for d in os.listdir('.') if d.startswith('cleanup_backup_')]
            if not backup_dirs:
                print("未找到备份目录")
                return False
            backup_dir = max(backup_dirs)
        
        manifest_path = os.path.join(backup_dir, "backup_manifest.json")
        if not os.path.exists(manifest_path):
            print(f"备份清单文件不存在: {manifest_path}")
            return False
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"开始从备份恢复文件: {backup_dir}")
        restored_count = 0
        
        for item in manifest["files"]:
            original_path = item["original"]
            backup_path = item["backup"]
            item_type = item["type"]
            
            if os.path.exists(backup_path):
                if item_type == "file":
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.copy2(backup_path, original_path)
                elif item_type == "directory":
                    if os.path.exists(original_path):
                        shutil.rmtree(original_path)
                    shutil.copytree(backup_path, original_path)
                
                restored_count += 1
                print(f"已恢复: {original_path}")
            else:
                print(f"备份文件不存在: {backup_path}")
        
        print(f"恢复完成，共恢复 {restored_count} 个项目")
        return True
    
    def restore_from_git(self, commit_hash=None):
        """从Git恢复"""
        if not self.git_available:
            print("Git不可用，无法从Git恢复")
            return False
        
        try:
            if commit_hash:
                subprocess.run(['git', 'reset', '--hard', commit_hash], check=True)
                print(f"已从Git恢复到提交: {commit_hash}")
            else:
                subprocess.run(['git', 'reset', '--hard', 'HEAD'], check=True)
                print("已从Git恢复到最新提交")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git恢复失败: {e}")
            return False
    
    def list_available_backups(self):
        """列出可用的备份"""
        backup_dirs = [d for d in os.listdir('.') if d.startswith('cleanup_backup_')]
        if not backup_dirs:
            print("未找到任何备份")
            return []
        
        print("可用的备份:")
        for backup_dir in sorted(backup_dirs, reverse=True):
            manifest_path = os.path.join(backup_dir, "backup_manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                print(f"  {backup_dir} - {manifest['backup_time']} ({len(manifest['files'])} 个项目)")
            else:
                print(f"  {backup_dir} - 清单文件缺失")
        
        return backup_dirs

def main():
    """主函数 - 提供交互式恢复选项"""
    rollback = CleanupRollback()
    
    print("VisionAI-ClipsMaster 清理回滚工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 列出可用备份")
        print("2. 从备份恢复")
        print("3. 从Git恢复")
        print("4. 退出")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == '1':
            rollback.list_available_backups()
        
        elif choice == '2':
            backups = rollback.list_available_backups()
            if backups:
                backup_choice = input("输入备份目录名称 (或按Enter选择最新): ").strip()
                if not backup_choice:
                    backup_choice = max(backups)
                rollback.restore_from_backup(backup_choice)
        
        elif choice == '3':
            commit_hash = input("输入Git提交哈希 (或按Enter恢复到HEAD): ").strip()
            if not commit_hash:
                commit_hash = None
            rollback.restore_from_git(commit_hash)
        
        elif choice == '4':
            print("退出回滚工具")
            break
        
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
