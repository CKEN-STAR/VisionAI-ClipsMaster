#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地化管理器

该模块负责VisionAI-ClipsMaster应用程序的国际化和本地化处理，
包括语言切换、文本资源加载、日期时间格式处理等功能。
"""

import os
import sys
import json
import logging
import locale
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("locale_manager")

# 常量定义
DEFAULT_LANGUAGE = "zh_CN"
FALLBACK_LANGUAGE = "en_US"
CONFIG_FILE = "configs/locale_config.json"
LOCALES_DIR = "resources/locales"

class LocaleManager:
    """本地化管理器类
    
    负责处理应用程序的国际化和本地化功能，包括加载、
    保存语言设置，提供翻译服务，以及处理与区域相关的格式。
    
    Attributes:
        current_locale: 当前语言设置
        translations: 已加载的翻译数据
        supported_locales: 支持的语言列表
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(LocaleManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化本地化管理器"""
        # 避免重复初始化
        if self._initialized:
            return
            
        # 初始化属性
        self.current_locale = DEFAULT_LANGUAGE
        self.translations = {}
        self.supported_locales = []
        self.date_formats = {}
        self.time_formats = {}
        self.number_formats = {}
        
        # 加载配置
        self._load_config()
        
        # 加载所有支持的语言
        self._discover_locales()
        
        # 加载当前语言的翻译
        self._load_translations(self.current_locale)
        
        # 标记为已初始化
        self._initialized = True
        
        logger.info(f"本地化管理器初始化完成，当前语言：{self.current_locale}")
    
    def _discover_locales(self) -> None:
        """发现所有支持的语言"""
        # 检查语言目录是否存在
        locales_path = Path(LOCALES_DIR)
        if not locales_path.exists():
            logger.warning(f"语言资源目录不存在：{LOCALES_DIR}")
            # 确保至少有默认语言和回退语言
            self.supported_locales = [DEFAULT_LANGUAGE, FALLBACK_LANGUAGE]
            return
            
        # 搜索所有语言文件
        locale_files = list(locales_path.glob("*.json"))
        
        if not locale_files:
            logger.warning("未找到语言资源文件")
            self.supported_locales = [DEFAULT_LANGUAGE, FALLBACK_LANGUAGE]
            return
            
        # 提取语言代码
        self.supported_locales = [f.stem for f in locale_files]
        
        # 确保默认语言和回退语言在列表中
        if DEFAULT_LANGUAGE not in self.supported_locales:
            self.supported_locales.append(DEFAULT_LANGUAGE)
        if FALLBACK_LANGUAGE not in self.supported_locales:
            self.supported_locales.append(FALLBACK_LANGUAGE)
            
        logger.info(f"已发现支持的语言：{', '.join(self.supported_locales)}")
    
    def _load_config(self) -> None:
        """加载语言配置"""
        config_path = Path(CONFIG_FILE)
        
        # 如果配置文件存在，则加载
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 读取当前语言设置
                if 'current_locale' in config and config['current_locale']:
                    self.current_locale = config['current_locale']
                    
                # 读取日期时间格式
                if 'date_formats' in config:
                    self.date_formats = config['date_formats']
                    
                if 'time_formats' in config:
                    self.time_formats = config['time_formats']
                    
                if 'number_formats' in config:
                    self.number_formats = config['number_formats']
                    
                logger.info(f"已加载语言配置，当前语言：{self.current_locale}")
            except Exception as e:
                logger.error(f"加载语言配置出错：{e}")
        else:
            logger.warning(f"语言配置文件不存在，使用默认配置：{DEFAULT_LANGUAGE}")
            # 创建默认配置
            self._save_config()
    
    def _save_config(self) -> bool:
        """保存语言配置
        
        Returns:
            是否成功保存
        """
        config_path = Path(CONFIG_FILE)
        
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 准备配置数据
            config = {
                'current_locale': self.current_locale,
                'supported_locales': self.supported_locales,
                'date_formats': self.date_formats,
                'time_formats': self.time_formats,
                'number_formats': self.number_formats
            }
            
            # 写入配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            logger.info(f"已保存语言配置：{self.current_locale}")
            return True
        except Exception as e:
            logger.error(f"保存语言配置出错：{e}")
            return False
    
    def _load_translations(self, locale_code: str) -> bool:
        """加载指定语言的翻译数据
        
        Args:
            locale_code: 语言代码
            
        Returns:
            是否成功加载
        """
        # 检查语言文件是否存在
        locale_path = Path(LOCALES_DIR) / f"{locale_code}.json"
        
        if not locale_path.exists():
            # 如果指定的语言文件不存在，尝试加载回退语言
            if locale_code != FALLBACK_LANGUAGE:
                logger.warning(f"语言文件不存在：{locale_path}，尝试使用回退语言：{FALLBACK_LANGUAGE}")
                return self._load_translations(FALLBACK_LANGUAGE)
            else:
                # 如果回退语言也不存在，使用内置的最小翻译
                logger.error(f"回退语言文件不存在：{locale_path}，使用内置最小翻译")
                self.translations = self._get_minimal_translations()
                return False
                
        try:
            # 加载翻译文件
            with open(locale_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                
            # 更新翻译数据
            self.translations = translations
            
            logger.info(f"已加载语言翻译：{locale_code}")
            return True
        except Exception as e:
            logger.error(f"加载语言翻译出错：{e}")
            # 使用内置的最小翻译
            self.translations = self._get_minimal_translations()
            return False
    
    def _get_minimal_translations(self) -> Dict[str, str]:
        """获取最小的内置翻译数据
        
        当无法加载任何翻译文件时使用
        
        Returns:
            最小翻译数据
        """
        # 英文的最小翻译集
        en_translations = {
            "app_title": "VisionAI ClipsMaster",
            "main_menu": "Main Menu",
            "file": "File",
            "edit": "Edit",
            "view": "View",
            "help": "Help",
            "import": "Import",
            "export": "Export",
            "settings": "Settings",
            "about": "About",
            "error": "Error",
            "warning": "Warning",
            "info": "Information",
            "success": "Success"
        }
        
        # 中文的最小翻译集
        zh_translations = {
            "app_title": "VisionAI 短视频剪辑大师",
            "main_menu": "主菜单",
            "file": "文件",
            "edit": "编辑",
            "view": "视图",
            "help": "帮助",
            "import": "导入",
            "export": "导出",
            "settings": "设置",
            "about": "关于",
            "error": "错误",
            "warning": "警告",
            "info": "信息",
            "success": "成功"
        }
        
        # 根据当前语言返回相应的翻译
        if self.current_locale.startswith("zh"):
            return zh_translations
        else:
            return en_translations
    
    def set_locale(self, locale_code: str) -> bool:
        """设置应用程序语言
        
        Args:
            locale_code: 语言代码
            
        Returns:
            是否成功设置
        """
        # 检查是否支持该语言
        if locale_code not in self.supported_locales:
            logger.warning(f"不支持的语言：{locale_code}")
            return False
            
        # 更新当前语言
        self.current_locale = locale_code
        
        # 加载翻译
        success = self._load_translations(locale_code)
        
        # 保存配置
        self._save_config()
        
        # 尝试设置系统区域
        try:
            system_locale = locale_code.replace('_', '-')
            locale.setlocale(locale.LC_ALL, system_locale)
            logger.info(f"已设置系统区域：{system_locale}")
        except locale.Error:
            logger.warning(f"设置系统区域失败：{locale_code}")
            # 尝试使用语言代码的前两个字符
            try:
                short_locale = locale_code[:2]
                locale.setlocale(locale.LC_ALL, short_locale)
                logger.info(f"已设置系统区域(简化)：{short_locale}")
            except locale.Error:
                logger.warning(f"设置简化系统区域失败：{short_locale}")
                
        logger.info(f"已切换应用程序语言：{locale_code}")
        return success
    
    def get_text(self, key: str, default: Optional[str] = None) -> str:
        """获取翻译文本
        
        Args:
            key: 文本键名
            default: 默认值，如果未找到翻译则返回此值
            
        Returns:
            翻译后的文本
        """
        # 检查键是否存在于翻译中
        if key in self.translations:
            return self.translations[key]
            
        # 如果找不到翻译，返回默认值或键名
        if default is not None:
            return default
        else:
            # 记录缺失的翻译
            logger.warning(f"缺失的翻译键：{key}")
            return key
    
    def get_formatted_date(self, date: Optional[datetime] = None, format_key: str = "default") -> str:
        """获取格式化的日期字符串
        
        Args:
            date: 日期对象，默认为当前日期
            format_key: 格式键名
            
        Returns:
            格式化的日期字符串
        """
        if date is None:
            date = datetime.now()
            
        # 获取日期格式
        date_format = self._get_date_format(format_key)
        
        # 格式化日期
        return date.strftime(date_format)
    
    def get_formatted_time(self, time: Optional[datetime] = None, format_key: str = "default") -> str:
        """获取格式化的时间字符串
        
        Args:
            time: 时间对象，默认为当前时间
            format_key: 格式键名
            
        Returns:
            格式化的时间字符串
        """
        if time is None:
            time = datetime.now()
            
        # 获取时间格式
        time_format = self._get_time_format(format_key)
        
        # 格式化时间
        return time.strftime(time_format)
    
    def get_formatted_number(self, number: float, format_key: str = "default") -> str:
        """获取格式化的数字字符串
        
        Args:
            number: 数字
            format_key: 格式键名
            
        Returns:
            格式化的数字字符串
        """
        # 获取数字格式
        number_format = self._get_number_format(format_key)
        
        # 处理特殊格式
        if format_key == "percentage":
            # 百分比格式
            return f"{number * 100:.1f}%"
        elif format_key == "currency":
            # 货币格式
            if self.current_locale == "zh_CN":
                return f"￥{number:.2f}"
            elif self.current_locale == "ja_JP":
                return f"¥{number:.0f}"
            else:
                return f"${number:.2f}"
        else:
            # 一般数字格式
            return number_format.format(number)
    
    def _get_date_format(self, format_key: str) -> str:
        """获取日期格式字符串
        
        Args:
            format_key: 格式键名
            
        Returns:
            日期格式字符串
        """
        # 默认日期格式
        default_formats = {
            "zh_CN": "%Y年%m月%d日",
            "en_US": "%m/%d/%Y",
            "ja_JP": "%Y年%m月%d日"
        }
        
        # 如果存在自定义格式，优先使用
        if self.current_locale in self.date_formats and format_key in self.date_formats[self.current_locale]:
            return self.date_formats[self.current_locale][format_key]
            
        # 否则使用默认格式
        if self.current_locale in default_formats:
            return default_formats[self.current_locale]
        else:
            return "%Y-%m-%d"  # ISO格式作为最后的回退
    
    def _get_time_format(self, format_key: str) -> str:
        """获取时间格式字符串
        
        Args:
            format_key: 格式键名
            
        Returns:
            时间格式字符串
        """
        # 默认时间格式
        default_formats = {
            "zh_CN": "%H:%M:%S",
            "en_US": "%I:%M:%S %p",
            "ja_JP": "%H時%M分%S秒"
        }
        
        # 如果存在自定义格式，优先使用
        if self.current_locale in self.time_formats and format_key in self.time_formats[self.current_locale]:
            return self.time_formats[self.current_locale][format_key]
            
        # 否则使用默认格式
        if self.current_locale in default_formats:
            return default_formats[self.current_locale]
        else:
            return "%H:%M:%S"  # 24小时制作为最后的回退
    
    def _get_number_format(self, format_key: str) -> str:
        """获取数字格式字符串
        
        Args:
            format_key: 格式键名
            
        Returns:
            数字格式字符串
        """
        # 默认数字格式
        default_formats = {
            "default": "{:.2f}",
            "integer": "{:d}",
            "percentage": "{:.1%}",
            "scientific": "{:.2e}"
        }
        
        # 如果存在自定义格式，优先使用
        if format_key in self.number_formats:
            return self.number_formats[format_key]
            
        # 否则使用默认格式
        if format_key in default_formats:
            return default_formats[format_key]
        else:
            return "{}"  # 简单字符串转换作为最后的回退
    
    def get_supported_locales(self) -> List[Tuple[str, str]]:
        """获取支持的语言列表
        
        Returns:
            语言代码和名称的元组列表
        """
        # 语言名称映射
        locale_names = {
            "zh_CN": "简体中文",
            "zh_TW": "繁體中文",
            "en_US": "English (US)",
            "en_GB": "English (UK)",
            "ja_JP": "日本語",
            "ko_KR": "한국어",
            "fr_FR": "Français",
            "de_DE": "Deutsch",
            "es_ES": "Español",
            "ru_RU": "Русский"
        }
        
        # 构建结果列表
        result = []
        for locale_code in self.supported_locales:
            locale_name = locale_names.get(locale_code, locale_code)
            result.append((locale_code, locale_name))
            
        return result
    
    def get_current_locale(self) -> str:
        """获取当前语言代码
        
        Returns:
            当前语言代码
        """
        return self.current_locale
    
    def get_locale_name(self, locale_code: Optional[str] = None) -> str:
        """获取语言名称
        
        Args:
            locale_code: 语言代码，不指定则使用当前语言
            
        Returns:
            语言名称
        """
        if locale_code is None:
            locale_code = self.current_locale
            
        # 语言名称映射
        locale_names = {
            "zh_CN": "简体中文",
            "zh_TW": "繁體中文",
            "en_US": "English (US)",
            "en_GB": "English (UK)",
            "ja_JP": "日本語",
            "ko_KR": "한국어",
            "fr_FR": "Français",
            "de_DE": "Deutsch",
            "es_ES": "Español",
            "ru_RU": "Русский"
        }
        
        return locale_names.get(locale_code, locale_code)

# 单例实例
_locale_manager = None

def get_locale_manager() -> LocaleManager:
    """获取本地化管理器实例
    
    Returns:
        本地化管理器实例
    """
    global _locale_manager
    if _locale_manager is None:
        _locale_manager = LocaleManager()
    return _locale_manager

# 便捷函数

def get_text(key: str, default: Optional[str] = None) -> str:
    """获取翻译文本
    
    Args:
        key: 文本键名
        default: 默认值，如果未找到翻译则返回此值
        
    Returns:
        翻译后的文本
    """
    return get_locale_manager().get_text(key, default)

def set_locale(locale_code: str) -> bool:
    """设置应用程序语言
    
    Args:
        locale_code: 语言代码
        
    Returns:
        是否成功设置
    """
    return get_locale_manager().set_locale(locale_code)

def get_current_locale() -> str:
    """获取当前语言代码
    
    Returns:
        当前语言代码
    """
    return get_locale_manager().get_current_locale()

def get_formatted_date(date: Optional[datetime] = None, format_key: str = "default") -> str:
    """获取格式化的日期字符串
    
    Args:
        date: 日期对象，默认为当前日期
        format_key: 格式键名
        
    Returns:
        格式化的日期字符串
    """
    return get_locale_manager().get_formatted_date(date, format_key)

def get_formatted_time(time: Optional[datetime] = None, format_key: str = "default") -> str:
    """获取格式化的时间字符串
    
    Args:
        time: 时间对象，默认为当前时间
        format_key: 格式键名
        
    Returns:
        格式化的时间字符串
    """
    return get_locale_manager().get_formatted_time(time, format_key)

# 模块测试
if __name__ == "__main__":
    # 测试本地化功能
    manager = get_locale_manager()
    
    print("=== 本地化管理器测试 ===")
    print(f"当前语言: {manager.get_current_locale()} ({manager.get_locale_name()})")
    print(f"支持的语言: {manager.get_supported_locales()}")
    
    # 测试语言切换
    print("\n=== 语言切换测试 ===")
    for locale_code in ["zh_CN", "en_US", "ja_JP"]:
        success = manager.set_locale(locale_code)
        print(f"切换到 {locale_code}: {'成功' if success else '失败'}")
        print(f"应用标题: {manager.get_text('app_title')}")
        print(f"导出按钮: {manager.get_text('export')}")
        print(f"当前日期: {manager.get_formatted_date()}")
        print(f"当前时间: {manager.get_formatted_time()}")
        print(f"数字格式: {manager.get_formatted_number(1234.567)}")
        print("") 