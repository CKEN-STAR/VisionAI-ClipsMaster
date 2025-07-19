"""
设置FFmpeg路径以供pydub和其他媒体处理库使用
"""

import os
import sys
from pathlib import Path

def set_ffmpeg_path():
    """将FFmpeg目录添加到环境变量PATH中"""
    project_root = Path(__file__).resolve().parent
    ffmpeg_path = os.path.join(project_root, "tools", "ffmpeg", "bin")
    
    # 确保路径存在
    if not os.path.exists(ffmpeg_path):
        print(f"错误: FFmpeg路径不存在: {ffmpeg_path}")
        return False
    
    # 添加到PATH环境变量
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + ffmpeg_path
    print(f"已添加FFmpeg到PATH: {ffmpeg_path}")
    
    # 为pydub设置特定环境变量
    ffmpeg_exe = os.path.join(ffmpeg_path, "ffmpeg.exe")
    ffprobe_exe = os.path.join(ffmpeg_path, "ffprobe.exe")
    
    os.environ["FFMPEG_BINARY"] = ffmpeg_exe
    os.environ["FFPROBE_BINARY"] = ffprobe_exe
    
    # 直接设置pydub的路径
    try:
        from pydub import AudioSegment
        AudioSegment.converter = ffmpeg_exe
        AudioSegment.ffprobe = ffprobe_exe
    except ImportError:
        # pydub未安装，忽略
        pass
    
    return True

if __name__ == "__main__":
    if set_ffmpeg_path():
        print("FFmpeg路径设置成功!")
        
        # 测试pydub是否能够找到FFmpeg
        try:
            import pydub
            print("pydub导入成功")
            
            # 创建一个简单的测试
            from pydub.generators import Sine
            sine = Sine(440).to_audio_segment(duration=100)
            print("pydub能够正常使用FFmpeg")
            
            # 测试导出功能
            test_file = "test_sine.wav"
            sine.export(test_file, format="wav")
            print(f"成功导出音频文件: {test_file}")
            
            # 清理
            import os
            if os.path.exists(test_file):
                os.remove(test_file)
                print("测试文件已删除")
            
        except Exception as e:
            print(f"pydub测试失败: {e}")
    else:
        print("FFmpeg路径设置失败!") 