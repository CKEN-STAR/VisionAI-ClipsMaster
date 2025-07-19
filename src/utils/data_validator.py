"""数据路径验证器

此模块负责验证数据加载路径的正确性和隔离性，确保不同语言的数据和模型完全隔离。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import PathError
from .config_loader import ConfigLoader
from loguru import logger


class DataPathValidator:
    """数据路径验证器类"""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """初始化数据路径验证器

        Args:
            config_loader: 配置加载器实例
        """
        self.config_loader = config_loader or ConfigLoader()
        self.base_paths = {
            'zh': {
                'data': 'data/zh',
                'models': 'models/zh',
                'cache': 'cache/zh'
            },
            'en': {
                'data': 'data/en',
                'models': 'models/en',
                'cache': 'cache/en'
            }
        }

    def validate_path_exists(self, path: str) -> bool:
        """验证路径是否存在

        Args:
            path: 要验证的路径

        Returns:
            bool: 路径是否存在
        """
        return os.path.exists(path)

    def validate_language_isolation(self, path: str, lang: str) -> bool:
        """验证语言数据隔离

        Args:
            path: 要验证的路径
            lang: 语言代码 ('zh' 或 'en')

        Returns:
            bool: 是否符合语言隔离要求

        Raises:
            PathError: 当路径不符合语言隔离要求时
        """
        if lang not in self.base_paths:
            raise PathError(f"Unsupported language: {lang}")

        path = Path(path).resolve()
        base_path = Path(self.base_paths[lang]['data']).resolve()

        try:
            path.relative_to(base_path)
            return True
        except ValueError:
            raise PathError(f"Path {path} is not under the correct language directory {base_path}")

    def validate_model_isolation(self, model_path: str, lang: str) -> bool:
        """验证模型隔离

        Args:
            model_path: 模型路径
            lang: 语言代码 ('zh' 或 'en')

        Returns:
            bool: 是否符合模型隔离要求

        Raises:
            PathError: 当模型路径不符合隔离要求时
        """
        if lang not in self.base_paths:
            raise PathError(f"Unsupported language: {lang}")

        model_path = Path(model_path).resolve()
        base_path = Path(self.base_paths[lang]['models']).resolve()

        try:
            model_path.relative_to(base_path)
            return True
        except ValueError:
            raise PathError(f"Model path {model_path} is not under the correct language directory {base_path}")

    def validate_cache_isolation(self, cache_path: str, lang: str) -> bool:
        """验证缓存隔离

        Args:
            cache_path: 缓存路径
            lang: 语言代码 ('zh' 或 'en')

        Returns:
            bool: 是否符合缓存隔离要求

        Raises:
            PathError: 当缓存路径不符合隔离要求时
        """
        if lang not in self.base_paths:
            raise PathError(f"Unsupported language: {lang}")

        cache_path = Path(cache_path).resolve()
        base_path = Path(self.base_paths[lang]['cache']).resolve()

        try:
            cache_path.relative_to(base_path)
            return True
        except ValueError:
            raise PathError(f"Cache path {cache_path} is not under the correct language directory {base_path}")

    def ensure_directory_structure(self) -> None:
        """确保所有必要的目录结构存在"""
        for lang in self.base_paths:
            for path_type, path in self.base_paths[lang].items():
                os.makedirs(path, exist_ok=True)
                logger.info(f"Ensured {path_type} directory for {lang}: {path}")

    def get_path(self, lang: str, path_type: str) -> str:
        """获取指定语言和类型的路径

        Args:
            lang: 语言代码 ('zh' 或 'en')
            path_type: 路径类型 ('data', 'models', 或 'cache')

        Returns:
            str: 对应的路径

        Raises:
            PathError: 当语言或路径类型无效时
        """
        if lang not in self.base_paths:
            raise PathError(f"Unsupported language: {lang}")
        if path_type not in self.base_paths[lang]:
            raise PathError(f"Invalid path type: {path_type}")
        
        return self.base_paths[lang][path_type]

    def validate_all_paths(self) -> Dict[str, List[str]]:
        """验证所有路径

        Returns:
            Dict[str, List[str]]: 验证结果，包含任何错误信息
        """
        results = {
            'success': [],
            'errors': []
        }

        for lang in self.base_paths:
            for path_type, path in self.base_paths[lang].items():
                try:
                    if not self.validate_path_exists(path):
                        results['errors'].append(f"Path does not exist: {path}")
                    elif path_type == 'data' and not self.validate_language_isolation(path, lang):
                        results['errors'].append(f"Invalid language isolation for {path}")
                    elif path_type == 'models' and not self.validate_model_isolation(path, lang):
                        results['errors'].append(f"Invalid model isolation for {path}")
                    elif path_type == 'cache' and not self.validate_cache_isolation(path, lang):
                        results['errors'].append(f"Invalid cache isolation for {path}")
                    else:
                        results['success'].append(f"Validated {path_type} path for {lang}: {path}")
                except PathError as e:
                    results['errors'].append(str(e))

        return results 