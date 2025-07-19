"""
热键管理器
提供热键绑定和管理功能
"""

from typing import Dict, Callable, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget

class PanelHotkeys(QObject):
    """面板热键管理器"""
    
    hotkey_triggered = pyqtSignal(str)  # 热键触发信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.shortcuts: Dict[str, QShortcut] = {}
        self.hotkey_map: Dict[str, str] = {}
        
    def register_hotkey(self, key_sequence: str, action_name: str, callback: Optional[Callable] = None) -> bool:
        """
        注册热键

        Args:
            key_sequence: 按键序列，如 "Ctrl+S"
            action_name: 动作名称
            callback: 回调函数（可选）

        Returns:
            是否成功注册
        """
        try:
            if not self.parent_widget:
                print(f"[WARN] 无法注册热键 {key_sequence}: 没有父组件")
                return False

            # 检查是否在主线程中
            from PyQt6.QtCore import QThread
            if QThread.currentThread() != self.parent_widget.thread():
                print(f"[WARN] 无法注册热键 {key_sequence}: 不在主线程中")
                return False

            # 创建快捷键
            shortcut = QShortcut(QKeySequence(key_sequence), self.parent_widget)
            
            # 连接信号
            if callback:
                shortcut.activated.connect(callback)
            else:
                shortcut.activated.connect(lambda: self.hotkey_triggered.emit(action_name))
            
            # 保存引用
            self.shortcuts[action_name] = shortcut
            self.hotkey_map[action_name] = key_sequence
            
            return True
            
        except Exception as e:
            print(f"[WARN] 热键注册失败 {key_sequence}: {e}")
            return False
    
    def unregister_hotkey(self, action_name: str) -> bool:
        """取消注册热键"""
        try:
            if action_name in self.shortcuts:
                self.shortcuts[action_name].deleteLater()
                del self.shortcuts[action_name]
                del self.hotkey_map[action_name]
                return True
            return False
        except Exception as e:
            print(f"[WARN] 热键取消注册失败 {action_name}: {e}")
            return False
    
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取已注册的热键"""
        return self.hotkey_map.copy()
    
    def clear_all_hotkeys(self):
        """清除所有热键"""
        for shortcut in self.shortcuts.values():
            shortcut.deleteLater()
        self.shortcuts.clear()
        self.hotkey_map.clear()

class GlobalHotkeys(QObject):
    """全局热键管理器"""
    
    def __init__(self):
        super().__init__()
        self.global_shortcuts: Dict[str, str] = {}
        
    def register_global_hotkey(self, key_sequence: str, action_name: str) -> bool:
        """
        注册全局热键（注意：Qt6中全局热键需要额外的实现）
        
        Args:
            key_sequence: 按键序列
            action_name: 动作名称
            
        Returns:
            是否成功注册
        """
        try:
            # 在实际实现中，这里需要使用平台特定的API
            # 目前只是记录，不实际注册全局热键
            self.global_shortcuts[action_name] = key_sequence
            print(f"[INFO] 全局热键已记录: {action_name} -> {key_sequence}")
            return True
            
        except Exception as e:
            print(f"[WARN] 全局热键注册失败: {e}")
            return False
    
    def get_global_hotkeys(self) -> Dict[str, str]:
        """获取全局热键"""
        return self.global_shortcuts.copy()

def create_default_hotkeys(parent: QWidget) -> PanelHotkeys:
    """创建默认热键配置"""
    hotkeys = PanelHotkeys(parent)
    
    # 注册默认热键
    default_bindings = {
        "Ctrl+N": "new_project",
        "Ctrl+O": "open_project", 
        "Ctrl+S": "save_project",
        "Ctrl+Q": "quit_application",
        "F1": "show_help",
        "F5": "refresh",
        "Ctrl+Z": "undo",
        "Ctrl+Y": "redo",
        "Space": "play_pause",
        "Ctrl+E": "export_project"
    }
    
    for key_seq, action in default_bindings.items():
        hotkeys.register_hotkey(key_seq, action)
    
    return hotkeys

def get_hotkey_help_text() -> List[str]:
    """获取热键帮助文本"""
    return [
        "快捷键说明:",
        "Ctrl+N - 新建项目",
        "Ctrl+O - 打开项目",
        "Ctrl+S - 保存项目", 
        "Ctrl+Q - 退出应用",
        "F1 - 显示帮助",
        "F5 - 刷新",
        "Ctrl+Z - 撤销",
        "Ctrl+Y - 重做",
        "Space - 播放/暂停",
        "Ctrl+E - 导出项目"
    ]

__all__ = [
    'PanelHotkeys',
    'GlobalHotkeys',
    'create_default_hotkeys',
    'get_hotkey_help_text'
]
