#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 上下文分析引擎集成模块

此模块用于将上下文分析引擎集成到现有的simple_ui.py中，
通过猴子补丁(Monkey Patching)的方式，无需修改原始文件。
"""

import sys
import os
import inspect
from functools import wraps
from pathlib import Path
from types import MethodType

# 确保项目根目录在Python路径中
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# 导入上下文分析引擎
from ui.assistant.context_analyzer import UserAction, ContextType, get_context_assistant
from ui.assistant.context_ui_helper import ContextAssistant

# 导入Simple UI
import simple_ui

def integrate_context_analyzer():
    """集成上下文分析引擎到Simple UI
    
    通过猴子补丁的方式，将上下文分析引擎集成到现有的Simple UI中，
    无需修改原始文件。
    """
    print("正在集成上下文分析引擎...")
    
    # 保存原始的SimpleScreenplayApp.__init__方法
    original_init = simple_ui.SimpleScreenplayApp.__init__
    
    @wraps(original_init)
    def patched_init(self, *args, **kwargs):
        # 调用原始的__init__方法
        original_init(self, *args, **kwargs)
        
        # 添加上下文助手
        self.context_assistant = ContextAssistant(self)
        
        # 如果已经初始化了UI，则添加上下文助手UI
        if hasattr(self, 'right_panel') and self.right_panel is not None:
            try:
                self.right_panel.layout().addWidget(self.context_assistant)
                print("已添加上下文助手UI到主窗口")
            except Exception as e:
                print(f"添加上下文助手UI时出错: {e}")
    
    # 替换__init__方法
    simple_ui.SimpleScreenplayApp.__init__ = patched_init
    print("已集成上下文助手到SimpleScreenplayApp.__init__")
    
    # 集成到init_ui方法
    original_init_ui = simple_ui.SimpleScreenplayApp.init_ui
    
    @wraps(original_init_ui)
    def patched_init_ui(self, *args, **kwargs):
        # 调用原始的init_ui方法
        original_init_ui(self, *args, **kwargs)
        
        # 添加上下文助手UI到主窗口
        if not hasattr(self, 'context_assistant'):
            self.context_assistant = ContextAssistant(self)
            
        try:
            # 尝试添加到right_panel
            if hasattr(self, 'right_panel') and self.right_panel is not None:
                self.right_panel.layout().addWidget(self.context_assistant)
                print("已添加上下文助手UI到主窗口")
            # 如果没有right_panel，尝试添加到其他位置
            elif hasattr(self, 'main_layout'):
                self.main_layout.addWidget(self.context_assistant)
                print("已添加上下文助手UI到主布局")
        except Exception as e:
            print(f"添加上下文助手UI时出错: {e}")
    
    # 替换init_ui方法
    simple_ui.SimpleScreenplayApp.init_ui = patched_init_ui
    print("已集成上下文助手到SimpleScreenplayApp.init_ui")
    
    # 集成到select_video方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'select_video'):
        original_select_video = simple_ui.SimpleScreenplayApp.select_video
        
        @wraps(original_select_video)
        def patched_select_video(self, *args, **kwargs):
            # 调用原始的select_video方法
            result = original_select_video(self, *args, **kwargs)
            
            # 记录用户上传视频操作
            if hasattr(self, 'context_assistant') and hasattr(self, 'video_path'):
                self.context_assistant.record_action(
                    UserAction.UPLOAD, 
                    {"type": "video", "path": self.video_path}
                )
                print("已记录用户上传视频操作")
            
            return result
        
        # 替换select_video方法
        simple_ui.SimpleScreenplayApp.select_video = patched_select_video
        print("已集成上下文助手到SimpleScreenplayApp.select_video")
    
    # 集成到select_subtitle方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'select_subtitle'):
        original_select_subtitle = simple_ui.SimpleScreenplayApp.select_subtitle
        
        @wraps(original_select_subtitle)
        def patched_select_subtitle(self, *args, **kwargs):
            # 调用原始的select_subtitle方法
            result = original_select_subtitle(self, *args, **kwargs)
            
            # 记录用户上传字幕操作
            if hasattr(self, 'context_assistant') and hasattr(self, 'srt_path'):
                self.context_assistant.record_action(
                    UserAction.UPLOAD, 
                    {"type": "subtitle", "path": self.srt_path}
                )
                print("已记录用户上传字幕操作")
            
            return result
        
        # 替换select_subtitle方法
        simple_ui.SimpleScreenplayApp.select_subtitle = patched_select_subtitle
        print("已集成上下文助手到SimpleScreenplayApp.select_subtitle")
    
    # 集成到change_language_mode方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'change_language_mode'):
        original_change_language_mode = simple_ui.SimpleScreenplayApp.change_language_mode
        
        @wraps(original_change_language_mode)
        def patched_change_language_mode(self, mode, *args, **kwargs):
            # 调用原始的change_language_mode方法
            result = original_change_language_mode(self, mode, *args, **kwargs)
            
            # 记录用户切换模型操作
            if hasattr(self, 'context_assistant'):
                self.context_assistant.record_action(
                    UserAction.MODEL_SWITCH, 
                    {"mode": mode}
                )
                print(f"已记录用户切换模型操作: {mode}")
            
            return result
        
        # 替换change_language_mode方法
        simple_ui.SimpleScreenplayApp.change_language_mode = patched_change_language_mode
        print("已集成上下文助手到SimpleScreenplayApp.change_language_mode")
    
    # 集成到trigger_generation方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'trigger_generation'):
        original_trigger_generation = simple_ui.SimpleScreenplayApp.trigger_generation
        
        @wraps(original_trigger_generation)
        def patched_trigger_generation(self, *args, **kwargs):
            # 调用原始的trigger_generation方法
            result = original_trigger_generation(self, *args, **kwargs)
            
            # 记录用户开始渲染操作
            if hasattr(self, 'context_assistant'):
                video_path = getattr(self, 'video_path', None)
                srt_path = getattr(self, 'srt_path', None)
                self.context_assistant.record_action(
                    UserAction.START_RENDER, 
                    {"video": video_path, "subtitle": srt_path}
                )
                print("已记录用户开始渲染操作")
            
            return result
        
        # 替换trigger_generation方法
        simple_ui.SimpleScreenplayApp.trigger_generation = patched_trigger_generation
        print("已集成上下文助手到SimpleScreenplayApp.trigger_generation")
    
    # 集成到on_tab_changed方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'on_tab_changed'):
        original_on_tab_changed = simple_ui.SimpleScreenplayApp.on_tab_changed
        
        @wraps(original_on_tab_changed)
        def patched_on_tab_changed(self, index, *args, **kwargs):
            # 调用原始的on_tab_changed方法
            result = original_on_tab_changed(self, index, *args, **kwargs)
            
            # 记录用户切换标签页操作
            if hasattr(self, 'context_assistant') and hasattr(self, 'tabs'):
                tab_name = self.tabs.tabText(index)
                self.context_assistant.record_action(
                    UserAction.SWITCH_TAB, 
                    {"tab_index": index, "tab_name": tab_name}
                )
                print(f"已记录用户切换标签页操作: {tab_name}")
            
            return result
        
        # 替换on_tab_changed方法
        simple_ui.SimpleScreenplayApp.on_tab_changed = patched_on_tab_changed
        print("已集成上下文助手到SimpleScreenplayApp.on_tab_changed")
    
    # 集成到show_about_dialog方法
    if hasattr(simple_ui.SimpleScreenplayApp, 'show_about_dialog'):
        original_show_about_dialog = simple_ui.SimpleScreenplayApp.show_about_dialog
        
        @wraps(original_show_about_dialog)
        def patched_show_about_dialog(self, *args, **kwargs):
            # 调用原始的show_about_dialog方法
            result = original_show_about_dialog(self, *args, **kwargs)
            
            # 添加会话摘要信息
            if hasattr(self, 'context_assistant'):
                try:
                    # 尝试获取会话摘要并添加到关于对话框
                    session_summary = self.context_assistant.get_session_summary()
                    print(f"会话摘要: {session_summary}")
                except Exception as e:
                    print(f"获取会话摘要时出错: {e}")
            
            return result
        
        # 替换show_about_dialog方法
        simple_ui.SimpleScreenplayApp.show_about_dialog = patched_show_about_dialog
        print("已集成上下文助手到SimpleScreenplayApp.show_about_dialog")
    
    print("上下文分析引擎集成完成!")
    return True

def main():
    """主函数"""
    # 集成上下文分析引擎
    integrate_context_analyzer()
    
    # 运行Simple UI
    print("正在启动Simple UI...")
    simple_ui.main()

if __name__ == "__main__":
    main()