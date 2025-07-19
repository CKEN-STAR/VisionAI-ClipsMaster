#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 第二阶段优化集成修复
简化集成策略，确保优化模块正常工作
"""

import sys
import time
import traceback
from PyQt6.QtCore import QTimer

class OptimizationIntegrationFix:
    """优化集成修复器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.optimization_status = {
            "startup_optimizer": False,
            "response_monitor": False,
            "css_optimizer": False,
            "user_experience": False
        }
        
    def apply_safe_integration(self):
        """应用安全的集成策略"""
        print("[INFO] 开始应用第二阶段优化安全集成...")
        
        # 延迟执行优化集成，避免启动时冲突
        QTimer.singleShot(3000, self._delayed_integration)
        
    def _delayed_integration(self):
        """延迟集成优化模块"""
        try:
            print("[INFO] 执行延迟优化集成...")
            
            # 1. 集成启动优化器
            self._integrate_startup_optimizer()
            
            # 2. 集成响应监控增强
            self._integrate_response_monitor()
            
            # 3. 集成CSS优化器
            self._integrate_css_optimizer()
            
            # 4. 集成用户体验增强
            self._integrate_user_experience()
            
            # 报告集成状态
            self._report_integration_status()
            
        except Exception as e:
            print(f"[ERROR] 延迟优化集成失败: {e}")
            traceback.print_exc()
    
    def _integrate_startup_optimizer(self):
        """集成启动优化器"""
        try:
            from startup_optimizer import initialize_startup_optimizer
            
            # 初始化启动优化器
            self.main_window.startup_optimizer = initialize_startup_optimizer(self.main_window)
            self.optimization_status["startup_optimizer"] = True
            
            print("[OK] 启动优化器集成成功")
            
        except Exception as e:
            print(f"[WARN] 启动优化器集成失败: {e}")
    
    def _integrate_response_monitor(self):
        """集成响应监控增强"""
        try:
            from response_monitor_enhanced import (
                initialize_enhanced_response_monitor, start_response_monitoring
            )
            
            # 初始化响应监控器
            self.main_window.enhanced_response_monitor = initialize_enhanced_response_monitor(self.main_window)
            start_response_monitoring()
            self.optimization_status["response_monitor"] = True
            
            print("[OK] 响应监控增强集成成功")
            
        except Exception as e:
            print(f"[WARN] 响应监控增强集成失败: {e}")
    
    def _integrate_css_optimizer(self):
        """集成CSS优化器"""
        try:
            from css_optimizer import apply_optimized_styles
            
            # 应用优化样式
            apply_optimized_styles(self.main_window)
            self.optimization_status["css_optimizer"] = True
            
            print("[OK] CSS优化器集成成功")
            
        except Exception as e:
            print(f"[WARN] CSS优化器集成失败: {e}")
    
    def _integrate_user_experience(self):
        """集成用户体验增强"""
        try:
            from user_experience_enhancer import initialize_user_experience_enhancer
            
            # 初始化用户体验增强器
            initialize_user_experience_enhancer(self.main_window)
            self.optimization_status["user_experience"] = True
            
            print("[OK] 用户体验增强集成成功")
            
        except Exception as e:
            print(f"[WARN] 用户体验增强集成失败: {e}")
    
    def _report_integration_status(self):
        """报告集成状态"""
        success_count = sum(self.optimization_status.values())
        total_count = len(self.optimization_status)
        
        print(f"\n📊 第二阶段优化集成报告:")
        print(f"成功集成: {success_count}/{total_count} 个模块")
        
        for module_name, status in self.optimization_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {module_name}: {'成功' if status else '失败'}")
        
        if success_count >= total_count * 0.75:
            print("🎉 第二阶段优化集成基本成功！")
        else:
            print("⚠️ 第二阶段优化集成需要进一步调试")
        
        # 显示用户通知
        if hasattr(self.main_window, 'alert_manager') and self.main_window.alert_manager:
            if success_count >= total_count * 0.75:
                self.main_window.alert_manager.info(
                    f"第二阶段优化已激活 ({success_count}/{total_count})", 
                    timeout=5000
                )
            else:
                self.main_window.alert_manager.warning(
                    f"部分优化功能不可用 ({success_count}/{total_count})", 
                    timeout=5000
                )

def apply_optimization_fix(main_window):
    """应用优化修复的全局接口"""
    try:
        fix = OptimizationIntegrationFix(main_window)
        fix.apply_safe_integration()
        return fix
    except Exception as e:
        print(f"[ERROR] 应用优化修复失败: {e}")
        return None

# 简化的优化功能包装器
class OptimizedFeatures:
    """优化功能包装器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.features_available = False
        
    def enable_optimizations(self):
        """启用优化功能"""
        try:
            # 应用修复
            fix = apply_optimization_fix(self.main_window)
            if fix:
                self.features_available = True
                
                # 添加优化的标签页切换
                self._optimize_tab_switching()
                
                # 添加优化的内存管理
                self._optimize_memory_management()
                
                print("[OK] 优化功能已启用")
            else:
                print("[WARN] 优化功能启用失败")
                
        except Exception as e:
            print(f"[ERROR] 启用优化功能失败: {e}")
    
    def _optimize_tab_switching(self):
        """优化标签页切换"""
        try:
            # 保存原始的标签页切换方法
            if hasattr(self.main_window, 'on_tab_changed'):
                original_method = self.main_window.on_tab_changed
                
                def optimized_tab_changed(index):
                    """优化的标签页切换"""
                    start_time = time.time()
                    try:
                        # 执行原始方法
                        original_method(index)
                        
                        # 记录响应时间
                        elapsed = time.time() - start_time
                        if elapsed > 0.1:
                            print(f"[PERF] 标签页切换耗时: {elapsed:.3f}秒")
                        else:
                            print(f"[OK] 标签页切换响应时间: {elapsed:.3f}秒")
                            
                    except Exception as e:
                        print(f"[ERROR] 优化标签页切换失败: {e}")
                        # 回退到原始方法
                        original_method(index)
                
                # 替换方法
                self.main_window.on_tab_changed = optimized_tab_changed
                print("[OK] 标签页切换优化已应用")
                
        except Exception as e:
            print(f"[WARN] 标签页切换优化失败: {e}")
    
    def _optimize_memory_management(self):
        """优化内存管理"""
        try:
            # 定期清理内存
            def memory_cleanup():
                try:
                    import gc
                    gc.collect()
                    print("[OK] 内存清理完成")
                except Exception as e:
                    print(f"[WARN] 内存清理失败: {e}")
            
            # 每30秒执行一次内存清理
            cleanup_timer = QTimer()
            cleanup_timer.timeout.connect(memory_cleanup)
            cleanup_timer.start(30000)  # 30秒
            
            self.main_window.memory_cleanup_timer = cleanup_timer
            print("[OK] 内存管理优化已应用")
            
        except Exception as e:
            print(f"[WARN] 内存管理优化失败: {e}")

# 全局优化应用函数
def apply_second_stage_optimizations(main_window):
    """应用第二阶段优化的主入口"""
    try:
        print("[INFO] 开始应用第二阶段优化...")
        
        # 创建优化功能实例
        optimized_features = OptimizedFeatures(main_window)
        
        # 启用优化
        optimized_features.enable_optimizations()
        
        # 保存到主窗口
        main_window.optimized_features = optimized_features
        
        print("[OK] 第二阶段优化应用完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 第二阶段优化应用失败: {e}")
        traceback.print_exc()
        return False
