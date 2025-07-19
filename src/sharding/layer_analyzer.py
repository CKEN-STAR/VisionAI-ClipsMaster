"""模型层分析器

此模块提供分析模型层结构的功能，用于支持智能层级分片：
1. 识别和分析模型内部结构
2. 提取模型层间依赖关系
3. 生成优化的层分组方案
4. 支持不同模型框架（PyTorch、Tensorflow等）
"""

import os
import re
import json
import torch
import numpy as np
import networkx as nx
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple, Union
from loguru import logger

try:
    import safetensors
    from safetensors.torch import load_file, save_file
    HAS_SAFETENSORS = True
except ImportError:
    HAS_SAFETENSORS = False
    logger.warning("safetensors 库未安装，某些模型格式可能无法正确处理")


class LayerAnalyzer:
    """模型层分析器"""
    
    def __init__(self):
        """初始化层分析器"""
        self.model_formats = {
            '.pt': self._analyze_pytorch_model,
            '.pth': self._analyze_pytorch_model,
            '.bin': self._analyze_pytorch_model,
            '.model': self._analyze_pytorch_model,
            '.ckpt': self._analyze_pytorch_model,
            '.safetensors': self._analyze_safetensors_model
        }
        
        # 层名称模式与类型匹配
        self.layer_patterns = {
            r'.*\.embed': 'embedding',
            r'.*\.weight_ih': 'recurrent',
            r'.*\.weight_hh': 'recurrent',
            r'.*\.attention': 'attention',
            r'.*\.self_attn': 'attention',
            r'.*\.attn': 'attention',
            r'.*\.query': 'attention',
            r'.*\.key': 'attention',
            r'.*\.value': 'attention',
            r'.*\.qkv': 'attention',
            r'.*\.ffn': 'ffn',
            r'.*\.mlp': 'ffn',
            r'.*\.fc\d+': 'ffn',
            r'.*\.norm': 'normalization',
            r'.*\.ln_\d+': 'normalization',
            r'.*\.ln': 'normalization',
            r'.*\.LayerNorm': 'normalization',
            r'.*\.head': 'output',
            r'.*\.lm_head': 'output',
            r'.*\.output': 'output',
        }
    
    def analyze_model(self, model_path: Union[str, Path]) -> Dict:
        """分析模型结构
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict: 模型结构分析结果
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        # 根据文件扩展名选择分析方法
        ext = model_path.suffix.lower()
        if ext in self.model_formats:
            analyzer = self.model_formats[ext]
            return analyzer(model_path)
        else:
            # 默认当作PyTorch模型处理
            logger.warning(f"未知模型格式 '{ext}'，将尝试作为PyTorch模型分析")
            return self._analyze_pytorch_model(model_path)
    
    def _analyze_pytorch_model(self, model_path: Path) -> Dict:
        """分析PyTorch模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict: 模型结构分析结果
        """
        try:
            # 加载模型
            logger.info(f"加载PyTorch模型: {model_path}")
            model_data = torch.load(model_path, map_location='cpu')
            
            # 如果模型是OrderedDict或dict格式的状态字典
            if isinstance(model_data, dict):
                state_dict = model_data.get('state_dict', model_data)
                return self._analyze_state_dict(state_dict)
            else:
                logger.warning(f"无法识别的模型格式: {type(model_data)}")
                # 尝试提取state_dict
                if hasattr(model_data, 'state_dict'):
                    return self._analyze_state_dict(model_data.state_dict())
                return {"error": "unsupported_model_format"}
        except Exception as e:
            logger.error(f"分析PyTorch模型出错: {e}")
            return {"error": str(e)}
    
    def _analyze_safetensors_model(self, model_path: Path) -> Dict:
        """分析safetensors模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Dict: 模型结构分析结果
        """
        if not HAS_SAFETENSORS:
            raise ImportError("缺少safetensors库，无法处理safetensors模型")
        
        try:
            # 加载模型
            logger.info(f"加载safetensors模型: {model_path}")
            state_dict = load_file(model_path)
            return self._analyze_state_dict(state_dict)
        except Exception as e:
            logger.error(f"分析safetensors模型出错: {e}")
            return {"error": str(e)}
    
    def _analyze_state_dict(self, state_dict: Dict) -> Dict:
        """分析模型状态字典
        
        Args:
            state_dict: 模型状态字典
            
        Returns:
            Dict: 模型结构分析结果
        """
        # 提取所有层名称
        layer_names = list(state_dict.keys())
        logger.info(f"模型包含 {len(layer_names)} 个参数张量")
        
        # 分析层结构
        layers = []
        layer_types = {}
        layer_sizes = {}
        
        for name, tensor in state_dict.items():
            # 获取张量大小
            if hasattr(tensor, 'shape'):
                size = tensor.shape
                size_bytes = tensor.numel() * tensor.element_size() if hasattr(tensor, 'element_size') else 0
            else:
                size = None
                size_bytes = 0
            
            # 识别层类型
            layer_type = self._identify_layer_type(name)
            
            layer_info = {
                "name": name,
                "type": layer_type,
                "shape": size,
                "size_bytes": size_bytes
            }
            
            layers.append(layer_info)
            layer_types[name] = layer_type
            layer_sizes[name] = size_bytes
        
        # 提取模型结构
        block_pattern = r'(\d+)'
        blocks = {}
        for name in layer_names:
            # 尝试识别层所属的块
            match = re.search(r'block\.(\d+)|layers\.(\d+)|transformer\.h\.(\d+)', name)
            if match:
                block_num = int(next(g for g in match.groups() if g is not None))
                if block_num not in blocks:
                    blocks[block_num] = []
                blocks[block_num].append(name)
        
        # 构建层依赖图
        dependencies = self._extract_dependencies(layer_names, layer_types)
        
        # 统计各类型层的总大小
        type_sizes = {}
        for name, layer_type in layer_types.items():
            if layer_type not in type_sizes:
                type_sizes[layer_type] = 0
            type_sizes[layer_type] += layer_sizes[name]
        
        return {
            "layers": layers,
            "layer_count": len(layers),
            "blocks": blocks,
            "dependencies": dependencies,
            "layer_types": list(set(layer_types.values())),
            "type_sizes": type_sizes
        }
    
    def _identify_layer_type(self, layer_name: str) -> str:
        """识别层类型
        
        Args:
            layer_name: 层名称
            
        Returns:
            str: 层类型
        """
        for pattern, layer_type in self.layer_patterns.items():
            if re.match(pattern, layer_name):
                return layer_type
        
        # 根据命名约定识别
        if any(k in layer_name for k in ["embed", "token", "position"]):
            return "embedding"
        elif any(k in layer_name for k in ["attention", "attn", "query", "key", "value", "qkv", "q_proj", "k_proj", "v_proj"]):
            return "attention"
        elif any(k in layer_name for k in ["ffn", "mlp", "fc", "feed", "linear"]):
            return "ffn"
        elif any(k in layer_name for k in ["norm", "ln", "layer_norm", "batch"]):
            return "normalization"
        elif any(k in layer_name for k in ["head", "output", "predict", "logit"]):
            return "output"
        
        return "other"
    
    def _extract_dependencies(self, layer_names: List[str], layer_types: Dict[str, str]) -> List[Dict]:
        """提取层依赖关系
        
        Args:
            layer_names: 层名称列表
            layer_types: 层类型映射
            
        Returns:
            List[Dict]: 依赖关系列表
        """
        dependencies = []
        
        # 常见的层依赖模式
        # 1. 识别前馈网络(FFN)依赖于注意力层(Attention)
        # 2. 识别LayerNorm依赖于前一层
        # 3. 识别Attention层之间的依赖
        
        # 构建层块映射 (block_1 -> layers in block_1)
        block_layers = {}
        for name in layer_names:
            match = re.search(r'block\.(\d+)|layers\.(\d+)|transformer\.h\.(\d+)', name)
            if match:
                block_num = int(next(g for g in match.groups() if g is not None))
                if block_num not in block_layers:
                    block_layers[block_num] = []
                block_layers[block_num].append(name)
        
        # 为每个块添加层内依赖
        for block_num, layers in block_layers.items():
            # 按层类型分组
            block_layer_types = {}
            for layer in layers:
                layer_type = layer_types.get(layer, "other")
                if layer_type not in block_layer_types:
                    block_layer_types[layer_type] = []
                block_layer_types[layer_type].append(layer)
            
            # 根据常见架构添加依赖
            if "attention" in block_layer_types and "ffn" in block_layer_types:
                for attn_layer in block_layer_types["attention"]:
                    for ffn_layer in block_layer_types["ffn"]:
                        dependencies.append({
                            "from": attn_layer,
                            "to": ffn_layer,
                            "type": "attention_to_ffn"
                        })
            
            # 在同一块内的层级关系
            if "embedding" in block_layer_types and "attention" in block_layer_types:
                for embed_layer in block_layer_types["embedding"]:
                    for attn_layer in block_layer_types["attention"]:
                        dependencies.append({
                            "from": embed_layer,
                            "to": attn_layer,
                            "type": "embedding_to_attention"
                        })
        
        # 添加块间依赖（每个块依赖前一个块的最后一层）
        block_nums = sorted(block_layers.keys())
        for i in range(1, len(block_nums)):
            prev_block = block_nums[i-1]
            curr_block = block_nums[i]
            
            # 前一个块的最后一层（通常是FFN或输出）
            prev_ffn = [l for l in block_layers[prev_block] if layer_types.get(l) == "ffn"]
            curr_attention = [l for l in block_layers[curr_block] if layer_types.get(l) == "attention"]
            
            if prev_ffn and curr_attention:
                for prev_layer in prev_ffn:
                    for curr_layer in curr_attention:
                        dependencies.append({
                            "from": prev_layer,
                            "to": curr_layer,
                            "type": "block_to_block"
                        })
        
        return dependencies
    
    def generate_layer_groups(self, model_structure: Dict, target_groups: int = 2) -> List[Dict]:
        """生成层分组
        
        Args:
            model_structure: 模型结构
            target_groups: 目标分组数量
            
        Returns:
            List[Dict]: 层分组列表
        """
        layers = model_structure["layers"]
        dependencies = model_structure.get("dependencies", [])
        
        # 如果没有依赖关系，按大小平均分组
        if not dependencies:
            return self._group_by_size(layers, target_groups)
        
        # 否则，考虑依赖关系进行分组
        return self._group_by_dependency(layers, dependencies, target_groups)
    
    def _group_by_size(self, layers: List[Dict], target_groups: int) -> List[Dict]:
        """按大小平均分组
        
        Args:
            layers: 层列表
            target_groups: 目标分组数量
            
        Returns:
            List[Dict]: 层分组列表
        """
        # 计算总大小
        total_size = sum(layer.get("size_bytes", 0) for layer in layers)
        target_size = total_size / target_groups
        
        # 按名称排序以确保确定性分组
        sorted_layers = sorted(layers, key=lambda x: x["name"])
        
        groups = []
        current_group = {"layers": [], "size_bytes": 0}
        
        for layer in sorted_layers:
            layer_name = layer["name"]
            layer_size = layer.get("size_bytes", 0)
            
            # 如果当前组接近目标大小，创建新组
            if current_group["size_bytes"] > 0 and current_group["size_bytes"] + layer_size > target_size and len(groups) < target_groups - 1:
                groups.append(current_group)
                current_group = {"layers": [], "size_bytes": 0}
            
            # 添加层到当前组
            current_group["layers"].append(layer_name)
            current_group["size_bytes"] += layer_size
        
        # 添加最后一个组
        if current_group["layers"]:
            groups.append(current_group)
        
        return groups
    
    def _group_by_dependency(self, layers: List[Dict], dependencies: List[Dict], target_groups: int) -> List[Dict]:
        """根据依赖关系分组
        
        Args:
            layers: 层列表
            dependencies: 依赖关系
            target_groups: 目标分组数量
            
        Returns:
            List[Dict]: 层分组列表
        """
        # 构建依赖图
        G = nx.DiGraph()
        
        # 添加所有层作为节点
        for layer in layers:
            G.add_node(layer["name"], size=layer.get("size_bytes", 0), type=layer.get("type", "other"))
        
        # 添加依赖关系作为边
        for dep in dependencies:
            from_layer = dep["from"]
            to_layer = dep["to"]
            G.add_edge(from_layer, to_layer, type=dep.get("type", "dependency"))
        
        # 使用社区检测算法分组
        try:
            # 网络太小时可能无法使用Louvain算法
            if len(layers) < 10:
                partition = {layer["name"]: i % target_groups for i, layer in enumerate(layers)}
            else:
                communities = nx.community.louvain_communities(G.to_undirected(), resolution=1.5)
                
                # 如果社区数量不符合目标，调整分辨率
                resolution = 1.5
                while len(communities) < target_groups and resolution < 5.0:
                    resolution += 0.5
                    communities = nx.community.louvain_communities(G.to_undirected(), resolution=resolution)
                
                while len(communities) > target_groups and resolution > 0.1:
                    resolution -= 0.5
                    communities = nx.community.louvain_communities(G.to_undirected(), resolution=max(0.1, resolution))
                
                # 构建分区映射
                partition = {}
                for i, community in enumerate(communities):
                    for node in community:
                        partition[node] = min(i, target_groups - 1)  # 确保不超过目标组数
        except:
            # 如果社区检测失败，退回到简单分组
            partition = {layer["name"]: i % target_groups for i, layer in enumerate(layers)}
        
        # 根据分区创建分组
        group_dict = {}
        for layer_name, group_id in partition.items():
            if group_id not in group_dict:
                group_dict[group_id] = {"layers": [], "size_bytes": 0}
            
            # 找到层大小
            layer_size = next((l.get("size_bytes", 0) for l in layers if l["name"] == layer_name), 0)
            
            group_dict[group_id]["layers"].append(layer_name)
            group_dict[group_id]["size_bytes"] += layer_size
        
        # 转换为列表
        return list(group_dict.values())
    
    def load_model_for_splitting(self, model_path: Path) -> Any:
        """加载模型用于分片
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            Any: 加载的模型对象
        """
        # 实际上这里只需要加载模型状态字典，而不需要初始化完整模型
        ext = model_path.suffix.lower()
        
        if ext == '.safetensors' and HAS_SAFETENSORS:
            return load_file(model_path)
        else:
            return torch.load(model_path, map_location='cpu')
    
    def extract_layers(self, model: Any, layer_names: List[str]) -> bytes:
        """从模型中提取指定层
        
        Args:
            model: 模型对象
            layer_names: 要提取的层名称列表
            
        Returns:
            bytes: 包含提取层的二进制数据
        """
        # 如果model是状态字典
        if isinstance(model, dict):
            # 提取指定的层
            extracted = {k: v for k, v in model.items() if k in layer_names}
            
            # 保存为临时文件
            buffer = BytesIO()
            torch.save(extracted, buffer)
            buffer.seek(0)
            return buffer.read()
        else:
            # 尝试从模型对象提取状态字典
            if hasattr(model, 'state_dict'):
                state_dict = model.state_dict()
                extracted = {k: v for k, v in state_dict.items() if k in layer_names}
                
                buffer = BytesIO()
                torch.save(extracted, buffer)
                buffer.seek(0)
                return buffer.read()
            else:
                raise ValueError("无法从提供的模型对象中提取层")
    
    def merge_model_from_layer_shards(self, layer_mappings: Dict, output_path: Path) -> None:
        """从层分片合并模型
        
        Args:
            layer_mappings: 层映射信息
            output_path: 输出路径
        """
        # 合并所有分片中的层
        merged_state_dict = {}
        
        for shard_id, shard_info in layer_mappings.items():
            shard_path = shard_info["path"]
            
            # 加载分片
            if Path(shard_path).suffix.lower() == '.safetensors' and HAS_SAFETENSORS:
                shard_dict = load_file(shard_path)
            else:
                shard_dict = torch.load(shard_path, map_location='cpu')
            
            # 合并层
            for key, value in shard_dict.items():
                if key in merged_state_dict:
                    logger.warning(f"层 {key} 在多个分片中存在，将使用分片 {shard_id} 中的版本")
                merged_state_dict[key] = value
        
        # 保存合并后的模型
        if output_path.suffix.lower() == '.safetensors' and HAS_SAFETENSORS:
            save_file(merged_state_dict, output_path)
        else:
            torch.save(merged_state_dict, output_path) 