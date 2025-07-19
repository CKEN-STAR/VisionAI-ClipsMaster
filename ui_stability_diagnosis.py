#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI稳定性诊断工具
用于诊断UI进程为什么会在测试过程中退出
"""

import sys
import os
import time
import psutil
import subprocess
import threading
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

class UIStabilityDiagnosis:
    """UI稳定性诊断器"""
    
    def __init__(self):
        self.ui_process = None
        self.ui_process_id = None
        self.monitoring_active = False
        self.monitor_thread = None
        self.process_logs = []
        
    def start_ui_process(self):
        """启动UI进程"""
        try:
            print("正在启动UI进程...")
            python_exe = r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
            ui_script = PROJECT_ROOT / "simple_ui_fixed.py"
            
            # 启动UI进程
            self.ui_process = subprocess.Popen(
                [python_exe, str(ui_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.ui_process_id = self.ui_process.pid
            print(f"✓ UI进程已启动，PID: {self.ui_process_id}")
            
            # 等待UI启动
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"✗ UI进程启动失败: {e}")
            return False
    
    def start_monitoring(self):
        """开始监控UI进程"""
        if not self.ui_process_id:
            print("✗ 无法开始监控：UI进程未启动")
            return False
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print("✓ 开始监控UI进程")
        return True
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                if not self.ui_process_id:
                    break
                
                # 检查进程状态
                process = psutil.Process(self.ui_process_id)
                
                # 收集进程信息
                process_info = {
                    'timestamp': time.time(),
                    'is_running': process.is_running(),
                    'status': process.status(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'create_time': process.create_time()
                }
                
                self.process_logs.append(process_info)
                
                # 打印状态信息
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"状态: {process_info['status']}, "
                      f"内存: {process_info['memory_mb']:.1f}MB, "
                      f"CPU: {process_info['cpu_percent']:.1f}%, "
                      f"线程: {process_info['num_threads']}")
                
                # 检查是否有异常
                if not process_info['is_running']:
                    print(f"⚠️ 进程已停止运行")
                    break
                
                time.sleep(2)  # 每2秒检查一次
                
            except psutil.NoSuchProcess:
                print(f"❌ 进程 {self.ui_process_id} 已退出")
                break
            except Exception as e:
                print(f"❌ 监控错误: {e}")
                break
        
        print("✓ 监控结束")
    
    def check_process_output(self):
        """检查进程输出"""
        if not self.ui_process:
            return None, None
        
        try:
            # 非阻塞读取输出
            stdout_data = ""
            stderr_data = ""
            
            if self.ui_process.stdout:
                stdout_data = self.ui_process.stdout.read()
            if self.ui_process.stderr:
                stderr_data = self.ui_process.stderr.read()
            
            return stdout_data, stderr_data
        except Exception as e:
            print(f"读取进程输出失败: {e}")
            return None, None
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def terminate_ui_process(self):
        """终止UI进程"""
        if self.ui_process:
            try:
                self.ui_process.terminate()
                self.ui_process.wait(timeout=10)
                print("✓ UI进程已终止")
            except Exception as e:
                print(f"终止UI进程失败: {e}")
    
    def generate_diagnosis_report(self):
        """生成诊断报告"""
        print("\n" + "="*60)
        print("UI稳定性诊断报告")
        print("="*60)
        
        if not self.process_logs:
            print("❌ 没有收集到进程日志")
            return
        
        print(f"监控时长: {len(self.process_logs) * 2} 秒")
        print(f"数据点数量: {len(self.process_logs)}")
        
        # 分析内存使用
        memory_values = [log['memory_mb'] for log in self.process_logs]
        print(f"内存使用: 最小 {min(memory_values):.1f}MB, "
              f"最大 {max(memory_values):.1f}MB, "
              f"平均 {sum(memory_values)/len(memory_values):.1f}MB")
        
        # 分析CPU使用
        cpu_values = [log['cpu_percent'] for log in self.process_logs if log['cpu_percent'] > 0]
        if cpu_values:
            print(f"CPU使用: 最大 {max(cpu_values):.1f}%, "
                  f"平均 {sum(cpu_values)/len(cpu_values):.1f}%")
        
        # 分析线程数
        thread_values = [log['num_threads'] for log in self.process_logs]
        print(f"线程数: 最小 {min(thread_values)}, "
              f"最大 {max(thread_values)}, "
              f"平均 {sum(thread_values)/len(thread_values):.1f}")
        
        # 检查进程状态变化
        statuses = [log['status'] for log in self.process_logs]
        unique_statuses = list(set(statuses))
        print(f"进程状态: {', '.join(unique_statuses)}")
        
        # 检查是否有异常退出
        last_log = self.process_logs[-1]
        if not last_log['is_running']:
            print("❌ 进程异常退出")
        else:
            print("✓ 进程正常运行")

def main():
    """主函数"""
    print("VisionAI-ClipsMaster UI稳定性诊断工具")
    print("="*50)
    
    diagnosis = UIStabilityDiagnosis()
    
    try:
        # 启动UI进程
        if not diagnosis.start_ui_process():
            return 1
        
        # 开始监控
        if not diagnosis.start_monitoring():
            return 1
        
        # 运行诊断（30秒）
        print("正在运行30秒诊断...")
        time.sleep(30)
        
        # 检查进程输出
        stdout, stderr = diagnosis.check_process_output()
        if stdout:
            print(f"进程标准输出:\n{stdout}")
        if stderr:
            print(f"进程错误输出:\n{stderr}")
        
    except KeyboardInterrupt:
        print("\n用户中断诊断")
    except Exception as e:
        print(f"诊断过程中发生错误: {e}")
    finally:
        # 停止监控
        diagnosis.stop_monitoring()
        
        # 生成报告
        diagnosis.generate_diagnosis_report()
        
        # 终止UI进程
        diagnosis.terminate_ui_process()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
