#!/usr/bin/env python3
"""
测试环境清理脚本
自动清理测试过程中生成的临时文件、缓存、日志等
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestEnvironmentCleaner:
    """测试环境清理器"""
    
    def __init__(self, preserve_reports: bool = True, preserve_logs_count: int = 3):
        self.preserve_reports = preserve_reports
        self.preserve_logs_count = preserve_logs_count
        self.cleanup_stats = {
            "start_time": datetime.now(),
            "files_deleted": 0,
            "directories_deleted": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
    def cleanup_all(self) -> Dict[str, Any]:
        """执行完整清理"""
        print("🧹 开始清理测试环境...")
        
        try:
            # 1. 清理临时文件
            self._cleanup_temp_files()
            
            # 2. 清理测试输出文件
            self._cleanup_test_outputs()
            
            # 3. 清理生成的视频文件
            self._cleanup_generated_videos()
            
            # 4. 清理模型缓存
            self._cleanup_model_cache()
            
            # 5. 清理日志文件
            self._cleanup_log_files()
            
            # 6. 清理Python缓存
            self._cleanup_python_cache()
            
            # 7. 清理测试数据
            self._cleanup_test_data()
            
            self.cleanup_stats["end_time"] = datetime.now()
            self.cleanup_stats["duration"] = (
                self.cleanup_stats["end_time"] - self.cleanup_stats["start_time"]
            ).total_seconds()
            
            print(f"✅ 清理完成!")
            print(f"   删除文件: {self.cleanup_stats['files_deleted']}")
            print(f"   删除目录: {self.cleanup_stats['directories_deleted']}")
            print(f"   释放空间: {self.cleanup_stats['space_freed_mb']:.1f} MB")
            print(f"   耗时: {self.cleanup_stats['duration']:.1f} 秒")
            
            if self.cleanup_stats["errors"]:
                print(f"   警告: {len(self.cleanup_stats['errors'])} 个清理错误")
            
            return self.cleanup_stats
            
        except Exception as e:
            print(f"❌ 清理过程中发生错误: {e}")
            self.cleanup_stats["errors"].append(str(e))
            return self.cleanup_stats
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        print("🗂️ 清理临时文件...")
        
        temp_patterns = [
            project_root / "test_output" / "*" / "temp",
            project_root / "tests" / "temp",
            project_root / "temp",
            project_root / "tmp"
        ]
        
        for pattern in temp_patterns:
            if pattern.exists() and pattern.is_dir():
                self._remove_directory(pattern)
        
        # 清理系统临时目录中的测试文件
        import tempfile
        system_temp = Path(tempfile.gettempdir())
        
        for temp_file in system_temp.glob("visionai_test_*"):
            self._remove_file_or_directory(temp_file)
        
        for temp_file in system_temp.glob("clipmaster_*"):
            self._remove_file_or_directory(temp_file)
    
    def _cleanup_test_outputs(self):
        """清理测试输出文件"""
        print("📁 清理测试输出文件...")
        
        output_dirs = [
            project_root / "test_output",
            project_root / "data" / "output" / "generated_srt",
            project_root / "data" / "output" / "final_videos",
            project_root / "data" / "output" / "edit_projects"
        ]
        
        for output_dir in output_dirs:
            if output_dir.exists():
                # 保留reports目录（如果设置了preserve_reports）
                if self.preserve_reports and output_dir.name == "test_output":
                    self._cleanup_directory_selective(output_dir, preserve_patterns=["reports"])
                else:
                    # 清理测试生成的文件
                    for file in output_dir.rglob("test_*"):
                        self._remove_file_or_directory(file)
                    
                    for file in output_dir.rglob("generated_*"):
                        self._remove_file_or_directory(file)
                    
                    for file in output_dir.rglob("*.tmp"):
                        self._remove_file_or_directory(file)
    
    def _cleanup_generated_videos(self):
        """清理生成的视频文件"""
        print("🎬 清理生成的视频文件...")
        
        video_patterns = [
            "test_*.mp4",
            "test_*.avi", 
            "test_*.flv",
            "generated_*.mp4",
            "output_*.mp4",
            "temp_*.mp4"
        ]
        
        search_dirs = [
            project_root / "data" / "output" / "final_videos",
            project_root / "test_output",
            project_root / "tests"
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for pattern in video_patterns:
                    for video_file in search_dir.rglob(pattern):
                        self._remove_file_or_directory(video_file)
    
    def _cleanup_model_cache(self):
        """清理模型缓存"""
        print("🤖 清理模型缓存...")
        
        cache_dirs = [
            project_root / "models" / "cache",
            project_root / "models" / "temp",
            project_root / ".cache",
            Path.home() / ".cache" / "visionai-clipmaster"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                # 清理测试相关的缓存文件
                for cache_file in cache_dir.rglob("test_*"):
                    self._remove_file_or_directory(cache_file)
                
                for cache_file in cache_dir.rglob("*.tmp"):
                    self._remove_file_or_directory(cache_file)
                
                # 清理过期的缓存文件（超过7天）
                cutoff_date = datetime.now() - timedelta(days=7)
                for cache_file in cache_dir.rglob("*"):
                    if cache_file.is_file():
                        try:
                            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                self._remove_file_or_directory(cache_file)
                        except (OSError, ValueError):
                            pass  # 忽略无法访问的文件
    
    def _cleanup_log_files(self):
        """清理日志文件"""
        print("📋 清理日志文件...")
        
        log_dirs = [
            project_root / "logs",
            project_root / "test_output" / "logs",
            project_root / "tests" / "logs"
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists():
                # 获取所有日志文件，按修改时间排序
                log_files = []
                for log_file in log_dir.rglob("*.log"):
                    if log_file.is_file():
                        log_files.append((log_file, log_file.stat().st_mtime))
                
                # 按时间排序，保留最新的几个
                log_files.sort(key=lambda x: x[1], reverse=True)
                
                # 删除多余的日志文件
                for log_file, _ in log_files[self.preserve_logs_count:]:
                    self._remove_file_or_directory(log_file)
                
                # 清理测试日志
                for log_file in log_dir.rglob("test_*.log"):
                    self._remove_file_or_directory(log_file)
    
    def _cleanup_python_cache(self):
        """清理Python缓存"""
        print("🐍 清理Python缓存...")
        
        # 清理__pycache__目录
        for pycache_dir in project_root.rglob("__pycache__"):
            if pycache_dir.is_dir():
                self._remove_directory(pycache_dir)
        
        # 清理.pyc文件
        for pyc_file in project_root.rglob("*.pyc"):
            self._remove_file_or_directory(pyc_file)
        
        # 清理.pyo文件
        for pyo_file in project_root.rglob("*.pyo"):
            self._remove_file_or_directory(pyo_file)
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        print("📊 清理测试数据...")
        
        test_data_dirs = [
            project_root / "test_data",
            project_root / "data" / "input" / "test_*",
            project_root / "tests" / "test_data"
        ]
        
        for test_data_path in test_data_dirs:
            if isinstance(test_data_path, Path) and test_data_path.exists():
                if test_data_path.is_dir():
                    # 只清理明确标记为测试的文件
                    for test_file in test_data_path.rglob("test_*"):
                        self._remove_file_or_directory(test_file)
                    
                    for temp_file in test_data_path.rglob("temp_*"):
                        self._remove_file_or_directory(temp_file)
            else:
                # 处理glob模式
                parent_dir = test_data_path.parent
                if parent_dir.exists():
                    pattern = test_data_path.name
                    for match in parent_dir.glob(pattern):
                        self._remove_file_or_directory(match)
    
    def _cleanup_directory_selective(self, directory: Path, preserve_patterns: List[str]):
        """选择性清理目录"""
        if not directory.exists():
            return
        
        for item in directory.iterdir():
            should_preserve = any(pattern in item.name for pattern in preserve_patterns)
            if not should_preserve:
                self._remove_file_or_directory(item)
    
    def _remove_file_or_directory(self, path: Path):
        """删除文件或目录"""
        try:
            if not path.exists():
                return
            
            # 计算文件大小
            size_mb = 0
            if path.is_file():
                size_mb = path.stat().st_size / (1024 * 1024)
                path.unlink()
                self.cleanup_stats["files_deleted"] += 1
            elif path.is_dir():
                # 计算目录大小
                size_mb = sum(f.stat().st_size for f in path.rglob('*') if f.is_file()) / (1024 * 1024)
                shutil.rmtree(path)
                self.cleanup_stats["directories_deleted"] += 1
            
            self.cleanup_stats["space_freed_mb"] += size_mb
            
        except Exception as e:
            error_msg = f"删除失败 {path}: {e}"
            self.cleanup_stats["errors"].append(error_msg)
            print(f"⚠️ {error_msg}")
    
    def _remove_directory(self, directory: Path):
        """删除整个目录"""
        self._remove_file_or_directory(directory)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 测试环境清理工具")
    parser.add_argument("--preserve-reports", action="store_true", default=True, 
                       help="保留测试报告文件")
    parser.add_argument("--preserve-logs", type=int, default=3,
                       help="保留的日志文件数量")
    parser.add_argument("--force", action="store_true",
                       help="强制清理，不询问确认")
    parser.add_argument("--dry-run", action="store_true",
                       help="模拟运行，不实际删除文件")
    
    args = parser.parse_args()
    
    print("🧹 VisionAI-ClipsMaster 测试环境清理工具")
    print("=" * 50)
    
    if not args.force and not args.dry_run:
        print("⚠️ 此操作将删除测试过程中生成的文件和缓存")
        print("包括: 临时文件、测试输出、生成的视频、模型缓存、日志文件等")
        
        if args.preserve_reports:
            print("✅ 测试报告将被保留")
        
        print(f"✅ 最新的 {args.preserve_logs} 个日志文件将被保留")
        
        response = input("\n确认继续？(y/N): ")
        if response.lower() != 'y':
            print("清理已取消")
            return 0
    
    if args.dry_run:
        print("🔍 模拟运行模式 - 不会实际删除文件")
    
    # 创建清理器
    cleaner = TestEnvironmentCleaner(
        preserve_reports=args.preserve_reports,
        preserve_logs_count=args.preserve_logs
    )
    
    # 执行清理
    if args.dry_run:
        print("模拟清理完成（实际未删除任何文件）")
        return 0
    else:
        cleanup_stats = cleaner.cleanup_all()
        
        # 检查是否有错误
        if cleanup_stats["errors"]:
            print(f"\n⚠️ 清理过程中遇到 {len(cleanup_stats['errors'])} 个错误:")
            for error in cleanup_stats["errors"][:5]:  # 只显示前5个错误
                print(f"   - {error}")
            if len(cleanup_stats["errors"]) > 5:
                print(f"   ... 还有 {len(cleanup_stats['errors']) - 5} 个错误")
            return 1
        
        return 0

if __name__ == "__main__":
    exit(main())
