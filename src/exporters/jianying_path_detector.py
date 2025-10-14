"""
剪映路径检测器

自动检测剪映专业版的安装路径和草稿目录
支持配置缓存，提高检测速度
"""

import os
import json
import winreg
import logging
from pathlib import Path
from typing import Optional, Dict, List
import subprocess

logger = logging.getLogger(__name__)


class JianyingPathDetector:
    """剪映路径检测器"""
    
    # 配置文件路径
    CONFIG_FILE = Path("config/jianying_paths.json")
    
    # 常见的剪映安装路径
    COMMON_INSTALL_PATHS = [
        r"C:\Program Files\JianyingPro\JianyingPro.exe",
        r"C:\Program Files (x86)\JianyingPro\JianyingPro.exe",
        r"C:\Program Files\ByteDance\JianyingPro\JianyingPro.exe",
        r"C:\Program Files (x86)\ByteDance\JianyingPro\JianyingPro.exe",
    ]
    
    # 常见的草稿目录路径
    COMMON_DRAFT_PATHS = [
        r"C:\Users\{username}\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft",
        r"C:\Users\{username}\Documents\JianyingPro Drafts",
    ]
    
    def __init__(self):
        """初始化检测器"""
        self.config: Dict[str, str] = {}
        self._load_config()
    
    def _load_config(self):
        """加载缓存的配置"""
        try:
            if self.CONFIG_FILE.exists():
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"已加载剪映路径配置: {self.config}")
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
            self.config = {}
    
    def _save_config(self):
        """保存配置到缓存"""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存剪映路径配置: {self.config}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def detect_draft_directory(self, force_detect: bool = False) -> Optional[str]:
        """
        检测剪映草稿目录
        
        Args:
            force_detect: 是否强制重新检测（忽略缓存）
            
        Returns:
            草稿目录路径，如果检测失败返回None
        """
        # 如果有缓存且不强制检测，直接返回
        if not force_detect and 'draft_directory' in self.config:
            draft_dir = self.config['draft_directory']
            if os.path.exists(draft_dir):
                logger.info(f"使用缓存的草稿目录: {draft_dir}")
                return draft_dir
            else:
                logger.warning(f"缓存的草稿目录不存在: {draft_dir}")
        
        logger.info("开始检测剪映草稿目录...")
        
        # 方法1: 检测注册表
        draft_dir = self._detect_draft_from_registry()
        if draft_dir:
            logger.info(f"从注册表检测到草稿目录: {draft_dir}")
            self.config['draft_directory'] = draft_dir
            self._save_config()
            return draft_dir
        
        # 方法2: 检测配置文件
        draft_dir = self._detect_draft_from_config_file()
        if draft_dir:
            logger.info(f"从配置文件检测到草稿目录: {draft_dir}")
            self.config['draft_directory'] = draft_dir
            self._save_config()
            return draft_dir
        
        # 方法3: 检测常见路径
        draft_dir = self._detect_draft_from_common_paths()
        if draft_dir:
            logger.info(f"从常见路径检测到草稿目录: {draft_dir}")
            self.config['draft_directory'] = draft_dir
            self._save_config()
            return draft_dir
        
        logger.warning("无法自动检测剪映草稿目录")
        return None
    
    def _detect_draft_from_registry(self) -> Optional[str]:
        """从注册表检测草稿目录"""
        try:
            # 尝试读取剪映的注册表配置
            registry_paths = [
                r"Software\JianyingPro",
                r"Software\ByteDance\JianyingPro",
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
                    try:
                        draft_path, _ = winreg.QueryValueEx(key, "DraftPath")
                        if draft_path and os.path.exists(draft_path):
                            return draft_path
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(key)
                except FileNotFoundError:
                    continue
        except Exception as e:
            logger.debug(f"从注册表检测草稿目录失败: {e}")
        
        return None
    
    def _detect_draft_from_config_file(self) -> Optional[str]:
        """从配置文件检测草稿目录"""
        try:
            # 剪映配置文件路径
            config_paths = [
                Path(os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\User Data\Preferences")),
                Path(os.path.expandvars(r"%APPDATA%\JianyingPro\Preferences")),
            ]
            
            for config_path in config_paths:
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            # 尝试从配置中提取草稿路径
                            draft_path = config_data.get('draft_path') or config_data.get('project_path')
                            if draft_path and os.path.exists(draft_path):
                                return draft_path
                    except Exception as e:
                        logger.debug(f"解析配置文件失败 {config_path}: {e}")
        except Exception as e:
            logger.debug(f"从配置文件检测草稿目录失败: {e}")
        
        return None
    
    def _detect_draft_from_common_paths(self) -> Optional[str]:
        """从常见路径检测草稿目录"""
        try:
            username = os.getenv('USERNAME')
            for path_template in self.COMMON_DRAFT_PATHS:
                path = path_template.format(username=username)
                if os.path.exists(path):
                    return path
        except Exception as e:
            logger.debug(f"从常见路径检测草稿目录失败: {e}")
        
        return None
    
    def detect_install_path(self, force_detect: bool = False) -> Optional[str]:
        """
        检测剪映安装路径
        
        Args:
            force_detect: 是否强制重新检测（忽略缓存）
            
        Returns:
            剪映可执行文件路径，如果检测失败返回None
        """
        # 如果有缓存且不强制检测，直接返回
        if not force_detect and 'install_path' in self.config:
            install_path = self.config['install_path']
            if os.path.exists(install_path):
                logger.info(f"使用缓存的安装路径: {install_path}")
                return install_path
            else:
                logger.warning(f"缓存的安装路径不存在: {install_path}")
        
        logger.info("开始检测剪映安装路径...")
        
        # 方法1: 检测注册表
        install_path = self._detect_install_from_registry()
        if install_path:
            logger.info(f"从注册表检测到安装路径: {install_path}")
            self.config['install_path'] = install_path
            self._save_config()
            return install_path
        
        # 方法2: 检测常见路径
        install_path = self._detect_install_from_common_paths()
        if install_path:
            logger.info(f"从常见路径检测到安装路径: {install_path}")
            self.config['install_path'] = install_path
            self._save_config()
            return install_path
        
        # 方法3: 检测快捷方式
        install_path = self._detect_install_from_shortcuts()
        if install_path:
            logger.info(f"从快捷方式检测到安装路径: {install_path}")
            self.config['install_path'] = install_path
            self._save_config()
            return install_path
        
        logger.warning("无法自动检测剪映安装路径")
        return None
    
    def _detect_install_from_registry(self) -> Optional[str]:
        """从注册表检测安装路径"""
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\JianyingPro"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\ByteDance\JianyingPro"),
                (winreg.HKEY_CURRENT_USER, r"Software\JianyingPro"),
                (winreg.HKEY_CURRENT_USER, r"Software\ByteDance\JianyingPro"),
            ]
            
            for hkey, reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(hkey, reg_path)
                    try:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        exe_path = os.path.join(install_path, "JianyingPro.exe")
                        if os.path.exists(exe_path):
                            return exe_path
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(key)
                except FileNotFoundError:
                    continue
        except Exception as e:
            logger.debug(f"从注册表检测安装路径失败: {e}")
        
        return None
    
    def _detect_install_from_common_paths(self) -> Optional[str]:
        """从常见路径检测安装路径"""
        for path in self.COMMON_INSTALL_PATHS:
            if os.path.exists(path):
                return path
        
        # 尝试在用户目录下查找
        user_local = Path(os.path.expandvars(r"%LOCALAPPDATA%"))
        possible_paths = [
            user_local / "JianyingPro" / "JianyingPro.exe",
            user_local / "Programs" / "JianyingPro" / "JianyingPro.exe",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _detect_install_from_shortcuts(self) -> Optional[str]:
        """从快捷方式检测安装路径"""
        try:
            # 检测桌面快捷方式
            desktop = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
            start_menu = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"))
            
            shortcut_locations = [desktop, start_menu]
            
            for location in shortcut_locations:
                if not location.exists():
                    continue
                
                # 查找剪映快捷方式
                for shortcut in location.rglob("*剪映*.lnk"):
                    try:
                        # 使用PowerShell读取快捷方式目标
                        cmd = f'powershell -command "(New-Object -COM WScript.Shell).CreateShortcut(\'{shortcut}\').TargetPath"'
                        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                        target_path = result.stdout.strip()
                        
                        if target_path and os.path.exists(target_path) and target_path.endswith('.exe'):
                            return target_path
                    except Exception as e:
                        logger.debug(f"读取快捷方式失败 {shortcut}: {e}")
        except Exception as e:
            logger.debug(f"从快捷方式检测安装路径失败: {e}")
        
        return None
    
    def set_draft_directory(self, path: str):
        """
        手动设置草稿目录
        
        Args:
            path: 草稿目录路径
        """
        if not os.path.exists(path):
            raise ValueError(f"草稿目录不存在: {path}")
        
        self.config['draft_directory'] = path
        self._save_config()
        logger.info(f"已手动设置草稿目录: {path}")
    
    def set_install_path(self, path: str):
        """
        手动设置安装路径
        
        Args:
            path: 剪映可执行文件路径
        """
        if not os.path.exists(path):
            raise ValueError(f"安装路径不存在: {path}")
        
        if not path.endswith('.exe'):
            raise ValueError(f"安装路径必须是可执行文件: {path}")
        
        self.config['install_path'] = path
        self._save_config()
        logger.info(f"已手动设置安装路径: {path}")


# 全局单例
_detector_instance: Optional[JianyingPathDetector] = None


def get_detector() -> JianyingPathDetector:
    """获取全局检测器实例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = JianyingPathDetector()
    return _detector_instance

