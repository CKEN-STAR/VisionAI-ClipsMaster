#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本更新监听器

自动检查新版本并下载schema文件作为需要。
支持定期检查和手动触发更新。
"""

import os
import sys
import json
import time
import logging
import threading
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("version_updater")

class VersionWatcher:
    """版本更新监听器类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化版本更新监听器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.config_path = config_path or os.path.join(root_dir, 'configs', 'version_updater.json')
        self.schema_dir = os.path.join(root_dir, 'configs')
        self.version_spec_path = os.path.join(root_dir, 'configs', 'version_specifications.json')
        
        # 默认配置
        self.config = {
            "last_checked": None,
            "auto_update": True,
            "check_interval": 24,  # 小时
            "update_url": "https://jianying.com/api/version",
            "update_history": [],
            "current_version": "3.0.0"
        }
        
        # 加载配置
        self._load_config()
        
        # 更新线程
        self.update_thread = None
        self.stop_event = threading.Event()
        
        # 如果开启自动更新，启动更新线程
        if self.config["auto_update"]:
            self.start_auto_updater()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"从 {self.config_path} 加载配置成功")
            else:
                logger.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
                self._save_config()  # 创建默认配置文件
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
    
    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到 {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def start_auto_updater(self) -> None:
        """启动自动更新线程"""
        if self.update_thread and self.update_thread.is_alive():
            logger.info("更新线程已在运行")
            return
            
        logger.info("启动自动更新线程")
        self.stop_event.clear()
        self.update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self.update_thread.start()
    
    def stop_auto_updater(self) -> None:
        """停止自动更新线程"""
        if not self.update_thread or not self.update_thread.is_alive():
            logger.info("更新线程未在运行")
            return
            
        logger.info("停止自动更新线程")
        self.stop_event.set()
        self.update_thread.join(timeout=1.0)
        if self.update_thread.is_alive():
            logger.warning("更新线程未能正常停止")
    
    def _auto_update_loop(self) -> None:
        """自动更新循环"""
        while not self.stop_event.is_set():
            try:
                # 检查是否需要更新
                self._check_update_needed()
                
                # 等待下一次检查
                for _ in range(3600):  # 每小时检查一次是否需要更新
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"自动更新循环出错: {e}")
                time.sleep(60)  # 出错后休息一分钟
    
    def _check_update_needed(self) -> bool:
        """
        检查是否需要更新
        
        Returns:
            bool: 是否需要更新
        """
        # 获取上次检查时间
        last_checked = self.config.get("last_checked")
        
        if last_checked:
            # 将字符串转换为datetime对象
            try:
                last_checked_dt = datetime.fromisoformat(last_checked)
            except ValueError:
                # 如果格式不正确，视为从未检查
                last_checked_dt = datetime.min
        else:
            # 如果从未检查，设置为最早日期
            last_checked_dt = datetime.min
        
        # 计算下次检查时间
        check_interval = timedelta(hours=self.config.get("check_interval", 24))
        next_check_dt = last_checked_dt + check_interval
        
        # 如果尚未到下次检查时间，则跳过
        if datetime.now() < next_check_dt:
            logger.debug(f"尚未到下次检查时间，下次检查时间: {next_check_dt}")
            return False
        
        # 执行更新检查
        logger.info("执行版本更新检查")
        self.check_updates()
        
        return True
    
    def check_updates(self, force: bool = False) -> bool:
        """
        检查更新
        
        Args:
            force: 是否强制检查更新，忽略上次检查时间
            
        Returns:
            bool: 是否有更新
        """
        now = datetime.now()
        
        # 更新上次检查时间
        self.config["last_checked"] = now.isoformat()
        self._save_config()
        
        try:
            # 检查是否有更新
            has_update, new_version = self._check_remote_update()
            
            if has_update:
                logger.info(f"发现新版本: {new_version}")
                
                # 如果设置为自动更新，则下载更新
                if self.config["auto_update"]:
                    success = self.download_new_schema(new_version)
                    
                    if success:
                        # 添加更新历史
                        self.config["update_history"].append({
                            "version": new_version,
                            "date": now.isoformat(),
                            "success": True
                        })
                        
                        # 更新当前版本
                        self.config["current_version"] = new_version
                        
                        # 保存配置
                        self._save_config()
                        
                        logger.info(f"已成功更新架构文件到版本: {new_version}")
                        return True
                    else:
                        # 添加更新历史
                        self.config["update_history"].append({
                            "version": new_version,
                            "date": now.isoformat(),
                            "success": False,
                            "error": "下载失败"
                        })
                        
                        # 保存配置
                        self._save_config()
                        
                        logger.error(f"更新架构文件失败")
                        return False
                else:
                    logger.info(f"已禁用自动更新，跳过下载")
                    return True  # 返回True表示有更新，即使没有下载
            else:
                logger.info(f"当前版本已是最新")
                return False
        
        except Exception as e:
            logger.error(f"检查更新时出错: {str(e)}")
            
            # 添加更新历史
            self.config["update_history"].append({
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
            Tuple[bool, str]: (是否有更新, 新版本号)
        """
        # 获取本地版本
        local_version = self.config.get("current_version", "3.0.0")
        
        try:
            # 从服务器获取远程版本信息
            response = requests.get(self.config["update_url"], timeout=10)
            
            # 如果请求成功
            if response.status_code == 200:
                try:
                    data = response.json()
                    remote_version = data.get("version", "3.0.0")
                except ValueError:
                    # 如果返回数据不是有效的JSON
                    logger.warning("远程服务器返回的数据不是有效的JSON")
                    return False, local_version
            else:
                logger.warning(f"远程服务器返回错误状态码: {response.status_code}")
                return False, local_version
            
            # 比较版本
            local_parts = [int(x) for x in local_version.split(".")]
            remote_parts = [int(x) for x in remote_version.split(".")]
            
            # 补齐版本号长度
            while len(local_parts) < 3:
                local_parts.append(0)
            while len(remote_parts) < 3:
                remote_parts.append(0)
            
            # 比较版本
            for i in range(3):
                if remote_parts[i] > local_parts[i]:
                    return True, remote_version
                elif remote_parts[i] < local_parts[i]:
                    return False, local_version
            
            # 版本相同
            return False, local_version
            
        except requests.exceptions.RequestException as e:
            logger.error(f"连接远程服务器时出错: {str(e)}")
            return False, local_version
        except Exception as e:
            logger.error(f"检查远程更新时出错: {str(e)}")
            return False, local_version
    
    def download_new_schema(self, version: str) -> bool:
        """
        下载新版本的架构文件
        
        Args:
            version: 版本号
            
        Returns:
            bool: 是否成功下载
        """
        logger.info(f"开始下载版本 {version} 的架构文件")
        
        try:
            # 下载剪映架构文件
            jianying_schema_url = f"https://jianying.com/schema/v{version}/jianying.xsd"
            jianying_schema_path = os.path.join(self.schema_dir, f"jianying_v{version}.xsd")
            
            # 下载架构文件
            self._download_file(jianying_schema_url, jianying_schema_path)
            
            # 下载Premiere架构文件
            premiere_schema_url = f"https://jianying.com/schema/v{version}/premiere.xsd"
            premiere_schema_path = os.path.join(self.schema_dir, f"premiere_v{version}.xsd")
            
            # 下载架构文件
            self._download_file(premiere_schema_url, premiere_schema_path)
            
            # 下载FCPXML架构文件
            fcpxml_schema_url = f"https://jianying.com/schema/v{version}/fcpxml.xsd"
            fcpxml_schema_path = os.path.join(self.schema_dir, f"fcpxml_v{version}.xsd")
            
            # 下载架构文件
            self._download_file(fcpxml_schema_url, fcpxml_schema_path)
            
            # 更新版本规格文件
            self._update_version_specs(version)
            
            return True
        except Exception as e:
            logger.error(f"下载架构文件时出错: {str(e)}")
            return False
    
    def _download_file(self, url: str, path: str) -> None:
        """
        下载文件
        
        Args:
            url: 文件URL
            path: 保存路径
        """
        try:
            # 创建目录
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 下载文件
            response = requests.get(url, timeout=30)
            
            # 如果请求成功
            if response.status_code == 200:
                # 保存文件
                with open(path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"文件已下载到 {path}")
            else:
                logger.warning(f"下载文件 {url} 失败，状态码: {response.status_code}")
                raise Exception(f"下载文件失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"下载文件 {url} 时出错: {str(e)}")
            raise
    
    def _update_version_specs(self, version: str) -> None:
        """
        更新版本规格文件
        
        Args:
            version: 新版本号
        """
        try:
            # 加载当前版本规格
            if os.path.exists(self.version_spec_path):
                with open(self.version_spec_path, 'r', encoding='utf-8') as f:
                    specs = json.load(f)
            else:
                specs = {}
            
            # 如果新版本已存在，则不需要更新
            if version in specs:
                logger.info(f"版本 {version} 的规格已存在，无需更新")
                return
            
            # 创建新版本规格
            new_spec = {
                "required_nodes": [
                    "info/metadata",
                    "info/metadata/title",
                    "info/metadata/creator",
                    "info/project_settings",
                    "info/project_settings/resolution",
                    "info/project_settings/frame_rate",
                    "resources",
                    "timeline"
                ],
                "default_values": {
                    "info/metadata/title": "未命名项目",
                    "info/metadata/creator": "VisionAI-ClipsMaster",
                    "info/project_settings/resolution": {
                        "width": "3840",
                        "height": "2160"
                    },
                    "info/project_settings/frame_rate": "30"
                },
                "required_attributes": {
                    "timeline": {
                        "id": "main_timeline",
                        "duration": "00:00:00.000"
                    },
                    "info/project_settings/resolution": {
                        "width": "3840",
                        "height": "2160"
                    }
                },
                "supported_features": [
                    "4k_resolution",
                    "hdr",
                    "nested_sequences",
                    "effects_layers",
                    "keyframes",
                    "3d_effects",
                    "color_grading",
                    "audio_effects",
                    "multi_track"
                ]
            }
            
            # 添加新版本规格
            specs[version] = new_spec
            
            # 保存更新后的规格
            with open(self.version_spec_path, 'w', encoding='utf-8') as f:
                json.dump(specs, f, ensure_ascii=False, indent=2)
            
            logger.info(f"版本 {version} 的规格已添加到 {self.version_spec_path}")
        except Exception as e:
            logger.error(f"更新版本规格文件时出错: {str(e)}")
            raise
    
    def check_updates_sync(self) -> Tuple[bool, Optional[str]]:
        """
        同步检查更新，主要用于UI调用
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有更新, 新版本号)
        """
        try:
            has_update, new_version = self._check_remote_update()
            return has_update, new_version
        except Exception as e:
            logger.error(f"同步检查更新时出错: {str(e)}")
            return False, None
    
    def set_auto_update(self, enabled: bool) -> None:
        """
        设置自动更新
        
        Args:
            enabled: 是否启用自动更新
        """
        if self.config["auto_update"] == enabled:
            return
            
        self.config["auto_update"] = enabled
        self._save_config()
        
        if enabled:
            self.start_auto_updater()
        else:
            self.stop_auto_updater()
        
        logger.info(f"自动更新已{'启用' if enabled else '禁用'}")
    
    def set_check_interval(self, hours: int) -> None:
        """
        设置检查间隔
        
        Args:
            hours: 小时数
        """
        if hours < 1:
            logger.warning(f"检查间隔不能小于1小时，设置为1小时")
            hours = 1
            
        self.config["check_interval"] = hours
        self._save_config()
        
        logger.info(f"检查间隔已设置为 {hours} 小时")
    
    def get_update_history(self) -> List[Dict[str, Any]]:
        """
        获取更新历史
        
        Returns:
            List[Dict[str, Any]]: 更新历史
        """
        return self.config.get("update_history", [])
    
    def clear_update_history(self) -> None:
        """清除更新历史"""
        self.config["update_history"] = []
        self._save_config()
        
        logger.info("更新历史已清除")
    
    def get_current_version(self) -> str:
        """
        获取当前版本
        
        Returns:
            str: 当前版本
        """
        return self.config.get("current_version", "3.0.0")
    
    def __del__(self):
        """析构函数，停止更新线程"""
        self.stop_auto_updater()


# 简单示例代码
if __name__ == "__main__":
    # 创建版本监听器
    watcher = VersionWatcher()
    
    # 打印当前版本
    print(f"当前版本: {watcher.get_current_version()}")
    
    # 检查更新
    print("检查更新...")
    has_update, new_version = watcher.check_updates_sync()
    
    if has_update:
        print(f"发现新版本: {new_version}")
        
        # 询问用户是否下载更新
        response = input("是否下载更新? (y/n) ")
        
        if response.lower() == 'y':
            print("下载更新...")
            success = watcher.download_new_schema(new_version)
            
            if success:
                print(f"更新成功，当前版本: {watcher.get_current_version()}")
            else:
                print("更新失败")
    else:
        print("当前已是最新版本")
    
    # 打印更新历史
    print("\n更新历史:")
    for item in watcher.get_update_history():
        date = item.get("date", "未知")
        version = item.get("version", "未知")
        success = item.get("success", False)
        error = item.get("error", "")
        
        status = "成功" if success else f"失败: {error}"
        print(f"{date} - 版本 {version} - {status}") 