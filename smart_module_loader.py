#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 智能模块加载器
解决模块加载时机和异常处理问题
"""

import sys
import time
import threading
import traceback
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from encoding_fix import safe_logger

class SmartModuleLoader(QObject):
    """智能模块加载器"""
    
    module_loaded = pyqtSignal(str, bool)  # 模块名, 是否成功
    all_modules_loaded = pyqtSignal(int, int)  # 成功数量, 总数量
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.modules_to_load = {}
        self.loaded_modules = {}
        self.loading_status = {}
        self.load_attempts = {}
        self.max_attempts = 3
        
    def register_module(self, name, import_func, init_func=None, dependencies=None, priority=1):
        """注册需要加载的模块
        
        Args:
            name: 模块名称
            import_func: 导入函数
            init_func: 初始化函数
            dependencies: 依赖模块列表
            priority: 优先级 (1=最高, 5=最低)
        """
        self.modules_to_load[name] = {
            'import_func': import_func,
            'init_func': init_func,
            'dependencies': dependencies or [],
            'priority': priority,
            'loaded': False,
            'initialized': False
        }
        self.loading_status[name] = 'pending'
        self.load_attempts[name] = 0
        
        safe_logger.info(f"注册模块: {name} (优先级: {priority})")
    
    def start_loading(self, delay_ms=2000):
        """开始加载模块"""
        safe_logger.info(f"将在 {delay_ms}ms 后开始智能模块加载...")
        QTimer.singleShot(delay_ms, self._load_modules_by_priority)
    
    def _load_modules_by_priority(self):
        """按优先级加载模块"""
        safe_logger.info("开始按优先级加载模块...")
        
        # 按优先级排序
        sorted_modules = sorted(
            self.modules_to_load.items(),
            key=lambda x: x[1]['priority']
        )
        
        for name, module_info in sorted_modules:
            if not module_info['loaded']:
                self._load_single_module(name)
                # 在模块之间添加小延迟，避免冲突
                time.sleep(0.1)
        
        # 检查加载结果
        self._check_loading_results()
    
    def _load_single_module(self, name):
        """加载单个模块"""
        if name not in self.modules_to_load:
            return False
            
        module_info = self.modules_to_load[name]
        
        # 检查是否已经加载
        if module_info['loaded']:
            return True
        
        # 检查加载次数
        if self.load_attempts[name] >= self.max_attempts:
            safe_logger.error(f"模块 {name} 加载失败，已达到最大尝试次数")
            self.loading_status[name] = 'failed'
            return False
        
        self.load_attempts[name] += 1
        safe_logger.info(f"尝试加载模块 {name} (第 {self.load_attempts[name]} 次)")
        
        try:
            # 检查依赖
            if not self._check_dependencies(name):
                safe_logger.warning(f"模块 {name} 的依赖未满足，稍后重试")
                QTimer.singleShot(1000, lambda: self._load_single_module(name))
                return False
            
            # 导入模块
            self.loading_status[name] = 'importing'
            imported_module = module_info['import_func']()
            
            if imported_module is not None:
                self.loaded_modules[name] = imported_module
                module_info['loaded'] = True
                self.loading_status[name] = 'imported'
                safe_logger.success(f"模块 {name} 导入成功")
                
                # 初始化模块
                if module_info['init_func']:
                    self._initialize_module(name)
                else:
                    module_info['initialized'] = True
                    self.loading_status[name] = 'ready'
                
                self.module_loaded.emit(name, True)
                return True
            else:
                raise Exception("模块导入返回None")
                
        except Exception as e:
            safe_logger.error(f"模块 {name} 加载失败: {e}")
            self.loading_status[name] = 'error'
            self.module_loaded.emit(name, False)
            
            # 如果还有尝试次数，延迟重试
            if self.load_attempts[name] < self.max_attempts:
                retry_delay = 2000 * self.load_attempts[name]  # 递增延迟
                safe_logger.info(f"将在 {retry_delay}ms 后重试加载 {name}")
                QTimer.singleShot(retry_delay, lambda: self._load_single_module(name))
            
            return False
    
    def _initialize_module(self, name):
        """初始化模块"""
        try:
            module_info = self.modules_to_load[name]
            if module_info['init_func'] and not module_info['initialized']:
                self.loading_status[name] = 'initializing'
                safe_logger.info(f"初始化模块 {name}...")
                
                result = module_info['init_func'](self.main_window)
                
                if result is not False:  # None 或 True 都认为成功
                    module_info['initialized'] = True
                    self.loading_status[name] = 'ready'
                    safe_logger.success(f"模块 {name} 初始化成功")
                else:
                    raise Exception("初始化函数返回False")
                    
        except Exception as e:
            safe_logger.error(f"模块 {name} 初始化失败: {e}")
            self.loading_status[name] = 'init_error'
    
    def _check_dependencies(self, name):
        """检查模块依赖"""
        module_info = self.modules_to_load[name]
        for dep_name in module_info['dependencies']:
            if dep_name not in self.modules_to_load:
                continue
            if not self.modules_to_load[dep_name]['loaded']:
                return False
        return True
    
    def _check_loading_results(self):
        """检查加载结果"""
        total_modules = len(self.modules_to_load)
        loaded_count = sum(1 for info in self.modules_to_load.values() if info['loaded'])
        initialized_count = sum(1 for info in self.modules_to_load.values() if info['initialized'])
        
        safe_logger.info(f"模块加载完成: {loaded_count}/{total_modules} 导入, {initialized_count}/{total_modules} 初始化")
        
        # 显示详细状态
        for name, status in self.loading_status.items():
            status_icon = {
                'ready': '✅',
                'imported': '🔄',
                'error': '❌',
                'init_error': '⚠️',
                'failed': '💥',
                'pending': '⏳'
            }.get(status, '❓')
            
            safe_logger.info(f"  {status_icon} {name}: {status}")
        
        # 发出完成信号
        self.all_modules_loaded.emit(initialized_count, total_modules)
        
        # 如果成功率达到75%，认为集成成功
        success_rate = initialized_count / total_modules
        if success_rate >= 0.75:
            safe_logger.success(f"模块集成成功! 成功率: {success_rate*100:.1f}%")
            self._notify_integration_success(initialized_count, total_modules)
        else:
            safe_logger.warning(f"模块集成部分成功，成功率: {success_rate*100:.1f}%")
    
    def _notify_integration_success(self, success_count, total_count):
        """通知集成成功"""
        try:
            if hasattr(self.main_window, 'alert_manager') and self.main_window.alert_manager:
                self.main_window.alert_manager.info(
                    f"第二阶段优化已激活 ({success_count}/{total_count})",
                    timeout=5000
                )
        except Exception as e:
            safe_logger.warning(f"通知显示失败: {e}")
    
    def get_loading_status(self):
        """获取加载状态"""
        return {
            'modules': dict(self.loading_status),
            'loaded_count': sum(1 for info in self.modules_to_load.values() if info['loaded']),
            'total_count': len(self.modules_to_load),
            'success_rate': sum(1 for info in self.modules_to_load.values() if info['initialized']) / len(self.modules_to_load) if self.modules_to_load else 0
        }

def create_module_loader(main_window):
    """创建模块加载器的工厂函数"""
    loader = SmartModuleLoader(main_window)
    
    # 注册第二阶段优化模块
    def import_startup_optimizer():
        try:
            from startup_optimizer import initialize_startup_optimizer
            return initialize_startup_optimizer
        except Exception as e:
            safe_logger.error(f"导入启动优化器失败: {e}")
            return None
    
    def import_response_monitor():
        try:
            from response_monitor_enhanced import initialize_enhanced_response_monitor, start_response_monitoring
            return (initialize_enhanced_response_monitor, start_response_monitoring)
        except Exception as e:
            safe_logger.error(f"导入响应监控器失败: {e}")
            return None
    
    def import_css_optimizer():
        try:
            from css_optimizer import apply_optimized_styles
            return apply_optimized_styles
        except Exception as e:
            safe_logger.error(f"导入CSS优化器失败: {e}")
            return None
    
    def import_user_experience():
        try:
            from user_experience_enhancer import initialize_user_experience_enhancer
            return initialize_user_experience_enhancer
        except Exception as e:
            safe_logger.error(f"导入用户体验增强器失败: {e}")
            return None
    
    def init_startup_optimizer(main_window):
        try:
            if 'startup_optimizer' in loader.loaded_modules:
                init_func = loader.loaded_modules['startup_optimizer']
                main_window.startup_optimizer = init_func(main_window)
                return True
        except Exception as e:
            safe_logger.error(f"初始化启动优化器失败: {e}")
            return False
    
    def init_response_monitor(main_window):
        try:
            if 'response_monitor' in loader.loaded_modules:
                init_func, start_func = loader.loaded_modules['response_monitor']
                main_window.enhanced_response_monitor = init_func(main_window)
                start_func()
                return True
        except Exception as e:
            safe_logger.error(f"初始化响应监控器失败: {e}")
            return False
    
    def init_css_optimizer(main_window):
        try:
            if 'css_optimizer' in loader.loaded_modules:
                apply_func = loader.loaded_modules['css_optimizer']
                apply_func(main_window)
                return True
        except Exception as e:
            safe_logger.error(f"初始化CSS优化器失败: {e}")
            return False
    
    def init_user_experience(main_window):
        try:
            if 'user_experience' in loader.loaded_modules:
                init_func = loader.loaded_modules['user_experience']
                init_func(main_window)
                return True
        except Exception as e:
            safe_logger.error(f"初始化用户体验增强器失败: {e}")
            return False
    
    # 注册模块
    loader.register_module('startup_optimizer', import_startup_optimizer, init_startup_optimizer, [], 1)
    loader.register_module('response_monitor', import_response_monitor, init_response_monitor, [], 2)
    loader.register_module('css_optimizer', import_css_optimizer, init_css_optimizer, [], 3)
    loader.register_module('user_experience', import_user_experience, init_user_experience, [], 4)
    
    return loader
