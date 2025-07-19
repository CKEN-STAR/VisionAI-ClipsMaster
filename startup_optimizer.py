#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 启动性能优化器
目标：将启动时间从7.88秒优化到3秒以内
"""

import time
import threading
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication
import weakref

class StartupOptimizer(QObject):
    """启动性能优化器"""
    
    startup_completed = pyqtSignal()
    component_loaded = pyqtSignal(str, float)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = weakref.ref(main_window)
        self.startup_start_time = time.time()
        self.component_load_times = {}
        self.deferred_components = []
        
        # 启动阶段定义
        self.startup_phases = {
            "critical": [],      # 立即加载（UI基础）
            "important": [],     # 2秒后加载（核心功能）
            "optional": [],      # 5秒后加载（辅助功能）
            "background": []     # 10秒后加载（后台功能）
        }
        
    def register_component(self, name, load_func, phase="important", dependencies=None):
        """注册需要延迟加载的组件
        
        Args:
            name: 组件名称
            load_func: 加载函数
            phase: 加载阶段 (critical/important/optional/background)
            dependencies: 依赖的组件列表
        """
        component = {
            "name": name,
            "load_func": load_func,
            "dependencies": dependencies or [],
            "loaded": False,
            "loading": False
        }
        
        self.startup_phases[phase].append(component)
        
    def start_optimized_startup(self):
        """开始优化的启动流程"""
        print("[INFO] 启动性能优化器开始工作...")
        
        # 立即加载关键组件
        self._load_phase("critical")
        
        # 延迟加载其他组件
        QTimer.singleShot(2000, lambda: self._load_phase("important"))
        QTimer.singleShot(5000, lambda: self._load_phase("optional"))
        QTimer.singleShot(10000, lambda: self._load_phase("background"))
        
        # 监控启动完成
        QTimer.singleShot(3000, self._check_startup_completion)
        
    def _load_phase(self, phase_name):
        """加载指定阶段的组件"""
        try:
            components = self.startup_phases.get(phase_name, [])
            print(f"[INFO] 开始加载 {phase_name} 阶段组件 ({len(components)} 个)")
            
            for component in components:
                if not component["loaded"] and not component["loading"]:
                    self._load_component_async(component)
                    
        except Exception as e:
            print(f"[ERROR] 加载 {phase_name} 阶段失败: {e}")
            
    def _load_component_async(self, component):
        """异步加载组件"""
        def load_worker():
            try:
                component["loading"] = True
                start_time = time.time()
                
                # 检查依赖
                if not self._check_dependencies(component):
                    print(f"[WARN] 组件 {component['name']} 依赖未满足，延迟加载")
                    QTimer.singleShot(1000, lambda: self._load_component_async(component))
                    return
                
                # 执行加载
                component["load_func"]()
                
                # 记录加载时间
                elapsed = time.time() - start_time
                self.component_load_times[component["name"]] = elapsed
                component["loaded"] = True
                component["loading"] = False
                
                print(f"[OK] 组件 {component['name']} 加载完成，耗时: {elapsed:.3f}秒")
                self.component_loaded.emit(component["name"], elapsed)
                
            except Exception as e:
                print(f"[ERROR] 组件 {component['name']} 加载失败: {e}")
                component["loading"] = False
                
        # 在线程池中执行
        threading.Thread(target=load_worker, daemon=True).start()
        
    def _check_dependencies(self, component):
        """检查组件依赖是否满足"""
        for dep_name in component["dependencies"]:
            # 查找依赖组件
            dep_loaded = False
            for phase_components in self.startup_phases.values():
                for comp in phase_components:
                    if comp["name"] == dep_name and comp["loaded"]:
                        dep_loaded = True
                        break
                if dep_loaded:
                    break
                    
            if not dep_loaded:
                return False
                
        return True
        
    def _check_startup_completion(self):
        """检查启动是否完成"""
        try:
            elapsed = time.time() - self.startup_start_time
            
            # 统计加载情况
            total_components = sum(len(comps) for comps in self.startup_phases.values())
            loaded_components = sum(
                1 for comps in self.startup_phases.values() 
                for comp in comps if comp["loaded"]
            )
            
            print(f"[INFO] 启动检查: {elapsed:.2f}秒, 已加载组件: {loaded_components}/{total_components}")
            
            # 如果关键组件已加载，认为启动完成
            critical_loaded = all(comp["loaded"] for comp in self.startup_phases["critical"])
            important_loaded = sum(1 for comp in self.startup_phases["important"] if comp["loaded"])
            important_total = len(self.startup_phases["important"])
            
            if critical_loaded and (important_loaded >= important_total * 0.7):
                print(f"[OK] 启动完成! 总耗时: {elapsed:.2f}秒")
                self.startup_completed.emit()
            else:
                # 继续检查
                QTimer.singleShot(1000, self._check_startup_completion)
                
        except Exception as e:
            print(f"[ERROR] 启动完成检查失败: {e}")
            
    def get_startup_report(self):
        """获取启动报告"""
        total_time = time.time() - self.startup_start_time
        
        report = {
            "total_startup_time": total_time,
            "component_load_times": self.component_load_times.copy(),
            "phases_status": {}
        }
        
        for phase_name, components in self.startup_phases.items():
            loaded_count = sum(1 for comp in components if comp["loaded"])
            total_count = len(components)
            
            report["phases_status"][phase_name] = {
                "loaded": loaded_count,
                "total": total_count,
                "completion_rate": loaded_count / total_count if total_count > 0 else 1.0
            }
            
        return report

class LazyModuleLoader:
    """懒加载模块管理器"""
    
    def __init__(self):
        self._modules = {}
        self._loading = set()
        
    def register_module(self, name, import_func):
        """注册模块"""
        self._modules[name] = {
            "import_func": import_func,
            "module": None,
            "loaded": False
        }
        
    def get_module(self, name):
        """获取模块（懒加载）"""
        if name not in self._modules:
            raise ValueError(f"未注册的模块: {name}")
            
        module_info = self._modules[name]
        
        if module_info["loaded"]:
            return module_info["module"]
            
        if name in self._loading:
            # 正在加载，等待
            while name in self._loading:
                time.sleep(0.001)
            return module_info["module"]
            
        # 开始加载
        self._loading.add(name)
        try:
            print(f"[INFO] 懒加载模块: {name}")
            start_time = time.time()
            
            module_info["module"] = module_info["import_func"]()
            module_info["loaded"] = True
            
            elapsed = time.time() - start_time
            print(f"[OK] 模块 {name} 加载完成，耗时: {elapsed:.3f}秒")
            
            return module_info["module"]
            
        except Exception as e:
            print(f"[ERROR] 模块 {name} 加载失败: {e}")
            raise
        finally:
            self._loading.discard(name)
            
    def preload_modules(self, module_names):
        """预加载指定模块"""
        for name in module_names:
            if name in self._modules and not self._modules[name]["loaded"]:
                try:
                    self.get_module(name)
                except Exception as e:
                    print(f"[WARN] 预加载模块 {name} 失败: {e}")

# 全局实例
startup_optimizer = None
lazy_loader = LazyModuleLoader()

def initialize_startup_optimizer(main_window):
    """初始化启动优化器"""
    global startup_optimizer
    startup_optimizer = StartupOptimizer(main_window)
    
    # 注册常用模块的懒加载
    lazy_loader.register_module("psutil", lambda: __import__("psutil"))
    lazy_loader.register_module("requests", lambda: __import__("requests"))
    lazy_loader.register_module("json", lambda: __import__("json"))
    
    print("[OK] 启动性能优化器初始化完成")
    return startup_optimizer

def register_component(name, load_func, phase="important", dependencies=None):
    """注册组件的全局接口"""
    if startup_optimizer:
        startup_optimizer.register_component(name, load_func, phase, dependencies)
    else:
        print(f"[WARN] 启动优化器未初始化，直接加载组件: {name}")
        try:
            load_func()
        except Exception as e:
            print(f"[ERROR] 组件 {name} 加载失败: {e}")

def start_optimized_startup():
    """开始优化启动的全局接口"""
    if startup_optimizer:
        startup_optimizer.start_optimized_startup()
    else:
        print("[WARN] 启动优化器未初始化")

def get_startup_report():
    """获取启动报告的全局接口"""
    if startup_optimizer:
        return startup_optimizer.get_startup_report()
    else:
        return {"error": "启动优化器未初始化"}

def get_lazy_module(name):
    """获取懒加载模块的全局接口"""
    return lazy_loader.get_module(name)
