#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 简单UI语言资源集成

将语言资源管理器与SimpleScreenplayApp连接，使其支持多语言,
并整合动态翻译引擎实现上下文感知的翻译功能
"""

import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 导入PyQt
try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QMenu, QAction
    from PyQt5.QtCore import Qt, QObject, pyqtSignal
    HAS_QT = True
except ImportError:
    HAS_QT = False

# 导入资源管理器
try:
    from ui.resource_manager import get_resource_manager, get_text
    HAS_RESOURCE_MANAGER = True
except ImportError:
    HAS_RESOURCE_MANAGER = False

# 导入语言资源处理器
try:
    from ui.i18n.resource_handler import get_resource_handler, tr as handler_tr
    HAS_RESOURCE_HANDLER = True
except ImportError:
    HAS_RESOURCE_HANDLER = False

# 导入动态翻译引擎
try:
    from ui.i18n.translation_engine import get_translator, tr as dynamic_tr
    from ui.i18n.translation_integration import get_translation_integrator, setup_application_translation
    HAS_TRANSLATION_ENGINE = True
except ImportError:
    HAS_TRANSLATION_ENGINE = False

# 设置日志
logger = logging.getLogger(__name__)

# 定义统一的翻译函数
def tr(key, default=None, **kwargs):
    """统一的翻译函数，优先使用动态翻译引擎
    
    Args:
        key: 文本键名
        default: 默认文本
        **kwargs: 格式化参数
    
    Returns:
        str: 翻译后的文本
    """
    # 尝试用动态翻译引擎
    if HAS_TRANSLATION_ENGINE:
        try:
            # 分离上下文和键名
            parts = key.split('.')
            if len(parts) >= 2:
                context = parts[0]
                text_key = '.'.join(parts[1:])
                return dynamic_tr(context, text_key, **kwargs)
            else:
                return dynamic_tr("", key, **kwargs)
        except Exception as e:
            logger.debug(f"动态翻译失败: {str(e)}")
    
    # 回退到资源处理器
    if HAS_RESOURCE_HANDLER:
        try:
            text = handler_tr(key, default)
            
            # 应用格式化
            if kwargs and text != key and text != default:
                try:
                    text = text.format(**kwargs)
                except Exception:
                    pass
            
            return text
        except Exception as e:
            logger.debug(f"资源处理器翻译失败: {str(e)}")
    
    # 回退到资源管理器
    if HAS_RESOURCE_MANAGER:
        try:
            text = get_text(key)
            
            # 应用格式化
            if kwargs and text != key:
                try:
                    text = text.format(**kwargs)
                except Exception:
                    pass
            
            return text
        except Exception as e:
            logger.debug(f"资源管理器翻译失败: {str(e)}")
    
    # 使用默认文本或键名
    if default is not None:
        # 应用格式化
        if kwargs:
            try:
                return default.format(**kwargs)
            except Exception:
                pass
        return default
    
    return key

class SimpleUILanguageHelper:
    """Simple UI 语言辅助类，帮助简易UI界面实现多语言支持"""
    
    def __init__(self, main_window=None):
        """初始化语言辅助类
        
        Args:
            main_window: 主窗口实例，通常是SimpleScreenplayApp的实例
        """
        self.main_window = main_window
        self.resource_handler = None
        self.translator = None
        self.integrator = None
        
        # 尝试获取资源处理器
        if HAS_RESOURCE_HANDLER:
            try:
                self.resource_handler = get_resource_handler()
                logger.info("已连接语言资源处理器")
                
                # 连接信号
                if self.resource_handler:
                    self.resource_handler.resources_changed.connect(self.on_language_changed)
            except Exception as e:
                logger.error(f"连接语言资源处理器失败: {e}")
        
        # 尝试获取翻译引擎
        if HAS_TRANSLATION_ENGINE:
            try:
                self.translator = get_translator()
                self.integrator = get_translation_integrator()
                logger.info("已连接动态翻译引擎")
            except Exception as e:
                logger.error(f"连接动态翻译引擎失败: {e}")
        
        # 初始化主窗口中的语言菜单
        self.setup_language_menu()
    
    def setup_language_menu(self):
        """设置语言菜单"""
        if not self.main_window or not hasattr(self.main_window, 'menuBar'):
            return
        
        try:
            # 创建语言菜单
            menu_bar = self.main_window.menuBar()
            
            # 检查是否已存在语言菜单
            language_menu = None
            for action in menu_bar.actions():
                if action.text() == tr("language", "语言"):
                    language_menu = action.menu()
                    break
            
            # 如果不存在，创建新菜单
            if not language_menu:
                language_menu = QMenu(tr("language", "语言"), self.main_window)
                menu_bar.addMenu(language_menu)
            else:
                # 清空现有菜单
                language_menu.clear()
            
            # 获取可用语言
            languages = []
            if HAS_RESOURCE_MANAGER:
                try:
                    languages = get_resource_manager().get_available_languages()
                except Exception as e:
                    logger.error(f"获取可用语言失败: {e}")
            
            # 添加语言选项
            for lang in languages:
                lang_code = lang.get('code', '')
                lang_name = lang.get('native_name', lang_code)
                
                lang_action = QAction(lang_name, self.main_window)
                lang_action.setData(lang_code)
                lang_action.triggered.connect(lambda checked, lc=lang_code: self.change_language(lc))
                language_menu.addAction(lang_action)
        
        except Exception as e:
            logger.error(f"设置语言菜单失败: {e}")
    
    def change_language(self, language_code: str):
        """切换语言
        
        Args:
            language_code: 语言代码
        """
        if not HAS_RESOURCE_MANAGER:
            logger.warning("资源管理器不可用，无法切换语言")
            return
            
        try:
            # 设置语言
            get_resource_manager().set_language(language_code)
            
            # 同时更新翻译引擎的语言
            if HAS_TRANSLATION_ENGINE:
                self.translator.update_language(language_code)
            
            # 更新UI
            self.update_ui_texts()
            
            logger.info(f"已切换语言: {language_code}")
        except Exception as e:
            logger.error(f"切换语言失败: {e}")
    
    def on_language_changed(self, language_code: str):
        """语言变更处理
        
        Args:
            language_code: 语言代码
        """
        # 更新UI文本
        self.update_ui_texts()
    
    def update_ui_texts(self):
        """更新UI文本"""
        if not self.main_window:
            return
            
        try:
            # 更新窗口标题
            self.main_window.setWindowTitle(tr("app_title", "VisionAI-ClipsMaster"))
            
            # 更新菜单
            self._update_menus()
            
            # 更新状态栏
            if hasattr(self.main_window, 'statusBar') and callable(self.main_window.statusBar):
                status_bar = self.main_window.statusBar()
                if status_bar:
                    status_bar.showMessage(tr("ready", "就绪"))
            
            # 使用翻译集成器重新翻译UI
            if HAS_TRANSLATION_ENGINE and self.integrator:
                self.integrator.retranslate_ui(self.main_window)
            
            # 记录日志
            logger.info("UI文本已更新")
        except Exception as e:
            logger.error(f"更新UI文本失败: {e}")
    
    def _update_menus(self):
        """更新菜单文本"""
        if not hasattr(self.main_window, 'menuBar'):
            return
            
        try:
            menu_bar = self.main_window.menuBar()
            
            # 更新顶级菜单
            for action in menu_bar.actions():
                if action.text() == "文件" or action.text() == "File":
                    action.setText(tr("file", "文件"))
                elif action.text() == "编辑" or action.text() == "Edit":
                    action.setText(tr("edit", "编辑"))
                elif action.text() == "视图" or action.text() == "View":
                    action.setText(tr("view", "视图"))
                elif action.text() == "帮助" or action.text() == "Help":
                    action.setText(tr("help", "帮助"))
                elif action.text() == "语言" or action.text() == "Language":
                    action.setText(tr("language", "语言"))
                elif action.text() == "设置" or action.text() == "Settings":
                    action.setText(tr("settings", "设置"))
                
                # 更新子菜单
                if action.menu():
                    for sub_action in action.menu().actions():
                        self._update_action_text(sub_action)
        except Exception as e:
            logger.error(f"更新菜单文本失败: {e}")
    
    def _update_action_text(self, action):
        """更新动作文本
        
        Args:
            action: QAction实例
        """
        if not action:
            return
            
        # 常见菜单项的翻译
        common_actions = {
            "打开": "open_project",
            "Open": "open_project",
            "保存": "save_project",
            "Save": "save_project",
            "导入": "import",
            "Import": "import",
            "导出": "export",
            "Export": "export",
            "退出": "exit",
            "Exit": "exit",
            "设置": "settings",
            "Settings": "settings",
            "关于": "about",
            "About": "about",
        }
        
        # 查找匹配的键
        current_text = action.text()
        for key, value in common_actions.items():
            if current_text == key:
                action.setText(tr(value, current_text))
                break

def integrate_language_with_simple_ui(main_window) -> Optional[SimpleUILanguageHelper]:
    """将语言资源管理器集成到SimpleScreenplayApp
    
    Args:
        main_window: SimpleScreenplayApp实例
    
    Returns:
        Optional[SimpleUILanguageHelper]: 语言辅助类实例，如果集成失败则返回None
    """
    if not HAS_QT:
        logger.error("PyQt未安装，无法集成语言支持")
        return None
        
    if not main_window:
        logger.error("主窗口为空，无法集成语言支持")
        return None
    
    try:
        # 配置应用程序翻译
        if HAS_TRANSLATION_ENGINE:
            app = QApplication.instance()
            if app:
                setup_application_translation(app)
        
        # 创建语言辅助类
        helper = SimpleUILanguageHelper(main_window)
        
        # 初始更新UI文本
        helper.update_ui_texts()
        
        logger.info("已将语言资源集成到SimpleScreenplayApp")
        return helper
    except Exception as e:
        logger.error(f"集成语言支持失败: {e}")
        return None

# 测试代码
if __name__ == "__main__":
    # 测试环境
    app = QApplication(sys.argv)
    
    # 创建简单窗口
    window = QMainWindow()
    window.setWindowTitle("测试窗口")
    window.resize(800, 600)
    
    # 测试集成
    helper = SimpleUILanguageHelper(window)
    
    # 显示窗口
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())
