#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工作流程进度设置对话框

提供工作流程进度显示的开关和功能介绍。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QPushButton, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class WorkflowSettingsDialog(QDialog):
    """工作流程进度设置对话框"""
    
    def __init__(self, parent=None, current_enabled=True):
        """初始化对话框
        
        Args:
            parent: 父窗口
            current_enabled: 当前是否启用工作流程进度显示
        """
        super().__init__(parent)
        self.enabled = current_enabled
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("工作流程进度设置")
        self.resize(600, 500)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("🔄 工作流程进度显示设置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 开关设置
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()
        
        self.enable_checkbox = QCheckBox("启用工作流程进度显示")
        self.enable_checkbox.setChecked(self.enabled)
        self.enable_checkbox.setToolTip("勾选后,生成视频时将显示详细的7步工作流程进度")
        settings_layout.addWidget(self.enable_checkbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 功能介绍
        intro_group = QGroupBox("功能介绍")
        intro_layout = QVBoxLayout()
        
        intro_text = QTextEdit()
        intro_text.setReadOnly(True)
        intro_text.setHtml("""
        <h3>工作流程进度显示功能</h3>
        
        <h4>功能概述</h4>
        <p>启用此功能后,在生成混剪视频时,系统会显示一个详细的进度对话框,实时展示7步工作流程的执行情况。</p>
        
        <h4>7步工作流程</h4>
        <ol>
            <li><b>1️⃣ 输入验证</b> - 验证视频和字幕文件的有效性</li>
            <li><b>2️⃣ 语言检测</b> - 自动检测字幕文件的语言(中文/英文)</li>
            <li><b>3️⃣ 字幕解析</b> - 解析字幕文件的结构和时间轴</li>
            <li><b>4️⃣ 剧情分析</b> - 分析叙事结构、节奏和情感曲线</li>
            <li><b>5️⃣ 剧本重构</b> - 重构剧本,生成爆款风格的新字幕</li>
            <li><b>6️⃣ 视频生成</b> - 根据新字幕自动剪辑和拼接视频片段</li>
            <li><b>7️⃣ 导出工程</b> - 导出剪映工程文件,支持二次编辑</li>
        </ol>
        
        <h4>用户价值</h4>
        <ul>
            <li><b>可视化工作流程</b> - 清楚看到每个处理步骤的执行情况</li>
            <li><b>实时进度反馈</b> - 不再是黑盒处理,提升用户体验</li>
            <li><b>错误定位</b> - 出错时可以快速定位到具体步骤</li>
            <li><b>日志记录</b> - 完整的处理日志便于问题排查</li>
        </ul>
        
        <h4>进度对话框特性</h4>
        <ul>
            <li><b>美观的UI设计</b> - 渐变进度条、步骤状态指示器</li>
            <li><b>实时日志输出</b> - 显示每个步骤的详细执行信息</li>
            <li><b>支持取消操作</b> - 可以随时中断处理流程</li>
            <li><b>自动日志滚动</b> - 始终显示最新的日志信息</li>
        </ul>
        
        <h4>使用建议</h4>
        <ul>
            <li><b>首次使用</b> - 建议启用此功能,了解完整的处理流程</li>
            <li><b>调试问题</b> - 遇到处理失败时,启用此功能查看详细日志</li>
            <li><b>批量处理</b> - 如果需要批量处理多个视频,可以关闭此功能以提升效率</li>
            <li><b>性能影响</b> - 此功能对处理性能影响极小,可以放心使用</li>
        </ul>
        
        <h4>技术实现</h4>
        <p>工作流程进度显示基于 <b>WorkflowProgressDialog</b> 组件实现,该组件提供了:</p>
        <ul>
            <li>7步工作流程的状态管理</li>
            <li>实时进度更新机制</li>
            <li>日志收集和显示功能</li>
            <li>错误处理和回退机制</li>
        </ul>
        
        <p style="color: #666; font-style: italic; margin-top: 20px;">
        💡 提示: 此功能完全可选,不影响视频生成的核心功能。您可以根据个人喜好随时开启或关闭。
        </p>
        """)
        intro_layout.addWidget(intro_text)
        
        intro_group.setLayout(intro_layout)
        layout.addWidget(intro_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def is_enabled(self):
        """获取是否启用工作流程进度显示
        
        Returns:
            bool: True表示启用,False表示禁用
        """
        return self.enable_checkbox.isChecked()

