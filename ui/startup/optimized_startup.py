"""
优化的启动流程
整合智能加载和进度显示，提供最佳启动体验
"""

import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

from .smart_loader import get_smart_loader, SmartModuleLoader
from .progress_manager import StartupProgressDialog

class OptimizedStartupManager(QObject):
    """优化启动管理器"""
    
    startup_completed = pyqtSignal(bool, float, dict)  # 成功, 耗时, 报告
    stage_progress = pyqtSignal(str, int, str)  # 阶段名, 进度, 状态
    
    def __init__(self):
        super().__init__()
        self.smart_loader = get_smart_loader()
        self.progress_dialog = None
        self.start_time = 0
        self.stages_completed = 0
        self.total_stages = 6
        
        # 启动阶段定义
        self.startup_stages = [
            {
                'name': '环境初始化',
                'function': self._stage_environment_init,
                'weight': 15
            },
            {
                'name': '关键模块预加载',
                'function': self._stage_critical_preload,
                'weight': 30
            },
            {
                'name': 'PyQt应用创建',
                'function': self._stage_app_creation,
                'weight': 20
            },
            {
                'name': '样式系统初始化',
                'function': self._stage_style_init,
                'weight': 15
            },
            {
                'name': '主窗口创建',
                'function': self._stage_main_window,
                'weight': 15
            },
            {
                'name': '后台组件加载',
                'function': self._stage_background_load,
                'weight': 5
            }
        ]
    
    def start_optimized_startup(self, show_progress: bool = True) -> Dict[str, Any]:
        """开始优化启动流程"""
        self.start_time = time.time()
        
        print("=" * 60)
        print("🚀 VisionAI-ClipsMaster 优化启动流程")
        print("=" * 60)
        
        # 首先创建QApplication（如果需要显示进度对话框）
        if show_progress:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            self._show_progress_dialog()

        # 执行启动阶段
        startup_success = True
        stage_results = {}
        
        cumulative_progress = 0
        
        for i, stage in enumerate(self.startup_stages):
            stage_name = stage['name']
            stage_function = stage['function']
            stage_weight = stage['weight']
            
            print(f"\n[{i+1}/{len(self.startup_stages)}] {stage_name}...")
            stage_start = time.time()
            
            # 更新进度
            self.stage_progress.emit(stage_name, int(cumulative_progress), f"正在执行: {stage_name}")
            
            try:
                # 执行阶段
                result = stage_function()
                stage_time = time.time() - stage_start
                
                stage_results[stage_name] = {
                    'success': True,
                    'time': stage_time,
                    'result': result
                }
                
                print(f"✅ {stage_name} 完成 (耗时: {stage_time:.2f}秒)")
                
            except Exception as e:
                stage_time = time.time() - stage_start
                stage_results[stage_name] = {
                    'success': False,
                    'time': stage_time,
                    'error': str(e)
                }
                
                print(f"❌ {stage_name} 失败: {e} (耗时: {stage_time:.2f}秒)")
                startup_success = False
                
                # 关键阶段失败则停止启动
                if i < 4:  # 前4个阶段是关键的
                    break
            
            # 更新累积进度
            cumulative_progress += stage_weight
            self.stage_progress.emit(stage_name, int(cumulative_progress), f"{stage_name} 完成")
        
        # 计算总耗时
        total_time = time.time() - self.start_time
        
        # 生成启动报告
        startup_report = self._generate_startup_report(stage_results, total_time, startup_success)
        
        # 发送完成信号
        self.startup_completed.emit(startup_success, total_time, startup_report)
        
        # 关闭进度对话框
        if self.progress_dialog:
            QTimer.singleShot(1000, self.progress_dialog.accept)
        
        print("\n" + "=" * 60)
        if startup_success:
            print(f"🎉 启动成功！总耗时: {total_time:.2f}秒")
        else:
            print(f"💥 启动失败！耗时: {total_time:.2f}秒")
        print("=" * 60)
        
        return startup_report
    
    def _show_progress_dialog(self):
        """显示进度对话框"""
        try:
            # 确保QApplication存在
            app = QApplication.instance()
            if app is None:
                print("[WARN] QApplication不存在，跳过进度对话框显示")
                return

            self.progress_dialog = StartupProgressDialog()

            # 创建适配器函数来匹配信号参数
            def progress_adapter(stage_name: str, progress: int, status: str):
                self.progress_dialog.update_progress(progress, status)

            self.stage_progress.connect(progress_adapter)

            # 在单独线程中显示对话框
            def show_dialog():
                self.progress_dialog.show()

            QTimer.singleShot(0, show_dialog)

        except Exception as e:
            print(f"[WARN] 无法显示进度对话框: {e}")
    
    def _stage_environment_init(self) -> Dict[str, Any]:
        """阶段1: 环境初始化"""
        # 设置CUDA环境
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TORCH_USE_CUDA_DSA'] = '0'
        
        # 设置Python路径
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        
        # 应用技术修复
        try:
            from ui.fixes.integrated_fix import apply_all_fixes
            apply_all_fixes()
        except Exception as e:
            print(f"[WARN] 技术修复失败: {e}")
        
        return {
            'cuda_disabled': True,
            'python_path_set': True,
            'fixes_applied': True
        }
    
    def _stage_critical_preload(self) -> Dict[str, Any]:
        """阶段2: 关键模块预加载"""
        # 预加载关键模块
        preload_results = self.smart_loader.preload_critical_modules(max_workers=4)
        
        # 等待关键模块加载完成
        critical_modules = ['PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui']
        for module_name in critical_modules:
            module = self.smart_loader.get_module(module_name, timeout=10)
            if module is None:
                raise Exception(f"关键模块 {module_name} 加载失败")
        
        return {
            'preload_results': preload_results,
            'critical_modules_loaded': len(critical_modules)
        }
    
    def _stage_app_creation(self) -> Dict[str, Any]:
        """阶段3: PyQt应用创建"""
        # 获取或创建QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 应用后修复
        try:
            from ui.fixes.integrated_fix import initialize_post_app_fixes
            initialize_post_app_fixes(app)
        except Exception as e:
            print(f"[WARN] 应用后修复失败: {e}")
        
        return {
            'app_created': True,
            'app_instance': app
        }
    
    def _stage_style_init(self) -> Dict[str, Any]:
        """阶段4: 样式系统初始化"""
        # 加载样式管理器
        style_manager = self.smart_loader.get_module('src.ui.enhanced_style_manager')
        if style_manager is None:
            raise Exception("样式管理器加载失败")
        
        # 初始化默认主题
        try:
            style_manager.style_manager.apply_theme('default')
        except Exception as e:
            print(f"[WARN] 应用默认主题失败: {e}")
        
        return {
            'style_manager_loaded': True,
            'default_theme_applied': True
        }
    
    def _stage_main_window(self) -> Dict[str, Any]:
        """阶段5: 主窗口创建"""
        # 这里只是准备主窗口创建的环境
        # 实际的主窗口创建由调用方负责
        
        # 预加载主窗口相关模块
        ui_modules = [
            'ui.responsive.simple_ui_adapter',
            'ui.hardware.performance_tier',
            'ui.components.alert_manager'
        ]
        
        loaded_count = 0
        for module_name in ui_modules:
            if self.smart_loader.get_module(module_name, timeout=5):
                loaded_count += 1
        
        return {
            'ui_modules_preloaded': loaded_count,
            'ready_for_main_window': True
        }
    
    def _stage_background_load(self) -> Dict[str, Any]:
        """阶段6: 后台组件加载"""
        # 启动后台预加载
        self.smart_loader.preload_by_priority(min_priority=4, max_workers=2)
        
        # 保存使用统计
        self.smart_loader.save_usage_stats()
        
        return {
            'background_loading_started': True,
            'usage_stats_saved': True
        }
    
    def _generate_startup_report(self, stage_results: Dict, total_time: float, success: bool) -> Dict[str, Any]:
        """生成启动报告"""
        # 计算各阶段统计
        successful_stages = sum(1 for result in stage_results.values() if result['success'])
        total_stages = len(stage_results)
        
        # 获取模块加载报告
        load_report = self.smart_loader.get_load_report()
        
        # 性能分析
        stage_times = {name: result['time'] for name, result in stage_results.items()}
        slowest_stage = max(stage_times.items(), key=lambda x: x[1]) if stage_times else ('无', 0)
        
        report = {
            'startup_success': success,
            'total_time': total_time,
            'successful_stages': successful_stages,
            'total_stages': total_stages,
            'success_rate': successful_stages / total_stages * 100 if total_stages > 0 else 0,
            'stage_results': stage_results,
            'stage_times': stage_times,
            'slowest_stage': slowest_stage,
            'module_load_report': load_report,
            'performance_metrics': {
                'target_time': 30.0,
                'achieved_time': total_time,
                'improvement_needed': max(0, total_time - 30.0),
                'performance_rating': 'excellent' if total_time <= 20 else 
                                    'good' if total_time <= 30 else 
                                    'needs_improvement'
            }
        }
        
        return report

def start_optimized_application(show_progress: bool = True) -> Dict[str, Any]:
    """启动优化应用程序"""
    manager = OptimizedStartupManager()
    return manager.start_optimized_startup(show_progress)

def create_main_window_after_startup():
    """在优化启动后创建主窗口"""
    try:
        # 获取智能加载器
        loader = get_smart_loader()
        
        # 确保主应用模块已加载
        main_module = loader.get_module('simple_ui_fixed', timeout=10)
        if main_module is None:
            raise Exception("主应用模块加载失败")
        
        # 创建主窗口
        app_class = getattr(main_module, 'SimpleScreenplayApp')
        main_window = app_class()
        
        return main_window
        
    except Exception as e:
        print(f"[ERROR] 创建主窗口失败: {e}")
        return None

__all__ = [
    'OptimizedStartupManager',
    'start_optimized_application',
    'create_main_window_after_startup'
]
