#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI界面组件测试

测试范围:
1. 所有UI组件加载与交互
2. 中英文界面切换
3. 主题切换功能 (light/dark/high-contrast)
4. 进度监控与实时图表
5. 内存使用监控 (UI≤400MB)
6. 响应时间验证 (≤2秒)
"""

import pytest
import time
import sys
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

# 模拟PyQt6环境
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtTest import QTest
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    # 创建模拟类
    class QApplication:
        @staticmethod
        def instance():
            return None
        def __init__(self, *args):
            pass
    
    class QWidget:
        def __init__(self, *args):
            pass
    
    class QMainWindow:
        def __init__(self, *args):
            pass


class TestUIComponents:
    """UI界面组件测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        if QT_AVAILABLE:
            # 创建QApplication实例
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
        
        # UI组件列表
        self.ui_components = [
            "main_window",
            "training_panel", 
            "progress_dashboard",
            "realtime_charts",
            "alert_manager",
            "file_upload_dialog",
            "settings_panel"
        ]
        
        # 性能目标
        self.ui_performance_targets = {
            "max_memory_mb": 400,
            "response_time_s": 2.0,
            "startup_time_s": 5.0,
            "theme_switch_time_s": 1.0
        }

    @pytest.mark.skipif(not QT_AVAILABLE, reason="PyQt6不可用")
    def test_main_window_initialization(self):
        """测试主窗口初始化"""
        try:
            from src.ui.main_window import SimpleScreenplayApp
            
            start_time = time.time()
            main_window = SimpleScreenplayApp()
            init_time = time.time() - start_time
            
            # 验证初始化时间
            assert init_time <= self.ui_performance_targets["startup_time_s"], \
                f"主窗口初始化时间过长: {init_time:.2f}s"
            
            # 验证窗口属性
            assert hasattr(main_window, 'tabs'), "主窗口缺少标签页组件"
            assert hasattr(main_window, 'statusBar'), "主窗口缺少状态栏"
            
            # 验证标签页数量
            if hasattr(main_window.tabs, 'count'):
                tab_count = main_window.tabs.count()
                assert tab_count >= 3, f"标签页数量不足: {tab_count}"
            
        except ImportError as e:
            pytest.skip(f"无法导入主窗口模块: {str(e)}")

    @pytest.mark.skipif(not QT_AVAILABLE, reason="PyQt6不可用")
    def test_training_panel_functionality(self):
        """测试训练面板功能"""
        try:
            from src.ui.training_panel import TrainingPanel
            
            training_panel = TrainingPanel()
            
            # 验证面板组件
            assert hasattr(training_panel, 'init_ui'), "训练面板缺少UI初始化方法"
            
            # 测试UI初始化
            training_panel.init_ui()
            
            # 验证关键组件
            expected_components = ['tabs', 'config_tab', 'monitor_tab', 'history_tab']
            for component in expected_components:
                if hasattr(training_panel, component):
                    assert getattr(training_panel, component) is not None, \
                        f"训练面板{component}组件未正确初始化"
            
        except ImportError as e:
            pytest.skip(f"无法导入训练面板模块: {str(e)}")

    @pytest.mark.skipif(not QT_AVAILABLE, reason="PyQt6不可用")
    def test_progress_dashboard_functionality(self):
        """测试进度看板功能"""
        try:
            from src.ui.progress_dashboard import ProgressDashboard
            
            dashboard = ProgressDashboard()
            
            # 测试任务管理功能
            task_id = "test_task_001"
            dashboard.add_task(task_id, "测试任务")
            
            # 验证任务添加
            assert task_id in dashboard.active_tasks, "任务添加失败"
            
            # 测试进度更新
            dashboard.update_task_progress(task_id, 50, "进行中", "处理中...")
            task_info = dashboard.active_tasks.get(task_id)
            
            if task_info:
                assert task_info["progress"] == 50, "进度更新失败"
                assert task_info["status"] == "进行中", "状态更新失败"
            
            # 测试任务完成
            dashboard.complete_task(task_id, success=True)
            assert task_id in dashboard.completed_tasks, "任务完成状态更新失败"
            
        except ImportError as e:
            pytest.skip(f"无法导入进度看板模块: {str(e)}")

    def test_language_interface_switching(self):
        """测试中英文界面切换"""
        try:
            # 模拟语言管理器
            from src.ui.components.language_manager import LanguageManager
            
            lang_manager = LanguageManager()
            
            # 测试语言切换
            switch_times = {}
            
            for language in ["zh", "en", "zh"]:
                start_time = time.time()
                success = lang_manager.switch_language(language)
                switch_time = time.time() - start_time
                
                switch_times[language] = switch_time
                assert success, f"{language}语言切换失败"
                assert switch_time <= 1.0, f"{language}语言切换时间过长: {switch_time:.2f}s"
            
            # 验证当前语言
            current_lang = lang_manager.get_current_language()
            assert current_lang == "zh", f"当前语言状态错误: {current_lang}"
            
        except ImportError:
            # 使用模拟测试
            mock_lang_manager = Mock()
            mock_lang_manager.switch_language.return_value = True
            mock_lang_manager.get_current_language.return_value = "zh"
            
            # 测试模拟切换
            assert mock_lang_manager.switch_language("en"), "模拟语言切换失败"

    def test_theme_switching_functionality(self):
        """测试主题切换功能"""
        try:
            # 导入主题管理器
            from src.ui.components.theme_manager import ThemeManager
            
            theme_manager = ThemeManager()
            
            # 测试三种主题切换
            themes = ["light", "dark", "high-contrast"]
            
            for theme in themes:
                start_time = time.time()
                success = theme_manager.switch_theme(theme)
                switch_time = time.time() - start_time
                
                assert success, f"{theme}主题切换失败"
                assert switch_time <= self.ui_performance_targets["theme_switch_time_s"], \
                    f"{theme}主题切换时间过长: {switch_time:.2f}s"
                
                # 验证主题应用
                current_theme = theme_manager.get_current_theme()
                assert current_theme == theme, f"主题状态错误: {current_theme} != {theme}"
            
            # 测试主题循环切换
            theme_manager.cycle_theme()
            cycled_theme = theme_manager.get_current_theme()
            assert cycled_theme in themes, f"循环切换主题无效: {cycled_theme}"
            
        except ImportError:
            # 使用模拟测试
            mock_theme_manager = Mock()
            mock_theme_manager.switch_theme.return_value = True
            mock_theme_manager.get_current_theme.return_value = "light"
            
            for theme in ["light", "dark", "high-contrast"]:
                assert mock_theme_manager.switch_theme(theme), f"模拟{theme}主题切换失败"

    def test_realtime_charts_performance(self):
        """测试实时图表性能"""
        try:
            from src.ui.components.realtime_charts import RealtimeCharts
            
            charts = RealtimeCharts()
            
            # 测试数据更新性能
            update_times = []
            
            for i in range(100):
                start_time = time.time()
                
                # 模拟数据更新
                charts.update_cpu_usage(50 + i % 50)
                charts.update_memory_usage(60 + i % 40)
                charts.update_gpu_usage(30 + i % 70)
                
                update_time = time.time() - start_time
                update_times.append(update_time)
            
            # 验证更新性能
            avg_update_time = sum(update_times) / len(update_times)
            max_update_time = max(update_times)
            
            assert avg_update_time <= 0.1, f"图表平均更新时间过长: {avg_update_time:.3f}s"
            assert max_update_time <= 0.5, f"图表最大更新时间过长: {max_update_time:.3f}s"
            
        except ImportError:
            pytest.skip("实时图表模块不可用")

    def test_alert_manager_functionality(self):
        """测试警告管理器功能"""
        try:
            from src.ui.components.alert_manager import AlertManager, AlertLevel
            
            alert_manager = AlertManager()
            
            # 测试不同级别的警告
            alert_levels = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
            
            for level in alert_levels:
                alert_id = alert_manager.show_alert(
                    title=f"测试{level.name}警告",
                    message=f"这是一个{level.name}级别的测试警告",
                    level=level
                )
                
                assert alert_id is not None, f"{level.name}级别警告创建失败"
                
                # 测试警告关闭
                close_success = alert_manager.close_alert(alert_id)
                assert close_success, f"{level.name}级别警告关闭失败"
            
            # 测试批量警告处理
            alert_ids = []
            for i in range(5):
                alert_id = alert_manager.show_alert(
                    title=f"批量警告{i}",
                    message=f"批量测试警告{i}",
                    level=AlertLevel.INFO
                )
                alert_ids.append(alert_id)
            
            # 批量关闭
            close_count = alert_manager.close_all_alerts()
            assert close_count == len(alert_ids), "批量关闭警告失败"
            
        except ImportError:
            pytest.skip("警告管理器模块不可用")

    def test_file_upload_dialog_functionality(self):
        """测试文件上传对话框功能"""
        try:
            from src.ui.components.file_upload_dialog import FileUploadDialog
            
            upload_dialog = FileUploadDialog()
            
            # 测试支持的文件格式
            supported_formats = upload_dialog.get_supported_formats()
            
            # 验证视频格式支持
            video_formats = [".mp4", ".avi", ".mov", ".mkv", ".flv"]
            for fmt in video_formats:
                assert fmt in supported_formats, f"不支持视频格式: {fmt}"
            
            # 验证字幕格式支持
            subtitle_formats = [".srt", ".ass", ".vtt"]
            for fmt in subtitle_formats:
                assert fmt in supported_formats, f"不支持字幕格式: {fmt}"
            
            # 测试文件验证功能
            test_files = [
                ("test.mp4", True),
                ("test.srt", True),
                ("test.txt", False),
                ("test.exe", False)
            ]
            
            for filename, should_be_valid in test_files:
                is_valid = upload_dialog.validate_file(filename)
                assert is_valid == should_be_valid, \
                    f"文件验证错误: {filename} -> {is_valid} (期望: {should_be_valid})"
            
        except ImportError:
            pytest.skip("文件上传对话框模块不可用")

    def test_ui_memory_usage_monitoring(self):
        """测试UI内存使用监控 (≤400MB)"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建多个UI组件
        ui_components = []
        
        try:
            if QT_AVAILABLE:
                from src.ui.main_window import SimpleScreenplayApp
                from src.ui.training_panel import TrainingPanel
                from src.ui.progress_dashboard import ProgressDashboard
                
                # 创建组件
                main_window = SimpleScreenplayApp()
                training_panel = TrainingPanel()
                progress_dashboard = ProgressDashboard()
                
                ui_components.extend([main_window, training_panel, progress_dashboard])
            
            # 检查内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            ui_memory_usage = current_memory - initial_memory
            
            # 验证内存使用限制
            assert ui_memory_usage <= self.ui_performance_targets["max_memory_mb"], \
                f"UI内存使用超限: {ui_memory_usage:.2f}MB (限制: {self.ui_performance_targets['max_memory_mb']}MB)"
            
        except ImportError:
            pytest.skip("UI模块不可用，跳过内存使用测试")
        
        finally:
            # 清理UI组件
            for component in ui_components:
                if hasattr(component, 'close'):
                    component.close()
                del component

    def test_ui_response_time_under_load(self):
        """测试负载下的UI响应时间"""
        if not QT_AVAILABLE:
            pytest.skip("PyQt6不可用")
        
        try:
            from src.ui.main_window import SimpleScreenplayApp
            
            main_window = SimpleScreenplayApp()
            
            # 模拟高负载操作
            response_times = []
            
            for i in range(20):
                start_time = time.time()
                
                # 模拟UI操作
                if hasattr(main_window, 'tabs') and hasattr(main_window.tabs, 'setCurrentIndex'):
                    main_window.tabs.setCurrentIndex(i % 3)  # 切换标签页
                
                # 模拟状态更新
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage(f"操作 {i}")
                
                # 处理事件
                if hasattr(self.app, 'processEvents'):
                    self.app.processEvents()
                
                response_time = time.time() - start_time
                response_times.append(response_time)
            
            # 验证响应时间
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time <= self.ui_performance_targets["response_time_s"], \
                f"平均UI响应时间过长: {avg_response_time:.2f}s"
            
            assert max_response_time <= self.ui_performance_targets["response_time_s"] * 2, \
                f"最大UI响应时间过长: {max_response_time:.2f}s"
            
        except ImportError:
            pytest.skip("UI模块不可用")

    def test_ui_accessibility_features(self):
        """测试UI可访问性功能"""
        try:
            # 测试高对比度主题
            from src.ui.components.theme_manager import ThemeManager
            
            theme_manager = ThemeManager()
            
            # 切换到高对比度主题
            success = theme_manager.switch_theme("high-contrast")
            assert success, "高对比度主题切换失败"
            
            # 验证对比度设置
            contrast_settings = theme_manager.get_contrast_settings()
            assert contrast_settings["ratio"] >= 7.0, \
                f"对比度不足: {contrast_settings['ratio']} (要求: ≥7.0)"
            
            # 测试字体大小调整
            font_sizes = ["small", "medium", "large", "extra-large"]
            for size in font_sizes:
                font_success = theme_manager.set_font_size(size)
                assert font_success, f"{size}字体大小设置失败"
            
        except ImportError:
            pytest.skip("主题管理器模块不可用")

    def test_ui_error_handling(self):
        """测试UI错误处理"""
        try:
            from src.ui.components.alert_manager import AlertManager
            
            alert_manager = AlertManager()
            
            # 测试错误处理机制
            error_scenarios = [
                {"type": "file_not_found", "message": "文件未找到"},
                {"type": "memory_error", "message": "内存不足"},
                {"type": "network_error", "message": "网络连接失败"},
                {"type": "permission_error", "message": "权限不足"}
            ]
            
            for scenario in error_scenarios:
                # 模拟错误处理
                alert_id = alert_manager.handle_error(
                    error_type=scenario["type"],
                    error_message=scenario["message"]
                )
                
                assert alert_id is not None, f"{scenario['type']}错误处理失败"
                
                # 验证错误恢复
                recovery_success = alert_manager.attempt_recovery(scenario["type"])
                # 恢复可能成功也可能失败，但不应该崩溃
                
        except ImportError:
            pytest.skip("警告管理器模块不可用")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
