#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster P0+P1级体积优化脚本
目标：从5.13GB压缩至2GB左右（50%压缩率）
"""

import os
import shutil
import glob
import json
from datetime import datetime
from pathlib import Path

class VisionAIOptimizer:
    def __init__(self):
        self.log_file = "optimization_log.txt"
        self.deleted_files = []
        self.total_saved = 0
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    
    def get_size_mb(self, path):
        """获取文件/目录大小(MB)"""
        if os.path.isfile(path):
            return os.path.getsize(path) / (1024 * 1024)
        elif os.path.isdir(path):
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except:
                        pass
            return total / (1024 * 1024)
        return 0
    
    def safe_remove(self, path, description=""):
        """安全删除文件/目录"""
        if not os.path.exists(path):
            self.log(f"⚠️ 路径不存在: {path}")
            return 0
        
        size_mb = self.get_size_mb(path)
        
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            
            self.deleted_files.append({
                "path": path,
                "size_mb": size_mb,
                "description": description
            })
            self.total_saved += size_mb
            self.log(f"✅ 已删除 {description}: {path} ({size_mb:.2f} MB)")
            return size_mb
        except Exception as e:
            self.log(f"❌ 删除失败 {path}: {e}")
            return 0
    
    def p0_optimization(self):
        """P0级优化：零风险清理"""
        self.log("=== 开始P0级优化（零风险清理）===")
        
        # 1. 清理缓存目录
        cache_dirs = ["cache", "temp", "__pycache__"]
        for cache_dir in cache_dirs:
            self.safe_remove(cache_dir, f"缓存目录 {cache_dir}")
        
        # 2. 清理Python编译文件
        pyc_files = glob.glob("**/*.pyc", recursive=True)
        for pyc_file in pyc_files:
            self.safe_remove(pyc_file, "Python编译文件")
        
        pycache_dirs = glob.glob("**/__pycache__", recursive=True)
        for pycache_dir in pycache_dirs:
            self.safe_remove(pycache_dir, "Python缓存目录")
        
        # 3. 清理日志文件
        log_patterns = [
            "*.log", "crash_log*.txt", "logs/", 
            "*_test.log", "*_debug.log"
        ]
        for pattern in log_patterns:
            files = glob.glob(pattern, recursive=True)
            for file in files:
                if file != self.log_file:  # 保留当前日志
                    self.safe_remove(file, f"日志文件 {pattern}")
        
        # 4. 清理历史备份
        backup_patterns = [
            "backup_*", "cleanup_backup", "*_backup_*",
            "*.backup", "docs_backup"
        ]
        for pattern in backup_patterns:
            items = glob.glob(pattern, recursive=True)
            for item in items:
                self.safe_remove(item, f"历史备份 {pattern}")
        
        # 5. 清理测试数据
        test_data_patterns = [
            "data/test_data/sample_video_*.mp4",
            "data/stress_test_files/",
            "tests/stress_test/",
            "tests/long_stress_test/",
            "*_report_*.json",
            "benchmark_results/",
            "stability_test_output/"
        ]
        for pattern in test_data_patterns:
            items = glob.glob(pattern, recursive=True)
            for item in items:
                self.safe_remove(item, f"测试数据 {pattern}")
        
        self.log(f"P0级优化完成，节省空间: {self.total_saved:.2f} MB")
    
    def p1_optimization(self):
        """P1级优化：低风险优化"""
        self.log("=== 开始P1级优化（低风险优化）===")
        
        # 1. 删除多语言文档副本
        doc_dirs = ["docs/en/", "docs/ja/", "docs/zh_CN/"]
        for doc_dir in doc_dirs:
            self.safe_remove(doc_dir, f"多语言文档 {doc_dir}")
        
        # 2. 删除示例配置
        config_dirs = [
            "configs/examples/", "configs/samples/",
            "configs/environments/dev/", "configs/environments/staging/"
        ]
        for config_dir in config_dirs:
            self.safe_remove(config_dir, f"示例配置 {config_dir}")
        
        # 3. 精简测试套件
        test_dirs = [
            "tests/benchmarks/", "tests/performance/", "tests/chaos_results/",
            "tests/device_compatibility/", "tests/hardware_test/"
        ]
        for test_dir in test_dirs:
            self.safe_remove(test_dir, f"边缘测试 {test_dir}")
        
        # 4. 删除可选功能模块
        optional_modules = [
            "src/audience/", "src/benchmarks/", "src/chaos/",
            "src/visualization/", "src/dashboard/web_*"
        ]
        for module in optional_modules:
            items = glob.glob(module, recursive=True)
            for item in items:
                self.safe_remove(item, f"可选模块 {module}")
        
        # 5. 清理大型测试报告文件
        large_files = glob.glob("*Test_Report_*.json", recursive=True)
        for file in large_files:
            if self.get_size_mb(file) > 1:  # 大于1MB的报告文件
                self.safe_remove(file, "大型测试报告")
        
        self.log(f"P1级优化完成，总节省空间: {self.total_saved:.2f} MB")
    
    def generate_report(self):
        """生成优化报告"""
        report = {
            "optimization_time": datetime.now().isoformat(),
            "total_saved_mb": round(self.total_saved, 2),
            "deleted_files_count": len(self.deleted_files),
            "deleted_files": self.deleted_files
        }
        
        with open("optimization_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"优化报告已生成: optimization_report.json")
        self.log(f"总计节省空间: {self.total_saved:.2f} MB")
        self.log(f"删除文件数量: {len(self.deleted_files)}")

if __name__ == "__main__":
    optimizer = VisionAIOptimizer()
    
    # 执行P0级优化
    optimizer.p0_optimization()
    
    # 执行P1级优化
    optimizer.p1_optimization()
    
    # 生成报告
    optimizer.generate_report()
    
    print(f"\n🎉 优化完成！总计节省空间: {optimizer.total_saved:.2f} MB")
    print("详细日志请查看: optimization_log.txt")
    print("优化报告请查看: optimization_report.json")
