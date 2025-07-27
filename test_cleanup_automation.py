#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 测试后自动清理脚本
按照用户要求清理所有生成的测试文件，保留测试报告和最新的3个日志文件
"""

import os
import sys
import shutil
import glob
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestCleanupManager:
    """测试清理管理器"""
    
    def __init__(self):
        self.project_root = project_root
        self.cleanup_report = {
            "cleanup_time": datetime.now().isoformat(),
            "cleaned_items": [],
            "preserved_items": [],
            "errors": [],
            "summary": {}
        }
        
    def cleanup_test_data(self) -> Dict[str, Any]:
        """清理测试数据文件"""
        print("🧹 开始清理测试数据文件...")
        
        test_data_paths = [
            "test_data/samples",
            "test_data/core_processing", 
            "test_data/comprehensive",
            "test_data/production_verification"
        ]
        
        cleaned_count = 0
        for path in test_data_paths:
            full_path = self.project_root / path
            if full_path.exists():
                try:
                    shutil.rmtree(full_path)
                    self.cleanup_report["cleaned_items"].append(f"测试数据目录: {path}")
                    cleaned_count += 1
                    print(f"  ✅ 已清理: {path}")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理失败 {path}: {e}")
                    print(f"  ❌ 清理失败: {path} - {e}")
        
        return {"cleaned_directories": cleaned_count}
    
    def cleanup_temporary_files(self) -> Dict[str, Any]:
        """清理临时文件"""
        print("🧹 开始清理临时文件...")
        
        temp_patterns = [
            "test_output/*/temp/*",
            "temp/*",
            "*.tmp",
            "*.temp",
            "*_temp.*",
            "recovery/*.recovery"
        ]
        
        cleaned_count = 0
        for pattern in temp_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        cleaned_count += 1
                    print(f"  ✅ 已清理临时文件: {os.path.basename(file_path)}")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理临时文件失败 {file_path}: {e}")
        
        self.cleanup_report["cleaned_items"].append(f"临时文件: {cleaned_count}个")
        return {"cleaned_files": cleaned_count}
    
    def cleanup_generated_videos(self) -> Dict[str, Any]:
        """清理生成的测试视频文件"""
        print("🧹 开始清理生成的视频文件...")
        
        video_patterns = [
            "test_output/*/final_videos/*",
            "data/output/final_videos/*",
            "output/*test*.mp4",
            "output/*test*.avi"
        ]
        
        cleaned_count = 0
        total_size_mb = 0
        
        for pattern in video_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        total_size_mb += file_size
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"  ✅ 已清理视频: {os.path.basename(file_path)} ({file_size:.1f}MB)")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理视频文件失败 {file_path}: {e}")
        
        self.cleanup_report["cleaned_items"].append(f"测试视频: {cleaned_count}个 ({total_size_mb:.1f}MB)")
        return {"cleaned_videos": cleaned_count, "freed_space_mb": total_size_mb}
    
    def cleanup_generated_subtitles(self) -> Dict[str, Any]:
        """清理生成的字幕文件"""
        print("🧹 开始清理生成的字幕文件...")
        
        subtitle_patterns = [
            "test_output/*/generated_srt/*",
            "data/output/generated_srt/*",
            "output/*test*.srt",
            "*_generated.srt",
            "*_viral.srt"
        ]
        
        cleaned_count = 0
        for pattern in subtitle_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"  ✅ 已清理字幕: {os.path.basename(file_path)}")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理字幕文件失败 {file_path}: {e}")
        
        self.cleanup_report["cleaned_items"].append(f"生成字幕: {cleaned_count}个")
        return {"cleaned_subtitles": cleaned_count}
    
    def cleanup_project_files(self) -> Dict[str, Any]:
        """清理工程文件"""
        print("🧹 开始清理工程文件...")
        
        project_patterns = [
            "test_output/*/edit_projects/*",
            "data/output/edit_projects/*",
            "output/*test*.json",
            "*_project.json",
            "*.draft_content"
        ]
        
        cleaned_count = 0
        for pattern in project_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned_count += 1
                        print(f"  ✅ 已清理工程文件: {os.path.basename(file_path)}")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理工程文件失败 {file_path}: {e}")
        
        self.cleanup_report["cleaned_items"].append(f"工程文件: {cleaned_count}个")
        return {"cleaned_projects": cleaned_count}
    
    def reset_model_cache(self) -> Dict[str, Any]:
        """重置模型缓存"""
        print("🧹 开始重置模型缓存...")
        
        cache_paths = [
            "models/cache",
            "models/temp",
            "cache/embeddings",
            "__pycache__"
        ]
        
        cleaned_count = 0
        for cache_path in cache_paths:
            full_path = self.project_root / cache_path
            if full_path.exists():
                try:
                    if full_path.is_dir():
                        # 清空目录但保留目录结构
                        for item in full_path.iterdir():
                            if item.is_file():
                                item.unlink()
                                cleaned_count += 1
                            elif item.is_dir():
                                shutil.rmtree(item)
                                cleaned_count += 1
                        print(f"  ✅ 已清理缓存: {cache_path}")
                except Exception as e:
                    self.cleanup_report["errors"].append(f"清理缓存失败 {cache_path}: {e}")
        
        self.cleanup_report["cleaned_items"].append(f"模型缓存: {cleaned_count}个文件")
        return {"cleaned_cache_items": cleaned_count}
    
    def preserve_important_files(self) -> Dict[str, Any]:
        """保留重要文件（测试报告和最新3个日志）"""
        print("📋 保留重要文件...")
        
        # 保留测试报告
        report_patterns = [
            "test_output/*/reports/*.html",
            "test_output/*/reports/*.json",
            "COMPREHENSIVE_*.md",
            "*_TEST_REPORT.md"
        ]
        
        preserved_reports = 0
        for pattern in report_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                if os.path.isfile(file_path):
                    self.cleanup_report["preserved_items"].append(f"测试报告: {os.path.basename(file_path)}")
                    preserved_reports += 1
        
        # 保留最新3个日志文件
        log_patterns = [
            "logs/*.log",
            "test_output/*/logs/*.log"
        ]
        
        all_logs = []
        for pattern in log_patterns:
            files = glob.glob(str(self.project_root / pattern), recursive=True)
            for file_path in files:
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    all_logs.append((file_path, stat.st_mtime))
        
        # 按修改时间排序，保留最新3个
        all_logs.sort(key=lambda x: x[1], reverse=True)
        preserved_logs = all_logs[:3]
        
        # 删除其他日志文件
        logs_to_delete = all_logs[3:]
        deleted_logs = 0
        for log_path, _ in logs_to_delete:
            try:
                os.remove(log_path)
                deleted_logs += 1
            except Exception as e:
                self.cleanup_report["errors"].append(f"删除旧日志失败 {log_path}: {e}")
        
        for log_path, _ in preserved_logs:
            self.cleanup_report["preserved_items"].append(f"日志文件: {os.path.basename(log_path)}")
        
        print(f"  ✅ 保留测试报告: {preserved_reports}个")
        print(f"  ✅ 保留最新日志: {len(preserved_logs)}个")
        print(f"  ✅ 清理旧日志: {deleted_logs}个")
        
        return {
            "preserved_reports": preserved_reports,
            "preserved_logs": len(preserved_logs),
            "deleted_old_logs": deleted_logs
        }
    
    def generate_cleanup_summary(self) -> None:
        """生成清理总结"""
        print("\n" + "="*60)
        print("🎯 测试环境清理完成")
        print("="*60)
        
        print("📋 已清理项目:")
        for item in self.cleanup_report["cleaned_items"]:
            print(f"  ✅ {item}")
        
        print("\n📋 已保留项目:")
        for item in self.cleanup_report["preserved_items"]:
            print(f"  📁 {item}")
        
        if self.cleanup_report["errors"]:
            print("\n⚠️ 清理过程中的错误:")
            for error in self.cleanup_report["errors"]:
                print(f"  ❌ {error}")
        
        # 保存清理报告
        cleanup_report_file = self.project_root / "test_cleanup_report.json"
        with open(cleanup_report_file, 'w', encoding='utf-8') as f:
            json.dump(self.cleanup_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 清理报告已保存: {cleanup_report_file}")

def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster 测试后自动清理")
    print("=" * 60)
    
    cleanup_manager = TestCleanupManager()
    
    # 执行清理步骤
    cleanup_manager.cleanup_test_data()
    cleanup_manager.cleanup_temporary_files()
    cleanup_manager.cleanup_generated_videos()
    cleanup_manager.cleanup_generated_subtitles()
    cleanup_manager.cleanup_project_files()
    cleanup_manager.reset_model_cache()
    cleanup_manager.preserve_important_files()
    
    # 生成总结
    cleanup_manager.generate_cleanup_summary()
    
    print("\n🎉 测试环境清理完成！")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
