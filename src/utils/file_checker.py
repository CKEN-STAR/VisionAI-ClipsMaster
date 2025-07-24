"""
文件完整性校验工具

提供文件哈希计算、完整性验证和文件修复功能：
1. 计算文件哈希值
2. 验证文件完整性
3. 检测文件损坏
"""

import json
import os
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Tuple, Union, List, Optional

try:
    import cv2
except ImportError:
    cv2 = None
    # 让依赖cv2的函数在未安装时直接return或raise

from loguru import logger


class FileValidator:
    """文件验证器基类。"""

    def __init__(self, config_path: str = "configs/security_policy.json") -> None:
        """初始化文件验证器。

        Args:
            config_path: 安全配置文件路径。
        """
        self.config = self._load_security_config(config_path)
        self.allowed_formats = self.config["content_security"]["input_validation"][
            "allowed_formats"
        ]

    def _load_security_config(self, config_path: str) -> Dict[str, dict]:
        """加载安全配置。

        Args:
            config_path: 配置文件路径。

        Returns:
            包含安全配置的字典。
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load security config: {e}")
            return {
                "content_security": {
                    "input_validation": {"allowed_formats": ["jpg", "png", "mp4", "mov"]}
                }
            }

    def validate_file_exists(self, file_path: str) -> bool:
        """验证文件是否存在。

        Args:
            file_path: 文件路径。

        Returns:
            文件是否存在。
        """
        return os.path.exists(file_path)

    def validate_file_size(self, file_path: str) -> bool:
        """验证文件大小是否在允许范围内。

        Args:
            file_path: 文件路径。

        Returns:
            文件大小是否合法。
        """
        max_size = self.config.get("resource_limits", {}).get(
            "max_file_size", 104857600
        )  # 默认100MB
        return os.path.getsize(file_path) <= max_size

    def validate_file_format(self, file_path: str) -> bool:
        """验证文件格式是否被允许。

        Args:
            file_path: 文件路径。

        Returns:
            文件格式是否合法。
        """
        if not self.validate_file_exists(file_path):
            return False
        ext = os.path.splitext(file_path)[1][1:].lower()
        return ext in self.allowed_formats or ext in ['srt', 'ass', 'vtt']  # 添加字幕格式支持

    def calculate_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """计算文件哈希值。

        Args:
            file_path: 文件路径。
            algorithm: 哈希算法，支持 'md5', 'sha1', 'sha256'。

        Returns:
            文件的哈希值字符串。
        """
        if not self.validate_file_exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 选择哈希算法
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"不支持的哈希算法: {algorithm}")

        try:
            with open(file_path, 'rb') as f:
                # 分块读取文件以处理大文件
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            raise

    def check_file_safety(self, file_path: str) -> bool:
        """检查文件安全性。

        Args:
            file_path: 文件路径。

        Returns:
            文件是否安全。
        """
        try:
            # 基础安全检查
            if not self.validate_file_exists(file_path):
                return False

            # 检查文件大小
            if not self.validate_file_size(file_path):
                logger.warning(f"文件大小超出限制: {file_path}")
                return False

            # 检查文件格式
            if not self.validate_file_format(file_path):
                logger.warning(f"文件格式不被允许: {file_path}")
                return False

            # 检查文件路径安全性
            if self._check_path_traversal(file_path):
                logger.warning(f"检测到路径遍历攻击: {file_path}")
                return False

            # 检查文件内容（针对字幕文件）
            if file_path.lower().endswith(('.srt', '.ass', '.vtt')):
                return self._check_subtitle_content_safety(file_path)

            return True

        except Exception as e:
            logger.error(f"文件安全检查失败: {e}")
            return False

    def verify_integrity(self, file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """验证文件完整性。

        Args:
            file_path: 文件路径。
            expected_hash: 期望的哈希值。
            algorithm: 哈希算法。

        Returns:
            文件完整性是否正确。
        """
        try:
            actual_hash = self.calculate_hash(file_path, algorithm)
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"文件完整性验证失败: {e}")
            return False

    def _check_path_traversal(self, file_path: str) -> bool:
        """检查路径遍历攻击。

        Args:
            file_path: 文件路径。

        Returns:
            是否存在路径遍历攻击。
        """
        # 检查危险的路径模式
        dangerous_patterns = ['../', '..\\', '../', '..\\\\']
        normalized_path = os.path.normpath(file_path)

        for pattern in dangerous_patterns:
            if pattern in file_path or pattern in normalized_path:
                return True

        return False

    def _check_subtitle_content_safety(self, file_path: str) -> bool:
        """检查字幕文件内容安全性。

        Args:
            file_path: 字幕文件路径。

        Returns:
            内容是否安全。
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024 * 1024)  # 只读取前1MB内容

            # 检查是否包含恶意脚本
            dangerous_patterns = [
                '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
                'eval(', 'document.', 'window.', 'alert('
            ]

            content_lower = content.lower()
            for pattern in dangerous_patterns:
                if pattern in content_lower:
                    logger.warning(f"字幕文件包含潜在危险内容: {pattern}")
                    return False

            return True

        except Exception as e:
            logger.error(f"字幕内容安全检查失败: {e}")
            return False


class VideoValidator(FileValidator):
    """视频文件验证器。"""

    def __init__(self, config_path: str = "configs/security_policy.json") -> None:
        """初始化视频验证器。

        Args:
            config_path: 安全配置文件路径。
        """
        super().__init__(config_path)
        self.video_formats = ["mp4", "mov"]

    def get_video_duration(self, video_path: str) -> float:
        """获取视频时长。"""
        try:
            try:
                import ffmpeg
            except ImportError:
                print("ffmpeg not installed, video duration check skipped.")
                raise ValueError("ffmpeg not installed")
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
            return float(probe["format"]["duration"])
        except Exception as e:
            raise ValueError(f"Error getting video duration: {e}")

    def validate_video_srt_sync(
        self, video_path: str, srt_path: str, max_drift: float = 0.5
    ) -> bool:
        """检验视频与字幕的同步率。

        Args:
            video_path: 视频文件路径。
            srt_path: 字幕文件路径。
            max_drift: 最大允许的时间偏差（秒）。

        Returns:
            视频和字幕是否同步。
        """
        if not all(self.validate_file_exists(f) for f in [video_path, srt_path]):
            return False

        try:
            video_dur = self.get_video_duration(video_path)
            srt_dur = self.parse_srt_duration(srt_path)
            return abs(video_dur - srt_dur) <= max_drift
        except Exception as e:
            print(f"Error validating video-srt sync: {e}")
            return False

    def parse_srt_duration(self, srt_path: str) -> float:
        """解析SRT文件获取总时长。

        Args:
            srt_path: 字幕文件路径。

        Returns:
            字幕总时长（秒）。

        Raises:
            ValueError: 解析字幕文件失败。
        """
        try:
            with open(srt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return 0.0

            # 检查是否包含有效的时间戳行
            last_time = None
            for line in reversed(lines):
                if " --> " not in line:
                    continue
                time_parts = line.strip().split(" --> ")
                if len(time_parts) != 2:
                    raise ValueError("Invalid SRT timestamp format")
                last_time = time_parts[1]
                break

            if last_time is None:
                raise ValueError("No valid timestamp found in SRT file")

            # 验证时间戳格式
            if ":" not in last_time or "," not in last_time:
                raise ValueError("Invalid SRT timestamp format")

            h, m, s = last_time.split(":")
            s, ms = s.split(",")

            # 验证时间值的合法性
            if not all(x.isdigit() for x in [h, m, s, ms]):
                raise ValueError("Invalid SRT timestamp values")

            if int(m) >= 60 or int(s) >= 60:
                raise ValueError("Invalid minutes or seconds value")

            return float(h) * 3600 + float(m) * 60 + float(s) + float(ms) / 1000
        except (ValueError, IndexError) as e:
            raise ValueError(f"Error parsing SRT file: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error parsing SRT file: {e}")

    def validate_video_quality(self, video_path: str) -> Tuple[bool, Dict[str, bool]]:
        """验证视频质量。"""
        try:
            try:
                import ffmpeg
            except ImportError:
                print("ffmpeg not installed, video quality check skipped.")
                return False, {}
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")

            width = int(video_info["width"])
            height = int(video_info["height"])
            fps = eval(video_info["r_frame_rate"])

            quality_check = {
                "resolution": width * height >= 1280 * 720,  # 至少720p
                "aspect_ratio": abs(width / height - 16 / 9) < 0.1,  # 接近16:9
                "frame_rate": fps >= 24,  # 至少24fps
            }

            return all(quality_check.values()), quality_check
        except Exception as e:
            print(f"Error checking video quality: {e}")
            return False, {}


class ImageValidator(FileValidator):
    """图片文件验证器。"""

    def __init__(self, config_path: str = "configs/security_policy.json") -> None:
        """初始化图片验证器。

        Args:
            config_path: 安全配置文件路径。
        """
        super().__init__(config_path)
        self.image_formats = ["jpg", "png"]

    def validate_image_quality(self, image_path: str) -> Tuple[bool, Dict[str, bool]]:
        """验证图片质量。

        Args:
            image_path: 图片文件路径。

        Returns:
            (是否通过质量检查, 质量检查详情)。
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                quality_check = {
                    "resolution": width * height >= 1280 * 720,  # 至少720p
                    "aspect_ratio": abs(width / height - 16 / 9) < 0.1,  # 接近16:9
                    "format": img.format.lower() in self.image_formats,
                }
                return all(quality_check.values()), quality_check
        except Exception as e:
            print(f"Error checking image quality: {e}")
            return False, {}

    def check_image_watermark(self, image_path: str) -> bool:
        """检查图片是否包含水印。

        Args:
            image_path: 图片文件路径。

        Returns:
            是否包含水印。
        """
        try:
            try:
                import cv2
            except ImportError:
                print("cv2 not installed, watermark check skipped.")
                return False
            img = cv2.imread(image_path)
            if img is None:
                return False

            # 简单的水印检测算法
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)[1]
            contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

            # 分析轮廓特征判断是否存在水印
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 10000:  # 水印通常在这个面积范围
                    return True
            return False
        except Exception as e:
            print(f"Error checking image watermark: {e}")
            return False


def validate_video_srt_sync(video_path: str, srt_path: str, max_drift: float = 0.5) -> bool:
    """兼容性包装函数，保持原有接口。

    Args:
        video_path: 视频文件路径。
        srt_path: 字幕文件路径。
        max_drift: 最大允许的时间偏差（秒）。

    Returns:
        视频和字幕是否同步。
    """
    validator = VideoValidator()
    return validator.validate_video_srt_sync(video_path, srt_path, max_drift)


def calculate_file_hash(file_path: str, algorithm: str = "md5", buffer_size: int = 65536) -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法，可选 md5, sha1, sha256
        buffer_size: 读取缓冲区大小
        
    Returns:
        文件哈希值
        
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 无权访问文件
        IOError: 读取文件错误
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if not os.path.isfile(file_path):
        raise IOError(f"路径不是文件: {file_path}")
    
    # 选择哈希算法
    if algorithm.lower() == "md5":
        hash_obj = hashlib.md5()
    elif algorithm.lower() == "sha1":
        hash_obj = hashlib.sha1()
    elif algorithm.lower() == "sha256":
        hash_obj = hashlib.sha256()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")
    
    # 逐块读取文件计算哈希
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(buffer_size), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    except PermissionError:
        raise PermissionError(f"无权读取文件: {file_path}")
    except Exception as e:
        raise IOError(f"计算文件哈希时出错: {e}")


def verify_file_integrity(file_path: str, expected_hash: str, algorithm: str = "md5") -> bool:
    """
    验证文件完整性
    
    Args:
        file_path: 文件路径
        expected_hash: 期望的哈希值
        algorithm: 哈希算法
        
    Returns:
        文件是否完整
    """
    try:
        actual_hash = calculate_file_hash(file_path, algorithm)
        is_valid = actual_hash.lower() == expected_hash.lower()
        
        if not is_valid:
            logger.warning(f"文件校验失败: {file_path}")
            logger.debug(f"预期哈希: {expected_hash}")
            logger.debug(f"实际哈希: {actual_hash}")
        
        return is_valid
    except Exception as e:
        logger.error(f"验证文件完整性时出错: {e}")
        return False


def create_file_hash_record(directory: str, 
                           output_file: str = "file_hashes.txt",
                           file_patterns = None) -> Dict[str, str]:
    """
    为目录中的文件创建哈希记录
    
    Args:
        directory: 目录路径
        output_file: 输出文件路径
        file_patterns: 文件模式列表 (例如 ["*.txt", "*.py"])
        
    Returns:
        文件路径到哈希值的映射
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"路径不是目录: {directory}")
    
    # 默认包含所有文件
    if file_patterns is None:
        file_patterns = ["*"]
    
    # 收集符合模式的文件
    files_to_hash = []
    for pattern in file_patterns:
        p = Path(directory)
        files_to_hash.extend(p.glob(pattern))
    
    # 计算并记录哈希值
    hash_records = {}
    for file_path in files_to_hash:
        if file_path.is_file():
            try:
                file_hash = calculate_file_hash(str(file_path))
                # 存储相对路径
                rel_path = os.path.relpath(str(file_path), directory)
                hash_records[rel_path] = file_hash
                logger.debug(f"已计算哈希: {rel_path} -> {file_hash}")
            except Exception as e:
                logger.warning(f"计算 {file_path} 的哈希时出错: {e}")
    
    # 保存哈希记录到文件
    output_path = os.path.join(directory, output_file)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for file_path, file_hash in hash_records.items():
                f.write(f"{file_hash}  {file_path}\n")
        logger.info(f"已保存哈希记录到: {output_path}")
    except Exception as e:
        logger.error(f"保存哈希记录时出错: {e}")
    
    return hash_records


def verify_directory_integrity(directory: str, 
                              hash_file: str = "file_hashes.txt") -> Tuple[bool, List[str]]:
    """
    验证目录内文件的完整性
    
    Args:
        directory: 目录路径
        hash_file: 哈希记录文件
        
    Returns:
        Tuple[bool, List[str]]: 所有文件是否完整，失败的文件列表
    """
    hash_file_path = os.path.join(directory, hash_file)
    
    if not os.path.exists(hash_file_path):
        logger.error(f"哈希记录文件不存在: {hash_file_path}")
        return False, ["哈希记录文件不存在"]
    
    # 读取哈希记录
    expected_hashes = {}
    try:
        with open(hash_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split("  ", 1)
                    if len(parts) == 2:
                        file_hash, file_path = parts
                        expected_hashes[file_path] = file_hash
    except Exception as e:
        logger.error(f"读取哈希记录时出错: {e}")
        return False, [f"读取哈希记录时出错: {e}"]
    
    # 验证文件完整性
    failed_files = []
    for file_path, expected_hash in expected_hashes.items():
        full_path = os.path.join(directory, file_path)
        if not os.path.exists(full_path):
            logger.warning(f"文件丢失: {file_path}")
            failed_files.append(f"丢失: {file_path}")
            continue
        
        if not verify_file_integrity(full_path, expected_hash):
            logger.warning(f"文件损坏: {file_path}")
            failed_files.append(f"损坏: {file_path}")
    
    is_valid = len(failed_files) == 0
    if is_valid:
        logger.info(f"目录 {directory} 的所有文件完整性验证通过")
    else:
        logger.warning(f"目录 {directory} 有 {len(failed_files)} 个文件验证失败")
    
    return is_valid, failed_files


def backup_file(file_path: str, backup_suffix: str = ".bak") -> Optional[str]:
    """
    备份文件
    
    Args:
        file_path: 文件路径
        backup_suffix: 备份文件后缀
        
    Returns:
        备份文件路径，如果备份失败则返回None
    """
    if not os.path.exists(file_path):
        logger.warning(f"要备份的文件不存在: {file_path}")
        return None
    
    backup_path = f"{file_path}{backup_suffix}"
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"已备份文件: {file_path} -> {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"备份文件时出错: {e}")
        return None


def restore_from_backup(backup_path: str, target_path: str = None) -> bool:
    """
    从备份恢复文件
    
    Args:
        backup_path: 备份文件路径
        target_path: 目标文件路径，如果为None则去除后缀
        
    Returns:
        恢复是否成功
    """
    if not os.path.exists(backup_path):
        logger.warning(f"备份文件不存在: {backup_path}")
        return False
    
    if target_path is None:
        # 自动确定目标路径（去除后缀）
        if backup_path.endswith(".bak"):
            target_path = backup_path[:-4]  # 去除.bak后缀
        else:
            logger.warning(f"无法确定目标路径: {backup_path}")
            return False
    
    try:
        # 如果目标文件存在，先备份
        if os.path.exists(target_path):
            temp_backup = f"{target_path}.old"
            shutil.copy2(target_path, temp_backup)
            logger.debug(f"已创建临时备份: {target_path} -> {temp_backup}")
        
        # 恢复文件
        shutil.copy2(backup_path, target_path)
        logger.info(f"已从备份恢复: {backup_path} -> {target_path}")
        return True
    except Exception as e:
        logger.error(f"从备份恢复时出错: {e}")
        return False


if __name__ == "__main__":
    # 简单测试
    import tempfile
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, World!")
        tmp_path = tmp.name
    
    print(f"测试文件: {tmp_path}")
    file_hash = calculate_file_hash(tmp_path)
    print(f"文件哈希: {file_hash}")
    
    is_valid = verify_file_integrity(tmp_path, file_hash)
    print(f"验证结果: {is_valid}")
    
    backup_path = backup_file(tmp_path)
    print(f"备份文件: {backup_path}")
    
    # 修改原文件
    with open(tmp_path, "w") as f:
        f.write("Modified content")
    
    is_valid = verify_file_integrity(tmp_path, file_hash)
    print(f"修改后验证结果: {is_valid}")
    
    # 从备份恢复
    restore_from_backup(backup_path)
    
    # 验证恢复后的文件
    is_valid = verify_file_integrity(tmp_path, file_hash)
    print(f"恢复后验证结果: {is_valid}")
    
    # 清理测试文件
    os.unlink(tmp_path)
    if backup_path:
        os.unlink(backup_path)
