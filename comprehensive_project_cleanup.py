#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 项目文档和测试报告清理工具
按照用户要求进行完整备份、识别重要文档、删除临时文件的清理操作
"""

import os
import sys
import json
import time
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

class ComprehensiveProjectCleanup:
    """综合项目清理工具"""
    
    def __init__(self):
        self.project_root = Path(".")
        self.backup_dir = self.project_root / "backup"
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "backup_status": {},
            "files_to_keep": [],
            "files_to_delete": [],
            "deletion_results": {},
            "summary": {}
        }
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "error"
    
    def step1_create_complete_backup(self) -> Dict[str, Any]:
        """第一步：创建完整备份"""
        print("🔄 第一步：创建完整备份")
        print("=" * 50)
        
        backup_result = {
            "status": "success",
            "backup_dir": str(self.backup_dir),
            "files_backed_up": [],
            "backup_errors": [],
            "file_counts": {},
            "total_size_mb": 0
        }
        
        try:
            # 确保backup目录存在
            self.backup_dir.mkdir(exist_ok=True)
            print(f"✓ 备份目录已准备: {self.backup_dir}")
            
            # 定义需要备份的文件类型
            backup_patterns = [
                "*.md",      # Markdown文档
                "*.json",    # JSON文件
                "*.txt",     # 文本文档
                "*test*.py", # 测试脚本
                "*_test_*.py",
                "*_TEST_*.py",
                "*_REPORT_*.py"
            ]
            
            files_to_backup = set()
            
            # 收集所有需要备份的文件
            for pattern in backup_patterns:
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        # 排除backup目录本身
                        if not str(file_path).startswith(str(self.backup_dir)):
                            files_to_backup.add(file_path)
            
            print(f"📁 发现 {len(files_to_backup)} 个文件需要备份")
            
            # 按文件类型统计
            file_types = {}
            total_size = 0
            
            for file_path in files_to_backup:
                file_ext = file_path.suffix.lower()
                if file_ext not in file_types:
                    file_types[file_ext] = {"count": 0, "size": 0}
                
                try:
                    file_size = file_path.stat().st_size
                    file_types[file_ext]["count"] += 1
                    file_types[file_ext]["size"] += file_size
                    total_size += file_size
                    
                    # 检查文件是否已经在backup目录中
                    backup_file_path = self.backup_dir / file_path.name
                    
                    if backup_file_path.exists():
                        # 比较文件哈希值
                        original_hash = self.calculate_file_hash(file_path)
                        backup_hash = self.calculate_file_hash(backup_file_path)
                        
                        if original_hash == backup_hash:
                            print(f"  ⏭️ 跳过已备份文件: {file_path.name}")
                            backup_result["files_backed_up"].append(f"{file_path.name} (已存在)")
                            continue
                        else:
                            print(f"  🔄 更新备份文件: {file_path.name}")
                    
                    # 复制文件到备份目录
                    shutil.copy2(file_path, backup_file_path)
                    backup_result["files_backed_up"].append(str(file_path.name))
                    print(f"  ✓ 已备份: {file_path.name} ({file_size/1024:.1f}KB)")
                    
                except Exception as e:
                    error_msg = f"备份失败 {file_path.name}: {str(e)}"
                    backup_result["backup_errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")
            
            backup_result["file_counts"] = file_types
            backup_result["total_size_mb"] = total_size / 1024 / 1024
            
            print(f"\n📊 备份统计:")
            for ext, info in file_types.items():
                print(f"  {ext or '无扩展名'}: {info['count']} 个文件, {info['size']/1024/1024:.1f}MB")
            print(f"  总计: {len(files_to_backup)} 个文件, {total_size/1024/1024:.1f}MB")
            
            # 验证备份完整性
            backup_files = list(self.backup_dir.glob("*"))
            print(f"\n🔍 备份验证: 备份目录包含 {len(backup_files)} 个文件")
            
            if len(backup_result["backup_errors"]) == 0:
                print("✅ 备份完成，无错误")
            else:
                print(f"⚠️ 备份完成，但有 {len(backup_result['backup_errors'])} 个错误")
                
        except Exception as e:
            backup_result["status"] = "failure"
            backup_result["error"] = str(e)
            print(f"❌ 备份过程失败: {e}")
        
        self.cleanup_report["backup_status"] = backup_result
        return backup_result
    
    def step2_identify_important_documents(self) -> List[str]:
        """第二步：识别需要保留的重要文档"""
        print("\n🔄 第二步：识别需要保留的重要文档")
        print("=" * 50)
        
        # 定义重要文档模式
        important_patterns = [
            "README.md",
            "INSTALLATION.md", 
            "QUICK_START.md",
            "USER_GUIDE.md",
            "API_REFERENCE.md",
            "TECHNICAL_SPECS.md",
            "DEPLOYMENT.md",
            "TROUBLESHOOTING.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            "LICENSE",
            "FAQ.md",
            "USAGE.md",
            "DEVELOPMENT.md",
            "PACKAGING_GUIDE.md",
            "DOCUMENTATION_INDEX.md",
            "CODE_OF_CONDUCT.md"
        ]
        
        # 配置文件和重要目录
        important_dirs = [
            "configs",
            "src", 
            "ui",
            "docs",
            "examples"
        ]
        
        files_to_keep = []
        
        # 检查重要文档
        for pattern in important_patterns:
            file_path = self.project_root / pattern
            if file_path.exists():
                files_to_keep.append(str(file_path))
                print(f"  ✓ 保留重要文档: {pattern}")
        
        # 检查重要目录下的文档
        for dir_name in important_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                for md_file in dir_path.rglob("*.md"):
                    if md_file.is_file():
                        files_to_keep.append(str(md_file))
                        print(f"  ✓ 保留目录文档: {md_file.relative_to(self.project_root)}")
        
        # 核心功能文件（绝对不能删除）
        core_files = [
            "simple_ui_fixed.py",
            "main.py",
            "app.py",
            "requirements.txt",
            "setup.py",
            "pyproject.toml"
        ]
        
        for core_file in core_files:
            file_path = self.project_root / core_file
            if file_path.exists():
                files_to_keep.append(str(file_path))
                print(f"  ✓ 保留核心文件: {core_file}")
        
        print(f"\n📋 总计保留 {len(files_to_keep)} 个重要文件")
        self.cleanup_report["files_to_keep"] = files_to_keep
        return files_to_keep
    
    def step3_identify_temporary_files(self) -> List[str]:
        """第三步：识别可以删除的临时文件"""
        print("\n🔄 第三步：识别可以删除的临时文件")
        print("=" * 50)
        
        # 定义临时文件模式
        temp_patterns = [
            "*test_report*.json",
            "*_test_*.json", 
            "*_REPORT_*.json",
            "*_report_*.json",
            "comprehensive_*_test*.py",
            "detailed_*_test*.py",
            "*_functionality_test*.py",
            "*_compatibility_test*.py",
            "*_verification_test*.py",
            "*_integration_test*.py",
            "exception_handling_test.py",
            "output_quality_verification_test.py",
            "performance_*_test*.py",
            "model_training_*_test*.py"
        ]
        
        # 临时报告文档模式
        temp_report_patterns = [
            "COMPREHENSIVE_*_REPORT.md",
            "FINAL_*_REPORT.md", 
            "*_TEST_REPORT.md",
            "*_VERIFICATION_REPORT.md",
            "*_FUNCTIONALITY_TEST_*.md",
            "*_COMPREHENSIVE_*.md",
            "*_E2E_*.md"
        ]
        
        files_to_delete = []
        
        # 收集临时JSON文件
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    files_to_delete.append(str(file_path))
                    print(f"  🗑️ 标记删除: {file_path.name}")
        
        # 收集临时报告文档
        for pattern in temp_report_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    files_to_delete.append(str(file_path))
                    print(f"  🗑️ 标记删除: {file_path.name}")
        
        # 特定的测试报告文件
        specific_temp_files = [
            "COMPREHENSIVE_E2E_TEST_FINAL_REPORT.md",
            "COMPREHENSIVE_FUNCTIONALITY_TEST_FINAL_REPORT.md",
            "Test_Reports_Cleanup_Summary.md",
            "PROJECT_CLEANUP_REPORT.md"
        ]
        
        for temp_file in specific_temp_files:
            file_path = self.project_root / temp_file
            if file_path.exists():
                files_to_delete.append(str(file_path))
                print(f"  🗑️ 标记删除特定文件: {temp_file}")
        
        print(f"\n📋 总计标记删除 {len(files_to_delete)} 个临时文件")
        self.cleanup_report["files_to_delete"] = files_to_delete
        return files_to_delete
    
    def run_complete_cleanup(self):
        """运行完整的清理流程"""
        print("🚀 开始VisionAI-ClipsMaster项目清理")
        print("=" * 80)
        
        try:
            # 第一步：创建完整备份
            backup_result = self.step1_create_complete_backup()
            
            if backup_result["status"] != "success":
                print("❌ 备份失败，停止清理操作")
                return False
            
            # 第二步：识别重要文档
            files_to_keep = self.step2_identify_important_documents()
            
            # 第三步：识别临时文件
            files_to_delete = self.step3_identify_temporary_files()
            
            # 安全检查：确保不删除重要文件
            safe_files_to_delete = []
            for file_path in files_to_delete:
                if file_path not in files_to_keep:
                    safe_files_to_delete.append(file_path)
                else:
                    print(f"⚠️ 安全检查：跳过重要文件 {Path(file_path).name}")
            
            print(f"\n🛡️ 安全检查完成：{len(files_to_delete)} → {len(safe_files_to_delete)} 个文件待删除")
            
            # 生成报告（不执行实际删除）
            report_file = self.generate_cleanup_report(safe_files_to_delete)
            
            print(f"\n✅ 项目清理分析完成！")
            print(f"📄 详细报告: {report_file}")
            print(f"⚠️ 注意：实际删除操作需要手动确认")
            
            return True
            
        except Exception as e:
            print(f"❌ 清理过程发生异常: {e}")
            return False
    
    def generate_cleanup_report(self, files_to_delete: List[str]) -> str:
        """生成清理报告"""
        print("\n📊 生成清理报告")
        print("=" * 50)
        
        # 计算总结信息
        backup_status = self.cleanup_report["backup_status"]
        
        summary = {
            "backup_files_count": len(backup_status.get("files_backed_up", [])),
            "backup_size_mb": backup_status.get("total_size_mb", 0),
            "files_kept_count": len(self.cleanup_report["files_to_keep"]),
            "files_to_delete_count": len(files_to_delete),
            "backup_errors": len(backup_status.get("backup_errors", []))
        }
        
        self.cleanup_report["summary"] = summary
        self.cleanup_report["files_to_delete"] = files_to_delete
        
        # 保存报告
        report_file = f"PROJECT_CLEANUP_ANALYSIS_REPORT_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.cleanup_report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 清理分析报告已保存: {report_file}")
        
        # 打印总结
        print(f"\n🎉 项目清理分析完成总结:")
        print(f"  📁 备份文件: {summary['backup_files_count']} 个 ({summary['backup_size_mb']:.1f}MB)")
        print(f"  📋 保留文件: {summary['files_kept_count']} 个")
        print(f"  🗑️ 待删除文件: {summary['files_to_delete_count']} 个")
        print(f"  ⚠️ 备份错误: {summary['backup_errors']} 个")
        
        return report_file

def main():
    """主函数"""
    cleanup_tool = ComprehensiveProjectCleanup()
    success = cleanup_tool.run_complete_cleanup()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
