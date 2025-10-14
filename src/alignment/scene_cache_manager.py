"""
场景缓存管理器
提供场景分析结果的缓存和加载功能
"""

import os
import json
import hashlib
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.utils.log_handler import get_logger

logger = get_logger("scene_cache_manager")


class SceneCacheManager:
    """场景缓存管理器"""
    
    def __init__(self, cache_dir: str = ".cache/scenes"):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"场景缓存管理器初始化完成: {self.cache_dir}")
    
    def calculate_video_hash(self, video_path: str) -> str:
        """计算视频文件的MD5哈希值
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            MD5哈希值(32位十六进制字符串)
        """
        try:
            # 使用文件路径和文件大小作为哈希输入(避免读取整个大文件)
            file_path = Path(video_path)
            if not file_path.exists():
                logger.warning(f"视频文件不存在: {video_path}")
                return ""
            
            # 组合文件路径、大小和修改时间
            file_size = file_path.stat().st_size
            file_mtime = file_path.stat().st_mtime
            hash_input = f"{video_path}_{file_size}_{file_mtime}"
            
            # 计算MD5
            md5_hash = hashlib.md5(hash_input.encode()).hexdigest()
            logger.debug(f"视频哈希计算完成: {md5_hash}")
            return md5_hash
            
        except Exception as e:
            logger.error(f"计算视频哈希失败: {e}")
            return ""
    
    def get_cache_path(self, video_path: str) -> Path:
        """获取缓存文件路径
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            缓存文件路径
        """
        video_hash = self.calculate_video_hash(video_path)
        if not video_hash:
            return None
        
        cache_file = self.cache_dir / f"{video_hash}.json"
        return cache_file
    
    def has_cache(self, video_path: str) -> bool:
        """检查是否存在缓存
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            是否存在缓存
        """
        cache_file = self.get_cache_path(video_path)
        if cache_file is None:
            return False
        
        exists = cache_file.exists()
        if exists:
            logger.info(f"[缓存] 找到场景缓存: {cache_file.name}")
        return exists
    
    def load_cache(self, video_path: str) -> Optional[List[Dict[str, Any]]]:
        """加载缓存的场景数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            场景数据列表,如果缓存不存在则返回None
        """
        cache_file = self.get_cache_path(video_path)
        if cache_file is None or not cache_file.exists():
            logger.debug(f"缓存不存在: {video_path}")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                scenes_data = json.load(f)
            
            logger.info(f"[缓存] 加载场景数据成功: {len(scenes_data)}个场景")
            return scenes_data
            
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None
    
    def save_cache(self, video_path: str, scenes: List[Any]) -> bool:
        """保存场景数据到缓存
        
        Args:
            video_path: 视频文件路径
            scenes: 场景对象列表
            
        Returns:
            是否保存成功
        """
        cache_file = self.get_cache_path(video_path)
        if cache_file is None:
            logger.warning("无法获取缓存路径")
            return False
        
        try:
            # 将Scene对象转换为字典
            scenes_data = []
            for scene in scenes:
                if hasattr(scene, 'to_dict'):
                    scenes_data.append(scene.to_dict())
                elif isinstance(scene, dict):
                    scenes_data.append(scene)
                else:
                    # 手动构建字典
                    scene_dict = {
                        'scene_id': getattr(scene, 'scene_id', 0),
                        'start_time': getattr(scene, 'start_time', 0.0),
                        'end_time': getattr(scene, 'end_time', 0.0),
                        'duration': getattr(scene, 'duration', 0.0),
                        'scene_type': getattr(scene, 'scene_type', 'unknown'),
                        'location': getattr(scene, 'location', 'unknown'),
                        'confidence': getattr(scene, 'confidence', 0.0),
                        'text': getattr(scene, 'text', ''),
                        'metadata': getattr(scene, 'metadata', {})
                    }
                    scenes_data.append(scene_dict)
            
            # 保存到文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(scenes_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"[缓存] 保存场景数据成功: {len(scenes_data)}个场景 → {cache_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    def clear_cache(self, video_path: Optional[str] = None) -> bool:
        """清除缓存
        
        Args:
            video_path: 视频文件路径,如果为None则清除所有缓存
            
        Returns:
            是否清除成功
        """
        try:
            if video_path is None:
                # 清除所有缓存
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.info("[缓存] 已清除所有场景缓存")
                return True
            else:
                # 清除指定视频的缓存
                cache_file = self.get_cache_path(video_path)
                if cache_file and cache_file.exists():
                    cache_file.unlink()
                    logger.info(f"[缓存] 已清除场景缓存: {cache_file.name}")
                return True
                
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            缓存信息字典
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            info = {
                'cache_dir': str(self.cache_dir),
                'cache_count': len(cache_files),
                'total_size_mb': total_size / (1024 * 1024),
                'cache_files': [f.name for f in cache_files]
            }
            
            logger.debug(f"缓存信息: {info['cache_count']}个文件, {info['total_size_mb']:.2f}MB")
            return info
            
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {
                'cache_dir': str(self.cache_dir),
                'cache_count': 0,
                'total_size_mb': 0.0,
                'cache_files': []
            }


# 全局缓存管理器实例
_cache_manager = None


def get_cache_manager() -> SceneCacheManager:
    """获取全局缓存管理器实例
    
    Returns:
        缓存管理器实例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SceneCacheManager()
    return _cache_manager

