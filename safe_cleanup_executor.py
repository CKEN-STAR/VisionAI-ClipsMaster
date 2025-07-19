#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 安全清理执行器
基于分析结果执行安全的体积优化，确保核心功能完整性
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import argparse

class SafeCleanupExecutor:
    def __init__(self, project_root=".", dry_run=True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.backup_dir = self.project_root / "cleanup_backup"
        self.cleanup_log = []
        
        # 核心功能必需文件（绝对不能删除）
        self.critical_files = [
            "src/",
            "configs/",
            "ui/",
            "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
            "VisionAI-ClipsMaster-Core/requirements.txt",
            "requirements.txt",
            "models/configs/",
            "models/*/quantized/",  # 保留量化模型
            "tools/ffmpeg/bin/",    # 保留一份FFmpeg
        ]
        
        # 安全清理目标（按风险等级分类）
        self.cleanup_targets = {
            "low_risk": {
                "description": "低风险：缓存和临时文件",
                "targets": [
                    "__pycache__/",
                    "*.pyc",
                    "cache/",
                    "temp/",
                    "*.tmp",
                    "*.temp"
                ]
            },
            "medium_risk": {
                "description": "中风险：日志和报告文件",
                "targets": [
                    "logs/*.log",
                    "logs/*.json",
                    "benchmark_results/",
                    "reports/",
                    "*_report_*.md",
                    "*_report_*.json",
                    "*_COMPLETE*.md",
                    "*_FIX_*.md",
                    "*_SUMMARY*.md"
                ]
            },
            "high_risk": {
                "description": "高风险：重复文件和大型测试数据",
                "targets": [
                    "VisionAI-ClipsMaster-Core/tools/ffmpeg/",  # 删除重复的FFmpeg
                    "tools/ffmpeg/ffmpeg.zip",                  # 删除压缩包
                    "test_data.bin",
                    "examples/test_data.bin",
                    "data/test_data/test_model_params.pkl",
                    "tests/golden_samples/zh/*.mp4"             # 大型视频样本
                ]
            }
        }
    
    def log_action(self, action, path, size_saved=0, risk_level="INFO"):
        """记录清理操作"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "path": str(path),
            "size_saved_mb": round(size_saved / (1024 * 1024), 2),
            "risk_level": risk_level,
            "dry_run": self.dry_run
        }
        self.cleanup_log.append(entry)
        
        status = "🔍" if self.dry_run else "✅"
        print(f"{status} [{risk_level}] {action}: {path} (节省 {size_saved / (1024 * 1024):.1f} MB)")
    
    def get_size(self, path):
        """计算文件或目录大小"""
        path = Path(path)
        if not path.exists():
            return 0
        
        if path.is_file():
            try:
                return path.stat().st_size
            except:
                return 0
        
        total = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        total += file_path.stat().st_size
                    except:
                        pass
        except:
            pass
        return total
    
    def is_critical_file(self, path):
        """检查是否为核心功能必需文件"""
        path_str = str(path)
        for critical in self.critical_files:
            if critical.endswith('/'):
                if path_str.startswith(critical) or critical.rstrip('/') in path_str:
                    return True
            else:
                if critical in path_str:
                    return True
        return False
    
    def safe_remove(self, path, risk_level="MEDIUM"):
        """安全删除文件或目录"""
        path = Path(path)
        if not path.exists():
            return 0
        
        # 检查是否为核心文件
        if self.is_critical_file(path):
            self.log_action("跳过核心文件", path, 0, "CRITICAL")
            return 0
        
        size = self.get_size(path)
        
        if not self.dry_run:
            try:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path, ignore_errors=True)
                self.log_action("删除成功", path, size, risk_level)
            except Exception as e:
                self.log_action(f"删除失败: {e}", path, 0, "ERROR")
                return 0
        else:
            self.log_action("预览删除", path, size, risk_level)
        
        return size
    
    def create_backup(self):
        """创建重要文件备份"""
        if self.dry_run:
            print("🔍 预览模式：跳过备份创建")
            return
        
        print("🔄 创建安全备份...")
        self.backup_dir.mkdir(exist_ok=True)
        
        # 备份核心配置文件
        backup_targets = [
            "src/core/",
            "configs/model_config.yaml",
            "VisionAI-ClipsMaster-Core/simple_ui_fixed.py",
            "requirements.txt"
        ]
        
        for target in backup_targets:
            source = self.project_root / target
            if source.exists():
                dest = self.backup_dir / target
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if source.is_dir():
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest)
                except Exception as e:
                    print(f"⚠️ 备份失败 {target}: {e}")
        
        print(f"✅ 备份已创建: {self.backup_dir}")
    
    def cleanup_low_risk(self):
        """清理低风险文件"""
        print("\n🧹 阶段1: 清理低风险文件（缓存和临时文件）")
        total_saved = 0
        
        # Python缓存
        for pycache in self.project_root.rglob("__pycache__"):
            if pycache.is_dir():
                total_saved += self.safe_remove(pycache, "LOW")
        
        for pyc in self.project_root.rglob("*.pyc"):
            total_saved += self.safe_remove(pyc, "LOW")
        
        # 临时文件和缓存
        temp_dirs = ["cache", "temp"]
        for temp_dir in temp_dirs:
            path = self.project_root / temp_dir
            if path.exists():
                # 清理内容但保留目录结构
                for item in path.rglob("*"):
                    if item.is_file():
                        total_saved += self.safe_remove(item, "LOW")
        
        return total_saved
    
    def cleanup_medium_risk(self):
        """清理中风险文件"""
        print("\n📝 阶段2: 清理中风险文件（日志和报告）")
        total_saved = 0
        
        # 清理日志文件（保留目录结构）
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            for log_file in logs_dir.rglob("*.log"):
                total_saved += self.safe_remove(log_file, "MEDIUM")
            
            for json_file in logs_dir.rglob("*.json"):
                # 保留重要的配置JSON
                if "config" not in json_file.name.lower():
                    total_saved += self.safe_remove(json_file, "MEDIUM")
        
        # 删除基准测试结果
        benchmark_dir = self.project_root / "benchmark_results"
        if benchmark_dir.exists():
            total_saved += self.safe_remove(benchmark_dir, "MEDIUM")
        
        # 删除报告目录
        reports_dir = self.project_root / "reports"
        if reports_dir.exists():
            total_saved += self.safe_remove(reports_dir, "MEDIUM")
        
        # 删除过时的报告文件
        report_patterns = [
            "*_report_*.md", "*_report_*.json", "*_COMPLETE*.md", 
            "*_FIX_*.md", "*_SUMMARY*.md", "*_ANALYSIS*.md"
        ]
        
        for pattern in report_patterns:
            for file in self.project_root.glob(pattern):
                # 保留当前分析报告
                if "size_analysis_report" not in file.name:
                    total_saved += self.safe_remove(file, "MEDIUM")
        
        return total_saved
    
    def cleanup_high_risk(self):
        """清理高风险文件"""
        print("\n⚠️ 阶段3: 清理高风险文件（重复文件和大型测试数据）")
        total_saved = 0
        
        # 删除重复的FFmpeg部署
        duplicate_ffmpeg = self.project_root / "VisionAI-ClipsMaster-Core" / "tools" / "ffmpeg"
        if duplicate_ffmpeg.exists():
            total_saved += self.safe_remove(duplicate_ffmpeg, "HIGH")
        
        # 删除FFmpeg压缩包
        ffmpeg_zip = self.project_root / "tools" / "ffmpeg" / "ffmpeg.zip"
        if ffmpeg_zip.exists():
            total_saved += self.safe_remove(ffmpeg_zip, "HIGH")
        
        # 删除大型测试文件
        large_test_files = [
            "test_data.bin",
            "examples/test_data.bin",
            "data/test_data/test_model_params.pkl"
        ]
        
        for file_path in large_test_files:
            path = self.project_root / file_path
            if path.exists():
                total_saved += self.safe_remove(path, "HIGH")
        
        # 删除大型视频样本（保留小的测试样本）
        golden_samples = self.project_root / "tests" / "golden_samples" / "zh"
        if golden_samples.exists():
            for video_file in golden_samples.glob("*.mp4"):
                # 只删除大于50MB的视频文件
                if self.get_size(video_file) > 50 * 1024 * 1024:
                    total_saved += self.safe_remove(video_file, "HIGH")
        
        return total_saved
    
    def generate_cleanup_report(self, total_saved):
        """生成清理报告"""
        report = {
            "cleanup_summary": {
                "execution_time": datetime.now().isoformat(),
                "dry_run": self.dry_run,
                "total_files_processed": len(self.cleanup_log),
                "total_size_saved_mb": round(total_saved / (1024 * 1024), 2),
                "total_size_saved_gb": round(total_saved / (1024 * 1024 * 1024), 2)
            },
            "cleanup_log": self.cleanup_log,
            "risk_breakdown": {
                "low_risk": len([l for l in self.cleanup_log if l["risk_level"] == "LOW"]),
                "medium_risk": len([l for l in self.cleanup_log if l["risk_level"] == "MEDIUM"]),
                "high_risk": len([l for l in self.cleanup_log if l["risk_level"] == "HIGH"]),
                "errors": len([l for l in self.cleanup_log if l["risk_level"] == "ERROR"])
            }
        }
        
        report_file = self.project_root / "cleanup_execution_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 清理完成！")
        print(f"处理文件数: {len(self.cleanup_log)}")
        print(f"节省空间: {total_saved / (1024 * 1024):.1f} MB ({total_saved / (1024 * 1024 * 1024):.2f} GB)")
        print(f"详细报告: {report_file}")
        
        if self.dry_run:
            print("\n🔍 这是预览模式，实际文件未被删除")
            print("💡 要执行实际清理，请运行: python safe_cleanup_executor.py --execute")
        
        return report
    
    def execute_cleanup(self, risk_levels=None):
        """执行清理操作"""
        if risk_levels is None:
            risk_levels = ["low", "medium", "high"]
        
        print("🎯 VisionAI-ClipsMaster 安全清理执行器")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 预览模式：显示将要删除的文件")
        else:
            self.create_backup()
        
        total_saved = 0
        
        # 执行清理阶段
        if "low" in risk_levels:
            total_saved += self.cleanup_low_risk()
        
        if "medium" in risk_levels:
            total_saved += self.cleanup_medium_risk()
        
        if "high" in risk_levels:
            total_saved += self.cleanup_high_risk()
        
        # 生成报告
        return self.generate_cleanup_report(total_saved)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 安全清理执行器")
    parser.add_argument("--execute", action="store_true",
                       help="执行实际清理操作（默认为预览模式）")
    parser.add_argument("--risk-levels", nargs="+", 
                       choices=["low", "medium", "high"],
                       default=["low", "medium", "high"],
                       help="选择要执行的风险等级")
    parser.add_argument("--project-root", default=".",
                       help="项目根目录路径")
    
    args = parser.parse_args()
    
    # 默认为预览模式，需要明确指定 --execute 才会实际删除
    dry_run = not args.execute
    
    executor = SafeCleanupExecutor(args.project_root, dry_run)
    executor.execute_cleanup(args.risk_levels)

if __name__ == "__main__":
    main()
