import os
import yaml
from pathlib import Path

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
EXPORT_POLICY_CONFIG = CONFIG_DIR / "export_policy.yaml"

def get_export_policy():
    """获取导出策略配置"""
    if not EXPORT_POLICY_CONFIG.exists():
        # 创建默认配置
        create_default_config()
    
    try:
        with open(EXPORT_POLICY_CONFIG, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"读取导出策略配置时出错: {str(e)}")
        return None

def get_compatibility_data():
    """获取兼容性数据，用于报告生成"""
    policy = get_export_policy()
    if not policy or "compatibility" not in policy:
        return {}
    
    return policy["compatibility"]

def create_default_config():
    """创建默认的导出策略配置文件"""
    default_config = {
        "default_format": "jianying",
        "formats": {
            "jianying": {
                "enabled": True,
                "version": "9.2",
                "template_path": "templates/jianying_template.jy"
            },
            "davinci": {
                "enabled": True,
                "version": "18",
                "template_path": "templates/davinci_template.xml"
            },
            "mp4": {
                "enabled": True,
                "codec": "h264",
                "resolution": "source",
                "bitrate": "4M"
            }
        },
        "compatibility": {
            "剪映v9.2": 0.95,
            "剪映v9.1": 0.92,
            "剪映v9.0": 0.85,
            "剪映v8.9": 0.70
        },
        "preferences": {
            "auto_open": True,
            "save_intermediates": False,
            "quality_priority": "speed"  # speed, quality, balanced
        }
    }
    
    # 确保目录存在
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # 写入默认配置
    with open(EXPORT_POLICY_CONFIG, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False)

if __name__ == "__main__":
    # 测试代码
    policy = get_export_policy()
    print(f"导出策略: {policy}")
    
    compat = get_compatibility_data()
    print(f"兼容性数据: {compat}") 