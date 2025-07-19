#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 性能测试脚本（改进版）

用于测试改进后的线程管理和视频处理模块的性能和稳定性
"""

import os
import sys
import time
import logging
import tempfile
import threading
import gc
from pathlib import Path
from typing import Dict, List, Any
import argparse

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QImage

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("performance_test_results.log", mode="w")
    ]
)

logger = logging.getLogger("performance_test")

# 尝试导入内存泄漏检测器
try:
    from ui.utils.memory_leak_detector import get_memory_leak_detector, generate_report
    HAS_MEMORY_DETECTOR = True
except ImportError:
    logger.warning("内存泄漏检测器不可用，将不进行内存分析")
    HAS_MEMORY_DETECTOR = False

# 尝试导入psutil（用于监控系统资源）
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    logger.warning("psutil模块不可用，将不进行系统资源监控")
    HAS_PSUTIL = False

# 导入视频处理模块
from ui.video import VideoProcessor, VideoManager

class TestCase:
    """测试用例基类"""
    
    def __init__(self, name: str, description: str):
        """初始化测试用例
        
        Args:
            name: 测试名称
            description: 测试描述
        """
        self.name = name
        self.description = description
        self.result = {
            "status": "not_run",
            "passed": False,
            "execution_time": 0,
            "memory_before": {},
            "memory_after": {},
            "details": {}
        }
    
    def run(self) -> Dict[str, Any]:
        """运行测试用例
        
        Returns:
            dict: 测试结果
        """
        logger.info(f"开始测试: {self.name} - {self.description}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 记录开始时的内存使用
        if HAS_PSUTIL:
            self.result["memory_before"] = self._get_memory_usage()
        
        # 运行测试前的准备
        self.setup()
        
        try:
            # 执行测试
            test_passed = self.execute()
            
            # 更新测试结果
            self.result["status"] = "completed"
            self.result["passed"] = test_passed
            
            if test_passed:
                logger.info(f"测试通过: {self.name}")
            else:
                logger.error(f"测试失败: {self.name}")
                
        except Exception as e:
            # 测试过程中出现异常
            logger.exception(f"测试异常: {self.name} - {str(e)}")
            self.result["status"] = "error"
            self.result["passed"] = False
            self.result["details"]["error"] = str(e)
            
        finally:
            # 测试后清理
            self.teardown()
            
            # 记录结束时间和内存使用
            end_time = time.time()
            self.result["execution_time"] = end_time - start_time
            
            if HAS_PSUTIL:
                self.result["memory_after"] = self._get_memory_usage()
        
        return self.result
    
    def setup(self):
        """测试前的准备"""
        pass
    
    def execute(self) -> bool:
        """执行测试
        
        Returns:
            bool: 测试是否通过
        """
        raise NotImplementedError("子类必须实现execute方法")
    
    def teardown(self):
        """测试后的清理"""
        pass
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """获取当前内存使用情况
        
        Returns:
            dict: 内存使用信息（MB）
        """
        result = {}
        
        if HAS_PSUTIL:
            try:
                # 获取当前进程
                process = psutil.Process(os.getpid())
                
                # 强制垃圾回收
                gc.collect()
                
                # 获取内存信息
                memory_info = process.memory_info()
                
                # 转换为MB
                result["rss"] = memory_info.rss / (1024 * 1024)  # 物理内存（MB）
                result["vms"] = memory_info.vms / (1024 * 1024)  # 虚拟内存（MB）
                
                # 获取系统内存信息
                system_memory = psutil.virtual_memory()
                result["system_used_percent"] = system_memory.percent
                result["system_available"] = system_memory.available / (1024 * 1024)  # MB
            except Exception as e:
                logger.error(f"获取内存使用信息时出错: {e}")
        
        return result

class MemoryUsageTest(TestCase):
    """内存使用测试"""
    
    def __init__(self, iterations: int = 10):
        """初始化内存使用测试
        
        Args:
            iterations: 迭代次数
        """
        super().__init__(
            "内存使用测试", 
            f"测试视频处理模块的内存使用稳定性，执行{iterations}次视频处理操作"
        )
        self.iterations = iterations
        self.app = None
    
    def setup(self):
        """测试前的准备"""
        # 创建Qt应用程序
        self.app = QApplication.instance() or QApplication([])
        
        if HAS_MEMORY_DETECTOR:
            # 启动内存监控
            detector = get_memory_leak_detector()
            detector.start_monitoring(interval=2)
    
    def execute(self) -> bool:
        """执行测试
        
        Returns:
            bool: 测试是否通过
        """
        # 创建临时视频文件
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_file.close()
        
        try:
            # 创建模拟的视频文件内容
            with open(temp_file.name, "wb") as f:
                f.write(b"X" * 1024 * 1024)  # 1MB的假视频数据
            
            # 创建视频处理器
            processor = VideoProcessor()
            
            # 处理内存使用记录
            memory_usages = []
            
            # 执行多次视频处理操作
            for i in range(self.iterations):
                logger.info(f"内存测试 - 迭代 {i+1}/{self.iterations}")
                
                # 处理视频（模拟）
                processor.process_video(temp_file.name, {"test": True})
                
                # 等待处理完成
                start_wait = time.time()
                while processor.is_processing and (time.time() - start_wait) < 30:
                    self.app.processEvents()
                    time.sleep(0.1)
                
                # 获取内存使用
                if HAS_PSUTIL:
                    memory_usage = self._get_memory_usage()
                    memory_usages.append(memory_usage["rss"])
                    logger.info(f"  内存使用: {memory_usage['rss']:.2f} MB")
            
            # 检查内存使用是否稳定（不持续增长）
            if memory_usages:
                # 计算内存增长率
                if len(memory_usages) >= 2:
                    first_half = memory_usages[:len(memory_usages)//2]
                    second_half = memory_usages[len(memory_usages)//2:]
                    
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    
                    # 增长率不应超过10%
                    growth_rate = (second_avg - first_avg) / first_avg * 100 if first_avg > 0 else 0
                    
                    logger.info(f"内存增长率: {growth_rate:.2f}%")
                    self.result["details"]["memory_growth_rate"] = growth_rate
                    self.result["details"]["memory_usages"] = memory_usages
                    
                    # 如果增长率超过10%，认为测试失败
                    if growth_rate > 10:
                        logger.warning("内存使用不稳定，可能存在泄漏")
                        return False
            
            return True
            
        finally:
            # 删除临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"删除临时文件时出错: {e}")
    
    def teardown(self):
        """测试后的清理"""
        if HAS_MEMORY_DETECTOR:
            # 生成内存报告
            detector = get_memory_leak_detector()
            detector.stop_monitoring()
            report = generate_report(detailed=False)
            
            # 保存报告
            with open("memory_report.txt", "w") as f:
                f.write(report)
            
            self.result["details"]["memory_report_file"] = "memory_report.txt"
        
        # 执行垃圾回收
        gc.collect()

class ThreadSafetyTest(TestCase):
    """线程安全测试"""
    
    def __init__(self, thread_count: int = 10):
        """初始化线程安全测试
        
        Args:
            thread_count: 线程数量
        """
        super().__init__(
            "线程安全测试", 
            f"测试线程管理器的安全性，创建并销毁{thread_count}个线程"
        )
        self.thread_count = thread_count
        self.app = None
        self.threads = []
    
    def setup(self):
        """测试前的准备"""
        # 创建Qt应用程序
        self.app = QApplication.instance() or QApplication([])
    
    def execute(self) -> bool:
        """执行测试
        
        Returns:
            bool: 测试是否通过
        """
        from ui.utils.thread_manager import SafeThread, get_thread_stats
        
        # 保存测试结果
        results = {
            "created_threads": 0,
            "terminated_threads": 0,
            "safely_finished_threads": 0,
            "errors": []
        }
        
        try:
            # 创建多个线程
            for i in range(self.thread_count):
                # 创建安全线程
                thread = SafeThread(name=f"TestThread-{i}")
                
                # 线程执行的操作
                def thread_operation(idx):
                    logger.info(f"线程 {idx} 开始执行")
                    # 模拟一些工作
                    time.sleep(0.5)
                    logger.info(f"线程 {idx} 执行完成")
                
                # 设置线程操作
                thread.run = lambda idx=i: thread_operation(idx)
                
                # 保存线程
                self.threads.append(thread)
                results["created_threads"] += 1
            
            # 启动所有线程
            for thread in self.threads:
                thread.start()
            
            # 等待一些线程正常结束
            time.sleep(2)
            
            # 终止一些线程（测试异常情况）
            for i, thread in enumerate(self.threads):
                if i % 3 == 0 and thread.isRunning():  # 每3个线程强制终止1个
                    logger.info(f"强制终止线程 {i}")
                    thread.terminate()
                    results["terminated_threads"] += 1
            
            # 等待所有线程完成
            start_wait = time.time()
            while any(thread.isRunning() for thread in self.threads) and (time.time() - start_wait) < 10:
                self.app.processEvents()
                time.sleep(0.1)
            
            # 计算安全完成的线程
            for i, thread in enumerate(self.threads):
                if not thread.isRunning():
                    if i % 3 != 0:  # 不是被强制终止的线程
                        results["safely_finished_threads"] += 1
            
            # 获取线程统计
            thread_stats = get_thread_stats()
            results["thread_stats"] = thread_stats
            
            logger.info(f"线程测试结果: 创建={results['created_threads']}, "
                        f"终止={results['terminated_threads']}, "
                        f"安全完成={results['safely_finished_threads']}")
            
            # 检查是否有活动线程残留（除了主线程和监控线程）
            active_count = thread_stats["active_threads"]
            
            # 允许有少量后台监控线程存在
            if active_count > 3:
                logger.warning(f"仍有{active_count}个线程活动，可能存在线程泄漏")
                results["errors"].append(f"检测到{active_count}个活动线程")
                
                # 将错误添加到测试结果
                self.result["details"].update(results)
                return False
            
            # 将结果添加到测试结果
            self.result["details"].update(results)
            return True
            
        except Exception as e:
            logger.exception(f"线程安全测试异常: {e}")
            results["errors"].append(str(e))
            self.result["details"].update(results)
            return False
    
    def teardown(self):
        """测试后的清理"""
        # 确保所有线程都已结束
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
        
        # 调用全局清理
        from ui.utils.thread_manager import cleanup_all_threads
        cleanup_all_threads()
        
        # 执行垃圾回收
        gc.collect()

class LargeFileTest(TestCase):
    """大文件处理测试"""
    
    def __init__(self, file_size_mb: int = 100):
        """初始化大文件处理测试
        
        Args:
            file_size_mb: 测试文件大小（MB）
        """
        super().__init__(
            "大文件处理测试", 
            f"测试处理{file_size_mb}MB的大视频文件"
        )
        self.file_size_mb = file_size_mb
        self.app = None
    
    def setup(self):
        """测试前的准备"""
        # 创建Qt应用程序
        self.app = QApplication.instance() or QApplication([])
    
    def execute(self) -> bool:
        """执行测试
        
        Returns:
            bool: 测试是否通过
        """
        # 创建临时大文件
        logger.info(f"创建{self.file_size_mb}MB的测试文件...")
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_file.close()
        
        try:
            # 创建指定大小的文件
            with open(temp_file.name, "wb") as f:
                # 每次写入1MB，重复指定次数
                for _ in range(self.file_size_mb):
                    f.write(b"X" * 1024 * 1024)
            
            logger.info(f"大文件创建完成: {os.path.getsize(temp_file.name) / (1024*1024):.1f} MB")
            
            # 创建视频处理器
            processor = VideoProcessor()
            
            # 设置处理选项（标记为大文件）
            options = {
                "large_file": True,
                "test": True
            }
            
            # 处理视频
            logger.info("开始处理大文件...")
            success = processor.process_video(temp_file.name, options)
            
            if not success:
                logger.error("启动视频处理失败")
                return False
            
            # 等待处理完成或超时
            start_wait = time.time()
            timeout = 30  # 30秒超时
            
            while processor.is_processing and (time.time() - start_wait) < timeout:
                self.app.processEvents()
                time.sleep(0.1)
            
            # 检查是否超时
            if processor.is_processing:
                logger.error(f"处理大文件超时（>{timeout}秒）")
                processor.cancel_processing()
                return False
            
            logger.info(f"大文件处理完成，用时: {time.time() - start_wait:.1f}秒")
            
            # 如果成功处理完成，测试通过
            return True
            
        except Exception as e:
            logger.exception(f"大文件处理测试异常: {e}")
            return False
            
        finally:
            # 删除临时文件
            try:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except Exception as e:
                logger.error(f"删除临时文件时出错: {e}")
    
    def teardown(self):
        """测试后的清理"""
        # 执行垃圾回收
        gc.collect()

class ConcurrentProcessingTest(TestCase):
    """并发处理测试"""
    
    def __init__(self, task_count: int = 5):
        """初始化并发处理测试
        
        Args:
            task_count: 并发任务数
        """
        super().__init__(
            "并发处理测试", 
            f"测试同时处理{task_count}个视频文件"
        )
        self.task_count = task_count
        self.app = None
    
    def setup(self):
        """测试前的准备"""
        # 创建Qt应用程序
        self.app = QApplication.instance() or QApplication([])
    
    def execute(self) -> bool:
        """执行测试
        
        Returns:
            bool: 测试是否通过
        """
        # 创建临时文件
        temp_files = []
        for i in range(self.task_count):
            temp_file = tempfile.NamedTemporaryFile(suffix=f"_{i}.mp4", delete=False)
            temp_file.close()
            
            # 写入一些测试数据
            with open(temp_file.name, "wb") as f:
                f.write(b"X" * 1024 * 1024)  # 1MB
            
            temp_files.append(temp_file.name)
        
        try:
            # 创建视频管理器
            manager = VideoManager(max_concurrent_tasks=3)  # 最多同时处理3个任务
            
            # 添加监控变量
            completed_count = 0
            failed_count = 0
            
            # 添加回调
            def on_task_completed(task_id, result):
                nonlocal completed_count
                completed_count += 1
                logger.info(f"任务完成: {task_id}")
            
            def on_task_failed(task_id, error):
                nonlocal failed_count
                failed_count += 1
                logger.error(f"任务失败: {task_id}, 错误: {error}")
            
            # 连接信号
            manager.task_completed.connect(on_task_completed)
            manager.task_failed.connect(on_task_failed)
            
            # 添加所有任务
            for i, file_path in enumerate(temp_files):
                task_id = manager.add_task(file_path, {"test": True})
                if task_id:
                    logger.info(f"已添加任务 {i+1}/{len(temp_files)}: {task_id}")
                else:
                    logger.error(f"添加任务失败: {file_path}")
                    return False
            
            # 等待所有任务完成
            start_wait = time.time()
            timeout = 60  # 60秒超时
            
            while (completed_count + failed_count < self.task_count) and (time.time() - start_wait) < timeout:
                self.app.processEvents()
                time.sleep(0.1)
            
            # 检查结果
            total_processed = completed_count + failed_count
            logger.info(f"处理结果: 完成={completed_count}, 失败={failed_count}, 总计={total_processed}/{self.task_count}")
            
            # 记录详细结果
            self.result["details"]["completed_count"] = completed_count
            self.result["details"]["failed_count"] = failed_count
            self.result["details"]["total_tasks"] = self.task_count
            self.result["details"]["execution_time"] = time.time() - start_wait
            
            # 如果有任务失败或未完成所有任务，则测试失败
            if failed_count > 0 or total_processed < self.task_count:
                return False
            
            return True
            
        except Exception as e:
            logger.exception(f"并发处理测试异常: {e}")
            return False
            
        finally:
            # 删除临时文件
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    logger.error(f"删除临时文件时出错: {e}")
    
    def teardown(self):
        """测试后的清理"""
        # 执行垃圾回收
        gc.collect()

def run_tests(selected_tests=None):
    """运行所有测试
    
    Args:
        selected_tests: 选定的测试名称列表
    
    Returns:
        dict: 测试结果
    """
    # 创建测试用例
    test_cases = [
        MemoryUsageTest(iterations=15),
        ThreadSafetyTest(thread_count=20),
        LargeFileTest(file_size_mb=50),  # 50MB的测试文件
        ConcurrentProcessingTest(task_count=8)
    ]
    
    # 过滤测试用例
    if selected_tests:
        test_cases = [tc for tc in test_cases if tc.name in selected_tests]
    
    # 总结果
    results = {
        "total_tests": len(test_cases),
        "passed_tests": 0,
        "failed_tests": 0,
        "execution_time": 0,
        "tests": {}
    }
    
    # 记录开始时间
    total_start_time = time.time()
    
    # 运行测试
    for test_case in test_cases:
        # 运行测试
        test_result = test_case.run()
        
        # 更新总结果
        if test_result["passed"]:
            results["passed_tests"] += 1
        else:
            results["failed_tests"] += 1
        
        # 添加详细结果
        results["tests"][test_case.name] = test_result
    
    # 计算总执行时间
    results["execution_time"] = time.time() - total_start_time
    
    return results

def print_results(results):
    """打印测试结果
    
    Args:
        results: 测试结果
    """
    print("\n========== 测试结果 ==========")
    print(f"总测试数: {results['total_tests']}")
    print(f"通过测试: {results['passed_tests']}")
    print(f"失败测试: {results['failed_tests']}")
    print(f"总执行时间: {results['execution_time']:.2f} 秒")
    print("\n详细测试结果:")
    
    for name, result in results["tests"].items():
        status = "通过" if result["passed"] else "失败"
        print(f"  {name}: {status} ({result['execution_time']:.2f} 秒)")
    
    print("\n============================")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 性能测试脚本")
    parser.add_argument("--tests", nargs="+", help="要运行的测试（默认运行所有测试）")
    args = parser.parse_args()
    
    # 运行测试
    results = run_tests(args.tests)
    
    # 打印结果
    print_results(results)
    
    # 将结果写入文件
    with open("test_results_improved.txt", "w", encoding="utf-8") as f:
        f.write("VisionAI-ClipsMaster 性能测试结果（改进版）\n\n")
        f.write(f"总测试数: {results['total_tests']}\n")
        f.write(f"通过测试: {results['passed_tests']}\n")
        f.write(f"失败测试: {results['failed_tests']}\n")
        f.write(f"总执行时间: {results['execution_time']:.2f} 秒\n\n")
        
        f.write("详细测试结果:\n")
        for name, result in results["tests"].items():
            status = "通过" if result["passed"] else "失败"
            f.write(f"  {name}: {status} ({result['execution_time']:.2f} 秒)\n")
    
    # 返回退出码
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 