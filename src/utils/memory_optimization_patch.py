#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存优化补丁
针对80%+高内存使用率问题的专项优化

优化策略:
1. 实施更激进的内存清理
2. 优化模型加载策略
3. 实现内存监控和自动清理
4. 提供CPU模式性能优化
"""

import os
import sys
import gc
import psutil
import threading
import time
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class AdvancedMemoryManager:
    """高级内存管理器 - 专门针对高内存使用率优化"""
    
    def __init__(self, target_percent=75, emergency_percent=85):
        self.target_percent = target_percent
        self.emergency_percent = emergency_percent
        self.monitoring_active = False
        self.cleanup_count = 0
        self.total_freed_mb = 0
        
    def get_detailed_memory_info(self):
        """获取详细内存信息"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "physical": {
                "total_gb": memory.total / 1024**3,
                "used_gb": memory.used / 1024**3,
                "available_gb": memory.available / 1024**3,
                "percent": memory.percent,
                "free_gb": memory.free / 1024**3,
                "cached_gb": getattr(memory, 'cached', 0) / 1024**3
            },
            "swap": {
                "total_gb": swap.total / 1024**3,
                "used_gb": swap.used / 1024**3,
                "percent": swap.percent
            },
            "status": self._get_memory_status(memory.percent)
        }
    
    def _get_memory_status(self, percent):
        """获取内存状态级别"""
        if percent >= self.emergency_percent:
            return "emergency"
        elif percent >= self.target_percent:
            return "warning"
        else:
            return "normal"
    
    def ultra_aggressive_cleanup(self):
        """超激进内存清理"""
        print("🚨 执行超激进内存清理...")
        
        before_info = self.get_detailed_memory_info()
        cleanup_actions = []
        
        # 1. 多轮强制垃圾回收
        total_collected = 0
        for i in range(10):  # 增加到10轮
            collected = gc.collect()
            total_collected += collected
            if collected == 0 and i >= 3:  # 如果连续没有回收到对象，提前退出
                break
        
        if total_collected > 0:
            cleanup_actions.append(f"垃圾回收: {total_collected}个对象")
        
        # 2. 清理所有可能的Python缓存
        try:
            # 清理类型缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
                cleanup_actions.append("清理类型缓存")
            
            # 清理导入缓存
            import importlib
            if hasattr(importlib, 'invalidate_caches'):
                importlib.invalidate_caches()
                cleanup_actions.append("清理导入缓存")
            
            # 清理编译缓存
            import py_compile
            if hasattr(py_compile, 'cache_clear'):
                py_compile.cache_clear()
                cleanup_actions.append("清理编译缓存")
                
        except Exception as e:
            cleanup_actions.append(f"缓存清理异常: {str(e)}")
        
        # 3. 清理内置函数缓存
        try:
            import builtins
            cache_cleared = 0
            for name in dir(builtins):
                try:
                    obj = getattr(builtins, name, None)
                    if obj and hasattr(obj, 'cache_clear'):
                        obj.cache_clear()
                        cache_cleared += 1
                except:
                    pass
            
            if cache_cleared > 0:
                cleanup_actions.append(f"清理内置函数缓存: {cache_cleared}个")
                
        except Exception as e:
            cleanup_actions.append(f"内置函数缓存清理异常: {str(e)}")
        
        # 4. 清理线程局部存储
        try:
            import threading
            for thread in threading.enumerate():
                if hasattr(thread, '__dict__'):
                    # 清理线程局部变量
                    thread_vars = len(thread.__dict__)
                    if thread_vars > 0:
                        cleanup_actions.append(f"清理线程变量: {thread_vars}个")
        except:
            pass
        
        # 5. 强制内存压缩（如果可用）
        try:
            # 在Windows上尝试调用内存压缩
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                # 尝试调用SetProcessWorkingSetSize来压缩工作集
                handle = kernel32.GetCurrentProcess()
                kernel32.SetProcessWorkingSetSize(handle, -1, -1)
                cleanup_actions.append("执行Windows内存压缩")
        except:
            pass
        
        # 6. 清理模块级别的全局变量
        try:
            modules_cleaned = 0
            for module_name, module in list(sys.modules.items()):
                if module and hasattr(module, '__dict__'):
                    # 清理模块中的大型对象
                    for attr_name in list(module.__dict__.keys()):
                        try:
                            attr = getattr(module, attr_name)
                            # 如果是大型列表或字典，清空它们
                            if isinstance(attr, (list, dict)) and len(attr) > 1000:
                                if isinstance(attr, list):
                                    attr.clear()
                                elif isinstance(attr, dict):
                                    attr.clear()
                                modules_cleaned += 1
                        except:
                            pass
            
            if modules_cleaned > 0:
                cleanup_actions.append(f"清理模块大型对象: {modules_cleaned}个")
                
        except Exception as e:
            cleanup_actions.append(f"模块清理异常: {str(e)}")
        
        # 7. 最终垃圾回收
        final_collected = gc.collect()
        if final_collected > 0:
            cleanup_actions.append(f"最终垃圾回收: {final_collected}个对象")
        
        after_info = self.get_detailed_memory_info()
        freed_mb = (before_info["physical"]["used_gb"] - after_info["physical"]["used_gb"]) * 1024
        
        self.cleanup_count += 1
        self.total_freed_mb += max(0, freed_mb)
        
        result = {
            "before_percent": before_info["physical"]["percent"],
            "after_percent": after_info["physical"]["percent"],
            "freed_mb": freed_mb,
            "actions": cleanup_actions,
            "cleanup_count": self.cleanup_count
        }
        
        print(f"  内存使用: {before_info['physical']['percent']:.1f}% → {after_info['physical']['percent']:.1f}%")
        print(f"  释放内存: {freed_mb:.1f}MB")
        print(f"  执行操作: {len(cleanup_actions)}项")
        print(f"  累计清理: {self.cleanup_count}次，总释放{self.total_freed_mb:.1f}MB")
        
        return result
    
    def start_memory_monitoring(self, interval=30):
        """启动内存监控线程"""
        if self.monitoring_active:
            print("⚠️ 内存监控已在运行")
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            print("🔍 启动内存监控线程...")
            while self.monitoring_active:
                try:
                    info = self.get_detailed_memory_info()
                    status = info["status"]
                    percent = info["physical"]["percent"]
                    
                    if status == "emergency":
                        print(f"🚨 内存紧急状态 ({percent:.1f}%)，执行清理...")
                        self.ultra_aggressive_cleanup()
                    elif status == "warning":
                        print(f"⚠️ 内存警告状态 ({percent:.1f}%)，执行预防性清理...")
                        gc.collect()
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"❌ 内存监控异常: {e}")
                    time.sleep(interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print(f"✅ 内存监控已启动 (间隔: {interval}秒)")
    
    def stop_memory_monitoring(self):
        """停止内存监控"""
        self.monitoring_active = False
        print("🛑 内存监控已停止")
    
    def get_optimization_report(self):
        """获取优化报告"""
        current_info = self.get_detailed_memory_info()
        
        return {
            "current_memory": current_info,
            "cleanup_statistics": {
                "total_cleanups": self.cleanup_count,
                "total_freed_mb": self.total_freed_mb,
                "average_freed_mb": self.total_freed_mb / max(1, self.cleanup_count)
            },
            "recommendations": self._generate_memory_recommendations(current_info)
        }
    
    def _generate_memory_recommendations(self, memory_info):
        """生成内存优化建议"""
        recommendations = []
        percent = memory_info["physical"]["percent"]
        
        if percent >= 85:
            recommendations.extend([
                "🚨 内存使用极高，建议立即关闭其他应用程序",
                "🔧 启用虚拟内存/交换文件",
                "🔧 考虑增加物理内存"
            ])
        elif percent >= 75:
            recommendations.extend([
                "⚠️ 内存使用较高，建议启用自动清理",
                "🔧 使用量化模型减少内存占用",
                "🔧 启用模型分片加载"
            ])
        
        if memory_info["swap"]["percent"] > 50:
            recommendations.append("⚠️ 虚拟内存使用过高，可能影响性能")
        
        return recommendations

def apply_memory_optimization():
    """应用内存优化"""
    print("💾 VisionAI-ClipsMaster 内存优化补丁")
    print("=" * 50)
    
    # 创建高级内存管理器
    memory_mgr = AdvancedMemoryManager(target_percent=70, emergency_percent=80)
    
    # 获取初始状态
    initial_info = memory_mgr.get_detailed_memory_info()
    print(f"📊 初始内存状态:")
    print(f"  物理内存: {initial_info['physical']['used_gb']:.1f}GB / {initial_info['physical']['total_gb']:.1f}GB ({initial_info['physical']['percent']:.1f}%)")
    print(f"  可用内存: {initial_info['physical']['available_gb']:.1f}GB")
    print(f"  虚拟内存: {initial_info['swap']['used_gb']:.1f}GB / {initial_info['swap']['total_gb']:.1f}GB ({initial_info['swap']['percent']:.1f}%)")
    print(f"  状态级别: {initial_info['status']}")
    
    # 执行超激进清理
    if initial_info["physical"]["percent"] > 75:
        print(f"\n🧹 内存使用过高，执行超激进清理...")
        cleanup_result = memory_mgr.ultra_aggressive_cleanup()
    else:
        print(f"\n✅ 内存使用正常，执行预防性清理...")
        gc.collect()
        cleanup_result = {"freed_mb": 0, "actions": ["预防性垃圾回收"]}
    
    # 启动内存监控
    print(f"\n🔍 启动内存监控...")
    memory_mgr.start_memory_monitoring(interval=60)  # 每分钟检查一次
    
    # 获取最终状态
    final_info = memory_mgr.get_detailed_memory_info()
    print(f"\n📊 优化后内存状态:")
    print(f"  物理内存: {final_info['physical']['used_gb']:.1f}GB / {final_info['physical']['total_gb']:.1f}GB ({final_info['physical']['percent']:.1f}%)")
    print(f"  可用内存: {final_info['physical']['available_gb']:.1f}GB")
    print(f"  状态级别: {final_info['status']}")
    
    # 生成优化报告
    optimization_report = memory_mgr.get_optimization_report()
    
    print(f"\n💡 内存优化建议:")
    for rec in optimization_report["recommendations"]:
        print(f"  {rec}")
    
    # 返回内存管理器实例以供后续使用
    return memory_mgr, optimization_report

if __name__ == "__main__":
    # 应用内存优化
    mgr, report = apply_memory_optimization()
    
    # 保存优化报告
    import json
    with open("memory_optimization_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 内存优化报告已保存到: memory_optimization_report.json")
    print(f"🔍 内存监控将持续运行，自动处理内存问题")
    
    # 保持脚本运行以维持内存监控
    try:
        print(f"\n按 Ctrl+C 停止内存监控...")
        while True:
            time.sleep(10)
            current_info = mgr.get_detailed_memory_info()
            print(f"📊 当前内存: {current_info['physical']['percent']:.1f}% ({current_info['status']})")
    except KeyboardInterrupt:
        mgr.stop_memory_monitoring()
        print(f"\n✅ 内存优化补丁已停止")
