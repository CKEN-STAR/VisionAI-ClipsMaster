"""
文件操作工具集

提供文件操作的辅助函数
"""

import os
import shutil
import json
import yaml
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import datetime
import tempfile

logger = logging.getLogger("file_utils")


def ensure_directory(directory: Union[str, Path]) -> Path:
    """
    确保目录存在，如不存在则创建

    Args:
        directory: 目录路径

    Returns:
        目录Path对象
    """
    dir_path = Path(directory)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    确保目录存在，如不存在则创建（ensure_directory的别名）

    Args:
        directory: 目录路径

    Returns:
        目录Path对象
    """
    return ensure_directory(directory)


def safe_write_file(file_path: Union[str, Path], content: Union[str, bytes], 
                   mode: str = "w", encoding: Optional[str] = "utf-8") -> bool:
    """
    安全地写入文件（先写入临时文件，然后重命名）
    
    Args:
        file_path: 文件路径
        content: 文件内容
        mode: 写入模式（默认为w，文本模式）
        encoding: 编码方式（默认为utf-8，仅在文本模式下有效）
        
    Returns:
        是否成功写入
    """
    file_path = Path(file_path)
    temp_file = None
    
    try:
        # 确保目录存在
        ensure_directory(file_path.parent)
        
        # 创建临时文件
        dir_path = file_path.parent
        with tempfile.NamedTemporaryFile(delete=False, dir=dir_path) as tf:
            temp_file = Path(tf.name)
        
        # 写入临时文件
        if "b" in mode:  # 二进制模式
            with open(temp_file, mode) as f:
                f.write(content)
        else:  # 文本模式
            with open(temp_file, mode, encoding=encoding) as f:
                f.write(content)
        
        # 重命名临时文件
        shutil.move(str(temp_file), str(file_path))
        return True
    
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {e}")
        
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
                
        return False


def safe_read_json(file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """
    安全地读取JSON文件
    
    Args:
        file_path: 文件路径
        default: 默认值（如果文件不存在或读取失败）
        
    Returns:
        JSON数据，或默认值
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"读取JSON文件 {file_path} 失败: {e}")
        return default if default is not None else {}


def safe_write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """
    安全地写入JSON文件
    
    Args:
        file_path: 文件路径
        data: 数据
        indent: 缩进级别
        
    Returns:
        是否成功写入
    """
    try:
        content = json.dumps(data, ensure_ascii=False, indent=indent)
        return safe_write_file(file_path, content)
    except Exception as e:
        logger.error(f"将数据序列化为JSON失败: {e}")
        return False


def safe_read_yaml(file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """
    安全地读取YAML文件
    
    Args:
        file_path: 文件路径
        default: 默认值（如果文件不存在或读取失败）
        
    Returns:
        YAML数据，或默认值
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"读取YAML文件 {file_path} 失败: {e}")
        return default if default is not None else {}


def safe_write_yaml(file_path: Union[str, Path], data: Any) -> bool:
    """
    安全地写入YAML文件
    
    Args:
        file_path: 文件路径
        data: 数据
        
    Returns:
        是否成功写入
    """
    try:
        content = yaml.dump(data, allow_unicode=True, sort_keys=False)
        return safe_write_file(file_path, content)
    except Exception as e:
        logger.error(f"将数据序列化为YAML失败: {e}")
        return False


def clean_old_files(directory: Union[str, Path], extension: str = "", 
                   max_age_days: int = 7) -> int:
    """
    清理指定目录中的过期文件
    
    Args:
        directory: 目录路径
        extension: 文件扩展名（如.json, .log等，为空则匹配所有文件）
        max_age_days: 最大保留天数
        
    Returns:
        删除的文件数量
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return 0
    
    now = datetime.datetime.now()
    deleted_count = 0
    
    for file_path in dir_path.iterdir():
        if not file_path.is_file():
            continue
            
        if extension and file_path.suffix != extension:
            continue
        
        # 获取文件修改时间
        file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
        age_days = (now - file_time).days
        
        # 如果文件超过最大保留天数，删除
        if age_days > max_age_days:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除文件 {file_path} 失败: {e}")
    
    return deleted_count


def find_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = True) -> List[Path]:
    """
    在目录中查找匹配模式的文件
    
    Args:
        directory: 目录路径
        pattern: 文件名模式（支持glob模式）
        recursive: 是否递归搜索子目录
        
    Returns:
        匹配的文件路径列表
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    if recursive:
        return list(dir_path.glob(f"**/{pattern}"))
    else:
        return list(dir_path.glob(pattern))


def get_file_size(file_path: Union[str, Path], unit: str = "B") -> float:
    """
    获取文件大小
    
    Args:
        file_path: 文件路径
        unit: 单位（B, KB, MB, GB）
        
    Returns:
        文件大小（指定单位）
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return 0
    
    size_bytes = path.stat().st_size
    
    if unit.upper() == "B":
        return size_bytes
    elif unit.upper() == "KB":
        return size_bytes / 1024
    elif unit.upper() == "MB":
        return size_bytes / (1024 * 1024)
    elif unit.upper() == "GB":
        return size_bytes / (1024 * 1024 * 1024)
    else:
        raise ValueError(f"不支持的单位: {unit}")


def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None, 
               timestamp: bool = True) -> Optional[Path]:
    """
    备份文件
    
    Args:
        file_path: 文件路径
        backup_dir: 备份目录（如果为None，则在原目录创建备份）
        timestamp: 是否在备份文件名中添加时间戳
        
    Returns:
        备份文件路径，如果备份失败则返回None
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        logger.warning(f"文件 {file_path} 不存在，无法备份")
        return None
    
    # 确定备份目录
    if backup_dir:
        backup_path = Path(backup_dir)
        ensure_directory(backup_path)
    else:
        backup_path = path.parent
    
    # 创建备份文件名
    if timestamp:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.stem}_{timestamp_str}{path.suffix}"
    else:
        backup_name = f"{path.stem}_backup{path.suffix}"
    
    backup_file = backup_path / backup_name
    
    try:
        shutil.copy2(path, backup_file)
        return backup_file
    except Exception as e:
        logger.error(f"备份文件 {file_path} 失败: {e}")
        return None


def get_file_path(relative_path: Union[str, Path]) -> str:
    """
    获取文件的完整路径
    
    如果提供的是相对路径，则相对于项目根目录解析；
    如果提供的是绝对路径，则直接返回
    
    Args:
        relative_path: 相对路径或绝对路径
        
    Returns:
        完整文件路径
    """
    path = Path(relative_path)
    
    # 如果是绝对路径，直接返回
    if path.is_absolute():
        return str(path)
    
    # 获取项目根目录
    # 假设项目结构为 project_root/src/utils/file_utils.py
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # 拼接完整路径
    full_path = project_root / path
    
    return str(full_path) 