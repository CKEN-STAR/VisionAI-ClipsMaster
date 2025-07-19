"""
示例工具函数，用于帮助演示
"""
import os
import subprocess
import platform

def create_dummy_video(output_path, duration=5, width=1280, height=720):
    """
    创建一个空白演示视频
    
    参数:
        output_path: 输出文件路径
        duration: 视频时长（秒）
        width: 视频宽度
        height: 视频高度
    
    注意: 需要系统安装FFmpeg
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 检查FFmpeg是否可用
        try:
            if platform.system() == "Windows":
                subprocess.run(["where", "ffmpeg"], check=True, capture_output=True)
            else:
                subprocess.run(["which", "ffmpeg"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("警告: 未检测到FFmpeg，将创建空文件代替")
            with open(output_path, "wb") as f:
                f.write(b"DUMMY VIDEO - Please replace with actual video file\n")
            return True
        
        # 使用FFmpeg生成演示视频
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=gray:s={width}x{height}:d={duration}",
            "-vf", "drawtext=text='VisionAI-ClipsMaster Demo':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"创建演示视频失败: {e}")
        return False

def extract_frames(video_path, output_dir, fps=1):
    """
    从视频中提取帧
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps={fps}",
            f"{output_dir}/frame_%04d.jpg"
        ]
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"提取帧失败: {e}")
        return False 