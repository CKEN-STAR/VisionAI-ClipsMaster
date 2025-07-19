#!/usr/bin/env python3
"""
FFmpeg自动安装和配置工具
支持Windows系统，使用国内高速镜像源
"""

import os
import sys
import subprocess
import platform
import zipfile
import requests
from pathlib import Path
import tempfile
import shutil
from typing import Optional, Tuple, Dict

class FFmpegInstaller:
    """FFmpeg安装器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.project_root = Path(__file__).parent
        self.ffmpeg_dir = self.project_root / "ffmpeg"
        
        # 国内镜像源配置
        self.mirrors = {
            "tsinghua": "https://mirrors.tuna.tsinghua.edu.cn/",
            "ustc": "https://mirrors.ustc.edu.cn/",
            "aliyun": "https://mirrors.aliyun.com/",
            "github_proxy": "https://ghproxy.com/"
        }
        
        # FFmpeg下载链接（Windows）
        self.ffmpeg_urls = {
            "windows": {
                "official": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                "github": "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip",
                "backup": "https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-latest-win64-static.zip"
            }
        }
    
    def check_ffmpeg_installed(self) -> Tuple[bool, Optional[str]]:
        """
        检查FFmpeg是否已安装
        
        Returns:
            (是否安装, FFmpeg路径)
        """
        try:
            # 检查系统PATH中的FFmpeg
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                # 获取FFmpeg路径
                which_result = subprocess.run(
                    ["where", "ffmpeg"] if self.system == "windows" else ["which", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                ffmpeg_path = which_result.stdout.strip().split('\n')[0] if which_result.returncode == 0 else "系统PATH"
                print(f"✅ FFmpeg已安装: {ffmpeg_path}")
                return True, ffmpeg_path
            else:
                print("❌ FFmpeg未在系统PATH中找到")
                return False, None
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            print("❌ FFmpeg未安装或不可访问")
            return False, None
    
    def download_with_mirrors(self, url: str, filename: str, use_proxy: bool = True) -> Optional[Path]:
        """
        使用镜像源下载文件
        
        Args:
            url: 原始下载链接
            filename: 保存的文件名
            use_proxy: 是否使用代理镜像
            
        Returns:
            下载文件的路径
        """
        download_urls = []
        
        # 如果使用代理，添加GitHub代理
        if use_proxy and "github.com" in url:
            proxy_url = url.replace("https://github.com", self.mirrors["github_proxy"] + "https://github.com")
            download_urls.append(("GitHub代理", proxy_url))
        
        # 添加原始链接
        download_urls.append(("官方源", url))
        
        temp_dir = Path(tempfile.gettempdir())
        
        for source_name, download_url in download_urls:
            try:
                print(f"🔗 尝试从{source_name}下载...")
                
                response = requests.get(
                    download_url, 
                    stream=True, 
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                
                if response.status_code == 200:
                    file_path = temp_dir / filename
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(file_path, 'wb') as f:
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    print(f"\r📥 下载进度: {progress:.1f}%", end="", flush=True)
                    
                    print(f"\n✅ 下载完成: {file_path}")
                    return file_path
                else:
                    print(f"❌ {source_name}下载失败: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {source_name}下载失败: {e}")
                continue
        
        return None
    
    def install_ffmpeg_windows(self) -> bool:
        """
        在Windows上安装FFmpeg
        
        Returns:
            是否安装成功
        """
        try:
            print("🔧 开始安装FFmpeg for Windows...")
            
            # 创建FFmpeg目录
            self.ffmpeg_dir.mkdir(exist_ok=True)
            
            # 尝试下载FFmpeg
            for source_name, url in self.ffmpeg_urls["windows"].items():
                print(f"\n📦 尝试从{source_name}下载FFmpeg...")
                
                zip_file = self.download_with_mirrors(url, "ffmpeg.zip")
                if zip_file and zip_file.exists():
                    break
            else:
                print("❌ 所有下载源都失败")
                return False
            
            # 解压FFmpeg
            print("📂 正在解压FFmpeg...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.ffmpeg_dir)
            
            # 查找ffmpeg.exe
            ffmpeg_exe = None
            for root, dirs, files in os.walk(self.ffmpeg_dir):
                if "ffmpeg.exe" in files:
                    ffmpeg_exe = Path(root) / "ffmpeg.exe"
                    break
            
            if not ffmpeg_exe:
                print("❌ 解压后未找到ffmpeg.exe")
                return False
            
            # 移动到标准位置
            target_dir = self.ffmpeg_dir / "bin"
            target_dir.mkdir(exist_ok=True)
            
            target_ffmpeg = target_dir / "ffmpeg.exe"
            if ffmpeg_exe != target_ffmpeg:
                shutil.copy2(ffmpeg_exe, target_ffmpeg)
            
            # 同时复制其他工具
            for tool in ["ffprobe.exe", "ffplay.exe"]:
                tool_path = ffmpeg_exe.parent / tool
                if tool_path.exists():
                    shutil.copy2(tool_path, target_dir / tool)
            
            # 清理临时文件
            zip_file.unlink()
            
            print(f"✅ FFmpeg安装完成: {target_ffmpeg}")
            return True
            
        except Exception as e:
            print(f"❌ FFmpeg安装失败: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """
        配置FFmpeg环境变量
        
        Returns:
            是否配置成功
        """
        try:
            ffmpeg_bin = self.ffmpeg_dir / "bin"
            
            if not ffmpeg_bin.exists():
                print("❌ FFmpeg bin目录不存在")
                return False
            
            # 添加到当前进程的环境变量
            current_path = os.environ.get('PATH', '')
            ffmpeg_path_str = str(ffmpeg_bin.absolute())
            
            if ffmpeg_path_str not in current_path:
                os.environ['PATH'] = ffmpeg_path_str + os.pathsep + current_path
                print(f"✅ 已添加FFmpeg到当前会话PATH: {ffmpeg_path_str}")
            
            # Windows系统级环境变量配置（需要管理员权限）
            if self.system == "windows":
                try:
                    # 尝试添加到用户环境变量
                    import winreg
                    
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
                        try:
                            current_user_path, _ = winreg.QueryValueEx(key, "PATH")
                        except FileNotFoundError:
                            current_user_path = ""
                        
                        if ffmpeg_path_str not in current_user_path:
                            new_path = ffmpeg_path_str + os.pathsep + current_user_path
                            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                            print("✅ 已添加FFmpeg到用户环境变量")
                            
                            # 通知系统环境变量已更改
                            subprocess.run([
                                "powershell", "-Command",
                                "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User'), 'User')"
                            ], check=False)
                            
                except Exception as e:
                    print(f"⚠️ 无法设置系统环境变量: {e}")
                    print("💡 请手动将以下路径添加到系统PATH:")
                    print(f"   {ffmpeg_path_str}")
            
            return True
            
        except Exception as e:
            print(f"❌ 环境变量配置失败: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """
        验证FFmpeg安装
        
        Returns:
            是否验证成功
        """
        try:
            print("🔍 验证FFmpeg安装...")
            
            # 测试FFmpeg命令
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg验证成功: {version_line}")
                
                # 测试基本功能
                test_result = subprocess.run(
                    ["ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1", "-f", "null", "-"],
                    capture_output=True,
                    timeout=15
                )
                
                if test_result.returncode == 0:
                    print("✅ FFmpeg功能测试通过")
                    return True
                else:
                    print("⚠️ FFmpeg功能测试失败，但基本安装正常")
                    return True
            else:
                print("❌ FFmpeg验证失败")
                return False
                
        except Exception as e:
            print(f"❌ FFmpeg验证异常: {e}")
            return False

    def install_ffmpeg(self) -> bool:
        """
        自动安装FFmpeg

        Returns:
            是否安装成功
        """
        print("=" * 60)
        print("🎬 FFmpeg自动安装工具")
        print("=" * 60)

        # 1. 检查是否已安装
        is_installed, ffmpeg_path = self.check_ffmpeg_installed()
        if is_installed:
            print("✅ FFmpeg已安装，无需重复安装")
            return True

        # 2. 根据系统类型安装
        if self.system == "windows":
            success = self.install_ffmpeg_windows()
        else:
            print(f"❌ 暂不支持自动安装到 {self.system} 系统")
            print("💡 请手动安装FFmpeg:")
            print("   - Ubuntu/Debian: sudo apt install ffmpeg")
            print("   - CentOS/RHEL: sudo yum install ffmpeg")
            print("   - macOS: brew install ffmpeg")
            return False

        if not success:
            return False

        # 3. 配置环境变量
        if not self.configure_environment():
            print("⚠️ 环境变量配置失败，但FFmpeg已安装")

        # 4. 验证安装
        return self.verify_installation()

    def get_manual_install_guide(self) -> Dict[str, str]:
        """
        获取手动安装指南

        Returns:
            安装指南字典
        """
        guides = {
            "windows": """
🪟 Windows手动安装指南:

1. 下载FFmpeg:
   - 官方网站: https://ffmpeg.org/download.html#build-windows
   - 推荐下载: https://www.gyan.dev/ffmpeg/builds/
   - 备用下载: https://github.com/BtbN/FFmpeg-Builds/releases

2. 解压到目录:
   - 解压到: C:\\ffmpeg\\
   - 确保存在: C:\\ffmpeg\\bin\\ffmpeg.exe

3. 添加环境变量:
   - 右键"此电脑" -> "属性" -> "高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 点击"新建"，添加: C:\\ffmpeg\\bin
   - 点击"确定"保存

4. 验证安装:
   - 打开命令提示符(cmd)
   - 输入: ffmpeg -version
   - 如果显示版本信息，则安装成功
""",
            "linux": """
🐧 Linux手动安装指南:

Ubuntu/Debian:
   sudo apt update
   sudo apt install ffmpeg

CentOS/RHEL:
   sudo yum install epel-release
   sudo yum install ffmpeg

Fedora:
   sudo dnf install ffmpeg

验证安装:
   ffmpeg -version
""",
            "macos": """
🍎 macOS手动安装指南:

使用Homebrew (推荐):
   brew install ffmpeg

使用MacPorts:
   sudo port install ffmpeg

验证安装:
   ffmpeg -version
"""
        }

        return guides.get(self.system, guides["windows"])

def main():
    """主函数"""
    installer = FFmpegInstaller()

    try:
        # 尝试自动安装
        success = installer.install_ffmpeg()

        if success:
            print("\n" + "=" * 60)
            print("🎉 FFmpeg安装完成!")
            print("=" * 60)
            print("✅ 现在可以使用视频处理功能了")
            print("🚀 请重新启动VisionAI-ClipsMaster以使用FFmpeg功能")
        else:
            print("\n" + "=" * 60)
            print("❌ 自动安装失败")
            print("=" * 60)
            print("📖 手动安装指南:")
            print(installer.get_manual_install_guide())

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n❌ 用户中断安装")
        return 1
    except Exception as e:
        print(f"\n❌ 安装过程中出现错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
