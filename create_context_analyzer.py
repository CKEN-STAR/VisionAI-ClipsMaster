#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
辅助脚本：创建上下文分析引擎文件
"""

import os

content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 上下文分析引擎

此模块负责分析用户操作的上下文，判断当前用户处于什么操作阶段，
以便系统能够提供相应的帮助和功能建议。
"""

import os
import time
import logging
from collections import deque
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Set

# 设置日志
logger = logging.getLogger(__name__)

class ContextType(Enum):
    """上下文类型枚举"""
    UPLOADING = "uploading"        # 文件上传阶段
    MODEL_LOADING = "model_loading" # 模型加载阶段
    EDITING = "editing"            # 参数调整阶段
    TRAINING = "training"          # 模型训练阶段
    RENDERING = "rendering"        # 视频生成阶段
    ANALYZING = "analyzing"        # 分析结果阶段
    EXPORTING = "exporting"        # 导出结果阶段
    IDLE = "idle"                  # 空闲状态

class UserAction(Enum):
    """用户操作类型枚举"""
    UPLOAD = "upload"              # 上传文件
    SELECT_MODEL = "select_model"  # 选择模型
    ADJUST_PARAMS = "adjust_params"# 调整参数
    START_TRAINING = "start_training" # 开始训练
    START_RENDER = "start_render"  # 开始渲染
    VIEW_RESULTS = "view_results"  # 查看结果
    EXPORT = "export"              # 导出结果
    SWITCH_TAB = "switch_tab"      # 切换标签页
    MODEL_SWITCH = "model_switching" # 切换模型

class ContextDetector:
    """上下文检测器
    
    分析用户操作历史，检测当前上下文环境，为UI提供智能建议
    """
    
    def __init__(self):
        """初始化上下文检测器"""
        self.state_history = deque(maxlen=5)  # 记录最近5个操作
        self.current_context = ContextType.IDLE
        self.last_action_time = 0
        self.action_counts = {action: 0 for action in UserAction}
        self.session_start_time = time.time()
        
    def record_action(self, action: UserAction, data: Optional[Dict] = None):
        """记录用户操作
        
        Args:
            action: 用户操作类型
            data: 操作相关数据
        """
        timestamp = time.time()
        action_record = {
            "action": action,
            "timestamp": timestamp,
            "data": data or {}
        }
        
        # 更新操作计数
        if action in self.action_counts:
            self.action_counts[action] += 1
        
        # 记录操作
        self.state_history.append(action_record)
        self.last_action_time = timestamp
        
        # 更新当前上下文
        self._update_context()
        
        logger.debug(f"记录操作: {action.value}, 当前上下文: {self.current_context.value}")
    
    def _update_context(self):
        """根据历史操作更新当前上下文"""
        # 如果历史记录为空，设为空闲状态
        if not self.state_history:
            self.current_context = ContextType.IDLE
            return
        
        # 获取最近的操作
        last_action = self.state_history[-1]["action"]
        
        # 根据最近操作更新上下文
        if last_action == UserAction.UPLOAD:
            self.current_context = ContextType.UPLOADING
        elif last_action == UserAction.SELECT_MODEL:
            self.current_context = ContextType.MODEL_LOADING
        elif last_action == UserAction.ADJUST_PARAMS:
            self.current_context = ContextType.EDITING
        elif last_action == UserAction.START_TRAINING:
            self.current_context = ContextType.TRAINING
        elif last_action == UserAction.START_RENDER:
            self.current_context = ContextType.RENDERING
        elif last_action == UserAction.VIEW_RESULTS:
            self.current_context = ContextType.ANALYZING
        elif last_action == UserAction.EXPORT:
            self.current_context = ContextType.EXPORTING
        elif last_action == UserAction.MODEL_SWITCH:
            self.current_context = ContextType.MODEL_LOADING
            
    def get_current_context(self) -> str:
        """综合判断当前用户场景
        
        Returns:
            str: 当前上下文类型
        """
        # 检查最近的两个操作是否有特定模式
        if len(self.state_history) > 0:
            actions = [x["action"].value for x in self.state_history]
            if "upload" in actions and "training" not in actions:
                return "uploading"
            elif len(actions) >= 2 and "model_switching" in actions[-2:]:
                return "model_loading"
        
        return "editing"  # 默认为编辑状态
            
    def get_action_frequency(self, action: UserAction) -> float:
        """获取特定操作的频率（每分钟）
        
        Args:
            action: 操作类型
            
        Returns:
            float: 操作频率（每分钟）
        """
        session_duration = (time.time() - self.session_start_time) / 60  # 转换为分钟
        if session_duration < 0.01:  # 避免除零错误
            return 0
            
        return self.action_counts.get(action, 0) / session_duration
        
    def get_context_duration(self) -> float:
        """获取当前上下文持续时间（秒）
        
        Returns:
            float: 持续时间（秒）
        """
        if not self.state_history:
            return 0
            
        context_start = None
        current_context = self.current_context
        
        # 从最近的操作向前查找上下文变化点
        for i in range(len(self.state_history) - 1, -1, -1):
            record = self.state_history[i]
            action_context = self._action_to_context(record["action"])
            
            if action_context != current_context:
                context_start = record["timestamp"]
                break
                
        if context_start is None:
            context_start = self.session_start_time
            
        return time.time() - context_start
        
    def _action_to_context(self, action: UserAction) -> ContextType:
        """将操作类型转换为对应的上下文类型
        
        Args:
            action: 操作类型
            
        Returns:
            ContextType: 对应的上下文类型
        """
        mapping = {
            UserAction.UPLOAD: ContextType.UPLOADING,
            UserAction.SELECT_MODEL: ContextType.MODEL_LOADING,
            UserAction.ADJUST_PARAMS: ContextType.EDITING,
            UserAction.START_TRAINING: ContextType.TRAINING,
            UserAction.START_RENDER: ContextType.RENDERING,
            UserAction.VIEW_RESULTS: ContextType.ANALYZING,
            UserAction.EXPORT: ContextType.EXPORTING,
            UserAction.MODEL_SWITCH: ContextType.MODEL_LOADING
        }
        return mapping.get(action, ContextType.IDLE)
        
    def get_suggestion(self) -> Tuple[str, str]:
        """根据当前上下文提供建议
        
        Returns:
            Tuple[str, str]: (建议标题, 建议内容)
        """
        if self.current_context == ContextType.UPLOADING:
            return "文件上传", "请选择视频文件或字幕文件进行上传。支持MP4、MOV视频格式和SRT字幕格式。"
        elif self.current_context == ContextType.MODEL_LOADING:
            return "模型加载", "正在加载AI模型，请稍候。首次使用可能需要下载模型文件。"
        elif self.current_context == ContextType.EDITING:
            return "参数调整", "您可以调整处理参数以获得更好的效果。尝试调整时长、风格或语言选项。"
        elif self.current_context == ContextType.TRAINING:
            return "模型训练", "正在训练个性化模型，这可能需要几分钟时间。训练完成后可以生成更符合风格的内容。"
        elif self.current_context == ContextType.RENDERING:
            return "视频生成", "正在生成视频，请耐心等待。处理速度取决于视频长度和复杂度。"
        elif self.current_context == ContextType.ANALYZING:
            return "分析结果", "您可以查看生成结果并进行评估。如需调整，可以返回编辑页面修改参数。"
        elif self.current_context == ContextType.EXPORTING:
            return "导出结果", "您可以将结果导出为视频文件或字幕文件，并选择保存位置。"
        else:
            return "准备就绪", "请选择要执行的操作。您可以上传文件、调整参数或生成内容。"
            
    def clear_history(self):
        """清除操作历史"""
        self.state_history.clear()
        self.current_context = ContextType.IDLE
        self.action_counts = {action: 0 for action in UserAction}
        
    def is_first_time_user(self) -> bool:
        """判断是否为首次使用的用户
        
        Returns:
            bool: 是否为首次使用
        """
        # 如果操作总数少于3，可能是新用户
        total_actions = sum(self.action_counts.values())
        return total_actions < 3
        
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要
        
        Returns:
            Dict[str, Any]: 会话摘要信息
        """
        session_duration = time.time() - self.session_start_time
        
        return {
            "duration": session_duration,
            "action_count": sum(self.action_counts.values()),
            "most_frequent_action": max(self.action_counts.items(), key=lambda x: x[1])[0].value if self.action_counts else None,
            "current_context": self.current_context.value,
            "context_duration": self.get_context_duration()
        }

# 创建上下文助手实例
context_assistant = ContextDetector()

def get_context_assistant() -> ContextDetector:
    """获取上下文助手实例
    
    Returns:
        ContextDetector: 上下文助手实例
    """
    return context_assistant
'''

# 确保目录存在
os.makedirs('ui/assistant', exist_ok=True)

# 写入文件
with open('ui/assistant/context_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("成功创建 ui/assistant/context_analyzer.py 文件") 