"""模型分片管理模块

此模块负责处理大型模型文件的分片策略，包括：
1. 模型文件分片
2. 分片合并
3. 分片验证
4. 并行加载优化
"""

import os
import math
import hashlib
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger

from src.utils.device_manager import HybridDevice
from src.utils.memory_manager import MemoryManager

class ModelSharding:
    """模型分片管理类"""
    
    def __init__(self, 
                 base_path: str = "models",
                 default_shard_size: int = 2 * 1024 * 1024 * 1024):  # 默认2GB
        """初始化模型分片管理器
        
        Args:
            base_path: 模型存储基础路径
            default_shard_size: 默认分片大小（字节）
        """
        self.base_path = Path(base_path)
        self.default_shard_size = default_shard_size
        self.device_manager = HybridDevice()
        self.memory_manager = MemoryManager()
        
        # 确保基础路径存在
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def split_model(self,
                         model_path: str,
                         shard_size: Optional[int] = None,
                         verify: bool = True) -> List[str]:
        """异步分片模型文件
        
        Args:
            model_path: 模型文件路径
            shard_size: 分片大小（字节），None则使用默认值
            verify: 是否验证分片完整性
            
        Returns:
            List[str]: 分片文件路径列表
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        # 确定分片大小
        shard_size = shard_size or self.default_shard_size
        
        # 计算分片数量
        total_size = model_path.stat().st_size
        num_shards = math.ceil(total_size / shard_size)
        
        # 创建分片目录
        shard_dir = model_path.parent / f"{model_path.stem}_shards"
        shard_dir.mkdir(exist_ok=True)
        
        # 异步分片处理
        shard_paths = []
        checksums = []
        
        async with aiofiles.open(model_path, 'rb') as f:
            for i in range(num_shards):
                shard_path = shard_dir / f"{model_path.stem}_part_{i:03d}.bin"
                shard_paths.append(str(shard_path))
                
                # 读取分片数据
                chunk = await f.read(shard_size)
                
                # 计算分片校验和
                if verify:
                    checksums.append(hashlib.sha256(chunk).hexdigest())
                
                # 写入分片文件
                async with aiofiles.open(shard_path, 'wb') as sf:
                    await sf.write(chunk)
        
        # 保存校验和信息
        if verify:
            checksum_file = shard_dir / f"{model_path.stem}_checksums.txt"
            async with aiofiles.open(checksum_file, 'w') as f:
                await f.write('\n'.join(checksums))
        
        logger.info(f"模型 {model_path.name} 已分片为 {num_shards} 个文件")
        return shard_paths
    
    async def merge_shards(self,
                          shard_dir: str,
                          output_path: Optional[str] = None,
                          verify: bool = True) -> str:
        """异步合并模型分片
        
        Args:
            shard_dir: 分片目录路径
            output_path: 输出文件路径，None则使用原始文件名
            verify: 是否验证分片完整性
            
        Returns:
            str: 合并后的文件路径
        """
        shard_dir = Path(shard_dir)
        if not shard_dir.exists():
            raise FileNotFoundError(f"分片目录不存在: {shard_dir}")
        
        # 获取所有分片文件
        shard_files = sorted(shard_dir.glob("*_part_*.bin"))
        if not shard_files:
            raise FileNotFoundError(f"未找到分片文件: {shard_dir}")
        
        # 确定输出路径
        if output_path is None:
            base_name = shard_files[0].name.split("_part_")[0]
            output_path = shard_dir.parent / f"{base_name}.model"
        else:
            output_path = Path(output_path)
        
        # 验证分片完整性
        if verify:
            await self._verify_shards(shard_dir)
        
        # 合并分片
        async with aiofiles.open(output_path, 'wb') as outfile:
            for shard in shard_files:
                async with aiofiles.open(shard, 'rb') as infile:
                    while True:
                        chunk = await infile.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        await outfile.write(chunk)
        
        logger.info(f"分片已合并到: {output_path}")
        return str(output_path)
    
    async def _verify_shards(self, shard_dir: Path) -> bool:
        """验证分片完整性
        
        Args:
            shard_dir: 分片目录路径
            
        Returns:
            bool: 验证是否通过
        """
        checksum_file = next(shard_dir.glob("*_checksums.txt"), None)
        if not checksum_file:
            raise FileNotFoundError(f"未找到校验和文件: {shard_dir}")
        
        # 读取原始校验和
        async with aiofiles.open(checksum_file, 'r') as f:
            original_checksums = (await f.read()).splitlines()
        
        # 验证每个分片
        shard_files = sorted(shard_dir.glob("*_part_*.bin"))
        if len(shard_files) != len(original_checksums):
            raise ValueError("分片文件数量与校验和不匹配")
        
        for shard, original_checksum in zip(shard_files, original_checksums):
            async with aiofiles.open(shard, 'rb') as f:
                content = await f.read()
                current_checksum = hashlib.sha256(content).hexdigest()
                if current_checksum != original_checksum:
                    raise ValueError(f"分片校验失败: {shard.name}")
        
        return True
    
    async def load_sharded_model(self,
                               model_dir: str,
                               load_fn: callable,
                               **kwargs) -> any:
        """异步加载分片模型
        
        Args:
            model_dir: 模型目录路径
            load_fn: 模型加载函数
            **kwargs: 传递给加载函数的参数
            
        Returns:
            any: 加载的模型对象
        """
        # 检查内存是否足够
        total_size = sum(f.stat().st_size for f in Path(model_dir).glob("*_part_*.bin"))
        if not self.memory_manager.check_system_memory(total_size):
            raise MemoryError("系统内存不足以加载模型")
        
        # 合并分片
        model_path = await self.merge_shards(model_dir)
        
        try:
            # 加载模型
            model = await asyncio.get_event_loop().run_in_executor(
                None, load_fn, model_path, **kwargs
            )
            return model
            
        finally:
            # 清理合并的临时文件
            try:
                os.remove(model_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
    
    def get_shard_info(self, model_path: str) -> Dict:
        """获取模型分片信息
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict: 分片信息
        """
        model_path = Path(model_path)
        shard_dir = model_path.parent / f"{model_path.stem}_shards"
        
        if not shard_dir.exists():
            return {"status": "not_sharded"}
        
        shard_files = list(shard_dir.glob("*_part_*.bin"))
        total_size = sum(f.stat().st_size for f in shard_files)
        
        return {
            "status": "sharded",
            "num_shards": len(shard_files),
            "total_size": total_size,
            "shard_dir": str(shard_dir),
            "shards": [str(f) for f in shard_files]
        }
    
    def cleanup_shards(self, model_path: str):
        """清理模型分片文件
        
        Args:
            model_path: 模型文件路径
        """
        model_path = Path(model_path)
        shard_dir = model_path.parent / f"{model_path.stem}_shards"
        
        if shard_dir.exists():
            for f in shard_dir.glob("*"):
                try:
                    f.unlink()
                except Exception as e:
                    logger.warning(f"删除分片文件失败: {e}")
            
            try:
                shard_dir.rmdir()
            except Exception as e:
                logger.warning(f"删除分片目录失败: {e}") 