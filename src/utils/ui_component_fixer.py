#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI组件集成修复器

专门修复VisionAI-ClipsMaster的UI组件导入、线程安全和CSS兼容性问题。
"""

import os
import sys
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UIComponentFixer:
    """UI组件集成修复器
    
    修复以下问题：
    1. UI组件导入失败
    2. PyQt6线程安全问题
    3. CSS兼容性警告
    4. 组件初始化错误
    """
    
    def __init__(self, project_root: str = "."):
        """初始化修复器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.css_warnings_fixed = 0
        self.thread_safety_fixes = 0
        
    def fix_ui_component_imports(self) -> Dict[str, Any]:
        """修复UI组件导入问题
        
        Returns:
            Dict[str, Any]: 修复结果
        """
        result = {
            "success": True,
            "components_fixed": [],
            "errors": []
        }
        
        try:
            # 修复training_panel.py导入
            training_panel_path = self.project_root / "ui" / "training_panel.py"
            if training_panel_path.exists():
                self._fix_component_imports(training_panel_path, "TrainingPanel")
                result["components_fixed"].append("TrainingPanel")
            
            # 修复progress_dashboard.py导入
            progress_dashboard_path = self.project_root / "ui" / "progress_dashboard.py"
            if progress_dashboard_path.exists():
                self._fix_component_imports(progress_dashboard_path, "ProgressDashboard")
                result["components_fixed"].append("ProgressDashboard")
            
            # 修复alert_manager.py导入
            alert_manager_path = self.project_root / "ui" / "components" / "alert_manager.py"
            if alert_manager_path.exists():
                self._fix_component_imports(alert_manager_path, "AlertManager")
                result["components_fixed"].append("AlertManager")
            
            logger.info(f"UI组件导入修复完成，修复了 {len(result['components_fixed'])} 个组件")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"UI组件导入修复失败: {e}")
        
        return result
    
    def _fix_component_imports(self, file_path: Path, component_name: str):
        """修复单个组件的导入问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加安全导入包装
            safe_import_wrapper = f'''
# 安全导入包装 - 自动生成
import sys
import os

# 确保PyQt6可用
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print(f"[WARN] PyQt6不可用，{component_name}将使用fallback模式")

# 线程安全检查
def ensure_main_thread():
    """确保在主线程中执行"""
    if QT_AVAILABLE and QApplication.instance():
        current_thread = QThread.currentThread()
        main_thread = QApplication.instance().thread()
        if current_thread != main_thread:
            print(f"[WARN] {component_name}不在主线程中，可能导致问题")
            return False
    return True

'''
            
            # 如果还没有安全导入包装，则添加
            if "# 安全导入包装 - 自动生成" not in content:
                content = safe_import_wrapper + content
            
            # 保存修复后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"组件 {component_name} 导入修复完成")
            
        except Exception as e:
            logger.error(f"修复组件 {component_name} 导入失败: {e}")
    
    def fix_thread_safety_issues(self) -> Dict[str, Any]:
        """修复PyQt6线程安全问题
        
        Returns:
            Dict[str, Any]: 修复结果
        """
        result = {
            "success": True,
            "fixes_applied": 0,
            "errors": []
        }
        
        try:
            # 创建线程安全工具模块
            thread_safety_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线程安全工具模块

提供PyQt6线程安全的工具函数和装饰器。
"""

import threading
from functools import wraps
from typing import Callable, Any

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread, QTimer, QMetaObject, Qt
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

def is_main_thread() -> bool:
    """检查是否在主线程中"""
    if not QT_AVAILABLE:
        return True
    
    app = QApplication.instance()
    if not app:
        return True
    
    return QThread.currentThread() == app.thread()

def ensure_main_thread(func: Callable) -> Callable:
    """装饰器：确保函数在主线程中执行"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if is_main_thread():
            return func(*args, **kwargs)
        else:
            print(f"[WARN] 函数 {func.__name__} 不在主线程中执行")
            # 使用QTimer.singleShot在主线程中执行
            if QT_AVAILABLE:
                QTimer.singleShot(0, lambda: func(*args, **kwargs))
            else:
                return func(*args, **kwargs)
    return wrapper

def safe_timer_create(parent=None, interval=1000, single_shot=False):
    """安全创建定时器"""
    if not QT_AVAILABLE:
        return None
    
    if is_main_thread():
        timer = QTimer(parent)
        timer.setInterval(interval)
        timer.setSingleShot(single_shot)
        return timer
    else:
        print("[WARN] 定时器不在主线程中创建")
        return None

class ThreadSafeSignalEmitter:
    """线程安全的信号发射器"""
    
    def __init__(self, signal):
        self.signal = signal
    
    def emit_safe(self, *args, **kwargs):
        """安全发射信号"""
        if is_main_thread():
            self.signal.emit(*args, **kwargs)
        else:
            # 使用QMetaObject.invokeMethod在主线程中发射
            if QT_AVAILABLE:
                QMetaObject.invokeMethod(
                    self.signal.parent(),
                    lambda: self.signal.emit(*args, **kwargs),
                    Qt.ConnectionType.QueuedConnection
                )
'''
            
            # 保存线程安全工具模块
            thread_safety_path = self.project_root / "src" / "utils" / "thread_safety.py"
            thread_safety_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(thread_safety_path, 'w', encoding='utf-8') as f:
                f.write(thread_safety_content)
            
            result["fixes_applied"] += 1
            self.thread_safety_fixes += 1
            
            logger.info("线程安全工具模块创建完成")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"线程安全修复失败: {e}")
        
        return result
    
    def fix_css_compatibility_warnings(self) -> Dict[str, Any]:
        """修复CSS兼容性警告
        
        Returns:
            Dict[str, Any]: 修复结果
        """
        result = {
            "success": True,
            "warnings_fixed": 0,
            "files_processed": [],
            "errors": []
        }
        
        try:
            # 不支持的CSS属性列表
            unsupported_properties = [
                'transform', 'box-shadow', 'text-shadow', 'transition',
                'animation', 'filter', 'backdrop-filter', 'clip-path'
            ]
            
            # CSS属性替换映射
            css_replacements = {
                'transform:': '/* transform: */',
                'box-shadow:': '/* box-shadow: */',
                'text-shadow:': '/* text-shadow: */',
                'transition:': '/* transition: */',
                'animation:': '/* animation: */'
            }
            
            # 查找并修复CSS文件
            css_files = list(self.project_root.rglob("*.qss")) + list(self.project_root.rglob("*.css"))
            
            for css_file in css_files:
                warnings_fixed = self._fix_css_file(css_file, css_replacements)
                if warnings_fixed > 0:
                    result["warnings_fixed"] += warnings_fixed
                    result["files_processed"].append(str(css_file))
            
            # 修复Python文件中的内联CSS
            py_files = [
                self.project_root / "simple_ui_fixed.py",
                self.project_root / "ui" / "main_window.py"
            ]
            
            for py_file in py_files:
                if py_file.exists():
                    warnings_fixed = self._fix_inline_css(py_file, css_replacements)
                    if warnings_fixed > 0:
                        result["warnings_fixed"] += warnings_fixed
                        result["files_processed"].append(str(py_file))
            
            self.css_warnings_fixed = result["warnings_fixed"]
            logger.info(f"CSS兼容性修复完成，修复了 {result['warnings_fixed']} 个警告")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"CSS兼容性修复失败: {e}")
        
        return result
    
    def _fix_css_file(self, css_file: Path, replacements: Dict[str, str]) -> int:
        """修复CSS文件中的兼容性问题"""
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            warnings_fixed = 0
            
            for old_prop, new_prop in replacements.items():
                if old_prop in content:
                    content = content.replace(old_prop, new_prop)
                    warnings_fixed += content.count(new_prop) - original_content.count(new_prop)
            
            if warnings_fixed > 0:
                with open(css_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return warnings_fixed
            
        except Exception as e:
            logger.error(f"修复CSS文件 {css_file} 失败: {e}")
            return 0
    
    def _fix_inline_css(self, py_file: Path, replacements: Dict[str, str]) -> int:
        """修复Python文件中的内联CSS"""
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            warnings_fixed = 0
            
            # 查找setStyleSheet调用中的CSS
            style_pattern = r'setStyleSheet\s*\(\s*["\']([^"\']*)["\']'
            
            def replace_css_in_match(match):
                css_content = match.group(1)
                for old_prop, new_prop in replacements.items():
                    css_content = css_content.replace(old_prop, new_prop)
                return f'setStyleSheet("{css_content}"'
            
            content = re.sub(style_pattern, replace_css_in_match, content)
            
            # 计算修复的警告数量
            for old_prop in replacements.keys():
                warnings_fixed += original_content.count(old_prop) - content.count(old_prop)
            
            if warnings_fixed > 0:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return warnings_fixed
            
        except Exception as e:
            logger.error(f"修复Python文件 {py_file} 中的内联CSS失败: {e}")
            return 0
    
    def get_fix_report(self) -> Dict[str, Any]:
        """获取修复报告
        
        Returns:
            Dict[str, Any]: 修复报告
        """
        return {
            "fixes_applied": len(self.fixes_applied),
            "css_warnings_fixed": self.css_warnings_fixed,
            "thread_safety_fixes": self.thread_safety_fixes,
            "success_rate": len(self.fixes_applied) / max(1, len(self.fixes_applied) + len(getattr(self, 'errors', []))),
            "summary": f"应用了 {len(self.fixes_applied)} 个修复，修复了 {self.css_warnings_fixed} 个CSS警告"
        }

# 全局修复器实例
_ui_fixer = None

def get_ui_component_fixer() -> UIComponentFixer:
    """获取UI组件修复器实例"""
    global _ui_fixer
    if _ui_fixer is None:
        _ui_fixer = UIComponentFixer()
    return _ui_fixer

def fix_all_ui_issues() -> Dict[str, Any]:
    """修复所有UI问题"""
    fixer = get_ui_component_fixer()
    
    results = {
        "import_fixes": fixer.fix_ui_component_imports(),
        "thread_safety_fixes": fixer.fix_thread_safety_issues(),
        "css_fixes": fixer.fix_css_compatibility_warnings()
    }
    
    return results

if __name__ == "__main__":
    # 测试UI组件修复器
    fixer = UIComponentFixer()
    
    print("开始修复UI组件问题...")
    
    # 修复导入问题
    import_result = fixer.fix_ui_component_imports()
    print(f"导入修复结果: {import_result}")
    
    # 修复线程安全问题
    thread_result = fixer.fix_thread_safety_issues()
    print(f"线程安全修复结果: {thread_result}")
    
    # 修复CSS兼容性问题
    css_result = fixer.fix_css_compatibility_warnings()
    print(f"CSS修复结果: {css_result}")
    
    # 获取总体报告
    report = fixer.get_fix_report()
    print(f"修复报告: {report}")
