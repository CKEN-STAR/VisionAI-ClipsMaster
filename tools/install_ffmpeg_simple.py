#!/usr/bin/env python3
"""
简化的FFmpeg安装脚本
为VisionAI-ClipsMaster项目提供FFmpeg支持
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_ffmpeg():
    """检查FFmpeg是否已安装"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ 系统中已安装FFmpeg")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # 检查项目本地FFmpeg
    project_root = Path(__file__).parent
    local_ffmpeg = project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    
    if local_ffmpeg.exists():
        try:
            result = subprocess.run([str(local_ffmpeg), '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ 本地FFmpeg已安装: {local_ffmpeg}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    print("❌ 未找到FFmpeg")
    return False

def show_install_guide():
    """显示安装指南"""
    print("\n" + "=" * 60)
    print("📖 FFmpeg安装指南")
    print("=" * 60)
    print("请选择以下任一方式安装FFmpeg：")
    print()
    print("方式1 - 使用Chocolatey（推荐）：")
    print("1. 以管理员身份打开PowerShell")
    print("2. 安装Chocolatey：")
    print("   Set-ExecutionPolicy Bypass -Scope Process -Force;")
    print("   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;")
    print("   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
    print("3. 安装FFmpeg：")
    print("   choco install ffmpeg")
    print()
    print("方式2 - 手动下载：")
    print("1. 访问 https://www.gyan.dev/ffmpeg/builds/")
    print("2. 下载 'release builds' 中的 'ffmpeg-release-essentials.zip'")
    print("3. 解压到任意目录")
    print("4. 将 bin 目录添加到系统PATH环境变量")
    print()
    print("方式3 - 项目本地安装：")
    print("1. 下载FFmpeg到项目目录：")
    print(f"   {Path(__file__).parent / 'tools' / 'ffmpeg'}")
    print("2. 确保目录结构为：")
    print("   tools/ffmpeg/bin/ffmpeg.exe")
    print("   tools/ffmpeg/bin/ffprobe.exe")
    print()
    print("安装完成后，重新运行程序即可。")
    print("=" * 60)

def create_ffmpeg_placeholder():
    """创建FFmpeg占位符目录"""
    project_root = Path(__file__).parent
    ffmpeg_dir = project_root / "tools" / "ffmpeg" / "bin"
    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建说明文件
    readme_file = ffmpeg_dir.parent / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("""FFmpeg安装目录

请将FFmpeg可执行文件放置在以下位置：
- bin/ffmpeg.exe
- bin/ffprobe.exe

下载地址：
1. https://www.gyan.dev/ffmpeg/builds/
2. https://github.com/BtbN/FFmpeg-Builds/releases

安装后的目录结构应该是：
tools/
└── ffmpeg/
    ├── bin/
    │   ├── ffmpeg.exe
    │   └── ffprobe.exe
    └── README.txt (本文件)
""")
    
    print(f"✅ 已创建FFmpeg目录: {ffmpeg_dir.parent}")
    print(f"📄 请查看说明文件: {readme_file}")

def test_video_processing():
    """测试视频处理功能"""
    print("\n🧪 测试视频处理功能...")
    
    # 检查FFmpeg
    ffmpeg_cmd = None
    
    # 尝试系统FFmpeg
    if shutil.which('ffmpeg'):
        ffmpeg_cmd = 'ffmpeg'
    else:
        # 尝试本地FFmpeg
        project_root = Path(__file__).parent
        local_ffmpeg = project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
        if local_ffmpeg.exists():
            ffmpeg_cmd = str(local_ffmpeg)
    
    if not ffmpeg_cmd:
        print("❌ 无法找到FFmpeg，跳过测试")
        return False
    
    try:
        # 测试基本功能
        result = subprocess.run([
            ffmpeg_cmd, '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-f', 'null', '-'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 视频处理功能测试通过")
            return True
        else:
            print(f"❌ 视频处理测试失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 视频处理测试异常: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎬 VisionAI-ClipsMaster FFmpeg安装助手")
    print("=" * 60)
    
    # 检查当前状态
    if check_ffmpeg():
        print("\n🎉 FFmpeg已正确安装！")
        
        # 测试功能
        if test_video_processing():
            print("\n✅ 视频处理功能正常，可以开始使用VisionAI-ClipsMaster")
        else:
            print("\n⚠️ 视频处理功能异常，但FFmpeg已安装")
        
        return True
    else:
        print("\n❌ 需要安装FFmpeg才能使用视频处理功能")
        
        # 创建占位符目录
        create_ffmpeg_placeholder()
        
        # 显示安装指南
        show_install_guide()
        
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n💡 提示：")
        print("- FFmpeg是视频处理的核心组件")
        print("- 安装后可以处理视频文件和SRT字幕")
        print("- 程序的其他功能不受影响")
        
        input("\n按回车键继续...")
    
    sys.exit(0 if success else 1)
