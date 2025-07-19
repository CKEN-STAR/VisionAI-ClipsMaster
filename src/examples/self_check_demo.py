#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自检容错系统示例

演示如何在VisionAI-ClipsMaster中使用自检容错系统。
"""

import os
import sys
import time
import logging
import threading
import signal
from typing import Dict, Any, List

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

from src.monitor.self_check import (
    Watchdog, SystemSelfCheck, ComponentStatus, CheckResult,
    get_self_check, start_self_check, stop_self_check
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("self_check_demo")


class DemoApplication:
    """示例应用类"""
    
    def __init__(self):
        """初始化示例应用"""
        self.running = False
        self.worker_threads = []
        self.self_check = get_self_check()
        
        # 注册自定义检查和恢复处理器
        self.register_custom_handlers()
        
        logger.info("初始化示例应用")
    
    def register_custom_handlers(self):
        """注册自定义处理器"""
        # 注册应用特定的检查
        self.self_check.register_check("app_health", self.check_app_health)
        self.self_check.register_check("worker_threads", self.check_worker_threads)
        
        # 注册应用特定的恢复处理器
        self.self_check.register_recovery("restart_workers", self.restart_workers)
    
    def start(self):
        """启动应用"""
        logger.info("启动示例应用")
        
        # 设置为运行状态
        self.running = True
        
        # 启动自检系统
        self.self_check.start()
        
        # 启动工作线程
        self.start_worker_threads()
        
        logger.info("示例应用已启动")
    
    def stop(self):
        """停止应用"""
        logger.info("停止示例应用")
        
        # 设置为停止状态
        self.running = False
        
        # 停止工作线程
        self.stop_worker_threads()
        
        # 停止自检系统
        stop_self_check()
        
        logger.info("示例应用已停止")
    
    def start_worker_threads(self):
        """启动工作线程"""
        logger.info("启动工作线程")
        
        # 清理旧线程
        self.worker_threads.clear()
        
        # 创建数据采集线程
        data_thread = self.create_data_thread()
        self.worker_threads.append(data_thread)
        
        # 创建处理线程
        process_thread = self.create_process_thread()
        self.worker_threads.append(process_thread)
        
        # 注册线程到监视器
        self.self_check.watchdog.register_thread(
            "data_thread", 
            data_thread, 
            self.create_data_thread
        )
        
        self.self_check.watchdog.register_thread(
            "process_thread", 
            process_thread, 
            self.create_process_thread
        )
        
        logger.info(f"已启动 {len(self.worker_threads)} 个工作线程")
    
    def stop_worker_threads(self):
        """停止工作线程"""
        logger.info("停止工作线程")
        
        # 等待线程结束
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # 清理线程列表
        self.worker_threads.clear()
        
        logger.info("所有工作线程已停止")
    
    def create_data_thread(self):
        """创建数据采集线程
        
        Returns:
            线程对象
        """
        def data_worker():
            """数据采集工作函数"""
            logger.info("数据采集线程开始运行")
            
            while self.running:
                try:
                    # 模拟数据采集
                    logger.debug("采集数据...")
                    time.sleep(0.5)
                    
                    # 更新心跳
                    self.self_check.watchdog.heartbeat()
                    
                except Exception as e:
                    logger.error(f"数据采集线程异常: {e}")
                
                # 检查是否需要退出
                if not self.running:
                    break
            
            logger.info("数据采集线程结束")
        
        # 创建线程
        thread = threading.Thread(
            target=data_worker,
            name="data-worker",
            daemon=True
        )
        
        # 启动线程
        thread.start()
        
        return thread
    
    def create_process_thread(self):
        """创建处理线程
        
        Returns:
            线程对象
        """
        def process_worker():
            """数据处理工作函数"""
            logger.info("数据处理线程开始运行")
            
            while self.running:
                try:
                    # 模拟数据处理
                    logger.debug("处理数据...")
                    time.sleep(0.7)
                    
                    # 更新心跳
                    self.self_check.watchdog.heartbeat()
                    
                except Exception as e:
                    logger.error(f"数据处理线程异常: {e}")
                
                # 检查是否需要退出
                if not self.running:
                    break
            
            logger.info("数据处理线程结束")
        
        # 创建线程
        thread = threading.Thread(
            target=process_worker,
            name="process-worker",
            daemon=True
        )
        
        # 启动线程
        thread.start()
        
        return thread
    
    def check_app_health(self) -> CheckResult:
        """检查应用健康状况
        
        Returns:
            检查结果
        """
        if not self.running:
            return CheckResult(
                ComponentStatus.WARNING,
                "应用未运行",
                {"running": False}
            )
        
        # 检查线程状态
        if not all(thread.is_alive() for thread in self.worker_threads):
            dead_threads = [t.name for t in self.worker_threads if not t.is_alive()]
            return CheckResult(
                ComponentStatus.ERROR,
                f"部分线程已停止: {', '.join(dead_threads)}",
                {"dead_threads": dead_threads}
            )
        
        # 其他健康检查
        # ...
        
        return CheckResult(
            ComponentStatus.NORMAL,
            "应用健康状况正常",
            {"running": True, "thread_count": len(self.worker_threads)}
        )
    
    def check_worker_threads(self) -> CheckResult:
        """检查工作线程状态
        
        Returns:
            检查结果
        """
        active_threads = [t for t in self.worker_threads if t.is_alive()]
        
        details = {
            "total": len(self.worker_threads),
            "active": len(active_threads),
            "threads": [{"name": t.name, "alive": t.is_alive()} for t in self.worker_threads]
        }
        
        if len(active_threads) < len(self.worker_threads):
            return CheckResult(
                ComponentStatus.WARNING,
                f"部分工作线程未运行 ({len(active_threads)}/{len(self.worker_threads)})",
                details
            )
        else:
            return CheckResult(
                ComponentStatus.NORMAL,
                f"所有工作线程正常运行 ({len(active_threads)}/{len(self.worker_threads)})",
                details
            )
    
    def restart_workers(self, check_name: str, details: Dict[str, Any]) -> bool:
        """重启工作线程
        
        Args:
            check_name: 检查名称
            details: 详细信息
        
        Returns:
            是否成功
        """
        logger.info(f"重启工作线程: {check_name}")
        
        try:
            self.stop_worker_threads()
            time.sleep(0.5)
            self.start_worker_threads()
            return True
        except Exception as e:
            logger.error(f"重启工作线程失败: {e}")
            return False
    
    def simulate_thread_crash(self, thread_name: str = None):
        """模拟线程崩溃
        
        Args:
            thread_name: 线程名称，如果为None则随机选择
        """
        if not self.worker_threads:
            logger.warning("没有可用的工作线程")
            return
        
        if thread_name:
            # 查找指定名称的线程
            for i, thread in enumerate(self.worker_threads):
                if thread.name == thread_name:
                    logger.info(f"模拟线程崩溃: {thread_name} (索引 {i})")
                    self.worker_threads[i] = threading.Thread(target=lambda: None)
                    self.worker_threads[i].name = thread_name
                    return
            
            logger.warning(f"未找到线程: {thread_name}")
        else:
            # 随机选择一个线程
            import random
            i = random.randint(0, len(self.worker_threads) - 1)
            thread_name = self.worker_threads[i].name
            logger.info(f"模拟线程崩溃: {thread_name} (索引 {i})")
            self.worker_threads[i] = threading.Thread(target=lambda: None)
            self.worker_threads[i].name = thread_name
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """运行诊断
        
        Returns:
            诊断结果
        """
        logger.info("运行应用诊断")
        
        # 运行所有检查
        results = self.self_check.run_all_checks()
        
        # 处理结果
        result_summary = {
            "total_checks": len(results),
            "status_counts": {},
            "checks": {}
        }
        
        # 汇总状态
        for name, result in results.items():
            status = result.status.value
            result_summary["status_counts"][status] = result_summary["status_counts"].get(status, 0) + 1
            result_summary["checks"][name] = {
                "status": status,
                "message": result.message
            }
        
        return result_summary
    
    def print_diagnostic_report(self):
        """打印诊断报告"""
        diagnostic = self.run_diagnostic()
        
        print("\n==== 应用诊断报告 ====")
        print(f"总检查项: {diagnostic['total_checks']}")
        
        print("\n状态统计:")
        for status, count in diagnostic["status_counts"].items():
            print(f"- {status}: {count}")
        
        print("\n详细检查结果:")
        for name, result in diagnostic["checks"].items():
            print(f"- {name}: {result['status']} - {result['message']}")
        
        print("\n==== Watchdog状态 ====")
        summary = self.self_check.watchdog.get_status_summary()
        print(f"Watchdog活跃: {summary['watchdog_alive']}")
        print(f"注册线程数: {summary['thread_count']}")
        print(f"活跃线程数: {summary['active_threads']}")
        print(f"最后心跳间隔: {summary['last_heartbeat_age']:.1f}秒")
        print(f"内存使用率: {summary['memory_percent']:.1f}%")
        print(f"CPU使用率: {summary['cpu_percent']:.1f}%")
        print(f"磁盘使用率: {summary['disk_percent']:.1f}%")
        
        print("\n==== 最近警报 ====")
        alerts = self.self_check.watchdog.get_alerts(limit=5)
        for alert in alerts:
            print(f"- {alert['datetime']} {alert['status']}: {alert['message']}")
        
        print("\n")


def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info("接收到终止信号，退出应用")
    
    # 停止应用
    if 'app' in globals():
        app.stop()
    
    # 退出程序
    sys.exit(0)


def demo_interactive():
    """交互式演示"""
    global app
    
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    
    # 创建应用
    app = DemoApplication()
    
    # 启动应用
    app.start()
    
    try:
        # 显示菜单
        while True:
            print("\n==== 自检容错系统演示 ====")
            print("1. 运行诊断")
            print("2. 模拟线程崩溃")
            print("3. 查看最近警报")
            print("4. 手动更新心跳")
            print("5. 重启工作线程")
            print("0. 退出")
            
            choice = input("\n请选择操作 [0-5]: ")
            
            if choice == '0':
                break
            elif choice == '1':
                app.print_diagnostic_report()
            elif choice == '2':
                thread_name = input("输入线程名称 (为空则随机选择): ")
                app.simulate_thread_crash(thread_name if thread_name else None)
            elif choice == '3':
                alerts = app.self_check.watchdog.get_alerts(limit=10)
                print("\n==== 最近警报 ====")
                for alert in alerts:
                    print(f"- {alert['datetime']} {alert['status']}: {alert['message']}")
            elif choice == '4':
                app.self_check.watchdog.heartbeat()
                print("心跳已更新")
            elif choice == '5':
                app.restart_workers("manual", {})
                print("工作线程已重启")
            else:
                print("无效的选择，请重新输入")
            
            # 小暂停，让自检系统有时间运行
            time.sleep(0.5)
    
    finally:
        # 停止应用
        app.stop()


def demo_automated():
    """自动演示"""
    global app
    
    # 创建应用
    app = DemoApplication()
    
    try:
        # 启动应用
        app.start()
        
        # 等待系统初始化
        time.sleep(2)
        
        # 运行诊断
        print("\n=== 初始状态诊断 ===")
        app.print_diagnostic_report()
        
        # 模拟线程崩溃
        print("\n=== 模拟线程崩溃 ===")
        app.simulate_thread_crash()
        
        # 等待自检系统检测并恢复
        print("等待自检系统检测并恢复...")
        time.sleep(5)
        
        # 再次运行诊断
        print("\n=== 恢复后诊断 ===")
        app.print_diagnostic_report()
        
    finally:
        # 停止应用
        app.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="自检容错系统演示")
    parser.add_argument("--interactive", action="store_true", help="启用交互式演示")
    parser.add_argument("--automated", action="store_true", help="启用自动演示")
    
    args = parser.parse_args()
    
    if args.interactive:
        demo_interactive()
    elif args.automated:
        demo_automated()
    else:
        # 默认使用交互式模式
        demo_interactive() 