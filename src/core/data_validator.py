"""数据验证模块。

此模块提供数据隔离和完整性验证功能，确保训练数据的质量和安全性。
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
import shutil
import re
from datetime import datetime

from loguru import logger
from ..utils.exceptions import ValidationError


class DataValidator:
    """数据验证器，负责验证数据隔离性和完整性。"""

    def __init__(self, data_root: str = "data"):
        """初始化数据验证器。

        Args:
            data_root: 数据根目录。
        """
        self.data_root = Path(data_root)
        self.training_dir = self.data_root / "training"
        self.validation_dir = self.data_root / "validation"
        self.test_dir = self.data_root / "test"
        self.metadata_dir = self.data_root / "metadata"
        
        # 确保目录存在
        for dir_path in [self.training_dir, self.validation_dir, self.test_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 初始化数据指纹缓存
        self._fingerprint_cache: Dict[str, str] = {}
        
        # 支持的语言
        self.supported_languages = {'en', 'zh'}

    def check_data_isolation(self, lang: str) -> bool:
        """检查指定语言的训练数据是否存在污染。

        Args:
            lang: 语言代码 ('en' 或 'zh')。

        Returns:
            bool: 如果数据隔离性验证通过返回 True，否则返回 False。

        Raises:
            ValidationError: 当验证失败时抛出。
        """
        if lang not in self.supported_languages:
            raise ValidationError(f"Unsupported language: {lang}")

        training_path = self.training_dir / lang
        if not training_path.exists():
            return True  # 目录不存在视为隔离

        # 检查是否存在跨语言文件
        other_lang = 'en' if lang == 'zh' else 'zh'
        contamination = []

        for file_path in training_path.rglob("*"):
            if not file_path.is_file():
                continue

            # 检查文件名是否包含其他语言标识
            if f".{other_lang}" in file_path.name:
                contamination.append(str(file_path))
                continue

            # 检查文件内容是否包含其他语言
            if self._detect_language_contamination(file_path, lang):
                contamination.append(str(file_path))

        if contamination:
            logger.warning(f"Found language contamination in {lang} dataset: {contamination}")
            return False

        return True

    def _detect_language_contamination(self, file_path: Path, expected_lang: str) -> bool:
        """检测文件内容是否存在语言污染。

        Args:
            file_path: 文件路径。
            expected_lang: 预期的语言。

        Returns:
            bool: 如果检测到语言污染返回 True，否则返回 False。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用简单的语言特征检测
            if expected_lang == 'zh':
                # 检查是否包含过多英文
                english_ratio = len(re.findall(r'[a-zA-Z]+', content)) / len(content)
                return english_ratio > 0.3
            else:
                # 检查是否包含中文字符
                return bool(re.search(r'[\u4e00-\u9fff]', content))

        except Exception as e:
            logger.error(f"Error checking language contamination in {file_path}: {e}")
            return False

    def verify_data_integrity(self, lang: str) -> Tuple[bool, List[str]]:
        """验证指定语言的数据完整性。

        Args:
            lang: 语言代码。

        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 错误消息列表)。

        Raises:
            ValidationError: 当验证失败时抛出。
        """
        if lang not in self.supported_languages:
            raise ValidationError(f"Unsupported language: {lang}")

        errors = []
        
        # 检查必需的目录结构
        for dir_name in ['training', 'validation', 'test']:
            dir_path = getattr(self, f"{dir_name}_dir") / lang
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_path}")
                continue

            # 检查数据文件
            if not any(dir_path.iterdir()):
                errors.append(f"Empty directory: {dir_path}")

        # 验证数据集的完整性
        for dir_name in ['training', 'validation', 'test']:
            dir_path = getattr(self, f"{dir_name}_dir") / lang
            if not dir_path.exists():
                continue

            # 检查每个文件的完整性
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue

                try:
                    # 验证文件格式
                    if not self._validate_file_format(file_path):
                        errors.append(f"Invalid file format: {file_path}")
                        continue

                    # 验证文件内容
                    if not self._validate_file_content(file_path):
                        errors.append(f"Invalid file content: {file_path}")
                        continue

                    # 验证文件指纹
                    if not self._verify_file_fingerprint(file_path):
                        errors.append(f"File fingerprint mismatch: {file_path}")

                except Exception as e:
                    errors.append(f"Error validating {file_path}: {str(e)}")

        return len(errors) == 0, errors

    def _validate_file_format(self, file_path: Path) -> bool:
        """验证文件格式。

        Args:
            file_path: 文件路径。

        Returns:
            bool: 如果格式有效返回 True，否则返回 False。
        """
        # 检查文件扩展名
        valid_extensions = {'.txt', '.json', '.jsonl', '.csv'}
        if file_path.suffix not in valid_extensions:
            return False

        # 检查文件大小
        if file_path.stat().st_size == 0:
            return False

        return True

    def _validate_file_content(self, file_path: Path) -> bool:
        """验证文件内容。

        Args:
            file_path: 文件路径。

        Returns:
            bool: 如果内容有效返回 True，否则返回 False。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查基本格式
            if not content.strip():
                return False

            # 根据文件类型进行特定验证
            if file_path.suffix == '.json':
                json.loads(content)  # 验证 JSON 格式
            elif file_path.suffix == '.csv':
                # 验证 CSV 格式
                lines = content.splitlines()
                if not lines:
                    return False
                header = lines[0].split(',')
                if not header:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating content of {file_path}: {e}")
            return False

    def _verify_file_fingerprint(self, file_path: Path) -> bool:
        """验证文件指纹。

        Args:
            file_path: 文件路径。

        Returns:
            bool: 如果指纹匹配返回 True，否则返回 False。
        """
        try:
            # 计算当前指纹
            current_fingerprint = self._calculate_file_fingerprint(file_path)

            # 获取存储的指纹
            fingerprint_file = self.metadata_dir / f"{file_path.stem}.fingerprint"
            if not fingerprint_file.exists():
                # 如果不存在指纹文件，创建一个
                self._save_file_fingerprint(file_path, current_fingerprint)
                return True

            # 比较指纹
            with open(fingerprint_file, 'r') as f:
                stored_fingerprint = f.read().strip()

            return current_fingerprint == stored_fingerprint

        except Exception as e:
            logger.error(f"Error verifying fingerprint of {file_path}: {e}")
            return False

    def _calculate_file_fingerprint(self, file_path: Path) -> str:
        """计算文件指纹。

        Args:
            file_path: 文件路径。

        Returns:
            str: 文件指纹。
        """
        if str(file_path) in self._fingerprint_cache:
            return self._fingerprint_cache[str(file_path)]

        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)

        fingerprint = hasher.hexdigest()
        self._fingerprint_cache[str(file_path)] = fingerprint
        return fingerprint

    def _save_file_fingerprint(self, file_path: Path, fingerprint: str) -> None:
        """保存文件指纹。

        Args:
            file_path: 文件路径。
            fingerprint: 文件指纹。
        """
        fingerprint_file = self.metadata_dir / f"{file_path.stem}.fingerprint"
        with open(fingerprint_file, 'w') as f:
            f.write(fingerprint)

    def clean_contaminated_data(self, lang: str) -> bool:
        """清理被污染的数据。

        Args:
            lang: 语言代码。

        Returns:
            bool: 如果清理成功返回 True，否则返回 False。

        Raises:
            ValidationError: 当清理失败时抛出。
        """
        if lang not in self.supported_languages:
            raise ValidationError(f"Unsupported language: {lang}")

        try:
            training_path = self.training_dir / lang
            if not training_path.exists():
                return True

            backup_path = self.data_root / "backup" / lang
            backup_path.mkdir(parents=True, exist_ok=True)

            # 创建备份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_path / f"backup_{timestamp}"
            shutil.copytree(training_path, backup_dir)

            # 查找并移除污染的文件
            other_lang = 'en' if lang == 'zh' else 'zh'
            contaminated_files = []

            for file_path in training_path.rglob("*"):
                if not file_path.is_file():
                    continue

                if (f".{other_lang}" in file_path.name or 
                    self._detect_language_contamination(file_path, lang)):
                    contaminated_files.append(file_path)

            # 移除污染文件
            for file_path in contaminated_files:
                file_path.unlink()

            logger.info(f"Cleaned {len(contaminated_files)} contaminated files from {lang} dataset")
            return True

        except Exception as e:
            logger.error(f"Error cleaning contaminated data for {lang}: {e}")
            raise ValidationError(f"Failed to clean contaminated data: {e}")

    def generate_data_report(self, lang: str) -> Dict[str, Any]:
        """生成数据验证报告。

        Args:
            lang: 语言代码。

        Returns:
            Dict[str, Any]: 包含验证结果的报告。
        """
        report = {
            "language": lang,
            "timestamp": datetime.now().isoformat(),
            "isolation_check": False,
            "integrity_check": False,
            "errors": [],
            "statistics": {
                "total_files": 0,
                "contaminated_files": 0,
                "invalid_files": 0,
                "dataset_sizes": {}
            }
        }

        try:
            # 检查数据隔离性
            report["isolation_check"] = self.check_data_isolation(lang)

            # 检查数据完整性
            integrity_result, errors = self.verify_data_integrity(lang)
            report["integrity_check"] = integrity_result
            report["errors"].extend(errors)

            # 收集统计信息
            for dir_name in ['training', 'validation', 'test']:
                dir_path = getattr(self, f"{dir_name}_dir") / lang
                if not dir_path.exists():
                    continue

                files = list(dir_path.rglob("*"))
                valid_files = [f for f in files if f.is_file() and self._validate_file_format(f)]
                
                report["statistics"]["total_files"] += len(valid_files)
                report["statistics"]["dataset_sizes"][dir_name] = len(valid_files)

                # 检查污染和无效文件
                contaminated = [f for f in valid_files if self._detect_language_contamination(f, lang)]
                invalid = [f for f in valid_files if not self._validate_file_content(f)]
                
                report["statistics"]["contaminated_files"] += len(contaminated)
                report["statistics"]["invalid_files"] += len(invalid)

        except Exception as e:
            logger.error(f"Error generating data report for {lang}: {e}")
            report["errors"].append(str(e))

        return report
