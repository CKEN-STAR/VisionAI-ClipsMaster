#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 面板测试夹具

提供UI面板测试所需的测试夹具和工具函数
"""

import sys
import os
import pytest
from pathlib import Path

import PyQt6
from PyQt6.QtWidgets import QApplication

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入相关组件
from ui.core.state_manager import StateManager
from ui.optimize.panel_perf import PanelOptimizer


# 测试模型类
class TestModel:
    """测试模型类，模拟AI模型以便测试"""
    
    def __init__(self):
        self.temperature = 0.0
        self.top_k = 40
        self.top_p = 0.9
        self.detail_level = 0.5
        self.style_strength = 0.5
        
    def set_temperature(self, value):
        """设置温度参数"""
        if value < 0 or value > 1.0:
            raise ValueError("Temperature must be between 0 and 1")
        self.temperature = value
        
    def set_params(self, params):
        """设置多个参数"""
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, value)


@pytest.fixture(scope="function")
def qapp():
    """创建Qt应用实例"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture(scope="function")
def reset_state():
    """重置状态管理器"""
    state_manager = StateManager()
    state_manager.reset()
    yield state_manager
    state_manager.reset()


@pytest.fixture(scope="function")
def test_model():
    """创建测试模型实例"""
    model = TestModel()
    yield model


@pytest.fixture(scope="function")
def panel_optimizer():
    """创建面板优化器实例"""
    optimizer = PanelOptimizer()
    yield optimizer


@pytest.fixture(scope="function")
def create_test_panels(qapp):
    """创建测试面板"""
    def _create_panels(num_panels=5):
        """创建指定数量的测试面板"""
        from PyQt6.QtWidgets import QWidget
        
        panels = []
        for i in range(num_panels):
            panel = QWidget()
            panel.setObjectName(f"panel{i}")
            panel.resources_loaded = True
            panels.append(panel)
        return panels
    
    return _create_panels


@pytest.fixture(scope="function")
def qtbot(qapp):
    """创建Qt测试机器人"""
    from pytestqt.plugin import QtBot
    result = QtBot(qapp)
    return result 