#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 法律声明更新监听器

此模块负责监听和更新法律声明模板，确保使用最新的法律文本。
主要功能包括：
1. 定期检查法律模板更新
2. 自动下载最新的法律模板
3. 记录更新历史
4. 通知系统法律模板已更新
"""

import os
import json
import time
import logging
import datetime
import tempfile
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import yaml

from src.utils.log_handler import get_logger
from src.utils.config_utils import load_yaml_config, save_config
from src.utils.legal_text_loader import LegalTextLoader

# 配置日志
logger = get_logger("legal_updater")

# 默认配置
DEFAULT_CHECK_INTERVAL = 7  # 默认检查间隔（天）
DEFAULT_UPDATE_URL = "https://api.visionai-clips.com/legal_templates"  # 默认更新服务器
CONFIG_FILE = "legal_updater.json"  # 更新器配置文件


class LegalWatcher:
    """法律声明更新监听器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化法律声明更新监听器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 初始化配置
        self.config = self._load_config(config_path)
        
        # 记录上次检查时间
        self.last_checked = self._get_last_checked()
        
        # 初始化法律文本加载器
        self.text_loader = LegalTextLoader()
        
        # 获取模板路径
        self.templates_dir = self._get_templates_dir()
        
        # 初始化更新历史
        self.update_history = self.config.get("update_history", [])
        
        # 初始化自动更新设置
        self.auto_update = self.config.get("auto_update", True)
        self.check_interval = self.config.get("check_interval", DEFAULT_CHECK_INTERVAL)
        self.update_url = self.config.get("update_url", DEFAULT_UPDATE_URL)
        
        logger.info(f"法律声明更新监听器已初始化，上次检查时间: {self.last_checked}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        if config_path is None:
            # 使用默认配置文件路径
            config_dir = self._get_config_dir()
            config_path = os.path.join(config_dir, CONFIG_FILE)
        
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(config_path):
            default_config = {
                "last_checked": datetime.datetime.now().isoformat(),
                "auto_update": True,
                "check_interval": DEFAULT_CHECK_INTERVAL,
                "update_url": DEFAULT_UPDATE_URL,
                "update_history": []
            }
            
            # 保存默认配置
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            return default_config
        
        # 加载配置文件
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"已加载法律声明更新器配置: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载法律声明更新器配置失败: {str(e)}")
            # 返回默认配置
            return {
                "last_checked": datetime.datetime.now().isoformat(),
                "auto_update": True,
                "check_interval": DEFAULT_CHECK_INTERVAL,
                "update_url": DEFAULT_UPDATE_URL,
                "update_history": []
            }
    
    def _save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 是否保存成功
        """
        config_dir = self._get_config_dir()
        config_path = os.path.join(config_dir, CONFIG_FILE)
        
        # 更新配置
        self.config["last_checked"] = self.last_checked.isoformat()
        self.config["update_history"] = self.update_history
        
        try:
            os.makedirs(config_dir, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存法律声明更新器配置: {config_path}")
            return True
        except Exception as e:
            logger.error(f"保存法律声明更新器配置失败: {str(e)}")
            return False
    
    def _get_config_dir(self) -> str:
        """
        获取配置目录
        
        Returns:
            str: 配置目录路径
        """
        # 尝试获取项目根目录
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent
            config_dir = os.path.join(root_dir, "configs")
        except:
            # 使用用户主目录
            config_dir = os.path.join(os.path.expanduser("~"), ".visionai_clips")
        
        return config_dir
    
    def _get_templates_dir(self) -> str:
        """
        获取法律模板目录
        
        Returns:
            str: 法律模板目录路径
        """
        # 尝试获取项目根目录
        try:
            root_dir = Path(__file__).resolve().parent.parent.parent
            templates_dir = os.path.join(root_dir, "configs")
        except:
            # 使用用户主目录
            templates_dir = os.path.join(os.path.expanduser("~"), ".visionai_clips")
        
        return templates_dir
    
    def _get_last_checked(self) -> datetime.datetime:
        """
        获取上次检查时间
        
        Returns:
            datetime.datetime: 上次检查时间
        """
        last_checked_str = self.config.get("last_checked")
        
        if last_checked_str:
            try:
                return datetime.datetime.fromisoformat(last_checked_str)
            except:
                logger.warning("无法解析上次检查时间，使用当前时间")
                return datetime.datetime.now()
        else:
            # 如果没有上次检查时间，使用当前时间
            return datetime.datetime.now()
    
    def check_updates(self, force: bool = False) -> bool:
        """
        检查法律模板更新
        
        Args:
            force: 是否强制检查更新，忽略检查间隔
            
        Returns:
            bool: 是否有更新
        """
        # 如果不是强制检查，且未达到检查间隔，则跳过
        now = datetime.datetime.now()
        days_since_last_check = (now - self.last_checked).days
        
        if not force and days_since_last_check < self.check_interval:
            logger.info(f"距离上次检查时间（{self.last_checked.strftime('%Y-%m-%d')}）未满{self.check_interval}天，跳过检查")
            return False
        
        # 更新最后检查时间
        self.last_checked = now
        self._save_config()
        
        logger.info(f"正在检查法律模板更新...")
        
        try:
            # 检查是否有更新
            has_update, version = self._check_remote_update()
            
            if has_update:
                logger.info(f"发现法律模板更新，版本: {version}")
                
                # 如果设置为自动更新，则下载更新
                if self.auto_update:
                    success = self.download_new_templates()
                    
                    if success:
                        # 添加更新历史
                        self.update_history.append({
                            "version": version,
                            "date": now.isoformat(),
                            "success": True
                        })
                        
                        # 重新加载模板
                        self.text_loader.reload_templates()
                        
                        # 保存配置
                        self._save_config()
                        
                        logger.info(f"已成功更新法律模板到版本: {version}")
                        return True
                    else:
                        # 添加更新历史
                        self.update_history.append({
                            "version": version,
                            "date": now.isoformat(),
                            "success": False,
                            "error": "下载失败"
                        })
                        
                        # 保存配置
                        self._save_config()
                        
                        logger.error(f"更新法律模板失败")
                        return False
                else:
                    logger.info(f"已禁用自动更新，跳过下载")
                    return True  # 返回True表示有更新，即使没有下载
            else:
                logger.info(f"法律模板已是最新版本")
                return False
        
        except Exception as e:
            logger.error(f"检查法律模板更新时出错: {str(e)}")
            
            # 添加更新历史
            self.update_history.append({
                "date": now.isoformat(),
                "success": False,
                "error": str(e)
            })
            
            # 保存配置
            self._save_config()
            
            return False
    
    def _check_remote_update(self) -> Tuple[bool, str]:
        """
        检查远程服务器是否有更新
        
        Returns:
            Tuple[bool, str]: (是否有更新, 版本号)
        """
        # 在实际项目中，这里应该连接到更新服务器检查更新
        # 本示例使用模拟实现
        
        try:
            # 获取本地模板版本
            local_version = self._get_local_version()
            
            # 模拟从服务器获取远程版本信息
            # 在实际项目中，应该从update_url获取
            # response = requests.get(f"{self.update_url}/version")
            # remote_info = response.json()
            
            # 模拟远程版本信息
            current_year = datetime.datetime.now().year
            current_month = datetime.datetime.now().month
            remote_version = f"{current_year}.{current_month}.15"  # 每月15日更新版本
            
            # 比较版本
            if local_version != remote_version:
                return True, remote_version
            else:
                return False, local_version
            
        except Exception as e:
            logger.error(f"检查远程更新时出错: {str(e)}")
            raise
    
    def _get_local_version(self) -> str:
        """
        获取本地法律模板版本
        
        Returns:
            str: 版本号
        """
        try:
            # 读取legal_templates.yaml中的版本号
            config_path = os.path.join(self.templates_dir, "legal_templates.yaml")
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    # 读取第一行注释中的版本号
                    first_line = f.readline()
                    second_line = f.readline()
                    
                    # 尝试从注释中提取版本号
                    import re
                    version_match = re.search(r'版本\s*[:：]\s*v?([0-9.]+)', second_line)
                    
                    if version_match:
                        return version_match.group(1)
                    else:
                        # 如果没有找到版本号，使用文件修改时间作为版本号
                        mod_time = os.path.getmtime(config_path)
                        dt = datetime.datetime.fromtimestamp(mod_time)
                        return f"{dt.year}.{dt.month}.{dt.day}"
            
            # 如果文件不存在，使用默认版本号
            return "0.0.0"
            
        except Exception as e:
            logger.error(f"获取本地法律模板版本时出错: {str(e)}")
            return "0.0.0"
    
    def download_new_templates(self) -> bool:
        """
        下载最新的法律模板
        
        Returns:
            bool: 是否成功下载
        """
        # 在实际项目中，这里应该从更新服务器下载最新模板
        # 本示例使用模拟实现
        
        try:
            # 真实实现应该从服务器下载模板
            # response = requests.get(f"{self.update_url}/templates")
            # template_data = response.json()
            
            # 模拟下载模板
            logger.info(f"正在下载最新法律模板...")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False, encoding='utf-8') as f:
                temp_path = f.name
                
                # 模拟下载内容，更新当前年份
                current_year = datetime.datetime.now().year
                current_month = datetime.datetime.now().month
                
                # 构建模板内容
                template_content = f"""# VisionAI-ClipsMaster 法律文本模板配置文件
# 版本: {current_year}.{current_month}.15
# 上次更新: {datetime.datetime.now().strftime('%Y-%m-%d')}

templates:
  zh:
    copyright: "本视频由{{app_name}} v{{app_version}}生成，版权归原作者所有 © {current_year}"
    disclaimer: "本内容仅用于技术演示，禁止商用。更新于{current_year}年{current_month}月"
    privacy_notice: "本工具生成的内容可能引用公开数据，使用前请检查内容的合规性"
    terms_of_use: "使用本工具生成的内容时，请遵守相关法律法规和平台规定"
    attribution: "使用{{app_name}}生成"
  
  en:
    copyright: "AI Generated Content by {{app_name}} v{{app_version}}, All Rights Reserved © {current_year}"
    disclaimer: "For technical demonstration only. Updated {current_month}/{current_year}"
    privacy_notice: "Content generated may reference public data. Please verify compliance before use"
    terms_of_use: "When using content generated by this tool, please comply with relevant laws and platform regulations"
    attribution: "Generated with {{app_name}}"

# 不同输出格式的模板配置
format_templates:
  video:
    watermark_position: "bottom-right"
    watermark_opacity: 0.8
    credits_duration: 3.0  # 秒
  
  document:
    header_position: "top"
    footer_position: "bottom"
    include_page_numbers: true
  
  audio:
    credits_position: "end"  # 在音频末尾添加声明
    fade_duration: 2.0  # 秒

# 特殊场景的法律声明
special_cases:
  commercial:
    zh:
      disclaimer: "本内容为商业用途，使用需获得{{app_name}}授权"
      copyright: "本视频由{{app_name}}商业版生成，版权所有 © {current_year}"
    en:
      disclaimer: "Commercial use requires authorization from {{app_name}}"
      copyright: "Generated by {{app_name}} Commercial Edition, All Rights Reserved © {current_year}"
  
  educational:
    zh:
      disclaimer: "本内容用于教育目的，请勿用于其他用途"
      attribution: "由{{app_name}}教育版生成"
    en:
      disclaimer: "Content for educational purposes only"
      attribution: "Generated with {{app_name}} Educational Edition"
"""
                
                # 写入临时文件
                f.write(template_content)
            
            # 将临时文件复制到目标位置
            target_path = os.path.join(self.templates_dir, "legal_templates.yaml")
            
            import shutil
            shutil.copy2(temp_path, target_path)
            
            # 删除临时文件
            os.unlink(temp_path)
            
            logger.info(f"已下载最新法律模板到: {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"下载最新法律模板时出错: {str(e)}")
            return False
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """
        获取更新历史
        
        Returns:
            List[Dict[str, Any]]: 更新历史列表
        """
        return self.update_history
    
    def set_auto_update(self, enabled: bool) -> None:
        """
        设置是否自动更新
        
        Args:
            enabled: 是否启用自动更新
        """
        self.auto_update = enabled
        self.config["auto_update"] = enabled
        self._save_config()
        
        logger.info(f"已{'启用' if enabled else '禁用'}自动更新")
    
    def set_check_interval(self, days: int) -> None:
        """
        设置检查间隔天数
        
        Args:
            days: 检查间隔天数
        """
        if days < 1:
            days = 1
            
        self.check_interval = days
        self.config["check_interval"] = days
        self._save_config()
        
        logger.info(f"已设置检查间隔为{days}天")
    
    def set_update_url(self, url: str) -> None:
        """
        设置更新服务器URL
        
        Args:
            url: 更新服务器URL
        """
        self.update_url = url
        self.config["update_url"] = url
        self._save_config()
        
        logger.info(f"已设置更新服务器URL为: {url}")


# 创建单例实例，方便其他模块导入使用
legal_watcher = LegalWatcher()


# 简化调用的辅助函数
def check_legal_updates(force: bool = False) -> bool:
    """
    检查法律模板更新（简化调用）
    
    Args:
        force: 是否强制检查更新，忽略检查间隔
        
    Returns:
        bool: 是否有更新
    """
    return legal_watcher.check_updates(force)


def download_new_templates() -> bool:
    """
    下载最新的法律模板（简化调用）
    
    Returns:
        bool: 是否成功下载
    """
    return legal_watcher.download_new_templates()


if __name__ == "__main__":
    # 测试代码
    watcher = LegalWatcher()
    
    # 检查更新
    has_update = watcher.check_updates(force=True)
    
    if has_update:
        print("发现法律模板更新")
    else:
        print("法律模板已是最新版本")
    
    # 显示更新历史
    history = watcher.get_update_history()
    print(f"更新历史: {history}") 