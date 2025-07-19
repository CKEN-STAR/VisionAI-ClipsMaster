"""
内存集成模块 - 整合内存压力生成器和内存防护器
提供统一的内存监控、测试和动态模型管理接口
"""

import time
import threading
import logging
import os
from typing import Dict, Callable, Any, Optional, List, Tuple
from pathlib import Path

# 导入内存组件
from src.utils.memory_guard import get_memory_guard, MemoryGuard, QuantizationManager
from src.utils.memory_pressure import MemoryPressurer

# 配置日志
logger = logging.getLogger("MemoryIntegration")

class MemoryManager:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """
    统一内存管理器 - 集成内存压力测试和模型内存优化
    
    功能:
    1. 内存压力测试与模型加载集成
    2. 动态内存压力响应
    3. 自适应模型量化调整
    4. 内存使用情况数据收集与分析
    """
    
    def __init__(self, env_profile_name: str = None):
        """
        初始化内存管理器
        
        Args:
            env_profile_name: 环境配置名称，如果指定则加载对应的环境配置
        """
        # 获取内存防护器单例
        self.memory_guard = get_memory_guard()
        
        # 创建内存压力生成器
        self.memory_pressurer = MemoryPressurer(
            safety_margin_mb=400,  # 较小的安全边际，更接近极限
            monitor_interval=0.5,   # 更频繁的监控
            threshold_critical=0.9,  # 90%内存使用触发危险
            threshold_warning=0.75   # 75%内存使用触发警告
        )
        
        # 创建量化管理器
        self.quant_manager = QuantizationManager(self.memory_guard)
        
        # 统计与监控数据
        self.memory_stats = []  # 内存使用历史
        self.model_load_times = {}  # 模型加载时间记录
        
        # 集成监控线程
        self.monitor_thread = None
        self.running = False
        
        # 系统状态
        self.is_under_pressure = False
        self.current_pressure_type = None
        
        # 环境配置
        self.env_profile = None
        if env_profile_name:
            self.load_environment_profile(env_profile_name)
        
    def load_environment_profile(self, profile_name: str) -> bool:
        """
        加载特定的环境配置
        
        Args:
            profile_name: 环境配置名称
            
        Returns:
            bool: 是否成功加载
        """
        try:
            # 导入环境模拟器
            from src.utils.env_simulator import EnvironmentSimulator
            
            # 创建环境模拟器
            simulator = EnvironmentSimulator()
            
            # 获取配置
            profile = simulator.get_profile(profile_name)
            if not profile:
                logger.error(f"未找到环境配置: {profile_name}")
                return False
                
            # 保存配置
            self.env_profile = profile
            
            # 调整内存压力生成器参数以适应环境
            total_mem_mb = profile.get('total_mem', 4096)
            
            # 根据环境调整安全边际和阈值
            if total_mem_mb <= 2048:  # 2GB或更少
                safety_margin_mb = 200  # 更小的安全边际
                threshold_critical = 0.85  # 更高的临界点
                threshold_warning = 0.7
            elif total_mem_mb <= 3072:  # 3GB
                safety_margin_mb = 300
                threshold_critical = 0.88
                threshold_warning = 0.72
            else:  # 4GB或更多
                safety_margin_mb = 400
                threshold_critical = 0.9
                threshold_warning = 0.75
                
            # 更新内存压力生成器参数
            self.memory_pressurer.safety_margin_mb = safety_margin_mb
            self.memory_pressurer.threshold_critical = threshold_critical
            self.memory_pressurer.threshold_warning = threshold_warning
            
            logger.info(f"已加载环境配置: {profile_name}, "
                      f"内存: {total_mem_mb}MB, "
                      f"安全边际: {safety_margin_mb}MB")
            
            return True
                
        except ImportError:
            logger.error("无法导入环境模拟器，请确保env_simulator.py文件存在")
            return False
        except Exception as e:
            logger.error(f"加载环境配置时出错: {str(e)}")
            return False
    
    def start_monitoring(self, collect_stats: bool = True):
        """
        启动统一内存监控
        
        Args:
            collect_stats: 是否收集内存统计数据
        """
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.running = True
            
            # 注册回调函数
            self.memory_pressurer.start_memory_monitor(
                callback_warning=self._handle_memory_warning,
                callback_critical=self._handle_memory_critical
            )
            
            # 启动内存防护器
            self.memory_guard.start_monitoring()
            
            # 启动统计收集
            if collect_stats:
                self.monitor_thread = threading.Thread(
                    target=self._collect_memory_stats,
                    daemon=True,
                    name="MemoryStatsCollector"
                )
                self.monitor_thread.start()
            
            logger.info("统一内存监控已启动")
            
    def stop_monitoring(self):
        """停止所有监控"""
        self.running = False
        
        # 停止内存压力监控
        self.memory_pressurer.stop_memory_monitor()
        
        # 停止内存防护器
        self.memory_guard.stop_monitoring()
        
        # 停止统计线程
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
            
        logger.info("统一内存监控已停止")
        
    def _collect_memory_stats(self):
        """收集内存使用统计数据"""
        while self.running:
            try:
                # 获取当前内存状态
                mem_info = self.memory_guard.get_memory_status()
                
                # 记录当前时间点的内存数据
                self.memory_stats.append({
                    "timestamp": time.time(),
                    "memory_usage": mem_info["memory_usage"],
                    "available_gb": mem_info["available_memory"],
                    "loaded_models": len(mem_info["loaded_models"]),
                    "under_pressure": self.is_under_pressure,
                    "pressure_type": self.current_pressure_type
                })
                
                # 保留最近100个数据点
                if len(self.memory_stats) > 100:
                    self.memory_stats = self.memory_stats[-100:]
                    
                time.sleep(5)  # 每5秒收集一次
                
            except Exception as e:
                logger.error(f"收集内存统计数据时出错: {str(e)}")
                time.sleep(1)
    
    def _handle_memory_warning(self, mem_info: Dict):
        """
        处理内存警告
        
        Args:
            mem_info: 内存状态信息
        """
        logger.warning(f"内存警告: 使用率{mem_info['percent_used']*100:.1f}%, "
                      f"可用{mem_info['available_gb']:.2f}GB")
        
        # 标记系统状态
        self.is_under_pressure = True
        self.current_pressure_type = "warning"
        
        # 尝试预防性释放一些资源
        current_quant = self.quant_manager.get_optimal_quantization()
        logger.info(f"建议当前使用的量化等级: {current_quant}")
        
        # 触发内存防护器的推荐清理
        self.memory_guard._recommended_cleanup()
        
    def _handle_memory_critical(self, mem_info: Dict):
        """
        处理内存危急情况
        
        Args:
            mem_info: 内存状态信息
        """
        logger.error(f"内存危急: 使用率{mem_info['percent_used']*100:.1f}%, "
                    f"可用{mem_info['available_gb']:.2f}GB")
        
        # 标记系统状态
        self.is_under_pressure = True
        self.current_pressure_type = "critical"
        
        # 获取紧急情况下的量化等级
        emergency_quant = self.quant_manager.quantization_levels["emergency"]
        logger.warning(f"紧急情况建议量化等级: {emergency_quant}")
        
        # 触发内存防护器的紧急清理
        self.memory_guard._emergency_cleanup()
    
    def run_controlled_pressure_test(self, 
                                    test_mode: str, 
                                    model_id: str = None,
                                    test_duration: int = 60,
                                    env_profile_name: str = None,
                                    **kwargs):
        """
        在模型加载的同时运行受控内存压力测试
        
        Args:
            test_mode: 压力测试模式
            model_id: 要加载的模型ID
            test_duration: 测试持续时间(秒)
            env_profile_name: 环境配置名称，如果指定则使用该环境
            **kwargs: 传递给压力测试的参数
        
        Returns:
            Dict: 测试结果
        """
        # 如果指定了环境配置，则加载该配置
        if env_profile_name and not self.env_profile:
            self.load_environment_profile(env_profile_name)
            
        # 记录环境信息    
        env_info = {}
        if self.env_profile:
            env_info = {
                "profile_name": self.env_profile.get("name", "unknown"),
                "total_mem_mb": self.env_profile.get("total_mem", 0),
                "swap_size_mb": self.env_profile.get("swap_size", 0)
            }
        
        logger.info(f"开始受控内存压力测试: 模式={test_mode}, 模型={model_id}, "
                   f"环境={env_info.get('profile_name', 'default')}")
        
        # 开始收集内存统计
        start_stats = self.get_current_memory_info()
        stats_history = []
        
        # 启动监控
        self.start_monitoring()
        
        test_thread = None
        model_obj = None
        load_time = 0
        
        try:
            # 如果指定了模型，则尝试加载
            if model_id:
                start_load = time.time()
                logger.info(f"尝试在压力下加载模型: {model_id}")
                
                # 获取适合当前内存情况的量化等级
                quant_level = self.quant_manager.get_optimal_quantization()
                logger.info(f"选择量化等级: {quant_level}")
                
                # 模拟模型加载(实际项目中这里应该调用真正的模型加载函数)
                # model_obj = load_model(model_id, quantization=quant_level)
                # 这里只是占位，实际项目中需要替换为真正的模型加载代码
                
                load_time = time.time() - start_load
                self.model_load_times[model_id] = load_time
                logger.info(f"模型加载完成，耗时: {load_time:.2f}秒")
            
            # 在单独线程中运行压力测试，避免阻塞主逻辑
            test_thread = threading.Thread(
                target=self._run_pressure_test_thread,
                args=(test_mode, kwargs)
            )
            test_thread.start()
            
            # 模拟测试持续时间
            start_time = time.time()
            while time.time() - start_time < test_duration and test_thread.is_alive():
                # 收集内存状态
                mem_info = self.get_current_memory_info()
                stats_history.append(mem_info)
                
                # 每秒检查一次
                time.sleep(1)
                
        finally:
            # 等待压力测试线程完成
            if test_thread and test_thread.is_alive():
                test_thread.join(timeout=10)
                
            # 清理内存
            self.memory_pressurer.release_all()
            if model_obj:
                # 实际项目中应该卸载模型
                # self.memory_guard.unload_model(model_id)
                pass
                
            # 停止监控
            self.stop_monitoring()
            
        # 收集最终状态
        end_stats = self.get_current_memory_info()
        
        # 生成测试报告
        report = {
            "test_mode": test_mode,
            "model_id": model_id,
            "duration": test_duration,
            "start_memory": start_stats,
            "end_memory": end_stats,
            "peak_memory": max(stats_history, key=lambda x: x["memory_percent"])["memory_percent"],
            "model_load_time": load_time,
            "memory_statistics": self._calculate_memory_statistics(stats_history),
            "environment": env_info
        }
        
        logger.info(f"内存压力测试完成: 峰值内存使用率={report['peak_memory']:.1f}%")
        return report
    
    def _run_pressure_test_thread(self, test_mode: str, kwargs: Dict):
        """在单独线程中运行压力测试"""
        try:
            if test_mode == "staircase":
                self.memory_pressurer.staircase_pressure(**kwargs)
            elif test_mode == "burst":
                self.memory_pressurer.burst_pressure(**kwargs)
            elif test_mode == "sawtooth":
                self.memory_pressurer.sawtooth_pressure(**kwargs)
            else:
                logger.error(f"未知的压力测试模式: {test_mode}")
        except Exception as e:
            logger.error(f"压力测试线程异常: {str(e)}")
    
    def _calculate_memory_statistics(self, stats_history: List[Dict]) -> Dict:
        """计算内存统计指标"""
        if not stats_history:
            return {}
            
        memory_percents = [s["memory_percent"] for s in stats_history]
        available_gbs = [s["available_gb"] for s in stats_history]
        
        return {
            "avg_memory_percent": sum(memory_percents) / len(memory_percents),
            "min_memory_percent": min(memory_percents),
            "max_memory_percent": max(memory_percents),
            "avg_available_gb": sum(available_gbs) / len(available_gbs),
            "min_available_gb": min(available_gbs),
            "volatility": self._calculate_volatility(memory_percents)
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """计算内存使用的波动性"""
        if len(values) <= 1:
            return 0.0
            
        changes = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        return sum(changes) / (len(changes))
    
    def get_current_memory_info(self) -> Dict:
        """获取当前内存状态信息"""
        mem_info = self.memory_guard.get_memory_status()
        return {
            "timestamp": time.time(),
            "memory_percent": mem_info["memory_usage"] * 100,  # 转为百分比
            "available_gb": mem_info["available_memory"],
            "total_gb": mem_info["total_memory"],
            "loaded_models": len(mem_info["loaded_models"]),
            "under_pressure": self.is_under_pressure,
            "pressure_type": self.current_pressure_type
        }
    
    def generate_memory_report(self) -> Dict:
        """生成详细的内存报告"""
        current = self.get_current_memory_info()
        
        if self.memory_stats:
            # 计算内存变化趋势
            trend = "stable"  # 默认稳定
            recent = self.memory_stats[-10:]  # 最近10个数据点
            
            if len(recent) > 5:
                # 计算最近数据点的平均内存使用率
                recent_avg = sum(s["memory_usage"] for s in recent) / len(recent)
                # 计算更早数据点的平均内存使用率
                earlier_avg = sum(s["memory_usage"] for s in self.memory_stats[:-10]) / max(1, len(self.memory_stats[:-10]))
                
                # 判断趋势
                if recent_avg > earlier_avg * 1.1:  # 增长超过10%
                    trend = "increasing"
                elif recent_avg < earlier_avg * 0.9:  # 减少超过10%
                    trend = "decreasing"
        else:
            trend = "unknown"  # 没有足够的历史数据
        
        # 模型加载性能
        model_performance = {}
        for model_id, load_time in self.model_load_times.items():
            model_performance[model_id] = {
                "load_time_sec": load_time,
                "rating": "good" if load_time < 3.0 else ("moderate" if load_time < 10.0 else "slow")
            }
        
        # 添加环境信息
        env_info = {}
        if self.env_profile:
            env_info = {
                "profile_name": self.env_profile.get("name", "未指定"),
                "total_mem_mb": self.env_profile.get("total_mem", 0),
                "swap_size_mb": self.env_profile.get("swap_size", 0),
                "memory_limit": self.env_profile.get("cgroups", {}).get("memory.limit_in_bytes", "未指定")
            }
        
        return {
            "current": current,
            "trend": trend,
            "model_performance": model_performance,
            "recommendation": self._generate_recommendation(current),
            "quantization": {
                "current_optimal": self.quant_manager.get_optimal_quantization(),
                "quality_impact": self._estimate_quality_impact()
            },
            "environment": env_info
        }
    
    def _generate_recommendation(self, current: Dict) -> str:
        """根据当前内存状态生成优化建议"""
        if current["memory_percent"] > 90:
            return "紧急：建议立即释放资源，关闭不必要的应用程序，降低量化级别至Q2_K"
        elif current["memory_percent"] > 75:
            return "警告：建议使用Q3_K_M量化级别，关闭部分后台任务"
        elif current["memory_percent"] > 60:
            return "注意：内存使用适中，建议使用Q4_K_M量化级别"
        else:
            return "良好：内存充足，可以使用Q5_K_M或更高量化级别获得更好质量"
    
    def _estimate_quality_impact(self) -> Dict:
        """估计不同量化级别的质量影响"""
        # 从量化管理器获取各级别质量估计
        quality_estimates = self.quant_manager.quality_estimates
        
        # 根据当前内存状态选择建议量化级别
        current_quant = self.quant_manager.get_optimal_quantization()
        
        # 计算质量提升空间
        max_quality = max(quality_estimates.values())
        current_quality = quality_estimates.get(current_quant, 80)  # 默认80
        quality_headroom = max_quality - current_quality
        
        return {
            "current_level": current_quant,
            "current_quality_score": current_quality,
            "potential_improvement": quality_headroom,
            "memory_constrained": self.is_under_pressure
        }


# 单例模式
_memory_manager_instance = None

def get_memory_manager(env_profile_name: str = None) -> MemoryManager:
    """
    获取内存管理器单例
    
    Args:
        env_profile_name: 环境配置名称，如果指定则加载对应的环境配置
    
    Returns:
        内存管理器实例
    """
    global _memory_manager_instance
    
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(env_profile_name)
    elif env_profile_name:
        # 如果已存在实例但指定了新的环境配置，则加载该配置
        _memory_manager_instance.load_environment_profile(env_profile_name)
        
    return _memory_manager_instance


# 简单测试函数
def run_test(env_profile_name: str = None):
    """
    运行内存管理器测试
    
    Args:
        env_profile_name: 可选的环境配置名称
    """
    mm = get_memory_manager(env_profile_name)
    
    print("=== 内存管理器测试 ===")
    
    # 如果指定了环境配置，则显示环境信息
    if env_profile_name:
        print(f"使用环境配置: {env_profile_name}")
        if mm.env_profile:
            print(f"  内存: {mm.env_profile.get('total_mem')}MB")
            print(f"  交换: {mm.env_profile.get('swap_size')}MB")
    
    print("1. 获取当前内存状态")
    current = mm.get_current_memory_info()
    print(f"  内存使用率: {current['memory_percent']:.1f}%")
    print(f"  可用内存: {current['available_gb']:.2f}GB")
    
    print("\n2. 运行阶梯式压力测试...")
    report = mm.run_controlled_pressure_test(
        test_mode="staircase",
        step_size_mb=200,
        step_interval_sec=1.0,
        max_steps=10,
        test_duration=15
    )
    
    print(f"  测试完成: 峰值内存 {report['peak_memory']:.1f}%")
    
    print("\n3. 生成内存报告")
    full_report = mm.generate_memory_report()
    print(f"  内存趋势: {full_report['trend']}")
    print(f"  建议: {full_report['recommendation']}")
    print(f"  最佳量化级别: {full_report['quantization']['current_optimal']}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    import sys
    
    # 检查是否指定了环境配置
    env_name = None
    if len(sys.argv) > 1:
        env_name = sys.argv[1]
        
    run_test(env_name) 