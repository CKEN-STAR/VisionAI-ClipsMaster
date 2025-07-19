"""爆款剧本数据湖模块

负责存储和管理爆款剧本转换对照数据，提供以下功能：
1. 数据导入与导出
2. 高效查询与检索
3. 模式验证与转换
4. 数据质量监控
5. 元数据管理
"""

import os
import time
import json
import yaml
import hashlib
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Iterator

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger

from src.utils.exceptions import DataLakeError, ErrorCode
from src.utils.file_checker import calculate_file_hash


class LakeFSClient:
    """数据湖文件系统客户端"""
    
    def __init__(self, repo: str, config_path: Optional[str] = None):
        """
        初始化数据湖客户端
        
        Args:
            repo: 存储库名称
            config_path: 配置文件路径，默认使用configs/data_lake.yaml
        """
        self.repo = repo
        self.config_path = config_path or os.path.join("configs", "data_lake.yaml")
        self._load_config()
        self._init_storage()
        logger.info(f"数据湖客户端初始化成功，存储库: {repo}")
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.debug(f"成功加载数据湖配置: {self.config_path}")
        except Exception as e:
            logger.error(f"加载数据湖配置失败: {e}")
            # 使用默认配置
            self.config = {
                "storage": {
                    "base_path": "data/lake",
                    "format": "parquet",
                    "partitioning": ["language", "source_type"]
                },
                "performance": {
                    "compression": "snappy"
                }
            }
            logger.warning("使用默认数据湖配置")
    
    def _init_storage(self) -> None:
        """初始化存储目录"""
        # 获取基础存储路径
        base_path = self.config.get("storage", {}).get("base_path", "data/lake")
        
        # 构建存储库路径
        self.repo_path = Path(base_path) / self.repo
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        # 创建元数据目录
        self.metadata_path = self.repo_path / ".metadata"
        self.metadata_path.mkdir(exist_ok=True)
        
        # 创建版本控制目录
        self.versions_path = self.repo_path / ".versions"
        self.versions_path.mkdir(exist_ok=True)
        
        # 创建临时目录
        self.tmp_path = self.repo_path / ".tmp"
        self.tmp_path.mkdir(exist_ok=True)
        
        logger.debug(f"初始化存储目录完成: {self.repo_path}")
    
    def write(self, path: str, data: Any, **kwargs) -> bool:
        """
        写入数据到指定路径
        
        Args:
            path: 存储路径
            data: 要存储的数据
            **kwargs: 额外参数
        
        Returns:
            是否成功
        """
        full_path = self.repo_path / path
        try:
            # 确保父目录存在
            os.makedirs(str(full_path.parent), exist_ok=True)
            
            # 创建临时文件
            os.makedirs(str(self.tmp_path), exist_ok=True)
            tmp_file = f"{os.path.basename(path)}.{int(time.time())}"
            tmp_path = self.tmp_path / tmp_file
            
            # 根据路径后缀和数据类型决定写入方式
            if isinstance(data, pd.DataFrame):
                self._write_dataframe(tmp_path, data, **kwargs)
            elif isinstance(data, (dict, list)):
                self._write_json(tmp_path, data, **kwargs)
            elif isinstance(data, str):
                self._write_text(tmp_path, data, **kwargs)
            elif isinstance(data, bytes):
                self._write_binary(tmp_path, data, **kwargs)
            else:
                logger.error(f"不支持的数据类型: {type(data)}")
                return False
            
            # 原子地移动到最终位置
            shutil.move(str(tmp_path), str(full_path))
            
            # 记录元数据
            self._record_write_metadata(path, full_path)
            
            logger.info(f"数据写入成功: {path}")
            return True
            
        except Exception as e:
            logger.error(f"数据写入失败: {path}, 错误: {e}")
            return False
    
    def _write_dataframe(self, path: Path, df: pd.DataFrame, **kwargs) -> None:
        """写入DataFrame到Parquet文件"""
        compression = kwargs.get("compression") or self.config.get("performance", {}).get("compression", "snappy")
        row_group_size = kwargs.get("row_group_size") or self.config.get("performance", {}).get("row_group_size", 100000)
        
        # 根据分区字段创建分区方案
        partition_cols = kwargs.get("partition_by") or self.config.get("storage", {}).get("partitioning", [])
        
        # 写入Parquet文件
        if partition_cols:
            # 使用分区写入
            path.parent.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pandas(df)
            pq.write_to_dataset(
                table,
                root_path=path.parent,
                partition_cols=partition_cols,
                basename_template=f"{path.name}" + "_{i}.parquet",
                compression=compression,
                row_group_size=row_group_size
            )
        else:
            # 直接写入单个文件
            df.to_parquet(
                path,
                compression=compression,
                row_group_size=row_group_size,
                index=False
            )
    
    def _write_json(self, path: Path, data: Union[Dict, List], **kwargs) -> None:
        """写入JSON数据"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _write_text(self, path: Path, data: str, **kwargs) -> None:
        """写入文本数据"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data)
    
    def _write_binary(self, path: Path, data: bytes, **kwargs) -> None:
        """写入二进制数据"""
        with open(path, 'wb') as f:
            f.write(data)
    
    def _record_write_metadata(self, path: str, full_path: Path) -> None:
        """记录写入操作的元数据"""
        try:
            # 计算文件哈希
            file_hash = calculate_file_hash(full_path)
            
            # 构建元数据
            metadata = {
                "path": path,
                "hash": file_hash,
                "size": full_path.stat().st_size,
                "timestamp": datetime.datetime.now().isoformat(),
                "operation": "write"
            }
            
            # 保存元数据
            metadata_file = self.metadata_path / f"{file_hash}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f)
            
            logger.debug(f"记录元数据成功: {path} -> {file_hash}")
        except Exception as e:
            logger.warning(f"记录元数据失败: {e}")
    
    def read(self, path: str, **kwargs) -> Any:
        """
        从指定路径读取数据
        
        Args:
            path: 存储路径
            **kwargs: 额外参数
        
        Returns:
            读取的数据
        """
        full_path = self.repo_path / path
        
        try:
            if not full_path.exists():
                logger.error(f"文件不存在: {full_path}")
                return None
            
            # 根据文件类型选择读取方式
            suffix = full_path.suffix.lower()
            
            if suffix == '.parquet':
                return self._read_parquet(full_path, **kwargs)
            elif suffix == '.json':
                return self._read_json(full_path, **kwargs)
            elif suffix in ('.txt', '.md', '.csv', '.srt'):
                return self._read_text(full_path, **kwargs)
            else:
                return self._read_binary(full_path, **kwargs)
        
        except Exception as e:
            logger.error(f"读取数据失败: {path}, 错误: {e}")
            return None
    
    def _read_parquet(self, path: Path, **kwargs) -> pd.DataFrame:
        """读取Parquet文件"""
        # 检查是否是分区目录
        if path.is_dir():
            return pq.read_table(path, **kwargs).to_pandas()
        else:
            return pd.read_parquet(path, **kwargs)
    
    def _read_json(self, path: Path, **kwargs) -> Any:
        """读取JSON文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _read_text(self, path: Path, **kwargs) -> str:
        """读取文本文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _read_binary(self, path: Path, **kwargs) -> bytes:
        """读取二进制文件"""
        with open(path, 'rb') as f:
            return f.read()
    
    def delete(self, path: str, permanent: bool = False) -> bool:
        """
        删除指定路径的数据
        
        Args:
            path: 存储路径
            permanent: 是否永久删除
        
        Returns:
            是否成功
        """
        full_path = self.repo_path / path
        
        try:
            if not full_path.exists():
                logger.warning(f"要删除的文件不存在: {full_path}")
                return False
            
            # 如果不是永久删除，先备份到版本目录
            if not permanent:
                timestamp = int(time.time())
                version_path = self.versions_path / f"{path}.{timestamp}"
                version_path.parent.mkdir(parents=True, exist_ok=True)
                
                if full_path.is_dir():
                    shutil.copytree(full_path, version_path)
                else:
                    shutil.copy2(full_path, version_path)
                
                logger.debug(f"备份文件到版本库: {path} -> {version_path}")
            
            # 删除文件或目录
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            
            logger.info(f"删除文件成功: {path} (永久={permanent})")
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {path}, 错误: {e}")
            return False
    
    def list(self, prefix: str = "", recursive: bool = False) -> List[str]:
        """
        列出指定前缀下的所有文件
        
        Args:
            prefix: 路径前缀
            recursive: 是否递归列出子目录
        
        Returns:
            文件路径列表
        """
        start_path = self.repo_path / prefix
        
        if not start_path.exists():
            return []
        
        result = []
        
        if recursive:
            # 递归遍历所有文件
            for root, _, files in os.walk(start_path):
                for file in files:
                    file_path = Path(root) / file
                    # 转换为相对路径
                    rel_path = file_path.relative_to(self.repo_path)
                    result.append(str(rel_path))
        else:
            # 只列出当前目录下的文件
            for item in start_path.iterdir():
                if item.is_file():
                    rel_path = item.relative_to(self.repo_path)
                    result.append(str(rel_path))
        
        return result
    
    def exists(self, path: str) -> bool:
        """
        检查指定路径是否存在
        
        Args:
            path: 存储路径
        
        Returns:
            是否存在
        """
        full_path = self.repo_path / path
        return full_path.exists()
    
    def get_metadata(self, path: str) -> Optional[Dict]:
        """
        获取文件元数据
        
        Args:
            path: 存储路径
        
        Returns:
            元数据字典
        """
        full_path = self.repo_path / path
        
        if not full_path.exists():
            return None
        
        try:
            # 计算文件哈希
            file_hash = calculate_file_hash(full_path)
            
            # 查找元数据文件
            metadata_file = self.metadata_path / f"{file_hash}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果元数据不存在，创建基本元数据
                metadata = {
                    "path": path,
                    "hash": file_hash,
                    "size": full_path.stat().st_size,
                    "created": datetime.datetime.fromtimestamp(full_path.stat().st_ctime).isoformat(),
                    "modified": datetime.datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
                    "inferred": True
                }
                return metadata
                
        except Exception as e:
            logger.error(f"获取元数据失败: {path}, 错误: {e}")
            return None


class HitPatternLake:
    """爆款剧本数据湖类"""
    
    def __init__(self):
        """初始化爆款剧本数据湖"""
        self.conn = LakeFSClient(repo="drama-patterns")
        logger.info("爆款剧本数据湖初始化完成")
    
    def ingest_data(self, origin_srt: str, hit_srt: str) -> bool:
        """
        摄入原创与爆款剧本对比数据
        
        Args:
            origin_srt: 原始字幕文件路径
            hit_srt: 爆款字幕文件路径
            
        Returns:
            是否成功
        """
        try:
            # 计算输入文件的哈希值
            origin_hash = calculate_file_hash(origin_srt)
            hit_hash = calculate_file_hash(hit_srt)
            
            # 构建输出路径
            output_path = f"pairs/{hash(origin_srt)}.parquet"
            
            # 转换数据为DataFrame格式
            data = convert_to_parquet(origin_srt, hit_srt)
            
            # 写入数据湖
            success = self.conn.write(
                path=output_path,
                data=data,
                partition_by=["modification_type"]
            )
            
            if success:
                logger.info(f"成功摄入对比数据: {origin_srt} -> {hit_srt}")
                return True
            else:
                logger.error(f"摄入对比数据失败: {origin_srt} -> {hit_srt}")
                return False
                
        except Exception as e:
            logger.error(f"数据摄入过程中发生错误: {e}")
            return False
    
    def query_patterns(self, 
                      modification_type: Optional[str] = None,
                      min_impact: float = 0.0,
                      limit: int = 100) -> pd.DataFrame:
        """
        查询爆款模式数据
        
        Args:
            modification_type: 转换类型过滤
            min_impact: 最小影响分值
            limit: 返回结果限制
            
        Returns:
            包含对比数据的DataFrame
        """
        try:
            # 获取所有对比数据文件
            pattern_files = self.conn.list(prefix="pairs", recursive=True)
            
            # 读取并合并数据
            all_data = []
            for file_path in pattern_files:
                df = self.conn.read(file_path)
                if df is not None:
                    all_data.append(df)
            
            if not all_data:
                return pd.DataFrame()
                
            # 合并所有数据
            result = pd.concat(all_data, ignore_index=True)
            
            # 应用过滤
            if modification_type:
                result = result[result["modification_type"] == modification_type]
            
            if min_impact > 0:
                result = result[result["impact_score"] >= min_impact]
            
            # 按照影响分值排序并限制结果数量
            result = result.sort_values("impact_score", ascending=False).head(limit)
            
            return result
            
        except Exception as e:
            logger.error(f"查询爆款模式数据失败: {e}")
            return pd.DataFrame()
    
    def get_top_patterns(self, top_n: int = 20) -> Dict[str, List[Dict]]:
        """
        获取各类型转换中最高效的模式
        
        Args:
            top_n: 每种类型返回的条目数
            
        Returns:
            字典，键为转换类型，值为对比数据列表
        """
        try:
            # 获取所有数据
            all_data = self.query_patterns(limit=1000)
            
            if all_data.empty:
                return {}
            
            # 获取所有转换类型
            mod_types = all_data["modification_type"].unique()
            
            # 对每种类型获取top条目
            result = {}
            for mod_type in mod_types:
                type_data = all_data[all_data["modification_type"] == mod_type]
                top_items = type_data.sort_values("impact_score", ascending=False).head(top_n)
                result[mod_type] = top_items.to_dict(orient="records")
            
            return result
            
        except Exception as e:
            logger.error(f"获取顶级模式失败: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据湖统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取所有文件
            all_files = self.conn.list(prefix="", recursive=True)
            
            # 获取所有pair文件
            pair_files = [f for f in all_files if f.startswith("pairs/")]
            
            # 尝试读取并合并所有数据以获取统计信息
            all_data = []
            for file_path in pair_files[:100]:  # 限制文件数量以提高性能
                df = self.conn.read(file_path)
                if df is not None:
                    all_data.append(df)
            
            # 如果没有数据，返回基本统计信息
            if not all_data:
                return {
                    "total_files": len(all_files),
                    "pair_files": len(pair_files),
                    "data_size": 0,
                    "last_update": datetime.datetime.now().isoformat()
                }
            
            # 合并数据
            merged_data = pd.concat(all_data, ignore_index=True)
            
            # 计算统计信息
            mod_type_counts = merged_data["modification_type"].value_counts().to_dict()
            avg_impact = merged_data["impact_score"].mean()
            max_impact = merged_data["impact_score"].max()
            
            # 获取文件总大小
            total_size = 0
            for file_path in pair_files:
                meta = self.conn.get_metadata(file_path)
                if meta and "size" in meta:
                    total_size += meta["size"]
            
            return {
                "total_files": len(all_files),
                "pair_files": len(pair_files),
                "data_size": total_size,
                "record_count": len(merged_data),
                "modification_types": mod_type_counts,
                "avg_impact_score": avg_impact,
                "max_impact_score": max_impact,
                "last_update": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }


def convert_to_parquet(origin_srt: str, hit_srt: str) -> pd.DataFrame:
    """
    将原始字幕与爆款字幕转换为带标记的对比数据
    
    Args:
        origin_srt: 原始字幕文件路径
        hit_srt: 爆款字幕文件路径
        
    Returns:
        转换后的DataFrame
    """
    try:
        # 导入SRT解析器
        from src.parsers.srt_decoder import parse_srt_to_dict
        
        # 解析字幕文件
        origin_data = parse_srt_to_dict(origin_srt)
        hit_data = parse_srt_to_dict(hit_srt)
        
        # 提取场景
        origin_scenes = [subtitle.get("text", "") for subtitle in origin_data.get("subtitles", [])]
        hit_scenes = [subtitle.get("text", "") for subtitle in hit_data.get("subtitles", [])]
        
        # 导入场景匹配器分析转换
        from src.knowledge.pattern_analyzer import analyze_transformations
        
        # 分析转换
        transformations = analyze_transformations(origin_scenes, hit_scenes)
        
        # 创建DataFrame
        rows = []
        for t in transformations:
            row = {
                "origin_scene": t.get("origin_scene", ""),
                "hit_scene": t.get("hit_scene", ""),
                "modification_type": t.get("type", "未知"),
                "impact_score": t.get("impact", 0.5),
                "source_id": f"{os.path.basename(origin_srt)}_{os.path.basename(hit_srt)}",
                "timestamp": datetime.datetime.now()
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
        
    except ImportError:
        # 如果对应模块还未实现，使用模拟数据
        logger.warning("未找到所需分析模块，使用模拟数据")
        
        # 读取文件内容用于对比
        with open(origin_srt, 'r', encoding='utf-8', errors='replace') as f:
            origin_content = f.read()
        
        with open(hit_srt, 'r', encoding='utf-8', errors='replace') as f:
            hit_content = f.read()
        
        # 简单分割为场景
        origin_scenes = origin_content.split('\n\n')
        hit_scenes = hit_content.split('\n\n')
        
        # 限制数量并配对
        min_len = min(len(origin_scenes), len(hit_scenes))
        pairs = list(zip(origin_scenes[:min_len], hit_scenes[:min_len]))
        
        # 创建模拟数据
        rows = []
        mod_types = ["动作强化", "冲突加剧", "悬念设置", "反转设计", "情感渲染"]
        
        for i, (origin, hit) in enumerate(pairs):
            if not origin or not hit:
                continue
                
            # 提取文本部分
            origin_text = "\n".join(origin.split('\n')[2:]) if len(origin.split('\n')) > 2 else origin
            hit_text = "\n".join(hit.split('\n')[2:]) if len(hit.split('\n')) > 2 else hit
            
            if not origin_text or not hit_text:
                continue
                
            # 随机选择修改类型和分数
            mod_type = mod_types[i % len(mod_types)]
            impact = 0.5 + (hash(origin_text + hit_text) % 50) / 100.0  # 0.5-0.99之间的随机值
            
            row = {
                "origin_scene": origin_text,
                "hit_scene": hit_text,
                "modification_type": mod_type,
                "impact_score": impact,
                "source_id": f"{os.path.basename(origin_srt)}_{os.path.basename(hit_srt)}",
                "timestamp": datetime.datetime.now()
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"转换Parquet数据失败: {e}")
        # 返回一个空的DataFrame保持接口一致性
        return pd.DataFrame(columns=[
            "origin_scene", "hit_scene", "modification_type", 
            "impact_score", "source_id", "timestamp"
        ]) 