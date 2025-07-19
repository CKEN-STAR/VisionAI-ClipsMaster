#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 动态提示集成示例

演示如何将动态提示生成器与simple_ui.py集成
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    # 导入simple_ui模块
    try:
        from simple_ui import SimpleScreenplayApp, main as simple_ui_main
        logger.info("成功导入simple_ui模块")
    except ImportError as e:
        logger.error(f"导入simple_ui模块失败: {e}")
        return

    # 导入动态提示集成模块
    try:
        from ui.assistant.dynamic_tip_integration import integrate_dynamic_tips, get_tip_manager
        HAS_DYNAMIC_TIPS = True
        logger.info("成功导入动态提示集成模块")
    except ImportError as e:
        logger.warning(f"导入动态提示集成模块失败: {e}")
        logger.warning("将不启用动态提示功能")
        HAS_DYNAMIC_TIPS = False

    # 导入个性化推荐模块
    try:
        from ui.assistant.simple_ui_integration import integrate_with_simple_ui
        HAS_PERSONALIZATION = True
        logger.info("成功导入个性化推荐模块")
    except ImportError as e:
        logger.warning(f"导入个性化推荐模块失败: {e}")
        logger.warning("将不启用个性化推荐功能")
        HAS_PERSONALIZATION = False

    # 保存原始的SimpleScreenplayApp.__init__方法
    original_init = SimpleScreenplayApp.__init__

    # 定义增强的__init__方法
    def enhanced_init(self, *args, **kwargs):
        """增强的初始化方法，集成动态提示和个性化推荐"""
        # 调用原始初始化方法
        original_init(self, *args, **kwargs)
        
        # 集成个性化推荐
        if HAS_PERSONALIZATION:
            try:
                integrate_with_simple_ui(self)
                logger.info("已集成个性化推荐")
            except Exception as e:
                logger.error(f"集成个性化推荐失败: {e}")
        
        # 集成动态提示
        if HAS_DYNAMIC_TIPS:
            try:
                integrate_dynamic_tips(self)
                logger.info("已集成动态提示")
                
                # 记录初始上下文数据
                tip_manager = get_tip_manager()
                
                # 检测是否有视频路径
                if hasattr(self, "video_path") and self.video_path:
                    tip_manager.update_context_data("uploading", {"file_count": 1})
                
                # 检测是否有字幕路径
                if hasattr(self, "srt_path") and self.srt_path:
                    tip_manager.update_context_data("uploading", {"has_subtitle": True})
                
                # 检测GPU
                if hasattr(self, "has_gpu"):
                    tip_manager.update_context_data("performance", {"has_gpu": self.has_gpu})
                
                # 强制显示一个初始提示
                tip_manager.check_and_show_tip(force=True)
            except Exception as e:
                logger.error(f"集成动态提示失败: {e}")

    # 替换SimpleScreenplayApp的__init__方法
    SimpleScreenplayApp.__init__ = enhanced_init
    
    # 保存原始main函数
    original_main = simple_ui_main
    
    # 定义增强的main函数
    def enhanced_main():
        """增强的main函数，添加日志记录"""
        logger.info("启动增强版SimpleScreenplayApp")
        
        # 调用原始main函数
        return original_main()
    
    # 替换main函数
    simple_ui_main = enhanced_main
    
    # 运行应用
    simple_ui_main()


if __name__ == "__main__":
    # 确保配置目录存在
    configs_dir = os.path.join(PROJECT_ROOT, "configs")
    os.makedirs(configs_dir, exist_ok=True)
    
    # 确保用户数据目录存在
    user_profiles_dir = os.path.join(PROJECT_ROOT, "data", "user_profiles")
    os.makedirs(user_profiles_dir, exist_ok=True)
    
    # 运行主函数
    main() 