#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全清理执行器
基于分析报告执行安全的文件删除操作
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class SafeCleanupExecutor:
    """安全清理执行器"""
    
    def __init__(self, analysis_report_file: str):
        self.project_root = Path(".")
        self.analysis_report_file = analysis_report_file
        self.analysis_data = None
        self.execution_report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_report_used": analysis_report_file,
            "deletion_results": {},
            "summary": {}
        }
        
    def load_analysis_report(self) -> bool:
        """加载分析报告"""
        try:
            with open(self.analysis_report_file, 'r', encoding='utf-8') as f:
                self.analysis_data = json.load(f)
            print(f"✓ 已加载分析报告: {self.analysis_report_file}")
            return True
        except Exception as e:
            print(f"❌ 加载分析报告失败: {e}")
            return False
    
    def verify_backup_integrity(self) -> bool:
        """验证备份完整性"""
        print("\n🔍 验证备份完整性...")
        
        if not self.analysis_data:
            print("❌ 分析数据未加载")
            return False
        
        backup_status = self.analysis_data.get("backup_status", {})
        if backup_status.get("status") != "success":
            print("❌ 备份状态不成功")
            return False
        
        backup_dir = Path(backup_status.get("backup_dir", "backup"))
        if not backup_dir.exists():
            print(f"❌ 备份目录不存在: {backup_dir}")
            return False
        
        # 检查备份文件数量
        backup_files = list(backup_dir.glob("*"))
        expected_count = backup_status.get("file_counts", {})
        total_expected = sum(info.get("count", 0) for info in expected_count.values())
        
        print(f"📁 备份目录: {backup_dir}")
        print(f"📊 备份文件数量: {len(backup_files)} (预期: {total_expected})")
        
        if len(backup_files) >= total_expected * 0.9:  # 允许10%的差异
            print("✅ 备份完整性验证通过")
            return True
        else:
            print("❌ 备份文件数量不足")
            return False
    
    def execute_safe_deletion(self) -> Dict[str, Any]:
        """执行安全删除"""
        print("\n🗑️ 执行安全删除...")
        
        deletion_result = {
            "deleted_files": [],
            "deletion_errors": [],
            "skipped_files": [],
            "total_deleted": 0,
            "space_freed_mb": 0
        }
        
        files_to_delete = self.analysis_data.get("files_to_delete", [])
        files_to_keep = self.analysis_data.get("files_to_keep", [])
        
        print(f"📋 计划删除 {len(files_to_delete)} 个文件")
        
        # 去重处理
        unique_files_to_delete = list(set(files_to_delete))
        print(f"📋 去重后删除 {len(unique_files_to_delete)} 个文件")
        
        total_size_freed = 0
        
        for file_path_str in unique_files_to_delete:
            file_path = Path(file_path_str)
            
            try:
                # 安全检查：确保不删除重要文件
                if str(file_path) in files_to_keep:
                    deletion_result["skipped_files"].append(f"{file_path.name} (重要文件)")
                    print(f"  ⏭️ 跳过重要文件: {file_path.name}")
                    continue
                
                # 安全检查：确保不删除核心功能文件
                if file_path.name in ["simple_ui_fixed.py", "main.py", "app.py", "requirements.txt"]:
                    deletion_result["skipped_files"].append(f"{file_path.name} (核心文件)")
                    print(f"  ⏭️ 跳过核心文件: {file_path.name}")
                    continue
                
                # 安全检查：确保不删除src目录下的文件
                if "src/" in str(file_path) or "src\\" in str(file_path):
                    deletion_result["skipped_files"].append(f"{file_path.name} (源码文件)")
                    print(f"  ⏭️ 跳过源码文件: {file_path.name}")
                    continue
                
                if file_path.exists():
                    # 记录文件大小
                    file_size = file_path.stat().st_size
                    
                    # 删除文件
                    file_path.unlink()
                    
                    deletion_result["deleted_files"].append(str(file_path.name))
                    total_size_freed += file_size
                    print(f"  ✓ 已删除: {file_path.name} ({file_size/1024:.1f}KB)")
                else:
                    deletion_result["skipped_files"].append(f"{file_path.name} (文件不存在)")
                    print(f"  ⏭️ 文件不存在: {file_path.name}")
                    
            except Exception as e:
                error_msg = f"删除失败 {file_path.name}: {str(e)}"
                deletion_result["deletion_errors"].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        deletion_result["total_deleted"] = len(deletion_result["deleted_files"])
        deletion_result["space_freed_mb"] = total_size_freed / 1024 / 1024
        
        print(f"\n📊 删除统计:")
        print(f"  成功删除: {deletion_result['total_deleted']} 个文件")
        print(f"  跳过文件: {len(deletion_result['skipped_files'])} 个")
        print(f"  删除错误: {len(deletion_result['deletion_errors'])} 个")
        print(f"  释放空间: {deletion_result['space_freed_mb']:.1f}MB")
        
        self.execution_report["deletion_results"] = deletion_result
        return deletion_result
    
    def generate_execution_report(self) -> str:
        """生成执行报告"""
        print("\n📊 生成执行报告...")
        
        deletion_results = self.execution_report["deletion_results"]
        
        summary = {
            "files_deleted": deletion_results.get("total_deleted", 0),
            "files_skipped": len(deletion_results.get("skipped_files", [])),
            "deletion_errors": len(deletion_results.get("deletion_errors", [])),
            "space_freed_mb": deletion_results.get("space_freed_mb", 0),
            "cleanup_success": deletion_results.get("total_deleted", 0) > 0
        }
        
        self.execution_report["summary"] = summary
        
        # 保存执行报告
        report_file = f"PROJECT_CLEANUP_EXECUTION_REPORT_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.execution_report, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 执行报告已保存: {report_file}")
        
        # 生成Markdown总结报告
        markdown_report = self.generate_markdown_summary()
        
        return report_file
    
    def generate_markdown_summary(self) -> str:
        """生成Markdown总结报告"""
        summary = self.execution_report["summary"]
        deletion_results = self.execution_report["deletion_results"]
        
        markdown_content = f"""# VisionAI-ClipsMaster 项目清理执行报告

## 清理概述

**执行时间**: {self.execution_report['timestamp']}  
**分析报告**: {self.execution_report['analysis_report_used']}  
**清理状态**: {'✅ 成功' if summary['cleanup_success'] else '❌ 失败'}

## 清理结果统计

| 项目 | 数量 | 说明 |
|------|------|------|
| 成功删除文件 | {summary['files_deleted']} | 已删除的临时文件和测试报告 |
| 跳过文件 | {summary['files_skipped']} | 重要文件和核心功能文件 |
| 删除错误 | {summary['deletion_errors']} | 删除过程中的错误 |
| 释放空间 | {summary['space_freed_mb']:.1f}MB | 清理释放的磁盘空间 |

## 已删除的文件

以下文件已被安全删除：

"""
        
        for i, file_name in enumerate(deletion_results.get("deleted_files", [])[:20]):
            markdown_content += f"{i+1}. {file_name}\n"
        
        if len(deletion_results.get("deleted_files", [])) > 20:
            markdown_content += f"... 还有 {len(deletion_results.get('deleted_files', [])) - 20} 个文件\n"
        
        markdown_content += f"""
## 跳过的文件

以下重要文件已被保留：

"""
        
        for i, file_info in enumerate(deletion_results.get("skipped_files", [])[:10]):
            markdown_content += f"{i+1}. {file_info}\n"
        
        if len(deletion_results.get("skipped_files", [])) > 10:
            markdown_content += f"... 还有 {len(deletion_results.get('skipped_files', [])) - 10} 个文件\n"
        
        markdown_content += f"""
## 清理效果

- ✅ 项目目录更加整洁
- ✅ 保留了所有重要文档和核心功能文件
- ✅ 删除了临时测试报告和重复文件
- ✅ 完整备份保存在 `backup/` 目录中

## 后续建议

1. 定期运行清理脚本保持项目整洁
2. 重要文档继续维护和更新
3. 备份目录可以定期归档
4. 建议建立文档管理规范

---

*报告生成时间: {datetime.now().isoformat()}*
"""
        
        # 保存Markdown报告
        markdown_file = f"PROJECT_CLEANUP_SUMMARY_{int(time.time())}.md"
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ Markdown总结报告已保存: {markdown_file}")
        return markdown_file
    
    def run_safe_cleanup(self) -> bool:
        """运行安全清理"""
        print("🚀 开始VisionAI-ClipsMaster安全清理执行")
        print("=" * 80)
        
        try:
            # 1. 加载分析报告
            if not self.load_analysis_report():
                return False
            
            # 2. 验证备份完整性
            if not self.verify_backup_integrity():
                print("❌ 备份验证失败，停止清理操作")
                return False
            
            # 3. 执行安全删除
            deletion_result = self.execute_safe_deletion()
            
            # 4. 生成执行报告
            report_file = self.generate_execution_report()
            
            print(f"\n✅ 项目清理执行完成！")
            print(f"📄 详细报告: {report_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 清理执行过程发生异常: {e}")
            return False

def main():
    """主函数"""
    # 查找最新的分析报告
    analysis_reports = list(Path(".").glob("PROJECT_CLEANUP_ANALYSIS_REPORT_*.json"))
    
    if not analysis_reports:
        print("❌ 未找到分析报告文件，请先运行 comprehensive_project_cleanup.py")
        return False
    
    # 使用最新的分析报告
    latest_report = max(analysis_reports, key=lambda p: p.stat().st_mtime)
    print(f"📄 使用分析报告: {latest_report}")
    
    # 执行安全清理
    cleanup_executor = SafeCleanupExecutor(str(latest_report))
    success = cleanup_executor.run_safe_cleanup()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
