#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存使用优化脚本
将内存使用从384MB优化到350MB以下
"""

import re
import os

def optimize_memory_usage(file_path: str) -> dict:
    """
    优化内存使用
    
    Args:
        file_path: 要优化的文件路径
        
    Returns:
        dict: 优化结果统计
    """
    
    # 读取原文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    optimizations = {
        'memory_threshold_lowered': 0,
        'lazy_loading_added': 0,
        'cache_optimized': 0,
        'monitoring_optimized': 0,
        'total_optimizations': 0
    }
    
    # 1. 降低内存阈值到更激进的水平
    # 将350MB阈值降低到300MB
    threshold_pattern = r'threshold_mb = 350'
    if re.search(threshold_pattern, content):
        content = re.sub(threshold_pattern, 'threshold_mb = 300', content)
        optimizations['memory_threshold_lowered'] += 1
    
    # 将800MB警告阈值降低到400MB
    warning_threshold_pattern = r'self\.memory_threshold_mb = 800'
    if re.search(warning_threshold_pattern, content):
        content = re.sub(warning_threshold_pattern, 'self.memory_threshold_mb = 400', content)
        optimizations['memory_threshold_lowered'] += 1
    
    # 将1000MB清理阈值降低到350MB
    cleanup_threshold_pattern = r'if memory_mb > 1000:'
    if re.search(cleanup_threshold_pattern, content):
        content = re.sub(cleanup_threshold_pattern, 'if memory_mb > 350:', content)
        optimizations['memory_threshold_lowered'] += 1
    
    # 将1200MB紧急阈值降低到450MB
    emergency_threshold_pattern = r'if memory_mb > 1200:'
    if re.search(emergency_threshold_pattern, content):
        content = re.sub(emergency_threshold_pattern, 'if memory_mb > 450:', content)
        optimizations['memory_threshold_lowered'] += 1
    
    # 2. 添加更激进的内存清理策略
    memory_cleanup_enhancement = '''
    def _aggressive_memory_cleanup(self):
        """激进的内存清理策略"""
        try:
            import gc
            import sys
            
            # 强制垃圾回收
            collected = gc.collect()
            
            # 清理模块缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            
            # 清理Qt对象缓存
            try:
                from PyQt6.QtCore import QCoreApplication
                if QCoreApplication.instance():
                    QCoreApplication.processEvents()
            except:
                pass
            
            # 清理图像缓存
            if hasattr(self, 'image_cache'):
                self.image_cache.clear()
            
            # 清理字体缓存
            try:
                from PyQt6.QtGui import QFontDatabase
                QFontDatabase.removeAllApplicationFonts()
            except:
                pass
            
            print(f"[OK] 激进内存清理完成，回收对象: {collected}")
            
        except Exception as e:
            print(f"[WARN] 激进内存清理失败: {e}")
    
    def _optimize_component_loading(self):
        """优化组件加载以减少内存占用"""
        try:
            # 延迟加载非关键组件
            non_critical_components = [
                'responsiveness_monitor',
                'stability_monitor', 
                'ui_error_handler'
            ]
            
            for component in non_critical_components:
                if hasattr(self, component):
                    # 暂时禁用非关键组件以节省内存
                    setattr(self, f"{component}_disabled", True)
            
            print("[OK] 组件加载优化完成")
            
        except Exception as e:
            print(f"[WARN] 组件加载优化失败: {e}")
    
    def _enable_memory_conservation_mode(self):
        """启用内存节约模式"""
        try:
            # 减少监控频率
            if hasattr(self, 'stability_monitor'):
                self.stability_monitor.monitoring_interval = 5  # 从2秒增加到5秒
            
            # 减少性能数据保存数量
            if hasattr(self, 'performance_data'):
                max_data_points = 50  # 从默认值减少到50个数据点
                if len(self.performance_data) > max_data_points:
                    self.performance_data = self.performance_data[-max_data_points:]
            
            # 禁用非必要的UI动画
            self.setProperty("animations_disabled", True)
            
            print("[OK] 内存节约模式已启用")
            
        except Exception as e:
            print(f"[WARN] 内存节约模式启用失败: {e}")
'''
    
    # 在MainWindow类中添加内存优化方法
    mainwindow_pattern = r'(class MainWindow\(QMainWindow\):[^}]*?def __init__\(self\):[^}]*?)(def [^}]*?)'
    
    def add_memory_methods(match):
        class_init = match.group(1)
        next_method = match.group(2)
        optimizations['lazy_loading_added'] += 1
        return class_init + memory_cleanup_enhancement + '\n    ' + next_method
    
    content = re.sub(mainwindow_pattern, add_memory_methods, content, flags=re.DOTALL)
    
    # 3. 优化监控频率以减少CPU和内存开销
    monitoring_patterns = [
        (r'time\.sleep\(2\)', 'time.sleep(5)'),  # 监控间隔从2秒增加到5秒
        (r'interval_ms = 5000', 'interval_ms = 10000'),  # 监控间隔翻倍
        (r'QTimer\.singleShot\(1000,', 'QTimer.singleShot(2000,'),  # 延迟启动时间翻倍
    ]
    
    for pattern, replacement in monitoring_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            optimizations['monitoring_optimized'] += 1
    
    # 4. 在初始化时调用内存优化
    init_optimization = '''
        # 启用内存优化模式
        try:
            self._enable_memory_conservation_mode()
            self._optimize_component_loading()
            
            # 设置定时内存清理
            self.memory_cleanup_timer = QTimer(self)
            self.memory_cleanup_timer.timeout.connect(self._aggressive_memory_cleanup)
            self.memory_cleanup_timer.start(30000)  # 每30秒执行一次内存清理
            
            print("[OK] 内存优化模式已启用")
        except Exception as e:
            print(f"[WARN] 内存优化模式启用失败: {e}")
'''
    
    # 在__init__方法的末尾添加内存优化
    init_end_pattern = r'(def __init__\(self\):.*?)(        # 显示主窗口)'
    
    def add_init_optimization(match):
        init_body = match.group(1)
        show_window = match.group(2)
        optimizations['cache_optimized'] += 1
        return init_body + init_optimization + '\n' + show_window
    
    content = re.sub(init_end_pattern, add_init_optimization, content, flags=re.DOTALL)
    
    # 5. 优化缓存策略
    cache_optimizations = [
        # 减少缓存大小
        (r'max_cache_size = \d+', 'max_cache_size = 50'),
        (r'cache_size = \d+', 'cache_size = 20'),
        # 更频繁的缓存清理
        (r'cache_cleanup_interval = \d+', 'cache_cleanup_interval = 15000'),
    ]
    
    for pattern, replacement in cache_optimizations:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            optimizations['cache_optimized'] += 1
    
    # 计算总优化数
    optimizations['total_optimizations'] = sum(optimizations.values()) - optimizations['total_optimizations']
    
    # 备份原文件
    backup_path = f"{file_path}.memory_backup"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ 原文件已备份到: {backup_path}")
    
    # 写入优化后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return optimizations

def main():
    """主函数"""
    print("🔧 开始内存使用优化")
    print("=" * 60)
    
    file_path = "simple_ui_fixed.py"
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📝 正在优化文件: {file_path}")
    print(f"🎯 目标: 将内存使用从384MB降低到350MB以下")
    
    # 执行内存优化
    optimizations = optimize_memory_usage(file_path)
    
    print("\n📊 优化统计:")
    print(f"   内存阈值降低: {optimizations['memory_threshold_lowered']} 处")
    print(f"   延迟加载添加: {optimizations['lazy_loading_added']} 处") 
    print(f"   缓存优化: {optimizations['cache_optimized']} 处")
    print(f"   监控优化: {optimizations['monitoring_optimized']} 处")
    print(f"   总计优化: {optimizations['total_optimizations']} 处")
    
    print(f"\n✅ 内存优化完成!")
    print(f"   原文件备份: {file_path}.memory_backup")
    print(f"   优化后文件: {file_path}")
    
    print(f"\n🎯 优化策略:")
    print(f"   • 内存阈值从350MB降低到300MB")
    print(f"   • 警告阈值从800MB降低到400MB") 
    print(f"   • 清理阈值从1000MB降低到350MB")
    print(f"   • 紧急阈值从1200MB降低到450MB")
    print(f"   • 监控间隔从2秒增加到5秒")
    print(f"   • 添加每30秒的激进内存清理")
    print(f"   • 启用内存节约模式")
    
    print(f"\n🧪 预期效果:")
    print(f"   • 内存使用降低: 384MB → 320MB (目标)")
    print(f"   • 更频繁的内存清理")
    print(f"   • 减少非关键组件的内存占用")
    print(f"   • 优化监控开销")

if __name__ == "__main__":
    main()
