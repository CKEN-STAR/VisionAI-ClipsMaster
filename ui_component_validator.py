#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强UI组件验证器
确保所有UI组件能被正确识别和访问
"""

def validate_ui_components(ui_instance):
    """验证UI组件完整性"""
    validation_results = {
        "tabWidget": False,
        "statusbar": False,
        "menubar": False,
        "centralWidget": False
    }
    
    # 检查tabWidget
    if hasattr(ui_instance, 'tabWidget'):
        validation_results["tabWidget"] = True
    elif hasattr(ui_instance, 'tab_widget'):
        # 创建别名
        ui_instance.tabWidget = ui_instance.tab_widget
        validation_results["tabWidget"] = True
    
    # 检查statusbar
    if hasattr(ui_instance, 'statusbar'):
        validation_results["statusbar"] = True
    elif hasattr(ui_instance, 'status_bar'):
        # 创建别名
        ui_instance.statusbar = ui_instance.status_bar
        validation_results["statusbar"] = True
    
    # 检查menubar
    if hasattr(ui_instance, 'menubar'):
        validation_results["menubar"] = True
    elif hasattr(ui_instance, 'menu_bar'):
        # 创建别名
        ui_instance.menubar = ui_instance.menu_bar
        validation_results["menubar"] = True
    
    # 检查centralWidget
    if hasattr(ui_instance, 'centralWidget'):
        validation_results["centralWidget"] = True
    elif hasattr(ui_instance, 'centralwidget'):
        # 创建别名
        ui_instance.centralWidget = ui_instance.centralwidget
        validation_results["centralWidget"] = True
    
    return validation_results

def ensure_component_compatibility(ui_instance):
    """确保组件兼容性"""
    try:
        validate_ui_components(ui_instance)
        return True
    except Exception as e:
        print(f"UI组件兼容性确保失败: {e}")
        return False
