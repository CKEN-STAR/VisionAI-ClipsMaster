#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg工具模块
提供FFmpeg路径检测和配置功能
"""

import os
import subprocess
import json
import platform
from pathlib import Path
from typing import Optional, List

class FFmpegUtils:
    """FFmpeg工具类 - 智能检测和管理FFmpeg路径"""

    def __init__(self):
        self.ffmpeg_path: Optional[str] = None
        self.ffprobe_path: Optional[str] = None
        self.project_root = Path(__file__).parent.parent.parent
        self._detect_ffmpeg()

    def _get_possible_paths(self) -> List[str]:
        """获取可能的FFmpeg路径列表"""
        paths = []
        system = platform.system()

        # 1. 系统PATH中的FFmpeg
        if system == "Windows":
            paths.extend(["ffmpeg.exe", "ffmpeg"])
        else:
            paths.append("ffmpeg")

        # 2. 项目本地FFmpeg（相对路径）
        local_ffmpeg_dir = self.project_root / "tools" / "ffmpeg" / "bin"
        if system == "Windows":
            paths.append(str(local_ffmpeg_dir / "ffmpeg.exe"))
        else:
            paths.append(str(local_ffmpeg_dir / "ffmpeg"))

        # 3. 常见安装路径
        if system == "Windows":
            paths.extend([
                r"C:\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
                r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            ])
        elif system == "Darwin":  # macOS
            paths.extend([
                "/usr/local/bin/ffmpeg",
                "/opt/homebrew/bin/ffmpeg",
            ])
        elif system == "Linux":
            paths.extend([
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
            ])

        return paths

    def _detect_ffmpeg(self):
        """智能检测FFmpeg路径"""
        # 1. 尝试从配置文件加载
        if self._load_from_config():
            if self._verify_path(self.ffmpeg_path):
                return

        # 2. 自动检测
        for path in self._get_possible_paths():
            if self._verify_path(path):
                self.ffmpeg_path = path
                # 推断ffprobe路径
                if path.endswith("ffmpeg.exe"):
                    self.ffprobe_path = path.replace("ffmpeg.exe", "ffprobe.exe")
                elif path.endswith("ffmpeg"):
                    self.ffprobe_path = path.replace("ffmpeg", "ffprobe")

                # 保存到配置
                self._save_to_config()
                return

        # 3. 如果都失败，使用默认值（可能不可用）
        self.ffmpeg_path = "ffmpeg"
        self.ffprobe_path = "ffprobe"

    def _verify_path(self, path: Optional[str]) -> bool:
        """验证FFmpeg路径是否可用"""
        if not path:
            return False
        try:
            result = subprocess.run(
                [path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _load_from_config(self) -> bool:
        """从配置文件加载FFmpeg路径"""
        config_files = [
            self.project_root / "configs" / "ffmpeg_config.json",
            self.project_root / "src" / "utils" / "ffmpeg_config.json",
            self.project_root / "ffmpeg_config.json"
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                    ffmpeg_path = config.get("ffmpeg_path")
                    ffprobe_path = config.get("ffprobe_path")

                    # 如果是相对路径，转换为绝对路径
                    if ffmpeg_path and not os.path.isabs(ffmpeg_path):
                        ffmpeg_path = str(self.project_root / ffmpeg_path)
                    if ffprobe_path and not os.path.isabs(ffprobe_path):
                        ffprobe_path = str(self.project_root / ffprobe_path)

                    self.ffmpeg_path = ffmpeg_path
                    self.ffprobe_path = ffprobe_path
                    return True
                except Exception:
                    continue

        return False

    def _save_to_config(self):
        """保存FFmpeg配置到文件"""
        config_dir = self.project_root / "configs"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "ffmpeg_config.json"

        try:
            # 尝试使用相对路径
            ffmpeg_rel = self._get_relative_path(self.ffmpeg_path)
            ffprobe_rel = self._get_relative_path(self.ffprobe_path)

            config = {
                "ffmpeg_path": ffmpeg_rel or self.ffmpeg_path,
                "ffprobe_path": ffprobe_rel or self.ffprobe_path,
                "system": platform.system(),
                "auto_detected": True,
                "status": "configured"
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # 保存失败不影响使用
            pass

    def _get_relative_path(self, abs_path: Optional[str]) -> Optional[str]:
        """尝试将绝对路径转换为相对于项目根目录的相对路径"""
        if not abs_path:
            return None
        try:
            abs_path_obj = Path(abs_path).resolve()
            if abs_path_obj.is_relative_to(self.project_root):
                return str(abs_path_obj.relative_to(self.project_root))
        except Exception:
            pass
        return None

    def is_available(self) -> bool:
        """检查FFmpeg是否可用"""
        return self._verify_path(self.ffmpeg_path)

    def get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径"""
        return self.ffmpeg_path or "ffmpeg"

    def get_ffprobe_path(self) -> str:
        """获取FFprobe路径"""
        return self.ffprobe_path or "ffprobe"

    def get_version(self) -> Optional[str]:
        """获取FFmpeg版本信息"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 提取第一行版本信息
                return result.stdout.split('\n')[0]
        except Exception:
            pass
        return None

# 全局实例
ffmpeg_utils = FFmpegUtils()
