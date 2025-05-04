"""
参数配置矩阵模块

该模块定义了混剪引擎的各种参数预设，用于控制剧本重构和视频混剪效果。
包括节奏控制、情感分析、剧情结构等关键维度的参数组合。
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from loguru import logger

class ParamMatrix:
    """参数配置矩阵类，提供多种预设和自定义配置选项"""
    
    # 基础预设参数组
    presets = {
        # 默认平衡参数
        "default": {
            "pace": 1.0,                 # 节奏系数 (0.5-2.0)
            "emotion_intensity": 0.7,    # 情感强度 (0-1)
            "subplot": 3,                # 支线数量 (0-5)
            "cliffhanger_freq": 0.4,     # 悬念频率 (0-1)
            "resolution_delay": 0.5,     # 悬念密度 (0-1)
            "character_focus": 2,        # 角色聚焦数量 (1-5)
            "conflict_intensity": 0.6,   # 冲突强度 (0-1)
            "punchline_ratio": 0.15,     # 金句保留比例 (0-0.3)
            "context_preservation": 0.5, # 上下文保留度 (0-1)
            "linearity": 0.7             # 线性叙事程度 (0-1, 0为高度非线性)
        },
        
        # 快节奏预设 - 适合动作/冲突场景
        "快节奏": {
            "pace": 1.3,                 # 更快的节奏
            "emotion_intensity": 0.8,    # 较高情感强度
            "subplot": 2,                # 减少支线，聚焦主线
            "cliffhanger_freq": 0.6,     # 较高悬念频率
            "resolution_delay": 0.8,     # 高悬念密度
            "character_focus": 2,        # 聚焦核心角色
            "conflict_intensity": 0.8,   # 高冲突强度
            "punchline_ratio": 0.2,      # 金句保留适中
            "context_preservation": 0.4, # 减少上下文，增加节奏感
            "linearity": 0.6             # 相对线性
        },
        
        # 深度情感预设 - 适合情感/人物刻画
        "深度情感": {
            "pace": 0.8,                 # 较慢节奏
            "emotion_intensity": 0.9,    # 高情感强度
            "subplot": 2,                # 集中情感线
            "cliffhanger_freq": 0.3,     # 低悬念频率
            "resolution_delay": 0.4,     # 低悬念密度
            "character_focus": 1,        # 单角色聚焦
            "conflict_intensity": 0.7,   # 中高冲突强度
            "punchline_ratio": 0.15,     # 金句保留适中
            "context_preservation": 0.7, # 高上下文保留
            "linearity": 0.8             # 高度线性
        },
        
        # 悬念优先预设 - 适合悬疑/惊悚
        "悬念优先": {
            "pace": 0.9,                 # 中等节奏
            "emotion_intensity": 0.6,    # 中等情感强度
            "subplot": 3,                # 多支线增加复杂性
            "cliffhanger_freq": 0.8,     # 高悬念频率
            "resolution_delay": 0.9,     # 最高悬念密度
            "character_focus": 3,        # 多角色视角
            "conflict_intensity": 0.5,   # 中等冲突强度
            "punchline_ratio": 0.1,      # 低金句保留
            "context_preservation": 0.5, # 中等上下文保留
            "linearity": 0.4             # 非线性叙事
        },
        
        # 剧情紧凑预设 - 适合网剧/短剧
        "剧情紧凑": {
            "pace": 1.2,                 # 较快节奏
            "emotion_intensity": 0.75,   # 中高情感强度
            "subplot": 1,                # 最少支线
            "cliffhanger_freq": 0.5,     # 中等悬念频率
            "resolution_delay": 0.6,     # 中高悬念密度
            "character_focus": 2,        # 双角色聚焦
            "conflict_intensity": 0.75,  # 高冲突强度
            "punchline_ratio": 0.25,     # 高金句保留
            "context_preservation": 0.4, # 低上下文保留
            "linearity": 0.85            # 高度线性
        },
        
        # 复杂叙事预设 - 适合剧情复杂的长剧
        "复杂叙事": {
            "pace": 0.7,                 # 慢节奏
            "emotion_intensity": 0.65,   # 中等情感强度
            "subplot": 5,                # 最多支线
            "cliffhanger_freq": 0.4,     # 中等悬念频率
            "resolution_delay": 0.5,     # 中等悬念密度
            "character_focus": 4,        # 多角色聚焦
            "conflict_intensity": 0.65,  # 中等冲突强度
            "punchline_ratio": 0.1,      # 低金句保留
            "context_preservation": 0.8, # 高上下文保留
            "linearity": 0.3             # 高度非线性
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化参数矩阵
        
        Args:
            config_path: 自定义配置文件路径
        """
        self.custom_presets = {}
        
        # 尝试加载自定义预设
        if config_path and os.path.exists(config_path):
            self._load_custom_presets(config_path)
    
    def _load_custom_presets(self, config_path: str) -> None:
        """从外部文件加载自定义预设
        
        Args:
            config_path: 配置文件路径
        """
        try:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_presets = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_presets = json.load(f)
            else:
                logger.warning(f"不支持的配置文件格式: {config_path}")
                return
                
            if isinstance(custom_presets, dict):
                self.custom_presets = custom_presets
                logger.info(f"已加载自定义参数预设: {len(custom_presets)}组")
            else:
                logger.warning(f"配置文件格式错误: {config_path}")
        except Exception as e:
            logger.error(f"加载自定义预设失败: {str(e)}")
    
    def get_preset(self, preset_name: str) -> Dict[str, Any]:
        """获取指定名称的预设参数
        
        Args:
            preset_name: 预设名称
            
        Returns:
            Dict[str, Any]: 预设参数字典
        """
        # 优先从自定义预设中查找
        if preset_name in self.custom_presets:
            return self.custom_presets[preset_name]
        
        # 再从内置预设中查找
        if preset_name in self.presets:
            return self.presets[preset_name]
        
        # 未找到，返回默认预设
        logger.warning(f"未找到预设 '{preset_name}', 使用默认预设")
        return self.presets["default"]
    
    def save_preset(self, preset_name: str, params: Dict[str, Any], 
                   output_path: str) -> bool:
        """保存自定义预设
        
        Args:
            preset_name: 预设名称
            params: 参数字典
            output_path: 输出文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 更新内存中的自定义预设
            self.custom_presets[preset_name] = params
            
            # 确定文件格式
            if output_path.endswith('.yaml') or output_path.endswith('.yml'):
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(self.custom_presets, f, allow_unicode=True)
            elif output_path.endswith('.json'):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(self.custom_presets, f, ensure_ascii=False, indent=2)
            else:
                # 默认使用YAML格式
                output_path = output_path if output_path.endswith('.yaml') else output_path + '.yaml'
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(self.custom_presets, f, allow_unicode=True)
            
            logger.info(f"已保存预设 '{preset_name}' 到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存预设失败: {str(e)}")
            return False
    
    def custom_config(self, **kwargs) -> Dict[str, Any]:
        """支持自定义参数组合
        
        Args:
            **kwargs: 自定义参数键值对
            
        Returns:
            Dict[str, Any]: 合并后的参数字典
        """
        # 获取基础预设参数（默认为"default"预设）
        preset_name = kwargs.pop('preset', 'default')
        base_params = self.get_preset(preset_name)
        
        # 将自定义参数合并到基础预设中
        merged_params = {**base_params, **kwargs}
        
        # 参数合法性校验和修正
        validated_params = self._validate_params(merged_params)
        
        return validated_params
    
    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """校验参数值是否在合法范围内
        
        Args:
            params: 待校验的参数字典
            
        Returns:
            Dict[str, Any]: 校验后的参数字典
        """
        # 参数合法范围定义
        valid_ranges = {
            "pace": (0.5, 2.0),
            "emotion_intensity": (0.0, 1.0),
            "subplot": (0, 5),
            "cliffhanger_freq": (0.0, 1.0),
            "resolution_delay": (0.0, 1.0),
            "character_focus": (1, 5),
            "conflict_intensity": (0.0, 1.0),
            "punchline_ratio": (0.0, 0.3),
            "context_preservation": (0.0, 1.0),
            "linearity": (0.0, 1.0)
        }
        
        validated = params.copy()
        
        # 校验每个参数
        for param, value in params.items():
            if param in valid_ranges:
                min_val, max_val = valid_ranges[param]
                
                # 数值类型强制转换
                if isinstance(value, str):
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"参数 '{param}' 值 '{value}' 无法转换为数字，使用默认值")
                        value = self.presets["default"][param]
                
                # 范围约束
                if value < min_val:
                    logger.warning(f"参数 '{param}' 值 {value} 小于最小值 {min_val}，已调整")
                    validated[param] = min_val
                elif value > max_val:
                    logger.warning(f"参数 '{param}' 值 {value} 大于最大值 {max_val}，已调整")
                    validated[param] = max_val
                else:
                    validated[param] = value
                    
        return validated
    
    def generate_language_specific_presets(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """生成语言特定的预设参数组
        
        为中英文生成各自优化的参数预设
        
        Returns:
            Dict: 语言特定的预设参数组
        """
        # 基于基础预设，为不同语言调整优化参数
        language_presets = {
            "zh": {},  # 中文预设
            "en": {}   # 英文预设
        }
        
        # 复制并调整所有基础预设
        for preset_name, preset_params in self.presets.items():
            # 中文优化参数 - 通常需要更高的上下文保留和较低线性度
            zh_params = preset_params.copy()
            zh_params["context_preservation"] = min(zh_params["context_preservation"] + 0.1, 1.0)
            zh_params["linearity"] = max(zh_params["linearity"] - 0.1, 0.0)
            
            # 英文优化参数 - 通常需要更高的情感强度和金句保留
            en_params = preset_params.copy()
            en_params["emotion_intensity"] = min(en_params["emotion_intensity"] + 0.05, 1.0)
            en_params["punchline_ratio"] = min(en_params["punchline_ratio"] + 0.05, 0.3)
            
            language_presets["zh"][preset_name] = zh_params
            language_presets["en"][preset_name] = en_params
        
        return language_presets
    
    def export_config_docs(self, output_path: str) -> bool:
        """导出参数配置文档
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 是否导出成功
        """
        try:
            # 参数说明
            param_descriptions = {
                "pace": "节奏系数 - 控制剪辑片段的平均时长 (0.5-2.0)",
                "emotion_intensity": "情感强度 - 控制情感波动和冲突强度 (0-1)",
                "subplot": "支线数量 - 允许保留的叙事支线数量 (0-5)",
                "cliffhanger_freq": "悬念频率 - 控制悬念点的出现频率 (0-1)",
                "resolution_delay": "悬念密度 - 控制悬念点与解决点之间的距离 (0-1)",
                "character_focus": "角色聚焦 - 重点关注的角色数量 (1-5)",
                "conflict_intensity": "冲突强度 - 控制矛盾冲突的强度 (0-1)",
                "punchline_ratio": "金句保留 - 决定保留原片金句的比例 (0-0.3)",
                "context_preservation": "上下文保留 - 决定场景切换的连续性 (0-1)",
                "linearity": "线性叙事 - 控制叙事的线性程度，越低越非线性 (0-1)"
            }
            
            # 生成文档内容
            doc_content = f"# 参数配置矩阵说明文档\n\n"
            doc_content += "本文档说明各预设参数的含义和作用。\n\n"
            
            # 参数说明部分
            doc_content += "## 参数详解\n\n"
            for param, desc in param_descriptions.items():
                doc_content += f"### {param}\n{desc}\n\n"
            
            # 预设列表
            doc_content += "## 内置预设\n\n"
            for preset_name, preset_params in self.presets.items():
                doc_content += f"### {preset_name}\n"
                doc_content += "```json\n"
                # 格式化JSON输出
                for param, value in preset_params.items():
                    doc_content += f"  \"{param}\": {value},\n"
                doc_content += "```\n\n"
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
                
            logger.info(f"已导出参数配置文档到 {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出参数配置文档失败: {str(e)}")
            return False


# 创建配置目录的单例实例
_param_matrix_instance = None

def get_param_matrix(config_path: Optional[str] = None) -> ParamMatrix:
    """获取参数矩阵单例实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ParamMatrix: 参数矩阵实例
    """
    global _param_matrix_instance
    if _param_matrix_instance is None:
        _param_matrix_instance = ParamMatrix(config_path)
    return _param_matrix_instance


if __name__ == "__main__":
    # 测试参数矩阵功能
    import os
    
    # 创建参数矩阵实例
    matrix = ParamMatrix()
    
    # 输出所有预设
    print("所有预设:")
    for name, params in matrix.presets.items():
        print(f"{name}: {params}")
    
    # 测试自定义配置
    custom = matrix.custom_config(
        preset="快节奏",
        emotion_intensity=0.85,
        subplot=4
    )
    print("\n自定义配置:")
    print(custom)
    
    # 导出配置文档
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    matrix.export_config_docs(os.path.join(docs_dir, "param_matrix.md")) 