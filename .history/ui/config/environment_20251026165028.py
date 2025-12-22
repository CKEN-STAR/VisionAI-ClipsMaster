"""
环境检查和配置模块
检查和设置运行环境
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def check_environment() -> Dict[str, bool]:
    """
    检查运行环境
    
    Returns:
        环境检查结果字典
    """
    results = {}
    
    try:
        # 检查Python版本
        results['python_version'] = sys.version_info >= (3, 8)
        
        # 检查FFmpeg
        results['ffmpeg'] = check_ffmpeg()
        
        # 检查必要的Python包
        results['pyqt6'] = check_package('PyQt6')
        results['torch'] = check_package('torch')
        results['numpy'] = check_package('numpy')
        
        # 检查系统资源
        results['memory'] = check_memory()
        results['disk_space'] = check_disk_space()
        
        # 检查权限
        results['write_permission'] = check_write_permission()
        
        return results
        
    except Exception as e:
        print(f"[WARN] 环境检查失败: {e}")
        return {}

def check_ffmpeg() -> bool:
    """检查FFmpeg是否可用"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def setup_ffmpeg_path() -> bool:
    """设置FFmpeg路径，支持自动安装"""
    try:
        # 检查是否禁用了自动下载
        config_file = Path(__file__).parent.parent.parent / "configs" / "auto_download_config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if not config.get('auto_download_enabled', True):
                    print("[INFO] 自动下载已禁用，跳过FFmpeg检查")
                    return True
            except Exception:
                pass

        # 首先检查系统PATH中的ffmpeg
        if shutil.which('ffmpeg'):
            print("[OK] 系统中已安装FFmpeg")
            return True

        # 检查项目本地的ffmpeg
        current_dir = Path(__file__).parent.parent.parent
        ffmpeg_paths = [
            current_dir / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
            current_dir / "ffmpeg" / "ffmpeg.exe",
            current_dir / "ffmpeg" / "bin" / "ffmpeg.exe",
            current_dir / "bin" / "ffmpeg.exe"
        ]

        for ffmpeg_path in ffmpeg_paths:
            if ffmpeg_path.exists():
                # 添加到PATH
                ffmpeg_dir = str(ffmpeg_path.parent)
                if ffmpeg_dir not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                print(f"[OK] FFmpeg路径已设置: {ffmpeg_path}")
                return True

        # 检查FFmpeg配置文件中的路径
        ffmpeg_config_file = current_dir / "configs" / "ffmpeg_config.json"
        if ffmpeg_config_file.exists():
            try:
                import json
                with open(ffmpeg_config_file, 'r', encoding='utf-8') as f:
                    ffmpeg_config = json.load(f)

                # 如果配置了跳过检查，直接返回True（但这不是推荐做法）
                if ffmpeg_config.get('skip_ffmpeg_check', False):
                    print("[INFO] FFmpeg检查已跳过（配置文件设置）")
                    return True

                # 尝试使用配置文件中的路径
                config_ffmpeg_path = ffmpeg_config.get('ffmpeg_path', '')
                if config_ffmpeg_path:
                    # 支持相对路径
                    if not Path(config_ffmpeg_path).is_absolute():
                        config_ffmpeg_path = current_dir / config_ffmpeg_path
                    else:
                        config_ffmpeg_path = Path(config_ffmpeg_path)

                    if config_ffmpeg_path.exists():
                        # 添加到PATH
                        ffmpeg_dir = str(config_ffmpeg_path.parent)
                        if ffmpeg_dir not in os.environ.get('PATH', ''):
                            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                        print(f"[OK] FFmpeg路径已设置（从配置文件）: {config_ffmpeg_path}")
                        return True
                    else:
                        print(f"[WARN] 配置文件中的FFmpeg路径不存在: {config_ffmpeg_path}")
            except Exception as e:
                print(f"[WARN] 读取FFmpeg配置文件失败: {e}")

        # 未找到FFmpeg，返回False
        print("[WARN] 未找到FFmpeg，视频处理功能将不可用")
        print("[INFO] 请下载FFmpeg并放置到 tools/ffmpeg/bin/ 目录")
        print("[INFO] 下载地址: https://ffmpeg.org/download.html")
        return False

    except Exception as e:
        print(f"[WARN] 设置FFmpeg路径失败: {e}")
        return True  # 即使失败也返回True，避免阻塞启动

def _show_ffmpeg_install_guide():
    """显示FFmpeg安装指南"""
    print("\n" + "=" * 50)
    print("📖 FFmpeg安装指南")
    print("=" * 50)
    print("请手动安装FFmpeg以启用视频处理功能：")
    print()
    print("推荐方式（国内用户）：")
    print("1. 清华大学镜像站：")
    print("   https://mirrors.tuna.tsinghua.edu.cn/github-release/BtbN/FFmpeg-Builds/")
    print("2. 下载 ffmpeg-master-latest-win64-gpl.zip")
    print("3. 解压到项目的 tools/ffmpeg/ 目录")
    print()
    print("或者运行以下命令自动安装：")
    print("   python scripts/tools/ffmpeg_installer.py")
    print("=" * 50)

def check_package(package_name: str) -> bool:
    """检查Python包是否已安装"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def check_memory() -> bool:
    """检查内存是否足够"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        # 检查是否有至少2GB可用内存
        return memory.available > 2 * 1024 * 1024 * 1024
    except ImportError:
        # 如果psutil不可用，假设内存足够
        return True
    except Exception:
        return True

def check_disk_space() -> bool:
    """检查磁盘空间是否足够"""
    try:
        import psutil
        disk = psutil.disk_usage('.')
        # 检查是否有至少1GB可用空间
        return disk.free > 1024 * 1024 * 1024
    except ImportError:
        return True
    except Exception:
        return True

def check_write_permission() -> bool:
    """检查写入权限"""
    try:
        test_file = Path('.') / 'test_write_permission.tmp'
        test_file.write_text('test')
        test_file.unlink()
        return True
    except Exception:
        return False

def get_system_info() -> Dict[str, str]:
    """获取系统信息"""
    try:
        info = {
            'platform': sys.platform,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'architecture': sys.maxsize > 2**32 and "64-bit" or "32-bit"
        }
        
        try:
            import psutil
            info['cpu_count'] = str(psutil.cpu_count())
            memory = psutil.virtual_memory()
            info['total_memory'] = f"{memory.total // (1024**3)}GB"
            info['available_memory'] = f"{memory.available // (1024**3)}GB"
        except ImportError:
            pass
        
        return info
        
    except Exception as e:
        print(f"[WARN] 获取系统信息失败: {e}")
        return {}

def setup_environment() -> bool:
    """设置运行环境"""
    try:
        success = True
        
        # 设置编码
        if sys.platform.startswith('win'):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 设置FFmpeg
        if not setup_ffmpeg_path():
            success = False
        
        # 设置CUDA环境（强制CPU模式）
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['TORCH_USE_CUDA_DSA'] = '0'
        
        # 创建必要的目录
        directories = ['cache', 'logs', 'output', 'temp']
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
        
        if success:
            print("[OK] 环境设置完成")
        else:
            print("[WARN] 部分环境设置失败")
        
        return success
        
    except Exception as e:
        print(f"[WARN] 环境设置失败: {e}")
        return False

def get_environment_report() -> str:
    """获取环境报告"""
    try:
        env_check = check_environment()
        sys_info = get_system_info()
        
        report = ["=== 环境检查报告 ==="]
        
        # 系统信息
        report.append("\n系统信息:")
        for key, value in sys_info.items():
            report.append(f"  {key}: {value}")
        
        # 环境检查
        report.append("\n环境检查:")
        for key, value in env_check.items():
            status = "✓" if value else "✗"
            report.append(f"  {status} {key}: {'通过' if value else '失败'}")
        
        return "\n".join(report)
        
    except Exception as e:
        return f"生成环境报告失败: {e}"

__all__ = [
    'check_environment',
    'check_ffmpeg',
    'setup_ffmpeg_path',
    'check_package',
    'get_system_info',
    'setup_environment',
    'get_environment_report'
]
