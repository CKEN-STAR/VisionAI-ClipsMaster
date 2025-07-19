#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态模板引擎

根据目标版本动态生成适配的模板，支持版本特性感知和多格式导出。
"""

import os
import logging
import yaml
import json
import xml.dom.minidom as minidom
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Iterator
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class VersionAwareTemplate:
    """版本感知的模板引擎，能够根据目标版本生成适配的导出模板"""
    
    def __init__(self, target_version, template_type="jianying", config_path=None):
        """
        初始化版本感知模板
        
        Args:
            target_version: 目标版本号，如 "3.0.0"
            template_type: 模板类型，默认为 "jianying"
            config_path: 配置文件路径，默认使用版本特征库路径
        """
        self.target_version = target_version
        self.template_type = template_type
        self.config_path = config_path
        
        # 加载版本特征库
        self.template_db = self._load_version_specs()
        
        # 选择适当的模式文件
        self.schema = self._select_schema()
        
        # 缓存特性查询结果
        self._features_cache = {}
        self._effects_cache = {}
        
        # 初始化模板生成器
        self._initialize_generators()
        
    def _load_version_specs(self) -> Dict[str, Any]:
        """加载版本特征配置"""
        try:
            # 优先使用指定配置文件
            if self.config_path and os.path.exists(self.config_path):
                config_file = self.config_path
            else:
                # 使用默认路径
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                config_file = os.path.join(root_dir, "configs", f"{self.template_type}_versions.yaml")
                
            # 检查文件是否存在
            if not os.path.exists(config_file):
                logger.error(f"版本特征库配置文件不存在: {config_file}")
                return {}
                
            # 加载YAML配置
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            return data
        except Exception as e:
            logger.error(f"加载版本特征库配置文件失败: {str(e)}")
            return {}
    
    def _select_schema(self) -> Optional[str]:
        """选择匹配版本的XSD架构"""
        if not self.template_db or 'version_specs' not in self.template_db:
            return None
            
        for v in self.template_db['version_specs']:
            if v.get('version') == self.target_version:
                return v.get('schema')
                
        # 如果没有精确匹配，尝试找最接近的版本
        target_parts = self._parse_version(self.target_version)
        closest_schema = None
        closest_distance = float('inf')
        
        for v in self.template_db['version_specs']:
            version = v.get('version')
            if not version:
                continue
                
            v_parts = self._parse_version(version)
            distance = sum(abs(t-v) for t, v in zip(target_parts, v_parts))
            
            if distance < closest_distance:
                closest_distance = distance
                closest_schema = v.get('schema')
                
        return closest_schema
    
    def _parse_version(self, version: str) -> List[int]:
        """解析版本号为整数列表"""
        try:
            if version.lower().startswith('v'):
                version = version[1:]
            return [int(x) for x in version.split('.')]
        except (ValueError, AttributeError):
            return [0, 0, 0]
    
    def _initialize_generators(self) -> None:
        """初始化各种格式的模板生成器"""
        self.generators = {
            'xml': self._generate_xml_template,
            'json': self._generate_json_template,
            'text': self._generate_text_template
        }
    
    def is_feature_supported(self, feature_name: str) -> bool:
        """
        检查特定特性是否在目标版本中支持
        
        Args:
            feature_name: 特性名称
            
        Returns:
            bool: 是否支持该特性
        """
        # 检查缓存
        if feature_name in self._features_cache:
            return self._features_cache[feature_name]
            
        if not self.template_db or 'version_specs' not in self.template_db:
            result = False
        else:
            # 查找目标版本
            for v in self.template_db['version_specs']:
                if v.get('version') == self.target_version:
                    # 检查支持的特性
                    supported = v.get('supported_features', [])
                    
                    # 搜索特性名称
                    result = any(
                        (isinstance(f, dict) and f.get('name') == feature_name) or 
                        (isinstance(f, str) and f == feature_name)
                        for f in supported
                    )
                    break
            else:
                result = False
                
        # 缓存结果
        self._features_cache[feature_name] = result
        return result
    
    def is_effect_supported(self, effect_name: str) -> bool:
        """
        检查特定效果是否在目标版本中支持
        
        Args:
            effect_name: 效果名称
            
        Returns:
            bool: 是否支持该效果
        """
        # 检查缓存
        if effect_name in self._effects_cache:
            return self._effects_cache[effect_name]
            
        if not self.template_db or 'version_specs' not in self.template_db:
            result = False
        else:
            # 查找目标版本
            for v in self.template_db['version_specs']:
                if v.get('version') == self.target_version:
                    # 检查支持的效果
                    supported = v.get('supported_effects', [])
                    result = effect_name in supported
                    break
            else:
                result = False
                
        # 缓存结果
        self._effects_cache[effect_name] = result
        return result
    
    def get_max_resolution(self) -> Tuple[int, int]:
        """
        获取目标版本支持的最大分辨率
        
        Returns:
            Tuple[int, int]: 宽和高的最大值
        """
        if not self.template_db or 'version_specs' not in self.template_db:
            return (1920, 1080)  # 默认返回1080p
            
        # 查找目标版本
        for v in self.template_db['version_specs']:
            if v.get('version') == self.target_version:
                max_res = v.get('max_resolution')
                if max_res:
                    try:
                        width, height = map(int, max_res.split('x'))
                        return (width, height)
                    except (ValueError, AttributeError):
                        pass
                break
                
        return (1920, 1080)  # 默认返回1080p
    
    def generate_template(self, format_type: str = 'xml', template_data: Dict[str, Any] = None) -> Optional[str]:
        """
        根据目标版本生成模板
        
        Args:
            format_type: 输出格式类型 ('xml', 'json', 'text')
            template_data: 要填充到模板中的数据
            
        Returns:
            Optional[str]: 生成的模板字符串，如果生成失败则返回None
        """
        if format_type not in self.generators:
            logger.error(f"不支持的模板格式: {format_type}")
            return None
            
        if template_data is None:
            template_data = {}
            
        try:
            # 调用对应的生成器
            return self.generators[format_type](template_data)
        except Exception as e:
            logger.error(f"生成{format_type}模板时出错: {str(e)}")
            return None
    
    def _generate_xml_template(self, data: Dict[str, Any]) -> str:
        """生成XML格式的模板"""
        # 创建XML文档
        doc = minidom.getDOMImplementation().createDocument(None, "jianying_project", None)
        root = doc.documentElement
        
        # 设置版本属性
        root.setAttribute("version", self.target_version)
        
        # 添加基本结构
        info = doc.createElement("info")
        metadata = doc.createElement("metadata")
        project_settings = doc.createElement("project_settings")
        
        # 填充元数据
        jy_type = doc.createElement("jy_type")
        jy_type.appendChild(doc.createTextNode(data.get("type", "project")))
        
        project_id = doc.createElement("project_id")
        project_id.appendChild(doc.createTextNode(data.get("id", "project_001")))
        
        title = doc.createElement("title")
        title.appendChild(doc.createTextNode(data.get("title", "新项目")))
        
        # 添加元素
        metadata.appendChild(jy_type)
        metadata.appendChild(project_id)
        metadata.appendChild(title)
        info.appendChild(metadata)
        
        # 添加项目设置
        resolution = doc.createElement("resolution")
        max_width, max_height = self.get_max_resolution()
        res_width = min(data.get("width", 1920), max_width)
        res_height = min(data.get("height", 1080), max_height)
        
        resolution.setAttribute("width", str(res_width))
        resolution.setAttribute("height", str(res_height))
        
        frame_rate = doc.createElement("frame_rate")
        frame_rate.appendChild(doc.createTextNode(str(data.get("fps", 30.0))))
        
        project_settings.appendChild(resolution)
        project_settings.appendChild(frame_rate)
        info.appendChild(project_settings)
        
        # 添加资源和时间线
        resources = doc.createElement("resources")
        timeline = doc.createElement("timeline")
        timeline.setAttribute("id", data.get("timeline_id", "timeline_001"))
        timeline.setAttribute("duration", data.get("duration", "00:01:00.000"))
        
        # 根据版本特性添加不同的轨道结构
        if self.is_feature_supported("multi_track"):
            # 多轨道支持
            for i in range(data.get("video_tracks", 1)):
                track = doc.createElement("track")
                track.setAttribute("id", f"video_track_{i+1}")
                track.setAttribute("type", "video")
                timeline.appendChild(track)
                
            for i in range(data.get("audio_tracks", 1)):
                track = doc.createElement("track")
                track.setAttribute("id", f"audio_track_{i+1}")
                track.setAttribute("type", "audio")
                timeline.appendChild(track)
                
            # 字幕轨支持
            if self.is_feature_supported("subtitle_track"):
                subtitle_track = doc.createElement("subtitle_track")
                subtitle_track.setAttribute("id", "subtitle_track_1")
                subtitle_track.setAttribute("language", data.get("language", "zh-CN"))
                timeline.appendChild(subtitle_track)
                
            # 效果层支持
            if self.is_feature_supported("effects_layer"):
                effects_track = doc.createElement("effects_track")
                effects_track.setAttribute("id", "effects_track_1")
                timeline.appendChild(effects_track)
        else:
            # 单轨道支持
            track = doc.createElement("track")
            track.setAttribute("id", "main_track")
            track.setAttribute("type", "video")
            timeline.appendChild(track)
        
        # 嵌套序列支持
        if self.is_feature_supported("nested_sequences") and data.get("use_nested", False):
            nested = doc.createElement("nested_sequence")
            nested.setAttribute("id", "nested_001")
            nested.setAttribute("name", data.get("nested_name", "嵌套序列"))
            nested.setAttribute("duration", "00:00:30.000")
            
            # 添加嵌套轨道
            nested_track = doc.createElement("track")
            nested_track.setAttribute("id", "nested_track_1")
            nested_track.setAttribute("type", "video")
            nested.appendChild(nested_track)
            
            root.appendChild(nested)
        
        # 添加主要部分到根元素
        root.appendChild(info)
        root.appendChild(resources)
        root.appendChild(timeline)
        
        # 输出格式化的XML
        return doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    
    def _generate_json_template(self, data: Dict[str, Any]) -> str:
        """生成JSON格式的模板"""
        # 基本结构
        template = {
            "jianying_project": {
                "version": self.target_version,
                "info": {
                    "metadata": {
                        "jy_type": data.get("type", "project"),
                        "project_id": data.get("id", "project_001"),
                        "title": data.get("title", "新项目")
                    },
                    "project_settings": {
                        "resolution": {
                            "width": min(data.get("width", 1920), self.get_max_resolution()[0]),
                            "height": min(data.get("height", 1080), self.get_max_resolution()[1])
                        },
                        "frame_rate": data.get("fps", 30.0)
                    }
                },
                "resources": {
                    "assets": []
                },
                "timeline": {
                    "id": data.get("timeline_id", "timeline_001"),
                    "duration": data.get("duration", "00:01:00.000"),
                    "tracks": []
                }
            }
        }
        
        # 根据版本特性添加不同的轨道结构
        if self.is_feature_supported("multi_track"):
            # 多轨道支持
            for i in range(data.get("video_tracks", 1)):
                template["jianying_project"]["timeline"]["tracks"].append({
                    "id": f"video_track_{i+1}",
                    "type": "video",
                    "clips": []
                })
                
            for i in range(data.get("audio_tracks", 1)):
                template["jianying_project"]["timeline"]["tracks"].append({
                    "id": f"audio_track_{i+1}",
                    "type": "audio",
                    "clips": []
                })
                
            # 字幕轨支持
            if self.is_feature_supported("subtitle_track"):
                template["jianying_project"]["timeline"]["subtitle_tracks"] = [{
                    "id": "subtitle_track_1",
                    "language": data.get("language", "zh-CN"),
                    "subtitles": []
                }]
                
            # 效果层支持
            if self.is_feature_supported("effects_layer"):
                template["jianying_project"]["timeline"]["effects_tracks"] = [{
                    "id": "effects_track_1",
                    "effects": []
                }]
        else:
            # 单轨道支持
            template["jianying_project"]["timeline"]["tracks"].append({
                "id": "main_track",
                "type": "video",
                "clips": []
            })
        
        # 嵌套序列支持
        if self.is_feature_supported("nested_sequences") and data.get("use_nested", False):
            template["jianying_project"]["nested_sequences"] = [{
                "id": "nested_001",
                "name": data.get("nested_name", "嵌套序列"),
                "duration": "00:00:30.000",
                "tracks": [{
                    "id": "nested_track_1",
                    "type": "video",
                    "clips": []
                }]
            }]
        
        # 输出格式化的JSON
        return json.dumps(template, indent=2, ensure_ascii=False)
    
    def _generate_text_template(self, data: Dict[str, Any]) -> str:
        """生成文本格式的模板（简化描述）"""
        lines = []
        lines.append(f"剪映项目模板 - 版本 {self.target_version}")
        lines.append("-" * 50)
        lines.append(f"项目名称: {data.get('title', '新项目')}")
        
        # 分辨率
        max_width, max_height = self.get_max_resolution()
        width = min(data.get("width", 1920), max_width)
        height = min(data.get("height", 1080), max_height)
        lines.append(f"分辨率: {width}x{height}")
        lines.append(f"帧率: {data.get('fps', 30.0)}")
        
        lines.append("")
        lines.append("支持的功能:")
        
        # 通用功能列表
        features_to_check = [
            ("multi_track", "多轨道"),
            ("single_track", "单轨道"),
            ("subtitle_track", "字幕轨"),
            ("effects_layer", "效果层"),
            ("nested_sequences", "嵌套序列"),
            ("audio_effects", "音频特效"),
            ("advanced_effects", "高级效果"),
            ("keyframe_animation", "关键帧动画"),
            ("motion_tracking", "运动跟踪")
        ]
        
        for feature_id, feature_name in features_to_check:
            if self.is_feature_supported(feature_id):
                lines.append(f"- {feature_name}")
        
        lines.append("")
        lines.append("支持的效果:")
        
        # 通用效果列表
        effects_to_check = [
            "blur", "color", "transform", "audio", "transition", "text", "3d"
        ]
        
        for effect_id in effects_to_check:
            if self.is_effect_supported(effect_id):
                lines.append(f"- {effect_id}")
        
        lines.append("")
        lines.append("轨道结构:")
        
        if self.is_feature_supported("multi_track"):
            lines.append(f"- 视频轨道数: {data.get('video_tracks', 1)}")
            lines.append(f"- 音频轨道数: {data.get('audio_tracks', 1)}")
            
            if self.is_feature_supported("subtitle_track"):
                lines.append("- 字幕轨道数: 1")
                
            if self.is_feature_supported("effects_layer"):
                lines.append("- 效果轨道数: 1")
        else:
            lines.append("- 单视频轨道")
        
        if self.is_feature_supported("nested_sequences") and data.get("use_nested", False):
            lines.append("")
            lines.append("嵌套序列:")
            lines.append(f"- 名称: {data.get('nested_name', '嵌套序列')}")
            lines.append("- 时长: 00:00:30.000")
        
        return "\n".join(lines)
    
    def get_template_path(self, format_type: str = 'xml') -> Optional[str]:
        """
        获取模板文件路径
        
        Args:
            format_type: 模板格式类型
            
        Returns:
            Optional[str]: 模板文件路径，如果不存在则返回None
        """
        if not self.schema:
            return None
            
        # 构建预设模板路径
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        if format_type == 'xml':
            return os.path.join(root_dir, "configs", self.schema)
        elif format_type == 'json':
            # 尝试查找对应的JSON模板
            json_schema = self.schema.replace('.xsd', '.json')
            json_path = os.path.join(root_dir, "configs", json_schema)
            
            if os.path.exists(json_path):
                return json_path
                
        return None


# 工厂函数，创建模板引擎实例
def create_template_engine(target_version: str, 
                           template_type: str = "jianying", 
                           config_path: str = None) -> VersionAwareTemplate:
    """
    创建模板引擎实例
    
    Args:
        target_version: 目标版本号
        template_type: 模板类型
        config_path: 配置文件路径
        
    Returns:
        VersionAwareTemplate: 模板引擎实例
    """
    return VersionAwareTemplate(target_version, template_type, config_path)


if __name__ == "__main__":
    # 简单测试
    import sys
    
    if len(sys.argv) > 1:
        target_version = sys.argv[1]
    else:
        target_version = "3.0.0"
        
    engine = create_template_engine(target_version)
    
    test_data = {
        "title": "测试项目",
        "width": 3840,
        "height": 2160,
        "fps": 29.97,
        "video_tracks": 3,
        "audio_tracks": 2,
        "use_nested": True,
        "nested_name": "场景1"
    }
    
    # 生成XML模板
    xml_template = engine.generate_template('xml', test_data)
    if xml_template:
        print("XML模板生成成功!")
        print(xml_template[:500] + "...\n")
    
    # 生成JSON模板
    json_template = engine.generate_template('json', test_data)
    if json_template:
        print("JSON模板生成成功!")
        print(json_template[:500] + "...\n")
    
    # 生成文本描述
    text_template = engine.generate_template('text', test_data)
    if text_template:
        print("文本模板生成成功!")
        print(text_template) 