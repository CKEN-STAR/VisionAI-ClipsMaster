"""模型分片切割器

此模块提供了智能模型分片功能，可以根据不同策略将大型模型切分为多个分片：
1. 基于模型层依赖关系的智能分片
2. 基于内存优化的平衡分片
3. 支持多种分片策略和硬件适配
4. 集成分片策略配置中心
"""

import os
import sys
import time
import json
import math
import torch
import hashlib
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Set, Callable
from loguru import logger

from src.core.shard_policy_manager import ShardPolicyManager
from src.core.model_sharding import ModelSharding
from src.utils.memory_manager import MemoryManager
from src.utils.device_manager import HybridDevice
from src.sharding.layer_analyzer import LayerAnalyzer


class ModelSplitter:
    """模型分片切割器"""
    
    def __init__(self, 
                 policy_manager: Optional[ShardPolicyManager] = None,
                 model_sharding: Optional[ModelSharding] = None,
                 working_dir: str = "models"):
        """初始化模型分片切割器
        
        Args:
            policy_manager: 分片策略管理器
            model_sharding: 模型分片管理类
            working_dir: 工作目录
        """
        self.policy_manager = policy_manager or ShardPolicyManager()
        self.model_sharding = model_sharding or ModelSharding()
        self.memory_manager = MemoryManager()
        self.device_manager = HybridDevice()
        self.working_dir = Path(working_dir)
        self.layer_analyzer = LayerAnalyzer()
        
        # 确保工作目录存在
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
    def split_model(self, 
                   model_path: str, 
                   model_name: Optional[str] = None,
                   strategy: Optional[str] = None,
                   output_dir: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Dict:
        """切分模型为多个分片
        
        Args:
            model_path: 模型文件路径
            model_name: 模型名称（如果为None，则从文件名提取）
            strategy: 使用的分片策略（如果为None，则自动选择）
            output_dir: 输出目录（如果为None，则使用默认目录）
            metadata: 额外的元数据
            
        Returns:
            Dict: 分片结果信息
        """
        # 解析路径和模型名称
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        model_name = model_name or model_path.stem
        output_dir = Path(output_dir) if output_dir else self.working_dir / f"{model_name}_shards"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 选择分片策略
        if strategy:
            strategy_name = strategy
        else:
            strategy_name = self.policy_manager.select_strategy_for_model(model_name)
        
        strategy_config = self.policy_manager._get_strategy_by_name(strategy_name)
        
        # 获取模型大小
        model_size = model_path.stat().st_size
        model_size_mb = model_size / (1024 * 1024)
        
        # 生成分片计划
        shard_plan = self.policy_manager.generate_sharding_plan(model_name, model_size)
        
        logger.info(f"为模型 {model_name} ({model_size_mb:.2f}MB) 应用 {strategy_name} 分片策略")
        logger.info(f"计划分片数: {shard_plan['num_shards']}, 每片大小: {shard_plan['shard_size_mb']:.2f}MB")
        
        # 根据不同的分片方式处理
        if strategy_config["layer_grouping"] == "isolated" or strategy_config["layer_grouping"] == "minimal":
            # 简单物理分片
            return self._split_model_by_size(model_path, output_dir, shard_plan, metadata)
        else:
            # 智能层级分片
            return self._split_model_by_layers(model_path, output_dir, shard_plan, metadata)
            
    def _split_model_by_size(self, 
                           model_path: Path, 
                           output_dir: Path, 
                           shard_plan: Dict,
                           metadata: Optional[Dict] = None) -> Dict:
        """按大小对模型进行简单物理分片
        
        Args:
            model_path: 模型文件路径
            output_dir: 输出目录
            shard_plan: 分片计划
            metadata: 额外的元数据
            
        Returns:
            Dict: 分片结果信息
        """
        start_time = time.time()
        model_size = model_path.stat().st_size
        num_shards = shard_plan["num_shards"]
        shard_size_bytes = math.ceil(model_size / num_shards)
        
        # 创建分片
        shard_paths = []
        checksums = []
        
        with open(model_path, 'rb') as f:
            for i in range(num_shards):
                shard_path = output_dir / f"model_part_{i:03d}.bin"
                shard_paths.append(str(shard_path))
                
                # 读取分片数据
                chunk = f.read(shard_size_bytes)
                
                # 计算校验和
                checksums.append(hashlib.sha256(chunk).hexdigest())
                
                # 写入分片文件
                with open(shard_path, 'wb') as sf:
                    sf.write(chunk)
                
                logger.info(f"已创建分片 {i+1}/{num_shards}: {shard_path.name} ({len(chunk)/1024/1024:.2f}MB)")
        
        # 保存校验和信息
        checksum_file = output_dir / "checksums.json"
        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump({
                "model_name": shard_plan["model_name"],
                "model_size": model_size,
                "num_shards": num_shards,
                "strategy": shard_plan["strategy"],
                "checksums": checksums,
                "metadata": metadata or {}
            }, f, indent=2)
        
        # 保存分片信息
        info_file = output_dir / "shard_info.json"
        info = {
            "model_name": shard_plan["model_name"],
            "original_path": str(model_path),
            "model_size_bytes": model_size,
            "model_size_mb": model_size / (1024 * 1024),
            "strategy": shard_plan["strategy"],
            "strategy_type": "physical",
            "num_shards": num_shards,
            "shard_size_bytes": shard_size_bytes,
            "shard_size_mb": shard_size_bytes / (1024 * 1024),
            "shard_paths": shard_paths,
            "checksum_file": str(checksum_file),
            "creation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": time.time() - start_time,
            "metadata": metadata or {}
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
        
        logger.info(f"模型分片完成，共 {num_shards} 个分片，耗时 {info['elapsed_time']:.2f} 秒")
        return info
            
    def _split_model_by_layers(self, 
                             model_path: Path, 
                             output_dir: Path, 
                             shard_plan: Dict,
                             metadata: Optional[Dict] = None) -> Dict:
        """按层结构对模型进行智能分片
        
        Args:
            model_path: 模型文件路径
            output_dir: 输出目录
            shard_plan: 分片计划
            metadata: 额外的元数据
            
        Returns:
            Dict: 分片结果信息
        """
        start_time = time.time()
        
        # 加载模型结构
        try:
            logger.info(f"分析模型层结构: {model_path}")
            model_structure = self.layer_analyzer.analyze_model(model_path)
            logger.info(f"模型分析完成，共 {len(model_structure['layers'])} 个层")
        except Exception as e:
            logger.warning(f"模型层分析失败: {e}，将使用简单物理分片")
            return self._split_model_by_size(model_path, output_dir, shard_plan, metadata)
        
        # 获取层分组信息
        layer_groups = []
        if "layer_grouping" in shard_plan and shard_plan["layer_grouping"]:
            # 使用自定义的层分组
            layer_groups = shard_plan["layer_grouping"]
        else:
            # 根据依赖关系自动分组
            layer_groups = self.layer_analyzer.generate_layer_groups(
                model_structure,
                target_groups=shard_plan["num_shards"]
            )
        
        # 检查层分组数量是否符合预期
        if len(layer_groups) != shard_plan["num_shards"]:
            logger.warning(f"实际层分组数量 ({len(layer_groups)}) 与计划分片数 ({shard_plan['num_shards']}) 不一致")
            
        # 根据层分组切分模型
        num_shards = len(layer_groups)
        shard_paths = []
        checksums = []
        layer_mappings = {}  # 记录每个分片包含的层
        
        logger.info(f"开始按层结构切分模型，共 {num_shards} 个分片")
        
        try:
            # 加载模型
            model = self.layer_analyzer.load_model_for_splitting(model_path)
            
            # 为每个分组创建分片
            for i, group in enumerate(layer_groups):
                shard_path = output_dir / f"model_part_{i:03d}.bin"
                shard_paths.append(str(shard_path))
                
                # 提取该分组的层
                shard_data = self.layer_analyzer.extract_layers(model, group["layers"])
                
                # 保存分片
                with open(shard_path, 'wb') as f:
                    f.write(shard_data)
                
                # 计算校验和
                checksums.append(hashlib.sha256(shard_data).hexdigest())
                
                # 记录层映射
                layer_mappings[f"shard_{i}"] = {
                    "path": str(shard_path),
                    "layers": group["layers"],
                    "size_bytes": len(shard_data),
                    "size_mb": len(shard_data) / (1024 * 1024)
                }
                
                logger.info(f"已创建分片 {i+1}/{num_shards}: {shard_path.name} ({len(shard_data)/1024/1024:.2f}MB)")
                logger.info(f"  包含 {len(group['layers'])} 个层")
        except Exception as e:
            logger.error(f"按层结构分片失败: {e}")
            logger.warning("退回到按大小分片")
            return self._split_model_by_size(model_path, output_dir, shard_plan, metadata)
        
        # 保存校验和信息
        checksum_file = output_dir / "checksums.json"
        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump({
                "model_name": shard_plan["model_name"],
                "strategy": shard_plan["strategy"],
                "checksums": checksums,
                "metadata": metadata or {}
            }, f, indent=2)
        
        # 保存层映射信息
        layers_file = output_dir / "layer_mapping.json"
        with open(layers_file, 'w', encoding='utf-8') as f:
            json.dump(layer_mappings, f, indent=2)
        
        # 保存分片信息
        info_file = output_dir / "shard_info.json"
        info = {
            "model_name": shard_plan["model_name"],
            "original_path": str(model_path),
            "strategy": shard_plan["strategy"],
            "strategy_type": "layerwise",
            "num_shards": num_shards,
            "shard_paths": shard_paths,
            "layer_mapping_file": str(layers_file),
            "checksum_file": str(checksum_file),
            "total_layers": len(model_structure["layers"]),
            "creation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": time.time() - start_time,
            "metadata": metadata or {}
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
        
        logger.info(f"模型分片完成，共 {num_shards} 个分片，耗时 {info['elapsed_time']:.2f} 秒")
        return info
    
    def merge_shards(self, 
                    shard_dir: str, 
                    output_path: Optional[str] = None, 
                    verify: bool = True) -> str:
        """合并模型分片
        
        Args:
            shard_dir: 分片目录
            output_path: 输出文件路径，如果为None则使用原始模型名称
            verify: 是否验证分片完整性
            
        Returns:
            str: 合并后的模型路径
        """
        shard_dir = Path(shard_dir)
        if not shard_dir.exists():
            raise FileNotFoundError(f"分片目录不存在: {shard_dir}")
        
        # 加载分片信息
        info_file = shard_dir / "shard_info.json"
        if not info_file.exists():
            raise FileNotFoundError(f"分片信息文件不存在: {info_file}")
            
        with open(info_file, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        # 确定输出路径
        if output_path is None:
            model_name = info.get("model_name", shard_dir.name.replace("_shards", ""))
            output_path = shard_dir.parent / f"{model_name}.model"
        
        output_path = Path(output_path)
        
        # 检查分片类型
        strategy_type = info.get("strategy_type", "physical")
        
        if strategy_type == "layerwise":
            # 按层合并
            return self._merge_layerwise_shards(shard_dir, output_path, info, verify)
        else:
            # 按物理顺序合并
            return self._merge_physical_shards(shard_dir, output_path, info, verify)
    
    def _merge_physical_shards(self, 
                             shard_dir: Path, 
                             output_path: Path, 
                             info: Dict, 
                             verify: bool) -> str:
        """按物理顺序合并分片
        
        Args:
            shard_dir: 分片目录
            output_path: 输出路径
            info: 分片信息
            verify: 是否验证
            
        Returns:
            str: 合并后的文件路径
        """
        logger.info(f"按物理顺序合并分片到: {output_path}")
        
        # 获取所有分片文件
        shard_paths = info.get("shard_paths", [])
        if not shard_paths:
            # 如果没有指定路径，则按模式查找
            shard_paths = sorted(str(p) for p in shard_dir.glob("model_part_*.bin"))
        
        if not shard_paths:
            raise FileNotFoundError(f"未找到分片文件: {shard_dir}")
        
        # 如果需要验证，检查校验和
        if verify:
            self._verify_shard_checksums(shard_dir, shard_paths)
        
        # 合并分片
        with open(output_path, 'wb') as outfile:
            for shard_path in shard_paths:
                with open(shard_path, 'rb') as infile:
                    while True:
                        chunk = infile.read(8 * 1024 * 1024)  # 8MB 一块
                        if not chunk:
                            break
                        outfile.write(chunk)
                
                logger.info(f"已合并分片: {Path(shard_path).name}")
        
        logger.info(f"模型分片合并完成: {output_path}")
        return str(output_path)
    
    def _merge_layerwise_shards(self, 
                              shard_dir: Path, 
                              output_path: Path, 
                              info: Dict, 
                              verify: bool) -> str:
        """按层结构合并分片
        
        Args:
            shard_dir: 分片目录
            output_path: 输出路径
            info: 分片信息
            verify: 是否验证
            
        Returns:
            str: 合并后的文件路径
        """
        logger.info(f"按层结构合并分片到: {output_path}")
        
        # 验证层映射文件
        layer_mapping_file = info.get("layer_mapping_file")
        if not layer_mapping_file:
            layer_mapping_file = shard_dir / "layer_mapping.json"
            if not layer_mapping_file.exists():
                logger.warning("未找到层映射文件，将按物理顺序合并")
                return self._merge_physical_shards(shard_dir, output_path, info, verify)
        
        # 加载层映射
        with open(layer_mapping_file, 'r', encoding='utf-8') as f:
            layer_mappings = json.load(f)
        
        # 如果需要验证，检查校验和
        if verify:
            shard_paths = [mapping["path"] for mapping in layer_mappings.values()]
            self._verify_shard_checksums(shard_dir, shard_paths)
        
        try:
            # 使用层分析器按层合并
            self.layer_analyzer.merge_model_from_layer_shards(
                layer_mappings, output_path
            )
        except Exception as e:
            logger.error(f"按层结构合并失败: {e}")
            logger.warning("退回到按物理顺序合并")
            return self._merge_physical_shards(shard_dir, output_path, info, verify)
        
        logger.info(f"模型分片按层结构合并完成: {output_path}")
        return str(output_path)
    
    def _verify_shard_checksums(self, shard_dir: Path, shard_paths: List[str]) -> bool:
        """验证分片校验和
        
        Args:
            shard_dir: 分片目录
            shard_paths: 分片路径列表
            
        Returns:
            bool: 验证是否通过
        """
        # 加载校验和信息
        checksum_file = shard_dir / "checksums.json"
        if not checksum_file.exists():
            logger.warning(f"未找到校验和文件: {checksum_file}")
            return False
        
        with open(checksum_file, 'r', encoding='utf-8') as f:
            checksum_info = json.load(f)
        
        original_checksums = checksum_info.get("checksums", [])
        if not original_checksums:
            logger.warning("校验和文件中没有校验和信息")
            return False
        
        # 验证每个分片
        if len(original_checksums) != len(shard_paths):
            logger.warning(f"校验和数量 ({len(original_checksums)}) 与分片数量 ({len(shard_paths)}) 不匹配")
            return False
        
        for shard_path, original_checksum in zip(shard_paths, original_checksums):
            with open(shard_path, 'rb') as f:
                content = f.read()
                current_checksum = hashlib.sha256(content).hexdigest()
                
                if current_checksum != original_checksum:
                    raise ValueError(f"分片校验失败: {Path(shard_path).name}")
        
        logger.info("所有分片校验通过")
        return True
    
    def get_shard_info(self, model_path_or_dir: str) -> Dict:
        """获取模型分片信息
        
        Args:
            model_path_or_dir: 模型路径或分片目录
            
        Returns:
            Dict: 分片信息
        """
        path = Path(model_path_or_dir)
        
        # 如果是目录，检查是否为分片目录
        if path.is_dir():
            info_file = path / "shard_info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"status": "not_sharded_dir"}
        
        # 如果是文件，检查是否有对应的分片目录
        elif path.is_file():
            shard_dir = path.parent / f"{path.stem}_shards"
            if shard_dir.exists():
                info_file = shard_dir / "shard_info.json"
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                        info["status"] = "sharded"
                        info["shard_dir"] = str(shard_dir)
                        return info
                else:
                    return {
                        "status": "sharded",
                        "shard_dir": str(shard_dir),
                        "details": "missing_info_file"
                    }
            else:
                return {"status": "not_sharded_file"}
        
        return {"status": "invalid_path"} 