#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试主窗口导入问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def debug_main_window_import():
    """调试主窗口导入"""
    print("=" * 60)
    print("调试主窗口导入问题")
    print("=" * 60)
    
    # 1. 测试PyQt6直接导入
    print("1. 测试PyQt6直接导入...")
    try:
        from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                    QTabWidget, QMenuBar, QStatusBar, QToolBar,
                                    QAction, QLabel, QProgressBar, QSplitter,
                                    QApplication, QMessageBox)
        from PyQt6.QtCore import Qt, pyqtSignal, QTimer
        from PyQt6.QtGui import QFont, QIcon, QKeySequence
        print("✅ PyQt6所有组件导入成功")
    except ImportError as e:
        print(f"❌ PyQt6导入失败: {e}")
        return False
    
    # 2. 模拟主窗口模块的导入过程
    print("\n2. 模拟主窗口模块导入过程...")
    try:
        # 清除可能的缓存
        if 'src.ui.main_window' in sys.modules:
            del sys.modules['src.ui.main_window']
        
        # 重新导入
        import src.ui.main_window as main_window_module
        print(f"✅ 主窗口模块导入成功")
        print(f"   PYQT_AVAILABLE = {main_window_module.PYQT_AVAILABLE}")
        
        if not main_window_module.PYQT_AVAILABLE:
            print("❌ 主窗口模块检测到PyQt6不可用")
            
            # 尝试手动设置
            print("3. 尝试手动修复...")
            main_window_module.PYQT_AVAILABLE = True
            print(f"   修复后 PYQT_AVAILABLE = {main_window_module.PYQT_AVAILABLE}")
            
            # 测试MainWindow类
            try:
                MainWindow = main_window_module.MainWindow
                app = QApplication.instance() or QApplication([])
                window = MainWindow()
                print("✅ MainWindow实例化成功（手动修复后）")
                return True
            except Exception as e:
                print(f"❌ MainWindow实例化失败: {e}")
                return False
        else:
            # 测试MainWindow类
            try:
                MainWindow = main_window_module.MainWindow
                app = QApplication.instance() or QApplication([])
                window = MainWindow()
                print("✅ MainWindow实例化成功")
                return True
            except Exception as e:
                print(f"❌ MainWindow实例化失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 主窗口模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_fixed_main_window():
    """创建修复版的主窗口模块"""
    print("\n" + "=" * 60)
    print("创建修复版主窗口模块")
    print("=" * 60)
    
    # 读取原始文件
    original_file = Path("src/ui/main_window.py")
    if not original_file.exists():
        print("❌ 原始主窗口文件不存在")
        return False
    
    try:
        content = original_file.read_text(encoding='utf-8')
        
        # 修复PyQt6检测逻辑
        fixed_content = content.replace(
            """try:
    from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTabWidget, QMenuBar, QStatusBar, QToolBar,
                                QAction, QLabel, QProgressBar, QSplitter,
                                QApplication, QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon, QKeySequence
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False""",
            """# 强制设置PyQt6可用（已验证安装）
PYQT_AVAILABLE = True

try:
    from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTabWidget, QMenuBar, QStatusBar, QToolBar,
                                QAction, QLabel, QProgressBar, QSplitter,
                                QApplication, QMessageBox)
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QIcon, QKeySequence
    print("[DEBUG] PyQt6导入成功，PYQT_AVAILABLE = True")
except ImportError as e:
    print(f"[ERROR] PyQt6导入失败: {e}")
    PYQT_AVAILABLE = False"""
        )
        
        # 保存修复版本
        backup_file = Path("src/ui/main_window_backup.py")
        backup_file.write_text(content, encoding='utf-8')
        print(f"✅ 原始文件已备份到: {backup_file}")
        
        original_file.write_text(fixed_content, encoding='utf-8')
        print(f"✅ 修复版本已保存到: {original_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 主窗口导入调试工具")
    
    # 调试导入问题
    success = debug_main_window_import()
    
    if not success:
        print("\n尝试创建修复版本...")
        if create_fixed_main_window():
            print("\n重新测试修复版本...")
            # 清除模块缓存
            if 'src.ui.main_window' in sys.modules:
                del sys.modules['src.ui.main_window']
            
            # 重新测试
            success = debug_main_window_import()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 主窗口导入问题已解决")
    else:
        print("❌ 主窗口导入问题未解决")
    print("=" * 60)
