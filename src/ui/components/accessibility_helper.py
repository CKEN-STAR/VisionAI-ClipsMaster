#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
无障碍访问助手模块

该模块提供了一系列工具函数和类，帮助UI组件实现无障碍访问功能，
确保应用符合WCAG 2.1 AA标准的要求。
"""

import os
import sys
import json
import logging
import math
import re
from typing import Dict, List, Tuple, Union, Optional, Any

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("accessibility_helper")

# WCAG 2.1 AA标准常量
WCAG_AA_MIN_CONTRAST_NORMAL = 4.5  # 普通文本的最小对比度
WCAG_AA_MIN_CONTRAST_LARGE = 3.0   # 大号文本(18pt+或14pt粗体)的最小对比度

class ColorHelper:
    """颜色处理助手类，提供颜色转换和对比度计算功能"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB值
        
        Args:
            hex_color: 十六进制颜色代码(如 "#FFFFFF")
            
        Returns:
            (R, G, B) 元组，每个值范围为0-255
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            # 简化形式如 #FFF 展开为 #FFFFFF
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """将RGB值转换为十六进制颜色代码
        
        Args:
            rgb: (R, G, B) 元组，每个值范围为0-255
            
        Returns:
            十六进制颜色代码(如 "#FFFFFF")
        """
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}".upper()
    
    @staticmethod
    def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
        """计算颜色的相对亮度(按照WCAG标准)
        
        Args:
            rgb: (R, G, B) 元组，每个值范围为0-255
            
        Returns:
            相对亮度值，范围为0-1
        """
        r, g, b = [x/255 for x in rgb]
        
        # 按WCAG标准进行gamma校正
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        # 计算加权亮度
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @staticmethod
    def calculate_contrast_ratio(color1: str, color2: str) -> float:
        """计算两个颜色之间的对比度比率
        
        Args:
            color1: 第一个十六进制颜色代码
            color2: 第二个十六进制颜色代码
            
        Returns:
            对比度比率
        """
        lum1 = ColorHelper.calculate_luminance(ColorHelper.hex_to_rgb(color1))
        lum2 = ColorHelper.calculate_luminance(ColorHelper.hex_to_rgb(color2))
        
        # 确保亮度值较大的在分子位置
        bright = max(lum1, lum2)
        dark = min(lum1, lum2)
        
        # WCAG对比度公式
        return (bright + 0.05) / (dark + 0.05)
    
    @staticmethod
    def verify_contrast(foreground: str, background: str, large_text: bool = False) -> Dict[str, Any]:
        """验证前景色和背景色的对比度是否符合WCAG AA标准
        
        Args:
            foreground: 前景色(文本颜色)十六进制代码
            background: 背景色十六进制代码
            large_text: 是否为大号文本(18pt+或14pt粗体)
            
        Returns:
            包含验证结果的字典
        """
        contrast = ColorHelper.calculate_contrast_ratio(foreground, background)
        min_contrast = WCAG_AA_MIN_CONTRAST_LARGE if large_text else WCAG_AA_MIN_CONTRAST_NORMAL
        
        return {
            "contrast_ratio": contrast,
            "min_required": min_contrast,
            "passes_aa": contrast >= min_contrast,
            "text_size": "large" if large_text else "normal"
        }
    
    @staticmethod
    def suggest_accessible_colors(color: str, target_contrast: float = 4.5) -> Dict[str, str]:
        """基于给定颜色，推荐符合无障碍要求的配色
        
        Args:
            color: 基础颜色十六进制代码
            target_contrast: 目标对比度
            
        Returns:
            建议的前景色和背景色
        """
        base_rgb = ColorHelper.hex_to_rgb(color)
        base_luminance = ColorHelper.calculate_luminance(base_rgb)
        
        # 如果基础颜色较亮，推荐深色文本
        if base_luminance > 0.5:
            # 从基础颜色生成合适的深色
            # 尝试逐步降低亮度直到达到目标对比度
            for factor in [0.8, 0.6, 0.4, 0.2, 0]:
                r = max(0, int(base_rgb[0] * factor))
                g = max(0, int(base_rgb[1] * factor))
                b = max(0, int(base_rgb[2] * factor))
                
                dark_color = ColorHelper.rgb_to_hex((r, g, b))
                if ColorHelper.calculate_contrast_ratio(dark_color, color) >= target_contrast:
                    return {
                        "background": color,
                        "foreground": dark_color
                    }
            
            # 如果无法得到符合要求的颜色，使用纯黑
            return {
                "background": color,
                "foreground": "#000000"
            }
        else:
            # 基础颜色较暗，推荐亮色文本
            # 尝试逐步提高亮度
            for factor in [1.2, 1.5, 2.0, 3.0, 4.0]:
                r = min(255, int(base_rgb[0] * factor))
                g = min(255, int(base_rgb[1] * factor))
                b = min(255, int(base_rgb[2] * factor))
                
                light_color = ColorHelper.rgb_to_hex((r, g, b))
                if ColorHelper.calculate_contrast_ratio(light_color, color) >= target_contrast:
                    return {
                        "background": color,
                        "foreground": light_color
                    }
            
            # 如果无法得到符合要求的颜色，使用纯白
            return {
                "background": color,
                "foreground": "#FFFFFF"
            }

class KeyboardNavigationHelper:
    """键盘导航助手类，提供键盘导航相关功能"""
    
    @staticmethod
    def get_standard_key_mapping() -> Dict[str, str]:
        """获取标准键盘映射表
        
        Returns:
            标准键盘快捷键映射
        """
        return {
            # 应用通用操作
            "app_help": "F1",
            "app_settings": "Alt+S",
            "app_exit": "Alt+F4",
            
            # 文件操作
            "file_open": "Ctrl+O",
            "file_save": "Ctrl+S",
            "file_save_as": "Ctrl+Shift+S",
            "file_export": "Ctrl+E",
            
            # 编辑操作
            "edit_undo": "Ctrl+Z",
            "edit_redo": "Ctrl+Y",
            "edit_cut": "Ctrl+X",
            "edit_copy": "Ctrl+C",
            "edit_paste": "Ctrl+V",
            "edit_select_all": "Ctrl+A",
            
            # 视图操作
            "view_zoom_in": "Ctrl+Plus",
            "view_zoom_out": "Ctrl+Minus",
            "view_reset_zoom": "Ctrl+0",
            
            # 导航操作
            "navigate_next": "Tab",
            "navigate_previous": "Shift+Tab",
            "navigate_menu": "Alt",
            "activate_element": "Enter",
            "escape_dialog": "Esc"
        }
    
    @staticmethod
    def create_keyboard_action_guide() -> str:
        """创建键盘操作指南HTML
        
        Returns:
            键盘操作指南的HTML字符串
        """
        key_mapping = KeyboardNavigationHelper.get_standard_key_mapping()
        
        html = """
        <div class="keyboard-guide" role="complementary" aria-label="键盘快捷键指南">
            <h2>键盘快捷键</h2>
            <table aria-label="快捷键列表">
                <thead>
                    <tr>
                        <th scope="col">功能</th>
                        <th scope="col">快捷键</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # 按类别组织快捷键
        categories = {
            "应用操作": ["app_help", "app_settings", "app_exit"],
            "文件操作": ["file_open", "file_save", "file_save_as", "file_export"],
            "编辑操作": ["edit_undo", "edit_redo", "edit_cut", "edit_copy", "edit_paste", "edit_select_all"],
            "视图操作": ["view_zoom_in", "view_zoom_out", "view_reset_zoom"],
            "导航操作": ["navigate_next", "navigate_previous", "navigate_menu", "activate_element", "escape_dialog"]
        }
        
        # 功能名称映射
        function_names = {
            "app_help": "帮助",
            "app_settings": "设置",
            "app_exit": "退出",
            "file_open": "打开文件",
            "file_save": "保存",
            "file_save_as": "另存为",
            "file_export": "导出",
            "edit_undo": "撤销",
            "edit_redo": "重做",
            "edit_cut": "剪切",
            "edit_copy": "复制",
            "edit_paste": "粘贴",
            "edit_select_all": "全选",
            "view_zoom_in": "放大",
            "view_zoom_out": "缩小",
            "view_reset_zoom": "重置缩放",
            "navigate_next": "下一项",
            "navigate_previous": "上一项",
            "navigate_menu": "菜单导航",
            "activate_element": "激活元素",
            "escape_dialog": "关闭对话框"
        }
        
        for category, keys in categories.items():
            html += f"""
                <tr>
                    <th scope="row" colspan="2">{category}</th>
                </tr>
            """
            
            for key in keys:
                if key in key_mapping:
                    html += f"""
                        <tr>
                            <td>{function_names.get(key, key)}</td>
                            <td><kbd>{key_mapping[key]}</kbd></td>
                        </tr>
                    """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html

class ScreenReaderHelper:
    """屏幕阅读器助手类，提供屏幕阅读器相关功能"""
    
    @staticmethod
    def create_aria_label(element_type: str, content: str, action: Optional[str] = None) -> str:
        """创建ARIA标签
        
        Args:
            element_type: 元素类型
            content: 元素内容
            action: 可选的操作描述
            
        Returns:
            ARIA标签
        """
        if action:
            return f"{element_type}：{content}，{action}"
        return f"{element_type}：{content}"
    
    @staticmethod
    def generate_screen_reader_attrs(role: str, label: str, expanded: bool = None,
                                    required: bool = None, controls: str = None,
                                    described_by: str = None, level: int = None) -> Dict[str, str]:
        """生成屏幕阅读器属性
        
        Args:
            role: ARIA角色
            label: 标签文本
            expanded: 是否展开(可选)
            required: 是否必填(可选)
            controls: 控制的元素ID(可选)
            described_by: 描述元素的ID(可选)
            level: 级别(用于标题)(可选)
            
        Returns:
            ARIA属性字典
        """
        attrs = {
            "role": role,
            "aria-label": label
        }
        
        if expanded is not None:
            attrs["aria-expanded"] = "true" if expanded else "false"
            
        if required is not None:
            attrs["aria-required"] = "true" if required else "false"
            
        if controls:
            attrs["aria-controls"] = controls
            
        if described_by:
            attrs["aria-describedby"] = described_by
            
        if level and role == "heading":
            attrs["aria-level"] = str(level)
            
        return attrs
    
    @staticmethod
    def validate_element_accessibility(element_html: str) -> Dict[str, Any]:
        """验证元素的无障碍访问合规性
        
        Args:
            element_html: 元素的HTML代码
            
        Returns:
            验证结果字典
        """
        results = {
            "has_role": False,
            "has_label": False,
            "image_has_alt": True,  # 默认为True，只有检测到image且无alt时为False
            "input_has_label": True,  # 默认为True，只有检测到input且无label时为False
            "issues": []
        }
        
        # 检查元素是否有ARIA角色
        if 'role="' in element_html:
            results["has_role"] = True
        else:
            results["issues"].append("缺少ARIA角色")
        
        # 检查元素是否有ARIA标签
        if 'aria-label="' in element_html:
            results["has_label"] = True
        else:
            # 对于某些元素，需要明确的ARIA标签
            if '<button' in element_html or '<a ' in element_html:
                if not ('<button>[^<>]+</button>' in element_html or '<a[^<>]+>[^<>]+</a>' in element_html):
                    results["has_label"] = False
                    results["issues"].append("按钮或链接缺少可访问标签")
        
        # 检查图片是否有alt文本
        img_matches = re.findall(r'<img[^>]*>', element_html)
        for img in img_matches:
            if 'alt="' not in img and 'aria-hidden="true"' not in img:
                results["image_has_alt"] = False
                results["issues"].append("图片缺少alt文本")
        
        # 检查输入框是否有标签
        input_matches = re.findall(r'<input[^>]*>', element_html)
        for input_elem in input_matches:
            # 忽略隐藏的输入框
            if 'type="hidden"' in input_elem:
                continue
                
            if 'id="' in input_elem:
                # 提取ID
                id_match = re.search(r'id="([^"]+)"', input_elem)
                if id_match:
                    input_id = id_match.group(1)
                    # 检查是否有关联的label
                    if f'for="{input_id}"' not in element_html and 'aria-label="' not in input_elem:
                        results["input_has_label"] = False
                        results["issues"].append("输入框缺少关联标签")
            elif 'aria-label="' not in input_elem:
                results["input_has_label"] = False
                results["issues"].append("输入框缺少关联标签")
        
        return results

class AccessibilityConfig:
    """无障碍配置管理器"""
    
    _instance = None
    _config_file = "configs/accessibility_config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AccessibilityConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def __init__(self):
        # 初始化已经在__new__中完成
        pass
    
    def _load_config(self):
        """加载无障碍配置"""
        default_config = {
            "screen_reader_enabled": False,
            "high_contrast_enabled": False,
            "contrast_ratio": 4.5,
            "font_size_multiplier": 1.0,
            "keyboard_navigation_enabled": True,
            "audio_feedback_enabled": False,
            "focus_visible": True,
            "reduced_motion": False,
            "auto_alt_text": True,
            "theme": "default",
            "accessible_themes": ["default", "high_contrast", "large_print", "reduced_motion"]
        }
        
        self.config = default_config
        
        # 尝试从文件加载配置
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 更新配置
                    self.config.update(user_config)
        except Exception as e:
            logger.error(f"加载无障碍配置失败: {e}")
    
    def save_config(self):
        """保存无障碍配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            
            # 保存配置
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                
            logger.info("已保存无障碍配置")
            return True
        except Exception as e:
            logger.error(f"保存无障碍配置失败: {e}")
            return False
    
    def get_config(self, key=None):
        """获取无障碍配置
        
        Args:
            key: 配置键名，不指定则返回全部配置
            
        Returns:
            配置值或配置字典
        """
        if key is None:
            return self.config
        return self.config.get(key)
    
    def set_config(self, key, value):
        """设置无障碍配置
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            是否设置成功
        """
        if key in self.config:
            self.config[key] = value
            return True
        return False
    
    def apply_theme(self, theme_name):
        """应用主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            主题配置字典
        """
        # 主题配置
        themes = {
            "default": {
                "contrast_ratio": 4.5,
                "font_size_multiplier": 1.0,
                "reduced_motion": False,
                "high_contrast_enabled": False,
                "colors": {
                    "text": "#000000",
                    "background": "#FFFFFF",
                    "primary": "#0078D7",
                    "secondary": "#6C757D",
                    "accent": "#28A745",
                    "error": "#DC3545"
                }
            },
            "high_contrast": {
                "contrast_ratio": 7.0,
                "font_size_multiplier": 1.0,
                "reduced_motion": True,
                "high_contrast_enabled": True,
                "colors": {
                    "text": "#FFFFFF",
                    "background": "#000000",
                    "primary": "#FFFF00",
                    "secondary": "#00FFFF",
                    "accent": "#FF00FF",
                    "error": "#FF0000"
                }
            },
            "large_print": {
                "contrast_ratio": 4.5,
                "font_size_multiplier": 1.5,
                "reduced_motion": True,
                "high_contrast_enabled": False,
                "colors": {
                    "text": "#000000",
                    "background": "#FFFFFF",
                    "primary": "#0078D7",
                    "secondary": "#6C757D",
                    "accent": "#28A745",
                    "error": "#DC3545"
                }
            },
            "reduced_motion": {
                "contrast_ratio": 4.5,
                "font_size_multiplier": 1.0,
                "reduced_motion": True,
                "high_contrast_enabled": False,
                "colors": {
                    "text": "#000000",
                    "background": "#FFFFFF",
                    "primary": "#0078D7",
                    "secondary": "#6C757D",
                    "accent": "#28A745",
                    "error": "#DC3545"
                }
            }
        }
        
        # 获取指定主题
        theme = themes.get(theme_name, themes["default"])
        
        # 应用主题配置
        for key, value in theme.items():
            if key != "colors":
                self.config[key] = value
        
        # 更新主题名称
        self.config["theme"] = theme_name
        
        # 保存配置
        self.save_config()
        
        return theme


# 导出便捷函数

def check_contrast(foreground: str, background: str, large_text: bool = False) -> bool:
    """检查前景色和背景色的对比度是否符合WCAG AA标准
    
    Args:
        foreground: 前景色(文本颜色)十六进制代码
        background: 背景色十六进制代码
        large_text: 是否为大号文本
        
    Returns:
        是否符合WCAG AA标准
    """
    return ColorHelper.verify_contrast(foreground, background, large_text)["passes_aa"]

def get_accessible_colors(color: str, target_contrast: float = 4.5) -> Dict[str, str]:
    """获取无障碍配色方案
    
    Args:
        color: 基础颜色
        target_contrast: 目标对比度
        
    Returns:
        前景色和背景色配色方案
    """
    return ColorHelper.suggest_accessible_colors(color, target_contrast)

def get_accessibility_config():
    """获取全局无障碍配置"""
    return AccessibilityConfig()

def get_screen_reader_attributes(role: str, label: str, **kwargs) -> Dict[str, str]:
    """获取屏幕阅读器属性
    
    Args:
        role: ARIA角色
        label: 标签文本
        **kwargs: 其他ARIA属性
        
    Returns:
        ARIA属性字典
    """
    return ScreenReaderHelper.generate_screen_reader_attrs(role, label, **kwargs)


# 模块测试代码
if __name__ == "__main__":
    # 测试色彩对比度
    test_colors = [
        ("#000000", "#FFFFFF"),  # 黑白
        ("#FFFFFF", "#000000"),  # 白黑
        ("#777777", "#FFFFFF"),  # 灰白
        ("#FFFFFF", "#FFFF00"),  # 白黄
        ("#000000", "#0078D7"),  # 黑蓝
        ("#FFFFFF", "#FF0000")   # 白红
    ]
    
    print("颜色对比度测试 (WCAG AA 标准):")
    for fg, bg in test_colors:
        result = ColorHelper.verify_contrast(fg, bg)
        status = "通过" if result["passes_aa"] else "未通过"
        print(f"  {fg} / {bg}: 对比度 = {result['contrast_ratio']:.2f}, 最低要求 = {result['min_required']} - {status}")
    
    # 测试键盘导航
    key_mapping = KeyboardNavigationHelper.get_standard_key_mapping()
    print("\n标准键盘映射:")
    for action, key in list(key_mapping.items())[:5]:  # 只显示前5项
        print(f"  {action}: {key}")
    
    # 测试无障碍配置
    config = get_accessibility_config()
    
    # 应用高对比度主题
    print("\n应用高对比度主题:")
    theme = config.apply_theme("high_contrast")
    for key, value in theme.items():
        if key == "colors":
            print(f"  颜色方案: {len(value)}个颜色")
        else:
            print(f"  {key}: {value}")
    
    print("\n无障碍测试完成") 