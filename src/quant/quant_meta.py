"""量化元数据管理模块

此模块实现量化模型的元数据管理，包括：
1. 量化配置记录
2. 性能指标追踪
3. 资源使用统计
4. 版本控制
5. 元数据导出导入
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from loguru import logger

@dataclass
class QuantizationRecord:
    """量化记录数据类"""
    model_hash: str
    config: Dict
    performance: Dict
    timestamp: float
    device_info: Dict
    memory_usage: Dict
    version: str = "1.0.0"

class QuantMetaManager:
    """量化元数据管理器"""
    
    def __init__(self, meta_dir: str = "metadata"):
        """初始化元数据管理器
        
        Args:
            meta_dir: 元数据存储目录
        """
        self.meta_dir = meta_dir
        self.records: Dict[str, List[QuantizationRecord]] = {}
        self._ensure_meta_dir()
        self._load_existing_records()

    def add_record(self,
                  model_hash: str,
                  config: Dict,
                  performance: Optional[Dict] = None,
                  device_info: Optional[Dict] = None) -> str:
        """添加量化记录
        
        Args:
            model_hash: 模型哈希值
            config: 量化配置
            performance: 性能指标
            device_info: 设备信息
            
        Returns:
            str: 记录ID
        """
        try:
            # 准备记录数据
            record = QuantizationRecord(
                model_hash=model_hash,
                config=config,
                performance=performance or {},
                timestamp=time.time(),
                device_info=device_info or self._get_device_info(),
                memory_usage=self._get_memory_usage()
            )
            
            # 添加记录
            if model_hash not in self.records:
                self.records[model_hash] = []
            self.records[model_hash].append(record)
            
            # 保存记录
            self._save_record(record)
            
            return f"{model_hash}_{record.timestamp}"
            
        except Exception as e:
            logger.error(f"添加量化记录失败: {str(e)}")
            raise

    def get_record(self, model_hash: str, timestamp: Optional[float] = None) -> Optional[QuantizationRecord]:
        """获取量化记录
        
        Args:
            model_hash: 模型哈希值
            timestamp: 时间戳（可选）
            
        Returns:
            Optional[QuantizationRecord]: 量化记录
        """
        if model_hash not in self.records:
            return None
            
        if timestamp is None:
            # 返回最新记录
            return self.records[model_hash][-1]
            
        # 查找指定时间戳的记录
        for record in self.records[model_hash]:
            if abs(record.timestamp - timestamp) < 1e-6:
                return record
                
        return None

    def update_record(self,
                     model_hash: str,
                     timestamp: float,
                     updates: Dict[str, Any]) -> bool:
        """更新量化记录
        
        Args:
            model_hash: 模型哈希值
            timestamp: 时间戳
            updates: 更新内容
            
        Returns:
            bool: 是否更新成功
        """
        record = self.get_record(model_hash, timestamp)
        if record is None:
            return False
            
        try:
            # 更新记录
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            # 保存更新
            self._save_record(record)
            return True
            
        except Exception as e:
            logger.error(f"更新量化记录失败: {str(e)}")
            return False

    def delete_record(self, model_hash: str, timestamp: Optional[float] = None) -> bool:
        """删除量化记录
        
        Args:
            model_hash: 模型哈希值
            timestamp: 时间戳（可选）
            
        Returns:
            bool: 是否删除成功
        """
        if model_hash not in self.records:
            return False
            
        try:
            if timestamp is None:
                # 删除所有记录
                del self.records[model_hash]
                self._delete_model_records(model_hash)
            else:
                # 删除指定记录
                records = self.records[model_hash]
                for i, record in enumerate(records):
                    if abs(record.timestamp - timestamp) < 1e-6:
                        records.pop(i)
                        self._delete_record(model_hash, timestamp)
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"删除量化记录失败: {str(e)}")
            return False

    def export_records(self, output_path: str) -> bool:
        """导出量化记录
        
        Args:
            output_path: 输出路径
            
        Returns:
            bool: 是否导出成功
        """
        try:
            # 转换记录为可序列化格式
            export_data = {
                model_hash: [asdict(record) for record in records]
                for model_hash, records in self.records.items()
            }
            
            # 保存记录
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"导出量化记录失败: {str(e)}")
            return False

    def import_records(self, input_path: str) -> bool:
        """导入量化记录
        
        Args:
            input_path: 输入路径
            
        Returns:
            bool: 是否导入成功
        """
        try:
            # 读取记录
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 转换记录为对象
            for model_hash, records in import_data.items():
                self.records[model_hash] = [
                    QuantizationRecord(**record)
                    for record in records
                ]
                
                # 保存记录
                for record in self.records[model_hash]:
                    self._save_record(record)
            
            return True
            
        except Exception as e:
            logger.error(f"导入量化记录失败: {str(e)}")
            return False

    def get_statistics(self, model_hash: Optional[str] = None) -> Dict:
        """获取统计信息
        
        Args:
            model_hash: 模型哈希值（可选）
            
        Returns:
            Dict: 统计信息
        """
        stats = {
            'total_models': len(self.records),
            'total_records': sum(len(records) for records in self.records.values()),
            'models': {}
        }
        
        if model_hash:
            if model_hash in self.records:
                stats['models'][model_hash] = self._calculate_model_stats(
                    self.records[model_hash]
                )
        else:
            for hash_value, records in self.records.items():
                stats['models'][hash_value] = self._calculate_model_stats(records)
        
        return stats

    def _ensure_meta_dir(self):
        """确保元数据目录存在"""
        os.makedirs(self.meta_dir, exist_ok=True)

    def _load_existing_records(self):
        """加载现有记录"""
        try:
            for filename in os.listdir(self.meta_dir):
                if filename.endswith('.json'):
                    with open(os.path.join(self.meta_dir, filename), 'r', encoding='utf-8') as f:
                        record_data = json.load(f)
                        record = QuantizationRecord(**record_data)
                        
                        if record.model_hash not in self.records:
                            self.records[record.model_hash] = []
                        self.records[record.model_hash].append(record)
                        
        except Exception as e:
            logger.error(f"加载现有记录失败: {str(e)}")

    def _save_record(self, record: QuantizationRecord):
        """保存记录
        
        Args:
            record: 量化记录
        """
        try:
            filename = f"{record.model_hash}_{record.timestamp}.json"
            filepath = os.path.join(self.meta_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(record), f, indent=2)
                
        except Exception as e:
            logger.error(f"保存记录失败: {str(e)}")
            raise

    def _delete_record(self, model_hash: str, timestamp: float):
        """删除记录文件
        
        Args:
            model_hash: 模型哈希值
            timestamp: 时间戳
        """
        try:
            filename = f"{model_hash}_{timestamp}.json"
            filepath = os.path.join(self.meta_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                
        except Exception as e:
            logger.error(f"删除记录文件失败: {str(e)}")

    def _delete_model_records(self, model_hash: str):
        """删除模型的所有记录
        
        Args:
            model_hash: 模型哈希值
        """
        try:
            for filename in os.listdir(self.meta_dir):
                if filename.startswith(f"{model_hash}_"):
                    filepath = os.path.join(self.meta_dir, filename)
                    os.remove(filepath)
                    
        except Exception as e:
            logger.error(f"删除模型记录失败: {str(e)}")

    def _get_device_info(self) -> Dict:
        """获取设备信息
        
        Returns:
            Dict: 设备信息
        """
        info = {
            'cpu': platform.processor(),
            'os': platform.system(),
            'python_version': platform.python_version(),
            'cuda_available': torch.cuda.is_available()
        }
        
        if info['cuda_available']:
            info.update({
                'cuda_version': torch.version.cuda,
                'gpu_name': torch.cuda.get_device_name(0)
            })
        
        return info

    def _get_memory_usage(self) -> Dict:
        """获取内存使用情况
        
        Returns:
            Dict: 内存使用信息
        """
        import psutil
        
        memory = psutil.virtual_memory()
        usage = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }
        
        if torch.cuda.is_available():
            usage['gpu_allocated'] = torch.cuda.memory_allocated(0)
            usage['gpu_reserved'] = torch.cuda.memory_reserved(0)
        
        return usage

    def _calculate_model_stats(self, records: List[QuantizationRecord]) -> Dict:
        """计算模型统计信息
        
        Args:
            records: 记录列表
            
        Returns:
            Dict: 统计信息
        """
        if not records:
            return {}
            
        # 基础统计
        stats = {
            'record_count': len(records),
            'first_record': records[0].timestamp,
            'last_record': records[-1].timestamp,
            'versions': set(r.version for r in records)
        }
        
        # 性能统计
        performance_metrics = []
        for record in records:
            if record.performance:
                performance_metrics.append(record.performance)
                
        if performance_metrics:
            stats['performance'] = {
                'min': min(metrics.get('score', 0) for metrics in performance_metrics),
                'max': max(metrics.get('score', 0) for metrics in performance_metrics),
                'avg': sum(metrics.get('score', 0) for metrics in performance_metrics) / len(performance_metrics)
            }
        
        return stats 