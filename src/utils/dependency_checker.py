import sys
import importlib
import subprocess
from pathlib import Path
from src.utils.log_handler import get_logger

logger = get_logger(__name__)

# 必需依赖列表
ESSENTIAL_DEPS = {
    "pytorch": "torch",
    "transformers": "transformers",
    "ffmpeg": "ffmpeg",
    "opencv": "cv2",
    "yaml": "yaml",
    "pandas": "pandas"
}

# 功能性依赖，按模块分组
FEATURE_DEPS = {
    "报告生成": {
        "plotly": "plotly",
        "pandas": "pandas",
        "jinja2": "jinja2"
    },
    "视频处理": {
        "moviepy": "moviepy",
        "ffmpeg": "ffmpeg_python"
    },
    "UI界面": {
        "PyQt6": "PyQt6",
        "pyqtgraph": "pyqtgraph"
    },
    "NLP处理": {
        "jieba": "jieba",
        "spacy": "spacy"
    }
}

def check_dependency(module_name, package_name=None):
    """检查依赖是否已安装
    
    Args:
        module_name: 模块导入名称
        package_name: pip包名称(若与模块名不同)
    
    Returns:
        bool: 是否已安装
    """
    if package_name is None:
        package_name = module_name
        
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_dependency(package_name):
    """尝试安装依赖
    
    Args:
        package_name: pip包名称
        
    Returns:
        bool: 是否安装成功
    """
    try:
        logger.info(f"正在安装依赖: {package_name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        logger.error(f"安装依赖失败: {package_name}")
        return False

def check_essential_dependencies(auto_install=False):
    """检查必需依赖
    
    Args:
        auto_install: 是否自动安装缺失依赖
        
    Returns:
        bool: 是否全部依赖可用
    """
    missing_deps = []
    
    for name, module in ESSENTIAL_DEPS.items():
        if not check_dependency(module, name):
            missing_deps.append(name)
            if auto_install:
                install_dependency(name)
    
    if missing_deps and not auto_install:
        logger.warning(f"缺少必需依赖: {', '.join(missing_deps)}")
        return False
    
    return True

def check_feature_dependencies(feature_name, auto_install=False):
    """检查特定功能的依赖
    
    Args:
        feature_name: 功能名称
        auto_install: 是否自动安装缺失依赖
        
    Returns:
        bool: 是否该功能的全部依赖可用
    """
    if feature_name not in FEATURE_DEPS:
        logger.warning(f"未知功能: {feature_name}")
        return False
    
    deps = FEATURE_DEPS[feature_name]
    missing_deps = []
    
    for name, module in deps.items():
        if not check_dependency(module, name):
            missing_deps.append(name)
            if auto_install:
                install_dependency(name)
    
    if missing_deps and not auto_install:
        logger.warning(f"功能 '{feature_name}' 缺少依赖: {', '.join(missing_deps)}")
        return False
    
    return True

def check_report_dependencies(auto_install=False):
    """检查报告生成功能的依赖
    
    Args:
        auto_install: 是否自动安装缺失依赖
        
    Returns:
        bool: 是否报告生成的全部依赖可用
    """
    return check_feature_dependencies("报告生成", auto_install)


if __name__ == "__main__":
    # 测试代码
    print(f"必需依赖检查: {'通过' if check_essential_dependencies() else '失败'}")
    
    for feature in FEATURE_DEPS:
        status = check_feature_dependencies(feature)
        print(f"功能 '{feature}' 依赖检查: {'通过' if status else '失败'}") 