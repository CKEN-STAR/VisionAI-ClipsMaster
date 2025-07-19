#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 语言包热加载功能演示

此演示程序展示了语言包热加载功能，允许在不重启应用的情况下
实时更新语言资源文件并立即看到效果。
"""

import os
import sys
import json
import time
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QComboBox, QGroupBox,
    QFileDialog, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer

# 确保可以导入ui模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ui.i18n import (
        get_language_manager, get_available_languages,
        get_hot_reload_manager, create_language_file, 
        register_reload_callback
    )
except ImportError as e:
    print(f"无法导入国际化模块: {e}")
    sys.exit(1)


class HotReloadDemo(QMainWindow):
    """语言包热加载演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisionAI-ClipsMaster 语言包热加载演示")
        self.resize(800, 600)
        
        # 获取语言管理器
        self.language_manager = get_language_manager()
        
        # 获取热加载管理器
        self.hot_reload_manager = get_hot_reload_manager()
        
        # 设置UI
        self._setup_ui()
        
        # 注册语言重新加载回调
        register_reload_callback(self._on_language_reloaded)
        
        # 更新语言文件列表
        self._update_language_files_list()
        
        # 设置自动刷新定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._update_watched_files)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
        
    def _setup_ui(self):
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部状态区域
        status_layout = QHBoxLayout()
        self.status_label = QLabel("语言包热加载演示")
        status_layout.addWidget(self.status_label)
        
        # 语言选择下拉框
        self.language_combo = QComboBox()
        self._populate_language_combo()
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        status_layout.addWidget(self.language_combo)
        
        main_layout.addLayout(status_layout)
        
        # 标签页控件
        tab_widget = QTabWidget()
        
        # 语言文件管理标签页
        language_files_tab = self._create_language_files_tab()
        tab_widget.addTab(language_files_tab, "语言文件管理")
        
        # 监视文件标签页
        watched_files_tab = self._create_watched_files_tab()
        tab_widget.addTab(watched_files_tab, "监视文件")
        
        # 编辑器标签页
        editor_tab = self._create_editor_tab()
        tab_widget.addTab(editor_tab, "语言文件编辑器")
        
        main_layout.addWidget(tab_widget)
        
        # 底部信息区域
        info_group = QGroupBox("热加载工作原理")
        info_layout = QVBoxLayout(info_group)
        
        info_text = (
            "语言包热加载功能允许在不重启应用的情况下实时更新语言资源。"
            "\n\n工作流程："
            "\n1. 监视translations目录下的语言文件"
            "\n2. 当文件被修改时，自动重新加载"
            "\n3. 通知应用更新UI文本"
            "\n4. 自动备份修改前的文件"
            "\n\n您可以尝试修改或创建语言文件，修改后的内容将在3秒内自动应用。"
        )
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        main_layout.addWidget(info_group)
        
    def _create_language_files_tab(self):
        """创建语言文件管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 可用语言列表
        lang_group = QGroupBox("可用语言文件")
        lang_layout = QVBoxLayout(lang_group)
        
        self.language_files_list = QTextEdit()
        self.language_files_list.setReadOnly(True)
        lang_layout.addWidget(self.language_files_list)
        
        layout.addWidget(lang_group)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        create_button = QPushButton("创建新语言文件")
        create_button.clicked.connect(self._create_new_language_file)
        buttons_layout.addWidget(create_button)
        
        open_dir_button = QPushButton("打开语言文件目录")
        open_dir_button.clicked.connect(self._open_translations_dir)
        buttons_layout.addWidget(open_dir_button)
        
        refresh_button = QPushButton("刷新列表")
        refresh_button.clicked.connect(self._update_language_files_list)
        buttons_layout.addWidget(refresh_button)
        
        layout.addLayout(buttons_layout)
        
        return tab
        
    def _create_watched_files_tab(self):
        """创建监视文件标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 被监视的文件列表
        watch_group = QGroupBox("当前监视的文件")
        watch_layout = QVBoxLayout(watch_group)
        
        self.watched_files_list = QTextEdit()
        self.watched_files_list.setReadOnly(True)
        watch_layout.addWidget(self.watched_files_list)
        
        layout.addWidget(watch_group)
        
        # 热加载状态
        status_group = QGroupBox("热加载状态")
        status_layout = QVBoxLayout(status_group)
        
        self.hot_reload_status = QLabel("热加载功能已启用，等待文件变更...")
        status_layout.addWidget(self.hot_reload_status)
        
        self.last_reload_label = QLabel("最后重新加载: 无")
        status_layout.addWidget(self.last_reload_label)
        
        layout.addWidget(status_group)
        
        return tab
        
    def _create_editor_tab(self):
        """创建编辑器标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 语言文件选择
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("选择语言文件:"))
        
        self.file_combo = QComboBox()
        select_layout.addWidget(self.file_combo)
        
        load_button = QPushButton("加载")
        load_button.clicked.connect(self._load_language_file)
        select_layout.addWidget(load_button)
        
        layout.addLayout(select_layout)
        
        # 编辑器
        editor_group = QGroupBox("文件内容")
        editor_layout = QVBoxLayout(editor_group)
        
        self.editor = QTextEdit()
        editor_layout.addWidget(self.editor)
        
        layout.addWidget(editor_group)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_language_file)
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        
        # 更新文件下拉列表
        self._update_file_combo()
        
        return tab
    
    def _populate_language_combo(self):
        """填充语言选择下拉框"""
        available_languages = get_available_languages()
        
        # 添加自动检测选项
        self.language_combo.addItem("自动检测", "auto")
        
        # 添加可用语言
        for lang_code, lang_info in available_languages.items():
            self.language_combo.addItem(lang_info["native_name"], lang_code)
            
        # 设置当前语言
        current_lang = self.language_manager.get_current_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
    
    def _update_language_files_list(self):
        """更新语言文件列表"""
        translations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations"
        )
        
        text = f"语言文件目录: {translations_dir}\n\n"
        
        # 添加可用语言文件
        if os.path.exists(translations_dir):
            files = [f for f in os.listdir(translations_dir) 
                    if f.endswith(".json") or f.endswith(".qm")]
            
            if files:
                text += "可用语言文件:\n"
                for file in sorted(files):
                    file_path = os.path.join(translations_dir, file)
                    size = os.path.getsize(file_path)
                    mtime = time.strftime(
                        "%Y-%m-%d %H:%M:%S", 
                        time.localtime(os.path.getmtime(file_path))
                    )
                    text += f"- {file} ({size} 字节, 修改时间: {mtime})\n"
            else:
                text += "没有找到语言文件\n"
        else:
            text += f"语言文件目录不存在: {translations_dir}\n"
            
        self.language_files_list.setText(text)
        
        # 更新文件下拉列表
        self._update_file_combo()
    
    def _update_watched_files(self):
        """更新被监视的文件列表"""
        watched_files = self.hot_reload_manager.get_watched_files()
        
        text = f"当前监视的文件数量: {len(watched_files)}\n\n"
        
        if watched_files:
            for file in sorted(watched_files):
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    mtime = time.strftime(
                        "%Y-%m-%d %H:%M:%S", 
                        time.localtime(os.path.getmtime(file))
                    )
                    text += f"- {os.path.basename(file)} ({size} 字节, 修改时间: {mtime})\n"
                else:
                    text += f"- {file} (文件不存在)\n"
        else:
            text += "没有被监视的文件\n"
            
        self.watched_files_list.setText(text)
    
    def _update_file_combo(self):
        """更新文件下拉列表"""
        self.file_combo.clear()
        
        translations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations"
        )
        
        if os.path.exists(translations_dir):
            json_files = [f for f in os.listdir(translations_dir) if f.endswith(".json")]
            
            for file in sorted(json_files):
                self.file_combo.addItem(file)
    
    def _create_new_language_file(self):
        """创建新的语言文件"""
        available_languages = get_available_languages()
        
        # 构建已有语言代码与尚未创建文件的语言列表
        existing_files = []
        translations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations"
        )
        
        if os.path.exists(translations_dir):
            existing_files = [
                f[:-5] if f.endswith(".json") else f[:-3] 
                for f in os.listdir(translations_dir) 
                if f.endswith(".json") or f.endswith(".qm")
            ]
        
        # 过滤出尚未创建文件的语言
        missing_languages = {}
        for code, info in available_languages.items():
            if code not in existing_files:
                missing_languages[code] = info["native_name"]
        
        if not missing_languages:
            QMessageBox.information(
                self, "创建语言文件", 
                "所有支持的语言都已有对应的语言文件。"
            )
            return
            
        # 创建语言选择对话框
        language_dialog = QWidget(self, Qt.WindowType.Dialog)
        language_dialog.setWindowTitle("选择要创建的语言")
        dialog_layout = QVBoxLayout(language_dialog)
        
        dialog_layout.addWidget(QLabel("选择要创建语言文件的语言:"))
        
        language_select = QComboBox()
        for code, name in missing_languages.items():
            language_select.addItem(f"{name} ({code})", code)
            
        dialog_layout.addWidget(language_select)
        
        buttons_layout = QHBoxLayout()
        create_button = QPushButton("创建")
        cancel_button = QPushButton("取消")
        
        buttons_layout.addWidget(create_button)
        buttons_layout.addWidget(cancel_button)
        
        dialog_layout.addLayout(buttons_layout)
        
        # 设置按钮动作
        cancel_button.clicked.connect(language_dialog.close)
        
        def on_create():
            lang_code = language_select.currentData()
            file_path = create_language_file(lang_code)
            
            if file_path:
                QMessageBox.information(
                    self, "创建语言文件", 
                    f"已成功创建语言文件: {file_path}"
                )
                self._update_language_files_list()
            else:
                QMessageBox.warning(
                    self, "创建语言文件", 
                    f"创建语言文件失败"
                )
                
            language_dialog.close()
            
        create_button.clicked.connect(on_create)
        
        # 显示对话框
        language_dialog.setMinimumWidth(300)
        language_dialog.show()
    
    def _open_translations_dir(self):
        """打开语言文件目录"""
        translations_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations"
        )
        
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir, exist_ok=True)
            
        # 使用系统文件管理器打开目录
        import subprocess
        import platform
        
        system = platform.system()
        if system == 'Windows':
            os.startfile(translations_dir)
        elif system == 'Darwin':  # macOS
            subprocess.call(['open', translations_dir])
        else:  # Linux
            subprocess.call(['xdg-open', translations_dir])
    
    def _load_language_file(self):
        """加载语言文件到编辑器"""
        if self.file_combo.count() == 0:
            return
            
        filename = self.file_combo.currentText()
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations", 
            filename
        )
        
        if not os.path.exists(filepath):
            QMessageBox.warning(
                self, "加载语言文件", 
                f"文件不存在: {filepath}"
            )
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.editor.setText(content)
            self.status_label.setText(f"已加载: {filename}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "加载语言文件", 
                f"加载文件失败: {e}"
            )
    
    def _save_language_file(self):
        """保存编辑器内容到语言文件"""
        if self.file_combo.count() == 0:
            return
            
        filename = self.file_combo.currentText()
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ui", "i18n", "translations", 
            filename
        )
        
        # 验证JSON格式
        try:
            content = self.editor.toPlainText()
            json.loads(content)
        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, "保存语言文件", 
                f"JSON格式错误: {e}"
            )
            return
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.status_label.setText(f"已保存: {filename}")
            QMessageBox.information(
                self, "保存语言文件", 
                f"文件已保存。\n\n语言包热加载系统将在几秒内自动检测并应用更改。"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "保存语言文件", 
                f"保存文件失败: {e}"
            )
    
    def _on_language_changed(self, index):
        """当语言选择变更时触发"""
        if index < 0:
            return
            
        lang_code = self.language_combo.itemData(index)
        self.language_manager.set_language(lang_code)
        
        self.status_label.setText(f"当前语言: {self.language_combo.currentText()}")
    
    def _on_language_reloaded(self, lang):
        """当语言被重新加载时触发"""
        self.hot_reload_status.setText(f"热加载功能已启用，检测到语言包变更: {lang}")
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_reload_label.setText(f"最后重新加载: {current_time} (语言: {lang})")
        
        # 如果是当前语言，更新状态标签
        current_lang = self.language_manager.get_current_language()
        if lang == current_lang:
            self.status_label.setText(f"当前语言已重新加载: {self.language_combo.currentText()}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = HotReloadDemo()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 