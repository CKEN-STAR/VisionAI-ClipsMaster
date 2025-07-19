#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 用户体验增强器
包括操作预览、智能错误诊断、快捷键支持等功能
"""

import time
import json
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QTextEdit, QMessageBox, QProgressBar, QFrame
)
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
import weakref

class OperationPreview(QObject):
    """操作预览功能"""
    
    preview_requested = pyqtSignal(str, dict)  # 操作名称, 预览数据
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = weakref.ref(main_window)
        self.preview_cache = {}
        
    def show_operation_preview(self, operation_name, operation_data):
        """显示操作预览"""
        try:
            preview_dialog = OperationPreviewDialog(
                self.main_window(), operation_name, operation_data
            )
            return preview_dialog.exec()
            
        except Exception as e:
            print(f"[ERROR] 显示操作预览失败: {e}")
            return False
            
    def cache_preview_data(self, operation_name, data):
        """缓存预览数据"""
        self.preview_cache[operation_name] = {
            "data": data,
            "timestamp": time.time()
        }

class OperationPreviewDialog(QDialog):
    """操作预览对话框"""
    
    def __init__(self, parent, operation_name, operation_data):
        super().__init__(parent)
        self.operation_name = operation_name
        self.operation_data = operation_data
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"操作预览 - {self.operation_name}")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel(f"🔍 {self.operation_name} - 操作预览")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 预览内容
        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_content = self._generate_preview_content()
        preview_text.setPlainText(preview_content)
        layout.addWidget(preview_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("✅ 确认执行")
        confirm_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)
        
    def _generate_preview_content(self):
        """生成预览内容"""
        content = f"操作: {self.operation_name}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if isinstance(self.operation_data, dict):
            for key, value in self.operation_data.items():
                content += f"{key}: {value}\n"
        else:
            content += f"数据: {self.operation_data}\n"
            
        content += "\n⚠️ 请确认以上信息无误后点击'确认执行'"
        
        return content

class IntelligentErrorDiagnostic(QObject):
    """智能错误诊断器"""
    
    error_diagnosed = pyqtSignal(str, str, list)  # 错误类型, 诊断结果, 建议解决方案
    
    def __init__(self):
        super().__init__()
        self.error_patterns = {
            "ffmpeg": {
                "keywords": ["ffmpeg", "not found", "command not found"],
                "diagnosis": "FFmpeg未安装或路径配置错误",
                "solutions": [
                    "检查FFmpeg是否已安装",
                    "验证FFmpeg路径配置",
                    "重新下载并安装FFmpeg",
                    "检查系统环境变量"
                ]
            },
            "memory": {
                "keywords": ["memory", "内存", "out of memory", "内存不足"],
                "diagnosis": "系统内存不足",
                "solutions": [
                    "关闭其他不必要的应用程序",
                    "减少处理的文件数量",
                    "使用较小的视频文件进行测试",
                    "重启应用程序释放内存"
                ]
            },
            "file": {
                "keywords": ["file not found", "文件不存在", "permission denied", "权限"],
                "diagnosis": "文件访问问题",
                "solutions": [
                    "检查文件是否存在",
                    "验证文件路径是否正确",
                    "检查文件访问权限",
                    "确保文件未被其他程序占用"
                ]
            },
            "network": {
                "keywords": ["network", "网络", "connection", "timeout", "超时"],
                "diagnosis": "网络连接问题",
                "solutions": [
                    "检查网络连接状态",
                    "尝试重新连接网络",
                    "检查防火墙设置",
                    "使用离线模式"
                ]
            }
        }
        
    def diagnose_error(self, error_message):
        """诊断错误"""
        try:
            error_message_lower = error_message.lower()
            
            for error_type, pattern in self.error_patterns.items():
                for keyword in pattern["keywords"]:
                    if keyword.lower() in error_message_lower:
                        diagnosis = pattern["diagnosis"]
                        solutions = pattern["solutions"]
                        
                        self.error_diagnosed.emit(error_type, diagnosis, solutions)
                        return {
                            "type": error_type,
                            "diagnosis": diagnosis,
                            "solutions": solutions
                        }
                        
            # 未匹配到已知模式
            return {
                "type": "unknown",
                "diagnosis": "未知错误类型",
                "solutions": [
                    "查看详细错误日志",
                    "重启应用程序",
                    "联系技术支持"
                ]
            }
            
        except Exception as e:
            print(f"[ERROR] 错误诊断失败: {e}")
            return None
            
    def show_error_dialog(self, error_message, diagnosis_result=None):
        """显示错误诊断对话框"""
        try:
            if diagnosis_result is None:
                diagnosis_result = self.diagnose_error(error_message)
                
            dialog = ErrorDiagnosticDialog(None, error_message, diagnosis_result)
            dialog.exec()
            
        except Exception as e:
            print(f"[ERROR] 显示错误诊断对话框失败: {e}")

class ErrorDiagnosticDialog(QDialog):
    """错误诊断对话框"""
    
    def __init__(self, parent, error_message, diagnosis_result):
        super().__init__(parent)
        self.error_message = error_message
        self.diagnosis_result = diagnosis_result
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("🔧 智能错误诊断")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🚨 错误诊断报告")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dc3545; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 错误信息
        error_frame = QFrame()
        error_frame.setFrameStyle(QFrame.Shape.Box)
        error_frame.setStyleSheet("background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px;")
        
        error_layout = QVBoxLayout(error_frame)
        error_label = QLabel("错误信息:")
        error_label.setStyleSheet("font-weight: bold;")
        error_layout.addWidget(error_label)
        
        error_text = QLabel(self.error_message)
        error_text.setWordWrap(True)
        error_text.setStyleSheet("font-family: monospace; color: #721c24;")
        error_layout.addWidget(error_text)
        
        layout.addWidget(error_frame)
        
        # 诊断结果
        if self.diagnosis_result:
            diagnosis_frame = QFrame()
            diagnosis_frame.setFrameStyle(QFrame.Shape.Box)
            diagnosis_frame.setStyleSheet("background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 10px;")
            
            diagnosis_layout = QVBoxLayout(diagnosis_frame)
            
            diagnosis_label = QLabel("诊断结果:")
            diagnosis_label.setStyleSheet("font-weight: bold;")
            diagnosis_layout.addWidget(diagnosis_label)
            
            diagnosis_text = QLabel(self.diagnosis_result.get("diagnosis", "未知"))
            diagnosis_text.setWordWrap(True)
            diagnosis_text.setStyleSheet("color: #0c5460;")
            diagnosis_layout.addWidget(diagnosis_text)
            
            layout.addWidget(diagnosis_frame)
            
            # 解决方案
            solutions_frame = QFrame()
            solutions_frame.setFrameStyle(QFrame.Shape.Box)
            solutions_frame.setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb; padding: 10px;")
            
            solutions_layout = QVBoxLayout(solutions_frame)
            
            solutions_label = QLabel("建议解决方案:")
            solutions_label.setStyleSheet("font-weight: bold;")
            solutions_layout.addWidget(solutions_label)
            
            solutions = self.diagnosis_result.get("solutions", [])
            for i, solution in enumerate(solutions, 1):
                solution_text = QLabel(f"{i}. {solution}")
                solution_text.setWordWrap(True)
                solution_text.setStyleSheet("color: #155724; margin-left: 10px;")
                solutions_layout.addWidget(solution_text)
                
            layout.addWidget(solutions_frame)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

class ShortcutManager(QObject):
    """快捷键管理器"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = weakref.ref(main_window)
        self.shortcuts = {}
        
    def register_shortcuts(self):
        """注册快捷键"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QThread

            # 检查是否在主线程中
            app = QApplication.instance()
            if not app:
                print("[WARN] QApplication实例不存在，无法注册快捷键")
                return

            current_thread = QThread.currentThread()
            main_thread = app.thread()

            if current_thread != main_thread:
                print("[WARN] 不在主线程中，延迟注册快捷键")
                # 使用QTimer在主线程中执行
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self._register_shortcuts_in_main_thread)
                return

            self._register_shortcuts_in_main_thread()

        except Exception as e:
            print(f"[ERROR] 注册快捷键失败: {e}")

    def _register_shortcuts_in_main_thread(self):
        """在主线程中注册快捷键"""
        try:
            window = self.main_window()
            if not window:
                return

            # 定义快捷键
            shortcuts_config = {
                "Ctrl+O": ("打开文件", self._open_file),
                "Ctrl+S": ("保存项目", self._save_project),
                "Ctrl+E": ("导出视频", self._export_video),
                "F5": ("刷新状态", self._refresh_status),
                "Ctrl+1": ("切换到视频处理", lambda: self._switch_tab(0)),
                "Ctrl+2": ("切换到模型训练", lambda: self._switch_tab(1)),
                "Ctrl+3": ("切换到关于我们", lambda: self._switch_tab(2)),
                "Ctrl+4": ("切换到设置", lambda: self._switch_tab(3)),
                "F1": ("显示帮助", self._show_help),
                "Ctrl+Q": ("退出应用", window.close)
            }

            # 注册快捷键
            for key_sequence, (description, callback) in shortcuts_config.items():
                shortcut = QShortcut(QKeySequence(key_sequence), window)
                shortcut.activated.connect(callback)
                self.shortcuts[key_sequence] = {
                    "description": description,
                    "callback": callback,
                    "shortcut": shortcut
                }

            print(f"[OK] 已注册 {len(self.shortcuts)} 个快捷键")

        except Exception as e:
            print(f"[ERROR] 在主线程中注册快捷键失败: {e}")
            
    def _open_file(self):
        """打开文件快捷键"""
        window = self.main_window()
        if window and hasattr(window, 'select_video'):
            window.select_video()
            
    def _save_project(self):
        """保存项目快捷键"""
        print("[INFO] 保存项目功能暂未实现")
        
    def _export_video(self):
        """导出视频快捷键"""
        window = self.main_window()
        if window and hasattr(window, 'export_to_jianying'):
            window.export_to_jianying()
            
    def _refresh_status(self):
        """刷新状态快捷键"""
        window = self.main_window()
        if window and hasattr(window, 'check_models'):
            window.check_models()
            
    def _switch_tab(self, index):
        """切换标签页快捷键"""
        window = self.main_window()
        if window and hasattr(window, 'tabs'):
            window.tabs.setCurrentIndex(index)
            
    def _show_help(self):
        """显示帮助快捷键"""
        window = self.main_window()
        if window and hasattr(window, 'show_hotkey_guide'):
            window.show_hotkey_guide()
            
    def get_shortcuts_info(self):
        """获取快捷键信息"""
        return {
            key: info["description"] 
            for key, info in self.shortcuts.items()
        }

class UserGuide(QObject):
    """用户操作引导"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = weakref.ref(main_window)
        self.guide_steps = []
        self.current_step = 0
        
    def start_guide(self, guide_type="basic"):
        """开始用户引导"""
        try:
            if guide_type == "basic":
                self.guide_steps = [
                    {"title": "欢迎使用VisionAI-ClipsMaster", "content": "让我们开始您的第一个短剧混剪项目"},
                    {"title": "添加视频文件", "content": "点击'添加视频'按钮选择您的视频文件"},
                    {"title": "导入SRT字幕", "content": "点击'添加SRT'按钮导入字幕文件"},
                    {"title": "生成爆款SRT", "content": "点击'生成爆款SRT'开始AI处理"},
                    {"title": "导出项目", "content": "处理完成后，点击'导出到剪映'生成项目文件"}
                ]
            
            self.current_step = 0
            self._show_current_step()
            
        except Exception as e:
            print(f"[ERROR] 启动用户引导失败: {e}")
            
    def _show_current_step(self):
        """显示当前步骤"""
        if self.current_step < len(self.guide_steps):
            step = self.guide_steps[self.current_step]
            self._show_guide_dialog(step["title"], step["content"])
            
    def _show_guide_dialog(self, title, content):
        """显示引导对话框"""
        try:
            window = self.main_window()
            if not window:
                return
                
            dialog = QDialog(window)
            dialog.setWindowTitle("用户引导")
            dialog.setModal(True)
            dialog.resize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
            
            button_layout = QHBoxLayout()
            
            if self.current_step > 0:
                prev_btn = QPushButton("上一步")
                prev_btn.clicked.connect(lambda: self._navigate_step(-1))
                button_layout.addWidget(prev_btn)
                
            if self.current_step < len(self.guide_steps) - 1:
                next_btn = QPushButton("下一步")
                next_btn.clicked.connect(lambda: self._navigate_step(1))
                button_layout.addWidget(next_btn)
            else:
                finish_btn = QPushButton("完成")
                finish_btn.clicked.connect(dialog.accept)
                button_layout.addWidget(finish_btn)
                
            skip_btn = QPushButton("跳过引导")
            skip_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(skip_btn)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            print(f"[ERROR] 显示引导对话框失败: {e}")
            
    def _navigate_step(self, direction):
        """导航步骤"""
        self.current_step += direction
        if 0 <= self.current_step < len(self.guide_steps):
            self._show_current_step()

# 全局实例
operation_preview = None
error_diagnostic = IntelligentErrorDiagnostic()
shortcut_manager = None
user_guide = None

def initialize_user_experience_enhancer(main_window):
    """初始化用户体验增强器"""
    global operation_preview, shortcut_manager, user_guide
    
    operation_preview = OperationPreview(main_window)
    shortcut_manager = ShortcutManager(main_window)
    user_guide = UserGuide(main_window)
    
    # 注册快捷键
    shortcut_manager.register_shortcuts()
    
    print("[OK] 用户体验增强器初始化完成")
    
def show_operation_preview(operation_name, operation_data):
    """显示操作预览的全局接口"""
    if operation_preview:
        return operation_preview.show_operation_preview(operation_name, operation_data)
    return True

def diagnose_and_show_error(error_message):
    """诊断并显示错误的全局接口"""
    error_diagnostic.show_error_dialog(error_message)

def start_user_guide(guide_type="basic"):
    """启动用户引导的全局接口"""
    if user_guide:
        user_guide.start_guide(guide_type)

def get_shortcuts_info():
    """获取快捷键信息的全局接口"""
    if shortcut_manager:
        return shortcut_manager.get_shortcuts_info()
    return {}
