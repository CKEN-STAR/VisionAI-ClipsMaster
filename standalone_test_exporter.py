#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立的剪映导出测试脚本
避开循环导入问题
"""

import os
import sys
import logging
import re
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import zipfile
import uuid
from pathlib import Path
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("exporter_test")

# 测试文件路径
ZH_TEST_VIDEO = "tests/golden_samples/zh/1_20250317_203031.mp4"
ZH_TEST_SRT = "tests/golden_samples/zh/1_20250317_203031.srt"
OUTPUT_DIR = "exporter_output"
OUTPUT_PROJECT = os.path.join(OUTPUT_DIR, "test_project.zip")


def parse_srt(srt_path):
    """解析SRT字幕文件"""
    logger.info(f"解析SRT文件: {srt_path}")
    
    # SRT时间码格式的正则表达式
    timestamp_pattern = re.compile(
        r'(\\\1{2}):(\\\1{2}):(\\\1{2}),(\\\1{3})\\\1+-->\\\1+(\\\1{2}):(\\\1{2}):(\\\1{2}),(\\\1{3})(?:\\\1+.*?)?$'
    )
    
    # 检查文件存在
    if not os.path.exists(srt_path):
        logger.error(f"SRT文件不存在: {srt_path}")
        return None
    
    subtitles = []
    
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按空行分割字幕块
        blocks = re.split(r'\n\\\1*\n', content.strip())
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            
            # 提取索引
            try:
                index = int(lines[0].strip())
            except ValueError:
                index = i + 1
            
            # 提取时间戳
            timestamp_match = None
            for j, line in enumerate(lines):
                match = timestamp_pattern.match(line.strip())
                if match:
                    timestamp_match = match
                    content_start_index = j + 1
                    break
            
            if not timestamp_match:
                continue
            
            # 解析时间戳
            start_time = (
                int(timestamp_match.group(1)) * 3600 +  # 小时
                int(timestamp_match.group(2)) * 60 +    # 分钟
                int(timestamp_match.group(3)) +         # 秒
                int(timestamp_match.group(4)) / 1000    # 毫秒
            )
            
            end_time = (
                int(timestamp_match.group(5)) * 3600 +  # 小时
                int(timestamp_match.group(6)) * 60 +    # 分钟
                int(timestamp_match.group(7)) +         # 秒
                int(timestamp_match.group(8)) / 1000    # 毫秒
            )
            
            # 提取字幕内容
            content = '\n'.join(lines[content_start_index:]).strip()
            
            # 添加到字幕列表
            subtitles.append({
                "id": index,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "text": content
            })
        
        logger.info(f"成功解析字幕，共 {len(subtitles)} 条")
        return subtitles
        
    except Exception as e:
        logger.error(f"解析SRT文件失败: {str(e)}")
        return None


def get_video_info(video_path):
    """获取视频信息"""
    logger.info(f"获取视频信息: {video_path}")
    
    try:
        # 查找 ffprobe 路径
        ffprobe_paths = [
            "bin/ffmpeg-7.1.1-essentials_build/bin/ffprobe.exe",
            "bin/ffprobe.exe",
            "tools/ffmpeg/bin/ffprobe.exe",
            "ffprobe"
        ]
        
        ffprobe_cmd = None
        for path in ffprobe_paths:
            if os.path.exists(path):
                ffprobe_cmd = path
                break
        
        if not ffprobe_cmd:
            logger.error("找不到 ffprobe 工具")
            return None
            
        cmd = [
            ffprobe_cmd,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"获取视频信息失败: {result.stderr}")
            return None
        
        info = json.loads(result.stdout)
        
        # 提取信息
        duration = float(info['format']['duration'])
        
        # 可能有多个流，找到视频流
        width = height = None
        for stream in info.get('streams', []):
            if 'width' in stream and 'height' in stream:
                width = stream['width']
                height = stream['height']
                break
        
        video_info = {
            'duration': duration,
            'width': width,
            'height': height
        }
        
        logger.info(f"视频信息: 时长={duration}秒, 分辨率={width}x{height}")
        return video_info
        
    except Exception as e:
        logger.error(f"获取视频信息出错: {str(e)}")
        return None


def create_jianying_project(video_path, subtitles, output_path):
    """创建剪映工程文件"""
    logger.info(f"创建剪映工程: {output_path}")
    
    try:
        # 获取视频信息
        video_info = get_video_info(video_path)
        if not video_info:
            logger.error("无法获取视频信息")
            return False
        
        # 创建临时目录
        temp_dir = os.path.join(OUTPUT_DIR, "temp_jianying")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建工程ID
        project_id = str(uuid.uuid4()).replace("-", "")
        
        # 创建draft.json (工程主要信息)
        draft = {
            "id": project_id,
            "name": "VisionAI混剪工程",
            "duration": video_info["duration"] * 1000,  # 毫秒
            "material": {
                "video_list": [
                    {
                        "id": f"video_{uuid.uuid4().hex}",
                        "path": video_path,
                        "duration": video_info["duration"] * 1000,
                        "width": video_info["width"],
                        "height": video_info["height"]
                    }
                ]
            },
            "tracks": [
                {
                    "id": "video_track",
                    "type": "video",
                    "clips": []
                },
                {
                    "id": "audio_track",
                    "type": "audio",
                    "clips": []
                }
            ]
        }
        
        # 添加片段
        for subtitle in subtitles:
            clip_id = f"clip_{uuid.uuid4().hex}"
            
            # 视频片段
            video_clip = {
                "id": clip_id,
                "material_id": draft["material"]["video_list"][0]["id"],
                "start_time": subtitle["start_time"] * 1000,  # 毫秒
                "duration": subtitle["duration"] * 1000,
                "in_point": subtitle["start_time"] * 1000,
                "out_point": subtitle["end_time"] * 1000
            }
            
            # 添加字幕信息
            video_clip["text"] = {
                "content": subtitle["text"],
                "font_size": 36,
                "color": "#FFFFFF",
                "alignment": "center",
                "background": "#88000000"
            }
            
            draft["tracks"][0]["clips"].append(video_clip)
        
        # 保存draft.json
        draft_path = os.path.join(temp_dir, "draft.json")
        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(draft, f, indent=2)
        
        # 创建meta.json (工程元数据)
        meta = {
            "app": "VisionAI-ClipsMaster",
            "version": "1.0.0",
            "created_at": int(time.time() * 1000),
            "modified_at": int(time.time() * 1000),
            "project_id": project_id,
            "subtitles_count": len(subtitles)
        }
        
        # 保存meta.json
        meta_path = os.path.join(temp_dir, "meta.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)
        
        # 创建工程压缩包
        with zipfile.ZipFile(output_path, 'w') as zip_file:
            zip_file.write(draft_path, arcname="draft.json")
            zip_file.write(meta_path, arcname="meta.json")
        
        logger.info(f"成功创建剪映工程: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建剪映工程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_xml_project(video_path, subtitles, output_path):
    """创建通用XML工程文件"""
    logger.info(f"创建XML工程: {output_path}")
    
    try:
        # 获取视频信息
        video_info = get_video_info(video_path)
        if not video_info:
            logger.error("无法获取视频信息")
            return False
        
        # 创建XML根元素
        root = ET.Element("project")
        root.set("name", "VisionAI混剪工程")
        
        # 添加媒体素材
        media = ET.SubElement(root, "media")
        video = ET.SubElement(media, "video")
        video.set("path", os.path.abspath(video_path))
        video.set("duration", str(video_info["duration"]))
        video.set("width", str(video_info["width"]))
        video.set("height", str(video_info["height"]))
        
        # 添加时间线
        timeline = ET.SubElement(root, "timeline")
        
        # 添加片段
        for subtitle in subtitles:
            clip = ET.SubElement(timeline, "clip")
            clip.set("id", f"clip_{uuid.uuid4().hex}")
            clip.set("start", str(subtitle["start_time"]))
            clip.set("end", str(subtitle["end_time"]))
            clip.set("duration", str(subtitle["duration"]))
            
            # 添加字幕
            text = ET.SubElement(clip, "text")
            text.text = subtitle["text"]
        
        # 美化输出
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        # 保存XML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        logger.info(f"成功创建XML工程: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建XML工程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("开始独立剪映导出测试")
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 解析原始字幕
    subtitles = parse_srt(ZH_TEST_SRT)
    if not subtitles:
        logger.error("解析字幕失败，无法继续测试")
        return 1
    
    # 创建剪映工程
    jianying_result = create_jianying_project(
        ZH_TEST_VIDEO, 
        subtitles, 
        os.path.join(OUTPUT_DIR, "jianying_project.zip")
    )
    
    # 创建XML工程
    xml_result = create_xml_project(
        ZH_TEST_VIDEO,
        subtitles,
        os.path.join(OUTPUT_DIR, "project.xml")
    )
    
    # 输出结果
    logger.info(f"剪映工程导出: {'成功' if jianying_result else '失败'}")
    logger.info(f"XML工程导出: {'成功' if xml_result else '失败'}")
    
    if jianying_result and xml_result:
        logger.info("导出测试成功完成")
        return 0
    else:
        logger.error("导出测试部分失败")
        return 1


if __name__ == "__main__":
    import time
    sys.exit(main()) 