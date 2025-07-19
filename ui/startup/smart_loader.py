"""
智能模块预加载器
基于用户使用习惯和系统性能智能预加载模块
"""

import os
import json
import time
import threading
import importlib
from typing import Dict, List, Set, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    priority: int  # 1-10, 10为最高优先级
    load_time: float  # 预估加载时间
    dependencies: List[str]  # 依赖模块
    usage_count: int = 0  # 使用次数
    last_used: float = 0  # 最后使用时间
    load_success: bool = True  # 是否加载成功

class SmartModuleLoader:
    """智能模块加载器"""
    
    def __init__(self, config_file: str = "config/module_usage.json"):
        self.config_file = config_file
        self.modules: Dict[str, ModuleInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.loading_threads: Dict[str, threading.Thread] = {}
        self.load_callbacks: Dict[str, List[Callable]] = {}
        
        # 预定义核心模块
        self.define_core_modules()
        
        # 加载使用统计
        self.load_usage_stats()
    
    def define_core_modules(self):
        """定义核心模块"""
        core_modules = [
            # 最高优先级 - 启动必需
            ModuleInfo("PyQt6.QtWidgets", 10, 0.5, []),
            ModuleInfo("PyQt6.QtCore", 10, 0.3, []),
            ModuleInfo("PyQt6.QtGui", 9, 0.2, ["PyQt6.QtCore"]),
            
            # 高优先级 - UI核心
            ModuleInfo("ui.fixes.integrated_fix", 9, 0.3, []),
            ModuleInfo("ui.config.environment", 8, 0.2, []),
            ModuleInfo("ui.compat", 8, 0.1, []),
            ModuleInfo("src.ui.enhanced_style_manager", 8, 0.4, []),
            
            # 中高优先级 - 常用功能
            ModuleInfo("ui.utils.enhanced_css_processor", 7, 0.2, []),
            ModuleInfo("ui.utils.unified_css_manager", 7, 0.2, []),
            ModuleInfo("ui.hardware.performance_tier", 7, 0.3, []),
            ModuleInfo("ui.responsive.simple_ui_adapter", 7, 0.2, []),
            
            # 中优先级 - 功能模块
            ModuleInfo("ui.components.alert_manager", 6, 0.2, []),
            ModuleInfo("ui.feedback.error_visualizer", 6, 0.2, []),
            ModuleInfo("ui.monitor.system_monitor_app", 6, 0.3, []),
            ModuleInfo("ui.progress.tracker", 6, 0.2, []),
            
            # 中低优先级 - 优化功能
            ModuleInfo("ui.hardware.memory_manager", 5, 0.3, []),
            ModuleInfo("ui.hardware.disk_cache", 5, 0.2, []),
            ModuleInfo("ui.performance.memory_guard", 5, 0.2, []),
            ModuleInfo("ui.optimize.panel_perf", 5, 0.3, []),
            
            # 低优先级 - 高级功能
            ModuleInfo("ui.hardware.render_optimizer", 4, 0.3, []),
            ModuleInfo("ui.hardware.input_latency", 4, 0.2, []),
            ModuleInfo("ui.hardware.power_manager", 4, 0.2, []),
            ModuleInfo("ui.utils.hotkey_manager", 4, 0.2, []),
            
            # 最低优先级 - 可选功能
            ModuleInfo("ui.hardware.compute_offloader", 3, 0.4, []),
            ModuleInfo("ui.hardware.enterprise_deploy", 3, 0.3, []),
            ModuleInfo("ui.utils.text_direction", 3, 0.1, []),
        ]
        
        for module in core_modules:
            self.modules[module.name] = module
    
    def load_usage_stats(self):
        """加载使用统计"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                
                for module_name, data in stats.items():
                    if module_name in self.modules:
                        self.modules[module_name].usage_count = data.get('usage_count', 0)
                        self.modules[module_name].last_used = data.get('last_used', 0)
                        
                print(f"[OK] 加载模块使用统计: {len(stats)} 个模块")
        except Exception as e:
            print(f"[WARN] 加载使用统计失败: {e}")
    
    def save_usage_stats(self):
        """保存使用统计"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            stats = {}
            for module_name, module_info in self.modules.items():
                stats[module_name] = {
                    'usage_count': module_info.usage_count,
                    'last_used': module_info.last_used,
                    'load_success': module_info.load_success
                }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
                
            print(f"[OK] 保存模块使用统计: {len(stats)} 个模块")
        except Exception as e:
            print(f"[WARN] 保存使用统计失败: {e}")
    
    def get_load_priority(self, module_name: str) -> float:
        """计算模块加载优先级"""
        if module_name not in self.modules:
            return 0
        
        module = self.modules[module_name]
        
        # 基础优先级
        base_priority = module.priority
        
        # 使用频率加权 (最近使用的模块优先级更高)
        current_time = time.time()
        time_weight = 0
        if module.last_used > 0:
            days_since_used = (current_time - module.last_used) / (24 * 3600)
            time_weight = max(0, 2 - days_since_used * 0.1)  # 最多加2分
        
        # 使用次数加权
        usage_weight = min(2, module.usage_count * 0.1)  # 最多加2分
        
        # 加载成功率加权
        success_weight = 1 if module.load_success else -5
        
        total_priority = base_priority + time_weight + usage_weight + success_weight
        return max(0, total_priority)
    
    def get_sorted_modules(self) -> List[str]:
        """获取按优先级排序的模块列表"""
        module_priorities = []
        for module_name in self.modules:
            priority = self.get_load_priority(module_name)
            module_priorities.append((module_name, priority))
        
        # 按优先级降序排序
        module_priorities.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in module_priorities]
    
    def load_module_async(self, module_name: str, callback: Optional[Callable] = None):
        """异步加载模块"""
        if module_name in self.loaded_modules:
            if callback:
                callback(module_name, self.loaded_modules[module_name], True)
            return
        
        if module_name in self.loading_threads:
            # 模块正在加载，添加回调
            if callback:
                if module_name not in self.load_callbacks:
                    self.load_callbacks[module_name] = []
                self.load_callbacks[module_name].append(callback)
            return
        
        def load_worker():
            start_time = time.time()
            success = False
            module = None
            
            try:
                # 检查依赖
                if module_name in self.modules:
                    for dep in self.modules[module_name].dependencies:
                        if dep not in self.loaded_modules:
                            print(f"[WARN] 模块 {module_name} 依赖 {dep} 未加载")
                
                # 导入模块
                module = importlib.import_module(module_name)
                self.loaded_modules[module_name] = module
                success = True
                
                # 更新统计
                if module_name in self.modules:
                    self.modules[module_name].usage_count += 1
                    self.modules[module_name].last_used = time.time()
                    self.modules[module_name].load_success = True
                
                load_time = time.time() - start_time
                print(f"[OK] 模块 {module_name} 加载成功 (耗时: {load_time:.3f}秒)")
                
            except Exception as e:
                load_time = time.time() - start_time
                print(f"[WARN] 模块 {module_name} 加载失败: {e} (耗时: {load_time:.3f}秒)")
                
                if module_name in self.modules:
                    self.modules[module_name].load_success = False
            
            # 执行回调
            if callback:
                callback(module_name, module, success)
            
            # 执行等待的回调
            if module_name in self.load_callbacks:
                for cb in self.load_callbacks[module_name]:
                    cb(module_name, module, success)
                del self.load_callbacks[module_name]
            
            # 清理线程引用
            if module_name in self.loading_threads:
                del self.loading_threads[module_name]
        
        # 启动加载线程
        thread = threading.Thread(target=load_worker, daemon=True)
        self.loading_threads[module_name] = thread
        thread.start()
    
    def preload_critical_modules(self, max_workers: int = 4) -> Dict[str, bool]:
        """预加载关键模块"""
        critical_modules = [name for name, module in self.modules.items() 
                          if module.priority >= 8]
        
        results = {}
        
        def load_callback(module_name: str, module: Any, success: bool):
            results[module_name] = success
        
        print(f"[INFO] 开始预加载 {len(critical_modules)} 个关键模块...")
        
        # 并行加载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for module_name in critical_modules:
                future = executor.submit(self.load_module_async, module_name, load_callback)
                futures.append(future)
            
            # 等待所有任务完成
            for future in as_completed(futures, timeout=30):
                try:
                    future.result()
                except Exception as e:
                    print(f"[WARN] 预加载任务失败: {e}")
        
        success_count = sum(1 for success in results.values() if success)
        print(f"[OK] 关键模块预加载完成: {success_count}/{len(critical_modules)} 成功")
        
        return results
    
    def preload_by_priority(self, min_priority: int = 5, max_workers: int = 2):
        """按优先级预加载模块"""
        sorted_modules = self.get_sorted_modules()
        target_modules = [name for name in sorted_modules 
                         if name in self.modules and self.modules[name].priority >= min_priority]
        
        print(f"[INFO] 按优先级预加载 {len(target_modules)} 个模块...")
        
        for module_name in target_modules:
            if module_name not in self.loaded_modules:
                self.load_module_async(module_name)
    
    def get_module(self, module_name: str, timeout: float = 5.0) -> Optional[Any]:
        """获取模块（同步）"""
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        
        # 如果正在加载，等待完成
        if module_name in self.loading_threads:
            thread = self.loading_threads[module_name]
            thread.join(timeout)
            
            if module_name in self.loaded_modules:
                return self.loaded_modules[module_name]
        
        # 同步加载
        try:
            module = importlib.import_module(module_name)
            self.loaded_modules[module_name] = module
            
            if module_name in self.modules:
                self.modules[module_name].usage_count += 1
                self.modules[module_name].last_used = time.time()
                self.modules[module_name].load_success = True
            
            return module
        except Exception as e:
            print(f"[WARN] 同步加载模块 {module_name} 失败: {e}")
            if module_name in self.modules:
                self.modules[module_name].load_success = False
            return None
    
    def get_load_report(self) -> Dict[str, Any]:
        """获取加载报告"""
        total_modules = len(self.modules)
        loaded_modules = len(self.loaded_modules)
        failed_modules = sum(1 for m in self.modules.values() if not m.load_success)
        
        return {
            'total_modules': total_modules,
            'loaded_modules': loaded_modules,
            'failed_modules': failed_modules,
            'success_rate': loaded_modules / total_modules * 100 if total_modules > 0 else 0,
            'loaded_list': list(self.loaded_modules.keys()),
            'failed_list': [name for name, module in self.modules.items() if not module.load_success]
        }

# 全局智能加载器实例
_smart_loader = None

def get_smart_loader() -> SmartModuleLoader:
    """获取全局智能加载器"""
    global _smart_loader
    if _smart_loader is None:
        _smart_loader = SmartModuleLoader()
    return _smart_loader

def preload_critical_modules():
    """预加载关键模块"""
    loader = get_smart_loader()
    return loader.preload_critical_modules()

def get_module(module_name: str, timeout: float = 5.0):
    """获取模块"""
    loader = get_smart_loader()
    return loader.get_module(module_name, timeout)

__all__ = [
    'ModuleInfo',
    'SmartModuleLoader',
    'get_smart_loader',
    'preload_critical_modules',
    'get_module'
]
