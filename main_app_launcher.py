#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 应用启动器

提供两种UI模式启动选项：简易UI模式和带导航菜单的完整UI模式
"""

import sys
import os
import argparse
import logging
import json
from pathlib import Path

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置配置目录
CONFIG_DIR = os.path.join(PROJECT_ROOT, "configs")
os.makedirs(CONFIG_DIR, exist_ok=True)

# 配置日志记录
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "app.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# 导入兼容性模块
try:
    from ui.compat import setup_compat, check_qt_requirements, check_system_requirements, check_python_requirements
except ImportError as e:
    logger.warning(f"无法导入兼容性模块，可能影响程序在某些环境下的运行: {e}")
    
    # 创建简单的兼容性检查函数作为后备
    def check_qt_requirements():
        return True, "兼容性模块未加载，跳过Qt版本检查"
    
    def check_system_requirements():
        return True, "兼容性模块未加载，跳过系统兼容性检查"
    
    def check_python_requirements():
        return True, "兼容性模块未加载，跳过Python版本检查"
    
    def setup_compat():
        logger.warning("兼容性模块未加载，跳过兼容性设置")
        return False

def initialize_compatibility():
    """初始化兼容性设置并检查系统要求"""
    logger.info("正在初始化系统兼容性设置...")
    
    # 检查系统要求
    sys_ok, sys_msg = check_system_requirements()
    if not sys_ok:
        logger.warning(f"系统兼容性检查警告: {sys_msg}")
    else:
        logger.info(f"系统兼容性检查: {sys_msg}")
    
    # 检查Python版本要求
    py_ok, py_msg = check_python_requirements()
    if not py_ok:
        logger.warning(f"Python版本检查警告: {py_msg}")
    else:
        logger.info(f"Python版本检查: {py_msg}")
    
    # 检查Qt版本要求
    qt_ok, qt_msg = check_qt_requirements()
    if not qt_ok:
        logger.warning(f"Qt版本检查警告: {qt_msg}")
    else:
        logger.info(f"Qt版本检查: {qt_msg}")
    
    # 应用兼容性设置
    setup_compat()
    logger.info("兼容性设置已初始化")
    
    return sys_ok and py_ok and qt_ok

def setup_global_state():
    """设置全局状态管理系统"""
    try:
        # 导入状态管理模块
        from ui.core.state_manager import state_manager
        
        # 记录应用启动状态
        state_manager.set_state("app.startup_time", logging.Formatter().converter())
        state_manager.set_state("app.version", "1.0.0")
        
        # 记录平台信息
        import platform
        state_manager.set_state("system.platform", platform.system())
        state_manager.set_state("system.python_version", platform.python_version())
        
        # 记录是否有GPU支持
        gpu_available = False
        gpu_name = "未检测到GPU"
        
        try:
            # 尝试使用torch检测GPU
            import torch
            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                gpu_available = True
                gpu_name = torch.cuda.get_device_name(0)
        except ImportError:
            pass
            
        state_manager.set_state("system.gpu_available", gpu_available)
        state_manager.set_state("system.gpu_name", gpu_name)
        
        # 设置性能配置
        from ui.utils.performance import UIOptimizer
        hw_profile = UIOptimizer.detect_hardware()
        state_manager.set_state("system.hardware_profile", hw_profile.value)
        state_manager.set_state("performance.config", UIOptimizer.get_config())
        
        logger.info("全局状态管理系统已初始化")
        return True
    except Exception as e:
        logger.error(f"设置全局状态管理系统失败: {e}")
        return False

def setup_performance_optimization(before_app=False):
    """设置性能优化
    
    Args:
        before_app: 是否在QApplication创建前调用
    """
    try:
        # 应用到QApplication之前的优化
        if before_app:
            # 设置环境变量
            if os.environ.get("VISION_AI_NO_HW_ACCEL") == "1":
                os.environ["QT_OPENGL"] = "software"
            else:
                if sys.platform == "win32":
                    os.environ["QT_OPENGL"] = "angle"
            
            # 无法在此阶段应用其他优化
            return True
            
        # QApplication创建后的优化
        from ui.utils.performance import apply_performance_settings

        # 应用渲染管线优化
        try:
            from ui.performance import optimize_rendering
            stats = optimize_rendering()
            logger.info(f"渲染管线优化已应用: 渲染调用减少约{stats['render_call_reduction_percent']:.1f}%, GPU负载降低约{stats['gpu_load_reduction_percent']:.1f}%")
        except ImportError as e:
            logger.warning(f"无法导入渲染管线优化模块: {e}")
        
        # 初始化资源按需加载系统
        try:
            from ui.performance import get_resource_manager, preload_resources
            
            # 获取资源管理器实例
            resource_manager = get_resource_manager()
            logger.info("资源按需加载系统已初始化")
            
            # 加载常用资源配置
            try:
                common_resources_data = resource_manager.get_json("common_resources")
                if common_resources_data:
                    # 预加载高优先级资源
                    high_priority_resources = common_resources_data.get("resource_priorities", {}).get("high", [])
                    if high_priority_resources:
                        preload_resources(high_priority_resources)
                        logger.info(f"已预加载 {len(high_priority_resources)} 个高优先级资源")
            except Exception as e:
                logger.warning(f"加载常用资源配置失败: {e}")
        except ImportError as e:
            logger.warning(f"无法导入资源按需加载模块: {e}")
            
        # 应用其他性能优化
        apply_performance_settings()
        logger.info("性能优化设置已应用")
        return True
    except Exception as e:
        logger.error(f"设置性能优化失败: {e}")
        return False

def launch_simple_ui():
    """启动简易UI"""
    try:
        # 在创建QApplication前应用性能优化
        setup_performance_optimization(before_app=True)
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from simple_ui_fixed import SimpleScreenplayApp
        
        # 创建应用实例
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # 使用通用的Fusion样式
        
        # 应用QApplication创建后的性能优化
        setup_performance_optimization()
        
        # 创建并显示简易界面
        window = SimpleScreenplayApp()
        window.show()
        
        return app.exec()
    except Exception as e:
        logger.error(f"启动简易UI失败: {e}")
        return 1

def launch_full_ui():
    """启动带有导航菜单的完整UI"""
    try:
        # 在创建QApplication前应用性能优化
        setup_performance_optimization(before_app=True)
        
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from ui.main_window_with_nav import MainWindowWithNav
        
        # 创建应用实例
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # 使用通用的Fusion样式
        app.setApplicationName("VisionAI-ClipsMaster")
        app.setApplicationVersion("1.0.0")
        
        # 应用QApplication创建后的性能优化
        setup_performance_optimization()
        
        # 创建并显示完整界面
        window = MainWindowWithNav()
        window.show()
        
        return app.exec()
    except Exception as e:
        logger.error(f"启动完整UI失败: {e}")
        return 1

def main():
    """程序主入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster应用启动器")
    parser.add_argument("--simple", action="store_true", help="启动简易界面模式")
    parser.add_argument("--full", action="store_true", help="启动完整界面模式（带导航菜单）")
    parser.add_argument("--optimize", action="store_true", help="启用额外的性能优化")
    parser.add_argument("--no-gpu", action="store_true", help="禁用GPU加速")
    args = parser.parse_args()
    
    # 设置性能标志
    if args.optimize:
        os.environ["VISION_AI_OPTIMIZE"] = "1"
        
    if args.no_gpu:
        os.environ["VISION_AI_NO_HW_ACCEL"] = "1"
    
    # 初始化兼容性设置
    initialize_compatibility()
    
    # 初始化全局状态
    setup_global_state()
    
    # 根据参数选择启动模式
    if args.full:
        return launch_full_ui()
    else:
        # 默认启动简易UI
        return launch_simple_ui()
        
if __name__ == "__main__":
    sys.exit(main()) 