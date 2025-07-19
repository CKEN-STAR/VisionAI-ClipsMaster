#!/usr/bin/env python3
"""媒体文件检查脚本。

此脚本用于在提交前验证媒体文件的有效性和大小。
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import magic
import numpy as np
from PIL import Image

# 配置
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
MIN_IMAGE_DIMENSION = 100  # 像素
MAX_IMAGE_DIMENSION = 4096  # 像素
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif'}
ALLOWED_VIDEO_TYPES = {'video/mp4', 'video/quicktime', 'video/x-msvideo'}

def check_file_type(file_path: Path) -> Tuple[bool, str]:
    """检查文件类型是否允许。

    Args:
        file_path: 文件路径

    Returns:
        Tuple[bool, str]: (是否通过检查, 错误信息)
    """
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(str(file_path))
    
    if file_type in ALLOWED_IMAGE_TYPES or file_type in ALLOWED_VIDEO_TYPES:
        return True, ""
    return False, f"不支持的文件类型: {file_type}"

def check_file_size(file_path: Path) -> Tuple[bool, str]:
    """检查文件大小是否在限制范围内。

    Args:
        file_path: 文件路径

    Returns:
        Tuple[bool, str]: (是否通过检查, 错误信息)
    """
    size = file_path.stat().st_size
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(str(file_path))
    
    if file_type in ALLOWED_IMAGE_TYPES and size > MAX_IMAGE_SIZE:
        return False, f"图片大小超过限制: {size} > {MAX_IMAGE_SIZE} bytes"
    elif file_type in ALLOWED_VIDEO_TYPES and size > MAX_VIDEO_SIZE:
        return False, f"视频大小超过限制: {size} > {MAX_VIDEO_SIZE} bytes"
    return True, ""

def check_image_content(file_path: Path) -> Tuple[bool, str]:
    """检查图片内容是否有效。

    Args:
        file_path: 文件路径

    Returns:
        Tuple[bool, str]: (是否通过检查, 错误信息)
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                return False, f"图片尺寸过小: {width}x{height}"
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                return False, f"图片尺寸过大: {width}x{height}"
            
            # 检查是否是空白或纯色图片
            if isinstance(img, Image.Image):
                img_array = np.array(img)
                if img_array.std() < 1.0:
                    return False, "图片内容无效（可能是空白或纯色图片）"
            
            return True, ""
    except Exception as e:
        return False, f"图片验证失败: {str(e)}"

def check_video_content(file_path: Path) -> Tuple[bool, str]:
    """检查视频内容是否有效。

    Args:
        file_path: 文件路径

    Returns:
        Tuple[bool, str]: (是否通过检查, 错误信息)
    """
    try:
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            return False, "无法打开视频文件"
        
        # 检查视频时长
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        if duration < 1.0:  # 小于1秒的视频
            return False, f"视频时长过短: {duration:.2f}秒"
        
        # 检查视频分辨率
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            return False, f"视频分辨率过低: {width}x{height}"
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            return False, f"视频分辨率过高: {width}x{height}"
        
        # 检查第一帧是否有效
        ret, frame = cap.read()
        if not ret or frame is None:
            return False, "视频内容无效"
        
        cap.release()
        return True, ""
    except Exception as e:
        return False, f"视频验证失败: {str(e)}"

def main(files: List[str]) -> int:
    """主函数。

    Args:
        files: 要检查的文件列表

    Returns:
        int: 返回码（0表示成功，1表示失败）
    """
    exit_code = 0
    
    for file_path in files:
        path = Path(file_path)
        if not path.exists():
            print(f"文件不存在: {file_path}")
            exit_code = 1
            continue
        
        # 检查文件类型
        type_ok, type_error = check_file_type(path)
        if not type_ok:
            print(f"[{file_path}] {type_error}")
            exit_code = 1
            continue
        
        # 检查文件大小
        size_ok, size_error = check_file_size(path)
        if not size_ok:
            print(f"[{file_path}] {size_error}")
            exit_code = 1
            continue
        
        # 根据文件类型进行内容检查
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(path))
        
        if file_type in ALLOWED_IMAGE_TYPES:
            content_ok, content_error = check_image_content(path)
        elif file_type in ALLOWED_VIDEO_TYPES:
            content_ok, content_error = check_video_content(path)
        else:
            continue
        
        if not content_ok:
            print(f"[{file_path}] {content_error}")
            exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_media_files.py <file1> [file2 ...]")
        sys.exit(1)
    
    sys.exit(main(sys.argv[1:])) 