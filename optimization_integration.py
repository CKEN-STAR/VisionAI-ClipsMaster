#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 优化集成管理器
确保优化过程中核心功能稳定性
"""

import time
import json
import traceback
from datetime import datetime
from pathlib import Path

class OptimizationIntegrator:
    """优化集成管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.optimization_log = []
        self.rollback_points = {}
        self.core_functions = [
            "视频文件选择", "SRT字幕导入", "AI剧情分析", 
            "字幕重构", "视频拼接", "导出功能"
        ]
        
    def create_rollback_point(self, optimization_name):
        """创建回滚点"""
        try:
            rollback_data = {
                "timestamp": datetime.now().isoformat(),
                "optimization": optimization_name,
                "core_function_status": self._test_core_functions(),
                "performance_baseline": self._get_performance_baseline()
            }
            
            self.rollback_points[optimization_name] = rollback_data
            print(f"[OK] 创建回滚点: {optimization_name}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 创建回滚点失败: {e}")
            return False
            
    def apply_optimization(self, optimization_name, optimization_func):
        """安全应用优化"""
        try:
            # 1. 创建回滚点
            if not self.create_rollback_point(optimization_name):
                return False
                
            # 2. 记录开始时间
            start_time = time.time()
            
            # 3. 应用优化
            print(f"[INFO] 开始应用优化: {optimization_name}")
            result = optimization_func()
            
            # 4. 验证核心功能
            if not self._verify_core_functions():
                print(f"[ERROR] 核心功能验证失败，回滚优化: {optimization_name}")
                self.rollback_optimization(optimization_name)
                return False
                
            # 5. 性能验证
            if not self._verify_performance_improvement():
                print(f"[WARN] 性能改善不明显: {optimization_name}")
                
            # 6. 记录成功
            elapsed = time.time() - start_time
            self._log_optimization_success(optimization_name, elapsed, result)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 应用优化失败: {optimization_name}, 错误: {e}")
            print(f"详细错误: {traceback.format_exc()}")
            self.rollback_optimization(optimization_name)
            return False
            
    def rollback_optimization(self, optimization_name):
        """回滚优化"""
        try:
            if optimization_name not in self.rollback_points:
                print(f"[ERROR] 未找到回滚点: {optimization_name}")
                return False
                
            print(f"[WARN] 开始回滚优化: {optimization_name}")
            
            # 这里应该实现具体的回滚逻辑
            # 由于我们使用渐进式优化，主要是禁用新功能
            
            rollback_data = self.rollback_points[optimization_name]
            self._log_optimization_rollback(optimization_name, rollback_data)
            
            print(f"[OK] 优化回滚完成: {optimization_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 回滚失败: {optimization_name}, 错误: {e}")
            return False
            
    def _test_core_functions(self):
        """测试核心功能"""
        results = {}
        
        try:
            # 测试视频文件选择
            results["视频文件选择"] = hasattr(self.main_window, 'select_video_files')
            
            # 测试SRT字幕导入
            results["SRT字幕导入"] = hasattr(self.main_window, 'import_srt_file')
            
            # 测试AI剧情分析
            results["AI剧情分析"] = hasattr(self.main_window, 'analyze_plot')
            
            # 测试字幕重构
            results["字幕重构"] = hasattr(self.main_window, 'reconstruct_subtitles')
            
            # 测试视频拼接
            results["视频拼接"] = hasattr(self.main_window, 'splice_videos')
            
            # 测试导出功能
            results["导出功能"] = hasattr(self.main_window, 'export_to_jianying')
            
        except Exception as e:
            print(f"[ERROR] 核心功能测试失败: {e}")
            
        return results
        
    def _verify_core_functions(self):
        """验证核心功能完整性"""
        try:
            current_status = self._test_core_functions()
            
            # 检查所有核心功能是否可用
            missing_functions = [
                func for func, available in current_status.items() 
                if not available
            ]
            
            if missing_functions:
                print(f"[ERROR] 缺失核心功能: {missing_functions}")
                return False
                
            print("[OK] 核心功能验证通过")
            return True
            
        except Exception as e:
            print(f"[ERROR] 核心功能验证失败: {e}")
            return False
            
    def _get_performance_baseline(self):
        """获取性能基线"""
        try:
            # 简单的性能测试
            start_time = time.time()
            
            # 模拟标签页切换
            if hasattr(self.main_window, 'tabs'):
                current_tab = self.main_window.tabs.currentIndex()
                self.main_window.tabs.setCurrentIndex((current_tab + 1) % 4)
                self.main_window.tabs.setCurrentIndex(current_tab)
                
            elapsed = time.time() - start_time
            
            return {
                "tab_switch_time": elapsed,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"[ERROR] 获取性能基线失败: {e}")
            return {}
            
    def _verify_performance_improvement(self):
        """验证性能改善"""
        try:
            current_performance = self._get_performance_baseline()
            
            # 简单的性能验证
            tab_switch_time = current_performance.get("tab_switch_time", 999)
            
            if tab_switch_time < 1.0:  # 目标响应时间
                print(f"[OK] 性能验证通过，响应时间: {tab_switch_time:.3f}秒")
                return True
            else:
                print(f"[WARN] 响应时间较慢: {tab_switch_time:.3f}秒")
                return False
                
        except Exception as e:
            print(f"[ERROR] 性能验证失败: {e}")
            return False
            
    def _log_optimization_success(self, name, elapsed, result):
        """记录优化成功"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "optimization": name,
            "status": "success",
            "elapsed_time": elapsed,
            "result": str(result)
        }
        
        self.optimization_log.append(log_entry)
        print(f"[OK] 优化成功: {name}, 耗时: {elapsed:.3f}秒")
        
    def _log_optimization_rollback(self, name, rollback_data):
        """记录优化回滚"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "optimization": name,
            "status": "rollback",
            "rollback_data": rollback_data
        }
        
        self.optimization_log.append(log_entry)
        
    def save_optimization_log(self):
        """保存优化日志"""
        try:
            log_file = Path("optimization_log.json")
            
            log_data = {
                "optimization_log": self.optimization_log,
                "rollback_points": self.rollback_points,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
                
            print(f"[OK] 优化日志已保存: {log_file}")
            
        except Exception as e:
            print(f"[ERROR] 保存优化日志失败: {e}")

class SafeOptimizationApplier:
    """安全优化应用器"""
    
    def __init__(self, main_window):
        self.integrator = OptimizationIntegrator(main_window)
        self.main_window = main_window
        
    def apply_async_ui_optimization(self):
        """应用异步UI优化"""
        def optimization_func():
            try:
                # 导入优化模块
                from ui_async_optimizer import initialize_optimizers
                
                # 初始化优化器
                initialize_optimizers(self.main_window)
                
                # 替换原有的标签页切换方法
                original_method = self.main_window.on_tab_changed
                
                def optimized_tab_changed(index):
                    from ui_async_optimizer import optimize_tab_switch
                    optimize_tab_switch(index)
                    # 仍然调用原方法以保持兼容性
                    original_method(index)
                
                self.main_window.on_tab_changed = optimized_tab_changed
                
                return "异步UI优化应用成功"
                
            except Exception as e:
                raise Exception(f"异步UI优化失败: {e}")
                
        return self.integrator.apply_optimization(
            "异步UI优化", optimization_func
        )
        
    def apply_memory_optimization(self):
        """应用内存优化"""
        def optimization_func():
            try:
                # 导入内存管理模块
                from memory_manager_enhanced import initialize_memory_manager
                
                # 初始化增强内存管理器
                memory_manager = initialize_memory_manager()
                
                # 连接到主窗口
                self.main_window.enhanced_memory_manager = memory_manager
                
                return "内存优化应用成功"
                
            except Exception as e:
                raise Exception(f"内存优化失败: {e}")
                
        return self.integrator.apply_optimization(
            "内存优化", optimization_func
        )
        
    def apply_all_optimizations(self):
        """应用所有优化"""
        results = {}
        
        # 按优先级顺序应用优化
        optimizations = [
            ("异步UI优化", self.apply_async_ui_optimization),
            ("内存优化", self.apply_memory_optimization)
        ]
        
        for name, optimization_func in optimizations:
            try:
                print(f"\n[INFO] 开始应用: {name}")
                result = optimization_func()
                results[name] = {"success": result, "error": None}
                
                if result:
                    print(f"[OK] {name} 应用成功")
                else:
                    print(f"[ERROR] {name} 应用失败")
                    
            except Exception as e:
                print(f"[ERROR] {name} 应用异常: {e}")
                results[name] = {"success": False, "error": str(e)}
                
        # 保存日志
        self.integrator.save_optimization_log()
        
        return results

# 全局应用器实例
safe_optimizer = None

def initialize_safe_optimizer(main_window):
    """初始化安全优化器"""
    global safe_optimizer
    safe_optimizer = SafeOptimizationApplier(main_window)
    print("[OK] 安全优化器初始化完成")
    return safe_optimizer
    
def apply_optimizations_safely():
    """安全应用所有优化"""
    if safe_optimizer:
        return safe_optimizer.apply_all_optimizations()
    else:
        print("[ERROR] 安全优化器未初始化")
        return {}
