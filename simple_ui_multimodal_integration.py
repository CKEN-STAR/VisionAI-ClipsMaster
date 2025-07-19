#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 多模态提示展示集成示例

此脚本展示了如何将多模态提示展示功能集成到simple_ui.py中
"""

import sys
import os
from pathlib import Path
import logging
import importlib.util

# 设置项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_simple_ui():
    """检查simple_ui.py是否存在"""
    simple_ui_path = os.path.join(PROJECT_ROOT, "simple_ui.py")
    return os.path.exists(simple_ui_path)

def import_simple_ui():
    """导入simple_ui模块"""
    simple_ui_path = os.path.join(PROJECT_ROOT, "simple_ui.py")
    
    if not os.path.exists(simple_ui_path):
        logger.error(f"找不到simple_ui.py: {simple_ui_path}")
        return None
    
    try:
        # 动态导入模块
        spec = importlib.util.spec_from_file_location("simple_ui", simple_ui_path)
        simple_ui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(simple_ui)
        
        logger.info("成功导入simple_ui模块")
        return simple_ui
    except Exception as e:
        logger.error(f"导入simple_ui.py失败: {e}")
        return None

def patch_simple_ui_app(simple_ui):
    """修补SimpleScreenplayApp类以集成多模态提示展示功能
    
    Args:
        simple_ui: simple_ui模块
    """
    if not simple_ui:
        logger.error("无法修补SimpleScreenplayApp: simple_ui模块不可用")
        return False
    
    # 获取SimpleScreenplayApp类
    SimpleScreenplayApp = getattr(simple_ui, "SimpleScreenplayApp", None)
    if not SimpleScreenplayApp:
        logger.error("找不到SimpleScreenplayApp类")
        return False
    
    # 保存原始的__init__方法
    original_init = SimpleScreenplayApp.__init__
    
    # 定义新的__init__方法
    def patched_init(self, *args, **kwargs):
        # 调用原始的__init__方法
        original_init(self, *args, **kwargs)
        
        # 添加多模态提示展示功能
        try:
            # 导入多模态提示展示集成模块
            from ui.assistant.multimodal_integration import integrate_multimodal_tips
            
            # 集成多模态提示展示功能
            self.multimodal_integrator = integrate_multimodal_tips(self)
            
            logger.info("成功集成多模态提示展示功能")
        except Exception as e:
            logger.error(f"集成多模态提示展示功能失败: {e}")
    
    # 替换__init__方法
    SimpleScreenplayApp.__init__ = patched_init
    
    logger.info("成功修补SimpleScreenplayApp类")
    return True

def main():
    """主函数"""
    logger.info("开始集成多模态提示展示功能到simple_ui.py")
    
    # 检查simple_ui.py是否存在
    if not check_simple_ui():
        logger.error("找不到simple_ui.py，无法继续")
        return
    
    # 导入simple_ui模块
    simple_ui = import_simple_ui()
    if not simple_ui:
        logger.error("导入simple_ui模块失败，无法继续")
        return
    
    # 修补SimpleScreenplayApp类
    if not patch_simple_ui_app(simple_ui):
        logger.error("修补SimpleScreenplayApp类失败，无法继续")
        return
    
    # 调用simple_ui的main函数
    logger.info("启动集成了多模态提示展示功能的simple_ui")
    simple_ui.main()

if __name__ == "__main__":
    main() 