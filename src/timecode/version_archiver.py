import json
import time
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class TimelineArchiver:
    """
    版本化时间轴存档系统
    
    用于保存和管理短剧混剪项目的不同字幕/时间轴版本，支持版本回溯、比较和恢复功能。
    每个版本都包含完整的场景数据、时间戳和用户注释。
    """
    
    def __init__(self, project_id: str = None, storage_dir: str = None):
        """
        初始化时间轴存档系统
        
        Args:
            project_id: 项目唯一标识符，如果为None则自动生成
            storage_dir: 版本文件存储目录，默认为"data/output/timeline_versions"
        """
        self.history: Dict[str, Dict] = {}  # 内存中的版本历史记录
        self.project_id = project_id or self._generate_project_id()
        self.storage_dir = storage_dir or os.path.join("data", "output", "timeline_versions")
        self.current_version_id: Optional[str] = None
        
        # 确保存储目录存在
        os.makedirs(os.path.join(self.storage_dir, self.project_id), exist_ok=True)
        
        # 加载已有的版本历史（如果存在）
        self._load_history()
    
    def _generate_project_id(self) -> str:
        """生成唯一的项目ID"""
        timestamp = int(time.time())
        random_suffix = os.urandom(4).hex()
        return f"project_{timestamp}_{random_suffix}"
    
    def _load_history(self) -> None:
        """从磁盘加载版本历史"""
        history_path = os.path.join(self.storage_dir, self.project_id, "history.json")
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                
                # 找到最新版本作为当前版本
                if self.history:
                    latest_version = max(
                        self.history.items(),
                        key=lambda x: x[1]["timestamp"]
                    )
                    self.current_version_id = latest_version[0]
            except Exception as e:
                print(f"警告: 加载版本历史时出错: {e}")
                # 如果加载失败，创建新的历史记录
                self.history = {}
    
    def _save_history(self) -> None:
        """将版本历史保存到磁盘"""
        history_path = os.path.join(self.storage_dir, self.project_id, "history.json")
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def _compute_hash(self, data: Any) -> str:
        """计算数据的哈希值作为版本ID"""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()[:12]
    
    def save_version(self, scenes: List[Dict], note: str = "") -> str:
        """
        保存新的时间轴版本
        
        Args:
            scenes: 场景数据列表，包含时间轴、文本内容等信息
            note: 版本说明，记录版本变更目的或特点
            
        Returns:
            version_id: 生成的版本ID
        """
        # 计算版本ID
        version_id = self._compute_hash(scenes)
        
        # 检查是否重复版本
        if version_id in self.history:
            # 如果内容相同但注释不同，更新注释
            if note and note != self.history[version_id].get("note", ""):
                self.history[version_id]["note"] = note
                self._save_history()
            return version_id
        
        # 创建新版本记录
        timestamp = time.time()
        formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        self.history[version_id] = {
            "timestamp": timestamp,
            "formatted_time": formatted_time,
            "note": note,
            "scene_count": len(scenes)
        }
        
        # 保存版本数据到单独的文件
        version_path = os.path.join(self.storage_dir, self.project_id, f"{version_id}.json")
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "version_id": version_id,
                    "timestamp": timestamp,
                    "formatted_time": formatted_time,
                    "note": note
                },
                "data": scenes
            }, f, ensure_ascii=False, indent=2)
        
        # 更新内存中的历史记录
        self._save_history()
        
        # 设置为当前版本
        self.current_version_id = version_id
        
        return version_id
    
    def load_version(self, version_id: str) -> Optional[List[Dict]]:
        """
        加载指定版本的时间轴数据
        
        Args:
            version_id: 要加载的版本ID
            
        Returns:
            场景数据列表，如果版本不存在则返回None
        """
        if version_id not in self.history:
            print(f"错误: 版本 {version_id} 不存在")
            return None
        
        version_path = os.path.join(self.storage_dir, self.project_id, f"{version_id}.json")
        if not os.path.exists(version_path):
            print(f"错误: 版本文件 {version_path} 不存在")
            return None
        
        try:
            with open(version_path, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            # 设置为当前版本
            self.current_version_id = version_id
            
            return version_data["data"]
        except Exception as e:
            print(f"错误: 加载版本 {version_id} 时发生异常: {e}")
            return None
    
    def get_version_list(self, limit: int = None, sort_by_time: bool = True) -> List[Dict]:
        """
        获取版本列表
        
        Args:
            limit: 返回结果数量限制
            sort_by_time: 是否按时间排序，True为从新到旧，False为从旧到新
            
        Returns:
            版本信息列表
        """
        versions = [
            {
                "version_id": v_id,
                "timestamp": info["timestamp"],
                "formatted_time": info.get("formatted_time", 
                    datetime.fromtimestamp(info["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")),
                "note": info.get("note", ""),
                "scene_count": info.get("scene_count", 0),
                "is_current": v_id == self.current_version_id
            }
            for v_id, info in self.history.items()
        ]
        
        # 按时间排序
        if sort_by_time:
            versions.sort(key=lambda x: x["timestamp"], reverse=True)
        else:
            versions.sort(key=lambda x: x["timestamp"])
        
        # 限制结果数量
        if limit and len(versions) > limit:
            versions = versions[:limit]
        
        return versions
    
    def delete_version(self, version_id: str) -> bool:
        """
        删除指定版本
        
        Args:
            version_id: 要删除的版本ID
            
        Returns:
            操作是否成功
        """
        if version_id not in self.history:
            print(f"错误: 版本 {version_id} 不存在")
            return False
        
        # 不允许删除唯一的版本
        if len(self.history) <= 1:
            print("错误: 不能删除唯一的版本")
            return False
        
        # 从历史记录中移除
        del self.history[version_id]
        
        # 删除版本文件
        version_path = os.path.join(self.storage_dir, self.project_id, f"{version_id}.json")
        if os.path.exists(version_path):
            os.remove(version_path)
        
        # 保存更新后的历史
        self._save_history()
        
        # 如果删除的是当前版本，将最新版本设为当前版本
        if version_id == self.current_version_id:
            latest_version = max(
                self.history.items(),
                key=lambda x: x[1]["timestamp"]
            )
            self.current_version_id = latest_version[0]
        
        return True
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict:
        """
        比较两个版本的差异
        
        Args:
            version_id1: 第一个版本ID
            version_id2: 第二个版本ID
            
        Returns:
            差异信息，包括场景数量变化、添加/删除/修改的场景等
        """
        scenes1 = self.load_version(version_id1)
        scenes2 = self.load_version(version_id2)
        
        if not scenes1 or not scenes2:
            return {"error": "无法加载版本数据"}
        
        # 基本统计
        stats = {
            "version1": {
                "id": version_id1,
                "scene_count": len(scenes1),
                "time": self.history[version_id1].get("formatted_time", "未知")
            },
            "version2": {
                "id": version_id2,
                "scene_count": len(scenes2),
                "time": self.history[version_id2].get("formatted_time", "未知")
            },
            "scene_diff": len(scenes2) - len(scenes1),
            "total_duration_diff": self._calculate_total_duration(scenes2) - self._calculate_total_duration(scenes1)
        }
        
        # 进一步分析可以添加场景内容的详细比较
        # 这里可以根据实际需求扩展比较逻辑
        
        return stats
    
    def _calculate_total_duration(self, scenes: List[Dict]) -> float:
        """计算场景总时长"""
        total = 0.0
        for scene in scenes:
            # 根据实际场景数据结构调整
            if "duration" in scene:
                total += scene["duration"]
            elif "start_time" in scene and "end_time" in scene:
                total += scene["end_time"] - scene["start_time"]
        return total
    
    def export_version(self, version_id: str, export_path: str) -> bool:
        """
        导出指定版本为独立文件
        
        Args:
            version_id: 要导出的版本ID
            export_path: 导出文件路径
            
        Returns:
            操作是否成功
        """
        data = self.load_version(version_id)
        if not data:
            return False
        
        metadata = self.history.get(version_id, {})
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": {
                        "version_id": version_id,
                        "timestamp": metadata.get("timestamp"),
                        "formatted_time": metadata.get("formatted_time"),
                        "note": metadata.get("note", ""),
                        "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "data": data
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"错误: 导出版本时发生异常: {e}")
            return False
    
    def import_version(self, import_path: str, note: str = None) -> Optional[str]:
        """
        从文件导入版本
        
        Args:
            import_path: 导入文件路径
            note: 可选的新注释，如果为None则使用原注释
            
        Returns:
            导入的版本ID，失败则返回None
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # 验证导入数据结构
            if "data" not in imported_data:
                print("错误: 导入文件格式不正确，缺少data字段")
                return None
            
            # 使用原注释或新注释
            original_note = imported_data.get("metadata", {}).get("note", "")
            version_note = note if note is not None else original_note
            
            # 保存为新版本
            return self.save_version(imported_data["data"], version_note)
            
        except Exception as e:
            print(f"错误: 导入版本时发生异常: {e}")
            return None
    
    def get_current_version(self) -> Optional[Dict]:
        """
        获取当前活动版本的完整信息
        
        Returns:
            当前版本的详细信息，包括元数据和场景数据
        """
        if not self.current_version_id:
            return None
        
        data = self.load_version(self.current_version_id)
        if not data:
            return None
        
        metadata = self.history.get(self.current_version_id, {})
        
        return {
            "metadata": {
                "version_id": self.current_version_id,
                "timestamp": metadata.get("timestamp"),
                "formatted_time": metadata.get("formatted_time"),
                "note": metadata.get("note", ""),
                "scene_count": len(data)
            },
            "data": data
        } 