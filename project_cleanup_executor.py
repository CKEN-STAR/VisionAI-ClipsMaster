#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 项目清理执行器
按照用户要求安全删除冗余文件
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from cleanup_rollback_script import CleanupRollback

class ProjectCleanupExecutor:
    def __init__(self):
        self.rollback = CleanupRollback()
        self.deleted_files = []
        
    def get_files_to_delete(self):
        """获取需要删除的文件列表"""
        files_to_delete = []
        
        # 1. 根目录下的文档文件
        root_docs = [
            "BACKUP_RECORD_UI_REALTIME_CHECK.md",
            "CHANGELOG.md", 
            "COMPLETE_WORKFLOW_TEST_FINAL_REPORT.md",
            "COMPREHENSIVE_FUNCTIONAL_VALIDATION_REPORT.md",
            "COMPREHENSIVE_WORKFLOW_TEST_SUMMARY.md",
            "CORE_FUNCTIONALITY_FINAL_TEST_REPORT.md",
            "DEPLOYMENT.md",
            "DEVELOPMENT.md", 
            "DOCUMENTATION_INDEX.md",
            "Documentation_Completion_Report.md",
            "FAQ.md",
            "FINAL_COMPREHENSIVE_TEST_REPORT.md",
            "FINAL_FIX_REPORT_v1_0_1.md",
            "FINAL_FIX_SUMMARY_REPORT.md",
            "FINAL_VALIDATION_SUMMARY.md",
            "Font_Revert_Report.md",
            "GPU_ACCELERATION_IMPLEMENTATION_SUMMARY.md",
            "GPU_DETECTION_DISCRETE_ONLY_SUMMARY.md",
            "GPU_DETECTION_FIX_GUIDE.md",
            "GPU_DETECTION_FIX_SUMMARY.md",
            "GPU_DIALOG_LOCALIZATION_SUMMARY.md",
            "GPU_DIALOG_SIMPLIFICATION_SUMMARY.md",
            "GPU_VIDEO_ACCELERATION_GUIDE.md",
            "GitHub_Repository_Verification_Report.md",
            "GitHub_Upload_Success_Report.md",
            "Git_Repository_Reset_Report.md",
            "INSTALLATION.md",
            "JIANYING_COMPATIBILITY_FIX_SUMMARY.md",
            "JIANYING_EXPORT_TEST_MODULE_SUMMARY.md",
            "JIANYING_PROJECT_FUNCTIONALITY_TEST_REPORT.md",
            "JIANYING_PROJECT_USAGE_GUIDE.md",
            "PERFORMANCE_TEST_COMPREHENSIVE_REPORT.md",
            "Project_History_Update_Report.md",
            "README.md",
            "README_Update_Report.md",
            "README_smart_downloader_ui_optimization.md",
            "RECOMMENDATION_ALGORITHM_OPTIMIZATION_SUMMARY.md",
            "RELEASE_NOTES_v1.0.1.md",
            "SMART_DOWNLOADER_VALIDATION_REPORT.md",
            "SYSTEMATIC_FIXES_COMPLETION_REPORT.md",
            "SYSTEM_REPAIR_VERIFICATION_REPORT.md",
            "TESTING_GUIDE.md",
            "TEST_MODULE_SUMMARY.md",
            "TRAINING_VALIDATION_SYSTEM_REPORT.md",
            "TRAINING_VALIDATION_TEST_RESULTS.md",
            "TROUBLESHOOTING.md",
            "UI_Font_Scaling_Fix_Report.md",
            "UI_INTEGRATION_FIX_REPORT.md",
            "UI_INTEGRATION_TEST_FINAL_REPORT.md",
            "USAGE.md",
            "USER_GUIDE.md",
            "VIDEO_WORKFLOW_VALIDATION_SYSTEM_REPORT.md",
            "Window_Size_Adjustment_Report.md",
            "create_github_release.md",
            "model_versions_comparison.md"
        ]
        
        # 添加所有以VisionAI_ClipsMaster开头的报告文件
        for file in os.listdir('.'):
            if file.startswith('VisionAI_ClipsMaster_') and file.endswith('.md'):
                root_docs.append(file)
        
        # 检查根目录文档文件是否存在
        for doc_file in root_docs:
            if os.path.exists(doc_file):
                files_to_delete.append(doc_file)
        
        # 2. HTML测试报告文件
        html_patterns = [
            'comprehensive_functional_test_',
            'comprehensive_test_report_',
            'ui_integration_comprehensive_report_',
            'video_workflow_test_report_',
            'training_module_final_report_'
        ]
        
        for file in os.listdir('.'):
            if file.endswith('.html'):
                for pattern in html_patterns:
                    if pattern in file:
                        files_to_delete.append(file)
                        break
                # 特殊文件
                if file in ['verification_report.html']:
                    files_to_delete.append(file)
        
        # 3. PNG测试图表文件
        png_test_files = [
            'VisionAI_Training_Curves_20250716_111902.png'
        ]
        
        for png_file in png_test_files:
            if os.path.exists(png_file):
                files_to_delete.append(png_file)
        
        # 4. 完整目录
        directories_to_delete = ['docs', 'tests']
        for directory in directories_to_delete:
            if os.path.exists(directory) and os.path.isdir(directory):
                files_to_delete.append(directory)
        
        return files_to_delete
    
    def verify_safe_to_delete(self, files_to_delete):
        """验证删除操作的安全性"""
        # 检查是否包含重要的功能性文件
        critical_files = [
            'src', 'configs', 'ui', 'models', 'data',
            'requirements.txt', 'Dockerfile', 'LICENSE',
            'main.py', 'app.py', 'simple_ui_fixed.py'
        ]
        
        for critical_file in critical_files:
            if critical_file in files_to_delete:
                print(f"⚠️  警告: 发现关键文件在删除列表中: {critical_file}")
                return False
        
        # 检查src目录是否会被误删
        for file_path in files_to_delete:
            if file_path.startswith('src/') or file_path.startswith('configs/') or file_path.startswith('ui/'):
                print(f"⚠️  警告: 发现核心代码文件在删除列表中: {file_path}")
                return False
        
        return True
    
    def execute_cleanup(self, files_to_delete, create_backup=True):
        """执行清理操作"""
        if not self.verify_safe_to_delete(files_to_delete):
            print("❌ 安全检查失败，取消删除操作")
            return False
        
        print(f"准备删除 {len(files_to_delete)} 个项目")
        
        # 创建备份
        if create_backup:
            print("正在创建备份...")
            backup_manifest = self.rollback.create_backup_before_cleanup(files_to_delete)
            git_checkpoint = self.rollback.create_git_checkpoint()
        
        # 执行删除
        deleted_count = 0
        failed_deletions = []
        
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f"✅ 已删除文件: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f"✅ 已删除目录: {file_path}")
                    
                    self.deleted_files.append(file_path)
                    deleted_count += 1
                else:
                    print(f"⚠️  文件不存在: {file_path}")
            
            except Exception as e:
                print(f"❌ 删除失败 {file_path}: {e}")
                failed_deletions.append((file_path, str(e)))
        
        # 保存删除记录
        deletion_record = {
            "deletion_time": datetime.now().isoformat(),
            "deleted_files": self.deleted_files,
            "failed_deletions": failed_deletions,
            "backup_created": create_backup,
            "total_deleted": deleted_count
        }
        
        with open("deletion_record.json", 'w', encoding='utf-8') as f:
            json.dump(deletion_record, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 清理完成!")
        print(f"✅ 成功删除: {deleted_count} 个项目")
        if failed_deletions:
            print(f"❌ 删除失败: {len(failed_deletions)} 个项目")
        
        if create_backup:
            print(f"💾 备份已创建: {self.rollback.backup_dir}")
            print("💡 如需恢复，请运行: python cleanup_rollback_script.py")
        
        return True

def main():
    """主函数"""
    print("VisionAI-ClipsMaster 项目清理工具")
    print("=" * 50)
    
    executor = ProjectCleanupExecutor()
    files_to_delete = executor.get_files_to_delete()
    
    print(f"发现 {len(files_to_delete)} 个项目需要删除:")
    print("\n📁 目录:")
    directories = [f for f in files_to_delete if os.path.isdir(f)]
    for directory in directories:
        print(f"  - {directory}/")
    
    print("\n📄 文件:")
    files = [f for f in files_to_delete if os.path.isfile(f)]
    for i, file in enumerate(files[:10]):  # 只显示前10个文件
        print(f"  - {file}")
    if len(files) > 10:
        print(f"  ... 还有 {len(files) - 10} 个文件")
    
    print(f"\n总计: {len(directories)} 个目录, {len(files)} 个文件")
    
    # 用户确认
    print("\n⚠️  此操作将永久删除上述文件和目录!")
    print("💾 删除前将自动创建备份")
    
    confirm = input("\n确认执行删除操作? (输入 'YES' 确认): ").strip()
    
    if confirm == 'YES':
        success = executor.execute_cleanup(files_to_delete, create_backup=True)
        if success:
            print("\n✨ 项目清理完成!")
        else:
            print("\n❌ 清理操作失败")
    else:
        print("❌ 操作已取消")

if __name__ == "__main__":
    main()
