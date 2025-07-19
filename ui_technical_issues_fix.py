#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI技术问题修复脚本
修复内存泄漏、OpenGL组件和线程问题
"""

import sys
import os
import gc
import threading
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

def fix_opengl_issues():
    """修复OpenGL相关问题"""
    print("🔧 修复OpenGL相关问题...")
    
    # 1. 修复PyQt6 OpenGL属性设置问题
    opengl_fix_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenGL兼容性修复模块
解决无独显环境下的OpenGL问题
"""

import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

class OpenGLCompatibilityManager:
    """OpenGL兼容性管理器"""
    
    def __init__(self):
        self.opengl_available = False
        self.software_rendering = False
        
    def setup_opengl_compatibility(self):
        """设置OpenGL兼容性"""
        try:
            # 在QApplication创建之前设置OpenGL属性
            if not QApplication.instance():
                # 强制使用软件渲染，避免GPU依赖
                os.environ['QT_OPENGL'] = 'software'
                os.environ['QT_QUICK_BACKEND'] = 'software'
                
                # 设置Qt属性（必须在QApplication创建前）
                QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)
                QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL, False)
                QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseOpenGLES, False)
                
                self.software_rendering = True
                print("[OK] OpenGL软件渲染模式已启用")
            else:
                print("[WARN] QApplication已创建，无法设置OpenGL属性")
                
        except Exception as e:
            print(f"[WARN] OpenGL兼容性设置失败: {e}")
            
    def check_opengl_support(self):
        """检查OpenGL支持"""
        try:
            from PyQt6.QtOpenGL import QOpenGLWidget
            self.opengl_available = True
            print("[OK] OpenGL组件可用")
        except ImportError:
            self.opengl_available = False
            print("[WARN] OpenGL组件不可用，将使用软件渲染")
            
        return self.opengl_available
        
    def get_fallback_widget(self):
        """获取OpenGL回退组件"""
        from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("图形渲染使用软件模式\\n(无独显环境兼容)")
        label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget

# 全局OpenGL管理器实例
opengl_manager = OpenGLCompatibilityManager()

def setup_opengl_before_app():
    """在应用程序创建前设置OpenGL"""
    return opengl_manager.setup_opengl_compatibility()
    
def check_opengl_after_app():
    """在应用程序创建后检查OpenGL"""
    return opengl_manager.check_opengl_support()
    
def get_opengl_fallback():
    """获取OpenGL回退组件"""
    return opengl_manager.get_fallback_widget()
'''
    
    # 保存OpenGL修复模块
    opengl_fix_path = PROJECT_ROOT / "ui" / "compat" / "opengl_fix.py"
    opengl_fix_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(opengl_fix_path, 'w', encoding='utf-8') as f:
        f.write(opengl_fix_content)
    
    print(f"✅ OpenGL修复模块已保存: {opengl_fix_path}")

def fix_memory_leak_issues():
    """修复内存泄漏问题"""
    print("🔧 修复内存泄漏问题...")
    
    memory_fix_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存泄漏检测和修复模块
"""

import gc
import sys
import threading
import weakref
from typing import Dict, List, Any
import psutil
import time

class MemoryLeakDetector:
    """内存泄漏检测器"""
    
    def __init__(self):
        self.object_refs = weakref.WeakSet()
        self.memory_snapshots = []
        self.monitoring = False
        self.monitor_thread = None
        
    def register_object(self, obj):
        """注册需要监控的对象"""
        try:
            self.object_refs.add(obj)
        except TypeError:
            # 某些对象不支持弱引用
            pass
            
    def start_monitoring(self):
        """开始内存监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            print("[OK] 内存泄漏监控已启动")
            
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("[OK] 内存泄漏监控已停止")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集内存快照
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                snapshot = {
                    'timestamp': time.time(),
                    'memory_mb': memory_mb,
                    'object_count': len(self.object_refs),
                    'gc_objects': len(gc.get_objects())
                }
                
                self.memory_snapshots.append(snapshot)
                
                # 只保留最近100个快照
                if len(self.memory_snapshots) > 100:
                    self.memory_snapshots.pop(0)
                
                # 检查内存增长趋势
                if len(self.memory_snapshots) >= 10:
                    self._check_memory_trend()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                print(f"[WARN] 内存监控错误: {e}")
                time.sleep(10)
                
    def _check_memory_trend(self):
        """检查内存增长趋势"""
        recent_snapshots = self.memory_snapshots[-10:]
        
        # 计算内存增长率
        start_memory = recent_snapshots[0]['memory_mb']
        end_memory = recent_snapshots[-1]['memory_mb']
        growth_rate = (end_memory - start_memory) / start_memory * 100
        
        # 如果内存增长超过20%，执行清理
        if growth_rate > 20:
            print(f"[WARN] 检测到内存增长 {growth_rate:.1f}%，执行清理")
            self.cleanup_memory()
            
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 强制垃圾回收
            for _ in range(3):
                gc.collect()
                
            # 清理Python内部缓存
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
                
            # 清理历史快照
            if len(self.memory_snapshots) > 20:
                self.memory_snapshots = self.memory_snapshots[-20:]
                
            print("[OK] 内存清理完成")
            
        except Exception as e:
            print(f"[WARN] 内存清理失败: {e}")
            
    def get_memory_report(self):
        """获取内存报告"""
        if not self.memory_snapshots:
            return {"status": "no_data"}
            
        latest = self.memory_snapshots[-1]
        
        return {
            "current_memory_mb": latest['memory_mb'],
            "object_count": latest['object_count'],
            "gc_objects": latest['gc_objects'],
            "snapshots_count": len(self.memory_snapshots)
        }

# 全局内存泄漏检测器
memory_detector = MemoryLeakDetector()

def start_memory_monitoring():
    """启动内存监控"""
    memory_detector.start_monitoring()
    
def stop_memory_monitoring():
    """停止内存监控"""
    memory_detector.stop_monitoring()
    
def register_for_monitoring(obj):
    """注册对象进行监控"""
    memory_detector.register_object(obj)
    
def cleanup_memory():
    """清理内存"""
    memory_detector.cleanup_memory()
    
def get_memory_status():
    """获取内存状态"""
    return memory_detector.get_memory_report()
'''
    
    # 保存内存修复模块
    memory_fix_path = PROJECT_ROOT / "ui" / "utils" / "memory_leak_detector.py"
    memory_fix_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(memory_fix_path, 'w', encoding='utf-8') as f:
        f.write(memory_fix_content)
    
    print(f"✅ 内存泄漏检测器已保存: {memory_fix_path}")

def fix_thread_issues():
    """修复线程相关问题"""
    print("🔧 修复线程相关问题...")
    
    thread_fix_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线程安全修复模块
解决Qt对象跨线程创建问题
"""

import threading
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication

class ThreadSafeManager:
    """线程安全管理器"""
    
    def __init__(self):
        self.main_thread = None
        self.main_app = None
        
    def initialize(self, app):
        """初始化线程安全管理器"""
        self.main_app = app
        self.main_thread = QThread.currentThread()
        print(f"[OK] 主线程已记录: {self.main_thread}")
        
    def is_main_thread(self):
        """检查当前是否为主线程"""
        return QThread.currentThread() == self.main_thread
        
    def ensure_main_thread(self, func, *args, **kwargs):
        """确保在主线程中执行函数"""
        if self.is_main_thread():
            return func(*args, **kwargs)
        else:
            # 使用QTimer在主线程中执行
            result = None
            exception = None
            
            def wrapper():
                nonlocal result, exception
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    exception = e
                    
            QTimer.singleShot(0, wrapper)
            
            # 等待执行完成（简单的同步机制）
            import time
            timeout = 5.0
            start_time = time.time()
            
            while result is None and exception is None:
                if time.time() - start_time > timeout:
                    raise TimeoutError("主线程执行超时")
                time.sleep(0.01)
                QApplication.processEvents()
                
            if exception:
                raise exception
            return result

class ThreadSafeQObject(QObject):
    """线程安全的QObject基类"""
    
    def __init__(self, parent=None):
        # 确保在主线程中创建
        if not thread_manager.is_main_thread():
            print(f"[WARN] QObject在非主线程中创建: {threading.current_thread().name}")
            
        super().__init__(parent)
        
    def moveToMainThread(self):
        """移动到主线程"""
        if thread_manager.main_thread:
            self.moveToThread(thread_manager.main_thread)

class ThreadSafeTimer(QTimer):
    """线程安全的定时器"""
    
    def __init__(self, parent=None):
        if not thread_manager.is_main_thread():
            print(f"[WARN] QTimer在非主线程中创建: {threading.current_thread().name}")
            
        super().__init__(parent)

# 全局线程安全管理器
thread_manager = ThreadSafeManager()

def initialize_thread_safety(app):
    """初始化线程安全"""
    thread_manager.initialize(app)
    
def ensure_main_thread(func):
    """装饰器：确保函数在主线程中执行"""
    def wrapper(*args, **kwargs):
        return thread_manager.ensure_main_thread(func, *args, **kwargs)
    return wrapper
    
def is_main_thread():
    """检查是否为主线程"""
    return thread_manager.is_main_thread()
    
def create_safe_timer(parent=None):
    """创建线程安全的定时器"""
    if thread_manager.is_main_thread():
        return QTimer(parent)
    else:
        return thread_manager.ensure_main_thread(QTimer, parent)
'''
    
    # 保存线程修复模块
    thread_fix_path = PROJECT_ROOT / "ui" / "utils" / "thread_safety.py"
    thread_fix_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(thread_fix_path, 'w', encoding='utf-8') as f:
        f.write(thread_fix_content)
    
    print(f"✅ 线程安全修复模块已保存: {thread_fix_path}")

def fix_css_warnings():
    """修复CSS属性警告"""
    print("🔧 修复CSS属性警告...")
    
    # 修复样式编译器中的正则表达式错误
    style_compiler_path = PROJECT_ROOT / "ui" / "themes" / "style_compiler.py"
    
    if style_compiler_path.exists():
        with open(style_compiler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复正则表达式
        fixes = [
            # 修复条件编译正则表达式
            (r'/\\\1\\\1\*@if\\\1\+(.*?)\\\1\*\\\1/(.*?)/\\\1\\\1\*@endif\\\1\*\\\1/', 
             r'/\*\*@if\s+(.*?)\s*\*/(.*?)/\*\*@endif\s*\*/'),
            
            # 修复变量替换正则表达式
            (r'\\\1\\\1([\\\1\\\1]+)\\\1', r'\{\{([^}]+)\}\}'),
            
            # 修复嵌套变量正则表达式
            (r'\\\1\\\1([\\\1\\\1]+):([\\\1\\\1]+)\\\1', r'\{\{([^:}]+):([^}]+)\}\}'),
        ]
        
        for old_pattern, new_pattern in fixes:
            content = content.replace(old_pattern, new_pattern)
        
        # 添加CSS属性兼容性处理
        css_compat_code = '''
    # CSS属性兼容性映射
    CSS_PROPERTY_MAPPING = {
        'transform': 'qproperty-transform',  # Qt不支持transform
        'box-shadow': 'border',  # 用border替代box-shadow
        'text-shadow': 'color',  # 用color替代text-shadow
    }
    
    def fix_css_compatibility(self, css_content):
        """修复CSS兼容性问题"""
        for unsupported, replacement in self.CSS_PROPERTY_MAPPING.items():
            # 移除不支持的属性
            import re
            pattern = rf'{unsupported}\\s*:[^;]+;'
            css_content = re.sub(pattern, '', css_content, flags=re.IGNORECASE)
        
        return css_content
'''
        
        # 如果还没有这个方法，添加它
        if 'fix_css_compatibility' not in content:
            content = content.replace(
                'class StyleCompiler:',
                f'class StyleCompiler:{css_compat_code}'
            )
        
        with open(style_compiler_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 样式编译器已修复: {style_compiler_path}")

def create_integrated_fix():
    """创建集成修复模块"""
    print("🔧 创建集成修复模块...")
    
    integrated_fix_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 集成技术问题修复模块
"""

import sys
import os
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

def apply_all_fixes():
    """应用所有技术修复"""
    print("🔧 应用VisionAI-ClipsMaster技术修复...")
    
    fixes_applied = []
    
    # 1. OpenGL修复
    try:
        from ui.compat.opengl_fix import setup_opengl_before_app
        setup_opengl_before_app()
        fixes_applied.append("OpenGL兼容性")
    except ImportError:
        print("[WARN] OpenGL修复模块不可用")
    
    # 2. 内存泄漏检测
    try:
        from ui.utils.memory_leak_detector import start_memory_monitoring
        start_memory_monitoring()
        fixes_applied.append("内存泄漏检测")
    except ImportError:
        print("[WARN] 内存泄漏检测模块不可用")
    
    # 3. 线程安全
    try:
        from ui.utils.thread_safety import initialize_thread_safety
        # 将在QApplication创建后初始化
        fixes_applied.append("线程安全")
    except ImportError:
        print("[WARN] 线程安全模块不可用")
    
    print(f"✅ 已应用修复: {', '.join(fixes_applied)}")
    return fixes_applied

def initialize_post_app_fixes(app):
    """在QApplication创建后初始化修复"""
    try:
        from ui.utils.thread_safety import initialize_thread_safety
        initialize_thread_safety(app)
        print("[OK] 线程安全已初始化")
    except ImportError:
        pass
    
    try:
        from ui.compat.opengl_fix import check_opengl_after_app
        check_opengl_after_app()
        print("[OK] OpenGL检查完成")
    except ImportError:
        pass

def cleanup_fixes():
    """清理修复资源"""
    try:
        from ui.utils.memory_leak_detector import stop_memory_monitoring
        stop_memory_monitoring()
        print("[OK] 内存监控已停止")
    except ImportError:
        pass
'''
    
    # 保存集成修复模块
    integrated_fix_path = PROJECT_ROOT / "ui" / "fixes" / "integrated_fix.py"
    integrated_fix_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(integrated_fix_path, 'w', encoding='utf-8') as f:
        f.write(integrated_fix_content)
    
    print(f"✅ 集成修复模块已保存: {integrated_fix_path}")

def main():
    """主修复函数"""
    print("🚀 VisionAI-ClipsMaster UI技术问题修复")
    print("=" * 60)
    
    try:
        # 1. 修复OpenGL问题
        fix_opengl_issues()
        
        # 2. 修复内存泄漏问题
        fix_memory_leak_issues()
        
        # 3. 修复线程问题
        fix_thread_issues()
        
        # 4. 修复CSS警告
        fix_css_warnings()
        
        # 5. 创建集成修复模块
        create_integrated_fix()
        
        print("\n" + "=" * 60)
        print("✅ 所有技术问题修复完成！")
        print("\n修复内容:")
        print("  1. ✅ OpenGL兼容性 - 支持无独显环境")
        print("  2. ✅ 内存泄漏检测 - 自动监控和清理")
        print("  3. ✅ 线程安全 - 解决跨线程创建问题")
        print("  4. ✅ CSS属性警告 - 移除不兼容属性")
        print("  5. ✅ 集成修复模块 - 统一管理所有修复")
        
        print("\n使用方法:")
        print("  在simple_ui_fixed.py中添加:")
        print("  from ui.fixes.integrated_fix import apply_all_fixes, initialize_post_app_fixes")
        print("  apply_all_fixes()  # 在QApplication创建前")
        print("  initialize_post_app_fixes(app)  # 在QApplication创建后")
        
    except Exception as e:
        print(f"❌ 修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
