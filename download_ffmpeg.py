#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载并配置FFmpeg的完整脚本
"""

import os
import sys
import requests
import zipfile
import json
from pathlib import Path
from urllib.parse import urlparse
import shutil

class FFmpegDownloader:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.ffmpeg_dir = self.project_root / "tools" / "ffmpeg"
        self.bin_dir = self.ffmpeg_dir / "bin"
        
        # FFmpeg下载URL (Windows 64位版本)
        self.ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        self.backup_urls = [
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
            "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
        ]
    
    def download_with_progress(self, url: str, filename: str) -> bool:
        """带进度显示的下载"""
        try:
            print(f"📥 开始下载: {url}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r   进度: {progress:.1f}% ({downloaded}/{total_size} bytes)", end='')
            
            print(f"\n✅ 下载完成: {filename}")
            return True
            
        except Exception as e:
            print(f"\n❌ 下载失败: {e}")
            return False
    
    def extract_ffmpeg(self, zip_file: str) -> bool:
        """解压FFmpeg"""
        try:
            print(f"📦 解压FFmpeg...")
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # 获取压缩包内容
                file_list = zip_ref.namelist()
                
                # 找到ffmpeg.exe和ffprobe.exe
                ffmpeg_files = [f for f in file_list if f.endswith('ffmpeg.exe')]
                ffprobe_files = [f for f in file_list if f.endswith('ffprobe.exe')]
                
                if not ffmpeg_files:
                    print("❌ 压缩包中未找到ffmpeg.exe")
                    return False
                
                # 确保目标目录存在
                self.bin_dir.mkdir(parents=True, exist_ok=True)
                
                # 解压ffmpeg.exe
                for ffmpeg_file in ffmpeg_files:
                    with zip_ref.open(ffmpeg_file) as source:
                        with open(self.bin_dir / "ffmpeg.exe", 'wb') as target:
                            shutil.copyfileobj(source, target)
                    print(f"✅ 解压: ffmpeg.exe")
                    break
                
                # 解压ffprobe.exe
                for ffprobe_file in ffprobe_files:
                    with zip_ref.open(ffprobe_file) as source:
                        with open(self.bin_dir / "ffprobe.exe", 'wb') as target:
                            shutil.copyfileobj(source, target)
                    print(f"✅ 解压: ffprobe.exe")
                    break
                
                # 解压其他重要文件
                important_files = [f for f in file_list if any(f.endswith(ext) for ext in ['.dll', '.txt'])]
                for imp_file in important_files[:10]:  # 限制数量
                    try:
                        filename = Path(imp_file).name
                        with zip_ref.open(imp_file) as source:
                            with open(self.bin_dir / filename, 'wb') as target:
                                shutil.copyfileobj(source, target)
                    except:
                        continue
                
                return True
                
        except Exception as e:
            print(f"❌ 解压失败: {e}")
            return False
    
    def test_ffmpeg_installation(self) -> bool:
        """测试FFmpeg安装"""
        ffmpeg_exe = self.bin_dir / "ffmpeg.exe"
        
        if not ffmpeg_exe.exists():
            print("❌ ffmpeg.exe不存在")
            return False
        
        try:
            import subprocess
            result = subprocess.run([str(ffmpeg_exe), '-version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✅ FFmpeg测试成功: {version_line}")
                return True
            else:
                print(f"❌ FFmpeg测试失败，返回码: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ FFmpeg测试异常: {e}")
            return False
    
    def configure_ffmpeg(self) -> bool:
        """配置FFmpeg到项目"""
        ffmpeg_exe = self.bin_dir / "ffmpeg.exe"
        ffprobe_exe = self.bin_dir / "ffprobe.exe"
        
        config = {
            "ffmpeg_path": str(ffmpeg_exe),
            "ffprobe_path": str(ffprobe_exe),
            "version_info": "FFmpeg essentials build",
            "system": "windows",
            "configured_at": str(self.project_root),
            "status": "configured",
            "type": "project_local",
            "skip_ffmpeg_check": False,
            "auto_configured": True,
            "installation_date": str(Path(__file__).stat().st_mtime)
        }
        
        # 保存配置
        config_file = self.project_root / "configs" / "ffmpeg_config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ FFmpeg配置已保存: {config_file}")
        return True
    
    def download_and_install(self) -> bool:
        """下载并安装FFmpeg"""
        print("=" * 60)
        print("📥 下载并安装FFmpeg")
        print("=" * 60)
        
        # 尝试下载
        download_success = False
        temp_file = self.project_root / "ffmpeg_temp.zip"
        
        urls_to_try = [self.ffmpeg_url] + self.backup_urls
        
        for i, url in enumerate(urls_to_try):
            print(f"\n🔄 尝试下载源 {i+1}/{len(urls_to_try)}")
            
            if self.download_with_progress(url, str(temp_file)):
                download_success = True
                break
            else:
                print(f"   ❌ 下载源 {i+1} 失败")
        
        if not download_success:
            print("❌ 所有下载源都失败了")
            return False
        
        # 解压
        if not self.extract_ffmpeg(str(temp_file)):
            return False
        
        # 清理临时文件
        try:
            temp_file.unlink()
            print("🗑️ 清理临时文件")
        except:
            pass
        
        # 测试安装
        if not self.test_ffmpeg_installation():
            return False
        
        # 配置
        if not self.configure_ffmpeg():
            return False
        
        print("\n🎉 FFmpeg安装和配置完成！")
        return True

def main():
    """主函数"""
    downloader = FFmpegDownloader()
    
    # 检查是否已经有FFmpeg
    ffmpeg_exe = downloader.bin_dir / "ffmpeg.exe"
    
    if ffmpeg_exe.exists():
        print("🔍 检测到现有FFmpeg安装，正在验证...")
        if downloader.test_ffmpeg_installation():
            print("✅ 现有FFmpeg工作正常")
            downloader.configure_ffmpeg()
            return True
        else:
            print("⚠️ 现有FFmpeg有问题，重新安装...")
    
    # 下载并安装
    success = downloader.download_and_install()
    
    if success:
        print("\n🎊 FFmpeg已成功安装并配置！")
        print("现在可以使用完整的视频处理功能了。")
    else:
        print("\n❌ FFmpeg安装失败")
        print("请手动下载FFmpeg并放置到 tools/ffmpeg/bin/ 目录")
    
    return success

if __name__ == "__main__":
    main()
