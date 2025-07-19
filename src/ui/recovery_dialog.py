#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恢复对话框模块

提供中断恢复功能的用户界面组件，显示可恢复的任务并让用户选择如何处理。
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta

from loguru import logger

# 导入恢复管理器
from src.core.recovery_manager import get_recovery_manager, RecoveryPoint

# 尝试导入不同UI框架的支持
UI_FRAMEWORK = os.environ.get("VISIONAI_UI_FRAMEWORK", "console").lower()

if UI_FRAMEWORK == "pyqt":
    try:
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
            QListWidget, QListWidgetItem, QWidget, QApplication, QMessageBox
        )
        from PyQt5.QtCore import Qt, pyqtSignal
        from PyQt5.QtGui import QIcon
        
        UI_AVAILABLE = True
    except ImportError:
        logger.warning("未能导入PyQt5，将使用控制台界面")
        UI_AVAILABLE = False
elif UI_FRAMEWORK == "tkinter":
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        UI_AVAILABLE = True
    except ImportError:
        logger.warning("未能导入tkinter，将使用控制台界面")
        UI_AVAILABLE = False
else:
    # 默认使用控制台界面
    UI_AVAILABLE = False


class RecoveryUI:
    """恢复UI基类，定义通用接口"""
    
    def __init__(self):
        """初始化恢复UI"""
        self.recovery_manager = get_recovery_manager()
    
    def get_recoverable_tasks(self) -> List[Dict[str, Any]]:
        """
        获取可恢复的任务列表
        
        Returns:
            任务信息列表
        """
        try:
            tasks = self.recovery_manager.list_recoverable_tasks()
            
            # 添加相对时间表示
            for task in tasks:
                timestamp = task.get("timestamp")
                if timestamp:
                    try:
                        # 将ISO时间字符串转换为datetime对象
                        task_time = datetime.fromisoformat(timestamp)
                        now = datetime.now()
                        delta = now - task_time
                        
                        # 格式化相对时间
                        if delta < timedelta(minutes=1):
                            relative_time = "刚刚"
                        elif delta < timedelta(hours=1):
                            relative_time = f"{delta.seconds // 60}分钟前"
                        elif delta < timedelta(days=1):
                            relative_time = f"{delta.seconds // 3600}小时前"
                        else:
                            relative_time = f"{delta.days}天前"
                            
                        task["relative_time"] = relative_time
                    except Exception as e:
                        logger.error(f"格式化相对时间失败: {e}")
                        task["relative_time"] = "未知时间"
            
            return tasks
        except Exception as e:
            logger.error(f"获取可恢复任务列表失败: {e}")
            return []
    
    def show_recovery_dialog(self, 
                           on_resume: Optional[Callable[[str], None]] = None,
                           on_delete: Optional[Callable[[str], None]] = None,
                           on_cancel: Optional[Callable[[], None]] = None) -> bool:
        """
        显示恢复对话框，由子类实现
        
        Args:
            on_resume: 恢复任务回调函数
            on_delete: 删除任务回调函数
            on_cancel: 取消对话框回调函数
            
        Returns:
            是否显示对话框（如果没有可恢复的任务，则不显示）
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def resume_task(self, task_id: str) -> Optional[RecoveryPoint]:
        """
        恢复任务处理
        
        Args:
            task_id: 任务ID
            
        Returns:
            恢复点对象或None
        """
        try:
            recovery_point = self.recovery_manager.resume_task(task_id)
            if recovery_point:
                logger.info(f"已恢复任务: {task_id}")
                return recovery_point
            else:
                logger.error(f"恢复任务失败: {task_id}")
                return None
        except Exception as e:
            logger.error(f"恢复任务时出错: {e}")
            return None
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            success = self.recovery_manager.cleanup_task(task_id)
            if success:
                logger.info(f"已删除任务: {task_id}")
            else:
                logger.error(f"删除任务失败: {task_id}")
            return success
        except Exception as e:
            logger.error(f"删除任务时出错: {e}")
            return False


class PyQtRecoveryDialog(RecoveryUI):
    """PyQt实现的恢复对话框"""
    
    def __init__(self):
        """初始化PyQt恢复对话框"""
        super().__init__()
        self.app = QApplication.instance() or QApplication(sys.argv)
    
    def show_recovery_dialog(self, 
                           on_resume: Optional[Callable[[str], None]] = None,
                           on_delete: Optional[Callable[[str], None]] = None,
                           on_cancel: Optional[Callable[[], None]] = None) -> bool:
        """
        显示PyQt恢复对话框
        
        Args:
            on_resume: 恢复任务回调函数
            on_delete: 删除任务回调函数
            on_cancel: 取消对话框回调函数
            
        Returns:
            是否显示对话框
        """
        # 获取可恢复的任务
        tasks = self.get_recoverable_tasks()
        if not tasks:
            logger.info("没有可恢复的任务")
            return False
        
        # 创建对话框
        dialog = QDialog()
        dialog.setWindowTitle("恢复中断任务")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 顶部提示
        label = QLabel("检测到以下中断任务，是否要恢复?")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(label)
        
        # 任务列表
        task_list = QListWidget()
        for task in tasks:
            task_id = task.get("task_id", "未知任务")
            stage = task.get("stage", "未知阶段")
            progress = task.get("metadata", {}).get("progress", 0) * 100
            relative_time = task.get("relative_time", "未知时间")
            
            item = QListWidgetItem(f"{task_id} - {stage} ({progress:.1f}%) - {relative_time}")
            item.setData(Qt.UserRole, task_id)
            task_list.addItem(item)
        
        main_layout.addWidget(task_list)
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        
        resume_button = QPushButton("恢复选定任务")
        delete_button = QPushButton("删除选定任务")
        cancel_button = QPushButton("取消")
        
        buttons_layout.addWidget(resume_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        
        main_layout.addLayout(buttons_layout)
        
        dialog.setLayout(main_layout)
        
        # 绑定事件
        def on_resume_clicked():
            selected_items = task_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(dialog, "警告", "请选择要恢复的任务")
                return
                
            task_id = selected_items[0].data(Qt.UserRole)
            if on_resume:
                on_resume(task_id)
            else:
                self.resume_task(task_id)
            dialog.accept()
        
        def on_delete_clicked():
            selected_items = task_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(dialog, "警告", "请选择要删除的任务")
                return
                
            task_id = selected_items[0].data(Qt.UserRole)
            
            # 确认删除
            confirm = QMessageBox.question(
                dialog, 
                "确认删除", 
                f"确定要删除任务 {task_id} 吗？该操作不可撤销。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                if on_delete:
                    on_delete(task_id)
                else:
                    self.delete_task(task_id)
                dialog.accept()
        
        def on_cancel_clicked():
            if on_cancel:
                on_cancel()
            dialog.reject()
        
        resume_button.clicked.connect(on_resume_clicked)
        delete_button.clicked.connect(on_delete_clicked)
        cancel_button.clicked.connect(on_cancel_clicked)
        
        # 显示对话框
        result = dialog.exec_()
        return result == QDialog.Accepted


class TkinterRecoveryDialog(RecoveryUI):
    """Tkinter实现的恢复对话框"""
    
    def __init__(self):
        """初始化Tkinter恢复对话框"""
        super().__init__()
        self.root = None
    
    def show_recovery_dialog(self, 
                           on_resume: Optional[Callable[[str], None]] = None,
                           on_delete: Optional[Callable[[str], None]] = None,
                           on_cancel: Optional[Callable[[], None]] = None) -> bool:
        """
        显示Tkinter恢复对话框
        
        Args:
            on_resume: 恢复任务回调函数
            on_delete: 删除任务回调函数
            on_cancel: 取消对话框回调函数
            
        Returns:
            是否显示对话框
        """
        # 获取可恢复的任务
        tasks = self.get_recoverable_tasks()
        if not tasks:
            logger.info("没有可恢复的任务")
            return False
        
        # 保存返回值
        result = {"accepted": False}
        
        # 创建主窗口
        if self.root is None:
            self.root = tk.Tk()
        else:
            # 如果已经有root，创建一个Toplevel
            self.root = tk.Toplevel(self.root)
            
        self.root.title("恢复中断任务")
        self.root.geometry("500x300")
        
        # 顶部提示
        label = tk.Label(self.root, text="检测到以下中断任务，是否要恢复?", font=("", 12, "bold"))
        label.pack(pady=10)
        
        # 任务列表框架
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 任务列表
        task_list = tk.Listbox(frame, selectmode=tk.SINGLE)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=task_list.yview)
        task_list.config(yscrollcommand=scrollbar.set)
        
        task_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储任务ID
        task_ids = []
        
        # 添加任务
        for task in tasks:
            task_id = task.get("task_id", "未知任务")
            stage = task.get("stage", "未知阶段")
            progress = task.get("metadata", {}).get("progress", 0) * 100
            relative_time = task.get("relative_time", "未知时间")
            
            task_list.insert(tk.END, f"{task_id} - {stage} ({progress:.1f}%) - {relative_time}")
            task_ids.append(task_id)
        
        # 底部按钮
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_resume_clicked():
            selection = task_list.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要恢复的任务")
                return
                
            index = selection[0]
            task_id = task_ids[index]
            
            if on_resume:
                on_resume(task_id)
            else:
                self.resume_task(task_id)
                
            result["accepted"] = True
            self.root.destroy()
        
        def on_delete_clicked():
            selection = task_list.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择要删除的任务")
                return
                
            index = selection[0]
            task_id = task_ids[index]
            
            # 确认删除
            confirm = messagebox.askyesno(
                "确认删除", 
                f"确定要删除任务 {task_id} 吗？该操作不可撤销。"
            )
            
            if confirm:
                if on_delete:
                    on_delete(task_id)
                else:
                    self.delete_task(task_id)
                    
                result["accepted"] = True
                self.root.destroy()
        
        def on_cancel_clicked():
            if on_cancel:
                on_cancel()
            self.root.destroy()
        
        resume_button = tk.Button(buttons_frame, text="恢复选定任务", command=on_resume_clicked)
        delete_button = tk.Button(buttons_frame, text="删除选定任务", command=on_delete_clicked)
        cancel_button = tk.Button(buttons_frame, text="取消", command=on_cancel_clicked)
        
        resume_button.pack(side=tk.LEFT, padx=5)
        delete_button.pack(side=tk.LEFT, padx=5)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # 运行主循环
        self.root.protocol("WM_DELETE_WINDOW", on_cancel_clicked)
        self.root.mainloop()
        
        return result["accepted"]


class ConsoleRecoveryUI(RecoveryUI):
    """控制台实现的恢复UI"""
    
    def show_recovery_dialog(self, 
                           on_resume: Optional[Callable[[str], None]] = None,
                           on_delete: Optional[Callable[[str], None]] = None,
                           on_cancel: Optional[Callable[[], None]] = None) -> bool:
        """
        显示控制台恢复对话框
        
        Args:
            on_resume: 恢复任务回调函数
            on_delete: 删除任务回调函数
            on_cancel: 取消对话框回调函数
            
        Returns:
            是否显示对话框
        """
        # 获取可恢复的任务
        tasks = self.get_recoverable_tasks()
        if not tasks:
            logger.info("没有可恢复的任务")
            return False
        
        print("\n" + "=" * 60)
        print("检测到中断任务")
        print("=" * 60)
        
        # 显示任务列表
        for i, task in enumerate(tasks, 1):
            task_id = task.get("task_id", "未知任务")
            stage = task.get("stage", "未知阶段")
            progress = task.get("metadata", {}).get("progress", 0) * 100
            relative_time = task.get("relative_time", "未知时间")
            
            print(f"{i}. {task_id} - {stage} ({progress:.1f}%) - {relative_time}")
        
        print("\n请选择操作:")
        print("1. 恢复任务")
        print("2. 删除任务")
        print("0. 取消")
        
        while True:
            try:
                choice = input("请输入选项 [0-2]: ")
                if choice.strip() == "0":
                    if on_cancel:
                        on_cancel()
                    return False
                    
                elif choice.strip() == "1":
                    # 恢复任务
                    if len(tasks) == 1:
                        task_index = 0
                    else:
                        task_index = int(input(f"请选择要恢复的任务 [1-{len(tasks)}]: ")) - 1
                        if task_index < 0 or task_index >= len(tasks):
                            print("无效的任务编号")
                            continue
                    
                    task_id = tasks[task_index].get("task_id")
                    if on_resume:
                        on_resume(task_id)
                    else:
                        self.resume_task(task_id)
                    return True
                    
                elif choice.strip() == "2":
                    # 删除任务
                    if len(tasks) == 1:
                        task_index = 0
                    else:
                        task_index = int(input(f"请选择要删除的任务 [1-{len(tasks)}]: ")) - 1
                        if task_index < 0 or task_index >= len(tasks):
                            print("无效的任务编号")
                            continue
                    
                    task_id = tasks[task_index].get("task_id")
                    confirm = input(f"确定要删除任务 {task_id} 吗？该操作不可撤销。(y/n): ")
                    if confirm.lower() == "y":
                        if on_delete:
                            on_delete(task_id)
                        else:
                            self.delete_task(task_id)
                        return True
                
                else:
                    print("无效的选项，请重新输入")
            
            except ValueError:
                print("请输入有效的数字")
            except Exception as e:
                logger.error(f"处理输入时出错: {e}")
                return False


def get_recovery_ui() -> RecoveryUI:
    """
    获取合适的恢复UI实现
    
    Returns:
        RecoveryUI实例
    """
    if UI_FRAMEWORK == "pyqt" and UI_AVAILABLE:
        return PyQtRecoveryDialog()
    elif UI_FRAMEWORK == "tkinter" and UI_AVAILABLE:
        return TkinterRecoveryDialog()
    else:
        return ConsoleRecoveryUI()


def check_for_interrupted_tasks() -> bool:
    """
    检查是否有中断的任务
    
    Returns:
        是否有中断任务
    """
    recovery_ui = get_recovery_ui()
    tasks = recovery_ui.get_recoverable_tasks()
    return len(tasks) > 0


def show_recovery_dialog(on_resume: Optional[Callable[[str], None]] = None,
                         on_delete: Optional[Callable[[str], None]] = None,
                         on_cancel: Optional[Callable[[], None]] = None) -> bool:
    """
    显示恢复对话框
    
    Args:
        on_resume: 恢复任务回调函数
        on_delete: 删除任务回调函数
        on_cancel: 取消对话框回调函数
        
    Returns:
        用户是否选择了恢复或删除（True）或取消（False）
    """
    recovery_ui = get_recovery_ui()
    return recovery_ui.show_recovery_dialog(on_resume, on_delete, on_cancel)


if __name__ == "__main__":
    # 测试恢复对话框
    def on_resume_task(task_id):
        print(f"恢复任务: {task_id}")
        
    def on_delete_task(task_id):
        print(f"删除任务: {task_id}")
        
    def on_cancel_dialog():
        print("取消对话框")
    
    # 显示恢复对话框
    show_recovery_dialog(on_resume_task, on_delete_task, on_cancel_dialog) 