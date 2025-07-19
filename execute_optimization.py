#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 体积优化执行器
一键执行完整的体积优化流程
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

class OptimizationExecutor:
    def __init__(self):
        self.project_root = Path(".")
        self.start_time = datetime.now()
        self.log_file = f"optimization_execution_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        
        # 执行阶段
        self.phases = [
            ("准备阶段", self.phase_preparation),
            ("体积分析", self.phase_analysis),
            ("安全备份", self.phase_backup),
            ("执行优化", self.phase_optimization),
            ("功能验证", self.phase_validation),
            ("生成报告", self.phase_reporting)
        ]
        
        self.results = {
            "execution_start": self.start_time.isoformat(),
            "phases": {},
            "overall_status": "RUNNING",
            "size_before_mb": 0,
            "size_after_mb": 0,
            "space_saved_mb": 0,
            "errors": [],
            "warnings": []
        }
    
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        
        # 控制台输出
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️ {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            print(f"ℹ️ {message}")
        
        # 文件日志
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    
    def run_script(self, script_name, args=None):
        """运行Python脚本"""
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log(f"脚本 {script_name} 执行成功")
                return True, result.stdout
            else:
                self.log(f"脚本 {script_name} 执行失败: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"脚本 {script_name} 执行超时", "ERROR")
            return False, "执行超时"
        except Exception as e:
            self.log(f"脚本 {script_name} 执行异常: {e}", "ERROR")
            return False, str(e)
    
    def get_project_size(self):
        """获取项目总大小"""
        total_size = 0
        try:
            for root, dirs, files in os.walk("."):
                # 跳过备份目录
                dirs[:] = [d for d in dirs if not d.startswith('optimization_backup')]
                
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except:
                        continue
            
            return total_size / (1024 * 1024)  # 转换为MB
        except Exception as e:
            self.log(f"计算项目大小失败: {e}", "ERROR")
            return 0
    
    def phase_preparation(self):
        """准备阶段"""
        self.log("开始准备阶段")
        
        # 检查Python环境
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            self.log("Python版本过低，需要Python 3.8+", "ERROR")
            return False
        
        self.log(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查必要的模块
        required_modules = ["json", "pathlib", "shutil", "subprocess"]
        for module in required_modules:
            try:
                __import__(module)
                self.log(f"模块 {module} 可用")
            except ImportError:
                self.log(f"缺少必要模块: {module}", "ERROR")
                return False
        
        # 检查磁盘空间
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            
            if free_gb < 2:
                self.log(f"磁盘空间不足: {free_gb:.1f}GB", "WARNING")
            else:
                self.log(f"磁盘可用空间: {free_gb:.1f}GB")
        except:
            self.log("无法检查磁盘空间", "WARNING")
        
        self.log("准备阶段完成", "SUCCESS")
        return True
    
    def phase_analysis(self):
        """体积分析阶段"""
        self.log("开始体积分析")
        
        # 记录优化前大小
        self.results["size_before_mb"] = self.get_project_size()
        self.log(f"优化前项目大小: {self.results['size_before_mb']:.1f}MB")
        
        # 运行详细分析脚本
        if os.path.exists("analyze_project_size_detailed.py"):
            success, output = self.run_script("analyze_project_size_detailed.py")
            if success:
                self.log("项目体积分析完成", "SUCCESS")
            else:
                self.log("项目体积分析失败", "WARNING")
        else:
            self.log("分析脚本不存在，跳过详细分析", "WARNING")
        
        return True
    
    def phase_backup(self):
        """安全备份阶段"""
        self.log("开始安全备份")
        
        # 创建备份目录
        backup_dir = Path("optimization_backup")
        backup_dir.mkdir(exist_ok=True)
        
        # 备份关键文件
        critical_files = [
            "simple_ui_fixed.py",
            "src/core",
            "configs",
            "requirements.txt"
        ]
        
        import shutil
        backup_success = True
        
        for item in critical_files:
            if os.path.exists(item):
                try:
                    backup_path = backup_dir / item
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if os.path.isfile(item):
                        shutil.copy2(item, backup_path)
                    elif os.path.isdir(item):
                        if backup_path.exists():
                            shutil.rmtree(backup_path)
                        shutil.copytree(item, backup_path)
                    
                    self.log(f"备份完成: {item}")
                except Exception as e:
                    self.log(f"备份失败 {item}: {e}", "ERROR")
                    backup_success = False
            else:
                self.log(f"备份目标不存在: {item}", "WARNING")
        
        if backup_success:
            self.log("安全备份完成", "SUCCESS")
        else:
            self.log("部分备份失败", "WARNING")
        
        return backup_success
    
    def phase_optimization(self):
        """执行优化阶段"""
        self.log("开始执行优化")
        
        if not os.path.exists("size_optimizer.py"):
            self.log("优化脚本不存在", "ERROR")
            return False
        
        # 运行优化脚本
        success, output = self.run_script("size_optimizer.py")
        
        if success:
            self.log("体积优化完成", "SUCCESS")
            
            # 计算优化后大小
            self.results["size_after_mb"] = self.get_project_size()
            self.results["space_saved_mb"] = self.results["size_before_mb"] - self.results["size_after_mb"]
            
            self.log(f"优化后项目大小: {self.results['size_after_mb']:.1f}MB")
            self.log(f"节省空间: {self.results['space_saved_mb']:.1f}MB")
            
            return True
        else:
            self.log("体积优化失败", "ERROR")
            return False
    
    def phase_validation(self):
        """功能验证阶段"""
        self.log("开始功能验证")
        
        if not os.path.exists("function_validator.py"):
            self.log("验证脚本不存在", "ERROR")
            return False
        
        # 运行验证脚本
        success, output = self.run_script("function_validator.py")
        
        if success:
            self.log("功能验证通过", "SUCCESS")
            return True
        else:
            self.log("功能验证失败", "ERROR")
            return False
    
    def phase_reporting(self):
        """生成报告阶段"""
        self.log("开始生成报告")
        
        # 计算执行时间
        end_time = datetime.now()
        execution_time = end_time - self.start_time
        
        self.results["execution_end"] = end_time.isoformat()
        self.results["execution_time_seconds"] = execution_time.total_seconds()
        
        # 生成最终报告
        report = {
            "optimization_summary": {
                "start_time": self.results["execution_start"],
                "end_time": self.results["execution_end"],
                "execution_time": f"{execution_time.total_seconds():.1f}秒",
                "size_before_gb": round(self.results["size_before_mb"] / 1024, 2),
                "size_after_gb": round(self.results["size_after_mb"] / 1024, 2),
                "space_saved_gb": round(self.results["space_saved_mb"] / 1024, 2),
                "space_saved_percent": round((self.results["space_saved_mb"] / self.results["size_before_mb"]) * 100, 1) if self.results["size_before_mb"] > 0 else 0,
                "target_achieved": self.results["size_after_mb"] / 1024 <= 5.0
            },
            "phase_results": self.results["phases"],
            "errors": self.results["errors"],
            "warnings": self.results["warnings"]
        }
        
        # 保存报告
        report_file = f"optimization_final_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"最终报告已保存: {report_file}", "SUCCESS")
        
        # 打印总结
        print("\n" + "="*60)
        print("🎉 VisionAI-ClipsMaster 体积优化完成!")
        print("="*60)
        print(f"📊 优化前大小: {report['optimization_summary']['size_before_gb']} GB")
        print(f"📊 优化后大小: {report['optimization_summary']['size_after_gb']} GB")
        print(f"💾 节省空间: {report['optimization_summary']['space_saved_gb']} GB ({report['optimization_summary']['space_saved_percent']}%)")
        print(f"⏱️ 执行时间: {report['optimization_summary']['execution_time']}")
        print(f"🎯 目标达成: {'✅ 是' if report['optimization_summary']['target_achieved'] else '❌ 否'}")
        print("="*60)
        
        return True
    
    def execute(self):
        """执行完整优化流程"""
        self.log("🚀 开始VisionAI-ClipsMaster体积优化执行")
        
        overall_success = True
        
        for phase_name, phase_func in self.phases:
            self.log(f"\n📋 执行阶段: {phase_name}")
            
            phase_start = time.time()
            
            try:
                success = phase_func()
                phase_time = time.time() - phase_start
                
                self.results["phases"][phase_name] = {
                    "status": "SUCCESS" if success else "FAILED",
                    "execution_time": round(phase_time, 2),
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    self.log(f"阶段 {phase_name} 完成 ({phase_time:.1f}秒)", "SUCCESS")
                else:
                    self.log(f"阶段 {phase_name} 失败", "ERROR")
                    overall_success = False
                    
                    # 关键阶段失败时询问是否继续
                    if phase_name in ["安全备份", "执行优化"]:
                        response = input(f"\n⚠️ 关键阶段 '{phase_name}' 失败，是否继续? (y/N): ")
                        if response.lower() != 'y':
                            self.log("用户选择中止执行", "ERROR")
                            break
                
            except Exception as e:
                self.log(f"阶段 {phase_name} 异常: {e}", "ERROR")
                self.results["errors"].append(f"{phase_name}: {str(e)}")
                overall_success = False
                break
        
        # 设置最终状态
        self.results["overall_status"] = "SUCCESS" if overall_success else "FAILED"
        
        return overall_success

def main():
    print("VisionAI-ClipsMaster 体积优化执行器")
    print("=" * 50)
    
    # 确认执行
    print("⚠️ 此操作将对项目进行体积优化，包括删除冗余文件")
    print("📋 执行前请确保:")
    print("  1. 已关闭所有相关程序")
    print("  2. 重要数据已备份")
    print("  3. 有足够的磁盘空间")
    
    response = input("\n是否继续执行优化? (y/N): ")
    if response.lower() != 'y':
        print("❌ 用户取消操作")
        return
    
    executor = OptimizationExecutor()
    
    try:
        success = executor.execute()
        
        if success:
            print("\n🎉 优化执行成功!")
            sys.exit(0)
        else:
            print("\n❌ 优化执行失败，请检查日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
