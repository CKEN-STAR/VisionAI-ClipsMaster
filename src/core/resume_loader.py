"""断点续载管理器模块

此模块实现了模型加载的断点续传功能，包括:
1. 加载进度保存
2. 断点恢复
3. 校验和验证
4. 分片管理
5. 错误恢复
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger

class ResumeLoader:
    """断点续载管理器"""
    
    def __init__(self,
                 save_dir: str,
                 chunk_size: int = 8 * 1024 * 1024,  # 8MB
                 max_retries: int = 3):
        """初始化断点续载管理器
        
        Args:
            save_dir: 保存目录
            chunk_size: 分片大小(字节)
            max_retries: 最大重试次数
        """
        self.save_dir = Path(save_dir)
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        
        # 确保保存目录存在
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前加载状态
        self._current_task: Optional[Dict] = None
        self._loaded_chunks: List[int] = []
        self._verified_chunks: List[int] = []
        
        # 性能统计
        self._stats = {
            "total_bytes": 0,
            "loaded_bytes": 0,
            "failed_chunks": 0,
            "retry_count": 0
        }
    
    def start_loading(self,
                     model_path: str,
                     total_size: int,
                     expected_checksum: Optional[str] = None) -> bool:
        """开始加载任务
        
        Args:
            model_path: 模型文件路径
            total_size: 总大小(字节)
            expected_checksum: 预期的校验和
            
        Returns:
            bool: 是否成功启动
        """
        try:
            # 初始化任务信息
            self._current_task = {
                'model_path': str(model_path),
                'total_size': total_size,
                'expected_checksum': expected_checksum,
                'start_time': time.time(),
                'chunk_size': self.chunk_size,
                'total_chunks': (total_size + self.chunk_size - 1) // self.chunk_size
            }
            
            # 保存任务状态
            self._save_progress()
            
            logger.info(f"开始加载任务: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"启动加载任务失败: {str(e)}")
            return False
    
    def load_chunk(self, chunk_index: int, chunk_data: bytes) -> bool:
        """加载数据分片
        
        Args:
            chunk_index: 分片索引
            chunk_data: 分片数据
            
        Returns:
            bool: 是否加载成功
        """
        if not self._current_task:
            logger.error("没有活动的加载任务")
            return False
            
        try:
            # 验证分片
            if not self._verify_chunk(chunk_index, chunk_data):
                return False
            
            # 保存分片
            chunk_path = self._get_chunk_path(chunk_index)
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            
            # 更新状态
            self._loaded_chunks.append(chunk_index)
            self._verified_chunks.append(chunk_index)
            self._stats["loaded_bytes"] += len(chunk_data)
            
            # 保存进度
            self._save_progress()
            
            # 检查是否完成
            if self._is_loading_complete():
                self._finalize_loading()
            
            return True
            
        except Exception as e:
            logger.error(f"加载分片失败 {chunk_index}: {str(e)}")
            self._stats["failed_chunks"] += 1
            return False
    
    def resume_loading(self) -> Tuple[bool, List[int]]:
        """恢复加载任务
        
        Returns:
            Tuple[bool, List[int]]: (是否成功恢复, 待加载的分片索引列表)
        """
        try:
            # 加载进度文件
            progress_path = self.save_dir / 'loading_progress.json'
            if not progress_path.exists():
                logger.error("未找到进度文件")
                return False, []
            
            # 读取进度
            with open(progress_path, 'r') as f:
                progress = json.load(f)
            
            # 恢复任务状态
            self._current_task = progress['task']
            self._loaded_chunks = progress['loaded_chunks']
            self._verified_chunks = progress['verified_chunks']
            self._stats = progress['stats']
            
            # 计算待加载分片
            all_chunks = set(range(self._current_task['total_chunks']))
            remaining_chunks = list(all_chunks - set(self._verified_chunks))
            
            logger.info(f"已恢复加载进度: {len(self._verified_chunks)}/{self._current_task['total_chunks']} 分片")
            return True, remaining_chunks
            
        except Exception as e:
            logger.error(f"恢复加载任务失败: {str(e)}")
            return False, []
    
    def get_progress(self) -> Dict:
        """获取加载进度
        
        Returns:
            Dict: 进度信息
        """
        if not self._current_task:
            return {}
            
        total_chunks = self._current_task['total_chunks']
        loaded_chunks = len(self._verified_chunks)
        
        return {
            'total_size': self._current_task['total_size'],
            'loaded_size': self._stats['loaded_bytes'],
            'progress': loaded_chunks / total_chunks if total_chunks > 0 else 0,
            'failed_chunks': self._stats['failed_chunks'],
            'retry_count': self._stats['retry_count'],
            'elapsed_time': time.time() - self._current_task['start_time']
        }
    
    def _verify_chunk(self, chunk_index: int, chunk_data: bytes) -> bool:
        """验证数据分片
        
        Args:
            chunk_index: 分片索引
            chunk_data: 分片数据
            
        Returns:
            bool: 是否验证通过
        """
        # 验证分片大小
        expected_size = min(
            self.chunk_size,
            self._current_task['total_size'] - chunk_index * self.chunk_size
        )
        if len(chunk_data) != expected_size:
            logger.error(f"分片大小不匹配: {len(chunk_data)} != {expected_size}")
            return False
        
        # 计算分片校验和
        chunk_checksum = hashlib.sha256(chunk_data).hexdigest()
        
        # 保存分片校验和
        checksums_path = self.save_dir / 'chunk_checksums.json'
        checksums = {}
        if checksums_path.exists():
            with open(checksums_path, 'r') as f:
                checksums = json.load(f)
        
        checksums[str(chunk_index)] = chunk_checksum
        
        with open(checksums_path, 'w') as f:
            json.dump(checksums, f)
        
        return True
    
    def _save_progress(self):
        """保存加载进度"""
        if not self._current_task:
            return
            
        progress = {
            'task': self._current_task,
            'loaded_chunks': self._loaded_chunks,
            'verified_chunks': self._verified_chunks,
            'stats': self._stats
        }
        
        progress_path = self.save_dir / 'loading_progress.json'
        with open(progress_path, 'w') as f:
            json.dump(progress, f)
    
    def _is_loading_complete(self) -> bool:
        """检查是否完成加载
        
        Returns:
            bool: 是否完成
        """
        if not self._current_task:
            return False
            
        return len(self._verified_chunks) == self._current_task['total_chunks']
    
    def _finalize_loading(self):
        """完成加载任务"""
        if not self._current_task:
            return
            
        try:
            # 合并所有分片
            output_path = Path(self._current_task['model_path'])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as outfile:
                for i in range(self._current_task['total_chunks']):
                    chunk_path = self._get_chunk_path(i)
                    with open(chunk_path, 'rb') as infile:
                        outfile.write(infile.read())
            
            # 验证完整性
            if self._current_task['expected_checksum']:
                with open(output_path, 'rb') as f:
                    final_checksum = hashlib.sha256(f.read()).hexdigest()
                if final_checksum != self._current_task['expected_checksum']:
                    raise ValueError("最终校验和不匹配")
            
            # 清理临时文件
            self._cleanup()
            
            logger.info(f"加载任务完成: {output_path}")
            
        except Exception as e:
            logger.error(f"完成加载任务失败: {str(e)}")
            raise
    
    def _get_chunk_path(self, chunk_index: int) -> Path:
        """获取分片文件路径
        
        Args:
            chunk_index: 分片索引
            
        Returns:
            Path: 分片文件路径
        """
        return self.save_dir / f"chunk_{chunk_index:06d}.bin"
    
    def _cleanup(self):
        """清理临时文件"""
        try:
            # 删除所有分片文件
            for chunk_index in range(self._current_task['total_chunks']):
                chunk_path = self._get_chunk_path(chunk_index)
                if chunk_path.exists():
                    chunk_path.unlink()
            
            # 删除进度文件
            progress_path = self.save_dir / 'loading_progress.json'
            if progress_path.exists():
                progress_path.unlink()
            
            # 删除校验和文件
            checksums_path = self.save_dir / 'chunk_checksums.json'
            if checksums_path.exists():
                checksums_path.unlink()
            
            logger.info("已清理临时文件")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    def __del__(self):
        """清理资源"""
        try:
            if self._current_task:
                self._cleanup()
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}") 