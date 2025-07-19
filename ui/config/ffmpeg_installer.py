#!/usr/bin/env python3
"""
FFmpeg自动安装和配置模块
支持Windows系统的FFmpeg自动下载、安装和配置
"""

import os
import sys
import subprocess
import zipfile
import shutil
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
import tempfile
import time

class FFmpegInstaller:
    """FFmpeg安装器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.ffmpeg_dir = self.project_root / "tools" / "ffmpeg"
        self.ffmpeg_exe = self.ffmpeg_dir / "bin" / "ffmpeg.exe"
        
        # 直接下载链接（使用稳定版本）
        self.download_sources = [
            {
                "name": "GitHub官方（最新版本）",
                "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
                "test_url": "https://github.com/"
            },
            {
                "name": "GitHub官方（备用链接）",
                "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2024-07-14-12-55/ffmpeg-master-latest-win64-gpl.zip",
                "test_url": "https://github.com/"
            },
            {
                "name": "FFmpeg官方网站",
                "url": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
                "test_url": "https://www.gyan.dev/"
            }
        ]

        # FFmpeg版本信息
        self.ffmpeg_build = "ffmpeg-master-latest-win64-gpl.zip"
        
    def check_ffmpeg_installed(self) -> Dict[str, any]:
        """检查FFmpeg是否已安装"""
        result = {
            "installed": False,
            "version": None,
            "path": None,
            "in_path": False,
            "local_install": False
        }
        
        # 1. 检查系统PATH中的FFmpeg
        try:
            output = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if output.returncode == 0:
                result["installed"] = True
                result["in_path"] = True
                result["version"] = self._extract_version(output.stdout)
                result["path"] = "系统PATH"
                print(f"✅ 检测到系统FFmpeg: {result['version']}")
                return result
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 2. 检查本地安装的FFmpeg
        if self.ffmpeg_exe.exists():
            try:
                output = subprocess.run(
                    [str(self.ffmpeg_exe), "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if output.returncode == 0:
                    result["installed"] = True
                    result["local_install"] = True
                    result["version"] = self._extract_version(output.stdout)
                    result["path"] = str(self.ffmpeg_exe)
                    print(f"✅ 检测到本地FFmpeg: {result['version']}")
                    return result
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        print("❌ 未检测到FFmpeg安装")
        return result
    
    def _extract_version(self, version_output: str) -> str:
        """从版本输出中提取版本号"""
        try:
            lines = version_output.split('\n')
            for line in lines:
                if line.startswith('ffmpeg version'):
                    return line.split()[2]
            return "unknown"
        except:
            return "unknown"
    
    def select_best_source(self) -> int:
        """选择最快的下载源"""
        print("🔍 测试下载源速度...")

        best_source = 0  # 默认使用第一个源
        best_time = float('inf')

        for i, source in enumerate(self.download_sources):
            try:
                print(f"  测试 {source['name']}...")
                start_time = time.time()

                response = requests.head(
                    source['test_url'],
                    timeout=5,
                    allow_redirects=True
                )

                if response.status_code < 400:
                    elapsed = time.time() - start_time
                    print(f"    响应时间: {elapsed:.2f}s")

                    if elapsed < best_time:
                        best_time = elapsed
                        best_source = i
                else:
                    print(f"    状态码: {response.status_code}")

            except Exception as e:
                print(f"    连接失败: {e}")
                continue

        selected_source = self.download_sources[best_source]
        print(f"✅ 选择下载源: {selected_source['name']} (响应时间: {best_time:.2f}s)")
        return best_source
    
    def download_ffmpeg(self, source_index: int = None) -> bool:
        """下载FFmpeg"""
        if source_index is None:
            source_index = self.select_best_source()

        source = self.download_sources[source_index]
        download_url = source['url']
        
        print(f"📦 开始下载FFmpeg...")
        print(f"🔗 下载地址: {download_url}")
        print(f"📁 安装目录: {self.ffmpeg_dir}")
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / self.ffmpeg_build
                
                # 下载文件
                print("⬇️ 正在下载...")
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\r  进度: {progress:.1f}% ({downloaded // 1024 // 1024}MB/{total_size // 1024 // 1024}MB)", end="")
                
                print("\n✅ 下载完成")
                
                # 解压文件
                print("📂 正在解压...")
                self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 提取到临时目录
                    extract_dir = Path(temp_dir) / "extracted"
                    zip_ref.extractall(extract_dir)
                    
                    # 找到FFmpeg目录（通常是解压后的第一个目录）
                    extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                    if extracted_dirs:
                        ffmpeg_source = extracted_dirs[0]
                        
                        # 复制文件到目标目录
                        if (ffmpeg_source / "bin").exists():
                            shutil.copytree(ffmpeg_source / "bin", self.ffmpeg_dir / "bin", dirs_exist_ok=True)
                        if (ffmpeg_source / "doc").exists():
                            shutil.copytree(ffmpeg_source / "doc", self.ffmpeg_dir / "doc", dirs_exist_ok=True)
                        if (ffmpeg_source / "presets").exists():
                            shutil.copytree(ffmpeg_source / "presets", self.ffmpeg_dir / "presets", dirs_exist_ok=True)
                
                print("✅ 解压完成")
                return True
                
        except requests.RequestException as e:
            print(f"❌ 下载失败: {e}")
            return False
        except zipfile.BadZipFile as e:
            print(f"❌ 解压失败: {e}")
            return False
        except Exception as e:
            print(f"❌ 安装失败: {e}")
            return False
    
    def configure_environment(self) -> bool:
        """配置环境变量"""
        try:
            if not self.ffmpeg_exe.exists():
                print("❌ FFmpeg可执行文件不存在")
                return False
            
            # 添加到PATH环境变量（仅当前进程）
            ffmpeg_bin_dir = str(self.ffmpeg_dir / "bin")
            current_path = os.environ.get('PATH', '')
            
            if ffmpeg_bin_dir not in current_path:
                os.environ['PATH'] = ffmpeg_bin_dir + os.pathsep + current_path
                print(f"✅ 已添加FFmpeg到PATH: {ffmpeg_bin_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ 配置环境变量失败: {e}")
            return False
    
    def verify_installation(self) -> bool:
        """验证FFmpeg安装"""
        try:
            # 测试FFmpeg命令
            result = subprocess.run(
                [str(self.ffmpeg_exe), "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = self._extract_version(result.stdout)
                print(f"✅ FFmpeg安装验证成功: {version}")
                
                # 测试基本功能
                test_result = subprocess.run(
                    [str(self.ffmpeg_exe), "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-f", "null", "-"],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if test_result.returncode == 0:
                    print("✅ FFmpeg功能测试通过")
                    return True
                else:
                    print("⚠️ FFmpeg功能测试失败，但基本安装正常")
                    return True
            else:
                print(f"❌ FFmpeg验证失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ FFmpeg验证异常: {e}")
            return False

    def install_ffmpeg(self, force_reinstall: bool = False) -> bool:
        """完整的FFmpeg安装流程"""
        print("=" * 60)
        print("🎬 FFmpeg自动安装程序")
        print("=" * 60)

        # 1. 检查现有安装
        if not force_reinstall:
            status = self.check_ffmpeg_installed()
            if status["installed"]:
                print("✅ FFmpeg已安装，跳过安装步骤")
                if status["local_install"]:
                    self.configure_environment()
                return True

        # 2. 下载和安装
        print("📦 开始安装FFmpeg...")

        # 尝试多个下载源
        for i, source in enumerate(self.download_sources):
            print(f"\n🔄 尝试使用 {source['name']}")

            if self.download_ffmpeg(i):
                break
        else:
            print("❌ 所有下载源都失败")
            self._show_manual_install_guide()
            return False

        # 3. 配置环境
        if not self.configure_environment():
            print("⚠️ 环境配置失败，但FFmpeg已安装")

        # 4. 验证安装
        if self.verify_installation():
            print("\n🎉 FFmpeg安装成功！")
            return True
        else:
            print("\n❌ FFmpeg安装验证失败")
            self._show_manual_install_guide()
            return False

    def _show_manual_install_guide(self):
        """显示手动安装指南"""
        print("\n" + "=" * 60)
        print("📖 FFmpeg手动安装指南")
        print("=" * 60)
        print("如果自动安装失败，请按以下步骤手动安装：")
        print()
        print("方法1 - 使用国内镜像下载：")
        print("1. 访问清华大学镜像站：")
        print("   https://mirrors.tuna.tsinghua.edu.cn/github-release/BtbN/FFmpeg-Builds/")
        print("2. 下载最新的 ffmpeg-master-latest-win64-gpl.zip")
        print("3. 解压到项目目录：")
        print(f"   {self.ffmpeg_dir}")
        print()
        print("方法2 - 使用官方网站：")
        print("1. 访问 https://ffmpeg.org/download.html")
        print("2. 选择 Windows 版本下载")
        print("3. 解压并配置环境变量")
        print()
        print("方法3 - 使用包管理器：")
        print("1. 安装 Chocolatey: https://chocolatey.org/")
        print("2. 运行命令: choco install ffmpeg")
        print()
        print("配置完成后，重新运行程序即可。")
        print("=" * 60)

    def get_ffmpeg_path(self) -> Optional[str]:
        """获取FFmpeg可执行文件路径"""
        status = self.check_ffmpeg_installed()
        if status["installed"]:
            if status["local_install"]:
                return str(self.ffmpeg_exe)
            elif status["in_path"]:
                return "ffmpeg"  # 系统PATH中
        return None

def install_ffmpeg_if_needed() -> bool:
    """如果需要则安装FFmpeg"""
    installer = FFmpegInstaller()
    return installer.install_ffmpeg()

def check_ffmpeg_available() -> bool:
    """检查FFmpeg是否可用"""
    installer = FFmpegInstaller()
    status = installer.check_ffmpeg_installed()
    return status["installed"]

def get_ffmpeg_executable() -> Optional[str]:
    """获取FFmpeg可执行文件路径"""
    installer = FFmpegInstaller()
    return installer.get_ffmpeg_path()

if __name__ == "__main__":
    # 命令行安装模式
    installer = FFmpegInstaller()

    import argparse
    parser = argparse.ArgumentParser(description="FFmpeg自动安装工具")
    parser.add_argument("--force", action="store_true", help="强制重新安装")
    parser.add_argument("--check", action="store_true", help="仅检查安装状态")

    args = parser.parse_args()

    if args.check:
        status = installer.check_ffmpeg_installed()
        if status["installed"]:
            print(f"✅ FFmpeg已安装: {status['version']} ({status['path']})")
        else:
            print("❌ FFmpeg未安装")
    else:
        success = installer.install_ffmpeg(force_reinstall=args.force)
        sys.exit(0 if success else 1)
