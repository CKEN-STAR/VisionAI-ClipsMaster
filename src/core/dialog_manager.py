#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全局单例对话框管理器
彻底解决重复弹窗问题
"""

import time
import threading
from typing import Optional, Dict, Any
from loguru import logger


class DialogManager:
    """全局单例对话框管理器 - 彻底解决重复弹窗问题"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._active_dialogs: Dict[str, Dict[str, Any]] = {}
            self._dialog_lock = threading.Lock()
            logger.info("🔧 全局对话框管理器初始化完成")
    
    @classmethod
    def get_instance(cls) -> 'DialogManager':
        """获取单例实例"""
        return cls()
    
    def can_show_dialog(self, model_name: str, parent_widget, tab_context: str = None) -> bool:
        """检查是否可以显示对话框 - 重构版本，确保100%可靠性"""
        with self._dialog_lock:
            current_time = time.time()

            # 🔧 彻底重构：构建唯一的对话框标识，包含时间戳确保唯一性
            base_dialog_id = f"{model_name}_{tab_context or 'default'}"
            dialog_id = f"{base_dialog_id}_{int(current_time * 1000)}"  # 添加毫秒时间戳

            logger.info(f"🔍 检查对话框权限: model={model_name}, tab={tab_context}, id={dialog_id}")

            # 🔧 彻底重构：强制清理所有相关的旧记录，确保不会有冲突
            self._force_cleanup_related_dialogs(base_dialog_id)

            # 🔧 彻底重构：只检查真正的模态对话框冲突，不依赖内部状态
            if self._has_real_modal_conflict():
                logger.warning("⚠️ 检测到真实的模态对话框冲突，暂时阻止弹窗")
                return False

            # 🔧 彻底重构：记录新的对话框，使用简化的状态管理
            self._active_dialogs[dialog_id] = {
                'model_name': model_name,
                'tab_context': tab_context,
                'parent_widget': parent_widget,
                'start_time': current_time,
                'status': 'active',
                'base_id': base_dialog_id
            }

            logger.info(f"✅ 允许显示对话框: {dialog_id}")
            return True
    
    def mark_dialog_closed(self, model_name: str, tab_context: str = None, result: str = 'unknown'):
        """标记对话框已关闭 - 重构版本，立即清理确保不会阻塞后续操作"""
        with self._dialog_lock:
            base_dialog_id = f"{model_name}_{tab_context or 'default'}"

            # 🔧 彻底重构：立即清理所有相关的对话框记录，不延迟
            closed_dialogs = []
            for dialog_id, dialog_info in list(self._active_dialogs.items()):
                if dialog_info.get('base_id') == base_dialog_id or dialog_id.startswith(base_dialog_id):
                    closed_dialogs.append(dialog_id)

            for dialog_id in closed_dialogs:
                if dialog_id in self._active_dialogs:
                    del self._active_dialogs[dialog_id]
                    logger.info(f"✅ 立即清理对话框记录: {dialog_id}")

            logger.info(f"✅ 对话框关闭处理完成: {base_dialog_id}, 清理了 {len(closed_dialogs)} 个记录, 结果: {result}")
    
    def _is_dialog_still_active(self, dialog_info: Dict[str, Any]) -> bool:
        """检查对话框是否仍然活跃"""
        current_time = time.time()
        start_time = dialog_info.get('start_time', 0)
        status = dialog_info.get('status', 'unknown')

        # 如果对话框已标记为关闭，则不活跃
        if status == 'closed':
            return False

        # 如果对话框显示超过30秒，认为可能有问题，清理它
        if current_time - start_time > 30:
            logger.warning(f"⚠️ 对话框显示时间过长，可能存在问题，强制清理")
            return False

        # 如果刚刚创建（小于0.1秒），认为仍然活跃
        if current_time - start_time < 0.1:
            return True

        # 检查父窗口是否还存在对话框实例
        parent_widget = dialog_info.get('parent_widget')
        if parent_widget and hasattr(parent_widget, '_dialog_instance'):
            if parent_widget._dialog_instance is not None:
                return True

        return False
    
    def _has_active_modal_dialog(self) -> bool:
        """检查是否有活跃的模态对话框"""
        try:
            from PyQt6.QtWidgets import QApplication
            active_modal_widget = QApplication.activeModalWidget()

            # 🔧 修复：更精确的模态对话框检查
            if active_modal_widget is None:
                return False

            # 🔧 修复：检查是否是我们自己的下载对话框
            # 如果是我们自己的对话框类型，允许显示新的对话框
            widget_class_name = active_modal_widget.__class__.__name__
            if widget_class_name in ['EnhancedDownloadDialog', 'QMessageBox']:
                # 检查对话框是否真的还在显示
                if hasattr(active_modal_widget, 'isVisible') and not active_modal_widget.isVisible():
                    logger.info(f"🔧 检测到隐藏的模态对话框 {widget_class_name}，允许新对话框")
                    return False

                # 检查对话框是否已经完成
                if hasattr(active_modal_widget, '_dialog_finished') and active_modal_widget._dialog_finished:
                    logger.info(f"🔧 检测到已完成的模态对话框 {widget_class_name}，允许新对话框")
                    return False

                logger.info(f"⚠️ 检测到活跃的模态对话框: {widget_class_name}")
                return True

            # 对于其他类型的模态对话框，保持原有逻辑
            logger.info(f"⚠️ 检测到其他类型的模态对话框: {widget_class_name}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ 检查模态对话框失败: {e}")
            # 🔧 修复：出现异常时，默认允许显示对话框，避免阻塞
            return False
    
    def _force_cleanup_related_dialogs(self, base_dialog_id: str):
        """强制清理所有相关的对话框记录，确保不会有冲突"""
        expired_dialogs = []

        for dialog_id, dialog_info in self._active_dialogs.items():
            # 清理所有相同base_id的对话框
            if dialog_info.get('base_id') == base_dialog_id:
                expired_dialogs.append(dialog_id)
            # 清理所有超过5秒的对话框（防止僵尸对话框）
            elif time.time() - dialog_info.get('start_time', 0) > 5:
                expired_dialogs.append(dialog_id)

        for dialog_id in expired_dialogs:
            del self._active_dialogs[dialog_id]
            logger.info(f"🗑️ 强制清理相关对话框: {dialog_id}")

    def _has_real_modal_conflict(self) -> bool:
        """检查是否有真实的模态对话框冲突"""
        try:
            from PyQt6.QtWidgets import QApplication
            active_modal_widget = QApplication.activeModalWidget()

            if active_modal_widget is None:
                return False

            # 只有当模态对话框真的可见且活跃时才认为有冲突
            if hasattr(active_modal_widget, 'isVisible') and active_modal_widget.isVisible():
                widget_class_name = active_modal_widget.__class__.__name__
                logger.info(f"🔍 检测到活跃的模态对话框: {widget_class_name}")

                # 如果是我们自己的下载对话框，检查是否真的在使用中
                if widget_class_name == 'EnhancedDownloadDialog':
                    # 检查对话框是否标记为已完成
                    if hasattr(active_modal_widget, '_dialog_finished') and active_modal_widget._dialog_finished:
                        logger.info("🔧 检测到已完成的下载对话框，允许新对话框")
                        return False

                    logger.info("⚠️ 检测到活跃的下载对话框，暂时阻止")
                    return True

                # 对于其他类型的模态对话框，也要检查是否真的活跃
                logger.info(f"⚠️ 检测到其他模态对话框: {widget_class_name}")
                return True

            return False

        except Exception as e:
            logger.warning(f"⚠️ 检查模态对话框失败: {e}")
            # 出现异常时，默认允许显示对话框
            return False

    def _cleanup_expired_dialogs(self):
        """清理所有过期的对话框记录（兼容性方法）"""
        current_time = time.time()
        expired_dialogs = []

        for dialog_id, dialog_info in self._active_dialogs.items():
            if current_time - dialog_info.get('start_time', 0) > 10:  # 10秒超时
                expired_dialogs.append(dialog_id)

        for dialog_id in expired_dialogs:
            del self._active_dialogs[dialog_id]
            logger.info(f"🗑️ 清理过期对话框: {dialog_id}")

    def _has_conflicting_modal_dialog(self, model_name: str, tab_context: str = None) -> bool:
        """检查是否有冲突的模态对话框"""
        try:
            from PyQt6.QtWidgets import QApplication
            active_modal_widget = QApplication.activeModalWidget()

            if active_modal_widget is None:
                return False

            # 检查是否是我们自己的下载对话框
            widget_class_name = active_modal_widget.__class__.__name__

            # 如果是下载对话框，检查是否真的在显示
            if widget_class_name == 'EnhancedDownloadDialog':
                if hasattr(active_modal_widget, 'isVisible') and active_modal_widget.isVisible():
                    # 检查是否是相同的模型和上下文
                    if hasattr(active_modal_widget, '_model_name') and hasattr(active_modal_widget, '_tab_context'):
                        if (active_modal_widget._model_name == model_name and
                            active_modal_widget._tab_context == tab_context):
                            logger.info(f"🔧 检测到相同的对话框正在显示，阻止重复")
                            return True

                    logger.info(f"🔧 检测到不同的下载对话框，允许新对话框")
                    return False
                else:
                    logger.info(f"🔧 检测到隐藏的下载对话框，允许新对话框")
                    return False

            # 对于其他类型的模态对话框，检查是否真的活跃
            if hasattr(active_modal_widget, 'isVisible') and not active_modal_widget.isVisible():
                return False

            # 只有真正活跃的非下载对话框才阻止
            logger.info(f"⚠️ 检测到活跃的模态对话框: {widget_class_name}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ 检查冲突对话框失败: {e}")
            return False

    def cleanup_expired_dialogs(self):
        """清理过期的对话框记录（兼容性方法）"""
        self._cleanup_expired_dialogs()

    def force_cleanup_all(self):
        """强制清理所有对话框记录"""
        with self._dialog_lock:
            count = len(self._active_dialogs)
            self._active_dialogs.clear()
            logger.info(f"🗑️ 强制清理了 {count} 个对话框记录")
    
    def get_active_dialogs(self) -> Dict[str, Dict[str, Any]]:
        """获取当前活跃的对话框列表（用于调试）"""
        with self._dialog_lock:
            return self._active_dialogs.copy()
    
    def __repr__(self):
        return f"DialogManager(active_dialogs={len(self._active_dialogs)})"
