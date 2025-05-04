"""数据血缘追踪模块

此模块负责追踪数据在系统中的流转、处理和使用情况,主要功能包括:
1. 数据源标记
2. 处理流程追踪
3. 数据使用分析
4. 血缘关系可视化
"""

import os
import time
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from loguru import logger

class DataTracer:
    """数据血缘追踪器"""
    
    def __init__(self, base_dir: str = "data"):
        """初始化数据追踪器
        
        Args:
            base_dir: 数据根目录
        """
        self.base_dir = Path(base_dir)
        self.trace_file = self.base_dir / ".data_trace.json"
        self.trace_data = self._load_trace_data()
        
    def _load_trace_data(self) -> Dict:
        """加载追踪数据"""
        if self.trace_file.exists():
            try:
                with open(self.trace_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载追踪数据失败: {str(e)}")
                return {}
        return {
            "files": {},
            "processes": [],
            "relationships": []
        }
    
    def _save_trace_data(self):
        """保存追踪数据"""
        try:
            with open(self.trace_file, 'w', encoding='utf-8') as f:
                json.dump(self.trace_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存追踪数据失败: {str(e)}")

    def tag_data_origin(self, file_path: Union[str, Path], lang: str, 
                       source: str = "user_upload", 
                       metadata: Optional[Dict] = None) -> bool:
        """标记数据源
        
        Args:
            file_path: 文件路径
            lang: 语言标识
            source: 数据来源
            metadata: 额外元数据
        
        Returns:
            bool: 是否成功标记
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 计算文件哈希值
            file_hash = self._calculate_file_hash(file_path)
            
            # 记录文件信息
            file_info = {
                "path": str(file_path),
                "hash": file_hash,
                "lang": lang,
                "source": source,
                "timestamp": time.time(),
                "metadata": metadata or {},
                "processing_history": []
            }
            
            # 在文件开头添加追踪标记
            self._add_trace_tag(file_path, lang)
            
            # 更新追踪数据
            self.trace_data["files"][str(file_path)] = file_info
            self._save_trace_data()
            
            logger.info(f"成功标记数据源: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"标记数据源失败: {str(e)}")
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _add_trace_tag(self, file_path: Path, lang: str):
        """添加追踪标记到文件"""
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                tag = f"\n<!-- ORIGIN_LANG={lang} TIMESTAMP={time.time()} -->\n"
                f.write(tag + content)
        except Exception as e:
            logger.error(f"添加追踪标记失败: {str(e)}")
    
    def record_processing(self, input_files: List[Union[str, Path]], 
                         output_file: Union[str, Path],
                         process_type: str,
                         processor: str,
                         metadata: Optional[Dict] = None) -> bool:
        """记录数据处理过程
        
        Args:
            input_files: 输入文件列表
            output_file: 输出文件
            process_type: 处理类型
            processor: 处理器标识
            metadata: 额外元数据
        
        Returns:
            bool: 是否成功记录
        """
        try:
            process_info = {
                "id": f"proc_{int(time.time())}",
                "type": process_type,
                "processor": processor,
                "timestamp": time.time(),
                "input_files": [str(f) for f in input_files],
                "output_file": str(output_file),
                "metadata": metadata or {}
            }
            
            # 记录处理过程
            self.trace_data["processes"].append(process_info)
            
            # 更新文件关系
            for input_file in input_files:
                relationship = {
                    "source": str(input_file),
                    "target": str(output_file),
                    "process_id": process_info["id"]
                }
                self.trace_data["relationships"].append(relationship)
                
                # 更新文件处理历史
                if str(input_file) in self.trace_data["files"]:
                    self.trace_data["files"][str(input_file)]["processing_history"].append(
                        process_info["id"]
                    )
            
            self._save_trace_data()
            logger.info(f"成功记录处理过程: {process_type}")
            return True
            
        except Exception as e:
            logger.error(f"记录处理过程失败: {str(e)}")
            return False
    
    def get_data_lineage(self, file_path: Union[str, Path]) -> Dict:
        """获取数据血缘关系
        
        Args:
            file_path: 文件路径
        
        Returns:
            Dict: 血缘关系信息
        """
        file_path = str(Path(file_path))
        lineage = {
            "upstream": [],   # 上游数据
            "downstream": [], # 下游数据
            "processes": []   # 相关处理过程
        }
        
        # 查找上游数据
        for rel in self.trace_data["relationships"]:
            if rel["target"] == file_path:
                lineage["upstream"].append({
                    "file": rel["source"],
                    "process": rel["process_id"]
                })
            elif rel["source"] == file_path:
                lineage["downstream"].append({
                    "file": rel["target"],
                    "process": rel["process_id"]
                })
        
        # 收集相关处理过程
        process_ids = set()
        for item in lineage["upstream"] + lineage["downstream"]:
            process_ids.add(item["process"])
        
        lineage["processes"] = [
            proc for proc in self.trace_data["processes"]
            if proc["id"] in process_ids
        ]
        
        return lineage
    
    def visualize_lineage(self, file_path: Union[str, Path], 
                         output_file: Optional[Union[str, Path]] = None):
        """可视化数据血缘关系
        
        Args:
            file_path: 目标文件路径
            output_file: 输出文件路径
        """
        try:
            import graphviz
            
            dot = graphviz.Digraph(comment='Data Lineage')
            dot.attr(rankdir='LR')
            
            lineage = self.get_data_lineage(file_path)
            
            # 添加节点
            dot.node(str(file_path), str(file_path), shape='box', style='filled', fillcolor='lightblue')
            
            # 添加上游关系
            for up in lineage["upstream"]:
                dot.node(up["file"], up["file"], shape='box')
                dot.edge(up["file"], str(file_path), label=up["process"])
            
            # 添加下游关系
            for down in lineage["downstream"]:
                dot.node(down["file"], down["file"], shape='box')
                dot.edge(str(file_path), down["file"], label=down["process"])
            
            # 保存图形
            if output_file:
                dot.render(str(output_file), view=True)
            else:
                dot.render('data_lineage', view=True)
                
        except ImportError:
            logger.warning("需要安装graphviz包来可视化血缘关系")
        except Exception as e:
            logger.error(f"可视化血缘关系失败: {str(e)}")
    
    def analyze_data_usage(self, file_path: Optional[Union[str, Path]] = None) -> Dict:
        """分析数据使用情况
        
        Args:
            file_path: 可选的目标文件路径
        
        Returns:
            Dict: 使用情况统计
        """
        stats = {
            "total_files": len(self.trace_data["files"]),
            "total_processes": len(self.trace_data["processes"]),
            "file_types": {},
            "process_types": {},
            "most_processed_files": []
        }
        
        # 统计文件类型
        for file_info in self.trace_data["files"].values():
            lang = file_info.get("lang", "unknown")
            stats["file_types"][lang] = stats["file_types"].get(lang, 0) + 1
        
        # 统计处理类型
        for proc in self.trace_data["processes"]:
            proc_type = proc["type"]
            stats["process_types"][proc_type] = stats["process_types"].get(proc_type, 0) + 1
        
        # 查找最常处理的文件
        file_process_count = {}
        for file_path, file_info in self.trace_data["files"].items():
            count = len(file_info.get("processing_history", []))
            file_process_count[file_path] = count
        
        # 排序并获取前10个最常处理的文件
        most_processed = sorted(file_process_count.items(), 
                              key=lambda x: x[1], 
                              reverse=True)[:10]
        stats["most_processed_files"] = [
            {"file": k, "process_count": v} for k, v in most_processed
        ]
        
        return stats

    def cleanup_old_traces(self, days: int = 30):
        """清理旧的追踪记录
        
        Args:
            days: 保留天数
        """
        try:
            current_time = time.time()
            max_age = days * 24 * 60 * 60
            
            # 清理旧文件记录
            files_to_remove = []
            for file_path, file_info in self.trace_data["files"].items():
                if current_time - file_info["timestamp"] > max_age:
                    files_to_remove.append(file_path)
            
            for file_path in files_to_remove:
                del self.trace_data["files"][file_path]
            
            # 清理旧处理记录
            self.trace_data["processes"] = [
                proc for proc in self.trace_data["processes"]
                if current_time - proc["timestamp"] <= max_age
            ]
            
            # 清理相关的关系记录
            valid_files = set(self.trace_data["files"].keys())
            self.trace_data["relationships"] = [
                rel for rel in self.trace_data["relationships"]
                if rel["source"] in valid_files and rel["target"] in valid_files
            ]
            
            self._save_trace_data()
            logger.info(f"成功清理{len(files_to_remove)}条旧追踪记录")
            
        except Exception as e:
            logger.error(f"清理旧追踪记录失败: {str(e)}") 