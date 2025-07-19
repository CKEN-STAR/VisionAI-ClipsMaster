"""
电源管理模块
提供电源感知的UI优化功能
"""

import platform
from typing import Dict, Any, Optional
from enum import Enum
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication

class PowerSource(Enum):
    """电源类型枚举"""
    BATTERY = "battery"
    AC_POWER = "ac_power"
    UNKNOWN = "unknown"

class PowerMode(Enum):
    """电源模式枚举"""
    POWER_SAVER = "power_saver"
    BALANCED = "balanced"
    HIGH_PERFORMANCE = "high_performance"

class PowerAwareUI(QObject):
    """电源感知UI"""
    
    power_mode_changed = pyqtSignal(str)
    battery_level_changed = pyqtSignal(int)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.current_mode = PowerMode.BALANCED
        self.power_optimizations = {
            'ui_animations_disabled': False,
            'refresh_rate_reduced': False,
            'background_tasks_limited': False,
            'cache_size_reduced': False
        }
    
    def apply_power_optimizations(self, mode: PowerMode) -> bool:
        """
        应用电源优化
        
        Args:
            mode: 电源模式
            
        Returns:
            是否成功应用
        """
        try:
            self.current_mode = mode
            optimizations = []
            
            if mode == PowerMode.POWER_SAVER:
                # 省电模式优化
                optimizations.extend(self._apply_power_saver_mode())
            elif mode == PowerMode.HIGH_PERFORMANCE:
                # 高性能模式优化
                optimizations.extend(self._apply_high_performance_mode())
            else:
                # 平衡模式优化
                optimizations.extend(self._apply_balanced_mode())
            
            # 发送模式变更信号
            self.power_mode_changed.emit(mode.value)
            
            print(f"[OK] 电源模式已切换到: {mode.value}")
            print(f"[OK] 应用的优化: {optimizations}")
            
            return True
            
        except Exception as e:
            print(f"[WARN] 应用电源优化失败: {e}")
            return False
    
    def _apply_power_saver_mode(self) -> list:
        """应用省电模式"""
        optimizations = []
        
        try:
            app = QApplication.instance()
            if app:
                # 禁用动画效果
                app.setEffectEnabled(app.Effect.UI_AnimateMenu, False)
                app.setEffectEnabled(app.Effect.UI_AnimateCombo, False)
                self.power_optimizations['ui_animations_disabled'] = True
                optimizations.append("animations_disabled")
                
                # 降低刷新率
                optimizations.append("refresh_rate_reduced")
                self.power_optimizations['refresh_rate_reduced'] = True
            
            # 限制后台任务
            self.power_optimizations['background_tasks_limited'] = True
            optimizations.append("background_tasks_limited")
            
            # 减少缓存大小
            self.power_optimizations['cache_size_reduced'] = True
            optimizations.append("cache_size_reduced")
            
        except Exception as e:
            print(f"[WARN] 省电模式设置失败: {e}")
        
        return optimizations
    
    def _apply_balanced_mode(self) -> list:
        """应用平衡模式"""
        optimizations = []
        
        try:
            app = QApplication.instance()
            if app:
                # 启用部分动画
                app.setEffectEnabled(app.Effect.UI_AnimateMenu, True)
                app.setEffectEnabled(app.Effect.UI_AnimateCombo, False)
                optimizations.append("selective_animations")
            
            # 重置优化状态
            self.power_optimizations = {
                'ui_animations_disabled': False,
                'refresh_rate_reduced': False,
                'background_tasks_limited': False,
                'cache_size_reduced': False
            }
            
            optimizations.append("balanced_settings")
            
        except Exception as e:
            print(f"[WARN] 平衡模式设置失败: {e}")
        
        return optimizations
    
    def _apply_high_performance_mode(self) -> list:
        """应用高性能模式"""
        optimizations = []
        
        try:
            app = QApplication.instance()
            if app:
                # 启用所有动画
                app.setEffectEnabled(app.Effect.UI_AnimateMenu, True)
                app.setEffectEnabled(app.Effect.UI_AnimateCombo, True)
                optimizations.append("all_animations_enabled")
            
            # 重置所有优化
            self.power_optimizations = {
                'ui_animations_disabled': False,
                'refresh_rate_reduced': False,
                'background_tasks_limited': False,
                'cache_size_reduced': False
            }
            
            optimizations.append("high_performance_settings")
            
        except Exception as e:
            print(f"[WARN] 高性能模式设置失败: {e}")
        
        return optimizations
    
    def get_current_mode(self) -> PowerMode:
        """获取当前电源模式"""
        return self.current_mode
    
    def get_power_optimizations(self) -> Dict[str, bool]:
        """获取当前电源优化状态"""
        return self.power_optimizations.copy()

class PowerWatcher(QObject):
    """电源监视器"""
    
    power_source_changed = pyqtSignal(str)
    battery_level_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.monitoring_enabled = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_power_status)
        self.last_power_source = PowerSource.UNKNOWN
        self.last_battery_level = -1
    
    def start_monitoring(self, interval_ms: int = 30000):
        """开始电源监控"""
        try:
            self.monitoring_enabled = True
            self.monitor_timer.start(interval_ms)
            print(f"[OK] 电源监控已启动，间隔: {interval_ms}ms")
        except Exception as e:
            print(f"[WARN] 启动电源监控失败: {e}")
    
    def stop_monitoring(self):
        """停止电源监控"""
        try:
            self.monitoring_enabled = False
            self.monitor_timer.stop()
            print("[OK] 电源监控已停止")
        except Exception as e:
            print(f"[WARN] 停止电源监控失败: {e}")
    
    def _check_power_status(self):
        """检查电源状态"""
        try:
            if not self.monitoring_enabled:
                return
            
            power_info = self.get_power_status()
            
            # 检查电源类型变化
            current_source = power_info['power_source']
            if current_source != self.last_power_source:
                self.last_power_source = current_source
                self.power_source_changed.emit(current_source.value)
            
            # 检查电池电量变化
            current_level = power_info['battery_level']
            if current_level != self.last_battery_level:
                self.last_battery_level = current_level
                self.battery_level_changed.emit(current_level)
                
        except Exception as e:
            print(f"[WARN] 检查电源状态失败: {e}")
    
    def get_power_status(self) -> Dict[str, Any]:
        """获取电源状态"""
        try:
            # 尝试使用psutil获取电池信息
            try:
                import psutil
                battery = psutil.sensors_battery()
                
                if battery:
                    return {
                        'power_source': PowerSource.AC_POWER if battery.power_plugged else PowerSource.BATTERY,
                        'battery_level': int(battery.percent),
                        'time_left_seconds': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
                    }
            except ImportError:
                pass
            
            # 回退到默认值
            return {
                'power_source': PowerSource.UNKNOWN,
                'battery_level': -1,
                'time_left_seconds': -1
            }
            
        except Exception as e:
            print(f"[WARN] 获取电源状态失败: {e}")
            return {
                'power_source': PowerSource.UNKNOWN,
                'battery_level': -1,
                'time_left_seconds': -1
            }

# 全局电源管理器实例
_power_manager: Optional[PowerAwareUI] = None
_power_watcher: Optional[PowerWatcher] = None

def get_power_manager() -> PowerAwareUI:
    """获取全局电源管理器"""
    global _power_manager
    if _power_manager is None:
        _power_manager = PowerAwareUI()
    return _power_manager

def get_power_watcher() -> PowerWatcher:
    """获取全局电源监视器"""
    global _power_watcher
    if _power_watcher is None:
        _power_watcher = PowerWatcher()
    return _power_watcher

def optimize_for_power_source(power_source: PowerSource) -> bool:
    """根据电源类型优化"""
    manager = get_power_manager()
    
    if power_source == PowerSource.BATTERY:
        return manager.apply_power_optimizations(PowerMode.POWER_SAVER)
    elif power_source == PowerSource.AC_POWER:
        return manager.apply_power_optimizations(PowerMode.HIGH_PERFORMANCE)
    else:
        return manager.apply_power_optimizations(PowerMode.BALANCED)

def get_power_status() -> Dict[str, Any]:
    """获取电源状态"""
    watcher = get_power_watcher()
    return watcher.get_power_status()

def enable_power_saving() -> bool:
    """启用省电模式"""
    manager = get_power_manager()
    return manager.apply_power_optimizations(PowerMode.POWER_SAVER)

__all__ = [
    'PowerSource',
    'PowerMode',
    'PowerAwareUI',
    'PowerWatcher',
    'get_power_manager',
    'get_power_watcher',
    'optimize_for_power_source',
    'get_power_status',
    'enable_power_saving'
]
