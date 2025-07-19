#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存压力检测系统演示
展示实时压力检测、趋势分析和熔断系统的功能
"""

import os
import time
import logging
import argparse
import numpy as np
import threading
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入压力检测系统
from src.fuse.pressure_detector import get_pressure_detector
from src.fuse.integration import get_integration_manager
from src.fuse.visualization import get_pressure_visualizer
from src.memory.fuse_manager import FuseLevel, get_fuse_manager


def simulate_memory_pressure(duration: int = 120, pattern: str = 'sine'):
    """
    模拟内存压力变化
    
    Args:
        duration: 模拟时长（秒）
        pattern: 压力模式，可选 'sine'（正弦波）, 'ramp'（递增）, 'spike'（尖峰）
    """
    print(f"开始模拟内存压力变化，模式: {pattern}，持续时间: {duration}秒")
    
    # 创建模拟线程
    stop_event = threading.Event()
    
    def simulate_thread():
        start_time = time.time()
        base_usage = 50.0  # 基础内存使用率
        
        try:
            while not stop_event.is_set() and time.time() - start_time < duration:
                elapsed = time.time() - start_time
                
                # 根据不同模式计算模拟压力值
                if pattern == 'sine':
                    # 正弦波模式，周期为60秒，振幅为30%
                    pressure = base_usage + 30 * np.sin(elapsed * np.pi / 30)
                elif pattern == 'ramp':
                    # 递增模式，从50%逐渐增加到95%
                    pressure = base_usage + (45 * elapsed / duration)
                elif pattern == 'spike':
                    # 尖峰模式，每30秒出现一次尖峰
                    cycle_time = elapsed % 30
                    if cycle_time < 5:
                        # 5秒内快速上升到高峰
                        pressure = base_usage + (40 * cycle_time / 5)
                    elif cycle_time < 10:
                        # 5秒内快速下降
                        pressure = base_usage + 40 - (40 * (cycle_time - 5) / 5)
                    else:
                        # 保持基础水平
                        pressure = base_usage
                else:
                    pressure = base_usage
                
                # 确保压力值在合理范围内
                pressure = max(min(pressure, 99), 10)
                
                # 注入模拟的内存压力值（直接修改压力检测器的样本）
                detector = get_pressure_detector()
                with detector._lock:
                    if detector.samples:
                        detector.samples[-1] = pressure
                        # 每5个样本，有50%概率触发快速上升的情况
                        if int(elapsed) % 5 == 0 and np.random.random() < 0.5 and pattern == 'spike':
                            # 创建一个快速上升的样本序列，使其能够触发is_escalating
                            for i in range(5):
                                if len(detector.samples) > i:
                                    detector.samples[-i-1] = pressure - (i * 2.5)
                
                # 更新间隔
                time.sleep(0.2)
                
        except Exception as e:
            print(f"模拟线程异常: {str(e)}")
    
    # 启动模拟线程
    sim_thread = threading.Thread(target=simulate_thread, daemon=True)
    sim_thread.start()
    
    try:
        # 等待指定时间
        sim_thread.join(timeout=duration)
    except KeyboardInterrupt:
        print("模拟被用户中断")
    finally:
        stop_event.set()
        if sim_thread.is_alive():
            sim_thread.join(timeout=2)
    
    print("内存压力模拟已完成")


def run_demo(args):
    """
    运行内存压力检测演示
    
    Args:
        args: 命令行参数
    """
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化系统
    integration = get_integration_manager()
    detector = get_pressure_detector()
    fuse_manager = get_fuse_manager()
    visualizer = get_pressure_visualizer()
    
    # 设置压力阈值
    integration.set_pressure_threshold(FuseLevel.WARNING, 75.0)
    integration.set_pressure_threshold(FuseLevel.CRITICAL, 85.0)
    integration.set_pressure_threshold(FuseLevel.EMERGENCY, 95.0)
    
    # 启用预测
    integration.enable_prediction(args.prediction)
    integration.set_prediction_window(30)
    
    # 注册回调函数
    def pressure_callback(pressure):
        print(f"当前内存压力指数: {pressure:.1f}")
    
    def warning_callback(pressure):
        print(f"⚠️ 警告: 内存压力达到警告级别 ({pressure:.1f})")
    
    def critical_callback(pressure):
        print(f"🔥 警告: 内存压力达到临界级别 ({pressure:.1f})")
    
    def emergency_callback(pressure):
        print(f"🚨 警告: 内存压力达到紧急级别 ({pressure:.1f})")
    
    def escalation_callback(pressure):
        print(f"📈 警告: 内存压力快速上升 ({pressure:.1f})")
    
    # 注册回调
    detector.set_callback(pressure_callback)
    detector.register_pressure_callback(75.0, warning_callback)
    detector.register_pressure_callback(85.0, critical_callback)
    detector.register_pressure_callback(95.0, emergency_callback)
    detector.register_escalation_callback(escalation_callback)
    
    # 初始化系统
    print("正在初始化内存压力检测系统...")
    integration.initialize()
    
    # 启动系统
    print("启动内存压力检测系统...")
    integration.start()
    
    # 启动模拟
    if args.simulate:
        simulate_memory_pressure(args.duration, args.pattern)
    
    # 如果需要可视化
    if args.visualize:
        if args.web:
            # 启动Web服务器
            print(f"启动内存压力监控Web服务器，访问 http://localhost:{args.port}/")
            try:
                visualizer.start_web_server(port=args.port)
            except KeyboardInterrupt:
                print("Web服务器已停止")
        else:
            # 简单的图形生成
            print("生成内存压力图表...")
            for _ in range(min(60, args.duration)):
                # 更新数据
                visualizer.update_data()
                time.sleep(1)
            
            # 保存图表
            output_file = "memory_pressure.png"
            visualizer.save_image(output_file, dark_mode=True)
            print(f"内存压力图表已保存到: {output_file}")
    else:
        # 如果不可视化，则简单等待
        try:
            print("内存压力检测系统运行中, 按Ctrl+C停止...")
            time.sleep(args.duration)
        except KeyboardInterrupt:
            print("用户中断")
    
    # 停止系统
    print("停止内存压力检测系统...")
    integration.stop()
    
    print("演示结束")


def demonstrate_safe_executor():
    """展示安全熔断执行器的使用"""
    from .safe_executor import (
        register_action, 
        register_resource, 
        safe_execute, 
        release_resource,
        force_gc
    )
    import time
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 模拟一个大对象
    large_data = [0] * (10 * 1024 * 1024)  # 约80MB的列表
    
    # 注册一个资源
    def release_large_data(data):
        print(f"释放大型数据对象，原大小: {len(data)}")
        data.clear()
        
    register_resource("large_data", large_data, release_large_data)
    
    # 注册一个自定义操作
    def process_data(data_id, iterations=10):
        print(f"处理数据 {data_id}, 迭代 {iterations} 次")
        for i in range(iterations):
            time.sleep(0.1)  # 模拟处理时间
            print(f"迭代 {i+1}/{iterations}")
        return {"status": "完成", "processed_items": iterations}
        
    register_action("process_data", process_data)
    
    # 执行操作
    print("安全执行自定义操作...")
    result = safe_execute("process_data", data_id="large_data", iterations=5)
    print(f"操作结果: {result}")
    
    # 强制GC
    print("执行强制垃圾回收...")
    force_gc()
    
    # 释放资源
    print("释放指定资源...")
    release_resource("large_data")
    
    print("安全熔断执行器演示完成")


def demonstrate_recovery_system():
    """展示熔断状态恢复系统的使用"""
    from .recovery_manager import (
        get_recovery_manager, 
        register_resource_state,
        register_recovery_handler,
        save_system_state,
        restore_system_state,
        ResourceState
    )
    from .safe_executor import register_resource, release_resource
    import time
    import logging
    import random
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 模拟资源数据
    class VideoResource:
        def __init__(self, file_path, duration):
            self.file_path = file_path
            self.duration = duration
        
        def get_info(self):
            return f"视频: {self.file_path}, 时长: {self.duration}秒"
            
    class ModelResource:
        def __init__(self, model_path, quantization):
            self.model_path = model_path
            self.quantization = quantization
            self.model_type = "subtitle_generator"
            
        def get_info(self):
            return f"模型: {self.model_path}, 量化: {self.quantization}"
    
    # 注册资源恢复处理器
    def restore_video(resource_state):
        """恢复视频资源的处理器"""
        metadata = resource_state.metadata
        return VideoResource(
            file_path=metadata.get("file_path", "unknown.mp4"),
            duration=metadata.get("duration", 0)
        )
        
    def restore_model(resource_state):
        """恢复模型资源的处理器"""
        metadata = resource_state.metadata
        return ModelResource(
            model_path=metadata.get("model_path", "unknown.bin"),
            quantization=metadata.get("quantization", "Q4_0")
        )
    
    # 注册恢复处理器
    recovery_manager = get_recovery_manager()
    recovery_manager.register_resource_handler("video", restore_video)
    recovery_manager.register_resource_handler("model", restore_model)
    
    # 创建并注册资源
    print("创建测试资源...")
    video = VideoResource("sample.mp4", 120)
    model = ModelResource("/models/qwen-7b.bin", "Q4_K_M")
    
    # 注册到执行器
    def release_video(res):
        print(f"释放视频资源: {res.file_path}")
        
    def release_model(res):
        print(f"释放模型资源: {res.model_path}")
    
    register_resource("video_main", video, release_video)
    register_resource("model_zh_main", model, release_model)
    
    # 注册资源状态以便恢复
    print("注册资源状态...")
    register_resource_state("video_main", "video", {
        "file_path": video.file_path,
        "duration": video.duration
    })
    
    register_resource_state("model_zh_main", "model", {
        "model_path": model.model_path,
        "quantization": model.quantization,
        "model_type": model.model_type
    })
    
    # 保存系统状态
    print("保存系统状态...")
    save_system_state()
    
    # 模拟熔断释放资源
    print("模拟熔断释放资源...")
    release_resource("video_main")
    release_resource("model_zh_main")
    
    # 等待一段时间
    time.sleep(1)
    
    # 恢复系统状态
    print("恢复系统状态...")
    result = restore_system_state()
    
    if result:
        print("系统状态恢复成功!")
        
        # 验证资源是否已恢复
        executor = get_executor()
        restored_resources = []
        
        with executor.action_lock:
            for res_id, res_data in executor.registered_resources.items():
                resource = res_data["resource"]
                if hasattr(resource, "get_info"):
                    info = resource.get_info()
                    restored_resources.append(f"{res_id}: {info}")
        
        if restored_resources:
            print("恢复的资源列表:")
            for res_info in restored_resources:
                print(f"  - {res_info}")
        else:
            print("未发现恢复的资源!")
    else:
        print("系统状态恢复失败!")
    
    print("熔断状态恢复系统演示完成")


def demonstrate_effect_validator():
    """展示熔断效果验证系统的使用"""
    from .effect_validator import (
        get_validator, 
        execute_with_validation,
        handle_failed_validation,
        FailureHandlingStrategy
    )
    from .safe_executor import register_action, safe_execute
    import time
    import logging
    import random
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 获取验证器实例
    validator = get_validator()
    
    # 启动内存监控
    validator.start_monitoring()
    
    # 创建模拟操作
    def clear_cache_action():
        """模拟清理缓存操作"""
        print("执行清理缓存操作...")
        # 模拟内存释放 - 创建并释放大对象
        big_list = [0] * (120 * 1024 * 1024 // 4)  # 约120MB的列表
        big_list.clear()
        return True
    
    def force_gc_action():
        """模拟强制GC操作"""
        print("执行强制GC操作...")
        import gc

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        gc.collect()
        return True
    
    def failed_action():
        """模拟一个失败的操作，不释放足够内存"""
        print("执行一个会失败的操作...")
        time.sleep(0.1)  # 只是消耗时间，不释放内存
        return True
    
    # 注册操作
    register_action("clear_cache", clear_cache_action)
    register_action("force_gc", force_gc_action)
    register_action("failed_action", failed_action)
    
    # 执行并验证操作
    print("\n1. 执行并验证成功操作")
    result, success = execute_with_validation("clear_cache")
    print(f"操作结果: {result}, 验证成功: {success}")
    
    # 获取最新的验证结果
    history = validator.get_validation_history(1)
    if history:
        result_dict = history[0].to_dict()
        print("验证详情:")
        for key, value in result_dict.items():
            print(f"  {key}: {value}")
    
    # 执行一个会失败的操作
    print("\n2. 执行并验证一个会失败的操作")
    result, success = execute_with_validation("failed_action")
    print(f"操作结果: {result}, 验证成功: {success}")
    
    # 如果验证失败，尝试进行失败处理
    if not success:
        history = validator.get_validation_history(1)
        if history:
            failed_result = history[0]
            
            print("\n3. 处理验证失败 - 使用RETRY策略")
            retry_success = handle_failed_validation(
                "failed_action", 
                failed_result, 
                FailureHandlingStrategy.RETRY
            )
            print(f"重试处理结果: {retry_success}")
            
            print("\n4. 处理验证失败 - 使用ESCALATE策略")
            # 模拟策略升级
            escalate_success = handle_failed_validation(
                "failed_action", 
                failed_result, 
                FailureHandlingStrategy.ESCALATE
            )
            print(f"升级处理结果: {escalate_success}")
            
            print("\n5. 处理验证失败 - 使用FALLBACK策略")
            # 使用备选方案
            fallback_success = handle_failed_validation(
                "failed_action", 
                failed_result, 
                FailureHandlingStrategy.FALLBACK,
                fallback_actions=["clear_cache", "force_gc"]
            )
            print(f"备选方案处理结果: {fallback_success}")
    
    # 获取操作有效性数据
    effectiveness = validator.get_action_effectiveness()
    print("\n操作有效性数据:")
    for action, score in effectiveness.items():
        print(f"  {action}: {score:.2f}")
    
    # 停止监控
    validator.stop_monitoring()
    
    print("\n熔断效果验证系统演示完成")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 内存压力检测系统演示")
    parser.add_argument("--simulate", action="store_true", help="模拟内存压力")
    parser.add_argument("--pattern", choices=["sine", "ramp", "spike"], default="sine", help="压力模式: sine(正弦波), ramp(递增), spike(尖峰)")
    parser.add_argument("--duration", type=int, default=120, help="持续时间(秒)")
    parser.add_argument("--prediction", action="store_true", help="启用压力预测")
    parser.add_argument("--visualize", action="store_true", help="可视化压力图表")
    parser.add_argument("--web", action="store_true", help="启动Web服务器实时展示")
    parser.add_argument("--port", type=int, default=8080, help="Web服务器端口")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    
    args = parser.parse_args()
    
    # 如果没有提供simulate或visualize参数，默认启用两者
    if not (args.simulate or args.visualize):
        args.simulate = True
        args.visualize = True
    
    run_demo(args)
    demonstrate_safe_executor()
    demonstrate_recovery_system()
    demonstrate_effect_validator() 