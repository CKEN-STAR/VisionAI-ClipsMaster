#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化版的ClipGenerator
"""

import os
import sys
import tempfile
import subprocess
import shutil
from typing import List, Dict, Any

# 添加路径
sys.path.insert(0, 'src')

class SimpleClipGenerator:
    """简化版的ClipGenerator用于测试"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="simple_clip_")
        
        # 设置FFmpeg路径
        project_root = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_path = os.path.join(project_root, "tools", "ffmpeg", "bin", "ffmpeg.exe")
        self.ffmpeg_path = ffmpeg_path if os.path.exists(ffmpeg_path) else 'ffmpeg'
    
    def extract_segments(self, video_path: str, segments: List[Dict[str, Any]]) -> List[str]:
        """从视频中提取指定片段"""
        try:
            extracted_files = []
            
            for i, segment in enumerate(segments):
                start_time = segment.get("start", "00:00:00,000")
                end_time = segment.get("end", "00:00:02,000")
                
                # 转换时间格式
                start_seconds = self._time_to_seconds(start_time)
                end_seconds = self._time_to_seconds(end_time)
                duration = end_seconds - start_seconds
                
                if duration <= 0:
                    print(f"片段 {i} 持续时间无效: {duration}秒")
                    continue
                
                # 生成输出文件名
                output_file = os.path.join(self.temp_dir, f"segment_{i:03d}.mp4")
                
                # 使用FFmpeg提取片段
                cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-ss', str(start_seconds),
                    '-t', str(duration),
                    '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    '-y',
                    output_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(output_file):
                    extracted_files.append(output_file)
                    print(f"成功提取片段 {i}: {output_file}")
                else:
                    print(f"提取片段 {i} 失败: {result.stderr}")
            
            print(f"成功提取 {len(extracted_files)} 个片段")
            return extracted_files
            
        except Exception as e:
            print(f"提取片段失败: {e}")
            return []
    
    def concatenate_segments(self, segments: List[Dict[str, Any]], output_path: str) -> bool:
        """拼接视频片段"""
        try:
            if not segments:
                print("没有片段可供拼接")
                return False
            
            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 如果只有一个片段，直接复制
            if len(segments) == 1:
                source_file = segments[0].get("source", segments[0].get("file"))
                if source_file and os.path.exists(source_file):
                    shutil.copy2(source_file, output_path)
                    print(f"单片段复制完成: {output_path}")
                    return True
                else:
                    print(f"源文件不存在: {source_file}")
                    return False
            
            # 多个片段需要拼接
            filelist_path = os.path.join(self.temp_dir, "filelist.txt")
            
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for segment in segments:
                    source_file = segment.get("source", segment.get("file"))
                    if source_file and os.path.exists(source_file):
                        escaped_path = source_file.replace("\\", "/").replace("'", "\\'")
                        f.write(f"file '{escaped_path}'\n")
                    else:
                        print(f"跳过不存在的文件: {source_file}")
            
            # 使用FFmpeg concat协议拼接
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-c', 'copy',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"视频拼接成功: {output_path}")
                
                # 清理临时文件
                if os.path.exists(filelist_path):
                    os.remove(filelist_path)
                
                return True
            else:
                print(f"视频拼接失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"拼接片段失败: {e}")
            return False
    
    def _time_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        try:
            time_str = time_str.replace(',', '.')
            parts = time_str.split(':')
            
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(parts[0])
                
        except Exception as e:
            print(f"时间转换失败: {time_str}, {e}")
            return 0.0

if __name__ == "__main__":
    print("=== 测试简化版ClipGenerator ===")
    
    # 创建实例
    cg = SimpleClipGenerator()
    
    # 检查方法
    methods = [m for m in dir(cg) if not m.startswith('_')]
    print(f"可用方法: {methods}")
    
    # 测试方法存在性
    print(f"extract_segments: {hasattr(cg, 'extract_segments')}")
    print(f"concatenate_segments: {hasattr(cg, 'concatenate_segments')}")
    
    # 测试concatenate_segments方法
    test_segments = [
        {"source": "nonexistent1.mp4"},
        {"source": "nonexistent2.mp4"}
    ]
    test_output = "test_output.mp4"
    
    print("\n=== 测试concatenate_segments方法 ===")
    result = cg.concatenate_segments(test_segments, test_output)
    print(f"方法调用结果: {result}")
    
    print("\n测试完成")
