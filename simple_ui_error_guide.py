#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 错误指引集成脚本

此脚本将错误指引系统集成到simple_ui.py中
"""

import sys
import os
import logging
import importlib.util
from pathlib import Path

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
    """修补SimpleScreenplayApp类以集成错误指引系统
    
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
        
        # 添加错误指引系统
        try:
            # 导入错误指引集成模块
            from ui.assistant.error_guide_integration import integrate_error_guide
            
            # 集成错误指引系统
            self.error_guide_integrator = integrate_error_guide(self)
            
            logger.info("成功集成错误指引系统")
        except Exception as e:
            logger.error(f"集成错误指引系统失败: {e}")
    
    # 替换__init__方法
    SimpleScreenplayApp.__init__ = patched_init
    
    logger.info("成功修补SimpleScreenplayApp类")
    return True

def create_error_solutions_config():
    """创建错误解决方案配置文件"""
    from ui.assistant.error_guide import get_error_guide
    
    # 获取错误指引实例
    error_guide = get_error_guide()
    
    # 保存默认配置
    error_guide._save_default_solutions()
    
    logger.info("已创建错误解决方案配置文件")

def ensure_tutorial_videos():
    """确保教程视频目录存在"""
    tutorials_dir = os.path.join(PROJECT_ROOT, "resources", "tutorials")
    os.makedirs(tutorials_dir, exist_ok=True)
    
    # 创建示例README文件
    readme_path = os.path.join(tutorials_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write("""# 教程视频目录

此目录用于存放错误解决方案的教程视频。

## 视频命名规则

教程视频应按照以下规则命名：

- `srt_fix.mp4`: 字幕修复教程
- `model_fix.mp4`: 模型修复教程
- `video_fix.mp4`: 视频修复教程
- `training_fix.mp4`: 训练修复教程
- `gpu_memory_fix.mp4`: GPU内存问题修复教程
- `dependency_fix.mp4`: 依赖库问题修复教程

## 视频格式

推荐使用MP4格式，分辨率为720p，编码为H.264。
""")
    
    logger.info("已创建教程视频目录")

def main():
    """主函数"""
    logger.info("开始集成错误指引系统到simple_ui.py")
    
    # 检查simple_ui.py是否存在
    if not check_simple_ui():
        logger.error("找不到simple_ui.py，无法继续")
        return
    
    # 创建错误解决方案配置文件
    create_error_solutions_config()
    
    # 确保教程视频目录存在
    ensure_tutorial_videos()
    
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
    logger.info("启动集成了错误指引系统的simple_ui")
    simple_ui.main()

if __name__ == "__main__":
    main() 